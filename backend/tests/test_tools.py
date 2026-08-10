import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from agent import Assistant
from memory import init_database, save_user

# Ensure database is initialized
init_database()


@pytest.fixture
def mock_run_context():
    context = AsyncMock()
    # Mock room and local_participant for UI publish_data testing
    context.room = AsyncMock()
    context.room.local_participant = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_lookup_educational_concept_success(mock_run_context):
    """Test lookup_educational_concept successfully fetches topic summary and includes timestamp."""
    assistant = Assistant(user_id="test_user_tools")

    # Call lookup_educational_concept for Photosynthesis
    result = await assistant.lookup_educational_concept(
        context=mock_run_context,
        topic="Photosynthesis",
    )

    assert "Photosynthesis" in result
    assert "as_of_date" in result or "Fetched on" in result or "2026" in result
    assert "Data source: Wikipedia" in result

    # Verify publish_data was called to push data to UI
    mock_run_context.room.local_participant.publish_data.assert_called_once()
    published_bytes = mock_run_context.room.local_participant.publish_data.call_args[0][
        0
    ]
    payload = json.loads(published_bytes.decode("utf-8"))
    assert payload["type"] == "educational_concept"
    assert "Photosynthesis" in payload["title"]


@pytest.mark.asyncio
async def test_lookup_educational_concept_timeout_failure(mock_run_context):
    """Test lookup_educational_concept handles timeout gracefully and returns out-loud failure instructions."""
    assistant = Assistant(user_id="test_user_tools")

    # Mock httpx.AsyncClient.get to raise TimeoutException
    with patch(
        "httpx.AsyncClient.get",
        side_effect=httpx.TimeoutException("Connection timed out"),
    ):
        result = await assistant.lookup_educational_concept(
            context=mock_run_context,
            topic="Quantum Physics",
        )

        assert "ONLINE SEARCH FAILED" in result or "TIMED OUT" in result
        assert "out loud" in result.lower()


@pytest.mark.asyncio
async def test_fetch_practice_exercise_explicit_level(mock_run_context):
    """Test fetch_practice_exercise with an explicit grade/difficulty level."""
    assistant = Assistant(user_id="test_user_tools")

    result = await assistant.fetch_practice_exercise(
        context=mock_run_context,
        subject="Mathematics",
        level="Class 10",
    )

    assert "Mathematics" in result
    assert "Class 10" in result
    assert "Question" in result or "Exercise" in result
    assert "Fetched on" in result or "2026" in result

    # Verify publish_data pushed exercise data to UI
    mock_run_context.room.local_participant.publish_data.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_practice_exercise_tool_chaining(mock_run_context):
    """Test fetch_practice_exercise automatically chains with Day 4 user memory level when level is None."""
    user_id = "test_chained_user_99"

    # Save caller memory with current_level="Class 10 Trigonometry"
    save_user(
        user_id=user_id,
        name="Anand",
        current_level="Class 10 Trigonometry",
    )

    assistant = Assistant(user_id=user_id)

    # Call fetch_practice_exercise WITHOUT passing level parameter
    result = await assistant.fetch_practice_exercise(
        context=mock_run_context,
        subject="Trigonometry",
        level=None,
    )

    # Tool should automatically retrieve stored memory level "Class 10 Trigonometry"
    assert "Class 10 Trigonometry" in result
    assert "Trigonometry" in result
