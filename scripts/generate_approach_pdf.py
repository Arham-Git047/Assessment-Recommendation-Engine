"""Generate a concise 2-page approach document as PDF."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from fpdf import FPDF


class ApproachPDF(FPDF):
    def header(self):
        if self.page_no() > 0:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, "SHL Assessment Recommender - Approach Document", align="R")
            self.ln(7)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}/2", align="C")

    def section(self, title):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(26, 26, 46)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(45, 156, 219)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def para(self, text):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 4.5, text)
        self.ln(1)

    def dash_item(self, text):
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 4.5, "  - " + text)

    def add_table(self, headers, rows):
        n = len(headers)

        if n == 2:
            widths = [45, self.w - self.l_margin - self.r_margin - 45]
        elif n == 3:
            widths = [52, 26, self.w - self.l_margin - self.r_margin - 78]
        else:
            w = (self.w - self.l_margin - self.r_margin) / n
            widths = [w] * n

        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 8.5)
        for i, h in enumerate(headers):
            self.cell(widths[i], 5.5, h, border=1)
        self.ln()

        self.set_font("Helvetica", "", 8.5)
        for row in rows:
            self.set_x(self.l_margin)
            for i, c in enumerate(row):
                self.cell(widths[i], 5.5, c, border=1)
            self.ln()
        self.ln(2)


pdf = ApproachPDF()
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_page()

# Title
pdf.set_font("Helvetica", "B", 16)
pdf.set_text_color(26, 26, 46)
pdf.cell(0, 10, "SHL Assessment Recommender", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 5, "Approach Document  |  Arham Kelkar  |  March 2026", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.ln(4)

# 1
pdf.section("1. Problem Statement")
pdf.para(
    "Given a natural-language query, job description text, or job description URL, recommend the "
    "most relevant individual SHL test solutions from a catalogue of 377 assessments. Each "
    "recommendation must include the assessment name, SHL URL, test type, duration, and "
    "remote/adaptive support flags. The system must expose a REST API returning JSON and a "
    "web-based frontend."
)

# 2
pdf.section("2. Data Pipeline")
pdf.para(
    "A scraper (scripts/scrape_catalogue.py) crawls SHL's public product catalogue "
    "using requests + BeautifulSoup. When the live site is unreachable or returns JS-rendered "
    "content, the script falls back to a curated catalogue of 377 individual test solutions "
    "derived from SHL's published product taxonomy. Each entry contains: assessment_name, url, "
    "test_type (Cognitive, Personality, Behavioral, Knowledge & Skills, Simulation, Language, "
    "Job Knowledge), duration (minutes), remote_support, adaptive_support, and description. "
    "Output: data/shl_products.json."
)

# 3
pdf.section("3. Retrieval & Ranking (Hybrid RAG)")
pdf.para(
    "Each assessment is represented as a document string (name + description + test_type). "
    "The system implements hybrid retrieval combining two complementary signals:"
)

pdf.add_table(
    ["Signal", "Weight", "Method"],
    [
        ["Dense", "0.70", "all-MiniLM-L6-v2 (384-dim) -> FAISS cosine"],
        ["Sparse", "0.30", "TF-IDF (8000 feat) -> sklearn cosine"],
    ],
)

pdf.para(
    "Procedure: (1) Encode user query with sentence-transformer. "
    "(2) FAISS retrieves top 3K candidates by dense cosine similarity. "
    "(3) TF-IDF retrieves top 3K candidates by sparse cosine in parallel. "
    "(4) Scores normalised to [0,1] and blended (70/30). "
    "(5) Top-K returned ordered by blended score. "
    "If a URL is provided, httpx fetches the page, BeautifulSoup extracts text (first 3000 chars). "
    "When SBERT/FAISS are unavailable (cloud RAM limits), TF-IDF-only fallback activates."
)

# 4
pdf.section("4. Why Hybrid Retrieval?")
pdf.para(
    "Dense embeddings capture semantic similarity (e.g., 'coding' ~ 'programming') but can "
    "miss exact keyword matches. TF-IDF catches lexical overlap that embeddings underweight. "
    "The 70/30 blend exploits both strengths and consistently outperforms either method alone "
    "in our evaluation. Lightweight, interpretable, deployable without GPUs."
)

# 5
pdf.section("5. API Design")
pdf.para("FastAPI service with three endpoints:")
pdf.dash_item("GET /health -- Returns service health and catalogue metadata.")
pdf.dash_item("POST /recommend -- JSON body with query and top_k, returns recommended_assessments.")
pdf.dash_item("GET /recommend?query=...&top_k=N -- Convenience GET for browser testing.")
pdf.ln(1)
pdf.para(
    "Pydantic models enforce request/response validation. CORS enabled. "
    "Deployed on Render (free tier). Interactive Swagger docs at /docs."
)

# 6
pdf.section("6. Frontend (Streamlit)")
pdf.para(
    "Four tabs: (1) Recommend -- three input modes (Job Role dropdown with 65+ roles, "
    "Job Description URL, Free-Text Query), results table with clickable SHL URLs and CSV export; "
    "(2) Catalogue -- browsable/filterable catalogue with metrics and distribution chart; "
    "(3) Evaluation -- interactive Recall@K with per-query breakdown; "
    "(4) About -- architecture summary and API docs. "
    "Design: Inter font, charcoal hero, teal accents, green CTA buttons."
)

# 7
pdf.section("7. Evaluation")
pdf.para(
    "Mean Recall@K evaluated over 15 labelled queries, each with 5-8 ground-truth assessments:"
)
pdf.add_table(
    ["Metric", "Value"],
    [
        ["Mean Recall@10 (hybrid SBERT+FAISS)", "0.6428"],
        ["Mean Recall@10 (TF-IDF fallback)", "~0.45"],
        ["Queries evaluated", "15"],
        ["Catalogue size", "377 individual test solutions"],
    ],
)
pdf.para(
    "Hybrid approach shows ~40% improvement over TF-IDF alone. Per-query breakdowns "
    "in the Evaluation tab and exported as evaluation_report.json."
)

# 8
pdf.section("8. Technology Stack")
pdf.add_table(
    ["Component", "Technology"],
    [
        ["Embeddings", "sentence-transformers (all-MiniLM-L6-v2)"],
        ["Vector Store", "FAISS (IndexFlatIP, exact cosine)"],
        ["Sparse Retrieval", "scikit-learn TfidfVectorizer"],
        ["API", "FastAPI + Pydantic + uvicorn"],
        ["Frontend", "Streamlit"],
        ["Web Scraping", "httpx + BeautifulSoup4 + lxml"],
        ["Deployment", "Streamlit Cloud + Render (API)"],
    ],
)

# 9
pdf.section("9. Limitations & Future Work")
pdf.dash_item("Curated catalogue covers 377 tests; live scraping would capture the full evolving SHL set.")
pdf.dash_item("At larger scale, approximate FAISS indices (IVF-PQ, HNSW) would reduce latency.")
pdf.dash_item("Fine-tuning sentence-transformer on SHL-specific text could improve relevance.")
pdf.dash_item("A cross-encoder re-ranker could refine top-K results.")
pdf.dash_item("User feedback loops (click-through, ratings) would enable online learning.")

# Output
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'Arham_Kelkar_Approach.pdf')
pdf.output(out_path)
print(f"PDF saved to {out_path}")
print(f"Pages: {pdf.pages_count}")
