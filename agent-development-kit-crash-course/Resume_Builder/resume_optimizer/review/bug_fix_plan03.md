# Fix Resume Text Truncation in Pipeline

## Root Cause Analysis

After tracing the full data flow through the logs and source code, I've identified **3 distinct bugs** causing the output resume to be incomplete:

---

### Bug 1: ResumeRewriterAgent receives empty `contact`, `experience`, `education`, `certifications` from DocumentParser

**Evidence from logs:**
- `document_parser_output` = 17,960 chars (the LLM's text output as a markdown-wrapped JSON string)
- `resume_rewriter_output` = only 1,714 chars total; the `rewritten_resume.contact` is `{}` (empty)
- The output file is named `UNKNOWN_resume.html` — proving `contact.name` was empty

**Root Cause:**
The `DocumentParserAgent` is an **LLM agent** that uses `output_key="document_parser_output"`. ADK stores the LLM's raw text response in that key — which is the JSON wrapped in a markdown code fence (`` ```json {...}``` ``).

The `ResumeRewriterAgent.run_resume_rewriter()` (line 105) correctly parses this via `get_dict()`. BUT look at what happens:

```python
orig_resume = doc_out.get("resume_sections", {})  # line 109
orig_exp = orig_resume.get("experience", [])       # line 110
```

This works correctly — IF the LLM's JSON includes all sections. The issue is that the **LLM correctly parses the resume into structured JSON** (17,960 chars with all 8 experience entries), **BUT** the `run_resume_rewriter` function only rewrites `summary` and `skills` via the LLM. Contact, education, and certifications are passed through from `orig_resume`:

```python
out_resume = {
    "contact": orig_resume.get("contact", {}),    # line 208
    ...
    "education": orig_resume.get("education", []),  # line 211
    "certifications": orig_resume.get("certifications", []),  # line 212
    "experience": rewritten_experiences  # line 213
}
```

So these DO get preserved. The truncation in the **output HTML** then must come from the HTML renderer seeing empty data.

### Bug 2: HTML template gets empty `contact` dict with empty string values

**Evidence from output HTML (line 234):**
```html
<!-- ── Contact Header ──────────────────── -->

```
The contact section is completely empty. The Jinja2 template checks `{% if contact %}` — but `contact` is `{"name": "", "email": "", "phone": "", "location": "", "linkedin": ""}` — a dict with empty string values. In Jinja2, a **non-empty dict is truthy** even if all values are empty strings. So the `if contact` check should pass... 

BUT looking at the actual HTML output more carefully — the contact section is present but ALL the inner `{% if contact.name %}` etc. fail because all values are empty strings. **This means the rewriter's `orig_resume.get("contact", {})` returned a dict with empty values.**

> [!IMPORTANT]
> **The real problem**: The ResumeRewriterAgent has `"contact": orig_resume.get("contact", {})` which correctly passes through the contact. BUT the DocumentParser LLM output's `resume_sections.contact` is being parsed fine (17,960 chars includes the contact). The issue is that **`get_dict()` is failing to parse the full JSON**, or the parsed dict doesn't have `resume_sections.contact` populated. 
> 
> Looking more carefully at the `get_dict()` regex: `r'```(?:json)?\s*(\{.*?\})\s*```'` — the `.*?` is **non-greedy** and uses `re.DOTALL`. For a 17,960-char JSON string, this will match the **first `}`** it finds, NOT the outermost closing brace. This causes it to extract only a partial JSON object!

### Bug 3: `get_dict()` regex extracts PARTIAL JSON — `\{.*?\}` is non-greedy

This is the **primary root cause**. The regex pattern:

```python
match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', val, re.DOTALL)
```

The `\{.*?\}` uses a **non-greedy quantifier** (`*?`), which means it matches the shortest possible string between `{` and `}`. For a deeply nested JSON like:

```json
{"completeness_status": "pass", "resume_sections": {"contact": {"name": "KAUSTAV DAS"}}}
```

The non-greedy match stops at the FIRST `}` it encounters, producing:

```json
{"completeness_status": "pass", "resume_sections": {"contact": {"name": "KAUSTAV DAS"}
```

Which is **invalid JSON**, causing `json.loads()` to fail. Then it falls through to Strategy 2 (brace matching), which correctly uses `val.find('{')` and `val.rfind('}')` — and this SHOULD work. But the regex in Strategy 1 isn't actually failing because the non-greedy `.*?` matches `{...first-close-brace}` which may accidentally be valid JSON if the first `}` happens to close a simple value like `{"completeness_status": "pass"}`.

Actually wait — `\{.*?\}` with `re.DOTALL` and non-greedy will match `{ + minimum-chars + }`, which for `{"completeness_status": "pass", ...}` would match from the opening `{` to the first `}` inside `"pass"}`. This IS actually valid JSON: `{"completeness_status": "pass"}` — a complete JSON object with just one field!

**This is exactly the bug**: Strategy 1 extracts `{"completeness_status": "pass"}` (or similar minimal match), which is valid JSON, so `json.loads()` succeeds — but returns a dict with only `completeness_status`, missing `resume_sections`, `experience_entry_count`, etc.

The same `get_dict()` bug exists in the rewriter, the ATS precheck agent, and the HTML renderer — ALL of them have the same non-greedy regex.

> [!CAUTION]
> This regex pattern is duplicated in **4 files** — any fix must update all of them.

---

### Bug 2b: Experience & Education sections empty in output HTML

**Evidence from output HTML (lines 294–301):**
```html
<!-- ── Professional Experience ──────────── -->

<!-- ── Education ────────────────────────── -->
```

Both are completely empty. The Jinja2 template checks `{% if experience %}` and `{% if education %}` — both are empty lists. This confirms that the `rewritten_resume` dict passed to the template has `experience: []` and `education: []`.

This is directly caused by Bug 3: the parser's output was truncated by `get_dict()`, so `orig_resume.get("experience", [])` returned `[]`.

---

## Proposed Changes

### Fix: Replace non-greedy `\{.*?\}` with greedy brace-matching in `get_dict()` / `get_dict_from_state()`

The regex-based approach is fundamentally flawed for nested JSON. Replace with a **greedy match** or better yet, use a **brace-depth-counting approach**.

The fix: Change the regex from `\{.*?\}` (non-greedy) to `\{.*\}` (greedy) in the markdown extraction pattern. The greedy version will match from the first `{` to the LAST `}` in the code block, which is the correct behavior for nested JSON.

#### [MODIFY] [agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizer/sub_agents/resume_rewriter/agent.py)

Fix the non-greedy regex in `get_dict()`:
```diff
-match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', val, re.DOTALL)
+match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', val, re.DOTALL)
```

---

#### [MODIFY] [agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizer/sub_agents/ats_precheck/agent.py)

Same fix in `get_dict_from_state()`.

---

#### [MODIFY] [agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizer/sub_agents/html_renderer/agent.py)

Same fix in `get_dict_from_state()`.

---

#### [MODIFY] [agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizer/sub_agents/ats_scorer/agent.py)

Same fix in `get_dict_from_state()` (if present).

---

#### [MODIFY] [agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizer/sub_agents/critic/agent.py)

Same fix in `get_dict_from_state()` (if present).

---

## Verification Plan

### Automated Tests
1. Re-run the pipeline via `positive_test_scenario_api.py`
2. Verify the output HTML contains:
   - Contact header with the candidate's name (not "UNKNOWN")
   - All 8 experience entries
   - Education section populated
   - Certifications section populated (if present in source)
3. Verify critic output no longer says "discarded 90% of professional history"

### Manual Verification
- Open the output HTML in a browser and visually confirm all sections are rendered
