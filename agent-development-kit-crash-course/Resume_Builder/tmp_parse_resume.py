import sys
import os

# Add the project root to sys.path to import tools
_PACKAGE_DIR = r"E:\GitHub\Python-Dev\agent-development-kit-crash-course\Resume_Builder"
if _PACKAGE_DIR not in sys.path:
    sys.path.insert(0, _PACKAGE_DIR)

from resume_optimizerv2.sub_agents.document_parser.tools import parse_pdf

file_path = r"E:\GitHub\Python-Dev\agent-development-kit-crash-course\Resume_Builder\data\KaustavDas_Resume_3.0.pdf"
output_path = "tmp_resume_text.txt"

with open(file_path, "rb") as f:
    res = parse_pdf(f.read())
    if res["success"]:
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(res["text"])
        print(f"Success: Text written to {output_path}")
    else:
        print(f"Error: {res['error']}")
