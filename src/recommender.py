"""
SHL Assessment Recommender – RAG Pipeline
==========================================
Uses sentence-transformers (all-MiniLM-L6-v2) for dense embeddings
and FAISS for fast approximate nearest-neighbour retrieval.
Falls back to TF-IDF + cosine-similarity when torch is unavailable.

Public API
----------
    rec = Recommender()              # auto-loads catalogue + builds index
    results = rec.recommend(query, top_k=10)
    health  = rec.health()
"""

from __future__ import annotations

import json, os, re, logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _ROOT / "data"
_PRODUCTS_JSON = _DATA_DIR / "shl_products.json"
_INDEX_DIR = _DATA_DIR / "faiss_index"
_INDEX_FILE = _INDEX_DIR / "index.faiss"
_META_FILE = _INDEX_DIR / "meta.json"

# ─── Embedding back-end selection ─────────────────────────────────────────────

_USE_SBERT = False
_sbert_model = None

try:
    from sentence_transformers import SentenceTransformer
    import faiss

    _USE_SBERT = True
    logger.info("Using sentence-transformers + FAISS back-end.")
except ImportError:
    logger.warning(
        "sentence-transformers or faiss-cpu not installed; "
        "falling back to TF-IDF retrieval."
    )

# TF-IDF fallback (always available via scikit-learn)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_doc(item: dict) -> str:
    """Concatenate searchable fields into a single document string."""
    parts = [
        item.get("assessment_name", ""),
        item.get("description", ""),
        item.get("test_type", ""),
    ]
    return " ".join(parts)


# ─── Recommender ──────────────────────────────────────────────────────────────

class Recommender:
    """Hybrid dense / sparse retriever for SHL assessments."""

    def __init__(self, catalogue_path: Optional[str | Path] = None):
        path = Path(catalogue_path) if catalogue_path else _PRODUCTS_JSON
        if not path.exists():
            raise FileNotFoundError(
                f"Catalogue not found at {path}. "
                "Run  python scripts/scrape_catalogue.py  first."
            )
        with open(path, encoding="utf-8") as f:
            self._catalogue: list[dict] = json.load(f)

        self._docs = [_build_doc(item) for item in self._catalogue]

        # Build retrieval indices
        self._tfidf_vec = TfidfVectorizer(stop_words="english", max_features=8000)
        self._tfidf_matrix = self._tfidf_vec.fit_transform(self._docs)

        if _USE_SBERT:
            self._build_faiss_index()

    # ── Dense index (sentence-transformers + FAISS) ───────────────────────

    def _get_model(self):
        global _sbert_model
        if _sbert_model is None:
            _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
        return _sbert_model

    def _build_faiss_index(self):
        """Build (or load cached) FAISS index from catalogue embeddings."""
        if _INDEX_FILE.exists() and _META_FILE.exists():
            self._faiss_index = faiss.read_index(str(_INDEX_FILE))
            logger.info("Loaded cached FAISS index.")
            return

        model = self._get_model()
        logger.info("Encoding catalogue with sentence-transformers ...")
        embeddings = model.encode(
            self._docs, show_progress_bar=True,
            batch_size=64, normalize_embeddings=True,
        )
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)  # inner product on normalised vecs = cosine
        index.add(embeddings.astype(np.float32))
        self._faiss_index = index

        # Cache to disk
        _INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(_INDEX_FILE))
        with open(_META_FILE, "w") as f:
            json.dump({"n": len(self._catalogue), "dim": dim}, f)
        logger.info(
            "Built and cached FAISS index (%d vectors, dim=%d).",
            len(self._catalogue), dim,
        )

    # ── Retrieval ─────────────────────────────────────────────────────────

    def _dense_search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Return (index, score) pairs from FAISS."""
        model = self._get_model()
        q_emb = model.encode([query], normalize_embeddings=True).astype(np.float32)
        scores, indices = self._faiss_index.search(q_emb, top_k)
        return [
            (int(idx), float(sc))
            for idx, sc in zip(indices[0], scores[0])
            if idx >= 0
        ]

    def _sparse_search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        """Return (index, score) pairs from TF-IDF cosine similarity."""
        q_vec = self._tfidf_vec.transform([query])
        sims = cosine_similarity(q_vec, self._tfidf_matrix).flatten()
        top_idx = sims.argsort()[::-1][:top_k]
        return [(int(i), float(sims[i])) for i in top_idx]

    def recommend(self, query: str, top_k: int = 10) -> list[dict]:
        """
        Return the top-K assessments for *query*.

        Uses hybrid retrieval when sentence-transformers is available:
        dense (0.7) + sparse (0.3).  Otherwise falls back to sparse only.
        """
        if not query or not query.strip():
            return []

        if _USE_SBERT:
            dense = self._dense_search(query, top_k * 3)
            sparse = self._sparse_search(query, top_k * 3)

            # Merge: normalise scores to [0, 1] then blend
            scores: dict[int, float] = {}
            if dense:
                max_d = max(s for _, s in dense) or 1.0
                for idx, sc in dense:
                    scores[idx] = scores.get(idx, 0) + 0.7 * (sc / max_d)
            if sparse:
                max_s = max(s for _, s in sparse) or 1.0
                for idx, sc in sparse:
                    scores[idx] = scores.get(idx, 0) + 0.3 * (sc / max_s)

            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        else:
            ranked = self._sparse_search(query, top_k)

        results = []
        for idx, score in ranked:
            item = self._catalogue[idx].copy()
            item["score"] = round(score, 4)
            results.append(item)
        return results

    # ── Convenience ───────────────────────────────────────────────────────

    def get_catalogue(self) -> list[dict]:
        """Return the full raw catalogue."""
        return self._catalogue

    def catalogue_df(self) -> pd.DataFrame:
        return pd.DataFrame(self._catalogue)

    def health(self) -> dict:
        return {
            "status": "healthy",
            "catalogue_size": len(self._catalogue),
            "backend": "sentence-transformers+FAISS" if _USE_SBERT else "TF-IDF",
        }


# ─── CLI quick-test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    rec = Recommender()
    q = " ".join(sys.argv[1:]) or "Python developer with data analysis skills"
    print(f"\nQuery: {q}\n")
    for r in rec.recommend(q, top_k=5):
        print(f"  {r['score']:.4f}  {r['assessment_name']}")
        print(f"           {r['url']}")
        print()
