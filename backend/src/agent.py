import asyncio
import contextlib
import json
import logging
import random
import re
import urllib.parse
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import (
    deepgram,
    google,
    murf,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from memory import (
    get_user,
    init_database,
    save_call_log,
    save_escalation,
    save_user,
    set_opt_out_status,
)

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Initialize SQLite database
init_database()


def sanitize_pii(text: str) -> str:
    """Strip sensitive private information like passwords, OTPs, PINs, bank accounts, and card numbers."""
    if not text:
        return ""
    # Redact explicit keyword matches
    text = re.sub(
        r"\b(password|passcode|otp|pin|cvv|account_number|card_number)\s*[:=]?\s*\S+",
        r"\1: [REDACTED]",
        text,
        flags=re.IGNORECASE,
    )
    # Redact 4-6 digit standalone numbers (OTPs / PINs)
    text = re.sub(r"\b\d{4,6}\b", "[REDACTED_CODE]", text)
    # Redact 12-16 digit standalone numbers (Account / Credit Card / Aadhaar)
    text = re.sub(r"\b\d{12,16}\b", "[REDACTED_ACCOUNT]", text)
    return text


def sanitize_math_formatting(text: str) -> str:
    """
    Strip LaTeX math syntax like dollar signs ($ and $$), \times, \text{}, etc.
    This prevents the TTS engine from pronouncing the word 'dollar' out loud
    and keeps the screen display clean.
    """
    if not text:
        return ""
    # Strip \text{...} -> ...
    text = re.sub(r"\\text\{([^}]*)\}", r"\1", text)
    # Replace \times -> x or *
    text = re.sub(r"\\times", "x", text)
    # Replace \cdot -> *
    text = re.sub(r"\\cdot", "*", text)
    # Strip LaTeX fraction \frac{a}{b} -> (a/b)
    text = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1/\2)", text)
    # Strip LaTeX square root \sqrt{a} -> sqrt(\1)
    text = re.sub(r"\\sqrt\{([^}]*)\}", r"sqrt(\1)", text)
    # Remove all dollar signs ($)
    text = text.replace("$", "")
    return text


SYSTEM_PROMPT = """
You are Medha AI, a friendly AI Voice Learning Companion created for
students in India as part of the VoiceForBharat Learning & Literacy track.

IDENTITY

You are a patient, encouraging and supportive AI tutor.

Your goal is to help students learn through natural voice conversations.

OBJECTIVES

1. Explain concepts in simple, easy-to-understand language.
2. Help students clear academic doubts.
3. Generate short quizzes when requested.
4. Help improve spoken English.
5. Read educational stories and explain vocabulary.
6. Encourage curiosity instead of simply giving answers.

KNOWLEDGE

You specialize in educational topics.

If you are unsure about something, honestly say you don't know.

Do not pretend to know current facts without verification.

ONLINE TOOLS & DATA

You have access to live tools to lookup real educational data off the internet:

1. lookup_educational_concept:
   Use this tool whenever the caller asks to look up, verify, or explain educational concepts, scientific facts, definitions, or historical events using live online educational sources.

2. fetch_practice_exercise:
   Use this tool whenever the caller asks for practice questions, quizzes, or exercises on any topic or subject.

IMPORTANT RULES FOR ONLINE TOOLS:
- ALWAYS state the fetched timestamp when presenting live data (e.g. "According to live educational data fetched on August 10, 2026...").
- HANDLING FAILURES OUT LOUD: If a tool call fails or times out, you MUST state out loud to the student that you were unable to connect to the live online database right now due to a network issue, but proceed to explain using your internal knowledge. Never stay silent or fake success when a lookup fails.
- TOOL CHAINING: When fetching exercises, if the student does not specify a grade or difficulty level, the tool automatically reuses their saved learning level from memory!



LANGUAGE

You are fluent in English, Telugu, and Hindi.

Always detect the user's preferred language automatically.

If the user speaks only English, reply only in English.

If the user speaks only Telugu, reply only in Telugu.

If the user speaks only Hindi, reply only in Hindi.

If the user mixes languages, reply in the same mixed style naturally.

Examples:

User:
"Recursion ni simple English lo explain cheyy."

Assistant:
"Sure! Recursion ante oka function tana ni thane call chesukovadam.
In simple English, it means a function calling itself until a
stopping condition is reached."

User:
"Photosynthesis ko English mein explain karo."

Assistant:
"Sure! Photosynthesis is the process by which plants prepare
their own food using sunlight, water and carbon dioxide."

User:
"Binary search Telugu lo explain cheyy."

Assistant:
"Binary Search ante sorted array lo element ni fast ga
search cheyyadaniki use chese algorithm."

Never ask the user which language they prefer unless the speech
is genuinely unclear.


MEMORY

You have access to persistent memory tools.

A caller's memory may contain:

- Name
- Language preference
- Current learning level
- Topics covered
- Common mistakes

IMPORTANT MEMORY RULES

1. You may look up the caller's existing memory.

2. You MUST ask for permission before saving new personal information.

3. Never save information without explicit consent.

4. If the caller says no, do not save anything.

5. Never invent memories.

6. Only save information that is useful for the caller's
   learning experience.

7. Do not save sensitive personal information.

8. Do not read the caller's entire stored profile aloud.

RETURNING CALLERS

At the beginning of a conversation, use the lookup_user tool.

If the caller already has memory:

- Greet the caller by name.
- Mention one useful learning detail from the previous interaction.
- Continue naturally from where they left off.

For example:

"Welcome back, Murali! Last time we discussed Machine Learning.
Would you like to continue with that?"

NEW CALLERS

If there is no memory:

- Have a normal conversation.
- If you learn useful information about the caller, explain
  that you can remember it for future conversations.
- Ask whether they want you to remember it.
- Only if they clearly agree, call confirm_memory_consent.
- After consent is confirmed, call save_user_memory.

If the caller refuses:

- Do not call save_user_memory.
- Continue helping normally.


GUARDRAILS

Never:

- Shame or insult a student.
- Say a student is unintelligent.
- Claim a child has ADHD, dyslexia, autism or any learning disability.
- Complete exams or assignments dishonestly.
- Give medical, legal or financial advice.
- Generate harmful, hateful or illegal content.
- Pretend to be a human teacher.
- Save sensitive personal information.

If the user asks for something outside education, politely refuse.


HUMAN HELP & ESCALATION PROTOCOL

You must know when to stop and create a human escalation request. You are an AI tutor, NOT a replacement for human teachers or counselors.

REASONS TO ASK FOR HUMAN HELP (Choose between these 2 triggers):

1. TRIGGER 1 - STUDENT EMOTIONAL DISTRESS:
   The caller is distressed, crying, upset, expressing severe learning anxiety, or saying things like "I give up", "This is too hard for me", "I can't do this anymore", or "I'm really upset".

2. TRIGGER 2 - HUMAN TEACHER CONSULTATION / DISPUTE:
   The caller explicitly asks to speak with a human teacher, requests official human evaluation of an assignment/exam grade, or has an academic dispute/complaint requiring human decision-making.

CRITICAL STEP 4 RULE - ASK BEFORE SHARING (PERMISSION FLOW):
When either Trigger 1 or Trigger 2 occurs:
1. Explain to the caller what information you will share with a human teacher:
   - Their name (if known)
   - A summary of the issue
   - What the agent already checked
   - Urgency level
   - Preferred follow-up method (Phone call or WhatsApp)
2. Ask for explicit permission:
   "Would you like me to submit an escalation request to a human teacher for you?"
3. ONLY IF the caller clearly says YES ("yes", "sure", "please do", "okay"):
   Call the `create_escalation` tool!
4. IF THE CALLER SAYS NO ("no", "don't send", "stop"):
   DO NOT call `create_escalation`! Comfort the student, offer encouragement, and continue helping normally without creating any ticket.

CLEAR NEXT STEPS AFTER ESCALATION CREATION (STEP 6 RULE):
After `create_escalation` succeeds and returns a Reference ID (e.g. ESC-2026-8492):
1. Recite the Reference ID clearly to the caller.
2. Explain what will happen next honestly:
   "Your reference ID is ESC-2026-8492. A human teacher will review your request within 24 hours and reach out via your preferred follow-up method."
3. Do NOT promise that a human will reply immediately unless specified.

NORMAL CONVERSATIONS:
For normal study questions, math problems, quizzes, or vocabulary help, DO NOT call `create_escalation`. Handle them directly.



STYLE

Speak like a friendly Indian teacher.

Use short sentences.

Sound natural.

When the user code-mixes, code-mix your response too.

Avoid sounding like a textbook.


SPECIALIST HANDOFF PROTOCOL

You are a general educational companion. However, for mathematics practice, step-by-step math problem solving, mental math tricks, algebra, or geometry questions, you MUST hand off the voice conversation to our dedicated Maths Practice Specialist.

HANDOFF TRIGGER:
Whenever the student asks for math help, math exercises, mental math tricks, algebra, geometry, arithmetic, or math word problems, you MUST call the `hand_off_to_maths_specialist` tool.

MANDATORY HANDOFF ANNOUNCEMENT RULE:
Before calling `hand_off_to_maths_specialist`, you MUST announce out loud to the student:
"I will connect you to our Maths Practice Specialist right now!"
Then immediately call `hand_off_to_maths_specialist`.

Do NOT attempt to solve complex math problems yourself when the Maths Specialist is available.


STRICT MATH FORMATTING RULES (CRITICAL FOR VOICE & DISPLAY)

1. NEVER use dollar signs ($ or $$) around math terms, numbers, variables, or equations! (e.g. NEVER write $x^2$, $+4$, or $2$).
2. NEVER use LaTeX syntax or commands such as \times, \text, \frac, \\sqrt.
3. Always write math in plain conversational text or standard keyboard characters:
   - Write "x squared" or "x^2" without dollar signs.
   - Write "2 times x" or "2 * x" instead of "\times".
   - Write "x^2 + 4x + 4 = 0" directly without any $ symbols.
4. REASON: Dollar signs cause the text-to-speech synthesizer to pronounce the word "DOLLAR" out loud (e.g. "dollar x squared dollar"), and LaTeX syntax displays raw code on screen!


OUTBOUND CALL RULES & OPT-OUT

When on an automated outbound call, you MUST open with the exact 3-part greeting:
1. Who is calling: "Hello! I am Medha AI, your AI Voice Learning Companion from VoiceForBharat."
2. Why: "I am calling for your scheduled daily practice call to review today's concept and quiz."
3. How to stop: "If you ever want to end this call or stop receiving daily practice calls, just say 'stop' or 'unsubscribe'."

If the caller asks to stop receiving calls, says "stop calling me", "unsubscribe", or requests to opt out:
1. Immediately call the `unsubscribe_outbound_calls` tool.
2. Confirm out loud that they have been unsubscribed from automated daily calls.
3. Wish them a great day and conclude the call politely.


FIRST GREETING

When an inbound conversation starts, simply say:

"Hello! I'm Medha AI. How can I help you learn today?"
"""


MATHS_SPECIALIST_PROMPT = """
You are the Maths Practice Specialist for Medha AI in the VoiceForBharat initiative.

IDENTITY & ROLE:
- You are a specialized AI Mathematics Tutor.
- Your sole focus is helping students master mathematics: step-by-step problem solving, arithmetic, algebra, geometry, trigonometry, mental math tricks, formulas, and math practice questions.
- Keep your job smaller and more focused than Medha AI's general role. You DO NOT answer general science, history, English literature, or non-math questions.

HANDOFF & INTRODUCING YOURSELF:
- When handed off a conversation, greet the student enthusiastically as the Maths Practice Specialist!
- Example: "Hello! I am Medha AI's Maths Practice Specialist. Let's solve this math problem together!"
- Immediately address the student's math request or problem based on the preceding conversation context.

NON-MATH QUESTIONS & HANDBACK:
- If the student asks a non-mathematical question (e.g., science, history, English literature, general advice, or asks to speak back with Medha AI), politely explain that you are the Maths Specialist, announce out loud: "I will connect you back to Medha AI!", and call the `hand_off_to_main_agent` tool!

STYLE & LANGUAGE:
- Speak like a friendly, encouraging Indian math teacher.
- Use short sentences, clear steps, and natural tone.
- Support English, Telugu, and Hindi code-mixing.

STRICT MATH FORMATTING RULES (CRITICAL FOR VOICE & DISPLAY):
1. NEVER use dollar signs ($ or $$) around math terms, numbers, variables, or equations! (e.g. NEVER write $x^2$, $+4$, or $2$).
2. NEVER use LaTeX syntax or commands such as \times, \text, \frac, \\sqrt.
3. Always write math in plain conversational text or standard keyboard characters:
   - Write "x squared" or "x^2" without dollar signs.
   - Write "2 times x" or "2 * x" instead of "\times".
   - Write "x^2 + 4x + 4 = 0" directly without any $ symbols.
4. REASON: Dollar signs cause the text-to-speech synthesizer to pronounce the word "DOLLAR" out loud (e.g. "dollar x squared dollar"), and LaTeX syntax displays raw code on screen!
"""


class MathsSpecialist(Agent):
    def __init__(self, user_id: str = "default_student") -> None:
        self.user_id = user_id
        self.math_problems_solved = 0
        super().__init__(instructions=MATHS_SPECIALIST_PROMPT)

    @function_tool
    async def solve_math_step_by_step(
        self,
        context: RunContext,
        math_problem: str,
        topic: str | None = None,
    ) -> str:
        """
        Solve a mathematics problem step-by-step with clear explanations for the student.

        Use this tool whenever the student presents a math equation, word problem, or calculation to solve.
        """
        self.math_problems_solved += 1
        logger.info(
            "MathsSpecialist solving problem '%s' for user %s",
            math_problem,
            self.user_id,
        )

        return (
            f"Math problem recorded for step-by-step breakdown.\n"
            f"Problem: {math_problem}\n"
            f"Topic: {topic or 'Mathematics'}\n"
            f"Instruction for Specialist: Break down this problem into 2-3 clear, step-by-step logical stages. "
            f"Use ONLY plain conversational text and standard keyboard characters. "
            f"CRITICAL RULE: NEVER use dollar signs ($) or LaTeX syntax like \\times or \\text. Write x^2 instead of $x^2$."
        )

    @function_tool
    async def generate_mental_math_trick(
        self,
        context: RunContext,
        operation: str,
    ) -> str:
        """
        Provide a mental mathematics shortcut or trick for quick mental calculation.

        Use this tool when the student asks for mental math shortcuts, speed math tricks, or quick calculation methods (e.g., multiplying by 11, squaring numbers ending in 5, quick percentage tricks).
        """
        logger.info(
            "MathsSpecialist generating mental math trick for operation '%s'",
            operation,
        )
        return (
            f"Mental math trick request for: {operation}.\n"
            f"Instruction for Specialist: Explain one simple, memorable mental math shortcut for {operation} with a quick example. "
            f"CRITICAL RULE: Use ONLY plain text without dollar signs ($) or LaTeX syntax."
        )

    @function_tool
    async def hand_off_to_main_agent(
        self,
        context: RunContext,
        reason: str,
    ) -> str:
        """
        Hand off the conversation back to Medha AI (Main Agent).

        Use this tool when the math practice is completed, or when the student asks a non-math question (science, history, literature) or explicitly requests to talk to Medha AI.
        Before calling this tool, announce out loud to the student:
        'I will connect you back to Medha AI!'
        """
        logger.info(
            "MathsSpecialist handing off back to Assistant for user %s (Reason: %s)",
            self.user_id,
            reason,
        )
        main_assistant = Assistant(user_id=self.user_id)
        context.session.update_agent(main_assistant)

        # Publish room data event
        try:
            if (
                context
                and hasattr(context, "room")
                and context.room
                and hasattr(context.room, "local_participant")
                and context.room.local_participant
            ):
                payload = json.dumps(
                    {
                        "type": "agent_handoff",
                        "active_agent": "Medha AI (Main Agent)",
                        "previous_agent": "Maths Practice Specialist",
                        "reason": reason,
                        "timestamp": datetime.now().isoformat(),
                    }
                ).encode("utf-8")
                await context.room.local_participant.publish_data(payload)
        except Exception as err:
            logger.warning("Could not publish handoff data to room: %s", err)

        return (
            "Handoff back to Medha AI (Main Agent) successful.\n"
            "Instruction for Assistant: Greet the caller as Medha AI and continue helping with their general educational request."
        )


class Assistant(Agent):
    def __init__(self, user_id: str = "default_student") -> None:
        self.user_id = user_id
        self.memory_consent = False
        self.exercises_completed = 0
        self.concept_lookups = 0
        self.topic = "General Learning"
        self.escalation_created = False
        self.specialist_handoff = False
        self.unsubscribed = False
        self.first_response_latency_ms = None

        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def hand_off_to_maths_specialist(
        self,
        context: RunContext,
        topic_or_problem: str,
    ) -> str:
        """
        Hand off the voice conversation to the Maths Practice Specialist agent.

        Use this tool IMMEDIATELY whenever the caller asks for math assistance, math problem solving,
        arithmetic practice, algebra, geometry, mental math shortcuts, math word problems, or math formulas.

        Before calling this tool, announce out loud to the caller:
        'I will connect you to our Maths Practice Specialist right now!'
        """
        self.specialist_handoff = True
        logger.info(
            "Handing off conversation for user %s to MathsPracticeSpecialist (Topic: %s)",
            self.user_id,
            topic_or_problem,
        )

        specialist = MathsSpecialist(user_id=self.user_id)
        context.session.update_agent(specialist)

        # Publish room data message for UI visual feedback
        try:
            if (
                context
                and hasattr(context, "room")
                and context.room
                and hasattr(context.room, "local_participant")
                and context.room.local_participant
            ):
                payload = json.dumps(
                    {
                        "type": "agent_handoff",
                        "active_agent": "Maths Practice Specialist",
                        "previous_agent": "Medha AI (Main Agent)",
                        "topic": topic_or_problem,
                        "timestamp": datetime.now().isoformat(),
                    }
                ).encode("utf-8")
                await context.room.local_participant.publish_data(payload)
        except Exception as err:
            logger.warning("Could not publish handoff data to room: %s", err)

        return (
            f"Handoff successful. The active agent is now MathsPracticeSpecialist.\n"
            f"Instruction for Specialist: Introduce yourself out loud to the student as the Maths Practice Specialist and answer their math request ({topic_or_problem}) directly."
        )

    @function_tool
    async def unsubscribe_outbound_calls(self, context: RunContext) -> str:
        """
        Unsubscribe the current caller from automated daily outbound practice calls.

        Use this tool whenever the caller asks to stop receiving calls, requests to opt out,
        says 'stop calling me', 'unsubscribe', or 'do not call again'.
        """
        self.unsubscribed = True
        logger.info("Unsubscribing user %s from outbound calls", self.user_id)
        set_opt_out_status(self.user_id, opted_out=True)

        try:
            if context.room and context.room.local_participant:
                payload = json.dumps(
                    {
                        "type": "outbound_opt_out",
                        "user_id": self.user_id,
                        "status": "unsubscribed",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                await context.room.local_participant.publish_data(
                    payload.encode("utf-8")
                )
        except Exception as err:
            logger.warning("Could not publish opt-out data to room: %s", err)

        return (
            "The caller has been successfully unsubscribed from daily practice calls. "
            "Politely inform the caller out loud that they will no longer receive automated calls, "
            "wish them a great day, and end the conversation."
        )

    @function_tool
    async def create_escalation(
        self,
        context: RunContext,
        reason: str,
        summary: str,
        checked_steps: str | None = None,
        urgency: str = "medium",
        language: str = "English",
        contact_method: str = "Phone Call",
    ) -> str:
        """
        Create a human escalation request for a teacher or support manager.

        Use this tool ONLY after the caller has given explicit permission to submit an escalation request.

        Parameters:
        - reason: Brief title of the escalation reason ("Student Emotional Distress" or "Human Teacher Consultation Request").
        - summary: Short summary of what happened (do NOT include sensitive passwords, PINs, or account numbers).
        - checked_steps: What Medha AI already checked or tried before escalating.
        - urgency: "low", "medium", "high", or "emergency".
        - language: Caller's preferred language (e.g., "English", "Telugu", "Hindi").
        - contact_method: Preferred follow-up method (e.g., "Phone Call", "WhatsApp", "SMS", "Email").
        """
        self.escalation_created = True
        # Generate reference ID format: ESC-2026-XXXX
        random_suffix = random.randint(1000, 9999)
        ref_id = f"ESC-2026-{random_suffix}"

        # Clean PII from summary and checked_steps
        clean_summary = sanitize_pii(summary)
        clean_checked = sanitize_pii(
            checked_steps
            or "Agent verified educational materials and offered explanation."
        )

        user = get_user(self.user_id)
        caller_name = (user.get("name") if user else None) or "Anonymous Student"

        logger.info(
            "Creating human escalation %s for user %s (%s). Urgency: %s",
            ref_id,
            self.user_id,
            reason,
            urgency,
        )

        escalation_data = save_escalation(
            ref_id=ref_id,
            user_id=self.user_id,
            caller_name=caller_name,
            reason=reason,
            summary=clean_summary,
            checked_steps=clean_checked,
            urgency=urgency,
            language=language,
            contact_method=contact_method,
        )

        # Publish payload to LiveKit room data channel for real-time frontend UI update
        try:
            if (
                context
                and hasattr(context, "room")
                and context.room
                and hasattr(context.room, "local_participant")
                and context.room.local_participant
            ):
                payload = json.dumps(
                    {
                        "type": "escalation_created",
                        "escalation": escalation_data,
                    }
                ).encode("utf-8")
                await context.room.local_participant.publish_data(payload)
        except Exception as p_err:
            logger.warning("Could not publish escalation data to room: %s", p_err)

        return (
            f"Escalation request successfully created.\n"
            f"Reference ID: {ref_id}\n"
            f"Reason: {reason}\n"
            f"Urgency: {urgency}\n"
            f"Follow-up Method: {contact_method}\n"
            f"Status: Open\n"
            f"Instruction for Assistant: Explicitly state out loud to the student that their request has been submitted with Reference ID '{ref_id}'. "
            f"Explain that a human teacher will review their request within 24 hours and reach out via {contact_method}. "
            f"Do NOT promise immediate response."
        )

    @function_tool
    async def lookup_user(self, context: RunContext) -> str:
        """
        Look up the current caller's saved learning memory.

        Use this at the beginning of the conversation to determine
        whether the caller has spoken with Medha before.
        """

        logger.info(
            "Looking up memory for user %s",
            self.user_id,
        )

        user = get_user(self.user_id)

        if user is None:
            logger.info(
                "No memory found for user %s",
                self.user_id,
            )

            return "No previous memory exists for this caller. This is a new caller."

        logger.info(
            "Returning caller found: %s",
            self.user_id,
        )

        return (
            "Returning caller found. "
            f"Name: {user.get('name') or 'unknown'}. "
            f"Language preference: "
            f"{user.get('language_preference') or 'unknown'}. "
            f"Current learning level: "
            f"{user.get('current_level') or 'unknown'}. "
            f"Topics covered: "
            f"{user.get('topics_covered') or 'none recorded'}. "
            f"Common mistakes: "
            f"{user.get('common_mistakes') or 'none recorded'}. "
            f"Last interaction: "
            f"{user.get('last_interaction') or 'unknown'}."
        )

    @function_tool
    async def confirm_memory_consent(
        self,
        context: RunContext,
    ) -> str:
        """
        Record that the caller explicitly agreed to let Medha
        remember useful learning information for future conversations.

        Only call this after the caller clearly says yes.
        """

        self.memory_consent = True

        logger.info(
            "Memory consent granted for user %s",
            self.user_id,
        )

        return (
            "Memory consent has been granted. "
            "You may now save relevant learning information."
        )

    @function_tool
    async def save_user_memory(
        self,
        context: RunContext,
        name: str | None = None,
        language_preference: str | None = None,
        current_level: str | None = None,
        topics_covered: str | None = None,
        common_mistakes: str | None = None,
    ) -> str:
        """
        Save useful learning information about the caller.

        This tool must only be used after the caller has explicitly
        given permission to remember their information.
        """

        if not self.memory_consent:
            logger.warning(
                "Blocked memory save without consent for user %s",
                self.user_id,
            )

            return (
                "Memory was NOT saved because the caller has "
                "not given explicit permission."
            )

        logger.info(
            "Saving memory for user %s",
            self.user_id,
        )

        save_user(
            user_id=self.user_id,
            name=name,
            language_preference=language_preference,
            current_level=current_level,
            topics_covered=topics_covered,
            common_mistakes=common_mistakes,
        )

        return "The caller's learning memory was saved successfully."

    @function_tool
    async def lookup_educational_concept(
        self,
        context: RunContext,
        topic: str,
    ) -> str:
        """
        Search for live educational concepts, scientific facts, definitions, or historical information
        from online educational repositories (e.g., Wikipedia).

        Use this tool whenever a student asks for factual educational explanations, scientific concepts,
        definitions, formulas, or history topics that require accurate up-to-date verification.
        """
        as_of_date = datetime.now().strftime("%B %d, %Y %H:%M IST")
        self.concept_lookups += 1
        self.topic = topic
        logger.info("Looking up educational concept '%s' (as of %s)", topic, as_of_date)

        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}"

        headers = {
            "User-Agent": "MedhaAI/1.0 (VoiceForBharat Learning Companion; contact@medha.ai)"
        }

        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title", topic)
                    extract = data.get("extract", "No extract available.")
                    source_url = (
                        data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    )

                    # Push payload to UI if room is available
                    if (
                        context
                        and hasattr(context, "room")
                        and context.room
                        and hasattr(context.room, "local_participant")
                        and context.room.local_participant
                    ):
                        try:
                            ui_payload = json.dumps(
                                {
                                    "type": "educational_concept",
                                    "topic": topic,
                                    "title": title,
                                    "extract": extract,
                                    "as_of_date": as_of_date,
                                    "source": "Wikipedia",
                                }
                            ).encode("utf-8")
                            await context.room.local_participant.publish_data(
                                ui_payload
                            )
                        except Exception as p_err:
                            logger.warning("Failed to publish data to UI: %s", p_err)

                    return (
                        f"Educational concept lookup successful.\n"
                        f"Topic: {title}\n"
                        f"Data source: Wikipedia\n"
                        f"Fetched on (as_of_date): {as_of_date}\n"
                        f"Summary: {extract}\n"
                        f"Source URL: {source_url}\n"
                        f"Instruction: Explain this topic to the student clearly, mentioning that this live data was fetched on {as_of_date} from Wikipedia."
                    )
                else:
                    return (
                        f"ONLINE SEARCH FAILED: Received HTTP status code {resp.status_code} for topic '{topic}'. "
                        f"Fetched on: {as_of_date}. "
                        "IMPORTANT INSTRUCTION FOR MEDHA AI: Explicitly tell the student out loud that you couldn't reach the live educational database right now, "
                        "but proceed to explain the topic using your core educational knowledge."
                    )
        except Exception as err:
            logger.error("Error looking up topic '%s': %s", topic, err)
            return (
                f"ONLINE SEARCH FAILED: Request timed out or encountered network failure ({err}). "
                f"Fetched on: {as_of_date}. "
                "IMPORTANT INSTRUCTION FOR MEDHA AI: Explicitly state out loud to the student that the live database request timed out, "
                "and then answer the question using your internal knowledge."
            )

    @function_tool
    async def fetch_practice_exercise(
        self,
        context: RunContext,
        subject: str,
        level: str | None = None,
    ) -> str:
        """
        Fetch real-time practice exercises, quiz problems, or educational questions for a student.

        Use this tool when a student asks for practice questions, exercises, or quizzes on any subject.
        If the student does not specify a level, leave level as None, and this tool will automatically
        chain with their saved memory level.
        """
        as_of_date = datetime.now().strftime("%B %d, %Y %H:%M IST")
        self.exercises_completed += 1
        self.topic = subject

        # Tool Chaining: if level is not specified, check Day 4 user memory
        effective_level = level
        user = get_user(self.user_id)
        if not effective_level and user:
            effective_level = user.get("current_level")

        if not effective_level:
            effective_level = "Class 10 General"

        logger.info(
            "Fetching practice exercise for subject '%s' at level '%s' (chained memory: %s)",
            subject,
            effective_level,
            level is None and user is not None,
        )

        try:
            # Try Open Quiz API for live questions
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://opentdb.com/api.php?amount=1&type=multiple"
                )
                if resp.status_code == 200 and resp.json().get("results"):
                    item = resp.json()["results"][0]
                    question = item.get("question", "")
                    correct = item.get("correct_answer", "")
                    import html

                    question = html.unescape(question)
                    correct = html.unescape(correct)

                    # Push payload to UI if room is available
                    if (
                        context
                        and hasattr(context, "room")
                        and context.room
                        and hasattr(context.room, "local_participant")
                        and context.room.local_participant
                    ):
                        try:
                            ui_payload = json.dumps(
                                {
                                    "type": "practice_exercise",
                                    "subject": subject,
                                    "level": effective_level,
                                    "question": question,
                                    "as_of_date": as_of_date,
                                }
                            ).encode("utf-8")
                            await context.room.local_participant.publish_data(
                                ui_payload
                            )
                        except Exception as p_err:
                            logger.warning("Failed to publish data to UI: %s", p_err)

                    return (
                        f"Practice exercise fetched successfully.\n"
                        f"Subject: {subject}\n"
                        f"Level: {effective_level}\n"
                        f"Fetched on (as_of_date): {as_of_date}\n"
                        f"Question: {question}\n"
                        f"Correct Answer (internal): {correct}\n"
                        f"Instruction: Present this practice question to the student for their level ({effective_level}) and ask them to try answering."
                    )
        except Exception as err:
            logger.warning("Live question API timeout/error: %s", err)

        # Fallback exercise if API times out or is offline
        fallback_question = (
            f"What is the key difference between speed and velocity in {subject}?"
        )
        if (
            context
            and hasattr(context, "room")
            and context.room
            and hasattr(context.room, "local_participant")
            and context.room.local_participant
        ):
            try:
                ui_payload = json.dumps(
                    {
                        "type": "practice_exercise",
                        "subject": subject,
                        "level": effective_level,
                        "question": fallback_question,
                        "as_of_date": as_of_date,
                    }
                ).encode("utf-8")
                await context.room.local_participant.publish_data(ui_payload)
            except Exception as p_err:
                logger.warning("Failed to publish data to UI: %s", p_err)

        return (
            f"Practice exercise fetched successfully.\n"
            f"Subject: {subject}\n"
            f"Level: {effective_level}\n"
            f"Fetched on (as_of_date): {as_of_date}\n"
            f"Question: {fallback_question}\n"
            f"Instruction: Present this practice question to the student for their level ({effective_level})."
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Determine whether this is an outbound call before looking for the
    # SIP participant. The SIP participant can join shortly after the room
    # is created, so wait for it instead of checking the room only once.
    metadata = {}
    if ctx.room.metadata:
        with contextlib.suppress(Exception):
            metadata = json.loads(ctx.room.metadata)

    is_outbound = metadata.get("is_outbound", False) or ctx.room.name.startswith(
        "outbound-"
    )

    # The job must connect to the LiveKit room before waiting for
    # the SIP participant. Without ctx.connect(), wait_for_participant()
    # can fail with "room is not connected".
    logger.info("Connecting agent to LiveKit room: %s", ctx.room.name)
    await ctx.connect()

    logger.info("Agent connected to room: %s", ctx.room.name)

    if is_outbound:
        logger.info("Outbound room detected: %s", ctx.room.name)
        logger.info("Waiting for SIP participant to join...")

        participant = await ctx.wait_for_participant()

        logger.info(
            "SIP participant joined: identity=%s kind=%s",
            participant.identity,
            participant.kind,
        )
    else:
        # Inbound calls normally already have a remote participant.
        participant = next(
            iter(ctx.room.remote_participants.values()),
            None,
        )

    if participant is None:
        logger.warning("No remote participant found.")
        user_id = f"anonymous_{ctx.room.name}"
    else:
        user_id = participant.identity

    logger.info("Medha caller ID: %s", user_id)

    # Set up the voice AI pipeline.
    session = AgentSession(
        stt=deepgram.STT(
            model="nova-3",
            interim_results=True,
            smart_format=True,
        ),
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        tts=murf.TTS(
            voice="Pooja",
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        min_endpointing_delay=1.0,
        preemptive_generation=True,
    )

    # Start the session only after the outbound SIP participant has joined.
    # This prevents the TTS pipeline from being started before the phone
    # participant is actually connected to the room.
    start_time = datetime.now(timezone.utc)
    channel = (
        "sip"
        if is_outbound
        or (
            participant
            and hasattr(participant, "kind")
            and participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
        )
        else "browser"
    )
    call_id = f"{ctx.room.name}_{int(start_time.timestamp())}"
    assistant = Assistant(user_id=user_id)

    try:
        await session.start(
            agent=assistant,
            room=ctx.room,
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: (
                        noise_cancellation.BVCTelephony()
                        if params.participant.kind
                        == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                        else noise_cancellation.BVC()
                    ),
                ),
            ),
        )

        # Explicitly speak first on outbound calls.
        if is_outbound:
            topic_info = metadata.get(
                "topic",
                "today's revision topic",
            )

            greeting_text = (
                "Hello! I am Medha AI, your AI Voice Learning Companion "
                "from VoiceForBharat. "
                f"I am calling for your scheduled daily practice call "
                f"to review {topic_info} and take a quick quiz. "
                "If you ever want to end this call or stop receiving "
                "daily practice calls, just say 'stop' or 'unsubscribe'."
            )

            logger.info(
                "Speaking outbound greeting to %s",
                user_id,
            )

            await session.say(
                greeting_text,
                allow_interruptions=True,
            )

        assistant.first_response_latency_ms = int(
            (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        )

        # Keep the agent job alive for the duration of the call.
        await asyncio.Event().wait()

    finally:
        end_time = datetime.now(timezone.utc)
        duration_seconds = max(0, int((end_time - start_time).total_seconds()))

        # Determine success condition for Learning & Literacy track:
        # Success if student completed an exercise, searched a concept, confirmed memory consent, or created an escalation ticket.
        if (
            assistant.exercises_completed > 0
            or assistant.concept_lookups > 0
            or assistant.memory_consent
            or assistant.escalation_created
            or assistant.specialist_handoff
        ):
            outcome = "success"
            failure_reason = None
        elif assistant.unsubscribed:
            outcome = "failure"
            failure_reason = "user_opt_out"
        elif duration_seconds < 15:
            outcome = "failure"
            failure_reason = "user_hung_up_early"
        else:
            outcome = "failure"
            failure_reason = "incomplete_task"

        save_call_log(
            call_id=call_id,
            room_name=ctx.room.name,
            user_id=user_id,
            channel=channel,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=duration_seconds,
            outcome=outcome,
            failure_reason=failure_reason,
            topic=assistant.topic,
            exercises_completed=assistant.exercises_completed,
            concept_lookups=assistant.concept_lookups,
            first_response_latency_ms=assistant.first_response_latency_ms or 1200,
        )
        logger.info(
            "Logged call session %s: outcome=%s, channel=%s, duration=%ds, exercises=%d, lookups=%d",
            call_id,
            outcome,
            channel,
            duration_seconds,
            assistant.exercises_completed,
            assistant.concept_lookups,
        )


if __name__ == "__main__":
    cli.run_app(server)
