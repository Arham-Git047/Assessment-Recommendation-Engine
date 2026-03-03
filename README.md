# SHL Assessment Recommender

A retrieval-augmented recommendation engine that finds the most relevant **SHL individual test solutions** for any role, using hybrid dense + sparse retrieval (sentence-transformers + FAISS + TF-IDF).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Build the catalogue (scrape SHL site or use curated fallback)
python scripts/scrape_catalogue.py --csv

# Start the API server
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Start the Streamlit frontend (in a separate terminal)
streamlit run app/app.py

# Run evaluation
python -m src.evaluation --top_k 10
```

## Architecture

| Component | Technology |
|-----------|-----------|
| Embeddings | [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (384-dim) |
| Vector Store | FAISS IndexFlatIP (cosine similarity) |
| Sparse Retrieval | TF-IDF + cosine similarity |
| Blending | 70% dense + 30% sparse |
| API | FastAPI with Pydantic validation |
| Frontend | Streamlit |
| Catalogue | 377 individual SHL test solutions |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health check |
| `POST` | `/recommend` | Get assessment recommendations |

### POST /recommend

**Request:**
```json
{
  "query": "I need a cognitive test for a senior data analyst",
  "top_k": 10
}
```

**Response:**
```json
{
  "recommended_assessments": [
    {
      "assessment_name": "Verify Interactive - Numerical Reasoning",
      "url": "https://www.shl.com/solutions/products/assessments/verify-interactive-numerical-reasoning/",
      "adaptive_support": "Yes",
      "description": "Measures ability to make correct decisions or inferences from numerical data.",
      "duration": 17,
      "remote_support": "Yes",
      "test_type": "Cognitive"
    }
  ]
}
```

## Project Structure

```
SHL_Assessment/
├── api/
│   ├── __init__.py
│   └── main.py              # FastAPI: /health, /recommend
├── app/
│   └── app.py               # Streamlit frontend
├── src/
│   ├── recommender.py        # Hybrid RAG recommendation engine
│   ├── evaluation.py         # Mean Recall@K metrics
│   ├── resume_parser.py      # PDF/TXT resume parser (optional)
│   ├── analytics.py          # Session tracking
│   └── utils.py              # Shared helpers
├── scripts/
│   ├── scrape_catalogue.py   # SHL catalogue scraper + curated fallback
│   └── test_api.py           # API test script
├── data/
│   ├── shl_products.json     # 377 individual test solutions
│   ├── shl_catalogue.csv     # CSV version
│   ├── faiss_index/          # Cached FAISS index
│   └── evaluation_report.json
├── docs/
│   └── approach.md           # 2-page approach document
├── requirements.txt
└── README.md
```

## Evaluation

Mean Recall@10 = **0.6428** across 15 labelled test queries.

## Input Types

The system accepts three input types:
1. **Natural-language query** – e.g., "I need a cognitive test for a data analyst"
2. **Job description text** – Paste a full JD
3. **JD URL** – Automatically fetches and extracts text from the page
