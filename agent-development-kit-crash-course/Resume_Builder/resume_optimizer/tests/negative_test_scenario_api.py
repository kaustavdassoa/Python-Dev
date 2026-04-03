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
Join us as a Principal Enterprise Architect, Director

We'll look to you to lead the definition of the overall architecture vision, strategic target architecture and roadmap, aligning them with business strategy and objectives
You'll be leading architecture decision making, partnering with key business and digital leaders to develop and evolve a comprehensive target architecture and roadmap
With valuable exposure, you'll cultivate strong relationships and proactively engage with key stakeholders, including C-level business and technology executives, vendors and partners, and industry thought leaders
We're offering the role at Director level

What you'll do
As a Principal Enterprise Architect, you'll be leading teams of architects and engineers to architect customer centric, high performance, secure, robust and sustainable end to end digital products, solutions, and services that drive capability models, roadmaps and long term strategic architecture planning while aligning to the bank's strategic target architecture.

The skills you'll need
To succeed in this role, you'll need extensive expert knowledge of enterprise architecture frameworks, modern technologies such as Cloud, microservices and AI, agile architecture and DevOps practices, including a deep understanding of business use cases and emerging trends that drive organisational success.
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
