# Resume Fit Refactoring Walkthrough

The ADK-based Resume Fit Application has been successfully refactored from a CLI/file-path-based script into a high-performance, robust **FastAPI application**. The refactoring specifically addressed the logical halting and context truncation bugs.

## What Was Changed?

### 1. The FastAPI Web Layer
- **New `main.py` entrypoint**: Exposes a `POST /api/v1/resume/optimize` endpoint.
- **In-Memory Uploads**: Switched `document_parser_agent` and its underlying tools (`parse_pdf`, `parse_docx`) to process raw bytes directly from the user's `multipart/form-data` upload. This removes the need to constantly write/clean temporary files.

### 2. The Gatekeeper (Halting Bug Fixed)
- **Problem:** ADK's `SequentialAgent` wasn't aborting based on the `AlignmentValidatorAgent`'s JSON output text.
- **Solution:** Added `alignment_gatekeeper_node` (a fast, deterministic `PythonTaskNode`). It reads the previous agent's evaluation and, if rejected, raises an `AbortPipelineError`. This structurally halts the pipeline at zero additional token cost and prevents invalid resumes from executing downstream logic.

### 3. Chunked Rewrite Engine (Truncation Bug Fixed)
- **Problem:** Massive block arrays in the `ResumeRewriterAgent` caused LLMs to drop/truncate older experience items due to laziness/token limits context size.
- **Solution:** Changed `ResumeRewriterAgent` into a `PythonTaskNode` that:
  - Uses the `google.genai` client directly (Map-Reduce style).
  - Evaluates the "Base Resume" (Summary, Skills, Edu) in one prompt.
  - Iterates over the `experience` array and makes **individual LLM calls** for each previously held job.
  - Assertively enforces data retention: `assert len(original) == len(rewritten)`.

### 4. PDF Rendering Strategy (`xhtml2pdf`)
- Created a server-compatible, dependency-free PDF generator right within `main.py`.
- Stripped all `flexbox` and modern layout CSS from `sub_agents/html_renderer/templates/resume.html` to guarantee perfect `xhtml2pdf` compatibility. It now uses structurally pure tables to align dates and roles.
- The HTTP response natively returns `application/pdf` with the candidate's custom `X-ATS-Score` headers for lightweight frontend parsing.

## How to Test

1. Ensure the new dependencies are installed:
    ```bash
    pip install -r requirements.txt
    ```
2. Start the API server:
    ```bash
    uvicorn main:app --reload
    ```
3. Test using `curl` to ensure it streams back the final PDF!

> [!TIP]
> If you decide you'd rather see the raw JSON layout, you can quickly fork the `main.py` return response to send back `session.state.get("resume_rewriter_output")` instead!
