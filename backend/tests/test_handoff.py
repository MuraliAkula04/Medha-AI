import json
from unittest.mock import AsyncMock

import pytest
from livekit.agents import AgentSession, inference, llm

from agent import Assistant, MathsSpecialist, sanitize_math_formatting
from memory import init_database

# Ensure database is initialized
init_database()


def _llm() -> llm.LLM:
    return inference.LLM(model="google/gemini-2.5-flash")


@pytest.fixture
def mock_run_context():
    context = AsyncMock()
    context.session = AsyncMock()
    context.room = AsyncMock()
    context.room.local_participant = AsyncMock()
    return context


# ============================================================================
# UNIT TESTS
# ============================================================================


def test_sanitize_math_formatting():
    """Test that sanitize_math_formatting strips dollar signs and LaTeX commands."""
    raw = (
        "Look at ($x^2$) and ($+4$). "
        "Does it equal $2 \\times (\\text{first root}) \\times (\\text{second root})$?"
    )
    cleaned = sanitize_math_formatting(raw)
    assert "$" not in cleaned
    assert "\\times" not in cleaned
    assert "\\text" not in cleaned
    assert "(x^2)" in cleaned
    assert "2 x (first root) x (second root)" in cleaned


@pytest.mark.asyncio
async def test_hand_off_to_maths_specialist_tool_execution(mock_run_context):
    """Test Assistant.hand_off_to_maths_specialist updates active agent to MathsSpecialist and publishes data."""
    assistant = Assistant(user_id="test_student_handoff_01")

    result = await assistant.hand_off_to_maths_specialist(
        context=mock_run_context,
        topic_or_problem="Class 10 Algebra Linear Equations",
    )

    # Verify return message instructions
    assert "Handoff successful" in result
    assert "MathsPracticeSpecialist" in result
    assert assistant.specialist_handoff is True

    # Verify session update_agent was called with MathsSpecialist
    mock_run_context.session.update_agent.assert_called_once()
    passed_agent = mock_run_context.session.update_agent.call_args[0][0]
    assert isinstance(passed_agent, MathsSpecialist)
    assert passed_agent.user_id == "test_student_handoff_01"

    # Verify LiveKit data channel publishing for UI feedback
    mock_run_context.room.local_participant.publish_data.assert_called_once()
    published_bytes = mock_run_context.room.local_participant.publish_data.call_args[0][
        0
    ]
    payload = json.loads(published_bytes.decode("utf-8"))
    assert payload["type"] == "agent_handoff"
    assert payload["active_agent"] == "Maths Practice Specialist"
    assert payload["topic"] == "Class 10 Algebra Linear Equations"


@pytest.mark.asyncio
async def test_maths_specialist_tools_and_handback(mock_run_context):
    """Test MathsSpecialist tools (solve_math, mental_math_trick) and handback to Assistant."""
    specialist = MathsSpecialist(user_id="test_math_student_02")

    # 1. Test solve_math_step_by_step
    solve_res = await specialist.solve_math_step_by_step(
        context=mock_run_context,
        math_problem="Solve 2x + 5 = 15",
        topic="Algebra",
    )
    assert "Solve 2x + 5 = 15" in solve_res
    assert specialist.math_problems_solved == 1

    # 2. Test generate_mental_math_trick
    trick_res = await specialist.generate_mental_math_trick(
        context=mock_run_context,
        operation="Multiply 2 digit numbers by 11",
    )
    assert "Multiply 2 digit numbers by 11" in trick_res

    # 3. Test hand_off_to_main_agent (handback)
    handback_res = await specialist.hand_off_to_main_agent(
        context=mock_run_context,
        reason="Completed math session, student wants general science revision",
    )
    assert "Handoff back to Medha AI" in handback_res

    # Verify session update_agent called with Assistant instance
    mock_run_context.session.update_agent.assert_called_once()
    passed_agent = mock_run_context.session.update_agent.call_args[0][0]
    assert isinstance(passed_agent, Assistant)


# ============================================================================
# LLM EVALUATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_llm_eval_normal_question_stays_with_main_agent():
    """Test that a general educational question stays with Assistant and does NOT trigger handoff."""
    async with (
        _llm() as llm_eval,
        AgentSession(llm=llm_eval) as session,
    ):
        await session.start(Assistant(user_id="test_normal_student"))

        result = await session.run(
            user_input="Can you explain what photosynthesis is in simple words?"
        )

        # Inspect function call names emitted during the turn
        func_names = [
            ev.item.name
            for ev in result.events
            if hasattr(ev, "item") and hasattr(ev.item, "name") and ev.item.name
        ]

        # Verify handoff tool was NOT called for normal question
        assert "hand_off_to_maths_specialist" not in func_names

        # Verify Assistant generated a chat message response
        messages = [
            ev.item.content
            for ev in result.events
            if type(ev).__name__ == "ChatMessageEvent"
            and hasattr(ev, "item")
            and hasattr(ev.item, "content")
        ]
        assert len(messages) > 0


@pytest.mark.asyncio
async def test_llm_eval_math_question_triggers_handoff():
    """Test that a math practice question causes Assistant to announce handoff and call hand_off_to_maths_specialist."""
    async with (
        _llm() as llm_eval,
        AgentSession(llm=llm_eval) as session,
    ):
        await session.start(Assistant(user_id="test_math_student"))

        result = await session.run(
            user_input="I need help practicing quadratic equations and solving 2x^2 + 4x - 6 = 0."
        )

        # 1. Check hand_off_to_maths_specialist tool call was made
        func_names = [
            ev.item.name
            for ev in result.events
            if hasattr(ev, "item") and hasattr(ev.item, "name") and ev.item.name
        ]
        assert "hand_off_to_maths_specialist" in func_names

        # 2. Check out-loud handoff announcement content
        all_messages = []
        for ev in result.events:
            if (
                type(ev).__name__ == "ChatMessageEvent"
                and hasattr(ev, "item")
                and hasattr(ev.item, "content")
            ):
                if isinstance(ev.item.content, list):
                    all_messages.extend([str(c) for c in ev.item.content])
                elif isinstance(ev.item.content, str):
                    all_messages.append(ev.item.content)

        combined_text = " ".join(all_messages).lower()
        assert (
            "maths practice specialist" in combined_text or "connect" in combined_text
        )

        # 3. Check AgentHandoffEvent switched session to MathsSpecialist
        handoff_events = [
            ev for ev in result.events if type(ev).__name__ == "AgentHandoffEvent"
        ]
        assert len(handoff_events) > 0
        assert isinstance(handoff_events[0].new_agent, MathsSpecialist)
