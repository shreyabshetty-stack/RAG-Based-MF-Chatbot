# Project Implementation Plan: Mutual Fund FAQ Assistant

This document outlines the phase-wise implementation plan for the RAG-based Mutual Fund FAQ Assistant, aligned with the [System Architecture](file:///d:/RAG%20Based%20MF%20Chatbot/architecture.md) and [Project Context](file:///d:/RAG%20Based%20MF%20Chatbot/context.md).

---

## 📅 Roadmap Overview

```
Phase 1: Setup & Data Ingestion ──> Phase 2: Vector DB Indexing ──> Phase 3: RAG Retrieval & LLM Setup
                                                                                  │
Phase 6: Web Interface & API   <── Phase 5: Post-Validation     <── Phase 4: Intent & PII Guardrails
       │
       └──> Phase 7: Verification & Testing ──> Phase 8: Daily Ingestion Scheduler
```

---

## 🛠️ Phase-Wise Breakdown

### Phase 1: Environment Setup & Data Ingestion
**Goal:** Gather raw mutual fund facts from the specified URLs and set up the development environment.

* **Task 1.1:** Setup Python virtual environment (`venv`) and install core dependencies:
  * Backend: `fastapi`, `uvicorn`, `pydantic`
  * Scrapers & Parsers: `beautifulsoup4`, `requests`, `html5lib`
  * AI & DB: `chromadb` (or `faiss-cpu`), `sentence-transformers` (for BGE embedding model), `groq` (Groq API), `python-dotenv`
  * Environment variables: Create `.env` and `.env.example` in the workspace root.
* **Task 1.2:** Implement a scraping script (`scripts/ingest.py`) targeting the [5 HDFC Groww mutual fund URLs](file:///d:/RAG%20Based%20MF%20Chatbot/context.md#l37-l44).
  * Extract: Scheme name, Expense Ratio, Exit Load, Minimum SIP amount, ELSS lock-in (if applicable), Riskometer classification, Benchmark index.
* **Task 1.3:** Store the scraped content locally in structured format (`data/raw_funds.json`) to act as the primary corpus.

---

### Phase 2: Chunking, Embeddings, & Vector Database Setup
**Goal:** Process the corpus, generate embeddings, and build the retrieval database.

* **Task 2.1:** Implement metadata-aware chunking. Split each fund's data into logical chunks (e.g., General Info, Fees & Load, Risk & Returns, How to Download statements) rather than arbitrary text splits.
* **Task 2.2:** Populate metadata tags for each chunk:
  * `fund_name`: e.g., `"HDFC Mid-Cap Opportunities Fund"`
  * `source_url`: e.g., `"https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"`
  * `last_updated`: Date of extraction (e.g., `2026-07-04`).
* **Task 2.3:** Generate embeddings using the BGE model (e.g., `BAAI/bge-small-en-v1.5`) and write chunks to a local ChromaDB collection.

---

### Phase 3: RAG Retrieval & Prompt Engineering
**Goal:** Setup vector retrieval and orchestrate the core LLM question-answering pipeline.

* **Task 3.1:** Create a retrieval service (`services/retriever.py`) supporting hybrid search:
  * Filters chunks to matches based on query terms or fund context.
* **Task 3.2:** Develop the LLM prompts with strict facts-only guidelines:
  ```
  Answer the query using ONLY the provided mutual fund context.
  - Rely only on clear facts. Do not speculate or recommend.
  - Do not exceed 3 sentences.
  - Output exactly one source URL from the context.
  ```
* **Task 3.3:** Connect the retriever to the LLM generation step (`services/generator.py`) using the Groq API (e.g., `llama3-8b-8192` or `llama3-70b-8192` via Groq client).

---

### Phase 4: Intent Classification & PII Guardrails
**Goal:** Add input guardrails to prevent advisory responses and protect PII.

* **Task 4.1:** Build an **Intent Classifier** (`services/classifier.py`) to detect non-factual queries:
  * Flag keywords: *"should I buy"*, *"which is better"*, *"recommend"*, *"growth forecast"*, *"compare"*.
* **Task 4.2:** Implement a **Refusal Handler** that immediately redirects advisory queries to a polite template response containing educational links (e.g., to AMFI or SEBI Investor Education websites).
* **Task 4.3:** Set up a **PII Sanitizer** using regex to identify and strip out sensitive user information (PAN, Aadhaar numbers, phone numbers, email addresses, OTPs) from incoming queries before processing.

---

### Phase 5: Output Validation & Post-Verification
**Goal:** Add programmatic verification of responses to guarantee strict format compliance.

* **Task 5.1:** Create a response validation middleware (`services/validator.py`) to verify LLM outputs:
  * **Sentence Counter:** Verifies the answer is $\le 3$ sentences.
  * **Link Checker:** Counts the number of links in the response (must be exactly 1, matching the target fund's source URL).
  * **Word Filter:** Screens out accidental advisory advice or speculation phrases.
* **Task 5.2:** Auto-inject the updated date footer format: `Last updated from sources: <date>`.
* **Task 5.3:** Set up a fallback generator that retries or formats a safe refusal answer if the validation checks fail.

---

### Phase 6: Minimalist Chat Interface & API Endpoints
**Goal:** Expose endpoints and build a user-friendly UI.

* **Task 6.1:** Set up API controllers using FastAPI:
  * `POST /api/chat`: Accepts user messages, processes them through the guardrail-RAG-validator pipeline, and returns the response.
* **Task 6.2:** Create a clean, minimalist chat interface (`frontend/index.html`, `frontend/style.css`, `frontend/app.js`):
  * **Disclaimer Banner:** Highlight *"Facts-only. No investment advice."*
  * **Welcome Message:** Introduce the tool's objective.
  * **Interactive Examples:** Add buttons for 3 common queries:
    1. *"What is the exit load of HDFC Mid-Cap?"*
    2. *"What is the benchmark of HDFC Large Cap?"*
    3. *"Can you tell me if I should invest in HDFC Flexi Cap?"* (triggers refusal behavior)

---

### Phase 7: Verification & Testing
**Goal:** Verify accuracy, compliance, and UI responsiveness.

* **Task 7.1:** Write unit tests for:
  * Ingestion parser correctness.
  * Guardrail classification (factual vs. advisory queries).
  * PII redaction.
  * Post-validator triggers.
* **Task 7.2:** Prepare a test script executing standard queries, verifying that responses match the source page facts and adhere strictly to the 3-sentence limits.

---

### Phase 8: Daily Ingestion Scheduler (GitHub Actions)
**Goal:** Automate raw data scraping and database updates daily using a GitHub Actions cron job.

* **Task 8.1:** Create a GitHub Actions workflow configuration file at [.github/workflows/daily_ingest.yml](file:///d:/RAG%20Based%20MF%20Chatbot/.github/workflows/daily_ingest.yml).
* **Task 8.2:** Set up the trigger schedule (daily at 10:30 AM IST / 5:00 AM UTC) and configure `workflow_dispatch` to allow manual execution.
* **Task 8.3:** Configure steps to set up Python, install dependencies from `requirements.txt`, run [ingest.py](file:///d:/RAG%20Based%20MF%20Chatbot/scripts/ingest.py), and run [chunk_and_embed.py](file:///d:/RAG%20Based%20MF%20Chatbot/scripts/chunk_and_embed.py).
* **Task 8.4:** Add a Git commit and push step within the workflow to save and deploy the updated JSON corpus and vector store.


