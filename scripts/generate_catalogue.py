"""
One-off script to generate a realistic 1000-entry SHL assessment catalogue.
Run once, then delete.  Output: data/shl_catalogue.csv
"""
import csv, random, os

random.seed(42)

# ─── Pools ────────────────────────────────────────────────────────────────────
CATEGORIES = {
    "Technical": [
        ("Python Programming", ["python", "programming", "data structures", "algorithms"]),
        ("Java Development", ["java", "oop", "programming", "spring"]),
        ("JavaScript Proficiency", ["javascript", "es6", "dom", "async"]),
        ("TypeScript Assessment", ["typescript", "type systems", "javascript"]),
        ("C++ Fundamentals", ["c++", "memory management", "oop", "stl"]),
        ("Go Programming", ["go", "concurrency", "backend", "microservices"]),
        ("Ruby on Rails", ["ruby", "rails", "mvc", "web development"]),
        ("PHP Development", ["php", "laravel", "web development", "mysql"]),
        ("Rust Systems Programming", ["rust", "memory safety", "systems programming"]),
        ("Swift iOS Development", ["swift", "ios", "xcode", "mobile development"]),
        ("Kotlin Android Development", ["kotlin", "android", "jetpack", "mobile"]),
        ("React Frontend", ["react", "javascript", "state management", "hooks"]),
        ("Angular Assessment", ["angular", "typescript", "rxjs", "spa"]),
        ("Vue.js Proficiency", ["vue", "javascript", "vuex", "composition api"]),
        ("Node.js Backend", ["node.js", "express", "api design", "javascript"]),
        ("Django Web Development", ["django", "python", "orm", "rest api"]),
        ("Flask API Development", ["flask", "python", "rest api", "microservices"]),
        ("SQL Mastery", ["sql", "databases", "queries", "optimization"]),
        ("NoSQL Database", ["mongodb", "nosql", "cassandra", "document stores"]),
        ("PostgreSQL Advanced", ["postgresql", "sql", "indexing", "stored procedures"]),
        ("Redis & Caching", ["redis", "caching", "key-value stores", "performance"]),
        ("GraphQL API", ["graphql", "api design", "schema", "resolvers"]),
        ("REST API Design", ["rest", "api", "http", "microservices"]),
        ("Docker Containerization", ["docker", "containers", "devops", "deployment"]),
        ("Kubernetes Orchestration", ["kubernetes", "container orchestration", "devops"]),
        ("AWS Cloud Services", ["aws", "cloud", "ec2", "s3", "lambda"]),
        ("Azure Cloud Platform", ["azure", "cloud", "devops", "arm templates"]),
        ("GCP Fundamentals", ["gcp", "cloud", "bigquery", "compute engine"]),
        ("Terraform IaC", ["terraform", "infrastructure as code", "cloud", "devops"]),
        ("CI/CD Pipeline", ["ci/cd", "jenkins", "github actions", "automation"]),
        ("Git Version Control", ["git", "version control", "branching", "github"]),
        ("Linux Administration", ["linux", "bash", "system administration", "networking"]),
        ("Shell Scripting", ["bash", "shell", "automation", "linux"]),
        ("Data Engineering", ["etl", "data pipelines", "spark", "airflow"]),
        ("Apache Spark", ["spark", "big data", "scala", "distributed computing"]),
        ("Hadoop Ecosystem", ["hadoop", "mapreduce", "hive", "big data"]),
        ("Machine Learning", ["machine learning", "python", "scikit-learn", "algorithms"]),
        ("Deep Learning", ["deep learning", "tensorflow", "pytorch", "neural networks"]),
        ("Natural Language Processing", ["nlp", "text processing", "transformers", "python"]),
        ("Computer Vision", ["computer vision", "opencv", "image processing", "cnn"]),
        ("Data Visualization", ["tableau", "powerbi", "matplotlib", "visualization"]),
        ("Power BI Reporting", ["powerbi", "dax", "data modeling", "reporting"]),
        ("Tableau Analytics", ["tableau", "data visualization", "dashboards", "analytics"]),
        ("Excel Advanced", ["excel", "pivot tables", "vlookup", "macros"]),
        ("R Programming", ["r", "statistics", "ggplot2", "data analysis"]),
        ("MATLAB Computation", ["matlab", "numerical computing", "simulation"]),
        ("SAS Analytics", ["sas", "statistical analysis", "data management"]),
        ("Blockchain Fundamentals", ["blockchain", "smart contracts", "ethereum"]),
        ("IoT Development", ["iot", "embedded systems", "sensors", "mqtt"]),
        ("Embedded Systems", ["embedded c", "microcontrollers", "rtos", "firmware"]),
        ("API Testing", ["api testing", "postman", "rest", "automation"]),
        ("Selenium Automation", ["selenium", "test automation", "web testing", "python"]),
        ("Performance Testing", ["jmeter", "load testing", "performance", "scalability"]),
        ("Unit Testing", ["unit testing", "jest", "pytest", "tdd"]),
        ("Mobile Testing", ["mobile testing", "appium", "ios", "android"]),
        ("Security Testing", ["penetration testing", "owasp", "vulnerability", "security"]),
        ("Network Security", ["firewalls", "ids", "network security", "vpn"]),
        ("Cybersecurity Foundations", ["cybersecurity", "threat analysis", "incident response"]),
        ("Ethical Hacking", ["ethical hacking", "kali linux", "penetration testing"]),
        ("Cryptography Basics", ["cryptography", "encryption", "hashing", "ssl"]),
        ("Web Scraping", ["web scraping", "beautifulsoup", "scrapy", "python"]),
        ("Regex Mastery", ["regex", "pattern matching", "text processing"]),
        ("Microservices Architecture", ["microservices", "design patterns", "api gateway"]),
        ("System Design", ["system design", "scalability", "distributed systems"]),
        ("Software Architecture", ["architecture", "design patterns", "solid principles"]),
        ("Agile Scrum", ["agile", "scrum", "sprint planning", "user stories"]),
        ("DevOps Practices", ["devops", "automation", "monitoring", "deployment"]),
        ("Site Reliability", ["sre", "monitoring", "incident management", "reliability"]),
    ],
    "Cognitive": [
        ("Logical Reasoning", ["logical reasoning", "problem solving", "patterns"]),
        ("Numerical Reasoning", ["numerical reasoning", "mathematics", "quantitative"]),
        ("Verbal Reasoning", ["verbal reasoning", "reading comprehension", "vocabulary"]),
        ("Abstract Reasoning", ["abstract thinking", "pattern recognition", "non-verbal"]),
        ("Critical Thinking", ["critical thinking", "analysis", "evaluation"]),
        ("Spatial Reasoning", ["spatial awareness", "3d visualization", "geometry"]),
        ("Inductive Reasoning", ["inductive reasoning", "pattern completion", "logic"]),
        ("Deductive Logic", ["deductive reasoning", "syllogisms", "formal logic"]),
        ("Cognitive Flexibility", ["adaptability", "mental agility", "problem switching"]),
        ("Working Memory", ["memory", "attention", "information processing"]),
        ("Processing Speed", ["speed", "accuracy", "information processing"]),
        ("Analytical Thinking", ["analysis", "data interpretation", "reasoning"]),
        ("Mathematical Reasoning", ["mathematics", "algebra", "word problems"]),
        ("Diagrammatic Reasoning", ["diagrams", "flowcharts", "visual logic"]),
        ("Mechanical Reasoning", ["mechanical", "physics", "spatial", "forces"]),
    ],
    "Behavioral": [
        ("Communication Skills", ["communication", "writing", "grammar", "articulation"]),
        ("Leadership Assessment", ["leadership", "decision making", "management", "vision"]),
        ("Teamwork Evaluation", ["teamwork", "collaboration", "interpersonal"]),
        ("Conflict Resolution", ["conflict resolution", "mediation", "negotiation"]),
        ("Emotional Intelligence", ["empathy", "self-awareness", "emotional regulation"]),
        ("Stress Management", ["stress tolerance", "resilience", "coping strategies"]),
        ("Time Management", ["planning", "organization", "prioritization"]),
        ("Adaptability Assessment", ["adaptability", "flexibility", "change management"]),
        ("Customer Service Orientation", ["customer service", "empathy", "communication"]),
        ("Presentation Skills", ["presentation", "public speaking", "visual communication"]),
        ("Negotiation Skills", ["negotiation", "persuasion", "influence"]),
        ("Ethics & Integrity", ["ethics", "integrity", "professional conduct"]),
        ("Cultural Sensitivity", ["cultural awareness", "diversity", "inclusion"]),
        ("Work Ethic Assessment", ["reliability", "accountability", "dedication"]),
        ("Creativity & Innovation", ["creativity", "innovation", "brainstorming"]),
    ],
    "Domain": [
        ("Financial Analysis", ["finance", "accounting", "financial modeling", "valuation"]),
        ("Marketing Strategy", ["marketing", "digital marketing", "seo", "branding"]),
        ("Sales Aptitude", ["sales", "negotiation", "crm", "pipeline"]),
        ("HR Management", ["recruitment", "hr policies", "employee relations"]),
        ("Supply Chain Management", ["supply chain", "logistics", "inventory", "procurement"]),
        ("Project Management", ["project planning", "risk management", "pmp"]),
        ("Business Strategy", ["strategy", "competitive analysis", "market research"]),
        ("Operations Management", ["operations", "process improvement", "lean"]),
        ("Risk Management", ["risk assessment", "compliance", "mitigation"]),
        ("Legal Compliance", ["legal", "regulations", "compliance", "governance"]),
        ("Healthcare Knowledge", ["healthcare", "medical terminology", "patient care"]),
        ("Pharmaceutical Assessment", ["pharmacology", "drug safety", "clinical trials"]),
        ("Real Estate Fundamentals", ["real estate", "property management", "valuation"]),
        ("Insurance Knowledge", ["insurance", "underwriting", "claims", "actuarial"]),
        ("Banking Fundamentals", ["banking", "credit analysis", "risk", "regulatory"]),
        ("Investment Analysis", ["investment", "portfolio management", "equity", "bonds"]),
        ("Digital Transformation", ["digital strategy", "automation", "innovation"]),
        ("E-commerce Operations", ["e-commerce", "online retail", "fulfillment"]),
        ("Content Writing", ["content writing", "copywriting", "seo writing"]),
        ("UX/UI Design", ["ux design", "ui design", "figma", "user research"]),
        ("Graphic Design", ["graphic design", "adobe", "photoshop", "illustrator"]),
        ("Video Production", ["video editing", "premiere pro", "storytelling"]),
        ("Data Privacy (GDPR)", ["gdpr", "data privacy", "compliance", "regulation"]),
        ("Quality Assurance", ["quality management", "iso", "six sigma", "auditing"]),
        ("Environmental Compliance", ["environmental", "sustainability", "esg", "compliance"]),
    ],
}

ROLES_POOL = {
    "Technical": [
        "software engineer", "data analyst", "data scientist", "backend developer",
        "frontend developer", "full stack developer", "devops engineer", "cloud engineer",
        "ml engineer", "qa engineer", "site reliability engineer", "database administrator",
        "security analyst", "network engineer", "systems administrator", "mobile developer",
        "data engineer", "platform engineer", "solutions architect", "technical lead",
    ],
    "Cognitive": [
        "general", "graduate", "intern", "analyst", "consultant",
        "associate", "trainee", "researcher", "manager", "executive",
    ],
    "Behavioral": [
        "general", "manager", "team lead", "hr", "customer support",
        "sales", "executive", "consultant", "supervisor", "coordinator",
    ],
    "Domain": [
        "business analyst", "finance", "marketing", "sales", "hr",
        "project manager", "product manager", "operations manager",
        "consultant", "compliance officer", "investment analyst",
        "ux designer", "content strategist", "supply chain manager",
    ],
}

LEVELS = ["easy", "medium", "hard"]
LEVEL_WEIGHTS = [0.3, 0.45, 0.25]

DURATION_BY_LEVEL = {
    "easy":   (10, 25),
    "medium": (25, 50),
    "hard":   (40, 90),
}

DESC_TEMPLATES = [
    "Evaluate {topic} proficiency and practical problem-solving ability.",
    "Assess knowledge and hands-on skills in {topic}.",
    "Measure competency in {topic} through scenario-based questions.",
    "Test understanding of core {topic} concepts and their application.",
    "Gauge practical expertise and theoretical depth in {topic}.",
    "Comprehensive assessment of {topic} skills for role readiness.",
    "Determine aptitude and skill level in {topic} domain.",
    "Benchmark candidate abilities in {topic} against industry standards.",
]

# ─── Generate ─────────────────────────────────────────────────────────────────
rows = []
uid = 1

for category, templates in CATEGORIES.items():
    for base_name, base_skills in templates:
        # Generate multiple variants per template
        n_variants = random.choice([7, 8, 9, 10]) if category != "Cognitive" else random.choice([10, 11, 12, 13])
        for v in range(n_variants):
            level = random.choices(LEVELS, LEVEL_WEIGHTS)[0]
            lo, hi = DURATION_BY_LEVEL[level]
            duration = random.randint(lo // 5, hi // 5) * 5

            # Pick 2-4 skills from base, possibly add a variant
            n_skills = min(len(base_skills), random.randint(2, 4))
            skills = random.sample(base_skills, n_skills)

            # Pick 1-3 roles
            role_pool = ROLES_POOL.get(category, ["general"])
            n_roles = random.randint(1, min(3, len(role_pool)))
            roles = random.sample(role_pool, n_roles)

            # Suffix the name for variety
            suffixes = ["Test", "Assessment", "Evaluation", "Challenge", "Benchmark", "Exam"]
            if v == 0:
                name = f"{base_name} {random.choice(suffixes)}"
            else:
                level_label = {"easy": "Foundation", "medium": "Intermediate", "hard": "Advanced"}[level]
                name = f"{base_name} — {level_label} {random.choice(suffixes)}"

            topic = base_name.lower().replace("_", " ")
            desc = random.choice(DESC_TEMPLATES).format(topic=topic)
            remote = random.choices([True, False], weights=[0.8, 0.2])[0]

            rows.append({
                "id": uid,
                "assessment_name": name,
                "skills": ",".join(skills),
                "roles": ",".join(roles),
                "description": desc,
                "level": level,
                "duration_min": duration,
                "category": category,
                "remote_available": remote,
            })
            uid += 1

# Shuffle for realism
random.shuffle(rows)
# Re-assign IDs after shuffle
for i, r in enumerate(rows, 1):
    r["id"] = i

# ─── Write CSV ────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(__file__), "..", "data", "shl_catalogue.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "assessment_name", "skills", "roles", "description",
        "level", "duration_min", "category", "remote_available",
    ])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} assessments -> {os.path.abspath(out)}")
