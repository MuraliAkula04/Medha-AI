import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

# ============================================================
# PATH SETUP
# ============================================================

src_dir = Path(__file__).resolve().parent
backend_dir = src_dir.parent
root_dir = backend_dir.parent

for path_entry in [str(src_dir), str(backend_dir), str(root_dir)]:
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)


# ============================================================
# MEMORY
# ============================================================

try:
    from memory import get_user, init_database, set_opt_out_status
except ImportError:
    from backend.src.memory import get_user, init_database, set_opt_out_status


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("outbound_call")
logging.basicConfig(level=logging.INFO)


# ============================================================
# ENVIRONMENT
# ============================================================

env_candidates = [
    Path(__file__).resolve().parent.parent / ".env.local",
    Path.cwd() / "backend" / ".env.local",
    Path.cwd() / ".env.local",
]

for candidate in env_candidates:
    if candidate.exists():
        load_dotenv(candidate)
        logger.info("Loaded environment from %s", candidate)
        break
else:
    load_dotenv(".env.local")


init_database()


# ============================================================
# CALL OUTCOMES
# ============================================================


class CallOutcome(str, Enum):
    COMPLETED = "completed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    VOICEMAIL = "voicemail"
    IMMEDIATE_HANGUP = "immediate_hangup"
    OPT_OUT = "opt_out"
    OPT_OUT_SUPPRESSED = "opt_out_suppressed"


# ============================================================
# RETRY RULES
# ============================================================


class RetryRule:
    """Defines retry behavior for outbound call outcomes."""

    @staticmethod
    def calculate_next_attempt(
        outcome: CallOutcome,
        current_retry_count: int,
    ) -> tuple[bool, datetime | None, str]:

        max_retries = 3

        if outcome in (
            CallOutcome.COMPLETED,
            CallOutcome.OPT_OUT,
            CallOutcome.OPT_OUT_SUPPRESSED,
        ):
            return (
                False,
                None,
                f"Call ended with terminal state '{outcome.value}'. No retry needed.",
            )

        if outcome == CallOutcome.VOICEMAIL:
            return (
                False,
                None,
                "Answering machine detected. "
                "Left automated message. No further retry today.",
            )

        if outcome == CallOutcome.IMMEDIATE_HANGUP:
            return (
                False,
                None,
                "User hung up immediately (< 5s). "
                "Will not retry today to respect user.",
            )

        if current_retry_count >= max_retries:
            return (
                False,
                None,
                f"Maximum retry attempts ({max_retries}) reached "
                f"for outcome '{outcome.value}'.",
            )

        if outcome == CallOutcome.NO_ANSWER:
            delay_minutes = 15 * (2**current_retry_count)
            next_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)

            return (
                True,
                next_time,
                f"No answer. Scheduled retry "
                f"#{current_retry_count + 1} in {delay_minutes} minutes.",
            )

        if outcome == CallOutcome.BUSY:
            delay_minutes = 10 * (2**current_retry_count)
            next_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)

            return (
                True,
                next_time,
                f"Line busy. Scheduled retry "
                f"#{current_retry_count + 1} in {delay_minutes} minutes.",
            )

        return False, None, f"Unhandled outcome '{outcome.value}'."


# ============================================================
# LIVEKIT ROOM
# ============================================================


async def _create_livekit_room(
    livekit_url: str,
    api_key: str,
    api_secret: str,
    room_name: str,
    metadata_dict: dict,
):
    """Pre-create LiveKit room with outbound metadata."""

    try:
        from livekit.api import CreateRoomRequest, LiveKitAPI

        async with LiveKitAPI(
            url=livekit_url,
            api_key=api_key,
            api_secret=api_secret,
        ) as api:
            await api.room.create_room(
                CreateRoomRequest(
                    name=room_name,
                    metadata=json.dumps(metadata_dict),
                    empty_timeout=300,
                )
            )

            logger.info(
                "Successfully pre-created LiveKit room '%s'.",
                room_name,
            )

    except Exception as err:
        logger.warning(
            "Could not pre-create LiveKit room: %s",
            err,
        )


# ============================================================
# LIVEKIT SIP DISPATCH
# ============================================================


async def _dispatch_agent(
    livekit_url: str,
    api_key: str,
    api_secret: str,
    room_name: str,
    agent_name: str,
    metadata: dict,
) -> str:
    """Explicitly dispatch the voice agent into the outbound room."""
    from livekit.api import CreateAgentDispatchRequest, LiveKitAPI

    async with LiveKitAPI(
        url=livekit_url,
        api_key=api_key,
        api_secret=api_secret,
    ) as api:
        dispatch = await api.agent_dispatch.create_dispatch(
            CreateAgentDispatchRequest(
                agent_name=agent_name,
                room=room_name,
                metadata=json.dumps(metadata),
            )
        )

        dispatch_id = (
            getattr(dispatch, "id", None)
            or getattr(dispatch, "dispatch_id", None)
            or getattr(dispatch, "agent_name", None)
            or agent_name
        )

        logger.info(
            "Agent '%s' dispatched to room '%s'. Dispatch ID: %s",
            agent_name,
            room_name,
            dispatch_id,
        )

        return dispatch_id


async def _dispatch_sip_participant(
    livekit_url: str,
    api_key: str,
    api_secret: str,
    trunk_id: str,
    to_number: str,
    room_name: str,
    user_id: str,
    user_name: str,
    sip_domain: str,
) -> str:
    """
    Create an outbound SIP participant through LiveKit.

    Accepts:
        murali12304
        sip:murali12304
        murali12304@sip.linphone.org
        sip:murali12304@sip.linphone.org
    """

    from livekit.api import (
        CreateSIPParticipantRequest,
        LiveKitAPI,
    )
    # --------------------------------------------------------
    # Normalize destination for LiveKit SIP
    # --------------------------------------------------------
    # LiveKit's sip_call_to expects a phone number or SIP user,
    # not a full sip: URI. For Linphone, pass only the username.

    sip_destination = to_number.strip()

    if sip_destination.lower().startswith("sip:"):
        sip_destination = sip_destination[4:]

    if "@" in sip_destination:
        sip_destination = sip_destination.split("@", 1)[0]

    logger.info(
        "Calling SIP user: %s",
        sip_destination,
    )

    # --------------------------------------------------------
    # Create SIP participant
    # --------------------------------------------------------

    async with LiveKitAPI(
        url=livekit_url,
        api_key=api_key,
        api_secret=api_secret,
    ) as api:
        sip_response = await api.sip.create_sip_participant(
            CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=sip_destination,
                room_name=room_name,
                participant_identity=user_id,
                participant_name=user_name,
                wait_until_answered=True,
            )
        )

        logger.info(
            "SIP participant response: %s",
            sip_response,
        )

        return (
            getattr(sip_response, "participant_id", None)
            or getattr(sip_response, "sip_participant_id", None)
            or user_id
        )


# ============================================================
# OUTBOUND CALL MANAGER
# ============================================================


class OutboundCallManager:
    """
    Manages outbound calls.

    Primary:
        LiveKit SIP + Linphone

    Optional fallback:
        Twilio
    """

    def __init__(self):

        # ----------------------------------------------------
        # LiveKit
        # ----------------------------------------------------

        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")

        # ----------------------------------------------------
        # LiveKit SIP
        # ----------------------------------------------------

        self.sip_trunk_id = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID") or os.getenv(
            "LIVEKIT_SIP_TRUNK_ID"
        )

        self.sip_domain = os.getenv(
            "LINPHONE_SIP_DOMAIN",
            "sip.linphone.org",
        )

        # ----------------------------------------------------
        # Optional Twilio fallback
        # ----------------------------------------------------

        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")

        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER")

    # ========================================================
    # PLACE OUTBOUND CALL
    # ========================================================

    def place_outbound_call(
        self,
        to_number: str,
        user_id: str,
        user_name: str = "Learner",
        topic: str = "Daily Revision Quiz",
        simulate_outcome: str | None = None,
    ) -> dict:

        # ----------------------------------------------------
        # STEP 1 — Check opt-out
        # ----------------------------------------------------

        user_data = get_user(user_id)

        if user_data and user_data.get("opted_out"):
            logger.warning(
                "Call cancelled for user '%s': User has opted out.",
                user_id,
            )

            return self.log_call_outcome(
                user_id=user_id,
                to_number=to_number,
                outcome=CallOutcome.OPT_OUT_SUPPRESSED,
                retry_count=0,
                notes=("Call suppressed due to active opt-out preference."),
            )

        # ----------------------------------------------------
        # ROOM
        # ----------------------------------------------------

        room_name = f"outbound-{user_id}-{int(datetime.now().timestamp())}"

        # ----------------------------------------------------
        # OUTBOUND METADATA
        # ----------------------------------------------------

        room_metadata = {
            "is_outbound": True,
            "outbound_reason": ("Scheduled Daily Practice Call"),
            "user_id": user_id,
            "user_name": user_name,
            "topic": topic,
            "opening_greeting": (
                "Hello! I am Medha AI, your AI Voice "
                "Learning Companion from VoiceForBharat. "
                f"I am calling for your scheduled daily "
                f"practice call to review {topic} and take "
                "a quick quiz. If you ever want to end this "
                "call or stop receiving daily practice calls, "
                "just say 'stop' or 'unsubscribe'."
            ),
        }

        logger.info(
            "Initiating outbound call to %s (User: %s) for topic '%s'...",
            to_number,
            user_name,
            topic,
        )

        # ----------------------------------------------------
        # STEP 2 — Simulation
        # ----------------------------------------------------

        if simulate_outcome:
            outcome = CallOutcome.COMPLETED

            try:
                outcome = CallOutcome(simulate_outcome.lower())

            except ValueError:
                logger.warning(
                    "Invalid outcome '%s'. Defaulting to completed.",
                    simulate_outcome,
                )

            if outcome == CallOutcome.OPT_OUT:
                set_opt_out_status(
                    user_id,
                    opted_out=True,
                )

            return self.log_call_outcome(
                user_id=user_id,
                to_number=to_number,
                outcome=outcome,
                retry_count=0,
                room_name=room_name,
                provider_call_id=(f"sim-call-{int(datetime.now().timestamp())}"),
                dispatch_status="simulated",
                metadata=room_metadata,
            )

        # ----------------------------------------------------
        # STEP 3 — VERIFY LIVEKIT CONFIGURATION
        # ----------------------------------------------------

        missing_keys = []

        if not self.livekit_url:
            missing_keys.append("LIVEKIT_URL")

        if not self.livekit_api_key:
            missing_keys.append("LIVEKIT_API_KEY")

        if not self.livekit_api_secret:
            missing_keys.append("LIVEKIT_API_SECRET")

        if not self.sip_trunk_id:
            missing_keys.append("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")

        if missing_keys:
            error_message = (
                "LiveKit SIP configuration is incomplete. "
                f"Missing: {', '.join(missing_keys)}"
            )

            logger.error(error_message)

            print(f"\n[ERROR] {error_message}\n")

            return self.log_call_outcome(
                user_id=user_id,
                to_number=to_number,
                outcome=CallOutcome.COMPLETED,
                retry_count=0,
                room_name=room_name,
                provider_call_id="",
                dispatch_status=("error_missing_livekit_credentials"),
                notes=error_message,
                metadata=room_metadata,
            )

        # ----------------------------------------------------
        # STEP 4 — PRE-CREATE LIVEKIT ROOM
        # ----------------------------------------------------

        try:
            asyncio.run(
                _create_livekit_room(
                    self.livekit_url,
                    self.livekit_api_key,
                    self.livekit_api_secret,
                    room_name,
                    room_metadata,
                )
            )

        except Exception as room_error:
            logger.warning(
                "LiveKit room creation warning: %s",
                room_error,
            )

        # ----------------------------------------------------
        # STEP 5 — EXPLICITLY DISPATCH THE AGENT
        # ----------------------------------------------------
        # LiveKit outbound calling requires the agent to be
        # dispatched into the same room BEFORE the SIP participant
        # is created. Otherwise the phone can ring successfully
        # while no AI agent is present to send audio.
        try:
            dispatch_id = asyncio.run(
                _dispatch_agent(
                    livekit_url=self.livekit_url,
                    api_key=self.livekit_api_key,
                    api_secret=self.livekit_api_secret,
                    room_name=room_name,
                    agent_name=os.getenv("LIVEKIT_AGENT_NAME", "my-agent"),
                    metadata=room_metadata,
                )
            )
            logger.info(
                "Successfully dispatched agent '%s' to room '%s' (dispatch=%s)",
                os.getenv("LIVEKIT_AGENT_NAME", "my-agent"),
                room_name,
                dispatch_id,
            )
        except Exception as dispatch_error:
            error_message = f"Agent dispatch failed: {dispatch_error}"
            logger.error(error_message)
            return self.log_call_outcome(
                user_id=user_id,
                to_number=to_number,
                outcome=CallOutcome.COMPLETED,
                retry_count=0,
                room_name=room_name,
                provider_call_id="",
                dispatch_status="error_agent_dispatch_failed",
                notes=error_message,
                metadata=room_metadata,
            )

        # ----------------------------------------------------
        # STEP 6 — LIVEKIT SIP CALL
        # ----------------------------------------------------

        dispatch_status = "error_dispatch_failed"
        provider_call_id = ""
        error_notes = ""

        try:
            sip_id = asyncio.run(
                _dispatch_sip_participant(
                    livekit_url=self.livekit_url,
                    api_key=self.livekit_api_key,
                    api_secret=self.livekit_api_secret,
                    trunk_id=self.sip_trunk_id,
                    to_number=to_number,
                    room_name=room_name,
                    user_id=user_id,
                    user_name=user_name,
                    sip_domain=self.sip_domain,
                )
            )

            dispatch_status = "dispatched_livekit_sip"

            provider_call_id = sip_id or f"sip-{int(datetime.now().timestamp())}"

            logger.info(
                "Successfully dispatched LiveKit SIP participant: %s",
                provider_call_id,
            )

        except Exception as sip_error:
            error_notes = f"LiveKit SIP dispatch failed: {sip_error}"

            logger.error(error_notes)

        # ----------------------------------------------------
        # STEP 6 — OPTIONAL TWILIO FALLBACK
        # ----------------------------------------------------

        if (
            dispatch_status != "dispatched_livekit_sip"
            and self.twilio_account_sid
            and self.twilio_auth_token
            and self.twilio_from_number
        ):
            try:
                from twilio.rest import Client

                client = Client(
                    self.twilio_account_sid,
                    self.twilio_auth_token,
                )

                sip_uri = f"sip:{room_name}@{self.sip_domain}"

                twiml = f"<Response><Connect><Sip>{sip_uri}</Sip></Connect></Response>"

                call = client.calls.create(
                    to=to_number,
                    from_=self.twilio_from_number,
                    twiml=twiml,
                    machine_detection="Enable",
                )

                provider_call_id = call.sid

                dispatch_status = "dispatched_twilio"

                logger.info(
                    "Dispatched Twilio call: %s",
                    call.sid,
                )

            except Exception as twilio_error:
                twilio_message = f"Twilio fallback failed: {twilio_error}"

                logger.error(twilio_message)

                error_notes += f" {twilio_message}"

        # ----------------------------------------------------
        # STEP 7 — LOG RESULT
        # ----------------------------------------------------

        return self.log_call_outcome(
            user_id=user_id,
            to_number=to_number,
            outcome=CallOutcome.COMPLETED,
            retry_count=0,
            room_name=room_name,
            provider_call_id=provider_call_id,
            dispatch_status=dispatch_status,
            notes=error_notes,
            metadata=room_metadata,
        )

    # ========================================================
    # LOG CALL OUTCOME
    # ========================================================

    def log_call_outcome(
        self,
        user_id: str,
        to_number: str,
        outcome: CallOutcome,
        retry_count: int = 0,
        room_name: str = "",
        provider_call_id: str = "",
        dispatch_status: str = "completed",
        notes: str = "",
        metadata: dict | None = None,
    ) -> dict:

        should_retry, next_attempt_at, rationale = RetryRule.calculate_next_attempt(
            outcome=outcome,
            current_retry_count=retry_count,
        )

        record = {
            "timestamp": (datetime.now(timezone.utc).isoformat()),
            "user_id": user_id,
            "to_number": to_number,
            "room_name": room_name,
            "provider_call_id": provider_call_id,
            "dispatch_status": dispatch_status,
            "outcome": outcome.value,
            "should_retry": should_retry,
            "next_attempt_at": (
                next_attempt_at.isoformat() if next_attempt_at else None
            ),
            "retry_count": retry_count,
            "retry_rationale": rationale,
            "notes": notes,
            "metadata": metadata or {},
        }

        logger.info(
            "Call Outcome Record: %s",
            json.dumps(
                record,
                indent=2,
            ),
        )

        return record


# ============================================================
# CLI
# ============================================================


def main():

    parser = argparse.ArgumentParser(
        description=("Medha AI Outbound Call Trigger (Day 6 - Linphone)")
    )

    parser.add_argument(
        "--to",
        required=True,
        help=(
            "Linphone username or SIP URI. "
            "Example: murali12304 or "
            "sip:murali12304@sip.linphone.org"
        ),
    )

    parser.add_argument(
        "--name",
        default="Learner",
        help="Learner's name",
    )

    parser.add_argument(
        "--user-id",
        default=None,
        help=("User ID. Defaults to the Linphone username."),
    )

    parser.add_argument(
        "--topic",
        default="Photosynthesis & Science Quiz",
        help="Learning topic for the practice call",
    )

    parser.add_argument(
        "--simulate-outcome",
        choices=[
            "completed",
            "no_answer",
            "busy",
            "voicemail",
            "immediate_hangup",
            "opt_out",
        ],
        help=("Simulate an outcome for testing retry and opt-out logic."),
    )

    args = parser.parse_args()

    user_id = args.user_id or f"user_{args.to.replace('+', '').replace(' ', '')}"

    manager = OutboundCallManager()

    result = manager.place_outbound_call(
        to_number=args.to,
        user_id=user_id,
        user_name=args.name,
        topic=args.topic,
        simulate_outcome=args.simulate_outcome,
    )

    print("\n--- OUTBOUND CALL LOG ENTRY ---")

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    # Return an error code when the actual
    # outbound dispatch failed.
    if result.get("dispatch_status") in (
        "error_missing_livekit_credentials",
        "error_dispatch_failed",
    ):
        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
