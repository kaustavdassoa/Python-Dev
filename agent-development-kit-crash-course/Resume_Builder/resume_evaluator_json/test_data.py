"""
Sample test data for the Resume Evaluator (JSON) agent.

Provides multiple candidate profiles to test different evaluation scenarios:
  - STRONG FIT  : Senior full-stack engineer, covers nearly all JD requirements
  - MODERATE FIT: Mid-level backend developer, partial coverage
  - WEAK FIT    : Junior frontend developer, significant gaps

Usage with adk web (without PDF):
  Paste one of the JD + candidate combos below into the chat.
  The agent will use retrieve_master_experience() as fallback.

Usage programmatically:
  from resume_evaluator_json.test_data import TEST_CANDIDATES, SAMPLE_JD
"""


SAMPLE_JD = """\
Required qualifications, capabilities and skills:
- Software engineering concepts and 10+ years applied experience.
  In addition, demonstrated coaching and mentoring experience.
- Hands-on practical experience delivering system design, application
  development, testing, and operational stability.
- Full stack developer experience with Java, Spring, Hibernate, ReactJS.
- Strong communicator, with experience of engaging with leadership/stakeholders.
- Experience in agile product development and managing technologists.
- Ability to tackle design and functionality problems independently
  with little to no oversight.
- Advanced knowledge of Java and experience of utilizing co-pilot
  or similar AI development tools.
- Practical cloud native experience and advanced knowledge of software
  applications and technical processes with considerable in-depth knowledge
  in one or more other technical disciplines (e.g., artificial intelligence,
  machine learning, mobile, etc.).
- Proficient in automation and continuous delivery methods and all aspects
  of the Software Development Life Cycle, including QA automation.
- Experience with Public Cloud & BigData/NoSQL database technologies.
"""


# ─────────────────────────────────────────────────────────────────────
# CANDIDATE 1 — Expected result: STRONG FIT (85-95%)
# Covers: 10+ years, Java full-stack, cloud-native, AI tools, BigData,
#         leadership, agile, CI/CD, QA automation
# ─────────────────────────────────────────────────────────────────────

CANDIDATE_STRONG_FIT = {
    "candidate_name": "Priya Sharma",
    "title": "Principal Software Engineer",
    "years_of_experience": 14,
    "summary": (
        "Principal Software Engineer with 14 years of experience in "
        "enterprise-grade full-stack development (Java, Spring Boot, "
        "Hibernate, React), cloud-native architecture (AWS, GCP, "
        "Kubernetes), and AI/ML integration. Led engineering teams of "
        "up to 18 members in fintech and healthcare domains."
    ),
    "technical_skills": [
        "Java", "Python", "TypeScript",
        "Spring Boot", "Hibernate", "ReactJS", "Next.js", "Node.js",
        "Apache Kafka", "Apache Spark", "Apache Flink",
        "AWS (EKS, Lambda, S3, RDS, EMR)", "GCP (BigQuery, GKE)",
        "Docker", "Kubernetes", "Terraform", "ArgoCD",
        "Jenkins", "GitHub Actions", "GitHub Copilot",
        "PostgreSQL", "Oracle", "MongoDB", "Cassandra", "Redis",
        "Elasticsearch", "Hadoop",
        "TensorFlow", "PyTorch", "LangChain", "LLMs",
        "REST APIs", "gRPC", "GraphQL",
    ],
    "soft_skills": [
        "Technical Mentoring & Coaching",
        "Executive Stakeholder Communication",
        "Agile/Scrum Product Delivery",
        "Architecture Review Board Lead",
        "Budget & Vendor Management",
        "Cross-functional Team Leadership",
    ],
    "certifications": [
        "AWS Solutions Architect – Professional",
        "Certified Kubernetes Administrator (CKA)",
        "Google Cloud Professional Data Engineer",
    ],
    "experience": [
        {
            "company": "FinCore Technologies",
            "role": "Principal Software Engineer",
            "duration": "2021 - Present",
            "accomplishments": [
                "Led a team of 18 engineers building a real-time payment "
                "processing platform on AWS EKS, handling 100K TPS with "
                "99.99% uptime.",
                "Architected full-stack dashboards using ReactJS + Spring "
                "Boot + Hibernate for regulatory compliance monitoring.",
                "Implemented ML-based fraud detection pipeline using "
                "TensorFlow and Apache Spark, reducing false positives by 40%.",
                "Adopted GitHub Copilot across the team, improving code "
                "velocity by 25% and reducing boilerplate code by 30%.",
                "Mentored 8 engineers through structured pairing sessions "
                "and architecture deep-dives; 3 promoted within 18 months.",
                "Drove CI/CD modernization with ArgoCD + GitHub Actions, "
                "achieving 15-minute deployment cycles from 4-hour builds.",
                "Established QA automation framework with Selenium, JUnit, "
                "and Cypress covering 92% of critical paths.",
            ],
        },
        {
            "company": "HealthBridge Systems",
            "role": "Staff Software Engineer",
            "duration": "2016 - 2021",
            "accomplishments": [
                "Designed and built patient data analytics platform on GCP "
                "BigQuery + Apache Spark, processing 5TB of daily records.",
                "Led migration from monolithic Java EE to Spring Boot "
                "microservices on Kubernetes, reducing release cycle from "
                "monthly to daily deployments.",
                "Built real-time event streaming infrastructure using "
                "Apache Kafka and Flink for clinical alert notifications.",
                "Engaged with C-suite stakeholders to align technology "
                "roadmap with HIPAA compliance requirements.",
                "Implemented NoSQL layer using MongoDB and Cassandra for "
                "high-throughput genomic data storage.",
            ],
        },
        {
            "company": "CodeWave Solutions",
            "role": "Senior Software Engineer",
            "duration": "2011 - 2016",
            "accomplishments": [
                "Built RESTful APIs in Java/Spring for e-commerce platform "
                "serving 2M daily users with sub-200ms response times.",
                "Developed automated regression testing suite using JUnit "
                "and Mockito, achieving 88% test coverage.",
                "Led agile ceremonies and sprint planning for a team of 6 "
                "engineers delivering bi-weekly releases.",
                "Migrated on-premise Oracle DB workloads to AWS RDS, "
                "reducing DB costs by 45%.",
            ],
        },
    ],
    "education": {
        "degree": "M.Tech in Computer Science",
        "university": "IIT Bombay",
        "graduation_year": 2011,
    },
}


# ─────────────────────────────────────────────────────────────────────
# CANDIDATE 2 — Expected result: MODERATE FIT (60-75%)
# Covers: Java backend (no ReactJS), some cloud (no BigData),
#         6 years experience (short of 10+), limited leadership
# ─────────────────────────────────────────────────────────────────────

CANDIDATE_MODERATE_FIT = {
    "candidate_name": "Ryan Mitchell",
    "title": "Senior Backend Engineer",
    "years_of_experience": 6,
    "summary": (
        "Senior Backend Engineer with 6 years of experience specializing "
        "in Java/Spring Boot microservices and AWS cloud infrastructure. "
        "Strong in system design and API development. Growing into "
        "leadership and exploring AI tooling for development productivity."
    ),
    "technical_skills": [
        "Java", "Python",
        "Spring Boot", "Hibernate", "JPA",
        "AWS (EC2, S3, RDS, Lambda, SQS)",
        "Docker", "Kubernetes",
        "Jenkins", "GitHub Actions",
        "PostgreSQL", "MySQL", "Redis",
        "REST APIs", "gRPC",
        "JUnit", "Mockito", "Testcontainers",
    ],
    "soft_skills": [
        "Technical Documentation",
        "Sprint Planning",
        "Code Review Leadership",
    ],
    "certifications": [
        "AWS Solutions Architect – Associate",
    ],
    "experience": [
        {
            "company": "ShopStream Inc.",
            "role": "Senior Backend Engineer",
            "duration": "2022 - Present",
            "accomplishments": [
                "Designed and built order management microservices using "
                "Java/Spring Boot, serving 50K orders/day with 99.9% uptime.",
                "Led migration from EC2-based deployments to EKS "
                "(Kubernetes), reducing infrastructure costs by 30%.",
                "Implemented automated integration testing with "
                "Testcontainers, reducing regression bugs by 60%.",
                "Mentored 2 junior developers on Spring Boot best "
                "practices and clean code principles.",
            ],
        },
        {
            "company": "DataPulse Analytics",
            "role": "Software Engineer",
            "duration": "2019 - 2022",
            "accomplishments": [
                "Built RESTful APIs in Java/Spring for internal analytics "
                "platform, handling 10K concurrent users.",
                "Implemented CI/CD pipeline with Jenkins and Docker, "
                "enabling daily deployments from weekly releases.",
                "Optimized PostgreSQL queries for reporting dashboard, "
                "reducing p95 latency from 2s to 300ms.",
            ],
        },
    ],
    "education": {
        "degree": "B.S. in Computer Science",
        "university": "University of Michigan",
        "graduation_year": 2019,
    },
}


# ─────────────────────────────────────────────────────────────────────
# CANDIDATE 3 — Expected result: WEAK FIT (below 60%)
# Covers: Frontend only (no Java backend), 3 years experience,
#         no cloud-native, no BigData, no leadership, no AI tools
# ─────────────────────────────────────────────────────────────────────

CANDIDATE_WEAK_FIT = {
    "candidate_name": "Emily Chen",
    "title": "Frontend Developer",
    "years_of_experience": 3,
    "summary": (
        "Frontend Developer with 3 years of experience building "
        "responsive web applications using React, TypeScript, and "
        "modern CSS frameworks. Passionate about user experience and "
        "accessibility. Looking to grow into full-stack development."
    ),
    "technical_skills": [
        "JavaScript", "TypeScript",
        "React", "Redux", "Next.js",
        "HTML5", "CSS3", "Tailwind CSS", "Material UI",
        "Node.js (basic)", "Express.js (basic)",
        "Git", "npm", "Webpack", "Vite",
        "Jest", "React Testing Library", "Cypress",
        "Figma", "Storybook",
    ],
    "soft_skills": [
        "UI/UX Collaboration",
        "Responsive Design",
        "Accessibility (WCAG)",
    ],
    "certifications": [],
    "experience": [
        {
            "company": "PixelCraft Studios",
            "role": "Frontend Developer",
            "duration": "2023 - Present",
            "accomplishments": [
                "Built a customer-facing e-commerce storefront using "
                "React + TypeScript, serving 20K daily visitors.",
                "Implemented responsive design system with Tailwind CSS "
                "and Storybook, reducing UI development time by 40%.",
                "Wrote end-to-end tests with Cypress covering 75% of "
                "critical user flows.",
            ],
        },
        {
            "company": "WebFlow Agency",
            "role": "Junior Frontend Developer",
            "duration": "2022 - 2023",
            "accomplishments": [
                "Developed landing pages and marketing sites using React "
                "and Next.js for 15+ client projects.",
                "Integrated REST APIs from backend services into "
                "frontend components using Axios and SWR.",
                "Participated in daily standups and sprint retrospectives "
                "in an agile team of 5 developers.",
            ],
        },
    ],
    "education": {
        "degree": "B.S. in Information Technology",
        "university": "San Jose State University",
        "graduation_year": 2022,
    },
}


# ── Convenience dict for programmatic access ─────────────────────────

TEST_CANDIDATES = {
    "strong_fit": CANDIDATE_STRONG_FIT,
    "moderate_fit": CANDIDATE_MODERATE_FIT,
    "weak_fit": CANDIDATE_WEAK_FIT,
}
