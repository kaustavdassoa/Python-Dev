"""
HTML Renderer Agent (Agent 8 of 9) - Deterministic

Converts the rewritten resume JSON into a styled, self-contained
HTML document using Jinja2 templating.
"""

import json
from ...shared.python_task_node import PythonTaskNode
from ...shared.utils import get_dict_from_state
from .tools import render_resume_html

def run_html_renderer(state: dict) -> str:
    rewriter_out = get_dict_from_state(state.get("resume_rewriter_output", {}))
    rewritten_resume = rewriter_out.get("rewritten_resume", {})
    
    # Ensure all expected fields are present with empty defaults
    if not isinstance(rewritten_resume.get("contact"), dict):
        rewritten_resume["contact"] = { "name": "", "email": "", "phone": "", "location": "", "linkedin": "" }
    rewritten_resume.setdefault("summary", "")
    rewritten_resume.setdefault("skills", [])
    rewritten_resume.setdefault("experience", [])
    rewritten_resume.setdefault("education", [])
    rewritten_resume.setdefault("certifications", [])

    # The tool expects a JSON string
    rewritten_json = json.dumps(rewritten_resume)
    
    result = render_resume_html(rewritten_json)
    if not result.get("success"):
        raise RuntimeError(f"HTML Rendering Failed: {result.get('error')}")
    
    html_output = result.get("html", "")
        
    return html_output

html_renderer_agent = PythonTaskNode(
    name="HTMLRendererAgent",
    task_func=run_html_renderer,
    output_key="html_renderer_output",
    description="Deterministic node that converts rewritten resume to a styled HTML document."
)
