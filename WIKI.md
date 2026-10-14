# 📚 Multi-Document RAG Service — Project Wiki

Welcome to the **Multi-Document RAG Service** technical documentation and system wiki. This guide covers the end-to-end architecture, ingestion pipeline, vector retrieval algorithms, REST API contracts, UI components, and production cloud deployment.

---

## 📑 Table of Contents

- [1. System Overview](#1-system-overview)
- [2. High-Level Architecture](#2-high-level-architecture)
- [3. Deep-Dive Pipelines](#3-deep-dive-pipelines)
  - [3.1 Document Ingestion & Vector Indexing](#31-document-ingestion--vector-indexing)
  - [3.2 Semantic Retrieval & Grounded Generation](#32-semantic-retrieval--grounded-generation)
- [4. Technology Stack](#4-technology-stack)
- [5. REST API Specification](#5-rest-api-specification)
  - [5.1 Standardized Error Envelope](#51-standardized-error-envelope)
  - [5.2 API Endpoints Reference](#52-api-endpoints-reference)
- [6. Frontend Architecture & UI Features](#6-frontend-architecture--ui-features)
- [7. Local Development Quickstart](#7-local-development-quickstart)
- [8. Production Cloud Deployment](#8-production-cloud-deployment)
  - [8.1 Backend on Render](#81-backend-on-render)
  - [8.2 Frontend on Vercel](#82-frontend-on-vercel)
  - [8.3 Keep-Alive Cron Monitor](#83-keep-alive-cron-monitor)
- [9. Configuration & Environment Variables](#9-configuration--environment-variables)
- [10. CI/CD & Testing Strategy](#10-cicd--testing-strategy)
- [11. FAQ & Troubleshooting](#11-faq--troubleshooting)

---

## 1. System Overview

The **Multi-Document RAG Service Platform** is a production-ready, AI-driven knowledge retrieval application. It allows users to upload enterprise documents (PDF, DOCX, TXT) and ask natural-language questions, receiving strictly grounded answers with verifiable source citations.

### Key Capabilities
- **Multi-Format Ingestion:** Robust text extraction from `.pdf`, `.docx`, and `.txt` files with page-number awareness.
- **Deterministic Token Chunking:** Overlapping token chunks (800–1200 tokens, 150 overlap) with unicode normalization.
- **High-Performance Vector Storage:** Fast similarity search powered by Qdrant with thread-safe file locking.
- **Grounded Answer Synthesis:** Powered by Google Gemini (`gemini-3.5-flash-lite`) with automated cascading failover (`gemini-3.6-flash` → `gemini-3.7-flash`).
- **Interactive Citation Tracking:** UI highlights exact source chunks, page numbers, and cosine similarity scores.
- **Strict Tenant & User Isolation:** All vector queries enforce `user_id` filtering at the database index level.

---

## 2. High-Level Architecture

The platform follows a decoupled, service-oriented architecture:

```
[ User Browser / Client ]
           │
           ▼
[ Vercel CDN: React + Vite SPA ]
   │ (REST API via HTTPS / CORS)
   ▼
[ Render Web Service: FastAPI Backend ]
   ├── Authentication & User Scoping
   ├── Ingestion Engine (Validator → Cleaner → Chunker)
   ├── Metadata Store (JSON Persistence)
   ├── Embedding Service (Google Gemini gemini-embedding-001)
   ├── Vector Engine (Qdrant Database: Local / Cloud)
   └── Generation Service (Google Gemini 3.5 Flash Lite)
```

### Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                              │
│                                                                        │
│  File Upload ──► Validation ──► Parser ──► Text Cleaning ──► Chunker   │
│                                                                 │      │
│  Qdrant Vector DB ◄── Idempotent Upsert ◄── Gemini Embeddings ◄─┘      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│                         QUERY PIPELINE                                 │
│                                                                        │
│  User Question ──► Gemini Query Vector ──► Qdrant Semantic Search      │
│                                                       │                │
│  Grounded Response ◄── Gemini LLM ◄── Context Builder ◄─ Filtered Chunks│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Deep-Dive Pipelines

### 3.1 Document Ingestion & Vector Indexing

1. **File Validation (`backend/app/utils/validator.py`):**
   - Validates file size (max 25MB by default).
   - Inspects file extension and verifies binary file signatures (magic bytes) to prevent extension spoofing (e.g. verifying `%PDF-` signature).
2. **Text Parsing (`backend/app/parsers/`):**
   - **PDF Parser:** Uses `pypdf` to extract text while maintaining individual page boundaries.
   - **DOCX Parser:** Uses `python-docx` to extract structural paragraphs and headings.
   - **TXT Parser:** Reads utf-8 text with automatic fallback for ISO-8859/Windows-1252 encodings.
3. **Text Cleaning (`backend/app/utils/cleaner.py`):**
   - Normalizes unicode forms (NFKC).
   - Repairs hyphenated word splits across line breaks.
   - Collapses irregular whitespace and redundant empty newlines.
4. **Token-Aware Chunking (`backend/app/utils/chunker.py`):**
   - Utilizes `tiktoken` (Cl100k tokenizer) to slice documents into target windows of 800–1200 tokens with 150 tokens of overlap.
   - Preserves source metadata (page numbers, chunk index, document ID).
5. **Vector Embedding (`backend/app/services/embedding_service.py`):**
   - Generates 768-dimensional dense vectors using Google Gemini `gemini-embedding-001`.
   - Embeds chunks in concurrency-throttled batches (configurable batch size).
6. **Vector Upsert (`backend/app/services/qdrant_service.py`):**
   - Upserts points into Qdrant using deterministic UUIDs (`uuid.uuid5` based on `chunk_id`) for idempotent re-runs.
   - Embeds payload metadata: `user_id`, `document_id`, `document_name`, `page_number`, `chunk_index`, and raw `text`.

### 3.2 Semantic Retrieval & Grounded Generation

1. **Query Vectorization:** The incoming query is embedded using `gemini-embedding-001`.
2. **Filtered Top-K Search:**
   - Filters by `user_id` (mandatory) and optional `document_id` filter.
   - Retrieves top $K=5$ most similar chunks with cosine similarity $\ge 0.50$.
3. **Context Construction (`backend/app/services/retrieval_service.py`):**
   - Combines retrieved chunks with clear separation markers:
     `[Source: filename.pdf | Page: 3 | Relevance: 0.89]`
4. **Grounded Generation (`backend/app/services/generation_service.py`):**
   - Prompts Gemini with strict system instructions: *Answer solely based on the provided context. If the answer is not contained in the context, explicitly state that.*
   - Automatically attempts failover to secondary model tiers (`3.6-flash`, `3.7-flash`) in the event of transient upstream demand spikes.
   - Attaches structured citation metadata containing document IDs, page references, and similarity scores.

---

## 4. Technology Stack

### Backend
| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | FastAPI | `^0.110.0` | Asynchronous high-performance REST API |
| **Server** | Uvicorn | `^0.28.0` | ASGI production application server |
| **Data Validation** | Pydantic & Pydantic Settings | `^2.0.0` | Strict request/response schemas & configuration |
| **Vector Database** | Qdrant Client | `^1.9.0` | Embedded file-based or managed vector database |
| **LLM & Embeddings** | Google GenAI SDK | `^0.1.1` | Gemini embeddings and answer generation |
| **Document Parsers** | PyPDF, Python-docx | `^4.0.0`, `^1.0.0` | Extraction of raw text and page metadata |
| **Testing & Linting** | Pytest, Pytest-asyncio, Ruff | `^8.0.0`, `^0.5.0` | Unit & integration testing, code style |

### Frontend
| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | React | `^18.3.1` | Reactive user interface components |
| **Build Tool** | Vite | `^5.4.14` | Ultra-fast build and bundling toolchain |
| **Styling** | Tailwind CSS | `^3.4.17` | Premium dark SaaS UI styling system |
| **Icons** | Lucide React | `^0.475.0` | Modern, minimal vector icons |
| **Utilities** | clsx, tailwind-merge | `^2.1.1`, `^3.0.1` | Dynamic conditional CSS class merging |

---

## 5. REST API Specification

### 5.1 Standardized Error Envelope

All API errors return a normalized JSON payload:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File size exceeds maximum allowed limit of 25MB."
  }
}
```

### 5.2 API Endpoints Reference

#### 1. System Health Checks
* **`GET /api/v1/health`** or **`POST /api/v1/health`**
  - **Description:** Verifies service health, database connectivity, and Gemini API readiness.
  - **Response (200 OK):**
    ```json
    {
      "status": "ok",
      "version": "1.0.0",
      "services": {
        "gemini_api_configured": true,
        "qdrant_url": "./qdrant_storage"
      }
    }
    ```
* **`GET /ping`** or **`POST /ping`**
  - **Description:** Lightweight endpoint for external uptime monitors and keep-alive cron jobs.
  - **Response (200 OK):** `{"status": "ok", "message": "pong"}`

#### 2. Document Management
* **`GET /api/v1/documents`**
  - **Headers:** `x-user-id` *(optional, defaults to `default_user`)*
  - **Description:** Returns all uploaded documents and their processing status.
  - **Response (200 OK):**
    ```json
    [
      {
        "document_id": "doc_a1b2c3d4e5f6",
        "user_id": "default_user",
        "document_name": "Annual_Report_2026.pdf",
        "file_type": "pdf",
        "file_size": 1048576,
        "status": "READY",
        "created_at": "2026-09-28T10:00:00Z",
        "updated_at": "2026-09-28T10:00:05Z"
      }
    ]
    ```

* **`POST /api/v1/documents/upload`**
  - **Headers:** `x-user-id` *(optional)*
  - **Body (`multipart/form-data`):** `files`: List of files (PDF, DOCX, TXT)
  - **Response (201 Created):**
    ```json
    [
      {
        "document_id": "doc_a1b2c3d4e5f6",
        "document_name": "Annual_Report_2026.pdf",
        "status": "READY",
        "total_chunks": 18,
        "error": null
      }
    ]
    ```

* **`GET /api/v1/documents/{document_id}`**
  - **Description:** Retrieves details for a specific document.
  - **Response (200 OK):** Returns single document object.
  - **Response (404 Not Found):** `{"error": {"code": "NOT_FOUND", "message": "Document not found."}}`

* **`DELETE /api/v1/documents/{document_id}`**
  - **Description:** Deletes the document metadata and purges all related vector points from Qdrant.
  - **Response (204 No Content):** Empty body.

#### 3. RAG Chat & Retrieval
* **`POST /api/v1/chat`**
  - **Headers:** `x-user-id` *(optional)*
  - **Request Body:**
    ```json
    {
      "question": "What were the primary revenue drivers discussed in the report?",
      "document_id": "doc_a1b2c3d4e5f6",
      "top_k": 5
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "answer": "According to Section 4.2 of the Annual Report, the primary revenue drivers were...",
      "sources": [
        {
          "document": "Annual_Report_2026.pdf",
          "page": 14,
          "score": 0.884,
          "chunk_id": "doc_a1b2c3d4e5f6_chunk_12",
          "text_snippet": "Cloud SaaS offerings grew by 42% year-over-year..."
        }
      ],
      "query": "What were the primary revenue drivers discussed in the report?"
    }
    ```

---

## 6. Frontend Architecture & UI Features

The frontend is an enterprise-grade React Single Page Application (SPA) designed with a minimal, distraction-free layout:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NAVBAR (Logo | Multi-Doc RAG v1.0 | Live Backend Heartbeat Pulse Indicator) │
├───────────────┬───────────────────────────────┬─────────────────────────────┤
│ DOCUMENTS     │ CHAT & CONTEXT                │ CITATION VIEWER             │
│ SIDEBAR       │ STREAM                        │ PANE                        │
│               │                               │                             │
│ • Upload Drop │ • Document Scope Chips        │ • Selected Document Name    │
│   Zone        │ • Chat History                │ • Page Reference            │
│ • Status List │ • Markdown Rendered Response  │ • Highlighted Semantic      │
│   (READY,     │ • Interactive Source Pills    │   Source Chunk              │
│    FAILED)    │ • Chat Input Box              │ • Direct Text Verification  │
│ • Delete File │                               │                             │
└───────────────┴───────────────────────────────┴─────────────────────────────┘
```

### Key UI Capabilities
1. **Live Heartbeat Indicator:** Polls `/api/v1/health` periodically. Displays a glowing green dot when online or an alert if offline.
2. **Context Scope Selector:** Allows users to query across all uploaded documents or restrict the search context to specific documents.
3. **Interactive Citation Pills:** Clicking a citation opens the exact chunk text, relevance score, and source page number in the Document Viewer.
4. **Drag & Drop Uploader:** Instant visual dropzone supporting multi-file uploads with real-time status reporting.

---

## 7. Local Development Quickstart

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- Google Gemini API Key ([Get one free from Google AI Studio](https://aistudio.google.com/app/apikey))

### Step 1: Clone Repository
```bash
git clone https://github.com/Amaanhussain11/DELOITTE-PROJECT-RAG.git
cd DELOITTE-PROJECT-RAG
```

### Step 2: Configure Backend
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Create .env configuration
cp backend/.env.example .env
# Edit .env and paste your GEMINI_API_KEY
```

### Step 3: Run Backend Service
```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### Step 4: Run Frontend Application
```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```
- Local Web Interface: [http://localhost:5173](http://localhost:5173)

---

## 8. Production Cloud Deployment

### 8.1 Backend on Render
- **Repository:** `Amaanhussain11/DELOITTE-PROJECT-RAG`
- **Environment:** Python 3 (or Docker via `backend/Dockerfile`)
- **Root Directory:** *(leave blank / repository root)*
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/api/v1/health`
- **Environment Variables:**
  - `GEMINI_API_KEY`: `<your_gemini_api_key>`
  - `GEMINI_EMBEDDING_MODEL`: `gemini-embedding-001`
  - `GEMINI_GENERATION_MODEL`: `gemini-3.5-flash-lite`
  - `QDRANT_URL`: `./qdrant_storage`
  - `CORS_ORIGINS`: `*` *(or your Vercel domain)*
  - `PYTHONPATH`: `.`

### 8.2 Frontend on Vercel
- **Root Directory:** `frontend`
- **Framework Preset:** `Vite`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variables:**
  - `VITE_API_BASE_URL`: `https://deloitte-project-rag-1.onrender.com/api/v1`
- **Rewrites (`frontend/vercel.json`):** Rewrites `/(.*)` to `/index.html` for client-side routing.

### 8.3 Keep-Alive Cron Monitor
Render instances spin down after 15 minutes of inactivity on free plans. To keep the service responsive:
1. Register a free monitor at [cron-job.org](https://cron-job.org) or [UptimeRobot](https://uptimerobot.com).
2. Set target URL: `https://deloitte-project-rag-1.onrender.com/ping`
3. Method: `POST` or `GET`
4. Schedule: Every 10 minutes.

---

## 9. Configuration & Environment Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | `string` | *(Empty / from env)* | Google Gemini API Key used for embeddings & answer generation |
| `GEMINI_EMBEDDING_MODEL` | `string` | `gemini-embedding-001` | Model used for semantic dense vector representations |
| `GEMINI_GENERATION_MODEL` | `string` | `gemini-3.5-flash-lite` | Primary LLM model for grounded answer synthesis |
| `QDRANT_URL` | `string` | `http://localhost:6333` | Local path (e.g. `./qdrant_storage`), `:memory:`, or cloud cluster URL |
| `QDRANT_API_KEY` | `string` | `None` | Authentication key if using managed Qdrant Cloud |
| `QDRANT_COLLECTION_NAME` | `string` | `rag_documents` | Target collection name in Qdrant |
| `CHUNK_SIZE` | `int` | `1000` | Target token chunk size (800–1200 range) |
| `CHUNK_OVERLAP` | `int` | `150` | Overlap in tokens between consecutive chunks |
| `MAX_FILE_SIZE_MB` | `int` | `25` | Maximum upload file size permitted |
| `DEFAULT_TOP_K` | `int` | `5` | Maximum semantic chunks retrieved per query |
| `SIMILARITY_THRESHOLD` | `float` | `0.5` | Minimum cosine similarity score required for context inclusion |
| `CORS_ORIGINS` | `list[str]` | `["*"]` | Allowed CORS origins (automatically trims trailing slashes) |
| `DEFAULT_USER_ID` | `string` | `default_user` | Default user identification fallback for multi-tenant isolation |

---

## 10. CI/CD & Testing Strategy

### GitHub Actions Workflow (`.github/workflows/ci.yml`)
Runs on every Pull Request and Push to `main` and `Dev`:
1. **Linter & Code Quality:**
   ```bash
   ruff check backend/
   ```
2. **Automated Unit & Integration Test Suite:**
   ```bash
   GEMINI_API_KEY="mock_ci_key" QDRANT_URL=":memory:" pytest -v backend/tests
   ```
   - 30 comprehensive tests covering document parsers, text cleaners, token chunkers, validators, isolation filters, and API route endpoints.
   - Runs 100% offline with zero external network dependencies via mock fixtures.

---

## 11. FAQ & Troubleshooting

#### Q: How is document and tenant isolation guaranteed?
**A:** Every point in Qdrant is upserted with `user_id` as part of its payload. All retrieval queries in `retrieval_service.py` apply a mandatory filter on `user_id`. Chunks belonging to User B will never be retrieved or included in User A's context.

#### Q: How does the application avoid LLM hallucinations?
**A:** The prompt template strictly instructs Gemini to synthesize answers *solely* from the provided context. If the document context does not answer the question, the model explicitly replies that the information is unavailable in the document.

#### Q: What happens if Gemini hits rate limits?
**A:** `generation_service.py` implements an automated cascading fallback tier. If `gemini-3.5-flash-lite` experiences high demand, it cascades to `gemini-3.6-flash`, followed by `gemini-3.7-flash`.

#### Q: Why are my uploads failing with 400?
**A:** Ensure your file is under 25MB and has a valid file extension (`.pdf`, `.docx`, `.txt`). The backend verifies magic byte signatures to prevent corrupt or spoofed files.
