# Resume Fit Refactoring Roadmap

This document outlines the three-phase plan to completely refactor the ADK-based Resume Fit Application, moving it from local scripts to a robust REST API while resolving logical halting and context truncation bugs.

## Phase 1: Forensic Log & Logic Review
Based on `@analyze-project` and `@systematic-debugging` principles, here are the root causes for the pipeline's current issues:

### 1. The Halting Logic Bug
**Symptom:** `SequentialAgent` does not stop even when the resume is deemed unfit by the `AlignmentValidatorAgent`.
**Root Cause (`AGENT_ARCHITECTURAL_ERROR`):** The `AlignmentValidatorAgent` is an `LlmAgent`. Although prompted to act as a "HARD GATE" and output "❌ PIPELINE HALTED" physically in text and JSON, ADK's `SequentialAgent` does not inherently inspect the text of an `output_key` to break its loop. Downstream agents have a guard `If pipeline_halted is true in state...`, but the boolean state key `pipeline_halted` is **never actually set** because `LlmAgent` only writes to its assigned `output_key` string.
**Fix:** We need a programmatic `PythonTaskNode` injected after the validator to evaluate the JSON and explicitly set `state["pipeline_halted"] = True` or raise an `AbortPipelineError`.

### 2. Context Truncation (Dropped Pages)
**Symptom:** The final generated output drops pages (usually older experience entries).
**Root Cause (`LEGITIMATE_TASK_COMPLEXITY` & `SPEC_AMBIGUITY`):** The `ResumeRewriterAgent` processes the entire parsed resume in one single shot. LLMs suffer from "laziness" and token-limit constraints when generating massive JSON arrays. Under the monolithic `ResumeRewriterOutputSchema`, the LLM silently truncates the `experience` array to save generation tokens. It drops the older jobs (which conceptually live on pages 2-3).
**Fix:** We must chunk the processing. Instead of one massive rewrite, the pipeline should isolate the `experience` items. We must enforce strict data retention using `@llm-structured-output` validation (e.g., assert `len(input_experience) == len(output_experience)`).

---

## Phase 2: API & Architecture Brainstorm
Following `@brainstorming`, `@pdf-official`, and `@llm-structured-output` methodologies, below is the proposed architecture:

### Proposed API Endpoints
- **`POST /api/v1/resume/optimize`**
  **Input:** `multipart/form-data` containing:
  - `file`: UploadFile (PDF or DOCX).
  - `job_description`: string.
  **Output:** `application/pdf` (Binary stream of the final formatted PDF) with custom headers providing the ATS Score.

### Updated System Architecture
1. **API Layer (FastAPI):** Exposes the endpoint, handles file uploads in-memory.
2. **Parser Layer:** Uses `pdfplumber` and `python-docx` to extract text from byte streams (no local file saving required).
3. **Pipeline Orchestrator (ADK `SequentialAgent`):**
   - **Evaluator Nodes:** Parse JD and Validate Alignment.
   - **Gatekeeper Node:** A deterministic Python node enforcing the HALT condition by checking the alignment output.
   - **Chunked Rewriter Node:** A Map-Reduce style node that rewrites `summary`, `skills`, and handles `experience` item by item to guarantee 100% data retention.
4. **Renderer Layer:** Convert the rewritten JSON to HTML (Jinja2), then convert HTML to PDF using a library like `pdfkit` or `WeasyPrint` before returning the HTTP response.

> [!IMPORTANT]
> **Core Assumptions**: 
> 1. You prefer **FastAPI** as the web framework going forward.
> 2. We will generate the PDF dynamically rather than saving to the local disk.
> 3. You are comfortable refactoring the one-shot rewrite agent into a mapped/chunked process.

---

## Phase 3: The Remediation Plan

If the above understanding and API architecture align with your goals, here are the concrete action items prioritizing `@clean-code` and `@concise-planning`:

### Scope
- **In:** Converting app to FastAPI, implementing Map-Reduce for resume rewriting, fixing pipeline halt state, converting HTML to PDF.
- **Out:** Replacing ADK with another framework, changing the upstream prompt templates (unless required for structured extraction).

### Action Items

- [ ] **Step 1: Bootstrap FastAPI Wrapper** 
      Create a `main.py` configuring FastAPI and standard `multipart/form-data` endpoints.
- [ ] **Step 2: Streamline Document Tools** 
      Refactor `parse_pdf` and `parse_docx` to read from byte streams instead of static file paths.
- [ ] **Step 3: Implement Pipeline Gatekeeper** 
      Create a `PythonTaskNode` to act as an evaluator after `alignment_validator_agent`. It will evaluate the JSON and officially halt the pipeline if the candidate fails the alignment check.
- [ ] **Step 4: Refactor Rewrite Agent (Chunking)** 
      Split `ResumeRewriterAgent`'s task. Process `experience` as an iterable list and enforce post-validation (asserting array lengths match) using strict Pydantic parsing (`@llm-structured-output`).
- [ ] **Step 5: Setup PDF Rendering Strategy** 
      Refactor `html_renderer_agent` to output an actual binary PDF (using a library like `WeasyPrint` or `pdfkit`) instead of stopping at HTML.
- [ ] **Step 6: Endpoint Integration** 
      Wire the ADK execution into the FastAPI endpoint, returning the generated PDF directly to the user.
- [ ] **Step 7: Validation & Testing** 
      Test halting logic by sending a barista resume for an engineering JD. Test context length logic by uploading a 3-page resume.

> [!WARNING]
> **Open Questions for Reviewer**
> 1. Do you have a preference for the PDF rendering library? `pdfkit` requires system packages (wkhtmltopdf), whereas `WeasyPrint` handles HTML/CSS nicely but might need dev libraries.
> 2. Does the plan to use an explicit `PythonTaskNode` for the gatekeeper align with your preferences for ADK?

**Please review this plan. Respond with your approval or modifications, and I will begin the implementation.**
