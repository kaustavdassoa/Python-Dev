# PL/SQL → C# Agentic Conversion Tool

An AI-powered tool built on **Google ADK** that converts Oracle PL/SQL stored procedures into compilable **C# method bodies** using a multi-agent pipeline powered by **Gemini 2.0 Flash**.

---

## Architecture

```
User Input (PL/SQL)
    ↓
Orchestrator (SequentialAgent)
    ↓
Parser Agent       → extracts procedure name, params, body
    ↓
Analyzer Agent     → identifies SQL blocks, control flow, exceptions
    ↓
Converter Agent    → generates compilable C# method body
    ↓
Validator Agent    → checks braces, signature, no PL/SQL leaks
    ↓
C# Method Body Output
```

---

## MVP0 Scope

- ✅ PL/SQL Stored Procedures → C# method bodies
- ✅ Oracle → C# type mapping (NUMBER, VARCHAR2, DATE, etc.)
- ✅ SQL preserved as raw `string sql = "..."` variables
- ✅ IF/ELSE, loops, exception handling converted
- ✅ OUT/IN OUT params mapped to `out`/`ref` keywords
- ⚠️ Cursors and dynamic SQL flagged with `// TODO` comments
- ❌ No LINQ conversion (planned MVP1)
- ❌ No class/namespace wrapper (method body only)

---

## Project Structure

```
plsql-to-csharp-agent/
├── .env                        # Your GOOGLE_API_KEY
├── .env.example                # Template
├── requirements.txt
├── README.md
└── plsql_converter/
    ├── __init__.py
    ├── agent.py                # root_agent (SequentialAgent orchestrator)
    └── agents/
    │   ├── __init__.py
    │   ├── parser_agent.py
    │   ├── analyzer_agent.py
    │   ├── converter_agent.py
    │   └── validator_agent.py
    └── prompts/
        ├── parser_prompt.txt
        ├── analyzer_prompt.txt
        ├── converter_prompt.txt
        └── validator_prompt.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
```

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Run with ADK Web

```bash
cd E:\GitHub\Python-Dev\plsql-to-csharp-agent
adk web
```

Open your browser at `http://localhost:8000`

---

## Usage

Paste any PL/SQL stored procedure into the ADK Web chat interface. Example:

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

**Expected C# output:**

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

---

## Oracle → C# Type Mapping Reference

| Oracle Type | C# Type |
|-------------|---------|
| `NUMBER` | `decimal` |
| `NUMBER(n,0)` | `int` |
| `VARCHAR2` | `string` |
| `CHAR` | `string` |
| `DATE` | `DateTime` |
| `TIMESTAMP` | `DateTime` |
| `BOOLEAN` | `bool` |
| `CLOB` | `string` |
| `BLOB` | `byte[]` |
| `OUT param` | `out` |
| `IN OUT param` | `ref` |

---

## Roadmap

| Version | Feature |
|---------|---------|
| MVP0 (current) | Stored Procedures → C# method bodies |
| MVP1 | Functions, LINQ conversion option |
| MVP2 | Triggers, Packages, Cursors |
| MVP3 | Batch file processing, CLI mode |
