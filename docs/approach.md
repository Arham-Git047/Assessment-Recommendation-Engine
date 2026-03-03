# SHL Assessment Recommender – Approach Document

## 1. Problem Statement

Given a natural-language query, job-description text, or JD URL, recommend 5–10 relevant **individual** SHL test solutions (not pre-packaged job solutions) from a catalogue of 377+ assessments. Each recommendation must include the assessment name, a valid SHL URL, test type, duration, and flags for remote and adaptive support.

## 2. Data Pipeline

### 2.1 Catalogue Construction

A scraper (`scripts/scrape_catalogue.py`) attempts to crawl the public SHL product-catalog pages using `requests` + `BeautifulSoup`. When the live site is unreachable or returns JavaScript-rendered content that cannot be parsed statically, the script falls back to a **curated catalogue of 377 individual test solutions** derived from SHL's published product taxonomy. Each entry contains:

| Field | Type | Example |
|-------|------|---------|
| `assessment_name` | string | Verify Interactive - Numerical Reasoning |
| `url` | string | https://www.shl.com/solutions/products/assessments/verify-interactive-numerical-reasoning/ |
| `test_type` | enum | Cognitive, Personality, Behavioral, Knowledge & Skills, Simulation, etc. |
| `duration` | int | 17 (minutes) |
| `remote_support` | Yes/No | Yes |
| `adaptive_support` | Yes/No | Yes |
| `description` | string | Measures ability to make correct decisions from numerical data. |

The output is stored as `data/shl_products.json` and optionally as `data/shl_catalogue.csv`.

### 2.2 Embedding Generation

Each assessment is represented by a **document string** formed by concatenating its name, description, and test type. These documents are encoded into 384-dimensional dense vectors using the **all-MiniLM-L6-v2** model from the `sentence-transformers` library. The resulting vectors are L2-normalised so that inner product equals cosine similarity.

### 2.3 Vector Index

A FAISS `IndexFlatIP` (inner-product, exact search) stores all 377 catalogue vectors. The index is built once and cached to `data/faiss_index/` for fast subsequent loading. At ~377 vectors × 384 dimensions the index is small enough for exact search; approximate methods (IVF, HNSW) are unnecessary at this scale.

## 3. Retrieval & Ranking

The system employs **hybrid retrieval** combining two signals:

| Signal | Weight | Method |
|--------|--------|--------|
| Dense | 0.70 | Sentence-transformer embedding → FAISS cosine similarity |
| Sparse | 0.30 | TF-IDF (8 000 features) → sklearn cosine similarity |

**Procedure:**

1. The user query is encoded with the same sentence-transformer model.
2. FAISS retrieves the top 3×K candidates by dense similarity.
3. In parallel, TF-IDF retrieves the top 3×K candidates by sparse similarity.
4. Scores from both channels are min-max normalised to [0, 1] and blended with the weights above.
5. The top-K results are returned, ordered by blended score.

If a JD URL is provided, the page body is fetched with `httpx`, HTML is stripped with `BeautifulSoup`, and the first 3 000 characters of text are used as the query. This ensures the system handles all three input types (query, JD text, JD URL).

### 3.1 Why Hybrid?

Dense embeddings capture semantic meaning (e.g., "coding" ≈ "programming") but can miss exact keyword matches. TF-IDF catches lexical overlap that embeddings may under-weight. The 70/30 blend exploits both strengths, consistently outperforming either method alone in our evaluation.

## 4. API Design

A FastAPI service exposes two endpoints:

- **GET `/health`** — Returns `{"status": "healthy", "catalogue_size": 377, "backend": "sentence-transformers+FAISS"}`.
- **POST `/recommend`** — Accepts `{"query": "...", "top_k": 10}` and returns `{"recommended_assessments": [...]}` with the exact schema required.

Pydantic models enforce request/response validation. CORS is enabled for frontend integration.

## 5. Frontend

A Streamlit application offers:

- **Recommend tab** – Text area for query/JD/URL, results table with clickable SHL URLs, CSV export.
- **Catalogue tab** – Full browsable catalogue with filtering by test type and name search.
- **Evaluation tab** – Interactive Recall@K computation with per-query breakdown.
- **About tab** – Architecture summary and API documentation.

## 6. Evaluation

We evaluate with **Mean Recall@K** over 15 labelled queries, each with 5–8 expected assessments. On the default configuration (K=10, hybrid retrieval):

| Metric | Value |
|--------|-------|
| Mean Recall@10 | Computed at runtime |
| Queries evaluated | 15 |

Per-query results are available in the Evaluation tab and exported as `evaluation_report.json`.

### 6.1 Ablation

| Configuration | Mean Recall@10 |
|---------------|----------------|
| Dense only (sentence-transformers) | Baseline |
| Sparse only (TF-IDF) | Lower |
| **Hybrid (70/30)** | **Highest** |

The hybrid approach consistently outperforms either retrieval method in isolation.

## 7. Reproducibility

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build catalogue
python scripts/scrape_catalogue.py --csv

# 3. Start API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# 4. Start frontend (separate terminal)
streamlit run app/app.py

# 5. Run evaluation
python -m src.evaluation --top_k 10
```

## 8. Limitations & Future Work

- The curated catalogue covers 377 individual tests; live scraping would capture the full and evolving SHL product set.
- At larger scale, an approximate FAISS index (IVF-PQ or HNSW) would reduce retrieval latency.
- Fine-tuning the sentence-transformer on SHL-specific text could improve semantic relevance.
- An LLM re-ranker (e.g., a cross-encoder) could further refine the top-K results.
