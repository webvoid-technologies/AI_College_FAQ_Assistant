<p align="center">
  <img src="https://www.webvoidtechnologies.com/webvoid_logo_tm.png" alt="Webvoid Technologies" width="220">
</p>

<h1 align="center">MJRCET AI Assistant</h1>
<h3 align="center">An Intelligent College FAQ Chatbot using Retrieval Augmented Generation</h3>

<p align="center">
  <b>Project Report</b>
</p>

---

## Abstract

The MJRCET AI Assistant is an intelligent chatbot application designed to answer questions about MJRCET college — including courses, admissions, fees, facilities, examinations, placements, and contact information. The system combines web scraping, vector databases, and large language models (LLMs) to deliver accurate, context-aware, conversational answers grounded in real college data.

Rather than relying on generic LLM knowledge (which may be outdated or hallucinated), the assistant uses a **Retrieval Augmented Generation (RAG)** approach: it scrapes the official college website, indexes the content into a vector database, retrieves the most relevant information for each user question, and generates a natural-language answer using that retrieved context. Every response is backed by real data from the college website, with source links provided for verification.

The application is built as a single Flask server that provides both the REST API and the web-based chat interface.

---

## 1. Introduction

### 1.1 Problem Statement

Students, parents, and prospective applicants frequently need information about a college — courses offered, admission procedures, fee structures, hostel facilities, placements, and contact details. Finding this information on a college website can be difficult: content is spread across many pages, site navigation varies, and the information may be buried in PDFs or tables. Phone calls and office visits are time-consuming and limited to working hours.

There is a need for an automated, always-available assistant that can answer college-related questions instantly and accurately, in natural language.

### 1.2 Proposed Solution

The MJRCET AI Assistant is a chatbot that:

1. Collects information automatically from the official college website (mjrcet.org)
2. Organizes that information into a searchable knowledge base
3. Understands user questions asked in plain English
4. Finds the most relevant information and generates a clear, conversational answer
5. Cites sources so users can verify the information

### 1.3 Objectives

- Provide instant, 24/7 answers to college-related questions
- Ensure answers are grounded in official college data, not generic AI guesses
- Support natural, conversational interaction (including follow-up questions)
- Present contact details (phone numbers, emails) when users need human assistance
- Maintain source transparency for every answer

### 1.4 Scope

- Answers questions about departments, courses, admissions, fees, scholarships, facilities, examinations, syllabus, placements, faculty contacts, and campus life
- English language support
- Web-based interface accessible from any browser
- Knowledge base refreshable on demand as the college website changes

---

## 2. Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Programming Language | Python 3.9+ | Core application logic |
| Web Framework | Flask 3.0 | REST API + web page serving |
| LLM Provider | Groq API | Fast LLM inference (openai/gpt-oss-120b) |
| Vector Database | ChromaDB 0.4 | Storing and searching embeddings |
| Embedding Model | Sentence Transformers (all-MiniLM-L6-v2) | Converting text to vectors |
| Web Scraping | BeautifulSoup4 + Requests + lxml | Extracting data from mjrcet.org |
| Frontend | HTML5 + Tailwind CSS + JavaScript | Chat user interface |
| Markdown Rendering | marked.js | Rich formatted answers |
| Configuration | python-dotenv | Environment variable management |

### Why These Technologies?

- **Groq** — provides extremely fast LLM inference (hundreds of tokens/second) with a free tier, making real-time chat feasible at zero cost
- **ChromaDB** — lightweight, embedded vector database that requires no separate server; data persists on disk
- **all-MiniLM-L6-v2** — a compact (~90MB) embedding model that runs locally on CPU, balancing speed and accuracy
- **Flask** — minimal, well-documented, and serves both the API and the UI in one process
- **Tailwind CSS** — utility-first styling for a clean, responsive, modern interface without a build step

### 2.1 Development Tools Used

| Tool | Purpose |
|---|---|
| Visual Studio Code | Code editor / IDE for development |
| Python `venv` + `pip` | Isolated environment and dependency management |
| Git | Version control |
| curl / Browser DevTools | API testing and debugging |
| Groq Console (console.groq.com) | API key management and model selection |
| Chrome / Safari | UI testing and preview |
| macOS Terminal | Running servers, scraper, and indexing scripts |

### 2.2 System Requirements

**Software Requirements**
- OS: Windows 10+ / macOS / Linux
- Python 3.9 or higher
- Modern web browser (Chrome, Edge, Firefox, Safari)
- Internet connection (for scraping, embedding model download, and Groq API calls)

**Hardware Requirements**
- Processor: Any modern dual-core CPU or better
- RAM: 4 GB minimum (8 GB recommended — embedding model loads into memory)
- Storage: ~2 GB free space (dependencies, embedding model, vector DB)

### 2.3 Feasibility Study

- **Technical feasibility** — All components (Flask, ChromaDB, Groq API, Sentence Transformers) are mature, documented, and run on a standard laptop. No GPU or paid infrastructure is required.
- **Economic feasibility** — The entire stack is free: open-source Python libraries, Groq's free API tier, and local embedding models. Hosting can be done on free tiers of Render/Railway.
- **Operational feasibility** — End users need only a browser. Maintenance is limited to periodic re-scraping via a single endpoint (`/api/refresh-knowledge`).

---

## 3. System Design

### 3.1 Architecture Overview

The application follows a **single-server, three-layer architecture**: a presentation layer (browser UI), an application layer (Flask API + RAG logic), and a data layer (ChromaDB vector store + scraped JSON). Everything runs inside one Flask process, so there is no separate frontend server or database server to manage.

```
┌─────────────────────────────────────────────────────────┐
│              PRESENTATION LAYER (Browser)                │
│   index.html — chat UI, markdown rendering, source links │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (fetch /api/chat)
                           ▼
┌─────────────────────────────────────────────────────────┐
│               APPLICATION LAYER (Flask)                  │
│                                                          │
│   main.py          llm_handler.py                        │
│   API routes  ──►  context builder ──► Groq LLM API      │
│                    system prompt                         │
│                          │                               │
│   scraper.py             ▼                               │
│   crawl site ──►  knowledge_base.py                      │
│   (one-time)      embed + retrieve chunks                │
└──────────┬───────────────────────────┬───────────────────┘
           │                           │
           ▼                           ▼
┌──────────────────────┐   ┌──────────────────────────────┐
│      DATA LAYER      │   │      EXTERNAL SERVICES       │
│  scraped_data.json   │   │  mjrcet.org (source data)    │
│  chroma_db/ (vectors)│   │  api.groq.com (LLM inference)│
└──────────────────────┘   └──────────────────────────────┘
```

**How the layers interact:**

1. **Presentation layer** — `index.html` is served by Flask itself. It renders the chat interface, sends user questions to `/api/chat` as JSON, renders the markdown answer, and displays source links below each answer.
2. **Application layer** — `main.py` exposes REST endpoints. On a chat request, `llm_handler.py` queries `knowledge_base.py` for relevant text chunks, assembles a prompt (system prompt + retrieved context + chat history + question), and calls the Groq API. The answer and its source metadata are returned as JSON.
3. **Data layer** — `scraped_data.json` is the raw corpus produced by the scraper; `chroma_db/` is the persistent vector index built from it. The scraper runs offline (first setup or manual refresh), never during a chat request.
4. **External services** — mjrcet.org supplies the raw data (scraped once, cached locally); Groq supplies LLM inference over HTTPS.

### 3.2 RAG Pipeline (How a Question Gets Answered)

RAG (Retrieval Augmented Generation) means the LLM does not answer from memory — it answers from retrieved college data, which is what keeps responses accurate and source-backed.

```
User Question
      │
      ▼
[1] EMBED — question → 384-dim vector (all-MiniLM-L6-v2)
      │
      ▼
[2] RETRIEVE — ChromaDB similarity search → top chunks
      │        (+ contact-page boost for contact questions)
      ▼
[3] AUGMENT — chunks assembled into context block
      │        system prompt + context + history + question
      ▼
[4] GENERATE — Groq LLM (openai/gpt-oss-120b) writes the answer
      │
      ▼
[5] RESPOND — answer text + top-3 source links → UI
```

**Why RAG instead of fine-tuning or plain LLM?**

| Approach | Why not chosen |
|---|---|
| Plain LLM prompt | Hallucinates college details; no way to cite sources |
| Fine-tuning a model | Expensive, slow to update, needs training data |
| **RAG (chosen)** | Cheap, always current (re-scrape to update), every answer traceable to a real page |

### 3.3 Module Description

| Module | File | Responsibility |
|---|---|---|
| Web Server | `app/main.py` | Flask routes, serves UI, exposes REST API |
| Scraper | `app/scraper.py` | Crawls mjrcet.org, extracts text/tables, follows links, skips non-HTML files, saves JSON |
| Knowledge Base | `app/knowledge_base.py` | Chunks text, generates embeddings, stores/searches ChromaDB |
| LLM Handler | `app/llm_handler.py` | System prompt, context building, contact-intent detection, Groq API calls |
| Configuration | `app/config.py` | Loads `.env` settings |
| Chat UI | `app/templates/index.html` | Single-page chat interface (Tailwind + marked.js) |

---

## 4. Implementation Details

### 4.1 Data Collection (Web Scraping)

The scraper (`scraper.py`) performs a breadth-first crawl starting from the college homepage:

- **Priority pages first**: admissions, departments, placements, fees/scholarships, hostels, transport, library, contacts, NIRF, and administration pages are queued before general link-following
- **Domain restriction**: only `mjrcet.org` links are followed
- **Content-type filtering**: images, CSS, JS, and other binary files are skipped (by URL extension *and* HTTP Content-Type); PDFs are recorded as reference documents so the assistant can point users to official forms and syllabi
- **Content extraction**: headings (`h1`–`h6`) become `##` sections; paragraphs, list items, and table cells are extracted with whitespace normalized; nav/script/style elements are removed
- **Politeness**: a delay between requests avoids overloading the site

Output: `data/scraped_data.json` — a list of `{url, title, content}` documents. In a typical run, ~66 pages plus ~40 PDF references are collected.

### 4.2 Knowledge Base (Indexing)

`knowledge_base.py` processes the scraped JSON:

1. **Chunking** — each document is split into overlapping chunks (500 words, 50-word overlap) so context fits in the LLM window while preserving continuity
2. **Filtering** — chunks shorter than 50 characters are dropped as noise
3. **Embedding** — each chunk is encoded by `all-MiniLM-L6-v2` into a 384-dimensional vector
4. **Storage** — vectors + text + metadata (title, URL) are stored in a persistent ChromaDB collection (`mjrcet_knowledge`); the collection is rebuilt from scratch on each re-index to avoid duplicates

Result: ~100 searchable chunks covering the whole site.

### 4.3 Query Answering (RAG)

`llm_handler.py` handles each chat request:

1. The user message is embedded and ChromaDB returns the top-5 most similar chunks
2. **Contact-intent boost**: if the question contains words like *contact, phone, email, reach, help desk*, the main contact page is explicitly added to the context (short department help-desk chunks otherwise outrank it)
3. A context block is assembled from the retrieved chunks
4. The **system prompt** instructs the model to answer directly, use markdown formatting, never mention sources/context/URLs in the answer body, always surface phone numbers when relevant, and suggest contacting the office when data is missing
5. The last 4 history messages are included for follow-up question support
6. Groq's `openai/gpt-oss-120b` model generates the answer (temperature 0.7, max 1024 tokens)
7. The response + top-3 source links are returned to the UI; the UI renders sources separately below the answer

### 4.4 User Interface

`templates/index.html` is a single-page application styled with Tailwind CSS:

- Glassmorphic header with online-status indicator
- Chat bubbles: gradient avatars, message tails, fade-in animation
- Typing indicator (bouncing dots) while waiting for the API
- Suggested-question cards that auto-send on click
- Auto-growing textarea input (Enter = send, Shift+Enter = newline)
- Markdown rendering via marked.js (bold, lists, tables)
- Clickable source links under each answer
- Fully responsive (mobile → desktop)

### 4.5 API Specification

| Method | Endpoint | Description | Request | Response |
|---|---|---|---|---|
| GET | `/` | Chat web page | — | HTML |
| GET | `/api/health` | Health check | — | `{status, llm_initialized, knowledge_base}` |
| POST | `/api/chat` | Main chat | `{message, history[]}` | `{response, sources[], model}` |
| POST | `/api/search` | Semantic search | `{query, n_results}` | `{results[], count}` |
| GET | `/api/stats` | KB statistics | — | `{collection_name, document_count, embedding_model}` |
| POST | `/api/refresh-knowledge` | Re-scrape & re-index | — | `{status, stats}` |

### 4.6 Configuration

All tunables live in the project-root `.env`:

| Variable | Purpose | Example |
|---|---|---|
| `GROQ_API_KEY` | Groq API key (required) | `gsk_…` |
| `GROQ_MODEL` | LLM model ID | `openai/gpt-oss-120b` |
| `TEMPERATURE` | Response creativity | `0.7` |
| `MAX_TOKENS` | Max response length | `1024` |
| `CHROMA_PERSIST_DIRECTORY` | Vector DB location | `./chroma_db` |
| `EMBEDDING_MODEL` | Embedding model | `all-MiniLM-L6-v2` |

---

## 5. Testing & Results

### 5.1 Test Scenarios

| # | Query | Result |
|---|---|---|
| 1 | "What courses does the college offer?" | Listed B.Tech departments (CSE, ECE, EEE, Mech, Civil) with syllabus references ✅ |
| 2 | "How can I contact the college?" | Full contact table — Principal, Advisor, Office, Exams, Placements, Library, Transport — with phone + email ✅ |
| 3 | "Who is the principal?" | Correct name returned (Dr. K V N V N Rao) ✅ |
| 4 | "Phone number of CSE department head?" | Correct help-desk number (9444043846) ✅ |
| 5 | "Tell me about placements" | Placement info with source citations ✅ |
| 6 | Health check `/api/health` | `{status: healthy, llm_initialized: true, document_count: 100}` ✅ |

### 5.2 Key Quality Measures

- **Groundedness**: answers cite real scraped chunks; source links displayed per response
- **No hallucinated contact info**: contact queries are backed by the actual contact page
- **Graceful degradation**: when data is missing, the bot says what it knows and points to the office rather than inventing answers
- **Clean output**: no citation markers or raw URLs inside the answer text

### 5.3 Known Limitations

- Answer quality depends on the college website's content — information not published on mjrcet.org (e.g., exact current fee amounts inside PDFs) can't be answered verbatim, though the assistant links the relevant PDF
- PDF contents are referenced by title/URL, not parsed into the knowledge base
- Single-user sessions; chat history is per-browser-tab (not persisted)
- English only

---

## 6. Future Enhancements

- Parse PDF contents into the knowledge base (fees, syllabus details)
- Streaming responses (token-by-token display)
- Persistent chat history and user accounts
- Multi-language support (Telugu, Hindi)
- Voice input/output
- Admin dashboard for monitoring questions and KB freshness
- Automatic scheduled re-scraping of the website
- Mobile app wrapper (PWA)

---

## 7. Conclusion

The MJRCET AI Assistant demonstrates a complete, practical application of modern AI techniques — web scraping, text embeddings, vector search, and retrieval-augmented LLM generation — packaged in a single easy-to-run Flask application. It solves a real problem (instant access to college information), grounds every answer in official data, and is simple to deploy, refresh, and extend.

---

## 8. References

- MJRCET official website — https://www.mjrcet.org/
- Groq API documentation — https://console.groq.com/docs
- ChromaDB documentation — https://docs.trychroma.com/
- Sentence Transformers — https://www.sbert.net/
- Flask documentation — https://flask.palletsprojects.com/
- Tailwind CSS — https://tailwindcss.com/

---

## Appendix — Running the Project

Detailed step-by-step setup instructions are in `README.md`. Summary:

```bash
cd AI_COLLAGE_Assistant
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your GROQ_API_KEY
python -m app.scraper         # collect data (first run only)
python -m app.knowledge_base  # build knowledge base (first run only)
python -m app.main            # start server → http://localhost:5000
```

---

<p align="center">
  <b>Developed by Webvoid Technologies</b><br>
  <a href="mailto:externalprojects@webvoidtechnologies.com">externalprojects@webvoidtechnologies.com</a>
</p>
