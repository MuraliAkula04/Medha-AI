import json
from unittest.mock import AsyncMock

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant, sanitize_pii
from memory import (
    get_escalations,
    init_database,
    save_escalation,
    update_escalation_status,
)

# Ensure SQLite database is initialized
init_database()


def _llm() -> llm.LLM:
    return inference.LLM(model="google/gemini-2.5-flash")


@pytest.fixture
def mock_run_context():
    context = AsyncMock()
    context.room = AsyncMock()
    context.room.local_participant = AsyncMock()
    return context


# ============================================================================
# UNIT TESTS
# ============================================================================


def test_sanitize_pii_redaction():
    """Test that sanitize_pii strips passwords, OTPs, PINs, and card numbers."""
    raw_text = (
        "User reported issue. Password: SecretPass123. "
        "Entered OTP 987654 and card number 4532112233445566."
    )
    cleaned = sanitize_pii(raw_text)

    assert "SecretPass123" not in cleaned
    assert "987654" not in cleaned
    assert "4532112233445566" not in cleaned
    assert "[REDACTED]" in cleaned or "[REDACTED_CODE]" in cleaned


@pytest.mark.asyncio
async def test_create_escalation_tool_success(mock_run_context):
    """Test create_escalation function tool generates ref_id, saves to DB, and publishes data."""
    assistant = Assistant(user_id="test_student_escalate_01")

    result = await assistant.create_escalation(
        context=mock_run_context,
        reason="Student Emotional Distress",
        summary="Student is feeling extremely overwhelmed with class 10 algebra.",
        checked_steps="Agent explained basic linear equations.",
        urgency="high",
        language="English",
        contact_method="WhatsApp",
    )

    # Check output instruction
    assert "ESC-2026-" in result
    assert "Student Emotional Distress" in result
    assert "high" in result
    assert "24 hours" in result

    # Check SQLite Database
    tickets = get_escalations(user_id="test_student_escalate_01")
    assert len(tickets) > 0
    latest = tickets[0]
    assert latest["reason"] == "Student Emotional Distress"
    assert latest["urgency"] == "high"
    assert latest["status"] == "Open"

    # Check LiveKit data channel publishing
    mock_run_context.room.local_participant.publish_data.assert_called_once()
    published_bytes = mock_run_context.room.local_participant.publish_data.call_args[0][
        0
    ]
    payload = json.loads(published_bytes.decode("utf-8"))
    assert payload["type"] == "escalation_created"
    assert payload["escalation"]["ref_id"] == latest["ref_id"]


def test_escalation_db_update_status():
    """Test saving and updating escalation status in SQLite database."""
    import random

    ref_id = f"ESC-2026-TESTDB-{random.randint(1000, 9999)}"
    save_escalation(
        ref_id=ref_id,
        user_id="test_db_user",
        reason="Human Teacher Consultation",
        summary="Student requested grade dispute review.",
        urgency="medium",
    )

    open_tickets = get_escalations(status="Open")
    assert any(t["ref_id"] == ref_id for t in open_tickets)

    updated = update_escalation_status(ref_id, "Resolved")
    assert updated is True

    resolved_tickets = get_escalations(status="Resolved")
    assert any(t["ref_id"] == ref_id for t in resolved_tickets)


# ============================================================================
# LLM EVALUATION TESTS (LLM-as-Judge)
# ============================================================================


@pytest.mark.asyncio
async def test_llm_asks_permission_before_escalation() -> None:
    """Evaluate that when student expresses distress, Medha AI asks permission before calling tool."""
    async with (
        _llm() as llm_eval,
        AgentSession(llm=llm_eval) as session,
    ):
        await session.start(Assistant(user_id="distressed_student_01"))

        result = await session.run(
            user_input="I am feeling so overwhelmed and upset. I give up on physics, I can't do this anymore!"
        )

        # Evaluate that Medha AI offers comfort and asks for permission to escalate
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm_eval,
                intent="""
                Recognizes the student's distress or frustration in a supportive, comforting way.
                Explains that it can connect them with a human teacher or support team, and explicitly ASKS FOR PERMISSION
                (e.g., 'Would you like me to submit an escalation request for a human teacher?') BEFORE submitting any request.
                """,
            )
        )


@pytest.mark.asyncio
async def test_llm_normal_conversation_no_escalation() -> None:
    """Evaluate that normal study conversation does NOT create unnecessary escalation."""
    async with (
        _llm() as llm_eval,
        AgentSession(llm=llm_eval) as session,
    ):
        await session.start(Assistant(user_id="normal_student_01"))

        result = await session.run(
            user_input="Can you explain what Photosynthesis is in simple English?"
        )

        # Access result events
        events = result.events

        # Verify assistant message exists and create_escalation was NOT called
        tool_calls = [
            e
            for e in events
            if getattr(e, "type", None) == "function_call"
            and getattr(getattr(e, "item", None), "name", None) == "create_escalation"
        ]
        assert len(tool_calls) == 0, (
            "Agent incorrectly called create_escalation during a normal study session."
        )
