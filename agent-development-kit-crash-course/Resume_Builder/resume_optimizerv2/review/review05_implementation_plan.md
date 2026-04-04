# FinOps Token Optimization — Implementation Plan

Comprehensive refactoring of the `resume_optimizerv2` pipeline to reduce token consumption by ~60-70%, based on the FinOps Token Audit Report.

---

## PART 1: Code Hygiene & Prompt Separation

### 1.1 Centralize `get_dict_from_state()` Utility

> [!IMPORTANT]
> The `get_dict_from_state()` function is duplicated in 5 different agent files with minor variations. The version in `report_generator` is notably weaker (uses non-greedy regex, misses brace-matching fallback).

#### [NEW] [utils.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv2/shared/utils.py)
- Create canonical `get_dict_from_state()` with all 3 extraction strategies (markdown block → brace matching → raw parse)
- Include logging for debug traceability

#### [MODIFY] Agents that currently define `get_dict_from_state` locally:
| Agent | Current Status |
|---|---|
| [ats_precheck/agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv2/sub_agents/ats_precheck/agent.py) | Lines 12-38 — full duplicate |
| [ats_scorer/agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv2/sub_agents/ats_scorer/agent.py) | Lines 12-38 — full duplicate |
| [html_renderer/agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv2/sub_agents/html_renderer/agent.py) | Lines 12-38 — full duplicate |
| [report_generator/agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv2/sub_agents/report_generator/agent.py) | Lines 11-25 — **weaker variant** (non-greedy regex, missing brace fallback) |
| [resume_rewriter/agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv2/sub_agents/resume_rewriter/agent.py) | Lines 63-101 — named `get_dict()`, has extra logging |
| [alignment_gatekeeper/agent.py](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv2/sub_agents/alignment_gatekeeper/agent.py) | Lines 10-20 — inline, different pattern |

**Action:** Remove local definitions, add `from ...shared.utils import get_dict_from_state` to each.

---

### 1.2 Separate Prompts into `prompts.py` Files

For each LLM-based agent, extract the `INSTRUCTION` string into a `prompts.py` file in the same folder.

| Agent Folder | Has INSTRUCTION? | Action |
|---|---|---|
| `document_parser/` | ✅ Lines 14-142 | Extract to `prompts.py` |
| `jd_analyzer/` | ✅ Lines 35-87 | Extract to `prompts.py` |
| `alignment_validator/` | ✅ Lines 16-103 | Extract to `prompts.py` (will be removed in Part 3) |
| `critic/` | ✅ Lines 20-68 | Extract to `prompts.py` |
| `resume_rewriter/` | ❌ Uses inline format strings | Create `prompts.py` with template constants |

> [!NOTE]
> The `ats_precheck`, `ats_scorer`, `html_renderer`, `report_generator`, and `alignment_gatekeeper` are already deterministic `PythonTaskNode` instances — they have no INSTRUCTION strings to extract.

---

## PART 2: Tier 1 Quick Wins (Token Compression)

### 2.1 Remove `raw_text` Echo

**Problem:** The DocumentParser LLM echoes the entire resume text in its `raw_text` output field (~2,000-4,000 tokens wasted). This bloats every downstream LLM agent's conversation history.

**Solution:**
- Remove `"raw_text": "..."` from the DocumentParser prompt's output schema example
- Update `ats_precheck/agent.py` (the only consumer) to read from `state["raw_resume_text"]` instead of `doc_out.get("raw_text")`
- Update `shared/state.py` comments to remove `raw_text` from the schema doc

### 2.2 Compress Prompts

Apply RSCIT framework compression to 3 verbose prompts:

| Prompt | Current Tokens (est.) | Target Reduction |
|---|---|---|
| DocumentParser | ~900 tokens | 40-50% — remove massive JSON example, collapse synonym table |
| JDAnalyzer | ~400 tokens | 30% — tighten steps, remove redundant context lines |
| Critic | ~350 tokens | 30% — compress check descriptions into terse directives |

---

## PART 3: Tier 2 Architectural Wins (Zero-History Nodes)

### 3.1 AlignmentValidator → Deterministic `PythonTaskNode`

**Current:** `LlmAgent` with 2 tools (`compare_seniority_levels`, `check_domain_alignment`). The LLM reads conversation history to extract skills/levels, then calls the tools. This wastes ~10K-20K tokens.

**Proposed:** Convert to `PythonTaskNode`:
1. Read `state["document_parser_output"]` → extract skills list, infer candidate seniority from job titles
2. Read `state["jd_analyzer_output"]` → extract seniority level, required skills
3. Call `compare_seniority_levels()` and `check_domain_alignment()` directly in Python
4. Write verdict to `state["alignment_validator_output"]`
5. If rejected, raise exception (the existing `alignment_gatekeeper` catches this)

> [!IMPORTANT]
> **Seniority inference from job titles** currently relies on the LLM. We'll replicate this deterministically using the existing `SENIORITY_LADDER` dict to scan experience titles for the highest matching level.

**Impact on pipeline:** The `alignment_gatekeeper` node still exists downstream — it reads `alignment_validator_output` and raises `AbortPipelineError` if rejected. This stays unchanged.

---

### 3.2 JDAnalyzer → Hybrid `PythonTaskNode`

**Current:** `LlmAgent` that calls 3 tools, then uses LLM to synthesize job title + skill separation. Sees full conversation history.

**Proposed:** Convert to `PythonTaskNode`:
1. Extract JD text from user message in state (or `state["__user_message"]` — we need to verify how to get it)
2. Call `check_jd_authenticity()`, `extract_seniority_signals()`, `extract_job_metadata()` directly
3. Call `extract_ats_keywords()` (currently unused by the agent despite being defined in tools.py!)
4. Make **one** scoped Gemini API call to extract: `job_title`, `required_skills`, `preferred_skills`, `core_responsibilities`
5. Merge all results → write to `state["jd_analyzer_output"]`

> [!WARNING]
> **JD text source:** The JD text is embedded in the user's message (`[JOB DESCRIPTION]\n...`). For a `PythonTaskNode`, we can't read conversation history. We need to either:
> - **(A)** Have `main.py` also set `state["raw_jd_text"]` alongside `state["raw_resume_text"]` — **this is the cleanest approach**
> - **(B)** Parse it from the user message stored in session events
>
> **Recommendation:** Option (A). Add `"raw_jd_text": job_description` to `initial_state` in `main.py`.

---

### 3.3 Critic → Scoped `PythonTaskNode`

**Current:** `LlmAgent` with 2 tools. Reads entire conversation history (~40K-60K tokens at this pipeline stage) to compare original vs. rewritten resume.

**Proposed:** Convert to `PythonTaskNode`:
1. Read from state only: `document_parser_output`, `resume_rewriter_output`, `jd_analyzer_output`
2. Run `estimate_page_length()` and `detect_keyword_stuffing()` deterministically
3. Make **one** scoped Gemini API call for fabrication detection only:
   - Input: original skills + titles, rewritten skills + titles (extracted from state)
   - Output: structured JSON verdict
4. Merge results → write to `state["critic_output"]`

---

## PART 4: Tier 3 Advanced Optimization

### 4.1 Prefix Caching for ResumeRewriter

**Current:** The rewriter loops over experience entries, sending a new prompt each time. The JD context + rules are repeated in every call.

**Proposed:**
- In `prompts.py`, create a `STATIC_PREFIX` variable containing: JD context block + all rewriting rules
- In the loop, place `STATIC_PREFIX` at the top of every prompt, with the dynamic `experience_entry` appended at the bottom
- This triggers Gemini's automatic prefix caching: after the first call, subsequent calls reuse the cached prefix (~50% cost reduction on experience calls)

**Structure:**
```
STATIC_PREFIX (cached after 1st call)
├── JD Title, Keywords, Missing Keywords
├── All rewriting rules (1-6)
└── [CACHE BOUNDARY]
    
DYNAMIC_SUFFIX (changes per call)
└── Original Experience Entry JSON
```

### 4.2 Deterministic Diff (Eliminate Summary LLM Call)

**Current:** After rewriting, a third LLM call generates `changes_summary` and `keywords_injected` — pure waste since we have both the original and rewritten data in memory.

**Proposed:** Replace with a Python function:
1. Compare original vs. rewritten summary (diff)
2. Compare original vs. rewritten skills (set difference)
3. For each experience entry: compare bullets, detect new keywords
4. Format as structured output matching `RewriterSummarySchema`

**Savings:** Eliminates 1 full LLM API call per pipeline run.

---

## Verification Plan

### Automated Tests
- Run the existing test suite (if any) in `tests/` directory
- Run a full pipeline end-to-end via the FastAPI endpoint using the test scenario script

### Manual Verification
- Verify all state keys are populated correctly after each Part
- Confirm no import errors with `python -c "from resume_optimizerv2.agent import root_agent"`
- Check that deterministic nodes produce identical output to their LLM predecessors for the same input

---

## Execution Order

| Step | Part | Risk | Saves |
|---|---|---|---|
| 1 | Part 1.1: Centralize utils | 🟢 Low | Code quality |
| 2 | Part 1.2: Separate prompts | 🟢 Low | Code quality |
| 3 | Part 2.1: Remove raw_text | 🟢 Low | ~3K-5K tokens |
| 4 | Part 2.2: Compress prompts | 🟢 Low | ~500-800 tokens |
| 5 | Part 3.1: AlignmentValidator → PythonTaskNode | 🟡 Medium | ~10K-20K tokens |
| 6 | Part 3.2: JDAnalyzer → Hybrid PythonTaskNode | 🟡 Medium | ~15K-25K tokens |
| 7 | Part 3.3: Critic → Scoped PythonTaskNode | 🟡 Medium | ~40K-60K tokens |
| 8 | Part 4.1: Prefix caching | 🟢 Low | ~50% on exp calls |
| 9 | Part 4.2: Deterministic diff | 🟢 Low | 1 full LLM call |

## Open Questions

> [!IMPORTANT]
> **Q1: JD Text State Key** — For Part 3.2 (JD Analyzer conversion), I need to add `state["raw_jd_text"]` in `main.py`. This is a minor change to `main.py` line 260-262. Is this acceptable?

> [!IMPORTANT]
> **Q2: Seniority Inference** — For Part 3.1, the AlignmentValidator currently uses the LLM to infer candidate seniority from job titles. My deterministic replacement will scan experience titles against the `SENIORITY_LADDER` dict and pick the highest match. This is less nuanced but covers >90% of cases. Acceptable?

> [!IMPORTANT]
> **Q3: `alignment_gatekeeper` consolidation** — Since we're converting AlignmentValidator to a `PythonTaskNode`, the separate `alignment_gatekeeper` node becomes redundant (the validator can raise the exception directly). Should I merge them into one node, or keep them separate for clarity?
