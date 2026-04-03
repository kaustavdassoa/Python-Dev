"""
HTML Renderer Agent (Agent 8 of 9) - Deterministic

Converts the rewritten resume JSON into a styled, self-contained
HTML document using Jinja2 templating.
"""

import json
from ...shared.python_task_node import PythonTaskNode
from .tools import render_resume_html

def get_dict_from_state(val):
    """Extract a dict from raw state value (may be dict, JSON string, or markdown-wrapped JSON)."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        import re
        # Strategy 1: markdown code-block extraction
        match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', val, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        # Strategy 2: outermost brace matching
        first_brace = val.find('{')
        last_brace = val.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(val[first_brace:last_brace + 1])
            except Exception:
                pass
        # Strategy 3: raw string
        try:
            return json.loads(val.strip())
        except Exception:
            pass
    return {}

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
