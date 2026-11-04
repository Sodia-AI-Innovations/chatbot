# RAG Chatbot

A multi-tenant, personalised RAG chatbot platform. Businesses upload their own documents or point the bot at their website, and get a chatbot (embeddable as a widget) that answers only from that data.

## Features

**Phase 1**
- Upload PDF / DOCX documents and chat with them (chunking, embeddings, similarity search)
- Grounded answers via a configurable LLM (Gemini by default)

**Phase 2**
- Per-site chatbots with API keys (create, rotate, delete) and per-site documents
- Embeddable chat widget served from `/widget.js`
- Ingest from URLs, with a site crawler
- Product loader for catalog-style data
- Usage tracking and an admin dashboard (users, chatbots, usage charts)

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Remix (Vite), React |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL (pgvector) |
| LLM / embeddings | Gemini via LangChain |

## Project structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/        # routes: chat, documents, sites, widget, admin, health
│   │   ├── core/       # config, db, errors, logging
│   │   ├── loaders/    # pdf/docx, url, crawler, product loaders
│   │   ├── models/     # pydantic / ORM models
│   │   ├── prompts/    # RAG prompt
│   │   └── services/   # rag, llm, embedding, document, usage
│   ├── requirements.txt
│   └── .env.example
├── frontend/           # Remix app (chat UI + admin dashboard)
├── evaluation/         # RAG evaluation dataset and runner
└── docs/
```

## Getting started

### Prerequisites
- Python 3.10+
- Node 20+
- PostgreSQL with a database named `ragdb` (and the `pgvector` extension if used)
- A Gemini API key

### Backend (port 8000)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then fill in API keys and the database URL
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend (port 5173)

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open http://localhost:5173.

## Configuration

Set these in `backend/.env` (see `.env.example` for the full list):

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY` | Chat model |
| `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY` | Embedding model |
| `VECTOR_DB_URL` | PostgreSQL connection string |
| `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K`, `SIMILARITY_THRESHOLD` | Retrieval tuning |
| `MAX_FILE_SIZE_MB` | Upload limit |
| `CORS_ORIGINS` | Allowed frontend origin(s) |

Frontend (`frontend/.env`):

```
VITE_API_URL=http://localhost:8000
API_URL=http://localhost:8000
```

## API overview

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/chat` | Ask a question |
| POST | `/documents/upload`, `/documents/url` | Add a document |
| GET / DELETE | `/documents`, `/documents/{id}` | List / delete documents |
| POST / GET / DELETE | `/sites`, `/sites/{id}` | Manage site chatbots |
| POST | `/sites/{id}/rotate` | Rotate a site key |
| POST / GET / DELETE | `/sites/{id}/documents` | Site-scoped documents |
| POST | `/widget/chat` | Chat endpoint used by the embedded widget |
| GET | `/widget.js` | Embeddable widget script |
| GET / POST | `/admin/overview`, `/admin/users`, `/admin/chatbots/{id}` | Admin dashboard data |

See `/docs` for the exact request and response schemas.


