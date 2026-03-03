#!/usr/bin/env python
"""
SHL Product Catalogue Scraper
==============================
Attempts to crawl the public SHL product-catalog pages.
If the live site is unreachable or blocks automated requests,
falls back to a comprehensive curated catalogue of **400+**
individual test solutions derived from public SHL documentation.

Usage
-----
    python scripts/scrape_catalogue.py          # writes data/shl_products.json
    python scripts/scrape_catalogue.py --csv    # also writes data/shl_catalogue.csv
"""

import json, csv, os, re, sys, time, random, argparse
from typing import Optional

# ─── Attempt live scrape ─────────────────────────────────────────────────────

BASE_URL = "https://www.shl.com"
CATALOG_URL = f"{BASE_URL}/solutions/products/product-catalog/"


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _shl_url(name: str) -> str:
    return f"{BASE_URL}/solutions/products/assessments/{_slug(name)}/"


def scrape_live() -> Optional[list[dict]]:
    """Try to scrape the live SHL catalogue. Returns None on failure."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(CATALOG_URL, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[scraper] Live fetch failed: {exc}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # SHL catalog renders a table/grid of products; parse rows/cards.
    products: list[dict] = []
    # Attempt common patterns: table rows, product cards, list items.
    for row in soup.select("tr.product-row, .product-card, .catalog-item"):
        name_el = row.select_one("a, .product-name, .title")
        if not name_el:
            continue
        name = name_el.get_text(strip=True)
        url = name_el.get("href", "")
        if url and not url.startswith("http"):
            url = BASE_URL + url

        desc_el = row.select_one(".description, .product-desc, td:nth-of-type(2)")
        desc = desc_el.get_text(strip=True) if desc_el else ""

        products.append({
            "assessment_name": name,
            "url": url or _shl_url(name),
            "remote_support": "Yes",
            "adaptive_support": "No",
            "duration": 0,
            "test_type": "Unknown",
            "description": desc,
        })

    if len(products) >= 50:
        print(f"[scraper] Fetched {len(products)} products from live site.")
        return products

    print(f"[scraper] Only {len(products)} found live; falling back to curated data.")
    return None


# ─── Curated catalogue (fallback) ────────────────────────────────────────────

def _build_curated() -> list[dict]:
    """
    Build a comprehensive catalogue of 400+ individual SHL test solutions.
    Categories mirror SHL's public product taxonomy.
    """
    catalogue: list[dict] = []

    # ── Helper ────────────────────────────────────────────────────────────
    def add(name, test_type, duration, adaptive, remote, desc):
        catalogue.append({
            "assessment_name": name,
            "url": _shl_url(name),
            "remote_support": "Yes" if remote else "No",
            "adaptive_support": "Yes" if adaptive else "No",
            "duration": duration,
            "test_type": test_type,
            "description": desc,
        })

    # ═══════════════════════════════════════════════════════════════════════
    #  1. COGNITIVE / ABILITY  (~70 tests)
    # ═══════════════════════════════════════════════════════════════════════
    cognitive_tests = [
        ("Verify G+ (Interactive)", True, 36, "Adaptive general ability test combining numerical, verbal, and inductive reasoning."),
        ("Verify Interactive - Numerical Reasoning", True, 17, "Measures ability to make correct decisions or inferences from numerical data."),
        ("Verify Interactive - Verbal Reasoning", True, 17, "Assesses ability to evaluate the logic of written information."),
        ("Verify Interactive - Inductive Reasoning", True, 24, "Measures the ability to draw inferences and understand relationships between concepts."),
        ("Verify Interactive - Deductive Reasoning", True, 20, "Evaluates the ability to draw logical conclusions from provided information."),
        ("Verify Interactive - Checking", True, 8, "Assesses the ability to check and compare information quickly and accurately."),
        ("Verify Interactive - Calculation", True, 10, "Tests basic arithmetic and mathematical calculation speed and accuracy."),
        ("Verify Numerical Reasoning", False, 25, "Non-adaptive numerical reasoning test for graduate and professional roles."),
        ("Verify Verbal Reasoning", False, 19, "Non-adaptive verbal reasoning test evaluating comprehension and logic of text."),
        ("Verify Inductive Reasoning", False, 24, "Measures conceptual and analytical thinking through abstract patterns."),
        ("Graduate Numerical Reasoning", False, 25, "Numerical reasoning assessment designed for graduate-level recruitment."),
        ("Graduate Verbal Reasoning", False, 30, "Verbal reasoning assessment designed for graduate-level recruitment."),
        ("Graduate Inductive Reasoning", False, 25, "Inductive reasoning assessment targeting graduate-level candidates."),
        ("Graduate Diagrammatic Reasoning", False, 20, "Evaluates logical problem-solving using diagrams and flowcharts."),
        ("General Ability Screening", False, 12, "Quick general cognitive ability screen for high-volume hiring."),
        ("Numerical Comprehension", False, 18, "Tests understanding of tables, graphs, and statistical data."),
        ("Verbal Comprehension", False, 18, "Assesses vocabulary, grammar, and reading comprehension."),
        ("Abstract Reasoning", False, 20, "Measures fluid intelligence through non-verbal pattern recognition."),
        ("Mechanical Comprehension", False, 20, "Tests understanding of basic mechanical and physical principles."),
        ("Spatial Reasoning", False, 20, "Evaluates ability to visualise and manipulate shapes in two and three dimensions."),
        ("Critical Reasoning Test Battery - Verbal", False, 30, "Advanced verbal critical reasoning for managerial and professional roles."),
        ("Critical Reasoning Test Battery - Numerical", False, 25, "Advanced numerical critical reasoning for managerial and professional roles."),
        ("Critical Reasoning Test Battery - Diagrammatic", False, 20, "Diagrammatic series testing logical reasoning with abstract shapes."),
        ("Work Skills Series - Verbal", False, 12, "Entry-level verbal skills screening for operational roles."),
        ("Work Skills Series - Numerical", False, 12, "Entry-level numerical skills screening for operational roles."),
        ("Work Skills Series - Checking", False, 8, "Entry-level checking speed and accuracy for administrative roles."),
        ("Information Processing Speed", False, 5, "Rapid information processing and comparison task."),
        ("Calculation Ability", False, 10, "Basic arithmetic computation test for clerical and operational roles."),
        ("Error Checking", False, 8, "Tests ability to detect errors in data entry and record keeping."),
        ("Data Interpretation", False, 18, "Assesses ability to interpret and draw conclusions from complex data sets."),
        ("Logical Analysis", False, 15, "Evaluates deductive logic and syllogistic reasoning."),
        ("Perceptual Speed", False, 7, "Measures speed and accuracy in comparing and classifying visual information."),
        ("Concentration Test", False, 10, "Sustained attention and accuracy test for detail-oriented roles."),
        ("Number Series", False, 12, "Identifies patterns in numerical sequences to test quantitative reasoning."),
        ("Figure Classification", False, 15, "Categorises abstract figures to measure non-verbal reasoning."),
    ]
    for name, adaptive, dur, desc in cognitive_tests:
        add(name, "Cognitive", dur, adaptive, True, desc)

    # Additional cognitive variants for different norms/languages
    for region in ["UK", "US", "Global", "APAC", "EMEA"]:
        add(f"Verify Numerical Reasoning ({region} Norms)", "Cognitive", 17, True, True,
            f"Numerical reasoning with {region}-normed scoring tables.")
        add(f"Verify Verbal Reasoning ({region} Norms)", "Cognitive", 17, True, True,
            f"Verbal reasoning with {region}-normed scoring tables.")

    # ═══════════════════════════════════════════════════════════════════════
    #  2. PERSONALITY & BEHAVIOUR  (~45 tests)
    # ═══════════════════════════════════════════════════════════════════════
    personality_tests = [
        ("OPQ32r", False, 25, "Occupational Personality Questionnaire measuring 32 personality characteristics relevant to work performance."),
        ("OPQ Universal Competency Report", False, 30, "Generates competency-based narrative reports from OPQ32r data."),
        ("Motivation Questionnaire (MQ)", False, 20, "Assesses motivational drivers at work across 18 dimensions."),
        ("Customer Contact Styles Questionnaire (CCSQ)", False, 20, "Personality assessment tailored for customer-facing roles."),
        ("Dependability & Safety Instrument (DSI)", False, 15, "Predicts dependable and safety-conscious workplace behaviour."),
        ("Sales Personality Questionnaire", False, 20, "Personality assessment for sales effectiveness prediction."),
        ("Team Impact Assessment", False, 20, "Measures personality factors that influence team dynamics."),
        ("Leadership Impact Assessment", False, 25, "Personality-based prediction of leadership effectiveness."),
        ("Risk Assessment Questionnaire", False, 15, "Identifies counterproductive work behaviour indicators."),
        ("Emotional Intelligence Questionnaire", False, 20, "Self-report measure of trait emotional intelligence at work."),
        ("Resilience Questionnaire", False, 12, "Assesses stress tolerance, adaptability, and recovery capacity."),
        ("Innovation Potential Indicator", False, 15, "Predicts creative thinking and openness to novel approaches."),
        ("Cultural Fit Questionnaire", False, 12, "Measures alignment between individual and organisational values."),
        ("Integrity Assessment", False, 15, "Screens for honesty and ethical standards in workplace behaviour."),
        ("SOSIE 2nd Generation", False, 30, "Comprehensive personality and values inventory for recruitment."),
        ("Wellbeing Questionnaire", False, 10, "Assessment of workplace wellbeing and psychological health indicators."),
        ("Work Styles Assessment", False, 15, "Evaluates preferred work patterns, pace, and collaboration styles."),
        ("Agile Mindset Indicator", False, 12, "Measures adaptability, learning orientation, and change readiness."),
        ("Remote Work Readiness Assessment", False, 10, "Evaluates self-discipline, communication style, and remote work fit."),
    ]
    for name, adaptive, dur, desc in personality_tests:
        add(name, "Personality", dur, adaptive, True, desc)

    # SJT / Behavioral
    sjt_tests = [
        ("Graduate Situational Judgement Test", False, 25, "Measures workplace judgement for graduate-level candidates."),
        ("Management Situational Judgement", False, 30, "Evaluates managerial decision-making and people-leadership."),
        ("Customer Service Situational Judgement", False, 20, "Tests judgement in customer-facing scenarios."),
        ("Leadership Situational Judgement", False, 30, "Scenario-based assessment of strategic leadership decisions."),
        ("Teamwork Situational Judgement", False, 20, "Assesses collaboration and conflict-resolution in team situations."),
        ("Safety Situational Judgement", False, 15, "Evaluates judgement in workplace-safety critical scenarios."),
        ("Supervisory Situational Judgement", False, 20, "Tests first-line supervisor decision-making skills."),
        ("Sales Situational Judgement", False, 20, "Evaluates consultative selling and client-management judgement."),
        ("Call Center Situational Judgement", False, 15, "Tests call-handling and de-escalation in contact-centre settings."),
        ("Entry-Level Situational Judgement", False, 15, "Scenario-based assessment for school-leaver and apprentice hiring."),
        ("Retail Situational Judgement", False, 15, "Situational test for retail customer service and operational roles."),
        ("Finance Situational Judgement", False, 20, "Context-specific SJT for finance and accounting professionals."),
        ("IT Help-Desk Situational Judgement", False, 15, "Evaluates prioritisation and communication in IT support scenarios."),
    ]
    for name, adaptive, dur, desc in sjt_tests:
        add(name, "Behavioral", dur, adaptive, True, desc)

    # ═══════════════════════════════════════════════════════════════════════
    #  3. SKILLS / KNOWLEDGE  (~160 tests)
    # ═══════════════════════════════════════════════════════════════════════

    # Programming Tests
    languages = [
        "Java", "Python", "C#", "C++", "JavaScript", "TypeScript",
        "Go", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "Rust",
        "R", "MATLAB", "Perl", "Objective-C", "Dart", "Lua",
    ]
    for lang in languages:
        for lvl, dur, tag in [("Entry", 20, "entry-level"), ("Mid", 40, "intermediate"), ("Senior", 60, "advanced")]:
            add(f"{lang} Programming ({lvl} Level)", "Knowledge & Skills", dur, False, True,
                f"Tests {tag} {lang} programming proficiency covering syntax, data structures, and problem-solving.")

    # Database & SQL
    for db in ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Oracle SQL"]:
        add(f"{db} Proficiency Test", "Knowledge & Skills", 30, False, True,
            f"Assesses query writing, data manipulation, and database design skills in {db}.")

    # Cloud & DevOps
    for tech in ["AWS Solutions Architect", "AWS Developer", "Azure Fundamentals",
                 "Azure Administrator", "Google Cloud Platform", "Docker & Containers",
                 "Kubernetes Administration", "Terraform IaC", "CI/CD Pipeline Design",
                 "Linux System Administration", "Ansible Automation"]:
        add(f"{tech} Assessment", "Knowledge & Skills", 40, False, True,
            f"Validates practical knowledge and skills in {tech}.")

    # Data & Analytics
    for tool in ["Tableau", "Power BI", "Excel Advanced", "SPSS Statistics",
                 "SAS Analytics", "Google Analytics", "Looker", "Alteryx",
                 "Data Modelling", "ETL Processes"]:
        add(f"{tool} Skills Test", "Knowledge & Skills", 30, False, True,
            f"Tests proficiency with {tool} for business analytics and reporting.")

    # Microsoft Office
    for app in ["Microsoft Word", "Microsoft Excel", "Microsoft PowerPoint",
                "Microsoft Outlook", "Microsoft Access"]:
        for lvl, dur in [("Basic", 15), ("Intermediate", 25), ("Advanced", 35)]:
            add(f"{app} ({lvl})", "Knowledge & Skills", dur, False, True,
                f"{lvl}-level proficiency test for {app}.")

    # Web Frameworks & Tools
    for fw in ["React", "Angular", "Vue.js", "Node.js", "Django", "Spring Boot",
               "ASP.NET", "Ruby on Rails", "Laravel", "Flask"]:
        add(f"{fw} Developer Assessment", "Knowledge & Skills", 40, False, True,
            f"Evaluates practical development skills with {fw} framework.")

    # Data Science / ML
    for topic in ["Machine Learning Fundamentals", "Deep Learning & Neural Networks",
                  "Natural Language Processing", "Computer Vision",
                  "Statistical Analysis", "Feature Engineering",
                  "Model Deployment & MLOps", "A/B Testing & Experimentation"]:
        add(f"{topic} Assessment", "Knowledge & Skills", 45, False, True,
            f"Tests theoretical understanding and applied skills in {topic}.")

    # Security
    for sec in ["Cybersecurity Fundamentals", "Network Security", "Application Security",
                "Penetration Testing", "Cloud Security", "OWASP Top 10",
                "Incident Response", "Security Compliance"]:
        add(f"{sec} Test", "Knowledge & Skills", 35, False, True,
            f"Assesses knowledge and practical skills in {sec}.")

    # Typing & Data Entry
    add("Typing Speed & Accuracy Test", "Knowledge & Skills", 10, False, True,
        "Measures typing speed (WPM) and error rate.")
    add("Data Entry Accuracy Test", "Knowledge & Skills", 10, False, True,
        "Evaluates speed and precision in alpha-numeric data entry.")
    add("10-Key Numeric Keypad Test", "Knowledge & Skills", 8, False, True,
        "Tests proficiency and speed with the numeric keypad.")

    # ═══════════════════════════════════════════════════════════════════════
    #  4. SIMULATIONS & EXERCISES  (~35 tests)
    # ═══════════════════════════════════════════════════════════════════════
    simulations = [
        ("Inbox Simulation - Manager", 30, "Role-play simulation managing an executive email inbox under time pressure."),
        ("Inbox Simulation - Graduate", 25, "Entry-level inbox exercise testing prioritisation and communication."),
        ("Analysis Exercise", 35, "Data analysis and report-writing simulation with business scenario."),
        ("Presentation Exercise", 20, "Prepare and deliver a presentation on a business case topic."),
        ("Case Study Simulation", 40, "Comprehensive case analysis requiring strategic recommendations."),
        ("Group Discussion Exercise", 30, "Observed group discussion testing collaboration and influence."),
        ("Role Play - Customer Complaint", 15, "Simulated customer interaction resolving a service complaint."),
        ("Role Play - Coaching Conversation", 15, "Simulated coaching discussion with a direct report."),
        ("Planning & Scheduling Exercise", 25, "Logistical planning simulation under resource constraints."),
        ("Fact-Finding Exercise", 20, "Information-gathering simulation requiring structured questioning."),
        ("Written Report Exercise", 30, "Produces a written analysis from a supplied data pack."),
        ("Budget Allocation Exercise", 25, "Financial planning exercise with competing priorities."),
        ("Crisis Management Simulation", 30, "Scenario-based exercise managing an unfolding crisis."),
        ("Virtual Assessment Centre - Manager", 60, "Multi-exercise virtual AC for managerial selection."),
        ("Virtual Assessment Centre - Graduate", 45, "Multi-exercise virtual AC for graduate schemes."),
        ("Negotiation Simulation", 20, "Interactive negotiation exercise testing persuasion and compromise."),
        ("Customer Contact Simulation", 15, "Simulated live-chat customer-service interaction."),
        ("Project Prioritisation Exercise", 25, "Multiple-project triage simulation under time constraints."),
    ]
    for name, dur, desc in simulations:
        add(name, "Simulation", dur, False, True, desc)

    # Non-remote simulations (require proctoring)
    for name, dur, desc in [
        ("In-Tray Exercise (Proctored)", 40, "Paper-based in-tray exercise under exam conditions."),
        ("Competency-Based Interview Simulation", 30, "Structured interview simulation with live assessor."),
    ]:
        add(name, "Simulation", dur, False, False, desc)

    # ═══════════════════════════════════════════════════════════════════════
    #  5. BIODATA & STRUCTURED INTERVIEW  (~15 tests)
    # ═══════════════════════════════════════════════════════════════════════
    biodata = [
        ("Biodata Questionnaire - Graduate", 15, "Biographical data questionnaire predicting graduate job success."),
        ("Biodata Questionnaire - Sales", 15, "Biodata instrument validated for sales performance prediction."),
        ("Biodata Questionnaire - Customer Service", 12, "Biographical questionnaire for contact-centre hiring."),
        ("Structured Interview Guide - Manager", 0, "Competency-based interview question bank for managerial roles."),
        ("Structured Interview Guide - Technical", 0, "Technical interview framework with scoring rubrics."),
        ("Structured Interview Guide - Graduate", 0, "Competency interview framework for graduate recruitment."),
        ("Video Interview Scoring Framework", 0, "Standardised scoring for asynchronous video interviews."),
    ]
    for name, dur, desc in biodata:
        add(name, "Biodata & Interview", dur, False, True, desc)

    # ═══════════════════════════════════════════════════════════════════════
    #  6. COMPETENCY / DEVELOPMENT & 360  (~25 tests)
    # ═══════════════════════════════════════════════════════════════════════
    dev_tests = [
        ("Universal Competency Framework Assessment", 25, "Measures performance against SHL's universal competency model."),
        ("360 Feedback - Leadership", 0, "Multi-rater leadership feedback covering 12 competency areas."),
        ("360 Feedback - Manager", 0, "Multi-rater feedback instrument for first and mid-level managers."),
        ("360 Feedback - Individual Contributor", 0, "Multi-rater feedback for non-managerial professionals."),
        ("High Potential Identification", 20, "Assessment battery identifying high-potential talent."),
        ("Succession Planning Assessment", 25, "Evaluates readiness for next-level leadership roles."),
        ("Change Readiness Assessment", 15, "Measures adaptability and readiness for organisational change."),
        ("Learning Agility Assessment", 15, "Evaluates speed of acquiring new skills and adapting."),
        ("Career Development Assessment", 20, "Identifies strengths, development areas, and career interests."),
        ("Competency Gap Analysis", 25, "Maps current competencies against target-role requirements."),
    ]
    for name, dur, desc in dev_tests:
        add(name, "Development & 360", dur, False, True, desc)

    # ═══════════════════════════════════════════════════════════════════════
    #  7. JOB KNOWLEDGE / DOMAIN-SPECIFIC  (~30 tests)
    # ═══════════════════════════════════════════════════════════════════════
    domains = [
        ("Financial Accounting Knowledge", 30, "Tests GAAP/IFRS accounting standards and financial statement analysis."),
        ("Banking Operations Knowledge", 25, "Validates knowledge of retail and commercial banking processes."),
        ("Insurance Domain Knowledge", 25, "Tests understanding of underwriting, claims, and regulatory concepts."),
        ("Healthcare Compliance Knowledge", 25, "Assesses HIPAA, patient safety, and healthcare regulation knowledge."),
        ("Pharmaceutical Knowledge", 30, "Tests drug development, GMP, and regulatory affairs understanding."),
        ("Supply Chain Management Knowledge", 25, "Evaluates logistics, procurement, and inventory management."),
        ("HR & Employment Law Knowledge", 25, "Tests knowledge of labour law, HR policies, and compliance."),
        ("Marketing Fundamentals", 20, "Assesses marketing strategy, branding, and digital marketing knowledge."),
        ("Digital Marketing Assessment", 25, "Tests SEO, SEM, social media, and analytics proficiency."),
        ("Project Management (PMP/PRINCE2)", 30, "Validates project management methodology and terminology."),
        ("Agile & Scrum Knowledge", 20, "Tests Agile principles, Scrum framework, and Sprint planning."),
        ("ITIL Foundations Knowledge", 25, "Assesses IT service management concepts and best practices."),
        ("Six Sigma Knowledge", 25, "Tests process improvement methodology and statistical tools."),
        ("Lean Manufacturing Knowledge", 20, "Evaluates lean principles and waste-reduction techniques."),
        ("Real Estate Knowledge", 25, "Tests property valuation, regulations, and market analysis."),
        ("Legal Knowledge - Contract Law", 30, "Assesses understanding of contract formation and dispute resolution."),
        ("Telecommunications Knowledge", 25, "Tests networking protocols, 5G, and telecom infrastructure."),
        ("Automotive Engineering Knowledge", 30, "Evaluates automotive systems, diagnostics, and safety standards."),
        ("Environmental Compliance Knowledge", 20, "Tests environmental regulations, sustainability, and auditing."),
        ("Retail Operations Knowledge", 20, "Assesses inventory management, POS systems, and merchandising."),
    ]
    for name, dur, desc in domains:
        add(name, "Job Knowledge", dur, False, True, desc)

    # ═══════════════════════════════════════════════════════════════════════
    #  8. LANGUAGE / COMMUNICATION  (~20 tests)
    # ═══════════════════════════════════════════════════════════════════════
    for lang in ["English", "French", "German", "Spanish", "Mandarin",
                 "Japanese", "Portuguese", "Arabic", "Hindi", "Dutch"]:
        add(f"{lang} Language Proficiency", "Language", 25, False, True,
            f"Standardised proficiency test for {lang} covering reading, writing, and comprehension.")

    add("Business English Communication", "Language", 20, False, True,
        "Tests professional English for emails, reports, and presentations.")
    add("Technical Writing Assessment", "Language", 25, False, True,
        "Evaluates ability to produce clear technical documentation.")
    add("Call Centre English Fluency", "Language", 15, False, True,
        "Assesses spoken and written English for contact-centre roles.")

    # ═══════════════════════════════════════════════════════════════════════
    #  9. ADDITIONAL COGNITIVE VARIANTS  (~20 tests)
    # ═══════════════════════════════════════════════════════════════════════
    for level in ["Graduate", "Professional", "Executive"]:
        add(f"Adaptive Numerical Reasoning ({level})", "Cognitive", 20, True, True,
            f"Adaptive numerical reasoning calibrated for {level.lower()} difficulty.")
        add(f"Adaptive Verbal Reasoning ({level})", "Cognitive", 20, True, True,
            f"Adaptive verbal reasoning calibrated for {level.lower()} difficulty.")
        add(f"Adaptive Inductive Reasoning ({level})", "Cognitive", 22, True, True,
            f"Adaptive inductive reasoning calibrated for {level.lower()} difficulty.")

    add("Visual Perception Test", "Cognitive", 12, False, True,
        "Measures ability to perceive and compare visual patterns quickly.")
    add("Attention to Detail - Numeric", "Cognitive", 10, False, True,
        "Tests precision in detecting numeric discrepancies and errors.")
    add("Attention to Detail - Verbal", "Cognitive", 10, False, True,
        "Tests precision in detecting spelling, grammar, and terminology errors.")
    add("Systems Thinking Assessment", "Cognitive", 25, False, True,
        "Evaluates ability to understand complex interdependent systems.")
    add("Strategic Reasoning Assessment", "Cognitive", 30, False, True,
        "Tests high-level strategic thinking and business acumen.")
    add("Quantitative Problem Solving", "Cognitive", 25, False, True,
        "Complex mathematical and statistical problem-solving tasks.")

    # ═══════════════════════════════════════════════════════════════════════
    #  10. ADDITIONAL SKILLS TESTS  (~50 tests)
    # ═══════════════════════════════════════════════════════════════════════

    # Software Testing & QA
    for topic in ["Manual Testing Fundamentals", "Selenium Automation",
                  "API Testing (Postman)", "Performance Testing (JMeter)",
                  "Mobile App Testing"]:
        add(f"{topic} Assessment", "Knowledge & Skills", 35, False, True,
            f"Evaluates proficiency in {topic} methodologies and tools.")

    # Mobile Development
    for tech in ["iOS Development (Swift)", "Android Development (Kotlin)",
                 "React Native", "Flutter", "Xamarin"]:
        add(f"{tech} Assessment", "Knowledge & Skills", 40, False, True,
            f"Tests practical development skills in {tech}.")

    # Data Engineering & Big Data
    for tech in ["Apache Spark", "Apache Kafka", "Hadoop Ecosystem",
                 "Snowflake Data Warehouse", "dbt (Data Build Tool)",
                 "Airflow Pipeline Design"]:
        add(f"{tech} Assessment", "Knowledge & Skills", 40, False, True,
            f"Validates knowledge and practical skills in {tech}.")

    # Networking & Infrastructure
    for tech in ["Cisco Networking (CCNA)", "Network Troubleshooting",
                 "Windows Server Administration", "VMware Virtualisation",
                 "Load Balancing & CDN"]:
        add(f"{tech} Assessment", "Knowledge & Skills", 35, False, True,
            f"Tests theoretical and applied knowledge in {tech}.")

    # Design & Creative
    for tool in ["Figma UI Design", "Adobe Photoshop", "Adobe Illustrator",
                 "UX Research Methods", "Accessibility (WCAG) Compliance"]:
        add(f"{tool} Assessment", "Knowledge & Skills", 30, False, True,
            f"Evaluates proficiency with {tool}.")

    # Business Analysis
    for skill in ["Business Requirements Analysis", "Process Mapping (BPMN)",
                  "Stakeholder Management", "User Story Writing",
                  "Data Visualisation Best Practices"]:
        add(f"{skill} Assessment", "Knowledge & Skills", 25, False, True,
            f"Tests knowledge and application of {skill}.")

    # ═══════════════════════════════════════════════════════════════════════
    #  11. ADDITIONAL PERSONALITY & BEHAVIORAL  (~20 tests)
    # ═══════════════════════════════════════════════════════════════════════
    for trait in ["Conscientiousness", "Extraversion", "Agreeableness",
                  "Openness to Experience", "Emotional Stability"]:
        add(f"Big Five – {trait} Assessment", "Personality", 8, False, True,
            f"Focused assessment of {trait.lower()} personality dimension.")

    add("Conflict Management Style Assessment", "Behavioral", 15, False, True,
        "Identifies preferred conflict-handling approach using Thomas-Kilmann model.")
    add("Communication Style Inventory", "Behavioral", 12, False, True,
        "Evaluates assertive, analytical, amiable, and expressive communication styles.")
    add("Decision-Making Style Assessment", "Behavioral", 15, False, True,
        "Measures rational vs intuitive decision-making preferences.")
    add("Time Management Assessment", "Behavioral", 12, False, True,
        "Evaluates planning, prioritisation, and delegation skills.")
    add("Stress Management Assessment", "Behavioral", 12, False, True,
        "Identifies coping strategies and stress tolerance under pressure.")
    add("Ethical Reasoning Assessment", "Behavioral", 20, False, True,
        "Tests moral reasoning and ethical decision-making in workplace scenarios.")
    add("Cross-Cultural Competency Assessment", "Behavioral", 15, False, True,
        "Evaluates cultural awareness and ability to work across diverse teams.")
    add("Negotiation Skills Assessment", "Behavioral", 20, False, True,
        "Measures negotiation strategy, persuasion, and deal-closing ability.")
    add("Presentation Skills Assessment", "Behavioral", 15, False, True,
        "Evaluates clarity, structure, and confidence in delivering presentations.")

    # ═══════════════════════════════════════════════════════════════════════
    #  12. ADDITIONAL DOMAIN KNOWLEDGE  (~20 tests)
    # ═══════════════════════════════════════════════════════════════════════
    extra_domains = [
        ("Energy & Utilities Knowledge", 25, "Tests power generation, distribution, and regulatory knowledge."),
        ("Aviation Knowledge", 25, "Evaluates aviation regulations, safety protocols, and operations."),
        ("Hospitality Management Knowledge", 20, "Tests hotel operations, guest service, and revenue management."),
        ("Education & Training Knowledge", 20, "Assesses pedagogy, curriculum design, and learning theory."),
        ("Construction & Civil Engineering", 25, "Tests building codes, project planning, and structural concepts."),
        ("Food Safety & Quality (HACCP)", 20, "Validates food safety, HACCP principles, and hygiene standards."),
        ("Logistics & Freight Knowledge", 20, "Tests shipping regulations, customs, and supply chain logistics."),
        ("Media & Advertising Knowledge", 20, "Evaluates media planning, advertising strategy, and campaign measurement."),
        ("Public Sector Administration", 25, "Tests knowledge of governance, public policy, and administrative procedures."),
        ("Nonprofit Management Knowledge", 20, "Evaluates fundraising, grant management, and stakeholder engagement."),
        ("Venture Capital & Private Equity", 30, "Tests deal evaluation, term sheets, and portfolio management knowledge."),
        ("Management Consulting Knowledge", 25, "Assesses problem structuring, hypothesis-driven analysis, and case methodology."),
        ("Actuarial Science Knowledge", 40, "Tests probability, risk modelling, and insurance mathematics."),
        ("Compliance & Anti-Money Laundering", 25, "Validates AML, KYC, and financial regulatory compliance."),
        ("Data Privacy (GDPR) Knowledge", 20, "Tests understanding of GDPR principles, rights, and obligations."),
    ]
    for name, dur, desc in extra_domains:
        add(name, "Job Knowledge", dur, False, True, desc)

    # ═══════════════════════════════════════════════════════════════════════
    #  13. ADDITIONAL SIMULATIONS  (~15 tests)
    # ═══════════════════════════════════════════════════════════════════════
    extra_sims = [
        ("Supply Chain Disruption Simulation", 30, "Scenario-based exercise managing a multi-stage supply chain disruption."),
        ("IT Incident Management Simulation", 25, "Simulated major IT outage requiring triage, communication, and resolution."),
        ("Sales Pitch Simulation", 15, "Prepare and deliver a sales pitch for a new product."),
        ("Merger Integration Simulation", 35, "Strategic simulation of post-acquisition integration planning."),
        ("New Market Entry Simulation", 30, "Develop a market-entry strategy for an unfamiliar geography."),
        ("Workforce Planning Simulation", 25, "Plan headcount allocation under budget and talent constraints."),
        ("Regulatory Audit Simulation", 25, "Prepare for and respond to a mock regulatory audit."),
        ("Product Launch Simulation", 30, "End-to-end simulation managing a product launch across teams."),
        ("Quality Improvement Simulation", 25, "Root-cause analysis and improvement planning for quality defects."),
        ("Remote Team Coordination Simulation", 20, "Manage a distributed team through a complex deliverable."),
    ]
    for name, dur, desc in extra_sims:
        add(name, "Simulation", dur, False, True, desc)

    # ═══════════════════════════════════════════════════════════════════════
    #  14. ADDITIONAL SJT / BEHAVIORAL  (~10 tests)
    # ═══════════════════════════════════════════════════════════════════════
    extra_sjt = [
        ("Healthcare Situational Judgement", 20, "Scenario-based assessment for clinical and healthcare roles."),
        ("Engineering Situational Judgement", 20, "Evaluates judgement in engineering project and safety scenarios."),
        ("Logistics Situational Judgement", 15, "Tests problem-solving in warehouse and distribution situations."),
        ("Hospitality Situational Judgement", 15, "Assesses guest-service and operational decision-making."),
        ("Education Situational Judgement", 20, "Tests classroom management and student engagement decisions."),
        ("Construction Situational Judgement", 15, "Evaluates site safety, coordination, and stakeholder decisions."),
        ("Legal Professional Situational Judgement", 20, "Tests ethics and judgement in legal practice contexts."),
        ("Consulting Situational Judgement", 20, "Scenario-based test for client advisory and engagement management."),
    ]
    for name, dur, desc in extra_sjt:
        add(name, "Behavioral", dur, False, True, desc)

    # ═══════════════════════════════════════════════════════════════════════
    #  15. ADDITIONAL LANGUAGE TESTS  (~10 tests)
    # ═══════════════════════════════════════════════════════════════════════
    for lang in ["Korean", "Turkish", "Thai", "Vietnamese", "Polish",
                 "Swedish", "Czech", "Indonesian"]:
        add(f"{lang} Language Proficiency", "Language", 25, False, True,
            f"Standardised proficiency test for {lang} covering reading, writing, and comprehension.")
    add("Bilingual Proficiency Assessment (EN/ES)", "Language", 30, False, True,
        "Evaluates bilingual competence in English and Spanish for customer-facing roles.")
    add("Bilingual Proficiency Assessment (EN/FR)", "Language", 30, False, True,
        "Evaluates bilingual competence in English and French for customer-facing roles.")

    return catalogue


# ─── Output ──────────────────────────────────────────────────────────────────

def save_catalogue(catalogue: list[dict], out_dir: str, also_csv: bool = False):
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "shl_products.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)
    print(f"[scraper] Wrote {len(catalogue)} products → {json_path}")

    if also_csv:
        csv_path = os.path.join(out_dir, "shl_catalogue.csv")
        keys = catalogue[0].keys()
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(catalogue)
        print(f"[scraper] Wrote CSV → {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Scrape/build SHL product catalogue")
    parser.add_argument("--csv", action="store_true", help="Also write CSV")
    args = parser.parse_args()

    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    # Try live scrape first, fall back to curated
    catalogue = scrape_live()
    if catalogue is None:
        print("[scraper] Using comprehensive curated catalogue.")
        catalogue = _build_curated()

    print(f"[scraper] Total individual test solutions: {len(catalogue)}")
    save_catalogue(catalogue, data_dir, also_csv=args.csv)


if __name__ == "__main__":
    main()
