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

# Add src, backend, and root to sys.path so both python -m backend.src.outbound_call and python -m src.outbound_call work
src_dir = Path(__file__).resolve().parent
backend_dir = src_dir.parent
root_dir = backend_dir.parent

for path_entry in [str(src_dir), str(backend_dir), str(root_dir)]:
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

try:
    from memory import get_user, init_database, set_opt_out_status
except ImportError:
    from backend.src.memory import get_user, init_database, set_opt_out_status

logger = logging.getLogger("outbound_call")
logging.basicConfig(level=logging.INFO)

# Robustly load backend/.env.local from potential paths
env_candidates = [
    Path(__file__).resolve().parent.parent / ".env.local",
    Path.cwd() / "backend" / ".env.local",
    Path.cwd() / ".env.local",
]
for candidate in env_candidates:
    if candidate.exists():
        load_dotenv(candidate)
        break
else:
    load_dotenv(".env.local")

init_database()


class CallOutcome(str, Enum):
    COMPLETED = "completed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    VOICEMAIL = "voicemail"
    IMMEDIATE_HANGUP = "immediate_hangup"
    OPT_OUT = "opt_out"
    OPT_OUT_SUPPRESSED = "opt_out_suppressed"


class RetryRule:
    """Defines retry behavior for outbound call outcomes."""

    @staticmethod
    def calculate_next_attempt(
        outcome: CallOutcome, current_retry_count: int
    ) -> tuple[bool, datetime | None, str]:
        """
        Calculates whether a retry should be scheduled, the next attempt time,
        and the rationale based on Day 6 advanced outcome rules.
        """
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
                "Answering machine detected. Left automated message. No further retry today.",
            )

        if outcome == CallOutcome.IMMEDIATE_HANGUP:
            return (
                False,
                None,
                "User hung up immediately (< 5s). Will not retry today to respect user.",
            )

        if current_retry_count >= max_retries:
            return (
                False,
                None,
                f"Maximum retry attempts ({max_retries}) reached for outcome '{outcome.value}'.",
            )

        if outcome == CallOutcome.NO_ANSWER:
            delay_minutes = 15 * (
                2**current_retry_count
            )  # Exponential backoff: 15m, 30m, 60m
            next_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
            return (
                True,
                next_time,
                f"No answer. Scheduled retry #{current_retry_count + 1} in {delay_minutes} minutes.",
            )

        if outcome == CallOutcome.BUSY:
            delay_minutes = 10 * (
                2**current_retry_count
            )  # Exponential backoff: 10m, 20m, 40m
            next_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
            return (
                True,
                next_time,
                f"Line busy. Scheduled retry #{current_retry_count + 1} in {delay_minutes} minutes.",
            )

        return False, None, f"Unhandled outcome '{outcome.value}'."


async def _create_livekit_room(
    livekit_url: str,
    api_key: str,
    api_secret: str,
    room_name: str,
    metadata_dict: dict,
):
    """Pre-create room with metadata via LiveKit API."""
    try:
        from livekit.api import CreateRoomRequest, LiveKitAPI

        async with LiveKitAPI(
            url=livekit_url, api_key=api_key, api_secret=api_secret
        ) as api:
            await api.room.create_room(
                CreateRoomRequest(
                    name=room_name,
                    metadata=json.dumps(metadata_dict),
                    empty_timeout=300,
                )
            )
            logger.info("Successfully pre-created LiveKit room '%s' with metadata.", room_name)
    except Exception as err:
        logger.warning("Could not pre-create LiveKit room via LiveKitAPI: %s", err)


async def _dispatch_sip_participant(
    livekit_url: str,
    api_key: str,
    api_secret: str,
    trunk_id: str,
    to_number: str,
    room_name: str,
    user_id: str,
    user_name: str,
) -> str:
    """Dispatch outbound SIP participant via LiveKit SIP API."""
    from livekit.api import CreateSipParticipantRequest, LiveKitAPI

    async with LiveKitAPI(
        url=livekit_url, api_key=api_key, api_secret=api_secret
    ) as api:
        sip_resp = await api.sip.create_sip_participant(
            CreateSipParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=to_number,
                room_name=room_name,
                participant_identity=user_id,
                participant_name=user_name,
            )
        )
        return sip_resp.sip_participant_id


class OutboundCallManager:
    """Manages outbound calls via Twilio / LiveKit SIP API and tracks outcome rules."""

    def __init__(self):
        self.livekit_url = os.getenv("LIVEKIT_URL")
        self.livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        self.livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from_number = os.getenv("TWILIO_FROM_NUMBER")
        self.sip_trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
        self.sip_domain = os.getenv("LIVEKIT_SIP_DOMAIN", "sip.livekit.cloud")

    def place_outbound_call(
        self,
        to_number: str,
        user_id: str,
        user_name: str = "Learner",
        topic: str = "Daily Revision Quiz",
        simulate_outcome: str | None = None,
    ) -> dict:
        """
        Initiates an outbound call to the target phone number / SIP user.
        Checks opt-out status prior to calling.
        """
        # Step 1: Check opt-out status in memory
        user_data = get_user(user_id)
        if user_data and user_data.get("opted_out"):
            logger.warning(
                "Call cancelled for user '%s': User has opted out of automated calls.",
                user_id,
            )
            return self.log_call_outcome(
                user_id=user_id,
                to_number=to_number,
                outcome=CallOutcome.OPT_OUT_SUPPRESSED,
                retry_count=0,
                notes="Call suppressed due to active opt-out preference.",
            )

        room_name = f"outbound-{user_id}-{int(datetime.now().timestamp())}"
        room_metadata = {
            "is_outbound": True,
            "outbound_reason": "Scheduled Daily Practice Call",
            "user_id": user_id,
            "user_name": user_name,
            "topic": topic,
            "opening_greeting": (
                "Hello! I am Medha AI, your AI Voice Learning Companion from VoiceForBharat. "
                f"I am calling for your scheduled daily practice call to review {topic} and take a quick quiz. "
                "If you ever want to end this call or stop receiving daily practice calls, just say 'stop' or 'unsubscribe'."
            ),
        }

        logger.info(
            "Initiating outbound call to %s (User: %s) for topic '%s'...",
            to_number,
            user_name,
            topic,
        )

        # Step 2: Handle explicit simulation mode (--simulate-outcome)
        if simulate_outcome:
            outcome = CallOutcome.COMPLETED
            try:
                outcome = CallOutcome(simulate_outcome.lower())
            except ValueError:
                logger.warning(
                    "Invalid outcome '%s', defaulting to completed.", simulate_outcome
                )

            if outcome == CallOutcome.OPT_OUT:
                set_opt_out_status(user_id, opted_out=True)

            return self.log_call_outcome(
                user_id=user_id,
                to_number=to_number,
                outcome=outcome,
                retry_count=0,
                room_name=room_name,
                provider_call_id=f"sim-call-{int(datetime.now().timestamp())}",
                dispatch_status="simulated",
                metadata=room_metadata,
            )

        # Step 3: REAL CALL MODE — Check required credentials
        missing_keys = []
        if not self.twilio_account_sid:
            missing_keys.append("TWILIO_ACCOUNT_SID")
        if not self.twilio_auth_token:
            missing_keys.append("TWILIO_AUTH_TOKEN")
        if not self.twilio_from_number:
            missing_keys.append("TWILIO_FROM_NUMBER")

        if missing_keys and not self.sip_trunk_id:
            err_msg = (
                "Twilio credentials are not configured. "
                f"Add {', '.join(missing_keys)} to backend/.env.local to place real outbound calls."
            )
            logger.error(err_msg)
            print(f"\n[ERROR] {err_msg}\n")
            return self.log_call_outcome(
                user_id=user_id,
                to_number=to_number,
                outcome=CallOutcome.COMPLETED,
                retry_count=0,
                room_name=room_name,
                provider_call_id="",
                dispatch_status="error_missing_credentials",
                notes=err_msg,
                metadata=room_metadata,
            )

        # Pre-create LiveKit room with metadata if LiveKit URL and API keys exist
        if self.livekit_url and self.livekit_api_key and self.livekit_api_secret:
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
            except Exception as r_err:
                logger.warning("LiveKit room pre-creation warning: %s", r_err)

        dispatch_status = "error_dispatch_failed"
        provider_call_id = ""
        error_notes = ""

        # Option A: LiveKit SIP Outbound Trunk Dispatch (if LIVEKIT_SIP_TRUNK_ID is configured)
        if self.sip_trunk_id and self.livekit_url and self.livekit_api_key and self.livekit_api_secret:
            try:
                sip_id = asyncio.run(
                    _dispatch_sip_participant(
                        self.livekit_url,
                        self.livekit_api_key,
                        self.livekit_api_secret,
                        self.sip_trunk_id,
                        to_number,
                        room_name,
                        user_id,
                        user_name,
                    )
                )
                dispatch_status = "dispatched_livekit_sip"
                provider_call_id = sip_id or f"sip-{int(datetime.now().timestamp())}"
                logger.info("Dispatched LiveKit SIP Participant ID: %s", provider_call_id)
            except Exception as sip_err:
                logger.error("LiveKit SIP Trunk dispatch failed: %s", sip_err)
                error_notes += f"LiveKit SIP failed: {sip_err}; "

        # Option B: Direct Twilio REST API Dispatch
        if (
            dispatch_status != "dispatched_livekit_sip"
            and self.twilio_account_sid
            and self.twilio_auth_token
            and self.twilio_from_number
        ):
            try:
                from twilio.rest import Client

                client = Client(self.twilio_account_sid, self.twilio_auth_token)
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
                logger.info("Dispatched Twilio Call SID: %s", call.sid)
            except Exception as twilio_err:
                err_msg = f"Twilio API call dispatch failed: {twilio_err}"
                logger.error(err_msg)
                print(f"\n[ERROR] {err_msg}\n")
                error_notes += err_msg

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
            outcome=outcome, current_retry_count=retry_count
        )

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "to_number": to_number,
            "room_name": room_name,
            "provider_call_id": provider_call_id,
            "dispatch_status": dispatch_status,
            "outcome": outcome.value,
            "should_retry": should_retry,
            "next_attempt_at": next_attempt_at.isoformat() if next_attempt_at else None,
            "retry_count": retry_count,
            "retry_rationale": rationale,
            "notes": notes,
            "metadata": metadata or {},
        }

        logger.info("Call Outcome Record: %s", json.dumps(record, indent=2))
        return record


def main():
    parser = argparse.ArgumentParser(
        description="Medha AI Outbound Call Trigger (Day 6)"
    )
    parser.add_argument(
        "--to",
        required=True,
        help="Target phone number or SIP URI (e.g. +919876543210)",
    )
    parser.add_argument("--name", default="Learner", help="Learner's name")
    parser.add_argument(
        "--user-id", default=None, help="User ID (defaults to formatted phone number)"
    )
    parser.add_argument(
        "--topic",
        default="Photosynthesis & Science Quiz",
        help="Learning topic for practice call",
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
        help="Simulate specific outcome for testing retry logic",
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
    print(json.dumps(result, indent=2))

    # Exit with code 1 if credentials missing or real dispatch failed
    if result.get("dispatch_status") in ("error_missing_credentials", "error_dispatch_failed"):
        sys.exit(1)


if __name__ == "__main__":
    main()
