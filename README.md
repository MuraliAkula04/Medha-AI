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

### 🔜 Upcoming

- Premium UI & Visual Cards
- Learning Dashboard
- Progress Analytics

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
