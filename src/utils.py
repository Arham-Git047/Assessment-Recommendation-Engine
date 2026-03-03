"""
Shared constants and helper functions for the SHL Assessment app.
"""

# ─── Role & Skill presets for quick-fill ─────────────────────────────────────
ROLE_PRESETS: dict[str, list[str]] = {
    "Data Analyst": ["python", "sql", "statistics", "excel", "data analysis"],
    "Data Scientist": ["python", "machine learning", "statistics", "sql"],
    "Software Engineer": ["java", "python", "programming", "testing", "cloud"],
    "Project Manager": ["project planning", "risk management", "leadership"],
    "Business Analyst": ["excel", "data analysis", "communication", "sql"],
    "HR Professional": ["recruitment", "hr policies", "communication"],
    "Marketing Specialist": ["marketing", "digital marketing", "communication"],
    "Customer Support": ["communication", "empathy", "customer service"],
    "Finance Analyst": ["finance", "accounting", "excel", "data analysis"],
    "Network Engineer": ["networking", "protocols", "security", "cloud"],
}

# ─── Level presentation ──────────────────────────────────────────────────────
LEVEL_COLORS = {
    "easy": "#00a86b",
    "medium": "#e0a458",
    "hard": "#c0392b",
}

LEVEL_LABELS = {
    "easy": "Easy",
    "medium": "Medium",
    "hard": "Hard",
}

# ─── Category labels ────────────────────────────────────────────────────
CATEGORY_ICONS = {
    "Technical": "Technical",
    "Cognitive": "Cognitive",
    "Behavioral": "Behavioral",
    "Domain": "Domain",
    "General": "General",
}


def format_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} min"
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if m else f"{h}h"


def level_badge_html(level: str) -> str:
    """Return an inline-styled HTML badge for the assessment level."""
    color = LEVEL_COLORS.get(level.lower(), "#888")
    label = level.capitalize()
    return (
        f'<span style="background:{color};color:#fff;padding:2px 10px;'
        f'border-radius:3px;font-size:0.78em;font-weight:700;'
        f'font-family:Inter,sans-serif;letter-spacing:0.03em;">'
        f'{label}</span>'
    )


def score_bar_html(score: float, max_score: float = 1.0) -> str:
    """Return an HTML progress-bar representing the score."""
    pct = min(score / max_score * 100, 100) if max_score else 0
    if pct >= 70:
        color = "#00a86b"
    elif pct >= 40:
        color = "#e0a458"
    else:
        color = "#c0392b"
    return (
        f'<div style="background:#ebedef;border-radius:3px;height:8px;width:100%;">'
        f'<div style="background:{color};width:{pct:.0f}%;height:100%;border-radius:3px;"></div>'
        f'</div>'
    )
