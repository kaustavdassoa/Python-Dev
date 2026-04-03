import requests
import json
import re
import os

# The URL of your local FastAPI server
url = "http://localhost:8000/api/v1/resume/optimize"

# The file pathway to the original resume
file_path = r"E:\GitHub\Python-Dev\agent-development-kit-crash-course\Resume_Builder\data\Trishan_Kakoti_SBI_Life_Manager_12302025.pdf"

# The Job Description
job_description = """
About the job
Key Responsibilities

Lead end-to-end requirement analysis, solution design, and stakeholder management for complex insurance projects.
Demonstrate strong domain knowledge across policy administration, underwriting, claims, and digital insurance platforms.
Translate complex business requirements into detailed technical specifications for engineering teams.
Handle complex integrations, system migrations, and large-scale UAT cycles.
Drive Agile / Scrum ceremonies and work closely with product owners and delivery teams.
Serve as the primary point of contact for business stakeholders and technology teams, ensuring alignment throughout delivery.
Mentor junior BAs and contribute to team capability building.


Required Skills & Experience

6–8 years of extensive experience as a Technical Business Analyst in the General Insurance domain (Motor or P&C preferred).
Strong domain knowledge across policy administration, underwriting, claims, and digital platforms.
Lead-level experience in end-to-end requirement analysis, solution design, and stakeholder management.
Proven ability to translate business requirements into technical specifications.
Experience handling complex integrations, system migrations, and UAT cycles.
Prior exposure to Agile / Scrum environments strongly preferred.
Strong leadership, communication, and problem-solving skills.
Minimum 2 years of tenure at a single organization (fewer job switches preferred).
Immediate joiners preferred.
Qualification: BE / BTech / MCA / MBA only.
"""

print(f"Sending request to {url}...")
print(f"Reading file: {file_path}")

try:
    with open(file_path, "rb") as f:
        files = {
            "file": ("Trishan_Kakoti_SBI_Life_Manager_12302025.pdf", f, "application/pdf")
        }
        data = {
               "job_description": job_description
        }
        
        response = requests.post(url, files=files, data=data)

        # response = requests.post(url, data=data)
        
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
