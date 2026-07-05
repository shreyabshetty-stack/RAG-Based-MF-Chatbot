"""
main.py — FastAPI application for the Groww RAG Mutual Fund FAQ Assistant.
Exposes:
  GET  /             → serves frontend/index.html
  POST /api/chat     → full guardrail → RAG → validator pipeline
  GET  /api/health   → status check
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from dotenv import load_dotenv

load_dotenv()

# ─── Logging ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")
logger = logging.getLogger(__name__)

# ─── Lazy-load pipeline components ───────────────────────────────
# Loaded once at startup via lifespan to avoid cold-start penalty
_retriever = None
_generator = None
_classifier = None
_pii_scrubber = None
_validator = None

ADVISORY_FALLBACK = (
    "I am a facts-only assistant and cannot provide investment advice, "
    "comparisons, or recommendations. For educational resources, please visit "
    "the AMFI Investor Education portal: https://www.amfiindia.com/investor-corner/investor-education"
)

RATE_LIMIT_FALLBACK = (
    "I am currently unable to fetch the latest details due to high demand. "
    "Please try again in a few moments. You can refer directly to HDFC mutual "
    "fund details on the Groww website."
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all ML/service components once at startup."""
    global _retriever, _generator, _classifier, _pii_scrubber, _validator
    logger.info("Loading pipeline components...")
    try:
        from services.retriever import MutualFundRetriever
        from services.generator import MutualFundGenerator
        from services.classifier import MutualFundClassifier
        from services.pii_scrubber import PIIScrubber
        from services.validator import ResponseValidator

        _retriever    = MutualFundRetriever()
        _generator    = MutualFundGenerator()
        _classifier   = MutualFundClassifier()
        _pii_scrubber = PIIScrubber()
        _validator    = ResponseValidator()
        logger.info("All pipeline components loaded successfully.")
    except Exception as e:
        logger.error("Failed to load pipeline component: %s", e)
        # App starts anyway so the health endpoint remains reachable
    yield
    logger.info("Shutting down FundBot API.")


# ─── App ─────────────────────────────────────────────────────────
app = FastAPI(
    title="FundBot — HDFC Mutual Fund FAQ Assistant",
    description="Facts-only RAG chatbot sourced from Groww mutual fund pages.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Serve frontend static assets
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ─── Request / Response models ────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000,
                         description="User query about HDFC mutual funds.")
    fund_filter: str | None = Field(None,
                                    description="Optional fund name to scope retrieval.")


class ChatResponse(BaseModel):
    answer: str
    source_url: str | None
    intent: str           # "FACTUAL" | "ADVISORY" | "ERROR"
    updated_date: str
    pii_detected: bool
    validation_warnings: list[str]


# ─── Routes ──────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the FundBot chat interface."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend not found.")
    return FileResponse(index_path, media_type="text/html")


@app.get("/api/health")
async def health_check():
    """Returns the health status of the API and pipeline components."""
    components = {
        "retriever":  _retriever  is not None,
        "generator":  _generator  is not None,
        "classifier": _classifier is not None,
        "pii_scrubber": _pii_scrubber is not None,
        "validator":  _validator  is not None,
    }
    all_ready = all(components.values())
    return JSONResponse(
        status_code=200 if all_ready else 503,
        content={
            "status": "healthy" if all_ready else "degraded",
            "components": components,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Full pipeline:
      1. PII Scrubbing
      2. Intent Classification (FACTUAL / ADVISORY)
      3. Vector Retrieval (ChromaDB + BGE)
      4. LLM Generation (Groq)
      5. Output Validation & Footer Injection
    """
    if not all([_retriever, _generator, _classifier, _pii_scrubber, _validator]):
        raise HTTPException(
            status_code=503,
            detail="Pipeline components not fully loaded. Try again shortly."
        )

    raw_query = req.message.strip()
    today_iso = datetime.utcnow().strftime("%Y-%m-%d")

    # ── Step 1: PII Scrubbing ──────────────────────────────────────
    clean_query, pii_detected = _pii_scrubber.scrub(raw_query)
    if pii_detected:
        logger.info("PII detected and redacted in incoming query.")

    # ── Step 2: Intent Classification ─────────────────────────────
    intent, refusal_message = _classifier.classify(clean_query)
    if intent == "ADVISORY":
        logger.info("Advisory intent detected. Returning refusal.")
        return ChatResponse(
            answer=refusal_message or ADVISORY_FALLBACK,
            source_url="https://www.amfiindia.com/investor-corner/investor-education",
            intent="ADVISORY",
            updated_date=today_iso,
            pii_detected=pii_detected,
            validation_warnings=[],
        )

    # ── Step 3: Vector Retrieval ───────────────────────────────────
    try:
        contexts = _retriever.retrieve(clean_query, k=3)
    except Exception as e:
        logger.error("Retrieval error: %s", e)
        raise HTTPException(status_code=500, detail="Retrieval service error.")

    if not contexts:
        return ChatResponse(
            answer="I am sorry, but I cannot find that information in the official documents.",
            source_url=None,
            intent="FACTUAL",
            updated_date=today_iso,
            pii_detected=pii_detected,
            validation_warnings=[],
        )

    # Determine primary source URL from top context
    primary_source = contexts[0].get("metadata", {}).get(
        "source_url", "https://groww.in"
    )

    # ── Step 4: LLM Generation ─────────────────────────────────────
    try:
        raw_answer = _generator.generate_response(clean_query, contexts)
    except Exception as e:
        logger.error("Generation error: %s", e)
        return ChatResponse(
            answer=RATE_LIMIT_FALLBACK,
            source_url=primary_source,
            intent="ERROR",
            updated_date=today_iso,
            pii_detected=pii_detected,
            validation_warnings=["LLM generation failed. Fallback response served."],
        )

    # Detect if generator returned the rate-limit fallback
    if RATE_LIMIT_FALLBACK in raw_answer:
        return ChatResponse(
            answer=raw_answer,
            source_url=primary_source,
            intent="ERROR",
            updated_date=today_iso,
            pii_detected=pii_detected,
            validation_warnings=["Rate limit fallback triggered."],
        )

    # ── Step 5: Output Validation ──────────────────────────────────
    is_valid, formatted_answer, warnings = _validator.validate_and_format(
        raw_answer, primary_source
    )

    if not is_valid:
        # Advisory leak in output — serve the standard refusal
        logger.warning("Advisory language leaked into LLM output. Serving fallback.")
        return ChatResponse(
            answer=ADVISORY_FALLBACK,
            source_url="https://www.amfiindia.com/investor-corner/investor-education",
            intent="ADVISORY",
            updated_date=today_iso,
            pii_detected=pii_detected,
            validation_warnings=warnings,
        )

    return ChatResponse(
        answer=formatted_answer,
        source_url=primary_source,
        intent="FACTUAL",
        updated_date=today_iso,
        pii_detected=pii_detected,
        validation_warnings=warnings,
    )
