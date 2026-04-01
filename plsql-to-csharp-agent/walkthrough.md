# PL/SQL → C# Agentic Tool — Walkthrough

## What Was Built

A greenfield **Google ADK multi-agent tool** that converts PL/SQL stored procedures into compilable C# method bodies via an `adk web` chat interface.

---

## Project Location

`E:\GitHub\Python-Dev\plsql-to-csharp-agent\`

## Files Created (13 total)

| File | Purpose |
|------|---------|
| `requirements.txt` | `google-adk`, `python-dotenv` |
| `.env.example` | API key template |
| `README.md` | Setup, usage, type mapping, roadmap |
| `plsql_converter/agent.py` | `root_agent` — `SequentialAgent` orchestrator |
| `agents/parser_agent.py` | Extracts procedure name, params, body |
| `agents/analyzer_agent.py` | Annotates SQL, control flow, exceptions |
| `agents/converter_agent.py` | Generates C# method body |
| `agents/validator_agent.py` | Checks braces, signature, PL/SQL leaks |
| `prompts/parser_prompt.txt` | Parser LLM instructions |
| `prompts/analyzer_prompt.txt` | Analyzer LLM instructions |
| `prompts/converter_prompt.txt` | Converter rules + type mapping table |
| `prompts/validator_prompt.txt` | Validator checklist |
| `plsql_converter/__init__.py` + `agents/__init__.py` | Package markers |

---

## Agent Pipeline

```
User → Orchestrator → Parser → Analyzer → Converter → Validator → C# Output
```

Each agent uses **Gemini 2.0 Flash** and writes its result to a named `output_key` that flows into the next agent's context.

---

## How to Run

```bash
# 1. Copy and configure .env
cp .env.example .env   # add your GOOGLE_API_KEY

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start ADK Web
cd E:\GitHub\Python-Dev\plsql-to-csharp-agent
adk web

# 4. Open browser → http://localhost:8000
# 5. Paste PL/SQL stored procedure → receive C# method body
```

---

## MVP0 Decisions

| Decision | Choice |
|----------|--------|
| PL/SQL scope | Stored Procedures only |
| Output | Method body (no class/namespace wrapper) |
| SQL handling | Raw `string sql = "..."` variables |
| LINQ | ❌ Not in MVP0 |
| Validation | Lightweight (no compiler) |
