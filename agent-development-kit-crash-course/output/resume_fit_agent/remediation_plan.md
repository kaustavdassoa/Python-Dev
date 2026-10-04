# Plan: Resume Fit Agent Remediation

We are refactoring the Resume Fit Agent pipeline to optimize token usage, prevent hallucinated "upgrades" on unrelated experience, and ensure the pipeline degrades gracefully instead of failing abruptly during quality checks.

## Scope

- **In:** 
  - Creating a reusable `PythonTaskNode(BaseAgent)` to execute deterministic steps.
  - Converting 4 agents (ATSPreCheck, ATSScorer, HTMLRenderer, and ReportGenerator) to pure `PythonTaskNode` instances.
  - Prompt updates for Rewriter and Critic agents.
  - Enforcing strict structured outputs using Pydantic schemas for LLMs preceding a deterministic node to avoid brittle handoffs.
- **Out:** 
  - Adding new subagents.
  - Modifying the web UI or deploying the application.

## Action Items

- [ ] **Step 0: Create `PythonTaskNode` Wrapper.** Create a reusable `BaseAgent` subclass that takes a standard Python callable, `input_keys`, and an `output_key`. It must include strict `try/except` blocks to handle standard errors and gracefully set an `error_state` and `pipeline_halted: true` on `context.session.state` to prevent hard crashes.
- [ ] **Step 1: Enforce Structured Outputs (Pydantic).** Do not rely on prompt engineering for JSON formatting. Define exact Pydantic/dataclass schemas for `resume_rewriter_agent` and `jd_analyzer_agent` to guarantee the subsequent Python nodes receive strictly typed JSON.
- [ ] **Step 2: Convert `ATSPreCheck` to `PythonTaskNode`.** Replace the LLM in `sub_agents/ats_precheck/agent.py` with an instance of `PythonTaskNode` wrapping formatting detection and baseline ATS scoring logic.
- [ ] **Step 3: Convert `ATSScorer` to `PythonTaskNode`.** Replace the LLM in `sub_agents/ats_scorer/agent.py` with `PythonTaskNode` calling the post-rewrite ATS score logic.
- [ ] **Step 4: Convert `HTMLRenderer` to `PythonTaskNode`.** Replace the LLM in `sub_agents/html_renderer/agent.py` with `PythonTaskNode` running Jinja2 directly against the rewritten resume JSON in state.
- [ ] **Step 5: Convert `ReportGenerator` to `PythonTaskNode`.** Replacing the LLM wrapper purely used for Markdown compilation. Formatting a report from structured state is a deterministic task; use string interpolation instead of wasting tokens.
- [ ] **Step 6: Update Critic Agent Logic.** Modify `critic_agent` in `sub_agents/critic/agent.py`. Remove the "hard gate" logic. Pass critical warnings into `state` directly instead of halting execution.
- [ ] **Step 7: Apply Unrelated Experience Safeguard.** Update `resume_rewriter_agent` prompt to prevent technical keywords from bleeding into non-technical past roles (e.g., retail, food service).
- [ ] **Step 8: Upgrade JD Analyzer Keyword Extraction.** Remove regex-based keyword extraction tools. Update `jd_analyzer_agent` prompt to extract keywords natively via LLM.

## Validation/Testing

- **Token Profile Test:** Verify the pipeline completes end-to-end, skipping LLM calls entirely at steps 4, 6, 8, and 9 (4 total LLM cycles eliminated).
- **Graceful Error Mock Test:** Inject a deliberate `KeyError` into the Jinja2 HTML mapping. Verify that `PythonTaskNode` catches the error, sets `pipeline_halted=True`, and the report gracefully logs the failure without raising a runtime stack trace to the user.
- **Barista Edge Case Test:** Submit a resume consisting entirely of "Retail Barista" experience against a Senior Software Engineer JD. Run assertions to verify that 0 technical cloud keywords were injected into the Barista experience bullets.

## Open Questions (RESOLVED)

- **Architecture Decision:** We will use a `Deterministic Custom Agent` pattern. We will implement `PythonTaskNode(BaseAgent)` to run Python efficiently in standard ADK flows without the token cost of `LlmAgent` wrappers. We will rely on tight JSON contracts from preceding LLMs to avoid brittle handoffs.
