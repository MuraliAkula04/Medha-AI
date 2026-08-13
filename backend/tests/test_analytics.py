from datetime import datetime, timezone

import pytest

from memory import (
    get_call_analytics,
    init_database,
    save_call_log,
)


@pytest.fixture(autouse=True)
def setup_db():
    init_database()


def test_save_and_retrieve_call_logs():
    test_id = f"test_call_{int(datetime.now(timezone.utc).timestamp())}"

    # Record a successful call
    log1 = save_call_log(
        call_id=test_id,
        room_name="room_test_1",
        user_id="student_123",
        channel="browser",
        duration_seconds=45,
        outcome="success",
        topic="Photosynthesis",
        exercises_completed=2,
        concept_lookups=1,
        first_response_latency_ms=950,
        caller_name="Test Student",
    )

    assert log1["outcome"] == "success"
    assert log1["exercises_completed"] == 2

    # Fetch analytics
    analytics = get_call_analytics()
    assert analytics["total_calls"] >= 1
    assert analytics["successful_calls"] >= 1
    assert analytics["total_exercises"] >= 2
    assert analytics["total_concept_lookups"] >= 1


def test_failure_path_logging():
    fail_id = f"fail_call_{int(datetime.now(timezone.utc).timestamp())}"

    log2 = save_call_log(
        call_id=fail_id,
        room_name="room_test_2",
        user_id="student_456",
        channel="sip",
        duration_seconds=8,
        outcome="failure",
        failure_reason="user_hung_up_early",
        topic="Math Quiz",
        exercises_completed=0,
        concept_lookups=0,
        first_response_latency_ms=1100,
        caller_name="Anonymous Caller",
    )

    assert log2["outcome"] == "failure"
    assert log2["failure_reason"] == "user_hung_up_early"

    analytics = get_call_analytics()
    assert analytics["failed_calls"] >= 1
    assert "user_hung_up_early" in analytics["failure_types"]
