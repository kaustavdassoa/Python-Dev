# Resume Optimizer — Refactoring Implementation Plan

Four changes requested: verbose logging, revert to HTML output, dynamic report file, and project rename.

---

## 1. Enhance Logging (Verbose Mode)

> [!IMPORTANT]  
> Currently, the event loop in `main.py` only prints `[AgentName] -> Event produced`. We need to mirror the `adk web` style.

### Changes:

#### [MODIFY] [main.py](file:///E:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_fit_agent/main.py)

- Replace the minimal event logging loop with a verbose logger that for each event prints:
  - **Agent name**, **event type** (text response, function_call, function_response, state_delta)
  - **Function call details**: tool name + truncated args
  - **State delta keys** when `event.actions.state_delta` is non-empty
  - **Text content** (truncated to 200 chars) for LLM responses
  - **Timestamps** and event counter
- Add a `log_event(event, index)` helper function for clean formatting

#### [MODIFY] [python_task_node.py](file:///E:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_fit_agent/shared/python_task_node.py)

- Add `print()` statements at entry/exit to clearly log deterministic node execution with timing

---

## 2. Revert Output to HTML (Drop PDF)

> [!IMPORTANT]  
> Remove `xhtml2pdf` dependency entirely. Write HTML files directly to disk using the **original** template from `output/resume.html`.

### Changes:

#### [MODIFY] [resume.html template](file:///E:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_fit_agent/sub_agents/html_renderer/templates/resume.html)

- Replace current xhtml2pdf-compatible template with the **original** high-quality template from `E:\...\output\resume.html` (flexbox, skill tags, print media queries, `.resume-wrapper`)

#### [MODIFY] [main.py](file:///E:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_fit_agent/main.py)

- Remove `xhtml2pdf` import and PDF generation logic
- After pipeline completes, write `html_renderer_output` to disk as `<session_id>_<NAME>_resume.html` in the `output/` directory
- Return the HTML content with `text/html` media type instead of `application/pdf`

#### [MODIFY] [requirements.txt](file:///E:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_fit_agent/requirements.txt)

- Remove `xhtml2pdf==0.2.16`

#### [MODIFY] [test_api.py](file:///E:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_fit_agent/test_api.py)

- Update to save `.html` output instead of `.pdf`

---

## 3. Dynamic Report File Generation

> [!IMPORTANT]  
> The `ReportGeneratorAgent` currently returns a markdown string to state only. We need it to also write a file to disk.

### Changes:

#### [MODIFY] [main.py](file:///E:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_fit_agent/main.py)

- After pipeline completes, extract `final_report` from state
- Write it to `<output_dir>/<session_id>_<NAME>_resume_optimization_report.html`
- Wrap the markdown report in a minimal styled HTML shell for browser readability
- Log the file path to console

---

## 4. Project Rename: `resume_fit_agent` → `resume_optimizer`

> [!WARNING]  
> This involves a filesystem directory rename. All imports, docstrings, `.env` comments, agent names, and app_name constants will be updated.

### Steps:

1. **Rename directory**: `resume_fit_agent/` → `resume_optimizer/`
2. **Update all string references** across these files:
   - `agent.py`: docstring, `name="ResumeFitPipeline"` → `name="ResumeOptimizerPipeline"`
   - `main.py`: `app_name="ResumeFitAPI"` → `app_name="ResumeOptimizerAPI"`, FastAPI title
   - `.env`: comment header
   - `requirements.txt`: comment header
   - `__init__.py`: no import path changes needed (relative)
   - `sub_agents/__init__.py`: comment
   - `report_generator/agent.py`: "Resume Fit Agent" → "Resume Optimizer"
   - All LLM instruction strings referencing "Resume Fit Pipeline"
   - `walkthrough.md`, `remediation_plan.md`, etc.

---

## Verification Plan

### Automated Tests
1. Start the server: `python -m uvicorn main:app --reload`
2. Run `python test_api.py`
3. Verify:
   - Console shows verbose agent-level logs with event details
   - Two files written to `output/`:
     - `<session_id>_<NAME>_resume.html` (resume)
     - `<session_id>_<NAME>_resume_optimization_report.html` (report)
   - Resume HTML matches the quality of the reference sample
   - API returns HTML content (not PDF)

### Manual Verification
- Open both HTML files in browser to confirm formatting and data completeness

---

## Open Questions

> [!IMPORTANT]  
> **Report format**: You asked for the report filename to end in `.html`. The current report is **Markdown**. Should I:
> - **(A)** Wrap the markdown in a styled HTML page (recommended — renders nicely in browser), or
> - **(B)** Save it as raw `.md` and rename the convention to `.md`?

I'll go with **(A)** unless you say otherwise.
