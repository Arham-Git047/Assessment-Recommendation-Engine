"""
Session-based analytics tracker for the SHL Recommendation Engine.
Stores search history and computes usage insights per Streamlit session.
"""

from datetime import datetime
from collections import Counter
from typing import Optional
import pandas as pd


class SessionAnalytics:
    """Lightweight in-memory analytics for a single user session."""

    def __init__(self) -> None:
        self.history: list[dict] = []

    def log_search(
        self,
        role: str,
        skills: str,
        experience: int,
        num_results: int,
        top_assessment: Optional[str] = None,
    ) -> None:
        self.history.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "role": role.strip(),
            "skills": skills.strip(),
            "experience": experience,
            "num_results": num_results,
            "top_assessment": top_assessment or "—",
        })

    @property
    def total_searches(self) -> int:
        return len(self.history)

    def skill_frequency(self) -> dict[str, int]:
        counter: Counter = Counter()
        for entry in self.history:
            for s in entry["skills"].split(","):
                s = s.strip().lower()
                if s:
                    counter[s] += 1
        return dict(counter.most_common(15))

    def role_frequency(self) -> dict[str, int]:
        counter: Counter = Counter()
        for entry in self.history:
            role = entry["role"].strip().lower()
            if role:
                counter[role] += 1
        return dict(counter.most_common(10))

    def top_assessments(self) -> dict[str, int]:
        counter: Counter = Counter()
        for entry in self.history:
            name = entry["top_assessment"]
            if name and name != "—":
                counter[name] += 1
        return dict(counter.most_common(10))

    def history_dataframe(self) -> pd.DataFrame:
        if not self.history:
            return pd.DataFrame(columns=[
                "timestamp", "role", "skills", "experience",
                "num_results", "top_assessment",
            ])
        return pd.DataFrame(self.history)

    def avg_experience(self) -> float:
        if not self.history:
            return 0.0
        return round(
            sum(e["experience"] for e in self.history) / len(self.history), 1
        )
