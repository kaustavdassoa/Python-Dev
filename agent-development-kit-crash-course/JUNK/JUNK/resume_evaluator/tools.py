"""Tool functions for the Resume Evaluator agent."""


def retrieve_master_experience() -> dict:
    """Retrieves the candidate's full master experience.

    Returns a structured dict of professional history, skills, and
    accomplishments. Replace this sample data with a real data source
    (database, API, file) in production.
    """

    return {
        "status": "success",
        "master_experience": {
            "candidate_name": "Alex Morgan",
            "title": "Senior Software Engineer",
            "years_of_experience": 8,
            "summary": (
                "Full-stack engineer with 8 years building scalable distributed "
                "systems, leading cross-functional teams, and driving revenue-impacting "
                "product launches at high-growth startups and Fortune 500 companies."
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
                "AWS Solutions Architect - Associate",
                "Google Cloud Professional Data Engineer",
            ],
            "experience": [
                {
                    "company": "TechNova Inc.",
                    "role": "Senior Software Engineer",
                    "duration": "Jan 2022 - Present",
                    "accomplishments": [
                        "Led migration of a monolithic order-processing system to event-driven microservices on AWS, reducing average order latency from 1.2s to 180ms (85% reduction) and improving throughput by 4x.",
                        "Designed and deployed a real-time fraud detection pipeline using Apache Kafka and Python, processing 50K transactions/min with 98.5% precision, preventing ~$2.1M in annual fraud losses.",
                        "Mentored 5 junior engineers through weekly code reviews and architecture sessions, resulting in 40% reduction in production incidents over 6 months.",
                        "Built a self-service internal developer portal (React + Node.js), cutting new-service onboarding time from 2 weeks to 3 hours for 120+ engineers.",
                        "Spearheaded Infrastructure-as-Code adoption with Terraform, reducing cloud provisioning time by 70% and eliminating configuration drift across 3 environments.",
                    ],
                },
                {
                    "company": "DataStream Analytics",
                    "role": "Software Engineer II",
                    "duration": "Mar 2019 - Dec 2021",
                    "accomplishments": [
                        "Architected a customer analytics data lake on GCP BigQuery, ingesting 2TB daily event data, enabling 10x faster ad-hoc queries vs legacy Redshift warehouse.",
                        "Developed a recommendation engine prototype (Python/scikit-learn, collaborative filtering) that increased user engagement by 18% in A/B tests across 500K users.",
                        "Optimized PostgreSQL query performance for core billing service, reducing p99 latency from 800ms to 120ms via materialized views and index tuning.",
                        "Implemented CI/CD pipeline with GitHub Actions + Docker enabling multiple daily zero-downtime deployments (from bi-weekly releases).",
                    ],
                },
                {
                    "company": "CloudFirst Solutions",
                    "role": "Junior Software Engineer",
                    "duration": "Jun 2017 - Feb 2019",
                    "accomplishments": [
                        "Built RESTful APIs in Java/Spring Boot for a B2B SaaS platform serving 200+ enterprise clients, handling 10K+ API calls/min.",
                        "Automated regression testing with Selenium + JUnit, increasing test coverage from 45% to 85% and reducing QA cycle time by 60%.",
                        "Contributed to on-premise to AWS migration, reducing infrastructure costs by 35% while improving uptime to 99.95%.",
                    ],
                },
            ],
            "education": {
                "degree": "B.S. in Computer Science",
                "university": "University of California, Berkeley",
                "graduation_year": 2017,
            },
        },
    }
