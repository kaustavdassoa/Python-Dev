import sys
import os

# Ensure the parent directory is in sys.path so we can import resume_optimizerv2 as a package
_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_PACKAGE_DIR)
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

import io
import json
import uuid
import time
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response

# Import the pipeline (as a package so relative imports work)
from resume_optimizerv2.agent import root_agent

# Document Tools
from resume_optimizerv2.sub_agents.document_parser.tools import parse_pdf, parse_docx, parse_plain_text

from google.adk.runners import InMemoryRunner
from google.genai import types

app = FastAPI(
    title="Resume Optimizer API",
    description="ADK-based Resume Optimizer Pipeline"
)

# Initialize Runner once to keep session service alive
runner = InMemoryRunner(agent=root_agent, app_name="ResumeOptimizerAPI")

# Output directory
OUTPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "output")
)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ──────────────────────────── Verbose Logger ────────────────────────────────
def log_event(event, index: int):
    """
    Mirror the adk web logging style: show agent name, event type,
    function calls, state deltas, and content previews.
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    author = event.author or "unknown"
    
    # Determine event type
    func_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else []
    func_responses = event.get_function_responses() if hasattr(event, 'get_function_responses') else []
    state_delta = event.actions.state_delta if event.actions else {}
    
    # Header
    print(f"\n{'─'*70}")
    print(f"  [{timestamp}] Event #{index}  │  Author: {author}")
    print(f"{'─'*70}")
    
    # Function Calls
    if func_calls:
        for fc in func_calls:
            args_preview = str(fc.args)[:150] + "..." if len(str(fc.args)) > 150 else str(fc.args)
            print(f"  🔧 FUNCTION CALL: {fc.name}")
            print(f"     Args: {args_preview}")
    
    # Function Responses
    if func_responses:
        for fr in func_responses:
            resp_preview = str(fr.response)[:200] + "..." if len(str(fr.response)) > 200 else str(fr.response)
            print(f"  📥 FUNCTION RESPONSE: {fr.name}")
            print(f"     Response: {resp_preview}")
    
    # State Delta
    if state_delta:
        delta_keys = list(state_delta.keys())
        print(f"  📦 STATE DELTA: {delta_keys}")
        for k, v in state_delta.items():
            if isinstance(v, str):
                print(f"     • {k}: string ({len(v)} chars)")
            elif isinstance(v, dict):
                print(f"     • {k}: dict with keys {list(v.keys())[:5]}")
            elif isinstance(v, list):
                print(f"     • {k}: list ({len(v)} items)")
            elif isinstance(v, bool):
                print(f"     • {k}: {v}")
            else:
                print(f"     • {k}: {type(v).__name__}")
    
    # Text Content (LLM response)
    if not func_calls and not func_responses:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    preview = part.text[:300].replace("\n", " ↵ ")
                    if len(part.text) > 300:
                        preview += f"... ({len(part.text)} chars total)"
                    print(f"  💬 TEXT: {preview}")


# ─────────────────────── Helper: Extract name from state ────────────────────
def extract_name(final_state: dict) -> str:
    """Extract candidate name from rewriter output, with fallback to parser."""
    rewriter_out = final_state.get("resume_rewriter_output", {})
    if isinstance(rewriter_out, str):
        try:
            rewriter_out = json.loads(rewriter_out)
        except Exception:
            rewriter_out = {}
    
    name = rewriter_out.get("rewritten_resume", {}).get("contact", {}).get("name", "")
    
    # Fallback to document parser
    if not name:
        doc_out = final_state.get("document_parser_output", {})
        if isinstance(doc_out, str):
            try:
                doc_out = json.loads(doc_out)
            except Exception:
                doc_out = {}
        name = doc_out.get("resume_sections", {}).get("contact", {}).get("name", "Unknown")
    
    return name or "Unknown"


# ─────────────── Helper: Wrap markdown report in styled HTML ────────────────
def wrap_report_in_html(markdown_text: str, candidate_name: str) -> str:
    """Wrap a markdown report in a styled HTML page for browser readability."""
    import re
    
    # Simple markdown → HTML conversion for the report
    html_body = markdown_text
    
    # Headers
    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
    
    # Bold
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    
    # Horizontal rules
    html_body = re.sub(r'^---$', r'<hr>', html_body, flags=re.MULTILINE)
    
    # List items
    html_body = re.sub(r'^- (.+)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)
    
    # Tables (simple conversion)
    lines = html_body.split('\n')
    in_table = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if all(set(c) <= set('-| ') for c in cells):
                continue  # skip separator rows
            if not in_table:
                new_lines.append('<table>')
                in_table = True
                new_lines.append('<tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr>')
            else:
                new_lines.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
        else:
            if in_table:
                new_lines.append('</table>')
                in_table = False
            new_lines.append(line)
    if in_table:
        new_lines.append('</table>')
    html_body = '\n'.join(new_lines)
    
    # Wrap paragraphs (lines that aren't tags)
    final_lines = []
    for line in html_body.split('\n'):
        stripped = line.strip()
        if stripped and not stripped.startswith('<') and not stripped.startswith('>'):
            final_lines.append(f'<p>{stripped}</p>')
        else:
            final_lines.append(line)
    html_body = '\n'.join(final_lines)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{candidate_name} — Resume Optimization Report</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
      font-size: 10.5pt;
      color: #1a1a2e;
      background: #f0f2f5;
      padding: 30px 20px;
      line-height: 1.6;
    }}
    .report-wrapper {{
      max-width: 860px;
      margin: 0 auto;
      background: #ffffff;
      padding: 44px 56px;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0,0,0,0.05);
      border-radius: 4px;
    }}
    h1 {{ font-size: 22pt; color: #1a365d; margin-bottom: 12px; border-bottom: 2.5px solid #1a365d; padding-bottom: 10px; }}
    h2 {{ font-size: 14pt; color: #1a365d; margin-top: 24px; margin-bottom: 8px; }}
    h3 {{ font-size: 11pt; color: #2d4a7a; margin-top: 16px; margin-bottom: 6px; }}
    hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 20px 0; }}
    p {{ margin-bottom: 8px; }}
    strong {{ color: #1a1a2e; }}
    li {{ margin-bottom: 4px; margin-left: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    th, td {{ text-align: left; padding: 8px 12px; border: 1px solid #ddd; }}
    th {{ background: #eef2f8; color: #1a365d; font-weight: 600; }}
    td {{ color: #333; }}
    tr:nth-child(even) td {{ background: #fafbfc; }}
    @media print {{
      body {{ background: white; padding: 0; }}
      .report-wrapper {{ box-shadow: none; padding: 0; max-width: none; }}
    }}
  </style>
</head>
<body>
  <div class="report-wrapper">
{html_body}
  </div>
</body>
</html>"""


# ──────────────────────────── API Endpoint ──────────────────────────────────
@app.post("/api/v1/resume/optimize")
async def optimize_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=400, detail="Only .pdf, .docx, and .txt files are supported")
    
    file_bytes = await file.read()
    
    # 1. Parse Resume manually before pipeline
    if ext == ".pdf":
        parse_res = parse_pdf(file_bytes)
    elif ext == ".docx":
        parse_res = parse_docx(file_bytes)
    else:
        parse_res = parse_plain_text(file_bytes.decode('utf-8', errors='ignore'))
        
    if not parse_res["success"]:
        raise HTTPException(status_code=400, detail=parse_res["error"])
        
    raw_resume_text = parse_res["text"]
    
    # 2. Setup ADK initial state
    initial_state = {
        "raw_resume_text": raw_resume_text,
        "raw_jd_text": job_description,
    }
    
    # 3. Create Session
    uid = str(uuid.uuid4())
    session = runner.session_service.create_session(
        app_name="ResumeOptimizerAPI", 
        user_id=uid, 
        state=initial_state
    )
    
    # Wrap resume text + JD into a single user message for the ADK pipeline
    prompt_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=f"[RESUME]\n{raw_resume_text}\n\n[JOB DESCRIPTION]\n{job_description}")]
    )
    
    try:
        # Run the pipeline with verbose logging
        pipeline_start = time.time()
        event_count = 0
        
        print("\n")
        print("=" * 70)
        print(f"  🚀 RESUME OPTIMIZER PIPELINE STARTING")
        print(f"  Session: {session.id}  |  User: {uid}")
        #print(f"  File: {file.filename}  |  Time: {datetime.now().strftime('%H:%M:%S')}  |  Model: {MODEL_NAME}")
        print(f"  File: {file.filename}  |  Time: {datetime.now().strftime('%H:%M:%S')}  |  Model: {os.environ.get('MODEL_NAME', 'NOT FOUND')}")
        print("=" * 70)
        
        async for event in runner.run_async(
            user_id=uid,
            session_id=session.id,
            new_message=prompt_content
        ):
            event_count += 1
            log_event(event, event_count)
            
        elapsed = time.time() - pipeline_start
        print(f"\n{'=' * 70}")
        print(f"  ✅ PIPELINE COMPLETE  |  {event_count} events  |  {elapsed:.1f}s elapsed")
        print(f"{'=' * 70}\n")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
        
    # Get Final Session State
    final_session = runner.session_service.get_session(
        app_name="ResumeOptimizerAPI", user_id=uid, session_id=session.id
    )
    
    # Debug summary
    state = final_session.state
    print(f"  [STATE] pipeline_halted: {state.get('pipeline_halted')}")
    print(f"  [STATE] halt_reason: {state.get('halt_reason')}")
    print(f"  [STATE] html_renderer_output: {'✅ present' if state.get('html_renderer_output') else '❌ missing'} ({len(state.get('html_renderer_output', ''))} chars)")
    print(f"  [STATE] final_report: {'✅ present' if state.get('final_report') else '❌ missing'} ({len(state.get('final_report', ''))} chars)")
    
    if state.get("pipeline_halted"):
        reason = state.get("halt_reason", "Candidate rejected.")
        raise HTTPException(status_code=400, detail=f"Pipeline aborted: {reason}")
        
    html_output = state.get("html_renderer_output", "")
    if not html_output:
        raise HTTPException(status_code=500, detail="HTML renderer produced no output.")
    
    # ── Extract candidate name ──
    candidate_name = extract_name(state)
    name_formatted = candidate_name.replace(" ", "_").upper()
    
    # ── Save Resume HTML to disk ──
    resume_filename = f"{session.id}_{name_formatted}_resume.html"
    resume_path = os.path.join(OUTPUT_DIR, resume_filename)
    with open(resume_path, "w", encoding="utf-8") as f:
        f.write(html_output)
    print(f"\n  📄 Resume HTML saved: {resume_path}")
    
    # ── Save Report HTML to disk ──
    report_markdown = state.get("final_report", "")
    if report_markdown:
        report_html = wrap_report_in_html(report_markdown, candidate_name)
        report_filename = f"{session.id}_{name_formatted}_resume_optimization_report.html"
        report_path = os.path.join(OUTPUT_DIR, report_filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_html)
        print(f"  📊 Report HTML saved: {report_path}")
    
    # ── Return HTML Response ──
    ats_score = state.get("ats_scorer_output", {})
    if isinstance(ats_score, dict):
        ats_score = ats_score.get("ats_score_after", 0)
    else:
        ats_score = 0
    
    headers = {
        "X-ATS-Score": str(ats_score),
        "X-Resume-File": resume_filename,
        "X-Report-File": report_filename if report_markdown else "",
        "Content-Disposition": f'attachment; filename="{resume_filename}"'
    }
    
    return Response(
        content=html_output,
        media_type="text/html",
        headers=headers
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
