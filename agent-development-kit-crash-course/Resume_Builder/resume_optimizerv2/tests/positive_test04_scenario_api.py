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
Job Title: Principal Software Engineer – AI & Intelligent Automation

About the Role:
We are looking for a visionary, hands-on leader to drive our next generation of internal systems. You will architect and build LLM-powered applications, agentic workflows, and intelligent automation platforms to modernize our enterprise operations.

Key Responsibilities:
* Architect scalable GenAI solutions using Python, Java, and modern LLM orchestration frameworks (e.g., LangGraph).
* Lead the development of agentic AI frameworks for enterprise workflow automation, including intelligent triage and process routing.
* Drive the technical roadmap for integrating foundation models into internal, highly-regulated platforms.
* Manage, mentor, and direct cross-functional engineering teams to deliver resilient, cloud-native systems (Kubernetes/OCP).

Required Qualifications:
* 15+ years of progressive software engineering experience, with deep expertise in Java, Spring Boot, and Python.
* Practical experience building and deploying LLM-powered applications, prompt engineering, or agentic workflows.
* Strong hands-on background in cloud platforms and DevSecOps practices.
* Proven ability to act as a hands-on leader who can balance high-level architecture roadmapping with tactical coding and code reviews.

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
