import requests
import json
import re
import os

# The URL of your local FastAPI server
url = "http://localhost:8000/api/v1/resume/optimize"

# The file pathway to the original resume
file_path = r"E:\GitHub\Python-Dev\agent-development-kit-crash-course\Resume_Builder\data\KaustavDas_Resume_3.0.pdf"

# The Job Description
job_description = """
Job Title: Principal Software Engineer – Regulatory & Compliance Technology

About the Role:
We are seeking a Seasoned Lead Software Engineer to drive large-scale modernization programs within our Regulatory and Compliance domains. In this role, you will lead cross-functional engineering teams to deliver business-driven transformations, resolve audit findings, and modernize legacy financial platforms.

Key Responsibilities:
Architect and develop highly scalable, resilient platforms using Java, Spring Boot, and microservices.
Lead cloud-native engineering and migration initiatives, specifically targeting containerized environments like Kubernetes and OpenShift (OCP).
Partner directly with compliance, audit, and executive stakeholders to align technology roadmaps with enterprise risk standards and regulatory obligations.
Drive DevSecOps adoption, enforce secure SDLC practices, and govern Non-Functional Requirements (NFR) such as High Availability (HA) and Disaster Recovery (DR).
Manage, mentor, and direct engineering teams (experience leading teams of 15+ engineers is highly preferred).
Lead budget planning, resource allocation, and vendor engagements for major application modernization initiatives.
Explore and pioneer the integration of AI/GenAI technologies (such as LLMs and agentic frameworks) to automate complex enterprise workflows and compliance operations.

Required Qualifications:

15+ years of progressive software engineering experience.
Expert-level proficiency in Java, Spring Boot, and RESTful API design.
Strong hands-on background in DevOps tools (Jenkins, Docker) and relational/NoSQL databases (Oracle, MongoDB, MySQL).
Proven experience in the banking or financial services sector, specifically handling Regulatory Compliance and audit remediation.
Demonstrated ability to champion API-first strategies and headless workflows to reduce time-to-market.

Preferred Skills:
Practical experience or active exploration of Python, LangGraph, and Prompt Engineering for workflow automation.
Relevant cloud or containerization certifications (e.g., Certified Kubernetes Application Developer).

"""

print(f"Sending request to {url}...")
print(f"Reading file: {file_path}")

try:
    with open(file_path, "rb") as f:
        files = {
            "file": ("KaustavDas_Resume_3.0.pdf", f, "application/pdf")
        }
        data = {
            "job_description": job_description
        }
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            print("✅ Success! Pipeline finished successfully.")
            
            # Extract ATS score header
            ats_score = response.headers.get("X-ATS-Score", "Undetermined")
            print(f"New ATS Score: {ats_score}")
            
            # Extract filenames from headers
            resume_file = response.headers.get("X-Resume-File", "")
            report_file = response.headers.get("X-Report-File", "")
            
            # Extract resume filename from Content-Disposition
            cd_header = response.headers.get("Content-Disposition", "")
            match = re.search(r'filename="?([^"]+)"?', cd_header)
            output_filename = match.group(1) if match else "Optimized_Resume.html"
            
            # The server already saves both files to output/, but we also
            # save the response body (resume HTML) for convenience
            output_dir = r"E:\GitHub\Python-Dev\agent-development-kit-crash-course\Resume_Builder\output"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, output_filename)
            
            with open(output_file, "w", encoding="utf-8") as out_f:
                out_f.write(response.text)
            
            print(f"✅ Optimized Resume saved to: {output_file}")
            if resume_file:
                print(f"   Server-side resume: output/{resume_file}")
            if report_file:
                print(f"   Server-side report: output/{report_file}")
            
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            try:
                print(f"Error details: {json.dumps(response.json(), indent=2)}")
            except:
                print(response.text)
except FileNotFoundError:
    print(f"❌ Could not find file {file_path}")
except Exception as e:
    print(f"❌ An error occurred: {str(e)}")
