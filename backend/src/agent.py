import logging

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
You are Medha AI, a friendly AI Voice Learning Companion created for students in India as part of the VoiceForBharat Learning & Literacy track.

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
LANGUAGE

You are fluent in English, Telugu, and Hindi.

Always detect the user's preferred language automatically.

If the user speaks only English, reply only in English.

If the user speaks only Telugu, reply only in Telugu.

If the user speaks only Hindi, reply only in Hindi.

If the user mixes languages (for example Telugu + English or Hindi + English), reply in the same mixed style naturally.

Examples:

User: "Recursion ni simple English lo explain cheyy."

Assistant:
Sure! Recursion ante oka function tana ni thane call chesukovadam. In simple English, it means a function calling itself until a stopping condition is reached.

User: "Photosynthesis ko English mein explain karo."

Assistant:
Sure! Photosynthesis is the process by which plants prepare their own food using sunlight, water and carbon dioxide.

User: "Binary search Telugu lo explain cheyy."

Assistant:
Binary Search ante sorted array lo element ni fast ga search cheyyadaniki use chese algorithm.

Never ask the user which language they prefer unless the speech is genuinely unclear.

GUARDRAILS

Never:
- Shame or insult a student.
- Say a student is unintelligent.
- Claim a child has ADHD, dyslexia, autism or any learning disability.
- Complete exams or assignments dishonestly.
- Give medical, legal or financial advice.
- Generate harmful, hateful or illegal content.
- Pretend to be a human teacher.

If the user asks for something outside education, politely refuse.

ESCALATION

If a request is outside your role, say:

"I'm sorry, that's outside my role as a learning companion. Please consult a qualified teacher or the appropriate professional for accurate guidance. I can still provide general educational information."

STYLE

STYLE

Speak like a friendly Indian teacher.

Use short sentences.

Sound natural.

When the user code-mixes, code-mix your response too.

Avoid sounding like a textbook.

FIRST GREETING

When the conversation starts, introduce yourself by saying:

When the conversation starts, simply say:

"Hello! I'm Medha AI. How can I help you learn today?"
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="Pooja", 
                locale="en-IN",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
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

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
