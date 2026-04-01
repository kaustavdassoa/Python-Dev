# PL/SQL → C# Agent

> An AI-powered multi-agent pipeline that converts Oracle PL/SQL stored procedures into compilable C# method bodies — in seconds, via a browser chat interface.

Built on **Google Agent Development Kit (ADK)** and powered by **Gemini 2.5 Flash Lite**, this tool eliminates hours of manual, error-prone PL/SQL-to-.NET migration work by orchestrating four specialist LLM agents in sequence: **Parse → Analyze → Convert → Validate**.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-0.1.0%2B-4285f4?style=flat-square&logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash%20Lite-8e43e7?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

---

## ⚡ Quick Start

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd plsql-to-csharp-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Gemini API key
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_api_key_here

# 4. Launch the ADK Web interface
adk web

# 5. Open your browser at http://localhost:8000
# Paste any PL/SQL stored procedure and receive C# instantly
```

> **Get a Gemini API key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) — free tier available.

---

## 🎯 What It Does

Paste this PL/SQL into the chat:

```sql
CREATE OR REPLACE PROCEDURE get_employee (
    p_emp_id   IN  NUMBER,
    p_name     OUT VARCHAR2,
    p_salary   OUT NUMBER
) AS
BEGIN
    SELECT emp_name, salary
    INTO p_name, p_salary
    FROM employees
    WHERE emp_id = p_emp_id;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        p_name := 'NOT FOUND';
        p_salary := 0;
END get_employee;
```

Get this C# method body back:

```csharp
public void GetEmployee(decimal pEmpId, out string pName, out decimal pSalary)
{
    try
    {
        string sql = "SELECT emp_name, salary FROM employees WHERE emp_id = :pEmpId";
        // TODO: Execute sql using your data access layer (e.g., Dapper, ADO.NET)
        // The INTO clause maps pName and pSalary to output parameters.
    }
    catch (Exception)
    {
        pName = "NOT FOUND";
        pSalary = 0;
    }
}
```

**Validation result:**
```
✅ VALIDATION PASSED
```

---

## ✨ Key Features

| Feature | Details |
|---------|---------|
| **4-Stage AI Pipeline** | Parse → Analyze → Convert → Validate, each a focused specialist agent |
| **Oracle → C# Type Mapping** | 10 built-in type conversions (NUMBER, VARCHAR2, DATE, BLOB, etc.) |
| **Parameter Direction** | `IN` → regular, `OUT` → `out`, `IN OUT` → `ref` |
| **Control Flow** | IF/ELSIF/ELSE, FOR LOOP, WHILE LOOP, LOOP...EXIT WHEN, CASE |
| **Exception Handling** | PL/SQL `EXCEPTION` block → C# `try/catch` with named exception mapping |
| **SQL Preservation** | All SQL wrapped as raw `string sql = "..."` variables + DAL TODO |
| **Unsupported Flagging** | Cursors, dynamic SQL, BULK COLLECT → `// TODO` comments, never silent |
| **Structural Validation** | Brace balance, method signature check, PL/SQL leak scan |
| **Browser UI** | Zero frontend code — Google ADK provides the chat interface |
| **No Database Required** | Runs entirely on local Python + Gemini API |

---

## 🏗️ Architecture

The system orchestrates four `LlmAgent` instances inside a `SequentialAgent`. Each agent writes its result to a named **session state key**, which is automatically threaded to all downstream agents by the ADK runtime.

```
User Input (PL/SQL)
        │
        ▼
┌─────────────────────────────────────────────┐
│     SequentialAgent Orchestrator            │
│                                             │
│  ① parser_agent    → output: parsed_plsql  │
│         │                                   │
│  ② analyzer_agent  → output: analyzed_plsql│
│         │                                   │
│  ③ converter_agent → output: csharp_code   │
│         │                                   │
│  ④ validator_agent → output: validated_csharp│
└─────────────────────────────────────────────┘
        │
        ▼
  ✅ C# Method Body (displayed in browser)
```

### Agent Responsibilities

| Agent | Stage | What It Does | Session Key Written |
|-------|-------|-------------|---------------------|
| `parser_agent` | 1 | Extracts procedure name, parameters (name/type/direction), local variables, and raw body | `parsed_plsql` |
| `analyzer_agent` | 2 | Annotates SQL statements, control flow, exception blocks; flags MVP0 unsupported constructs | `analyzed_plsql` |
| `converter_agent` | 3 | Renders compilable C# method body using 7 strict conversion rules and the Oracle→C# type table | `csharp_code` |
| `validator_agent` | 4 | Checks method signature, brace balance, and PL/SQL token leaks; outputs `✅ PASSED` or `⚠️ WARNINGS` | `validated_csharp` |

> 📖 **Deep dives**: See the [`docs/`](docs/) folder for per-agent wiki pages and the full architecture document.

---

## 📁 Project Structure

```
plsql-to-csharp-agent/
├── .env                              # Your GOOGLE_API_KEY (not committed)
├── .env.example                      # API key template
├── requirements.txt                  # google-adk, python-dotenv
├── README.md                         # This file
│
├── plsql_converter/                  # Main Python package
│   ├── __init__.py                   # Re-exports root_agent for ADK discovery
│   ├── agent.py                      # SequentialAgent orchestrator definition
│   │
│   ├── agents/                       # Four specialist LLM agents
│   │   ├── __init__.py
│   │   ├── parser_agent.py           # Stage 1: PL/SQL structure extraction
│   │   ├── analyzer_agent.py         # Stage 2: Logical annotation
│   │   ├── converter_agent.py        # Stage 3: C# code generation
│   │   └── validator_agent.py        # Stage 4: Structural validation
│   │
│   └── prompts/                      # Agent instruction files (plain text)
│       ├── parser_prompt.txt         # Parser rules and output schema
│       ├── analyzer_prompt.txt       # Analyzer categories and schema
│       ├── converter_prompt.txt      # Type table + 7 conversion rules
│       └── validator_prompt.txt      # 3-check validation protocol
│
└── docs/                             # Comprehensive documentation
    ├── architecture.md               # Full system architecture + diagrams
    ├── prompt-engineering-reference.md  # All 4 prompt contracts
    └── agents/
        ├── parser-agent.md
        ├── analyzer-agent.md
        ├── converter-agent.md
        └── validator-agent.md
```

---

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.9+ |
| **Agent Framework** | Google ADK (`google-adk`) | ≥ 0.1.0 |
| **LLM** | Gemini 2.5 Flash Lite | via Gemini API |
| **UI** | ADK Web (`adk web`) | Built-in |
| **Config** | python-dotenv | ≥ 1.0.0 |
| **Auth** | `GOOGLE_API_KEY` env var | — |

---

## ⚙️ Setup & Configuration

### Prerequisites

- **Python 3.9 or higher**
- **pip** (comes with Python)
- **Google Gemini API key** — [Get one free at Google AI Studio](https://aistudio.google.com/app/apikey)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `google-adk` — the Google Agent Development Kit
- `python-dotenv` — loads your `.env` file automatically

### Step 2: Configure API Key

```bash
cp .env.example .env
```

Open `.env` and set your key:

```env
GOOGLE_API_KEY=AIzaSy...your_key_here
```

> ⚠️ **Never commit your `.env` file.** It should be in `.gitignore`.

### Step 3: Launch ADK Web

```bash
# From the project root directory:
adk web
```

The ADK Web server starts at `http://localhost:8000`. Open it in your browser, select the `plsql_to_csharp_orchestrator` agent from the left panel, and start chatting.

### Environment Variables Reference

| Variable | Required | Description | How to Get |
|----------|----------|-------------|-----------|
| `GOOGLE_API_KEY` | ✅ Yes | Authenticates all Gemini API calls | [AI Studio](https://aistudio.google.com/app/apikey) |

---

## 🚀 Usage Guide

### Basic Usage

1. Navigate to `http://localhost:8000` after running `adk web`
2. Select **plsql_to_csharp_orchestrator** from the agent selector
3. Paste a complete PL/SQL stored procedure into the chat input
4. Press Enter — the pipeline runs in ~5-13 seconds
5. Review the `✅ VALIDATION PASSED` or `⚠️ VALIDATION WARNINGS` result
6. Copy the C# method body into your IDE

### What to Paste

The agent expects a **complete** PL/SQL stored procedure block, including:

```sql
CREATE OR REPLACE PROCEDURE procedure_name (
    param1   IN  data_type,
    param2   OUT data_type
) AS
    -- optional local variable declarations
BEGIN
    -- procedure body
EXCEPTION
    -- optional exception handlers
END procedure_name;
```

### Example 1: Simple Parameter Fetch

```sql
CREATE OR REPLACE PROCEDURE get_employee (
    p_emp_id   IN  NUMBER,
    p_name     OUT VARCHAR2,
    p_salary   OUT NUMBER
) AS
BEGIN
    SELECT emp_name, salary
    INTO p_name, p_salary
    FROM employees
    WHERE emp_id = p_emp_id;
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        p_name := 'NOT FOUND';
        p_salary := 0;
END get_employee;
```

**Generated C#:**

```csharp
public void GetEmployee(decimal pEmpId, out string pName, out decimal pSalary)
{
    try
    {
        string sql = "SELECT emp_name, salary FROM employees WHERE emp_id = :pEmpId";
        // TODO: Execute sql using your data access layer (e.g., Dapper, ADO.NET)
    }
    catch (Exception)
    {
        pName = "NOT FOUND";
        pSalary = 0;
    }
}
```

### Example 2: Loop with Input Validation

```sql
CREATE OR REPLACE PROCEDURE calculate_interest_breakdown (
    p_tenure     IN  INTEGER,
    p_rate       IN  FLOAT,
    p_amount     IN  BINARY_DOUBLE,
    p_result     OUT SYS_REFCURSOR
) AS
    v_opening  BINARY_DOUBLE;
    v_interest BINARY_DOUBLE;
    v_closing  BINARY_DOUBLE;
BEGIN
    IF p_tenure <= 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Tenure must be a positive integer.');
    ELSIF p_rate <= 0 OR p_rate > 100 THEN
        RAISE_APPLICATION_ERROR(-20002, 'Rate must be between 0 and 100.');
    END IF;

    v_opening := p_amount;

    FOR i IN 1 .. p_tenure LOOP
        v_interest := ROUND(v_opening * (p_rate / 100), 2);
        v_closing  := ROUND(v_opening + v_interest, 2);
        v_opening  := v_closing;
    END LOOP;
EXCEPTION
    WHEN INVALID_NUMBER THEN
        RAISE_APPLICATION_ERROR(-20010, 'Invalid numeric input.');
    WHEN OTHERS THEN
        RAISE_APPLICATION_ERROR(-20099, 'Unexpected error: ' || SQLERRM);
END calculate_interest_breakdown;
```

**Generated C# (abridged):**

```csharp
// TODO: SYS_REFCURSOR is not directly supported in C#. Consider returning a DataTable or List<T>.
public void CalculateInterestBreakdown(int pTenure, double pRate, double pAmount, out object pResult)
{
    double vOpening;
    double vInterest;
    double vClosing;

    if (pTenure <= 0)
    {
        throw new Exception("Tenure must be a positive integer.");
    }
    else if (pRate <= 0 || pRate > 100)
    {
        throw new Exception("Rate must be between 0 and 100.");
    }

    vOpening = pAmount;

    for (int i = 1; i <= pTenure; i++)
    {
        vInterest = Math.Round(vOpening * (pRate / 100), 2);
        vClosing = Math.Round(vOpening + vInterest, 2);
        vOpening = vClosing;
    }
    try { } // TODO: SYS_REFCURSOR open statement needs C# data access layer
    catch (InvalidCastException)
    {
        throw new Exception("Invalid numeric input.");
    }
    catch (Exception ex)
    {
        throw new Exception("Unexpected error: " + ex.Message);
    }
}
```

---

## 🗺️ Oracle → C# Type Mapping Reference

Complete mapping embedded in the Converter agent's prompt (`converter_prompt.txt`):

| Oracle Type | C# Type | Notes |
|-------------|---------|-------|
| `NUMBER` | `decimal` | Default for unspecified precision |
| `NUMBER(n,0)` | `int` | Integer-only precision |
| `INTEGER` | `int` | |
| `FLOAT` | `double` | |
| `BINARY_DOUBLE` | `double` | IEEE 754 double precision |
| `VARCHAR2` | `string` | Any declared length |
| `CHAR` | `string` | Fixed-length → mutable string |
| `CLOB` | `string` | Large text |
| `DATE` | `DateTime` | No timezone |
| `TIMESTAMP` | `DateTime` | Fractional seconds mapped |
| `BOOLEAN` | `bool` | PL/SQL non-SQL type |
| `BLOB` | `byte[]` | Binary data |

### Parameter Direction Mapping

| PL/SQL | C# | Example Signature |
|--------|----|-------------------|
| `IN param` | regular parameter | `decimal pAmount` |
| `OUT param` | `out` keyword | `out string pName` |
| `IN OUT param` | `ref` keyword | `ref decimal pBalance` |

---

## 🔄 Conversion Rules Reference

The Converter agent applies 7 named rules (source: `plsql_converter/prompts/converter_prompt.txt`):

| Rule | PL/SQL | C# |
|------|--------|-----|
| Method signature | `get_employee` | `public void GetEmployee(...)` |
| SQL statements | `SELECT ... INTO` | `string sql = "..."; // TODO: Execute` |
| IF/ELSIF/ELSE | `IF x THEN ... ELSIF y THEN ... END IF;` | `if (x) { ... } else if (y) { ... }` |
| FOR loop | `FOR i IN 1..n LOOP ... END LOOP;` | `for (int i = 1; i <= n; i++) { ... }` |
| LOOP...EXIT WHEN | `LOOP ... EXIT WHEN cond; END LOOP;` | `while (true) { ... if (cond) break; }` |
| Exception blocks | `EXCEPTION WHEN X THEN` | `try { } catch (Exception) { }` |
| Assignment | `:=` | `=` |
| NULL checks | `IS NULL` / `IS NOT NULL` | `== null` / `!= null` |
| Unsupported | `CURSOR`, `EXECUTE IMMEDIATE`, `BULK COLLECT` | `// TODO: not supported in MVP0` |

---

## ✅ Validation Rules Reference

The Validator agent (Stage 4) performs three checks on every generated output:

### Check 1: Method Signature
Confirms the code starts with a valid C# method signature — access modifier, return type, PascalCase name, typed parameter list.

### Check 2: Brace Balance
Counts `{` and `}` occurrences. They must be equal. Unbalanced braces = guaranteed compile error.

### Check 3: PL/SQL Leak Detection
Scans for unconverted Oracle tokens:

| Token Detected | Meaning |
|---------------|---------|
| `:=` | Assignment operator not converted |
| `BEGIN` / `END;` (standalone) | PL/SQL block delimiters leaked |
| `DECLARE` | Oracle section keyword leaked |
| `DBMS_OUTPUT` | Oracle print function not converted |
| `v_` prefix variables | PL/SQL naming convention not renamed |

**Output always includes the code**, regardless of result — designed for human review, not hard blocking.

---

## ⚠️ MVP0 Scope & Known Limitations

| Status | Feature |
|--------|---------|
| ✅ | PL/SQL Stored Procedures → C# method bodies |
| ✅ | 10-type Oracle → C# type mapping |
| ✅ | IN / OUT / IN OUT parameter direction mapping |
| ✅ | IF/ELSIF/ELSE, FOR, WHILE, LOOP control flow |
| ✅ | Exception handling → try/catch |
| ✅ | RAISE_APPLICATION_ERROR → `throw new Exception(...)` |
| ✅ | SQL preserved as raw `string sql` variables |
| ⚠️ | Cursors flagged with `// TODO` (no DataReader generation) |
| ⚠️ | `EXECUTE IMMEDIATE` (dynamic SQL) flagged with `// TODO` |
| ⚠️ | `BULK COLLECT / FORALL` flagged with `// TODO` |
| ⚠️ | `SYS_REFCURSOR` flagged with `// TODO` (suggest `DataTable`/`List<T>`) |
| ❌ | LINQ conversion (planned MVP1) |
| ❌ | Class / namespace wrapper (intentional — method body only) |
| ❌ | PL/SQL Functions (planned MVP1) |
| ❌ | Triggers (planned MVP2) |
| ❌ | Packages (planned MVP2) |
| ❌ | Batch file processing / CLI mode (planned MVP3) |

> **On unsupported constructs**: The agent never silently ignores them. Every unsupported construct receives a `// TODO` comment at the appropriate location in the generated C#, so you always know exactly what needs manual attention.

---

## 🔧 Troubleshooting

### `adk web` fails to start

**Check**: Are you running `adk web` from the project root directory (`plsql-to-csharp-agent/`)?

```bash
# Correct:
cd E:\GitHub\Python-Dev\plsql-to-csharp-agent
adk web

# Incorrect — ADK won't find the package:
cd E:\GitHub\Python-Dev
adk web
```

ADK discovers `root_agent` by importing `plsql_converter`, which must be on the Python path from the working directory.

---

### `ModuleNotFoundError: No module named 'google.adk'`

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install google-adk>=0.1.0 python-dotenv>=1.0.0
```

---

### `GOOGLE_API_KEY not found` / Authentication errors

1. Verify your `.env` file exists in the project root:
   ```bash
   ls .env
   ```

2. Verify the key is set correctly (no quotes around the value):
   ```env
   GOOGLE_API_KEY=AIzaSyABC123...
   ```

3. Verify your key is valid at [Google AI Studio](https://aistudio.google.com/).

---

### Agent produces garbled or missing output

**Cause**: LLM output formatting drift — the model didn't follow the expected delimiter schema.

**Solution**: This is probabilistic behavior. Simply re-submit the same PL/SQL. The structured prompt design makes this rare.

**Prevention**: Avoid sending very long procedures (>300 lines). Very large procedures may exceed the context window's ability to maintain structured formatting.

---

### Validator returns `⚠️ VALIDATION WARNINGS`

This is expected for complex procedures. The validator is heuristic (LLM-based, not a compiler). Warnings mean:

1. **Read the issue list** in the validation output
2. **Fix obvious issues** (e.g., a missed `:=` → `=` replacement)
3. **Compile in your IDE** — the C# compiler is the ground truth
4. **For `v_` prefix warnings**: These may be false positives if you use `v_` in your C# codebase

---

### Generated C# has `// TODO` comments

This is **by design** — not a bug. `// TODO` marks constructs that cannot be fully auto-converted in MVP0, such as cursors, dynamic SQL, and `SYS_REFCURSOR`. Review each TODO and implement the .NET equivalent manually.

---

## 📖 Documentation Index

| Document | Contents |
|----------|---------|
| [Architecture](docs/architecture.md) | C4 context diagram, pipeline flowchart, ADK session-state threading, design decisions |
| [Parser Agent](docs/agents/parser-agent.md) | Extraction contract, output schema, error handling |
| [Analyzer Agent](docs/agents/analyzer-agent.md) | 4 annotation categories, MVP0 exclusions, decision tree |
| [Converter Agent](docs/agents/converter-agent.md) | 7 conversion rules, full type table, end-to-end example |
| [Validator Agent](docs/agents/validator-agent.md) | 3-check logic, validation state machine, pass/warning schemas |
| [Prompt Engineering Reference](docs/prompt-engineering-reference.md) | All 4 prompt contracts, delimiter schemas, modification guide |

---

## 🗺️ Roadmap

| Version | Status | Features |
|---------|--------|---------|
| **MVP0** | ✅ Current | Stored Procedures → C# method bodies |
| **MVP1** | 🔲 Planned | PL/SQL Functions, LINQ conversion option |
| **MVP2** | 🔲 Planned | Triggers, Packages, full Cursor/`SYS_REFCURSOR` support |
| **MVP3** | 🔲 Planned | Batch file processing, CLI mode, multi-procedure files |

---

## 🤝 Contributing

Contributions are welcome! The most impactful areas for improvement:

1. **Extend the type mapping table** — add missing Oracle types to `plsql_converter/prompts/converter_prompt.txt`
2. **Improve cursor handling** — design a DataReader/`IEnumerable<T>` generation pattern
3. **Add Roslyn-based validation** — replace the LLM validator with a real C# syntax tree check
4. **CLI mode** — wrap the pipeline in a Click/argparse script for batch processing

### Prompt Modification Guide

All agent behavior lives in the `.txt` prompt files. To modify an agent:

1. Edit the relevant file in `plsql_converter/prompts/`
2. Restart `adk web` (prompts load at import time)
3. Test with representative PL/SQL input

See [`docs/prompt-engineering-reference.md`](docs/prompt-engineering-reference.md) for the modification guide and all prompt schemas.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- **[Google ADK](https://google.github.io/adk-docs/)** — Multi-agent orchestration framework
- **[Gemini API](https://ai.google.dev/)** — LLM inference powering all four pipeline stages
- **[Oracle PL/SQL Documentation](https://docs.oracle.com/en/database/oracle/oracle-database/)** — Reference for type and syntax mapping

---

*Built with Google ADK · Powered by Gemini 2.5 Flash Lite · MVP0*
