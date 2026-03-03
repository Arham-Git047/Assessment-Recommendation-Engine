"""
Resume Parser for the SHL Assessment Recommendation Engine
===========================================================
Extracts text from PDF / plain-text resumes, identifies skills,
detects the likely target role, estimates experience, and performs
a **gap analysis** against a known skill taxonomy.
"""

import re
import io
from typing import Optional
from pdfminer.high_level import extract_text as pdf_extract_text


# ─── Skill taxonomy (canonical skills grouped by domain) ─────────────────────
SKILL_TAXONOMY: dict[str, list[str]] = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "sas",
    ],
    "Web Development": [
        "html", "css", "react", "angular", "vue", "node.js", "express",
        "django", "flask", "spring", "rails", "laravel", "next.js", "fastapi",
    ],
    "Data & Analytics": [
        "sql", "nosql", "mongodb", "postgresql", "mysql", "redis", "excel",
        "pivot tables", "tableau", "powerbi", "data analysis", "etl",
        "data pipelines", "data modeling", "data visualization",
    ],
    "Machine Learning & AI": [
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "scikit-learn", "nlp", "computer vision", "neural networks",
        "transformers", "reinforcement learning", "feature engineering",
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "ci/cd", "jenkins", "github actions", "ansible", "cloud",
        "microservices", "serverless", "linux", "bash",
    ],
    "Testing & QA": [
        "unit testing", "selenium", "pytest", "jest", "cypress",
        "api testing", "performance testing", "test automation", "qa",
        "jmeter", "tdd", "bdd",
    ],
    "Security": [
        "cybersecurity", "penetration testing", "owasp", "encryption",
        "network security", "firewalls", "ethical hacking", "soc",
        "vulnerability", "incident response", "cryptography",
    ],
    "Soft Skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "critical thinking", "presentation", "negotiation", "time management",
        "adaptability", "creativity", "empathy", "decision making",
        "conflict resolution", "project management", "agile", "scrum",
    ],
    "Domain Knowledge": [
        "finance", "accounting", "marketing", "sales", "hr", "recruitment",
        "supply chain", "healthcare", "insurance", "banking", "investment",
        "compliance", "risk management", "e-commerce", "ux design",
        "ui design", "graphic design", "content writing",
    ],
}

# Flat lookup: skill -> domain
_SKILL_TO_DOMAIN: dict[str, str] = {}
for _domain, _skills in SKILL_TAXONOMY.items():
    for _sk in _skills:
        _SKILL_TO_DOMAIN[_sk] = _domain

ALL_KNOWN_SKILLS: set[str] = set(_SKILL_TO_DOMAIN.keys())

# ─── Role detection patterns ─────────────────────────────────────────────────
ROLE_PATTERNS: list[tuple[str, str]] = [
    (r"data\s*scientist", "Data Scientist"),
    (r"data\s*analyst", "Data Analyst"),
    (r"data\s*engineer", "Data Engineer"),
    (r"machine\s*learning\s*engineer", "ML Engineer"),
    (r"ml\s*engineer", "ML Engineer"),
    (r"software\s*engineer", "Software Engineer"),
    (r"software\s*developer", "Software Engineer"),
    (r"full\s*stack", "Full Stack Developer"),
    (r"front\s*end|frontend", "Frontend Developer"),
    (r"back\s*end|backend", "Backend Developer"),
    (r"devops", "DevOps Engineer"),
    (r"cloud\s*engineer", "Cloud Engineer"),
    (r"site\s*reliability|sre", "Site Reliability Engineer"),
    (r"qa\s*engineer|quality\s*assurance", "QA Engineer"),
    (r"security\s*analyst|cybersecurity", "Security Analyst"),
    (r"network\s*engineer", "Network Engineer"),
    (r"project\s*manager", "Project Manager"),
    (r"product\s*manager", "Product Manager"),
    (r"business\s*analyst", "Business Analyst"),
    (r"ux\s*design|ui\s*design", "UX/UI Designer"),
    (r"marketing", "Marketing Specialist"),
    (r"human\s*resource|hr\s", "HR Professional"),
    (r"finance|financial\s*analyst", "Finance Analyst"),
    (r"consultant", "Consultant"),
    (r"manager", "Manager"),
    (r"analyst", "Analyst"),
    (r"engineer", "Engineer"),
    (r"developer", "Developer"),
]

# Experience-detection patterns
_EXP_PATTERNS = [
    re.compile(r"(\d{1,2})\+?\s*(?:years?|yrs?)[\s\w]*(?:experience|exp)", re.I),
    re.compile(r"(?:experience|exp)[\s:]*(\d{1,2})\+?\s*(?:years?|yrs?)", re.I),
    re.compile(r"(\d{4})\s*[-–]\s*(?:present|current|\d{4})", re.I),
]


class ResumeParser:
    """Extract structured profile data from a resume file."""

    def __init__(self, known_skills: Optional[set[str]] = None) -> None:
        self.known_skills = known_skills or ALL_KNOWN_SKILLS

    # ---------------------------------------------------------------- extract
    def extract_text(self, uploaded_file) -> str:
        """Return plain text from a Streamlit UploadedFile (PDF or TXT)."""
        name = uploaded_file.name.lower()
        raw = uploaded_file.read()

        if name.endswith(".pdf"):
            text = pdf_extract_text(io.BytesIO(raw))
        else:
            text = raw.decode("utf-8", errors="ignore")

        return text

    def parse(self, text: str) -> dict:
        """
        Analyse resume text and return a structured profile:
          - detected_skills: skills found in the resume
          - skill_domains: which domains the skills fall into
          - missing_skills_by_domain: skills NOT found, grouped by domain
          - detected_role: best-guess target role
          - estimated_experience: years (int)
          - raw_length: character count
        """
        lower = text.lower()
        cleaned = re.sub(r"[^a-z0-9\s/#+.]", " ", lower)
        cleaned = " ".join(cleaned.split())

        found_skills = self._find_skills(cleaned)
        skill_domains = self._group_by_domain(found_skills)
        missing = self._gap_analysis(found_skills)
        role = self._detect_role(cleaned)
        experience = self._estimate_experience(text)

        return {
            "detected_skills": sorted(found_skills),
            "skill_domains": skill_domains,
            "missing_skills_by_domain": missing,
            "detected_role": role,
            "estimated_experience": experience,
            "raw_length": len(text),
        }

    # ------------------------------------------------------------- internals
    def _find_skills(self, text: str) -> set[str]:
        found = set()
        for skill in self.known_skills:
            # Use word-boundary matching for short skills to avoid false positives
            if len(skill) <= 3:
                pattern = rf"\b{re.escape(skill)}\b"
            else:
                pattern = re.escape(skill)
            if re.search(pattern, text):
                found.add(skill)
        return found

    @staticmethod
    def _group_by_domain(skills: set[str]) -> dict[str, list[str]]:
        groups: dict[str, list[str]] = {}
        for sk in sorted(skills):
            domain = _SKILL_TO_DOMAIN.get(sk, "Other")
            groups.setdefault(domain, []).append(sk)
        return groups

    def _gap_analysis(self, found: set[str]) -> dict[str, list[str]]:
        """For each domain the user HAS skills in, list the ones they're missing."""
        user_domains = {_SKILL_TO_DOMAIN.get(s, "Other") for s in found}
        gaps: dict[str, list[str]] = {}
        for domain in sorted(user_domains):
            all_in_domain = set(SKILL_TAXONOMY.get(domain, []))
            missing = sorted(all_in_domain - found)
            if missing:
                gaps[domain] = missing
        return gaps

    @staticmethod
    def _detect_role(text: str) -> str:
        for pattern, role in ROLE_PATTERNS:
            if re.search(pattern, text):
                return role
        return "General"

    @staticmethod
    def _estimate_experience(text: str) -> int:
        # Try direct mention
        for pat in _EXP_PATTERNS[:2]:
            m = pat.search(text)
            if m:
                return min(int(m.group(1)), 30)

        # Try year-range spans (e.g., 2018 - Present)
        spans = re.findall(
            r"(20\d{2})\s*[-–]\s*(present|current|20\d{2})", text, re.I
        )
        if spans:
            from datetime import datetime
            current_year = datetime.now().year
            total = 0
            for start, end in spans:
                end_y = current_year if end.lower() in ("present", "current") else int(end)
                total += max(end_y - int(start), 0)
            return min(total, 30)

        return 0
