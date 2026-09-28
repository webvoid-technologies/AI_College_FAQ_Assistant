<p align="center">
  <img src="https://www.webvoidtechnologies.com/webvoid_logo_tm.png" alt="Webvoid Technologies" width="220">
</p>

<h1 align="center">MJRCET AI Assistant</h1>

<p align="center">
  An AI-powered chatbot that answers questions about MJRCET — courses, admissions, fees, facilities, placements, contacts, and more.
</p>

---

## Prerequisites

Before you start, make sure you have:

| Requirement | Version | How to check |
|---|---|---|
| Python | 3.9 or higher | `python3 --version` |
| pip | Latest | `pip3 --version` |
| Groq API Key | — | Get a free key at [console.groq.com/keys](https://console.groq.com/keys) |

---

## Step-by-Step Setup

### Step 1 — Navigate to the project folder

```bash
cd AI_COLLAGE_Assistant
```

### Step 2 — Create a virtual environment

```bash
python3 -m venv venv
```

### Step 3 — Activate the virtual environment

**macOS / Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

> This installs Flask, Groq SDK, ChromaDB, Sentence Transformers, and other required packages. It may take a few minutes on the first run.

### Step 5 — Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Open `.env` in any editor and paste your Groq API key:

```env
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=openai/gpt-oss-120b
TEMPERATURE=0.7
MAX_TOKENS=1024
CHROMA_PERSIST_DIRECTORY=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
FLASK_ENV=development
FLASK_DEBUG=True
```

### Step 6 — Collect college data

```bash
python -m app.scraper
```

This scrapes pages from the college website and saves them to `data/scraped_data.json`. It takes a few minutes.

### Step 7 — Build the knowledge base

```bash
python -m app.knowledge_base
```

This creates embeddings from the scraped data and stores them in the `chroma_db/` folder.

> **Note:** Steps 6 and 7 are required only on the first run, or whenever you want to refresh the data.

### Step 8 — Start the server

```bash
python -m app.main
```

You should see:

```
============================================================
MJRCET AI FAQ Assistant - Backend Server
============================================================
✓ LLM Handler initialized successfully
✓ Ready to serve requests!
Server starting on http://localhost:5000
```

### Step 9 — Open the application

Open your browser and go to:

```
http://localhost:5000
```

Start chatting! Try questions like:

- "What courses are offered in the CSE department?"
- "Tell me about admission requirements"
- "What is the fee structure?"
- "How can I contact the college?"
- "Tell me about placements"

---

## Quick Start (after first-time setup)

Once the initial setup is done, running the app takes just two commands:

```bash
cd AI_COLLAGE_Assistant
source venv/bin/activate        # venv\Scripts\activate on Windows
python -m app.main
```

Then open `http://localhost:5000`.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `GROQ_API_KEY not found` | Make sure `.env` exists in the project root and contains a valid key starting with `gsk_` |
| `ModuleNotFoundError: No module named 'app'` | Run the server as `python -m app.main` from the project root folder |
| `model_decommissioned` error | Update `GROQ_MODEL` in `.env` to a currently available model |
| No answers / empty knowledge base | Run `python -m app.scraper` then `python -m app.knowledge_base` |
| Port 5000 already in use | Stop the other process using that port, or edit the port in `app/main.py` |
| Scraper errors | Check your internet connection and that mjrcet.org is reachable |

---

## Project Structure

```
AI_COLLAGE_Assistant/
├── app/
│   ├── main.py            # Server & routes
│   ├── scraper.py         # Data collection
│   ├── knowledge_base.py  # Vector database
│   ├── llm_handler.py     # AI response generation
│   ├── config.py          # Settings
│   └── templates/
│       └── index.html     # Chat interface
├── data/                  # Scraped data (generated)
│   └── scraped_data.json
├── chroma_db/             # Knowledge base (generated)
├── .env                   # Your configuration (generated)
├── .env.example           # Configuration template
├── requirements.txt       # Python dependencies
├── README.md              # Setup guide (this file)
└── PROJECT_REPORT.md      # Full project report data
```

---

## Support

For questions or issues, contact:

**Email:** [studentprogram@webvoidtechnologies.com](mailto:studentprogram@webvoidtechnologies.com)

---

<p align="center">
  <sub>Developed by <b>Webvoid Technologies</b></sub>
</p>
