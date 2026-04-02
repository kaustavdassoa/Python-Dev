"""
HTML Renderer Tools

Converts the rewritten resume JSON structure into a styled HTML document
using Jinja2 templating.
"""

import json
import os


def render_resume_html(rewritten_resume_json: str) -> dict:
    """
    Render a rewritten resume dict as a styled HTML page using Jinja2.

    Args:
        rewritten_resume_json: JSON string matching the rewritten_resume schema:
            {
              "contact": { "name", "email", "phone", "location", "linkedin" },
              "summary": str,
              "skills": [str, ...],
              "experience": [{ "title", "company", "dates", "bullets": [str] }],
              "education": [{ "degree", "institution", "year" }],
              "certifications": [str]  (optional)
            }

    Returns:
        dict with: success (bool), html (str), error (str|None)
    """
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        return {
            "success": False,
            "html": "",
            "error": "Jinja2 not installed. Run: pip install jinja2",
        }

    # Parse the JSON input
    try:
        resume_data = json.loads(rewritten_resume_json)
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "html": "",
            "error": f"Invalid JSON input: {str(e)}",
        }

    # Load Jinja2 template
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    try:
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("resume.html")
        html = template.render(**resume_data)
        return {"success": True, "html": html, "error": None}
    except Exception as e:
        return {"success": False, "html": "", "error": f"Rendering failed: {str(e)}"}
