# 🎙️ Medha AI – India's AI Voice Learning Companion

> Built for **10 Days of Voice Agents – VoiceForBharat Edition** by Murf AI

Medha AI is an AI-powered voice learning companion designed to make education more interactive, engaging, and accessible through natural voice conversations.

This project is being developed under the **Learning & Literacy** track of the VoiceForBharat Challenge.

---

## 📚 Problem Statement

Many students lack access to personalized and interactive learning support whenever they need it. Traditional learning methods are often text-heavy and do not provide real-time guidance.

Medha AI aims to solve this by enabling students to learn through natural voice conversations powered by AI.

---

## 🚀 Day 1 Progress

✅ Successfully set up the Voice Agent

✅ Integrated Murf Falcon Text-to-Speech

✅ Configured LiveKit for real-time voice communication

✅ Configured Speech-to-Text

✅ Integrated Gemini as the Language Model

✅ Successfully completed end-to-end voice conversations

---

## ✨ Planned Features

- 📖 Explain difficult concepts
- 📝 Generate quizzes
- 🗣 Spoken English practice
- 📚 Story reading
- 🌍 Regional language learning
- 🎯 Personalized learning experience
- 📊 Learning progress tracking
- 🎤 Natural voice interaction

---

## 🛠 Tech Stack

### Frontend

- Next.js
- React
- Tailwind CSS

### Backend

- Python
- LiveKit Agents

### AI & Voice

- Murf Falcon (Text-to-Speech)
- Deepgram (Speech-to-Text)
- Google Gemini

### Infrastructure

- LiveKit Cloud

---

## 📂 Project Structure

```
murf-livekit-starter
│
├── backend
│   ├── src
│   └── tests
│
├── frontend
│   ├── app
│   ├── components
│   ├── hooks
│   └── lib
│
└── README.md
```

---

## ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/MuraliAkula04/murf-livekit-starter.git
```

Move into the project

```bash
cd murf-livekit-starter
```

Install backend dependencies

```bash
cd backend
uv sync
```

Install frontend dependencies

```bash
cd ../frontend
pnpm install
```

Configure environment variables using the provided `.env.example` files.

Run the application

```bash
./start_app.ps1
```

or

```bash
cd backend
uv run python src/agent.py dev
```

and

```bash
cd frontend
pnpm dev
```

---

## 🎯 Challenge

This project is part of the **10 Days of Voice Agents – VoiceForBharat Edition** by **Murf AI**.

Track:
**Learning & Literacy**

---

## 📅 Roadmap

### ✅ Day 5 – The Tools

- 🌐 **Real Domain Data Lookup**: Integrated `lookup_educational_concept` to query live Wikipedia educational summaries & factual data.
- 📝 **Practice Exercise Fetcher**: Integrated `fetch_practice_exercise` to pull live quiz questions by subject and level from an Open Quiz API.
- 🔗 **Tool Chaining**: Automatically chains with Day 4 persistent user memory — if a student requests practice questions without specifying a level, the agent reuses their stored learning level without asking again.
- 🔊 **Out-Loud Failure Handling**: Implemented 5-second network timeouts with explicit instructions for Medha AI to inform the student out loud about connection issues before falling back cleanly.
- 🕒 **Timestamp Reporting**: All fetched tool responses include `as_of_date` timestamps so Medha AI states when the live data was retrieved.
- 🖥️ **UI Data Push**: Emits real-time JSON data payloads over LiveKit room data channels for visual UI display.

### ✅ Day 6 – Make it Real (Outbound Calls & Opt-Out)

- 📞 **Outbound SIP Integration**: Added SIP dispatch support for automated daily practice and review calls.
- 🗣️ **Standardized Outbound Greeting**: Implemented a mandatory 3-part greeting identifying Medha AI, stating the purpose of the scheduled daily study session, and providing opt-out instructions.
- 🛑 **Outbound Opt-Out Tool**: Built `unsubscribe_outbound_calls` tool to persist caller opt-out status in SQLite database and gracefully stop automated daily calls.

### ✅ Day 7 – Know When to Ask for Human Help

- 🚨 **Defined Escalation Triggers**: Configured Medha AI to recognize student emotional distress (*"I give up"*, *"I can't do this anymore"*) and explicit human teacher consultation / grade dispute requests.
- ✋ **Permission Flow (*Ask Before Sharing*)**: Enforced rule where Medha AI must explain what details will be sent and receive explicit verbal consent before creating any human ticket.
- 🔒 **PII Scrubbing**: Built `sanitize_pii` utility to automatically redact sensitive information (passwords, OTPs, PINs, bank accounts, card numbers) from request summaries.
- 🎫 **Reference ID & Honest ETA**: Generates unique ticket reference IDs (e.g. `ESC-2026-5197`) and recites clear, honest next steps without false promises of instant replies.
- 📊 **Human Escalation Dashboard**: Built real-time Next.js UI dashboard (`/api/escalations` + LiveKit room data channel) to track, filter, and resolve open escalation tickets.
- 🧪 **Automated & LLM-Judged Test Suite**: Written 16 comprehensive unit & LLM-as-judge tests in `pytest` verifying both escalation and normal session paths.

### ✅ Day 9 – Hand Off to a Specialist Agent

- 🧮 **Dedicated Specialist Agent (`MathsSpecialist`)**: Built a focused mathematics practice specialist with specific instructions, step-by-step problem breakdown tools (`solve_math_step_by_step`), and mental math calculation tricks (`generate_mental_math_trick`).
- 🔄 **Dynamic Agent Handoff Tool (`hand_off_to_maths_specialist`)**: Equips Medha AI with seamless session switching via `context.session.update_agent(MathsSpecialist)`.
- 🗣️ **Out-Loud Announcement**: Medha AI explicitly informs the student out loud (*"I will connect you to our Maths Practice Specialist right now!"*) prior to executing handoff.
- 🤝 **Seamless Context & Round-Trip Handback**: Preserves full conversation history so students do not repeat themselves, and provides `hand_off_to_main_agent` to return to Medha AI when math work finishes or topic changes.
- 📡 **Real-Time UI Telemetry**: Emits `agent_handoff` room data channel payloads to visually notify frontend interfaces of active agent transitions.
- 🧪 **Comprehensive Evaluation Suite**: Added 4 unit & LLM-as-judge tests in `tests/test_handoff.py` validating both normal routing and specialist handoff paths.

---

## 🤝 Acknowledgements

- Murf AI
- LiveKit
- Deepgram
- Google Gemini

---

## 📧 Contact

**Murali Akula**

GitHub: https://github.com/MuraliAkula04

LinkedIn: *(Add your LinkedIn profile link here)*

---

⭐ This project is actively being developed as part of the **10 Days of Voice Agents – VoiceForBharat Edition** challenge.
