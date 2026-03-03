"""Tool functions for the Resume Evaluator (JSON) agent."""

import os


def extract_resume_from_pdf(file_path: str) -> dict:
    """Extracts text content from a PDF resume file.

    The orchestrator agent provides the absolute file path to the PDF resume.
    This tool reads the PDF page by page and returns the concatenated text.

    Args:
        file_path: Absolute path to the PDF resume file.

    Returns:
        A dict with 'status' and either 'resume_text' on success
        or 'message' on error.
    """
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return {
            "status": "error",
            "message": (
                "PyPDF2 is not installed. "
                "Run: pip install PyPDF2"
            ),
        }

    if not file_path:
        return {"status": "error", "message": "file_path is empty."}

    if not os.path.isfile(file_path):
        return {
            "status": "error",
            "message": f"File not found: {file_path}",
        }

    try:
        reader = PdfReader(file_path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text.strip())

        full_text = "\n\n".join(pages_text)

        if not full_text.strip():
            return {
                "status": "error",
                "message": "PDF appears to contain no extractable text (may be scanned/image-based).",
            }

        return {"status": "success", "resume_text": full_text}

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to read PDF: {e}",
        }


def retrieve_master_experience() -> dict:
    """Retrieves the candidate's full master experience.

    Returns a structured dict of professional history, skills, and
    accomplishments that covers all major JD evaluation scenarios:
      - 10+ years experience & leadership/mentoring
      - Full-stack: Java, Spring, Hibernate, ReactJS
      - Cloud-native: AWS, Azure, GCP, Kubernetes, OpenShift
      - AI/GenAI: LLMs, LangGraph, Agentic AI, Copilot
      - BigData/NoSQL: MongoDB, Kafka, Spark, Elasticsearch
      - DevSecOps, CI/CD, QA automation, Secure SDLC
      - Stakeholder engagement & agile delivery

    Replace this sample data with a real data source
    (database, API, file) in production.
    """

    return {
        "status": "success",
        "master_experience": {
            "candidate_name": "Kaustav Das",
            "title": "Lead Software Engineer, COO-Tech",
            "years_of_experience": 18,
            "summary": (
                "Seasoned Lead Software Engineer with 18+ years of experience "
                "driving large-scale modernization programs across regulatory and "
                "compliance domains. Combines hands-on full-stack development "
                "(Java, Spring Boot, Hibernate, ReactJS) with cloud-native "
                "engineering, AI/GenAI technologies, and executive stakeholder "
                "engagement. Proven track record in building resilient platforms, "
                "leading cross-functional teams, and establishing secure SDLC "
                "practices in highly regulated environments."
            ),
            "technical_skills": [
                # Languages & Frameworks
                "Java", "Python", "Spring Boot", "Hibernate", "ReactJS",
                # Messaging & Streaming
                "Apache Kafka",
                # Cloud & Container Platforms
                "Tanzu", "OpenShift", "AWS", "Azure", "Google Cloud",
                "Docker", "Kubernetes",
                # CI/CD & DevOps
                "Jenkins", "IBM Urban Deploy", "Harness",
                "GitHub Actions", "GitHub Copilot",
                # Databases & Data
                "Oracle", "MySQL", "PostgreSQL",
                "MongoDB", "Redis", "Elasticsearch",
                "Apache Spark", "BigQuery",
                # AI & GenAI
                "LLMs", "LangGraph", "Agentic AI", "Prompt Engineering",
                # APIs & Integration
                "REST APIs", "GraphQL", "gRPC", "SOA", "BPM",
            ],
            "soft_skills": [
                "Regulatory Compliance",
                "Audit Remediation",
                "Incident Response",
                "Application Modernization",
                "Cloud Migration",
                "Microservices & APIs",
                "DevSecOps / Secure SDLC",
                "NFR Governance",
                "Vendor Engagement",
                "Budget Planning & Allocation",
                "Executive Stakeholder Engagement",
                "Agile Delivery & Roadmapping",
                "Architecture Review & Standards",
                "Manager + Engineer Leadership",
            ],
            "certifications": [
                "Certified Kubernetes Application Developer (in progress)",
                "Advanced Java & Spring Boot (Security, Multi-threading, "
                "Distributed Systems) – Ongoing deep dive",
                "AI/GenAI: Exploring LangGraph, Agentic AI, and Prompt "
                "Engineering for enterprise workflow automation",
            ],
            "experience": [
                {
                    "company": "Wells Fargo",
                    "role": "Lead Software Engineer, SMIS 2.0",
                    "duration": "2020 - Present",
                    "accomplishments": [
                        "Directed regulatory-driven modernization of SCRA/SMIS, "
                        "delivering audit finding remediation and application "
                        "changes within tight deadlines, preventing repeat "
                        "compliance gaps.",
                        "Led a cross-functional team peaking at 22 engineers "
                        "across locations; blended architecture review, secure "
                        "SDLC governance, and hands-on coding to accelerate "
                        "compliant delivery.",
                        "Partnered with compliance/audit to remediate production "
                        "incidents with potential compliance/SLA impact, avoiding "
                        "escalation and stabilizing KPIs.",
                        "Worked with SCRA leadership to plan and create the SMIS "
                        "modernization roadmap for a $250K budget, aligning spend "
                        "with compliance mandates and technical debt reduction.",
                        "Presented modernization updates and compliance closure "
                        "status to SCRA CoE Leadership, influencing "
                        "prioritization and release plans.",
                        "Drove platform migration PCF → OCP, leading NFR "
                        "initiatives (scalability, performance, HA, DR); "
                        "instituted reliability patterns and capacity planning.",
                        "Standardized design/coding practices and architecture "
                        "reviews to enforce secure SDLC, data protection, and "
                        "operational readiness; improved deployment lead time "
                        "and enforced strong hard gates for production releases.",
                        "AI/GenAI Hackathon 2025: Developed Email Triage System "
                        "using LLMs and Python — automatically classifying "
                        "mailbox requests and routing to correct serving groups.",
                        "Built full-stack dashboards with ReactJS frontend and "
                        "Spring Boot backend for real-time compliance monitoring.",
                        "Leveraged GitHub Copilot and similar AI development "
                        "tools to accelerate code generation and code reviews.",
                    ],
                },
                {
                    "company": "Wells Fargo",
                    "role": "Application Architect / SDE4, SMIS 1.0",
                    "duration": "2015 - 2020",
                    "accomplishments": [
                        "Championed an API-first strategy by developing headless "
                        "BPM workflows, accelerating integrations and reducing "
                        "time-to-market for SMIS compliance processes by 30%.",
                        "Partnered with SMIS Product teams to design BPM "
                        "workflows, achieving zero compliance breaches.",
                        "Led workflow automation and process re-engineering that "
                        "reduced manual touchpoints and improved operational "
                        "efficiency by 30%.",
                        "Engaged with Oracle vendor teams to implement platform "
                        "features and resolve DB compliance vulnerabilities.",
                        "Established robust QA and automated testing frameworks, "
                        "ensuring zero defect releases.",
                        "Implemented BigData analytics pipeline using Apache "
                        "Spark and Elasticsearch for compliance reporting, "
                        "processing 500K+ records daily.",
                    ],
                },
                {
                    "company": "Oracle",
                    "role": "Sr. Pre-Sales Consultant",
                    "duration": "2012 - 2015",
                    "accomplishments": [
                        "Advised enterprise clients on cloud-native and "
                        "Java-based architectures, shaping modernization "
                        "roadmaps and migration strategies.",
                        "Conducted technical deep dives and enablement sessions "
                        "to accelerate adoption of modern frameworks.",
                        "Influenced C-suite stakeholders by translating business "
                        "needs into scalable, secure reference architectures; "
                        "supported deals totaling $2.5M across multiple accounts.",
                    ],
                },
                {
                    "company": "Accenture",
                    "role": "Team Lead",
                    "duration": "2006 - 2012",
                    "accomplishments": [
                        "Established an Oracle Center of Excellence (CoE), "
                        "standardizing Fusion development practices across "
                        "global delivery teams.",
                        "Led design and development of the Accenture Foundation "
                        "Platform for Oracle (AFPO) to accelerate ERP/SOA/BPM "
                        "implementations; reduced timelines by 25%.",
                        "Spearheaded SOA/BPM integration solutions to improve "
                        "scalability and interoperability across platforms.",
                        "Drove reusable frameworks and documentation that reduced "
                        "risk and improved onboarding for multi-project "
                        "portfolios.",
                    ],
                },
            ],
            "education": {
                "degree": "BE Electronic",
                "university": "Nagpur University",
                "graduation_year": 2004,
            },
        },
    }
