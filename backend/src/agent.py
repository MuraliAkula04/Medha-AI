import asyncio
import contextlib
import json
import logging
import urllib.parse
from datetime import datetime

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

from memory import get_user, init_database, save_user, set_opt_out_status

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Initialize SQLite database
init_database()


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


ESCALATION

If a request is outside your role, say:

"I'm sorry, that's outside my role as a learning companion.
Please consult a qualified teacher or the appropriate professional
for accurate guidance. I can still provide general educational
information."


STYLE

Speak like a friendly Indian teacher.

Use short sentences.

Sound natural.

When the user code-mixes, code-mix your response too.

Avoid sounding like a textbook.


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


class Assistant(Agent):
    def __init__(self, user_id: str = "default_student") -> None:
        self.user_id = user_id
        self.memory_consent = False

        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def unsubscribe_outbound_calls(self, context: RunContext) -> str:
        """
        Unsubscribe the current caller from automated daily outbound practice calls.

        Use this tool whenever the caller asks to stop receiving calls, requests to opt out,
        says 'stop calling me', 'unsubscribe', or 'do not call again'.
        """
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

    # Connect to the LiveKit room first so the participant
    # information is available.
    await ctx.connect()

    # Get the caller's persistent LiveKit participant identity.
    participant = next(
        iter(ctx.room.remote_participants.values()),
        None,
    )

    if participant is None:
        logger.warning("No remote participant found.")

        user_id = f"anonymous_{ctx.room.name}"

    else:
        user_id = participant.identity

    logger.info(
        "Medha caller ID: %s",
        user_id,
    )

    # Set up the voice AI pipeline.
    session = AgentSession(
        # Speech-to-text
        stt=deepgram.STT(
            model="nova-3",
        ),
        # Large Language Model
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech
        tts=murf.TTS(
            voice="Pooja",
            locale="en-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # Turn detection
        turn_detection=MultilingualModel(),
        # Voice activity detection
        vad=ctx.proc.userdata["vad"],
        # Generate responses before the user completely finishes
        preemptive_generation=True,
    )

    # Check room metadata or name to determine if this is an outbound call
    metadata = {}
    if ctx.room.metadata:
        with contextlib.suppress(Exception):
            metadata = json.loads(ctx.room.metadata)

    is_outbound = (
        metadata.get("is_outbound", False)
        or ctx.room.name.startswith("outbound-")
        or (
            participant and participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
        )
    )

    # Start the session with the memory-enabled assistant.
    session_task = asyncio.create_task(
        session.start(
            agent=Assistant(
                user_id=user_id,
            ),
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
    )

    # If this is an outbound call, greet the user immediately with the mandatory 3-part greeting
    if is_outbound:
        topic_info = metadata.get("topic", "today's revision topic")
        greeting_text = (
            "Hello! I am Medha AI, your AI Voice Learning Companion from VoiceForBharat. "
            f"I am calling for your scheduled daily practice call to review {topic_info} and take a quick quiz. "
            "If you ever want to end this call or stop receiving daily practice calls, just say 'stop' or 'unsubscribe'."
        )
        # Give session.start a brief moment to finish room binding
        await asyncio.sleep(0.5)
        await session.say(greeting_text)

    await session_task


if __name__ == "__main__":
    cli.run_app(server)
