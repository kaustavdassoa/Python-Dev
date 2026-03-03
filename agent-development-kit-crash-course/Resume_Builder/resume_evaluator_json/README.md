# Resume Evaluator — JSON Output Agent

A Google ADK (Agent Development Kit) agent that evaluates a candidate's resume against a Job Description and returns a **structured JSON** evaluation with match scoring, gap analysis, candidate details, and recruiter recommendations.

Designed to be called by an **orchestrator agent** that passes a PDF resume file path, but also works standalone via `adk web`.

---

## 📁 Package Structure

```
resume_evaluator_json/
├── __init__.py        # Package exports (root_agent alias)
├── agent.py           # Agent definition + Pydantic output schema
├── config.py          # Model configuration (gemini-2.5-flash)
├── tools.py           # extract_resume_from_pdf + retrieve_master_experience
├── test_data.py       # 3 fictitious candidate profiles for testing
├── run_tests.py       # Automated test runner
├── requirements.txt   # Dependencies
└── .env               # GOOGLE_API_KEY (not committed)
```

---

## 🚀 Setup

### 1. Install dependencies

```powershell
pip install -r resume_evaluator_json/requirements.txt
```

### 2. Set your API key

Create or edit `resume_evaluator_json/.env`:

```
GOOGLE_API_KEY=your-google-api-key-here
```

---

## 🧪 Testing

### Option A — Interactive testing with `adk web`

```powershell
cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\Resume_Builder
adk web resume_evaluator_json
```

Then in the chat UI, type a prompt like:

> **With a PDF resume:**
> ```
> Evaluate the resume at e:\path\to\resume.pdf against this JD:
> - 10+ years Java experience
> - Full stack: Java, Spring, Hibernate, ReactJS
> - Cloud-native experience (AWS, Kubernetes)
> ...
> ```

> **Without a PDF (uses fallback data):**
> ```
> Use the candidate's master experience. Evaluate against this JD:
> - 10+ years Java experience
> ...
> ```

> ⚠️ **Important:** Provide the PDF as a **file path in the message text** (don't use the upload button). The agent calls `extract_resume_from_pdf` with the path.

---

### Option B — Automated testing with `run_tests.py`

```powershell
cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\Resume_Builder
python -m resume_evaluator_json.run_tests
```

This runs the agent against **3 test candidate profiles** from `test_data.py`:

| Candidate | Expected Score | Covers |
|---|---|---|
| **Priya Sharma** (Strong Fit) | 85-95% | Java/React/Cloud/AI/BigData/Leadership |
| **Ryan Mitchell** (Moderate Fit) | 60-75% | Java backend only, 6yr, no React/AI/BigData |
| **Emily Chen** (Weak Fit) | <60% | Frontend only, 3yr, no Java/Cloud/leadership |

Results are saved to `data/test_results/`:
- `result_strong_fit.json`
- `result_moderate_fit.json`
- `result_weak_fit.json`

Each result is validated as well-formed JSON ✓.

---

## 🏗️ How the Agent Works — Deep Dive

### Agent Definition

```python
resume_evaluator_json_agent = Agent(
    name="resume_evaluator_json",
    model=config.model,
    description="...",
    instruction=INSTRUCTION,
    tools=[
        FunctionTool(extract_resume_from_pdf),
        FunctionTool(retrieve_master_experience),
    ],
    output_key="evaluation",
    output_schema=ResumeEvaluation,
)
```

Here's what each parameter does and why it matters:

---

### `name="resume_evaluator_json"`

The unique identifier for this agent within an ADK application. When used as a sub-agent, the orchestrator references it by this name to delegate tasks.

---

### `model=config.model`

The LLM that powers the agent. Set in `config.py` as `gemini-2.5-flash`. This model:
- Supports **structured output** (required for `output_schema`)
- Has a large context window for processing full resumes + JDs
- Supports **tool calling** for `extract_resume_from_pdf`

---

### `instruction=INSTRUCTION`

The system prompt that defines the agent's behavior. It contains:

1. **Role definition** — "You are ResumeEvaluator, an expert talent assessment system"
2. **Matching rules** — Strict criteria for STRONG MATCH vs PARTIAL MATCH vs GAP
3. **Workflow steps** — How to extract candidate data, parse the JD, classify requirements, and calculate scores
4. **Scoring formula** — `Score = (points earned / max points) × 100`

The instruction does **not** include an output format template because `output_schema` handles that.

---

### `tools=[...]`

Two tools are registered, giving the LLM the ability to call external functions:

#### `extract_resume_from_pdf(file_path: str) → dict`

```
Orchestrator passes file_path → Agent calls this tool → PyPDF2 reads PDF → Returns text
```

- Takes an absolute file path to a PDF
- Uses PyPDF2 to extract text from every page
- Returns `{"status": "success", "resume_text": "..."}` or an error dict
- **This is the primary path** when called by the orchestrator

#### `retrieve_master_experience() → dict`

- Takes no arguments — returns a hardcoded fictitious candidate profile
- Acts as a **fallback** when no PDF is provided
- Contains comprehensive test data covering all JD scenarios
- Useful for testing without needing an actual PDF file

**How tool calling works:**

```
User message arrives
        │
        ▼
   Gemini reads the instruction + user message
        │
        ▼
   Gemini decides which tool to call based on context:
     • file_path mentioned? → calls extract_resume_from_pdf
     • no file?            → calls retrieve_master_experience
        │
        ▼
   ADK executes the tool function on the server
        │
        ▼
   Tool result is sent back to Gemini
        │
        ▼
   Gemini generates the structured JSON evaluation
```

---

### `output_key="evaluation"`

Stores the agent's final response into the **session state**:

```python
state["evaluation"] = "<JSON output>"
```

**Why this matters for the orchestrator:**

```
┌──────────────┐                          ┌────────────────────────┐
│  Orchestrator │  ── delegates to ──────▶ │  resume_evaluator_json │
│              │                          │                        │
│              │  ◀── reads result ──────  │  output_key="eval…"    │
│              │     state["evaluation"]   │                        │
└──────────────┘                          └────────────────────────┘
```

Without `output_key`, the orchestrator would need to parse conversation history to find the result. With it, the result is cleanly accessible at `state["evaluation"]`.

---

### `output_schema=ResumeEvaluation`

This is the key to **guaranteed well-formed JSON**. It passes a Pydantic model to Gemini's structured output mode.

#### What happens under the hood:

1. ADK converts `ResumeEvaluation` (Pydantic model) → JSON Schema
2. The JSON schema is sent to Gemini as a **response constraint**
3. Gemini generates output **token by token**, constrained to produce valid JSON matching the schema
4. Every field, type, and nested structure is enforced at generation time

#### The Pydantic model hierarchy:

```
ResumeEvaluation
├── candidate_name: str
├── candidate_title: str
├── total_years_of_experience: int
├── skills: list[str]
├── past_experiences: list[PastExperience]
│   ├── company: str
│   ├── role: str
│   ├── duration: str
│   └── key_accomplishments: list[str]
├── education: Education
│   ├── degree: str
│   ├── university: str
│   └── graduation_year: str
├── certifications: list[str]
├── overall_match_score: int
├── fit_category: str
├── required_matched: str
├── nice_to_have_matched: str
├── score_calculation: str
├── strong_matches: list[StrongMatch]
│   ├── requirement: str
│   └── evidence: list[str]     ← list, not string!
├── partial_matches: list[PartialMatch]
│   ├── requirement: str
│   ├── candidate_has: str
│   └── whats_missing: str
├── gaps: list[Gap]
│   ├── requirement: str
│   └── notes: str
├── key_highlights: list[str]
└── recruiter_recommendation: str
```

#### Why `evidence: list[str]` matters:

Without schema enforcement, the LLM sometimes produces invalid JSON like:

```json
"evidence": "Led team", "Manager Leadership", "Established CoE"
```

With `output_schema`, the `evidence` field is typed as `list[str]`, so Gemini is **forced** to output:

```json
"evidence": ["Led team", "Manager Leadership", "Established CoE"]
```

---

### How `output_key` and `output_schema` work together

| Parameter | What it does |
|---|---|
| `output_schema` | **Format guarantee** — Ensures the output is valid JSON matching the Pydantic model |
| `output_key` | **State storage** — Saves the validated JSON into `state["evaluation"]` for the orchestrator |

Together they form a contract: *"This agent will always produce well-formed JSON at a predictable location."*

---

## 🔗 Orchestrator Integration

To call this agent from an orchestrator:

```python
from google.adk.agents import Agent
from resume_evaluator_json.agent import resume_evaluator_json_agent

orchestrator = Agent(
    name="hiring_pipeline",
    model="gemini-2.5-flash",
    sub_agents=[resume_evaluator_json_agent],
    instruction="""
    When asked to evaluate a candidate:
    1. Delegate to resume_evaluator_json with the PDF path and JD.
    2. Read the result from state["evaluation"].
    3. Use the evaluation to make hiring recommendations.
    """,
)
```

The orchestrator passes a message like:

> "Evaluate the resume at /path/to/resume.pdf against this JD: ..."

The sub-agent processes it, and the result is available in `state["evaluation"]` as structured JSON.

---

## 📋 Sample Output

```json
{
  "candidate_name": "Arjun Mehta",
  "candidate_title": "Lead Software Engineer",
  "total_years_of_experience": 18,
  "skills": ["Java", "Spring Boot", "ReactJS", "Kubernetes", "..."],
  "past_experiences": [
    {
      "company": "Pinnacle Financial Services",
      "role": "Lead Software Engineer",
      "duration": "2020 - Present",
      "key_accomplishments": ["Led 22-engineer team...", "..."]
    }
  ],
  "education": {
    "degree": "B.E. in Electronics Engineering",
    "university": "Vishwakarma Institute of Technology, Pune",
    "graduation_year": "2004"
  },
  "certifications": ["Certified Kubernetes Application Developer"],
  "overall_match_score": 88,
  "fit_category": "Strong Fit",
  "required_matched": "10 of 11",
  "nice_to_have_matched": "0 of 0",
  "score_calculation": "(10×1.0 + 1×0.5) / 11 × 100 = 95.5%",
  "strong_matches": [
    {
      "requirement": "10+ years Java experience",
      "evidence": [
        "18+ years in software engineering",
        "Java listed as primary language"
      ]
    }
  ],
  "partial_matches": [
    {
      "requirement": "Full stack with ReactJS",
      "candidate_has": "Java, Spring Boot, Hibernate",
      "whats_missing": "ReactJS not explicitly demonstrated"
    }
  ],
  "gaps": [],
  "key_highlights": ["18+ years experience...", "..."],
  "recruiter_recommendation": "Strong candidate. Probe ReactJS depth..."
}
```
