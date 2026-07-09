# 🤖 FundBot — RAG-Based Mutual Fund FAQ Assistant (HDFC Funds)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/Groq-Llama%203-orange.svg)](https://groq.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FC6D26?style=flat)](https://trychroma.com/)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-BGE%20Embeddings-yellow)](https://huggingface.co/BAAI/bge-small-en-v1.5)

An AI-powered, facts-only FAQ assistant for mutual fund schemes sourced directly from Groww. This application combines semantic vector search (ChromaDB + BGE Embeddings) with Groq's Large Language Model reasoning (`llama3-8b-8192` or `llama3-70b-8192`) and multi-stage guardrails (PII scrubbing, intent classification, sentence/citation validation) to answer objective, verifiable investor queries while strictly adhering to SEBI and AMFI compliance regulations against providing investment advice.

---

## ✨ Key Features

- **Facts-Only Retrieval**: Answers objective, scheme-specific queries regarding expense ratios, exit loads, minimum SIP amounts, ELSS lock-in periods, Riskometer classifications, and benchmark indices.
- **Strict Compliance Guardrails**: Programmatically validates LLM responses to ensure they do not exceed 3 sentences, contain exactly one citation link, and include no advisory terminology.
- **PII Scrubbing & Privacy**: Redacts sensitive personal information (PAN, Aadhaar, phone numbers, emails) automatically at the input boundary.
- **Hybrid Search Engine**: Combines keyword search (BM25) and dense semantic vector search (ChromaDB + BGE Embeddings) for extremely high retrieval accuracy.
- **Polite Refusal Handler**: Bypasses the LLM entirely for speculative or advisory queries (e.g., *"Should I buy..."*, *"Which fund is better?"*), returning polite refusals alongside educational AMFI portal links.
- **Interactive UI Dashboard**: A clean, minimalist single-page chat interface built with native HTML, CSS, and JS, featuring quick examples, disclaimers, and live system log tracking.

### 📊 Supported HDFC Mutual Fund Schemes
FundBot operates on a curated corpus of the following 5 HDFC mutual fund schemes:
- **[HDFC Mid-Cap Opportunities Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)**
- **[HDFC Flexi Cap Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth)**
- **[HDFC Focused 30 Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth)**
- **[HDFC ELSS Tax Saver Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth)**
- **[HDFC Top 100 Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth)**

---

## 🏗️ System Architecture & Data Flow

FundBot processes user questions through a multi-stage pipeline:

```
[User Query] ──> [PII Sanitizer] ──> [Intent Classifier (Guardrail)]
                                              │
                      ┌───────────────────────┴───────────────────────┐
             [Factual Query]                                   [Advisory Query]
                      │                                               │
           [Hybrid Vector Retrieval]                                  ▼
         (ChromaDB + BGE Embeddings)                        [Direct Refusal Response]
                      │                                    (Polite Refusal + AMFI Link)
                      ▼                                               │
             [Response Generator]                                     │
                 (Groq/Llama 3)                                       │
                      │                                               │
                      ▼                                               │
             [Output Validator]                                       │
      (Checks sentence count, citation,                               │
       and advisory term compliance)                                  │
                      │                                               │
                      ▼                                               ▼
             [Final Chat Output] <────────────────────────────────────┘
```

1. **PII Sanitizer**: Redacts sensitive personal information (such as PAN, Aadhaar, phone numbers, and emails) to preserve user privacy.
2. **Intent Classifier**: Evaluates the query. If the user asks for advice (*"Should I buy..."*, *"Which fund is better?"*), it bypasses RAG and routes directly to a polite refusal response including educational investor links.
3. **Hybrid Vector Retrieval**: For factual queries, retrieves relevant segments from a local Chroma DB vector database containing scraped facts of the 5 HDFC mutual fund Groww pages.
4. **Response Generator**: Generates answers utilizing Groq API's Llama 3 models based strictly on the retrieved context.
5. **Output Validator**: Programmatically checks the LLM output to guarantee it does not exceed 3 sentences, contains exactly 1 citation, includes no advisory terminology, and formats the source update date.

---

## 📂 Project Structure

```
├── main.py                     # FastAPI application & API endpoints (serve chat interface, status)
├── requirements.txt            # Python dependencies
├── context.md                  # Project context, objectives, rules, and scope definitions
├── architecture.md             # Detailed service and pipeline block diagrams
├── implementation.md           # Implementation phase checklist
├── evals.md                    # Verification metrics and test assertions
├── edgecase.md                 # System edge case and boundary handling protocols
├── frontend/                   # Single Page Application (SPA) resources
│   ├── index.html              # Chat UI layout with disclaimers and examples
│   ├── style.css               # Clean, minimalist custom chat design layout
│   └── app.js                  # Frontend interface logic, API integration, and rendering
├── services/                   # Backend services and modules
│   ├── classifier.py           # User query intent analysis & routing (factual vs advisory)
│   ├── generator.py            # LLM prompt orchestrator and Groq API client
│   ├── pii_scrubber.py         # Regex PII scrubber rules
│   ├── retriever.py            # Chroma vector database retriever with semantic query filters
│   └── validator.py            # Programmatic output quality validation checks
├── scripts/                    # CLI execution utilities
│   ├── ingest.py               # Groww web pages scraper for mutual fund attributes
│   ├── chunk_and_embed.py      # Semantic chunking model and vector store pipeline
│   ├── run_golden_eval.py      # Golden dataset evaluation runner
│   ├── test_guardrails.py      # Test suite for intent classification and PII scrubbing
│   ├── test_retrieval.py       # Test suite for context search accuracy
│   ├── test_validator.py       # Test suite for programmatic output validation checks
│   └── test_rag.py             # Test suite for the full generation flow
└── data/                       # Ingested datasets and database storage (Git-ignored)
    ├── raw_funds.json          # Scraped raw JSON data of mutual funds
    └── chroma_db/              # Chroma DB SQLite database files
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
* Python 3.10+
* Groq API Key (get one from [Groq Console](https://console.groq.com/))

### 2. Installation
1. Clone the repository to your local machine.
2. Initialize and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Environment Configuration
Create a `.env` file in the root directory (you can copy `.env.example` as a template):
```env
GROQ_API_KEY=your_groq_api_key_here
CHROMA_DB_PATH=data/chroma_db
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5
```

### 4. Build the Knowledge Base
To fetch the latest Groww fund stats and index them into the database:
1. **Scrape fund details**:
   ```bash
   python scripts/ingest.py
   ```
   *Fetches and parses the target mutual fund scheme URLs, storing raw parameters in `data/raw_funds.json`.*

2. **Chunk and Embed**:
   ```bash
   python scripts/chunk_and_embed.py
   ```
   *Generates semantic text chunks, calculates BGE embedding vectors, and populates the database collection at `data/chroma_db`.*

### 5. Running the Chatbot
Launch the API server using Uvicorn:
```bash
uvicorn main:app --reload
```
Once started, open `http://127.0.0.1:8000` in your web browser to access the chat web application.

---

## 🧪 Testing & Verification

The project includes test scripts to verify the functionality of each component and the complete end-to-end pipeline:

### Component Tests
* **Test Guardrails & Scrubbing**:
  ```bash
  python scripts/test_guardrails.py
  ```
* **Test Database Retrieval**:
  ```bash
  python scripts/test_retrieval.py
  ```
* **Test Output Validator Rules**:
  ```bash
  python scripts/test_validator.py
  ```
* **Test Full RAG pipeline**:
  ```bash
  python scripts/test_rag.py
  ```

### Golden Dataset Evaluation
To perform a complete accuracy and compliance evaluation of the chatbot model against the pre-defined target questionnaire dataset:
```bash
python scripts/run_golden_eval.py
```
This script runs the queries, checks response correctness, parses outputs against constraints, and outputs a performance summary document in `data/eval_summary.md`.

---

## ⚖️ Compliance & Disclaimers
* **Facts-Only**: FundBot strictly references public Groww data and AMC factsheets.
* **No Advisory**: FundBot does not provide comparisons, recommendations, star-ratings explanations, or advice to buy/sell mutual fund assets.
* **Privacy**: FundBot does not store chat histories or ask for any credentials, accounts, or PII.
