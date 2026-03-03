"""Generate predictions CSV from labelled test queries."""
import csv, sys, os

# Force TF-IDF fallback to avoid slow sentence-transformers loading
os.environ["SHL_FORCE_TFIDF"] = "1"

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Temporarily block sentence_transformers import to force TF-IDF
import importlib
_orig_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

import unittest.mock as mock

with mock.patch.dict('sys.modules', {'sentence_transformers': None, 'faiss': None}):
    # Clear cached module if already imported
    if 'src.recommender' in sys.modules:
        del sys.modules['src.recommender']
    
    from src.recommender import Recommender
    from src.evaluation import LABELLED_QUERIES

    rec = Recommender()
    rows = []
    for item in LABELLED_QUERIES:
        q = item['query']
        results = rec.recommend(q, top_k=10)
        for rank, r in enumerate(results, 1):
            rows.append({
                'query': q,
                'rank': rank,
                'assessment_name': r['assessment_name'],
                'url': r['url'],
                'test_type': r['test_type'],
                'duration': r['duration'],
                'remote_support': r['remote_support'],
                'adaptive_support': r['adaptive_support'],
                'score': r.get('score', ''),
            })

    with open('Arham_Kelkar.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=[
            'query', 'rank', 'assessment_name', 'url',
            'test_type', 'duration', 'remote_support',
            'adaptive_support', 'score',
        ])
        w.writeheader()
        w.writerows(rows)
    print(f'Wrote {len(rows)} rows to Arham_Kelkar.csv')
