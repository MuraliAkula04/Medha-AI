from unittest.mock import AsyncMock

import pytest

from agent import Assistant
from memory import get_user, init_database, save_user, set_opt_out_status
from outbound_call import CallOutcome, OutboundCallManager, RetryRule

init_database()


@pytest.fixture
def mock_run_context():
    context = AsyncMock()
    context.room = AsyncMock()
    context.room.local_participant = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_unsubscribe_outbound_calls_tool(mock_run_context):
    """Test that unsubscribe_outbound_calls updates memory opted_out flag to True."""
    user_id = "test_opt_out_user_123"
    save_user(user_id=user_id, name="Sunita", opted_out=False)

    assistant = Assistant(user_id=user_id)
    result = await assistant.unsubscribe_outbound_calls(context=mock_run_context)

    assert "unsubscribed" in result.lower()
    user_state = get_user(user_id)
    assert user_state is not None
    assert user_state["opted_out"] is True


def test_retry_rules_outcomes():
    """Test outcome handling and retry rules for Day 6 advanced requirements."""
    # Terminal outcomes: Completed, Opt-out
    should_retry, next_time, rationale = RetryRule.calculate_next_attempt(
        CallOutcome.COMPLETED, 0
    )
    assert not should_retry
    assert next_time is None

    should_retry, next_time, rationale = RetryRule.calculate_next_attempt(
        CallOutcome.OPT_OUT, 0
    )
    assert not should_retry
    assert next_time is None

    # Voicemail outcome: Left message, no retry today
    should_retry, next_time, rationale = RetryRule.calculate_next_attempt(
        CallOutcome.VOICEMAIL, 0
    )
    assert not should_retry
    assert "Answering machine" in rationale

    # Immediate hangup outcome: Do not retry today
    should_retry, next_time, rationale = RetryRule.calculate_next_attempt(
        CallOutcome.IMMEDIATE_HANGUP, 0
    )
    assert not should_retry
    assert "hung up immediately" in rationale

    # No answer: Retry with exponential backoff (retry count 0 -> retry 1)
    should_retry, next_time, rationale = RetryRule.calculate_next_attempt(
        CallOutcome.NO_ANSWER, 0
    )
    assert should_retry
    assert next_time is not None
    assert "No answer" in rationale

    # Max retries reached
    should_retry, next_time, rationale = RetryRule.calculate_next_attempt(
        CallOutcome.NO_ANSWER, 3
    )
    assert not should_retry
    assert "Maximum retry attempts" in rationale


def test_outbound_manager_opt_out_suppression():
    """Test that OutboundCallManager suppresses calls to users who have opted out."""
    user_id = "opted_out_user_99"
    set_opt_out_status(user_id, opted_out=True)

    manager = OutboundCallManager()
    log_entry = manager.place_outbound_call(
        to_number="+919876543210",
        user_id=user_id,
        user_name="Ramesh",
        topic="Math Quiz",
    )

    assert log_entry["outcome"] == CallOutcome.OPT_OUT_SUPPRESSED.value
    assert not log_entry["should_retry"]
    assert "suppressed" in log_entry["notes"].lower()


def test_outbound_manager_place_call():
    """Test outbound call placement with simulated completed outcome."""
    user_id = "active_student_44"
    save_user(user_id=user_id, name="Priya", opted_out=False)

    manager = OutboundCallManager()
    log_entry = manager.place_outbound_call(
        to_number="+919876543210",
        user_id=user_id,
        user_name="Priya",
        topic="Cell Structure",
        simulate_outcome="completed",
    )

    assert log_entry["outcome"] == CallOutcome.COMPLETED.value
    assert log_entry["metadata"]["is_outbound"] is True
    assert "Medha AI" in log_entry["metadata"]["opening_greeting"]
    assert "stop" in log_entry["metadata"]["opening_greeting"].lower()
