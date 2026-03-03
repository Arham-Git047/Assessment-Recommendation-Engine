"""
SHL Assessment Recommender – Streamlit Frontend
=================================================
Provides a clean, professional interface to:
  1. Enter a query / JD text / JD URL and get recommendations
  2. Browse the full catalogue
  3. View evaluation metrics and dataset statistics
  4. Export results as CSV

Launch
------
    streamlit run app/app.py
"""

from __future__ import annotations

import sys, io, re, logging
from pathlib import Path

import streamlit as st
import pandas as pd

# Ensure project root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.recommender import Recommender
from src.evaluation import mean_recall_at_k, LABELLED_QUERIES

logging.basicConfig(level=logging.INFO)

# ─── Page configuration ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="https://www.shl.com/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Design system (Inter font, charcoal / teal / green palette) ─────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', sans-serif;
}

/* Hero banner */
.hero {
    background: #1a1a2e;
    color: #ffffff;
    padding: 2.5rem 2rem 2rem 2rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
}
.hero h1 {
    font-weight: 800;
    font-size: 2rem;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.5px;
}
.hero p {
    font-weight: 400;
    font-size: 1rem;
    color: #b0b0c0;
    margin: 0;
}

/* Teal divider */
.teal-rule {
    height: 3px;
    background: linear-gradient(90deg, #2d9cdb 0%, #5b8a9a 50%, transparent 100%);
    margin: 0.4rem 0 1.8rem 0;
    border-radius: 2px;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 2px solid #e0e0e0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    color: #4a4a5a;
    padding: 0.7rem 1.5rem;
    border-bottom: 3px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #1a1a2e;
    border-bottom: 3px solid #2d9cdb;
}

/* Green CTA button */
.stButton > button {
    background: #00a86b;
    color: #fff;
    border: none;
    font-weight: 600;
    font-size: 0.95rem;
    border-radius: 6px;
    padding: 0.6rem 1.6rem;
    transition: background 0.2s;
}
.stButton > button:hover {
    background: #008f5a;
}

/* Data tables */
.stDataFrame {
    border: 1px solid #e8e8e8;
    border-radius: 8px;
}

/* Section headings */
h2, h3 {
    color: #1a1a2e;
    font-weight: 700;
}

/* Metric cards */
.metric-card {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1.2rem;
    text-align: center;
}
.metric-card .value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #1a1a2e;
}
.metric-card .label {
    font-size: 0.85rem;
    color: #6c6c7a;
    margin-top: 0.2rem;
}

/* Link styling in tables */
a { color: #2d9cdb; font-weight: 500; }
a:hover { color: #00a86b; }

/* ─── Input mode selector ─── */
.input-mode-bar {
    display: flex;
    gap: 0;
    margin-bottom: 1.4rem;
    border-radius: 8px;
    overflow: hidden;
    border: 2px solid #e0e0e0;
    background: #f0f0f0;
}
.input-mode-bar .mode-btn {
    flex: 1;
    text-align: center;
    padding: 0.7rem 1rem;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    color: #6c6c7a;
    cursor: pointer;
    transition: all 0.2s;
    border-right: 1px solid #e0e0e0;
    background: transparent;
}
.input-mode-bar .mode-btn:last-child { border-right: none; }
.input-mode-bar .mode-btn.active {
    background: #1a1a2e;
    color: #fff;
}
.input-mode-bar .mode-btn .icon {
    display: block;
    font-size: 1.3rem;
    margin-bottom: 0.15rem;
}

/* Input panels */
.input-panel {
    background: #f8f9fb;
    border: 1px solid #e4e6ea;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.input-panel-header {
    font-weight: 700;
    font-size: 1rem;
    color: #1a1a2e;
    margin-bottom: 0.15rem;
}
.input-panel-sub {
    font-size: 0.82rem;
    color: #8a8a9a;
    margin-bottom: 1rem;
}

/* Role chips */
.role-chip {
    display: inline-block;
    background: #eaf4f8;
    color: #2d6e8a;
    border: 1px solid #c8dfe8;
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 0.15rem 0.1rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Cached recommender ──────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading recommendation engine...")
def load_recommender() -> Recommender:
    return Recommender()


rec = load_recommender()

# ─── Hero banner ──────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <h1>SHL Assessment Recommender</h1>
    <p>Enter a job description, natural-language query, or URL to find the most relevant SHL assessments.</p>
</div>
<div class="teal-rule"></div>
""", unsafe_allow_html=True)

# ─── Tabs ─────────────────────────────────────────────────────────────────────

tab_recommend, tab_catalogue, tab_eval, tab_about = st.tabs([
    "Recommend", "Catalogue", "Evaluation", "About",
])

# ─── Job role presets for the dropdown ─────────────────────────────────────────

_JOB_ROLES = [
    # Engineering & Technology
    "Software Engineer", "Frontend Developer", "Backend Developer",
    "Full-Stack Developer", "DevOps Engineer", "Data Engineer",
    "Machine Learning Engineer", "Data Scientist", "Data Analyst",
    "QA / Test Engineer", "Mobile Developer (iOS/Android)",
    "Cloud Architect", "Site Reliability Engineer", "Security Engineer",
    "Systems Administrator", "Network Engineer", "Database Administrator",
    "Embedded Systems Engineer", "AI Research Scientist",
    # Business & Management
    "Project Manager", "Product Manager", "Business Analyst",
    "Management Consultant", "Operations Manager", "Account Manager",
    "Scrum Master", "Chief Technology Officer",
    # Sales & Marketing
    "Sales Representative", "Sales Manager", "Marketing Manager",
    "Digital Marketing Specialist", "Content Strategist", "Brand Manager",
    "SEO/SEM Specialist",
    # Finance & Accounting
    "Financial Analyst", "Accountant", "Auditor", "Investment Banker",
    "Actuary", "Risk Analyst", "Compliance Officer",
    # Customer Service & Support
    "Customer Service Representative", "Call Centre Agent",
    "Technical Support Specialist", "Help Desk Analyst",
    # Healthcare
    "Healthcare Administrator", "Registered Nurse", "Clinical Research Associate",
    "Pharmaceutical Sales Rep",
    # Human Resources
    "HR Manager", "Recruiter / Talent Acquisition",
    "Learning & Development Specialist", "Compensation Analyst",
    # Creative & Design
    "UX Designer", "UI Designer", "Graphic Designer", "UX Researcher",
    # Legal & Compliance
    "Legal Counsel", "Paralegal", "Compliance Analyst",
    # Trades & Operations
    "Warehouse Supervisor", "Retail Store Manager", "Supply Chain Analyst",
    "Logistics Coordinator", "Manufacturing Technician",
    "Mechanical Technician", "Electrician", "Construction Supervisor",
    # Education
    "Teacher / Educator", "Training Specialist",
    # Executive
    "Executive / C-Suite", "Senior Leadership / VP",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 1 – Recommend
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_recommend:
    st.subheader("Find Relevant Assessments")
    st.caption("Choose an input method below, then click **Get Recommendations**.")

    # ── Input mode selector (radio styled as segmented control) ───────────
    input_mode = st.radio(
        "Input method",
        ["Job Role", "Job Description URL", "Free-Text Query"],
        horizontal=True,
        label_visibility="collapsed",
    )

    # ── Shared settings row ───────────────────────────────────────────────
    query = ""

    if input_mode == "Job Role":
        st.markdown("**Select a Job Role**")
        st.markdown("<span style='font-size:0.85rem;color:#8a8a9a'>Pick a standard role from the dropdown, or type a custom title if yours is not listed.</span>", unsafe_allow_html=True)

        col_role, col_custom = st.columns([1, 1])
        with col_role:
            selected_role = st.selectbox(
                "Standard role",
                options=["-- Select a role --"] + sorted(_JOB_ROLES),
                index=0,
            )
        with col_custom:
            custom_role = st.text_input(
                "Or type a custom role",
                placeholder="e.g. Robotics Process Automation Developer",
            )

        # Determine final query
        if custom_role.strip():
            query = custom_role.strip()
        elif selected_role != "-- Select a role --":
            query = f"Assessment for a {selected_role}"

        # Show popular role chips for quick selection
        popular = ["Software Engineer", "Data Analyst", "Project Manager",
                   "Sales Manager", "Customer Service Representative",
                   "Financial Analyst", "UX Designer", "DevOps Engineer"]
        chips_html = " ".join(f'<span class="role-chip">{r}</span>' for r in popular)
        st.markdown(
            f'<div style="margin-top:0.3rem"><span style="font-size:0.78rem;color:#8a8a9a;font-weight:500">' \
            f'Popular:</span> {chips_html}</div>',
            unsafe_allow_html=True,
        )

    elif input_mode == "Job Description URL":
        st.markdown("**Paste a Job Description URL**")
        st.markdown("<span style='font-size:0.85rem;color:#8a8a9a'>We will fetch the page, extract the job description text, and find matching assessments.</span>", unsafe_allow_html=True)
        query = st.text_input(
            "URL",
            placeholder="https://www.example.com/careers/job-posting-123",
            label_visibility="collapsed",
        )

    else:  # Free-Text Query
        st.markdown("**Describe What You Need**")
        st.markdown("<span style='font-size:0.85rem;color:#8a8a9a'>Type a natural-language query or paste the full text of a job description.</span>", unsafe_allow_html=True)
        query = st.text_area(
            "Query",
            height=140,
            placeholder=(
                "Examples:\n"
                "- I need a cognitive ability test for graduate software engineers\n"
                "- Looking for personality and situational-judgement tests for a sales team lead\n"
                "- Paste a complete job description here..."
            ),
            label_visibility="collapsed",
        )

    # ── Button row ──────────────────────────────────────────────────────────
    search_clicked = st.button("Get Recommendations", type="primary")

    # ── Execute search ────────────────────────────────────────────────────
    if search_clicked and query.strip():
        resolved_query = query.strip()

        # If URL mode, fetch the page
        if input_mode == "Job Description URL" and re.match(r"^https?://\S+$", resolved_query):
            with st.spinner("Fetching job description from URL..."):
                try:
                    import httpx
                    from bs4 import BeautifulSoup as BS

                    resp = httpx.get(resolved_query, follow_redirects=True, timeout=15)
                    resp.raise_for_status()
                    soup = BS(resp.text, "lxml")
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    resolved_query = soup.get_text(separator=" ", strip=True)[:3000]
                    st.info(f"Extracted {len(resolved_query)} characters from the URL.")
                except Exception as exc:
                    st.warning(f"Could not fetch URL: {exc}. Using raw URL as query.")

        with st.spinner("Searching..."):
            results = rec.recommend(resolved_query, top_k=20)

        if results:
            st.success(f"Found {len(results)} relevant assessments.")

            # Build display DataFrame
            display_data = []
            for r in results:
                display_data.append({
                    "Assessment Name": r["assessment_name"],
                    "URL": r["url"],
                    "Test Type": r["test_type"],
                    "Remote": r["remote_support"],
                    "Adaptive": r["adaptive_support"],
                    "Duration (min)": r["duration"],
                    "Description": r["description"],
                })

            df = pd.DataFrame(display_data)

            st.markdown("#### Results")
            st.dataframe(
                df,
                column_config={
                    "URL": st.column_config.LinkColumn("URL", display_text="Open"),
                    "Duration (min)": st.column_config.NumberColumn(format="%d"),
                },
                use_container_width=True,
                hide_index=True,
            )

            # CSV export
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            st.download_button(
                "Export CSV",
                data=csv_buf.getvalue(),
                file_name="shl_recommendations.csv",
                mime="text/csv",
            )
        else:
            st.warning("No matching assessments found. Try a different query.")

    elif search_clicked:
        if input_mode == "Job Role":
            st.warning("Please select a role from the dropdown or type a custom role.")
        elif input_mode == "Job Description URL":
            st.warning("Please enter a valid URL.")
        else:
            st.warning("Please enter a query or job description.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 2 – Catalogue
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_catalogue:
    st.subheader("SHL Assessment Catalogue")

    cat_df = rec.catalogue_df()
    total = len(cat_df)

    # Summary metrics
    cols = st.columns(4)
    with cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{total}</div>
            <div class="label">Total Assessments</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[1]:
        n_types = cat_df["test_type"].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{n_types}</div>
            <div class="label">Test Types</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[2]:
        remote_pct = int((cat_df["remote_support"] == "Yes").mean() * 100)
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{remote_pct}%</div>
            <div class="label">Remote Support</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[3]:
        adaptive_pct = int((cat_df["adaptive_support"] == "Yes").mean() * 100)
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{adaptive_pct}%</div>
            <div class="label">Adaptive Support</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Filter controls
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        type_filter = st.multiselect(
            "Filter by Test Type",
            options=sorted(cat_df["test_type"].unique()),
        )
    with f_col2:
        search_filter = st.text_input("Search by name", "")

    filtered = cat_df.copy()
    if type_filter:
        filtered = filtered[filtered["test_type"].isin(type_filter)]
    if search_filter:
        filtered = filtered[
            filtered["assessment_name"].str.contains(search_filter, case=False, na=False)
        ]

    st.dataframe(
        filtered,
        column_config={
            "url": st.column_config.LinkColumn("URL", display_text="Open"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # Distribution chart
    st.markdown("#### Assessments by Test Type")
    type_counts = cat_df["test_type"].value_counts().reset_index()
    type_counts.columns = ["Test Type", "Count"]
    st.bar_chart(type_counts, x="Test Type", y="Count", color="#2d9cdb")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 3 – Evaluation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_eval:
    st.subheader("Evaluation Metrics")

    eval_k = st.slider("K for Recall@K", min_value=1, max_value=20, value=10, key="eval_k")

    if st.button("Run Evaluation", type="primary"):
        with st.spinner("Evaluating on labelled queries..."):
            report = mean_recall_at_k(rec, k=eval_k)

        st.markdown(f"""
        <div class="metric-card" style="max-width:300px">
            <div class="value">{report['mean_recall_at_k']:.4f}</div>
            <div class="label">Mean Recall@{report['k']} ({report['num_queries']} queries)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Per-Query Results")

        eval_rows = []
        for pq in report["per_query"]:
            eval_rows.append({
                "Query": pq["query"][:80],
                "Recall@K": f"{pq['recall_at_k']:.2f}",
                "Hits": len(pq["hits"]),
                "Expected": len(pq["expected"]),
                "Hit Names": ", ".join(pq["hits"]) if pq["hits"] else "None",
            })
        st.dataframe(pd.DataFrame(eval_rows), use_container_width=True, hide_index=True)

        # Export evaluation report
        import json
        report_json = json.dumps(report, indent=2)
        st.download_button(
            "Export Evaluation Report (JSON)",
            data=report_json,
            file_name="evaluation_report.json",
            mime="application/json",
        )
    else:
        st.info(
            "Click **Run Evaluation** to compute Mean Recall@K using the "
            f"{len(LABELLED_QUERIES)} labelled test queries."
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TAB 4 – About
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_about:
    st.subheader("About This System")

    health = rec.health()

    st.markdown(f"""
**SHL Assessment Recommender** is a retrieval-augmented recommendation engine
that helps hiring managers and talent acquisition teams find the most relevant
SHL individual test solutions for any role.

---

**Architecture**

| Component | Detail |
|-----------|--------|
| Retrieval | Hybrid dense (sentence-transformers) + sparse (TF-IDF) |
| Embeddings | all-MiniLM-L6-v2 (384-dim) via sentence-transformers |
| Vector Store | FAISS (IndexFlatIP, cosine similarity) |
| API | FastAPI with /health and /recommend endpoints |
| Frontend | Streamlit |
| Catalogue | {health['catalogue_size']} individual SHL test solutions |
| Backend | {health['backend']} |

---

**How It Works**

1. A query (natural language, JD text, or JD URL) is received.
2. If a URL is provided, the page is fetched and text is extracted.
3. The query is encoded into a 384-dimensional vector using all-MiniLM-L6-v2.
4. FAISS retrieves the top candidates by cosine similarity (dense retrieval).
5. TF-IDF cosine similarity provides a parallel sparse retrieval signal.
6. Scores are blended (70% dense, 30% sparse) and the top-K results are returned.
7. Each result includes the assessment name, SHL URL, test type, duration,
   remote support, adaptive support, and a description.

---

**API Endpoints**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health and catalogue metadata |
| POST | `/recommend` | Get assessment recommendations |

**POST /recommend** request body:
```json
{{"query": "your query here", "top_k": 10}}
```
""")
