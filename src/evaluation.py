"""
Evaluation – Mean Recall@K
===========================
Computes Mean Recall@K for the SHL recommendation system
using a labelled set of (query, expected_assessment_names) pairs.

Usage
-----
    python -m src.evaluation              # run default evaluation
    python -m src.evaluation --top_k 5    # evaluate at K=5
"""

from __future__ import annotations

import json, logging, sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent


# ─── Labelled test set ────────────────────────────────────────────────────────

LABELLED_QUERIES: list[dict] = [
    {
        "query": "I need a cognitive ability test for a graduate software engineer",
        "expected": [
            "Verify G+ (Interactive)",
            "Verify Interactive - Numerical Reasoning",
            "Verify Interactive - Inductive Reasoning",
            "Graduate Numerical Reasoning",
            "Graduate Verbal Reasoning",
            "Abstract Reasoning",
        ],
    },
    {
        "query": "Personality assessment for a sales manager",
        "expected": [
            "OPQ32r",
            "Sales Personality Questionnaire",
            "Motivation Questionnaire (MQ)",
            "Management Situational Judgement",
            "Leadership Impact Assessment",
        ],
    },
    {
        "query": "Python programming test for a data analyst",
        "expected": [
            "Python Programming (Entry Level)",
            "Python Programming (Mid Level)",
            "Python Programming (Senior Level)",
            "Data Modelling Skills Test",
            "Statistical Analysis Assessment",
        ],
    },
    {
        "query": "Customer service assessment for a call centre representative",
        "expected": [
            "Customer Contact Styles Questionnaire (CCSQ)",
            "Customer Service Situational Judgement",
            "Call Center Situational Judgement",
            "Call Centre English Fluency",
            "Customer Contact Simulation",
        ],
    },
    {
        "query": "Leadership development assessment for senior executives",
        "expected": [
            "Leadership Impact Assessment",
            "Leadership Situational Judgement",
            "360 Feedback - Leadership",
            "Succession Planning Assessment",
            "High Potential Identification",
            "OPQ32r",
        ],
    },
    {
        "query": "Java developer skills test for mid-level backend engineering position",
        "expected": [
            "Java Programming (Mid Level)",
            "Java Programming (Senior Level)",
            "Java Programming (Entry Level)",
            "Spring Boot Developer Assessment",
            "SQL Proficiency Test",
        ],
    },
    {
        "query": "Numerical and verbal reasoning for finance graduates",
        "expected": [
            "Verify Interactive - Numerical Reasoning",
            "Verify Interactive - Verbal Reasoning",
            "Graduate Numerical Reasoning",
            "Graduate Verbal Reasoning",
            "Financial Accounting Knowledge",
            "Data Interpretation",
        ],
    },
    {
        "query": "Situational judgement test for a retail store supervisor",
        "expected": [
            "Supervisory Situational Judgement",
            "Retail Situational Judgement",
            "Retail Operations Knowledge",
            "Management Situational Judgement",
            "Customer Service Situational Judgement",
        ],
    },
    {
        "query": "Cloud architect assessment for AWS and Azure skills",
        "expected": [
            "AWS Solutions Architect Assessment",
            "AWS Developer Assessment",
            "Azure Fundamentals Assessment",
            "Azure Administrator Assessment",
            "Google Cloud Platform Assessment",
            "Docker & Containers Assessment",
        ],
    },
    {
        "query": "Microsoft Office proficiency tests for an administrative assistant",
        "expected": [
            "Microsoft Excel (Basic)",
            "Microsoft Excel (Intermediate)",
            "Microsoft Word (Basic)",
            "Microsoft Word (Intermediate)",
            "Microsoft Outlook (Basic)",
            "Microsoft PowerPoint (Basic)",
            "Typing Speed & Accuracy Test",
            "Data Entry Accuracy Test",
        ],
    },
    {
        "query": "Emotional intelligence and teamwork assessment for a project manager",
        "expected": [
            "Emotional Intelligence Questionnaire",
            "Team Impact Assessment",
            "Teamwork Situational Judgement",
            "Project Management (PMP/PRINCE2)",
            "Communication Style Inventory",
        ],
    },
    {
        "query": "Cybersecurity skills test for an information security analyst",
        "expected": [
            "Cybersecurity Fundamentals Test",
            "Network Security Test",
            "Application Security Test",
            "Penetration Testing Test",
            "Cloud Security Test",
            "OWASP Top 10 Test",
        ],
    },
    {
        "query": "Healthcare compliance and safety assessment for hospital staff",
        "expected": [
            "Healthcare Compliance Knowledge",
            "Healthcare Situational Judgement",
            "Safety Situational Judgement",
            "Dependability & Safety Instrument (DSI)",
            "Food Safety & Quality (HACCP)",
        ],
    },
    {
        "query": "Data science and machine learning assessment for a research scientist",
        "expected": [
            "Machine Learning Fundamentals Assessment",
            "Deep Learning & Neural Networks Assessment",
            "Natural Language Processing Assessment",
            "Statistical Analysis Assessment",
            "Python Programming (Senior Level)",
            "R Programming (Senior Level)",
        ],
    },
    {
        "query": "Mechanical comprehension test for an engineering technician",
        "expected": [
            "Mechanical Comprehension",
            "Spatial Reasoning",
            "Verify Interactive - Inductive Reasoning",
            "Construction Situational Judgement",
            "Automotive Engineering Knowledge",
        ],
    },
]


# ─── Evaluation functions ─────────────────────────────────────────────────────

def recall_at_k(recommended: list[str], expected: list[str], k: int) -> float:
    """
    Compute Recall@K: fraction of expected items found in top-K recommendations.

    Parameters
    ----------
    recommended : list of assessment names returned by the recommender (ordered)
    expected    : list of ground-truth relevant assessment names
    k           : cutoff

    Returns
    -------
    float in [0, 1]
    """
    if not expected:
        return 1.0  # vacuous truth: nothing expected, recall is perfect
    top_k_set = {name.lower().strip() for name in recommended[:k]}
    hits = sum(1 for e in expected if e.lower().strip() in top_k_set)
    return hits / len(expected)


def mean_recall_at_k(
    recommender,
    queries: Optional[list[dict]] = None,
    k: int = 10,
) -> dict:
    """
    Evaluate the recommender on a labelled query set.

    Parameters
    ----------
    recommender : Recommender instance with a .recommend(query, top_k) method
    queries     : list of {"query": str, "expected": list[str]}.
                  Defaults to LABELLED_QUERIES.
    k           : cutoff for Recall@K

    Returns
    -------
    dict with "mean_recall_at_k", "per_query" details, "k"
    """
    queries = queries or LABELLED_QUERIES
    per_query = []

    for item in queries:
        q = item["query"]
        expected = item["expected"]
        results = recommender.recommend(q, top_k=k)
        rec_names = [r["assessment_name"] for r in results]
        r_at_k = recall_at_k(rec_names, expected, k)
        per_query.append({
            "query": q,
            "recall_at_k": round(r_at_k, 4),
            "retrieved": rec_names[:k],
            "expected": expected,
            "hits": [
                e for e in expected
                if e.lower().strip() in {n.lower().strip() for n in rec_names[:k]}
            ],
        })

    mean_r = sum(pq["recall_at_k"] for pq in per_query) / len(per_query) if per_query else 0.0

    return {
        "mean_recall_at_k": round(mean_r, 4),
        "k": k,
        "num_queries": len(per_query),
        "per_query": per_query,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Evaluate SHL recommender")
    parser.add_argument("--top_k", type=int, default=10, help="K for Recall@K")
    args = parser.parse_args()

    # Add project root to path
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))

    from src.recommender import Recommender

    rec = Recommender()
    report = mean_recall_at_k(rec, k=args.top_k)

    print(f"\n{'=' * 60}")
    print(f"  Mean Recall@{report['k']}  =  {report['mean_recall_at_k']:.4f}")
    print(f"  Queries evaluated: {report['num_queries']}")
    print(f"{'=' * 60}\n")

    for pq in report["per_query"]:
        status = "PASS" if pq["recall_at_k"] > 0.3 else "LOW "
        print(f"  [{status}] R@{report['k']}={pq['recall_at_k']:.2f}  {pq['query'][:60]}")
        if pq["hits"]:
            for h in pq["hits"]:
                print(f"            + {h}")
    print()

    # Save report
    report_path = _ROOT / "data" / "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Full report saved to {report_path}")
