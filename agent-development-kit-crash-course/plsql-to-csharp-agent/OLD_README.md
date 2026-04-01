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

**Example 1:**

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

**Expected C# output:**

```csharp
public void GetEmployee(decimal pEmpId, out string pName, out decimal pSalary)
{
    try
    {
        string sql = "SELECT emp_name, salary INTO :pName, :pSalary FROM employees WHERE emp_id = :pEmpId";
        // TODO: Execute sql using your data access layer (e.g., Dapper, ADO.NET)
        // The INTO clause in PL/SQL maps to output parameters in C#.
        // You will need to bind pName and pSalary to the output parameters of your data access method.
    }
    catch (Exception)
    {
        pName = "NOT FOUND";
        pSalary = 0;
    }
}
// TODO: SYS_REFCURSOR is not directly supported in C#. Consider returning a DataTable, List<T>, or a custom object.
// TODO: The PL/SQL collection type 't_interest_table' needs a C# equivalent, like a List of a custom class.
// TODO: The RAISE_APPLICATION_ERROR function needs to be mapped to appropriate C# exception handling.
public void CalculateInterestBreakdown(int pTenure, double pRate, double pAmount, out object pResult) // Using 'object' as a placeholder for SYS_REFCURSOR
{
    // TODO: Convert PL/SQL Record and Table types to C# classes and Lists.
    // Example placeholder for the collection: List<InterestRow> vTable = new List<InterestRow>();

    if (pTenure <= 0)
    {
        // TODO: Map RAISE_APPLICATION_ERROR to C# exceptions.
        throw new Exception("Tenure must be a positive integer.");
    }
    else if (pRate <= 0 || pRate > 100)
    {
        // TODO: Map RAISE_APPLICATION_ERROR to C# exceptions.
        throw new Exception("Rate must be between 0 and 100.");
    }
    else if (pAmount <= 0)
    {
        // TODO: Map RAISE_APPLICATION_ERROR to C# exceptions.
        throw new Exception("Amount must be a positive value.");
    }

    double vOpening = pAmount;
    double vInterest;
    double vClosing;

    // TODO: Implement the collection population logic using C# Lists and custom objects.
    for (int i = 1; i <= pTenure; i++)
    {
        vInterest = Math.Round(vOpening * (pRate / 100), 2);
        vClosing = Math.Round(vOpening + vInterest, 2);

        // TODO: Add calculated row to the C# collection (e.g., vTable.Add(new InterestRow { ... }));

        vOpening = vClosing;
    }

    // TODO: Convert the C# collection to a format that can be returned, simulating a SYS_REFCURSOR.
    // This might involve creating a DataTable or a List of dynamic objects.
    // Example: pResult = ConvertToDataTable(vTable);

    try
    {
        // The OPEN p_result FOR statement is a PL/SQL construct for returning query results.
        // In C#, you would typically execute a query using your data access layer and return the results.
        string sql = @"
            SELECT v_year        AS year_number,
                   v_opening_bal AS opening_balance,
                   v_interest    AS interest_collected,
                   v_closing_bal AS closing_balance
            FROM TABLE(v_table) -- This FROM TABLE syntax is specific to Oracle and needs a C# equivalent.
            ORDER BY v_year";
        // TODO: Execute sql using your data access layer (e.g., Dapper, ADO.NET) and assign the result to pResult.
    }
    catch (InvalidCastException) // Simulating INVALID_NUMBER
    {
        // TODO: Map RAISE_APPLICATION_ERROR to C# exceptions.
        throw new Exception("Invalid numeric input detected.");
    }
    catch (Exception ex)
    {
        // TODO: Map RAISE_APPLICATION_ERROR to C# exceptions.
        throw new Exception("Unexpected error in CalculateInterestBreakdown: " + ex.Message);
    }
}
```

**Example 2:**

```sql
CREATE OR REPLACE PROCEDURE calculate_interest_breakdown (
    p_tenure     IN  INTEGER,         -- Number of years (e.g., 10)
    p_rate       IN  FLOAT,           -- Annual interest rate % (e.g., 7.5)
    p_amount     IN  BINARY_DOUBLE,   -- Principal amount (e.g., 100000.00)
    p_result     OUT SYS_REFCURSOR    -- Year-wise breakdown as a result set
)
AS
    -- Local collection type to hold year-wise rows
    TYPE t_interest_row IS RECORD (
        v_year        INTEGER,
        v_opening_bal BINARY_DOUBLE,
        v_interest    BINARY_DOUBLE,
        v_closing_bal BINARY_DOUBLE
    );
    TYPE t_interest_table IS TABLE OF t_interest_row INDEX BY PLS_INTEGER;

    v_table    t_interest_table;
    v_opening  BINARY_DOUBLE;
    v_interest BINARY_DOUBLE;
    v_closing  BINARY_DOUBLE;

BEGIN
    -- Input validation
    IF p_tenure <= 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Tenure must be a positive integer.');
    ELSIF p_rate <= 0 OR p_rate > 100 THEN
        RAISE_APPLICATION_ERROR(-20002, 'Rate must be between 0 and 100.');
    ELSIF p_amount <= 0 THEN
        RAISE_APPLICATION_ERROR(-20003, 'Amount must be a positive value.');
    END IF;

    v_opening := p_amount;

    -- Build year-wise interest breakdown into local collection
    FOR i IN 1 .. p_tenure LOOP
        v_interest := ROUND(v_opening * (p_rate / 100), 2);
        v_closing  := ROUND(v_opening + v_interest, 2);

        v_table(i).v_year        := i;
        v_table(i).v_opening_bal := v_opening;
        v_table(i).v_interest    := v_interest;
        v_table(i).v_closing_bal := v_closing;

        -- Next year opens at this year's closing balance
        v_opening := v_closing;
    END LOOP;

    -- Return as a ref cursor ordered by year
    OPEN p_result FOR
        SELECT v_year        AS year_number,
               v_opening_bal AS opening_balance,
               v_interest    AS interest_collected,
               v_closing_bal AS closing_balance
        FROM TABLE(v_table)
        ORDER BY v_year;

EXCEPTION
    WHEN INVALID_NUMBER THEN
        RAISE_APPLICATION_ERROR(-20010, 'Invalid numeric input detected.');
    WHEN OTHERS THEN
        RAISE_APPLICATION_ERROR(-20099,
            'Unexpected error in calculate_interest_breakdown: ' || SQLERRM);
END calculate_interest_breakdown;
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
