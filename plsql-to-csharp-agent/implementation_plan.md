# Phase 1: Context & Architecture Mapping — plsql-to-csharp-agent

## 🔍 Audit Context (Ultra-Granular Line-by-Line Analysis)

### Repository-Wide Orientation

| Attribute | Value |
|-----------|-------|
| Total Python files | 6 (agent.py, __init__.py, 4× agent modules) |
| Prompt files | 4 (parser, analyzer, converter, validator) |
| Framework | Google ADK (`google-adk >= 0.1.0`) |
| LLM Backend | Gemini 2.5 Flash Lite (per all 4 specialist agents) |
| Env management | `python-dotenv` via `.env` |
| Entry point | `adk web` → discovers `plsql_converter.root_agent` |
| Runtime mode | Stateless, single-turn, human-in-loop via browser chat |

---

### Per-File Deep Analysis

#### `plsql_converter/__init__.py` (2 lines)
```python
from plsql_converter.agent import root_agent
```
- **Purpose**: Re-exports `root_agent` at the package surface. Google ADK's `adk web` CLI discovers the agent by importing `<package>.root_agent`.  
- **Key Invariant**: This is the **sole public interface** the ADK runtime touches. All sub-agents are wired through `agent.py` before this export.  
- **Assumption**: The package is named `plsql_converter` and must be importable from the working directory where `adk web` is launched.

#### `plsql_converter/agent.py` (20 lines)
```python
root_agent = SequentialAgent(
    name="plsql_to_csharp_orchestrator",
    sub_agents=[parser_agent, analyzer_agent, converter_agent, validator_agent],
)
```
- **Purpose**: Defines the pipeline DAG as a `SequentialAgent` — a first-class ADK primitive that chains sub-agents and passes the shared session state (via `output_key` slots) through each stage.  
- **Ordering invariant**: The list order `[parser → analyzer → converter → validator]` is **significant** — ADK executes them strictly in sequence. Swapping any two would break the data contract.  
- **5 Whys — Why SequentialAgent?**  
  1. Each stage depends on the output of the prior stage.  
  2. Parallelism would require all agents to share identical inputs, which they don't.  
  3. `SequentialAgent` is ADK's primitive for ordered pipelines with implicit state threading.  
  4. No custom orchestration code is required — ADK handles step management.  
  5. Session state (`output_key` slots) acts as the inter-agent communication channel, persisted automatically.

#### `plsql_converter/agents/parser_agent.py` (20 lines)
- **Pattern**: Prompt loaded at module import time via `os.path.join(__file__, "..", "prompts", "parser_prompt.txt")`.
- **Output key**: `parsed_plsql` — written to ADK session state.  
- **Model**: `gemini-2.5-flash-lite` — chosen for speed/cost at extraction tasks.
- **Input expectation**: Raw user message (PL/SQL text from the chat).
- **Prompt contract** (`parser_prompt.txt`):  
  - Extracts: `PROCEDURE_NAME`, `PARAMETERS` (name|direction|type), `LOCAL_VARIABLES`, `BODY`.  
  - Output delimited by `---PARSED OUTPUT---` / `---END PARSED OUTPUT---`.  
  - Strict instruction: **Do NOT interpret or convert logic** — pure extraction only.  
  - Error signal: `ERROR: Invalid or missing PL/SQL stored procedure input.`

#### `plsql_converter/agents/analyzer_agent.py` (21 lines)
- **Input**: Reads the session state which now includes `parsed_plsql`.
- **Output key**: `analyzed_plsql`.
- **Prompt contract** (`analyzer_prompt.txt`):  
  - Identifies 4 categories: `SQL_STATEMENTS`, `CONTROL_FLOW`, `EXCEPTION_HANDLING`, `UNSUPPORTED_CONSTRUCTS`.  
  - SQL annotation: type (SELECT/INSERT/UPDATE/DELETE) + whether it uses INTO pattern.  
  - Flags MVP0 non-support: cursors, `EXECUTE IMMEDIATE`, `BULK COLLECT / FORALL`.  
  - Output delimited by `---ANALYZED OUTPUT---` / `---END ANALYZED OUTPUT---`.  
- **5 Whys — Why a separate Analyzer stage?**  
  1. The Converter needs structured knowledge of *what* constructs exist before mapping them.  
  2. Separation prevents prompt complexity explosion in a single "parse + analyze + convert" mega-prompt.  
  3. The analysis output can be reused independently (e.g., for future linting or flagging reports).  
  4. A dedicated stage means the LLM token budget for analysis isn't competing with conversion logic.  
  5. Enables stage-level unit testability in isolation.

#### `plsql_converter/agents/converter_agent.py` (20 lines)
- **Input**: Session state contains both `parsed_plsql` and `analyzed_plsql`.
- **Output key**: `csharp_code`.
- **Prompt contract** (`converter_prompt.txt`):  
  - Contains a **10-row Oracle → C# type mapping table** (NUMBER, VARCHAR2, CHAR, DATE, TIMESTAMP, BOOLEAN, CLOB, BLOB, NUMBER(n,0), parameter directions).  
  - 7 numbered conversion rules covering: method signature casing (PascalCase method, camelCase params), SQL-as-string-variables, control flow mapping, exception mapping, `:=` → `=`, null checks, and TODO-as-unsupported-marker.  
  - Output: **Method body ONLY** — no class, no namespace, no using statements.  
  - Includes a concrete csharp example output block in the prompt itself to anchor the model's output format.

#### `plsql_converter/agents/validator_agent.py` (20 lines)
- **Input**: Session state includes `csharp_code` (the converter's output).
- **Output key**: `validated_csharp` — final output presented to user.
- **Prompt contract** (`validator_prompt.txt`):  
  - 3 structural checks:  
    1. **Method Signature Check** — starts with `public void/int/...`, valid C# param types.  
    2. **Brace Balance Check** — counts `{` vs. `}`.  
    3. **PL/SQL Leak Check** — scans for `:=`, standalone `BEGIN`/`END;`, `DECLARE`, `DBMS_OUTPUT`, `v_` prefix patterns.  
  - Returns `✅ VALIDATION PASSED` or `⚠️ VALIDATION WARNINGS` with issue list.  
  - Critical design decision: **Always returns body + status** — never withholds code even if warnings found (developer-friendly degraded output).

---

### Global System Invariants

1. **State threading**: Each agent writes exactly ONE `output_key`. The ADK `SequentialAgent` accumulates all keys in session state throughout the pipeline run. Later agents have access to ALL prior outputs.  
2. **Prompt isolation**: Prompts live in `.txt` files, loaded at import time. Changes to prompts take effect on next process restart — no hot-reload.  
3. **No tools**: All four `LlmAgent` instances are pure text-in / text-out. No function-calling tools are defined. The agents operate entirely on LLM inference over structured text.  
4. **Model uniformity**: All agents use `gemini-2.5-flash-lite`. This is deliberate — consistency in capability and cost profile across stages.  
5. **Output is delimited text, not structured JSON**: Each agent's output is a delimited text block (e.g., `---PARSED OUTPUT---`). Downstream agents read this as part of the context window, not as parsed objects. This is a design trade-off: simpler but susceptible to formatting drift.

---

## 🏛️ C4 System Context

### System Overview

**Short description**: An AI-powered pipeline that converts Oracle PL/SQL stored procedures into compilable C# method bodies via a 4-stage LLM agentic pipeline.

**Long description**: `plsql-to-csharp-agent` addresses the common enterprise problem of migrating Oracle database logic to .NET applications. It eliminates hours of manual translation work by automating the structural and semantic conversion of PL/SQL procedures — including type mapping, control flow translation, exception handling, and SQL preservation — using Google ADK's multi-agent framework backed by Gemini Flash.

### Personas

| Persona | Type | Goal |
|---------|------|------|
| **Database Developer** | Human User | Paste a PL/SQL procedure; receive compilable C# to integrate |
| **Backend Engineer (.NET)** | Human User | Receive idiomatic C# method bodies without knowing PL/SQL syntax |
| **DevOps / CI Pipeline** | *(Planned MVP3)* | Batch-process multiple `.sql` files via CLI |

### External Systems & Dependencies

| System | Type | Purpose |
|--------|------|---------|
| **Google ADK** | Framework / Library | Agent orchestration, `SequentialAgent`, `LlmAgent` primitives, `adk web` server |
| **Gemini API** (via ADK) | LLM API | PL/SQL parsing, analysis, conversion, and validation inference |
| **Browser (User)** | UI Client | `adk web` serves a chat UI at `localhost:8000` |
| **`.env` / OS env** | Config | Supplies `GOOGLE_API_KEY` to authenticate with Gemini |

### C4 Context Diagram

```mermaid
C4Context
    title System Context: PL/SQL → C# Agent

    Person(dev, "Developer", "Database or .NET developer with a PL/SQL stored procedure to migrate")

    System(sys, "plsql-to-csharp-agent", "4-stage AI pipeline that parses, analyzes, converts, and validates PL/SQL → C# method body")

    System_Ext(adk, "Google ADK", "Multi-agent orchestration framework: SequentialAgent, LlmAgent, adk web UI server")
    System_Ext(gemini, "Google Gemini API", "LLM inference engine (gemini-2.5-flash-lite) powering each pipeline stage")
    System_Ext(browser, "Web Browser", "Developer's browser accessing the ADK chat UI on localhost:8000")

    Rel(dev, browser, "Pastes PL/SQL, receives C#")
    Rel(browser, sys, "HTTP / WebSocket", "adk web")
    Rel(sys, adk, "Built on / Uses primitives")
    Rel(sys, gemini, "LLM API calls (4× per conversion)")
    Rel(adk, gemini, "Routes inference requests")
```

---

## 🏗️ Architecture: Component-Level Data Flow

```
User Input (PL/SQL text)
        │
        ▼
┌─────────────────────────────────────────────────┐
│         SequentialAgent Orchestrator             │
│         (plsql_to_csharp_orchestrator)           │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ [1] parser_agent (LlmAgent)              │   │
│  │     model: gemini-2.5-flash-lite         │   │
│  │     prompt: parser_prompt.txt            │   │
│  │     output_key: "parsed_plsql"           │   │
│  │     → PROCEDURE_NAME, PARAMETERS, BODY  │   │
│  └──────────────┬───────────────────────────┘   │
│                 │ (session state)                │
│  ┌──────────────▼───────────────────────────┐   │
│  │ [2] analyzer_agent (LlmAgent)            │   │
│  │     model: gemini-2.5-flash-lite         │   │
│  │     prompt: analyzer_prompt.txt          │   │
│  │     output_key: "analyzed_plsql"         │   │
│  │     → SQL_STATEMENTS, CONTROL_FLOW,     │   │
│  │       EXCEPTION_HANDLING, UNSUPPORTED   │   │
│  └──────────────┬───────────────────────────┘   │
│                 │ (session state, 2 keys now)    │
│  ┌──────────────▼───────────────────────────┐   │
│  │ [3] converter_agent (LlmAgent)           │   │
│  │     model: gemini-2.5-flash-lite         │   │
│  │     prompt: converter_prompt.txt         │   │
│  │     output_key: "csharp_code"            │   │
│  │     → C# method body (no class/NS)      │   │
│  └──────────────┬───────────────────────────┘   │
│                 │ (session state, 3 keys now)    │
│  ┌──────────────▼───────────────────────────┐   │
│  │ [4] validator_agent (LlmAgent)           │   │
│  │     model: gemini-2.5-flash-lite         │   │
│  │     prompt: validator_prompt.txt         │   │
│  │     output_key: "validated_csharp"       │   │
│  │     → ✅ PASSED / ⚠️ WARNINGS + code    │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
        │
        ▼
  Final C# method body displayed in ADK Web chat
```

---

## 📋 Documentation Plan (concise-planning output)

**Approach**: Build a structured `docs/` folder with 6 files covering architecture, each agent module, the API/prompt reference, and a comprehensive README. Documentation will be grounded strictly in evidence from the source.

**Scope**:
- **In**: Architecture doc, 4 agent wiki pages, prompt engineering reference, full README.md
- **Out**: Tutorial videos, contributor guide, deployment configs, class/namespace generation

---

### Documentation Files to Create

- `[ ]` **`docs/architecture.md`** — Full system architecture: C4 context + component diagrams, data flow, design decisions, ADK SequentialAgent pattern, session-state threading model
- `[ ]` **`docs/agents/parser-agent.md`** — Deep wiki page: purpose, prompt contract, input/output schema, edge cases, `parsed_plsql` output key
- `[ ]` **`docs/agents/analyzer-agent.md`** — Deep wiki page: annotation categories, MVP0 unsupported constructs, `analyzed_plsql` output key
- `[ ]` **`docs/agents/converter-agent.md`** — Deep wiki page: all 7 conversion rules, Oracle→C# type table, `csharp_code` output key
- `[ ]` **`docs/agents/validator-agent.md`** — Deep wiki page: 3-check validation logic, PASSED/WARNINGS protocol, graceful degradation design
- `[ ]` **`docs/prompt-engineering-reference.md`** — API/prompt reference: all 4 prompt contracts, delimiter schemas, error signals, inter-agent data threading
- `[ ]` **`README.md`** — Absurdly thorough front-page: badges, quickstart, architecture overview, type mapping table, examples, roadmap, troubleshooting

### Open Questions

- None blocking — enough evidence to proceed.
