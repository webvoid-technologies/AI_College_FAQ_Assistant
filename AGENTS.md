# Project Configuration for AI Agents

This file contains project-specific information for AI coding assistants.

## Project Overview

**Name:** AI College FAQ Assistant for MJRCET  
**Type:** Educational AI Chatbot Application  
**Stack:** Flask (serves UI + API) + Groq (LLM) + ChromaDB (Vector DB)  
**Purpose:** Answer questions about MJRCET using RAG architecture

## Tech Stack

- **Framework:** Flask 3.0
- **LLM:** Groq API (`openai/gpt-oss-120b`)
- **Vector DB:** ChromaDB 0.4.22
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **Scraping:** BeautifulSoup4
- **UI:** Jinja template + Tailwind CSS (CDN) + marked.js
- **Language:** Python 3.9+

## Project Structure

```
app/
├── main.py           - Flask server, routes, serves chat UI
├── config.py         - Configuration management (.env loader)
├── scraper.py        - Web scraper for mjrcet.org
├── knowledge_base.py - ChromaDB vector database
├── llm_handler.py    - Groq LLM integration + system prompt
└── templates/
    └── index.html    - Chat interface (single-page, Tailwind CDN)
data/scraped_data.json - Scraped corpus (generated)
chroma_db/             - Vector store (generated)
.env                   - Secrets/config (gitignored)
venv/                  - Python virtual environment
```

## Commands

```bash
# Setup (from project root)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # add GROQ_API_KEY

# Data collection (first run or refresh)
python -m app.scraper          # Scrape website → data/scraped_data.json
python -m app.knowledge_base   # Build vector DB → chroma_db/

# Run
python -m app.main             # Server on port 5000, UI at /
```

IMPORTANT: Always run with `python -m app.main` from the project root — `python app/main.py` fails on imports.

## Environment Variables

**.env:**
```env
GROQ_API_KEY=gsk_xxx           # Required: Groq API key
GROQ_MODEL=openai/gpt-oss-120b # Must be a model the key has access to
TEMPERATURE=0.7
MAX_TOKENS=1024
CHROMA_PERSIST_DIRECTORY=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## API Endpoints

- `GET /` - Chat web interface (HTML)
- `GET /api/health` - Health check
- `POST /api/chat` - Main chat endpoint `{message, history[]}`
- `GET /api/stats` - Knowledge base statistics
- `POST /api/search` - Direct semantic search `{query, n_results}`
- `POST /api/refresh-knowledge` - Re-scrape and re-index

## Notes for AI Assistants

- Activate venv (`source venv/bin/activate`) or use `./venv/bin/python` directly
- `httpx==0.27.2` is pinned in requirements.txt — groq 0.4.1 breaks on httpx>=0.28
- Groq model IDs change over time; verify available models via `GET https://api.groq.com/openai/v1/models`
- Scraped data only contains mjrcet.org content; PDFs are indexed as link stubs, not parsed
- The chat UI must NOT show inline source citations in answer text — sources render separately below the message
- Rebuilding the KB deletes and recreates the `mjrcet_knowledge` collection; restart the server afterwards (LLMHandler holds a stale collection handle)
- Contact-intent queries auto-include contact.php via a `where` metadata filter in llm_handler.py
- Flask runs in debug mode — it auto-reloads on .py changes; template edits need only a browser refresh

## Verification

```bash
curl http://localhost:5000/api/health          # status: healthy, document_count > 0
curl -X POST http://localhost:5000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Who is the principal?"}'     # should return a sourced answer
```
