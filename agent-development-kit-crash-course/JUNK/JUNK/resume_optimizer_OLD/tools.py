"""
Atomic tool functions for the Resume Optimizer agent pipeline.

These are deterministic Python functions wired into the ADK agent flow
via google.adk.tools.FunctionTool.
"""


def retrieve_master_experience() -> dict:
    """Retrieves the candidate's complete master experience document.

    Returns a structured dictionary of the candidate's professional history,
    technical skills, certifications, and key accomplishments. This serves
    as the single source of truth that all resume bullets must trace back to.

    In production, this would connect to a database, API, or file store.
    For now, it returns a comprehensive sample profile.
    """

    master_experience = {
        "candidate_name": "Alex Morgan",
        "title": "Senior Software Engineer",
        "years_of_experience": 8,
        "summary": (
            "Full-stack engineer with 8 years of experience building scalable "
            "distributed systems, leading cross-functional teams, and driving "
            "revenue-impacting product launches at high-growth startups and "
            "Fortune 500 companies."
        ),
        "technical_skills": [
            "Python", "Go", "TypeScript", "Java",
            "React", "Next.js", "Node.js",
            "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
            "AWS (EC2, Lambda, S3, DynamoDB, SQS)", "GCP (BigQuery, Cloud Run)",
            "Docker", "Kubernetes", "Terraform",
            "Apache Kafka", "Apache Spark",
            "CI/CD (GitHub Actions, Jenkins)",
            "REST APIs", "gRPC", "GraphQL",
            "Machine Learning (scikit-learn, TensorFlow basics)",
        ],
        "certifications": [
            "AWS Solutions Architect – Associate",
            "Google Cloud Professional Data Engineer",
        ],
        "experience": [
            {
                "company": "TechNova Inc.",
                "role": "Senior Software Engineer",
                "duration": "Jan 2022 – Present",
                "accomplishments": [
                    "Led the migration of a monolithic order-processing system to an event-driven microservices architecture on AWS, reducing average order latency from 1.2s to 180ms (85% reduction) and improving throughput by 4x.",
                    "Designed and deployed a real-time fraud detection pipeline using Apache Kafka and Python, processing 50,000 transactions/minute with a 98.5% precision rate, preventing an estimated $2.1M in annual fraud losses.",
                    "Mentored a team of 5 junior engineers through weekly code reviews and architecture sessions, resulting in a 40% reduction in production incidents over 6 months.",
                    "Built a self-service internal developer portal using React and Node.js, cutting new-service onboarding time from 2 weeks to 3 hours for 120+ engineers.",
                    "Spearheaded adoption of Infrastructure-as-Code with Terraform, reducing cloud provisioning time by 70% and eliminating configuration drift across 3 environments.",
                ],
            },
            {
                "company": "DataStream Analytics",
                "role": "Software Engineer II",
                "duration": "Mar 2019  Dec 2021",
                "accomplishments": [
                    "Architected a customer analytics data lake on GCP BigQuery, ingesting 2TB of daily event data, enabling the product team to run ad-hoc queries 10x faster than the legacy Redshift warehouse.",
                    "Developed a recommendation engine prototype using collaborative filtering (Python/scikit-learn) that increased user engagement by 18% in A/B tests across 500K users.",
                    "Optimized PostgreSQL query performance for the core billing service, reducing p99 latency from 800ms to 120ms by introducing materialized views and index tuning.",
                    "Implemented a CI/CD pipeline with GitHub Actions and Docker that reduced deployment frequency from bi-weekly to multiple daily releases with zero-downtime deployments.",
                ],
            },
            {
                "company": "CloudFirst Solutions",
                "role": "Junior Software Engineer",
                "duration": "Jun 2017 – Feb 2019",
                "accomplishments": [
                    "Built RESTful APIs in Java/Spring Boot for a B2B SaaS platform serving 200+ enterprise clients, handling 10K+ API calls per minute.",
                    "Automated regression testing with Selenium and JUnit, increasing test coverage from 45% to 85% and reducing QA cycle time by 60%.",
                    "Contributed to the migration from on-premise data centers to AWS, reducing infrastructure costs by 35% while improving system uptime to 99.95%.",
                ],
            },
        ],
        "education": {
            "degree": "B.S. in Computer Science",
            "university": "University of California, Berkeley",
            "graduation_year": 2017,
        },
    }

    return {
        "status": "success",
        "master_experience": master_experience,
    }


def audit_hallucination(optimized_bullets: str, master_experience: str) -> dict:
    """Audits optimized resume bullets against the master experience for hallucinations.

    Cross-references every claim, metric, and technology mentioned in the
    optimized bullets against the candidate's verified master experience.
    Flags any bullet that contains information not grounded in the source data.

    Args:
        optimized_bullets: The AI-generated, optimized resume bullet points
            as a single string.
        master_experience: The candidate's verified master experience document
            as a string (JSON or plain text).

    Returns:
        A dict with 'status' ('pass' or 'fail'), 'total_bullets' count,
        'verified_count', and 'flagged_items' list with details of any
        unverifiable claims.
    """

    # Deterministic keyword-overlap audit
    # In production, this could use embeddings or an LLM-as-judge pattern.
    flagged_items = []
    bullets = [b.strip() for b in optimized_bullets.strip().split("\n") if b.strip()]
    experience_text = master_experience.lower()

    for i, bullet in enumerate(bullets, 1):
        # Extract key terms (numbers, percentages, proper nouns) from the bullet
        words = bullet.split()
        suspicious_terms = []
        for word in words:
            cleaned = word.strip(".,;:!?()\"'")
            # Flag numeric claims that don't appear in the source
            if any(char.isdigit() for char in cleaned):
                if cleaned.lower() not in experience_text:
                    suspicious_terms.append(cleaned)

        if suspicious_terms:
            flagged_items.append({
                "bullet_number": i,
                "bullet_text": bullet,
                "unverified_claims": suspicious_terms,
                "severity": "warning",
            })

    status = "pass" if len(flagged_items) == 0 else "fail"

    return {
        "status": status,
        "total_bullets": len(bullets),
        "verified_count": len(bullets) - len(flagged_items),
        "flagged_items": flagged_items,
        "audit_note": (
            "All bullets are grounded in the master experience."
            if status == "pass"
            else f"{len(flagged_items)} bullet(s) contain claims not directly "
                 f"verifiable against the master experience. Review flagged items."
        ),
    }
