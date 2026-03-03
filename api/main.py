"""
SHL Assessment Recommendation API
===================================
FastAPI service exposing two endpoints:

    GET  /health     → {"status": "healthy", ...}
    POST /recommend  → {"recommended_assessments": [...]}

Launch
------
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging, re, sys, os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is on sys.path so `src.*` imports work
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.recommender import Recommender

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("api")

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SHL Assessment Recommender API",
    version="1.0.0",
    description=(
        "Accepts a natural-language query, job-description text, or JD URL "
        "and returns 1-10 relevant SHL individual test solutions."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Singleton recommender (loaded once at startup) ──────────────────────────

_recommender: Optional[Recommender] = None


def _get_recommender() -> Recommender:
    global _recommender
    if _recommender is None:
        logger.info("Initialising recommender …")
        _recommender = Recommender()
        logger.info("Recommender ready – %s", _recommender.health())
    return _recommender


@app.on_event("startup")
async def _warm_up():
    """Pre-load model + index so the first request isn't slow."""
    _get_recommender()


# ─── Pydantic models ─────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language query, job-description text, or JD URL.",
        examples=["I need a cognitive test for a senior data analyst"],
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of recommendations (1-20).",
    )


class AssessmentOut(BaseModel):
    assessment_name: str
    url: str
    adaptive_support: str
    description: str
    duration: int
    remote_support: str
    test_type: str


class RecommendResponse(BaseModel):
    recommended_assessments: list[AssessmentOut]


class HealthResponse(BaseModel):
    status: str
    catalogue_size: int
    backend: str


# ─── URL-to-text helper ──────────────────────────────────────────────────────

_URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)


async def _resolve_query(raw: str) -> str:
    """If the query looks like a URL, fetch and extract its text."""
    if not _URL_RE.match(raw.strip()):
        return raw
    try:
        import httpx
        from bs4 import BeautifulSoup

        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(raw.strip())
            resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        # Remove scripts / styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Trim to first ~3000 chars to keep embedding input reasonable
        return text[:3000]
    except Exception as exc:
        logger.warning("URL fetch failed (%s); using raw URL as query.", exc)
        return raw


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Return service health and catalogue metadata."""
    rec = _get_recommender()
    return rec.health()


@app.post(
    "/recommend",
    response_model=RecommendResponse,
    tags=["Recommendation"],
    summary="Get assessment recommendations",
)
async def recommend(body: RecommendRequest):
    """
    Accept a natural-language query, job-description text, or JD URL
    and return up to *top_k* relevant SHL individual test solutions.
    """
    rec = _get_recommender()
    query = await _resolve_query(body.query)

    results = rec.recommend(query, top_k=body.top_k)
    if not results:
        return RecommendResponse(recommended_assessments=[])

    # Map internal keys → response schema
    assessments = []
    for r in results:
        assessments.append(
            AssessmentOut(
                assessment_name=r["assessment_name"],
                url=r["url"],
                adaptive_support=r.get("adaptive_support", "No"),
                description=r.get("description", ""),
                duration=r.get("duration", 0),
                remote_support=r.get("remote_support", "Yes"),
                test_type=r.get("test_type", ""),
            )
        )
    return RecommendResponse(recommended_assessments=assessments)
