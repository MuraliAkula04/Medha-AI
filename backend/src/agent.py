import logging

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
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import (
    murf,
    silero,
    google,
    deepgram,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from memory import get_user, save_user, init_database


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


FIRST GREETING

When the conversation starts, simply say:

"Hello! I'm Medha AI. How can I help you learn today?"
"""


class Assistant(Agent):
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        self.memory_consent = False

        super().__init__(
            instructions=SYSTEM_PROMPT
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

            return (
                "No previous memory exists for this caller. "
                "This is a new caller."
            )

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

        return (
            "The caller's learning memory was saved successfully."
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
        logger.warning(
            "No remote participant found."
        )

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
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        # Turn detection
        turn_detection=MultilingualModel(),

        # Voice activity detection
        vad=ctx.proc.userdata["vad"],

        # Generate responses before the user completely finishes
        preemptive_generation=True,
    )

    # Start the session with the memory-enabled assistant.
    await session.start(
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


if __name__ == "__main__":
    cli.run_app(server)