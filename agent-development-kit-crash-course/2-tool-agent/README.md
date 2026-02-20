# Tool Agent Example

## What is a Tool Agent?

A Tool Agent extends the basic ADK agent by incorporating tools that allow the agent to perform actions beyond just generating text responses. Tools enable agents to interact with external systems, retrieve information, and perform specific functions to accomplish tasks more effectively.

In this example, we demonstrate how to build an agent that can use built-in tools (like Google Search) and custom function tools to enhance its capabilities.

---

## Project Structure

```
2-tool-agent/
├── README.md                          ← This file
├── tool_agent/                        ← Python package (has __init__.py)
│   ├── __init__.py                    ← Package initializer (imports agent module)
│   ├── .env                           ← Environment variables (GOOGLE_API_KEY)
│   ├── agent.py                       ← Agent definition + interactive chat mode
│   ├── test_agent.py                  ← Unit tests (no API calls)
│   └── test_agent_integration.py      ← Integration tests (real API calls)
```

---

## How `agent.py` Works

The `agent.py` file is the core of this project. It defines the AI agent and provides an interactive chat mode for testing.

### Part 1: Environment Setup (Lines 1–11)

```python
from google.adk.agents import Agent
from google.adk.tools import google_search
from dotenv import load_dotenv
import os

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    print("Warning: GOOGLE_API_KEY not found in environment")
```

**What happens here:**
1. **Imports** the `Agent` class from Google ADK and the built-in `google_search` tool
2. **Loads `.env`** file using `python-dotenv` — this reads `GOOGLE_API_KEY` from the `.env` file and sets it as an environment variable
3. **Checks** if the API key is available and prints a warning if not

### Part 2: Agent Definition (Lines 21–33)

```python
root_agent = Agent(
    name="tool_agent",
    model="gemini-2.5-flash-lite",
    description="Tool agent",
    instruction="""
    You are a helpful assistant that can use the following tools:
    - google_search
    """,
    tools=[google_search],
)
```

**What each parameter does:**

| Parameter | Purpose |
|-----------|---------|
| `name` | Unique identifier for the agent (used by ADK internally) |
| `model` | The Gemini model to use for generating responses |
| `description` | Short description (used in multi-agent setups for agent selection) |
| `instruction` | System prompt — tells the LLM how to behave and what tools are available |
| `tools` | List of tools the agent can invoke during conversations |

**How the `google_search` tool works internally:**
- It's a **model-native tool** — it doesn't execute code locally
- When the LLM decides it needs search results, it sends a `google_search` function call
- The Gemini API internally performs the search and returns results to the LLM
- The LLM then synthesizes the search results into its response

### Part 3: Interactive Chat Mode (Lines 35–89)

```python
if __name__ == "__main__":
    ...
```

This block runs **only** when you execute `python agent.py` directly. It:

1. **Creates an `InMemorySessionService`** — stores conversation history in memory (lost when the program exits)
2. **Creates a session** — a unique conversation context identified by `SESSION_ID`
3. **Creates a `Runner`** — the orchestrator that connects the agent, session, and LLM
4. **Starts an interactive loop** — reads user input, sends it to the agent, and prints responses

**Flow diagram:**

```
┌─────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  User    │────►│  Runner  │────►│  Agent   │────►│ Gemini   │
│  Input   │     │          │     │          │     │ API      │
└─────────┘     └──────────┘     └──────────┘     └──────────┘
                     │                                   │
                     │         ┌──────────┐              │
                     │         │ Session  │              │
                     └────────►│ Service  │◄─────────────┘
                               │ (memory) │  stores history
                               └──────────┘
```

**Key concept — `runner.run()` event loop:**

```python
for event in runner.run(user_id=..., session_id=..., new_message=message):
    if event.is_final_response():
        print(event.content.parts[0].text)
```

- `runner.run()` returns an **iterator of events**
- Events include: tool calls, intermediate responses, and the final response
- We only care about `is_final_response()` — the agent's completed answer
- The session service automatically stores the conversation history, enabling multi-turn context

---

## How `test_agent.py` Works (Unit Tests)

### Purpose
Unit tests verify the agent's **configuration and structure** without making any API calls. They are fast, free, and repeatable.

### How to Run

```bash
cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\2-tool-agent
python -m unittest tool_agent.test_agent -v
```

### Test Classes

#### `TestAgentConfiguration` — Verifies agent setup

| Test | What it checks |
|------|---------------|
| `test_agent_name` | Agent name is `"tool_agent"` |
| `test_agent_model` | Model is set correctly |
| `test_agent_description` | Description is `"Tool agent"` |
| `test_agent_instruction_is_set` | Instructions mention `"google_search"` |
| `test_agent_has_tools` | At least one tool is configured |
| `test_agent_has_google_search_tool` | `google_search` is in the tools list |
| `test_root_agent_is_agent_instance` | `root_agent` is an `Agent` instance |

**Key technique — Mocking the API key:**

```python
@patch.dict(os.environ, {"GOOGLE_API_KEY": "test-api-key-12345"})
def setUp(self):
    import importlib
    import tool_agent.agent as agent_module
    importlib.reload(agent_module)
    self.agent = agent_module.root_agent
```

- `@patch.dict` temporarily sets a fake API key so the agent module doesn't print warnings
- `importlib.reload()` forces Python to re-execute `agent.py` with the patched environment
- This ensures each test gets a fresh agent instance

#### `TestEnvironmentSetup` — Verifies `.env` handling

| Test | What it checks |
|------|---------------|
| `test_api_key_present` | No warning printed when key exists |
| `test_api_key_missing_prints_warning` | Warning printed when key is missing |

#### `TestModuleImports` — Verifies dependencies are installed

| Test | What it checks |
|------|---------------|
| `test_import_agent_class` | `google.adk.agents.Agent` is importable |
| `test_import_google_search` | `google.adk.tools.google_search` is importable |
| `test_import_dotenv` | `dotenv.load_dotenv` is importable |
| `test_import_root_agent` | `tool_agent.agent.root_agent` is importable |

---

## How `test_agent_integration.py` Works (Integration Tests)

### Purpose
Integration tests make **real API calls** to the Gemini LLM to verify the agent works end-to-end. They consume API quota and require internet access.

### Requirements
- ✅ Valid `GOOGLE_API_KEY` in the `.env` file
- ✅ Internet access
- ✅ Available API quota (free tier: 1,500 requests/day)

### How to Run

```bash
cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\2-tool-agent
python -m unittest tool_agent.test_agent_integration -v
```

### Architecture

```
┌───────────────────────────────────────────────────────┐
│  test_agent_integration.py                            │
│                                                       │
│  ┌──────────────┐    ┌──────────────────────────┐     │
│  │  run_agent() │───►│  InMemorySessionService  │     │ 
│  │  (helper)    │    │  + Runner + Agent        │     │
│  └──────┬───────┘    └───────────┬──────────────┘     │
│         │                        │                    │
│  ┌──────▼───────┐    ┌───────────▼──────────────┐     │
│  │ _run_or_skip │    │  Gemini API (real call)   │    │
│  │ (error       │    │  Model: gemini-2.5-flash  │    │
│  │  handler)    │    │  -lite                    │    │
│  └──────────────┘    └──────────────────────────┘     │
└───────────────────────────────────────────────────────┘
```

### The `run_agent()` Helper Function

This is the core helper that every test uses:

```python
def run_agent(user_message: str) -> str:
```

**Step-by-step flow:**

1. Creates a new `InMemorySessionService` (fresh session each test)
2. Calls `asyncio.run(session_service.create_session(...))` — async because newer ADK versions require it
3. Creates a `Runner` with the agent
4. Sends the message and collects the response from the event stream
5. If the response is empty, raises a `RuntimeError` (catches silent background thread failures)

### Rate Limit Protection

```python
DELAY_BETWEEN_TESTS = 5  # seconds

def setUp(self):
    time.sleep(DELAY_BETWEEN_TESTS)
```

Each test waits **5 seconds** before running to avoid hitting the free tier rate limit (30 requests/minute for `gemini-2.5-flash-lite`).

### Quota Error Handling: `_run_or_skip()`

```python
def _run_or_skip(self, message: str) -> str:
    try:
        return run_agent(message)
    except RuntimeError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "empty response" in str(e):
            self.skipTest(f"API quota exhausted or empty response: {e}")
        raise
```

Instead of **failing** when the API quota is exhausted, tests **skip** gracefully. This is important because:
- Quota errors are not bugs — they're resource limits
- A skipped test (`s`) is different from a failed test (`F`) in the test report
- CI/CD pipelines can distinguish between real failures and quota issues

### Test Cases

#### `TestAgentLLMIntegration` — Single-turn tests

| Test | What it sends | What it asserts |
|------|--------------|----------------|
| `test_simple_greeting` | `"Hello, how are you?"` | Response is non-empty string |
| `test_factual_question` | `"What is the capital of France?"` | Response contains `"Paris"` |
| `test_search_query` | `"Search for the latest news about Python..."` | Response is non-empty (exercises `google_search` tool) |
| `test_response_is_not_error` | `"Tell me a fun fact about space"` | Response doesn't contain `"Error"` or `"exception"` |

#### `TestAgentMultiTurn` — Multi-turn conversation test

This test verifies the agent **remembers context** across conversation turns:

```
Turn 1: "My favorite programming language is Python."
         → Agent acknowledges
         
         [3 second delay]
         
Turn 2: "What is my favorite programming language?"
         → Agent should respond with "Python"
```

This works because both turns share the **same session** (`session_id`), so the `InMemorySessionService` stores Turn 1's conversation history and includes it when processing Turn 2.

---

## Key Components (ADK Concepts)

### 1. Built-in Tools
ADK provides several built-in tools that you can use with your agents:

- **Google Search**: Allows your agent to search the web for information
- **Code Execution**: Enables your agent to run code snippets
- **Vertex AI Search**: Lets your agent search through your own data

**Important Note**: Currently, for each root agent or single agent, only one built-in tool is supported. See the [ADK documentation](https://google.github.io/adk-docs/tools/built-in-tools/#use-built-in-tools-with-other-tools) for more details.

### 1. Built-in & Standard Tools

Google ADK provides several "model-native" tools that are handled directly by the Gemini API.

| Tool Name | Description | Configurable Parameters | Import Path |
| :--- | :--- | :--- | :--- |
| **Google Search** | Performs web searches using Google Search with Gemini to provide real-time info. | None (Auto-managed) | `from google.adk.tools import google_search` |
| **Code Execution** | Securely executes Python code generated by the model to solve math or logic tasks. | `code_executor=BuiltInCodeExecutor()` | `from google.adk.code_executors import BuiltInCodeExecutor` |
| **Computer Use** | Allows the agent to operate a computer UI (e.g., controlling a browser). | `computer` (requires an implementation like `PlaywrightComputer`) | `from google.adk.tools.computer_use.computer_use_toolset import ComputerUseToolset` |

### 2. Custom Function Tools
You can create your own tools by defining Python functions. These custom tools extend your agent's capabilities to perform specific tasks.

#### Best Practices for Custom Function Tools:

- **Parameters**: Define your function parameters using standard JSON-serializable types (string, integer, list, dictionary)
- **No Default Values**: Default values are not currently supported in ADK
- **Return Type**: The preferred return type is a dictionary
  - If you don't return a dictionary, ADK will wrap it into a dictionary `{"result": ...}`
  - Best practice format: `{"status": "success", "error_message": None, "result": "..."}`
- **Docstrings**: The function's docstring serves as the tool's description and is sent to the LLM
  - Focus on clarity so the LLM understands how to use the tool effectively

## Limitations

### Single Built-in Tool Restriction

**Currently, for each root agent or single agent, only one built-in tool is supported.**

```python
# ❌ NOT SUPPORTED — two built-in tools
root_agent = Agent(
    tools=[built_in_code_execution, google_search],
)
```

### Built-in Tools vs. Custom Tools

**You cannot mix built-in tools with custom function tools in the same agent.**

```python
# ❌ NOT SUPPORTED — mixing built-in + custom
root_agent = Agent(
    tools=[google_search, get_current_time],
)
```

> [!IMPORTANT]
> **Mixing Built-in + Custom Tools**: You cannot currently mix model-native tools (like `google_search`) and custom function tools in the same `tools=[]` list. To use both, you should use an **Agent Tool** pattern where one agent handles search and another handles custom functions.

To use both types, use the Agent Tool approach described in the Multi-Agent example.

---

## Getting Started

### Prerequisites

1. **Python 3.12+** with the required packages:
   ```bash
   pip install google-adk python-dotenv google-generativeai
   ```

2. **API Key**: Rename `.env.example` to `.env` in the `tool_agent/` folder and add your key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

### Running the Agent

#### Option 1: Interactive Chat Mode (direct)
```bash
cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\2-tool-agent\tool_agent
python agent.py
```
Type messages and get responses. Type `quit` to exit.

#### Option 2: ADK Web UI
```bash
cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\2-tool-agent
adk web
```
Open [http://localhost:8000](http://localhost:8000) and select "tool_agent" from the dropdown.

#### Option 3: ADK CLI
```bash
cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\2-tool-agent
adk run tool_agent
```

### Running Tests

> **Important**: You must run test commands from the `2-tool-agent/` directory (the **parent** of `tool_agent/`), not from inside the package. This is because Python needs to find `tool_agent` as a package on `sys.path`.

```bash
cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\2-tool-agent

# Unit tests (no API calls, fast, free)
python -m unittest tool_agent.test_agent -v

# Integration tests (real API calls, consume quota)
python -m unittest tool_agent.test_agent_integration -v

# Run all tests
python -m unittest discover -s tool_agent -p "test_*.py" -v
```

### Example Prompts to Try

- "Search for recent news about artificial intelligence"
- "Find information about Google's Agent Development Kit"
- "What are the latest advancements in quantum computing?"

---

## Monitoring Token Usage

The agent script tracks and displays token usage after every interaction. This helps you monitor your consumption against the daily quota.

### Token Types Explained

| Token Type | Description |
|------------|-------------|
| **Prompt Tokens** | The total number of tokens sent to the model. This includes your current question, the system instructions, and the **entire conversation history** (cumulative memory). |
| **Completion Tokens** | The number of tokens generated by the model in its response. |
| **Total Tokens** | The cumulative sum of all tokens processed during that specific turn, including internal tool-calling steps. |

### Example Interaction

Notice how the prompt tokens grow as the conversation continues, due to the cumulative chat history:

==================================================

**📝 You:** Where India AI Sumit 2026 is going to be held ?

**💬 Agent:** The India AI Impact Summit 2026 is being held in New Delhi, India. The primary venue is Bharat Mandapam, with additional events taking place at Sushma Swaraj Bhawan, Vigyan Bhawan, and Dr. Ambedkar Bhawan. The summit is scheduled to run from February 16 to February 20, 2026.

**📊 Usage:** Prompt: 62 | Completion: 107 | Total: 262

**📝 You:** Where will the India AI Summit 2026 be held?

**💬 Agent:** The India AI Impact Summit 2026 will be held at Bharat Mandapam in New Delhi, India. Other venues for events include Sushma Swaraj Bhawan and Vigyan Bhawan. The summit is scheduled to take place from February 16 to February 20, 2026.

**📊 Usage:** Prompt: 154 | Completion: 99 | Total: 441

> [!NOTE]
> Even though both questions are similar, the second prompt is larger because it contains the first question and answer as context. Misspellings like "Sumit" vs "Summit" also subtly affect tokenization.

---

---

## Free Tier API Quota

| Model | Requests/Min | Requests/Day | Tokens/Min |
|-------|-------------|-------------|-----------|
| `gemini-2.5-flash-lite` | 30 | 1,500 | 1,000,000 |
| `gemini-2.0-flash` | 15 | 1,500 | 1,000,000 |
| `gemini-2.5-pro` | 5 | 250 | 1,000,000 |

### Requests vs. Tokens: Which matters more?

In the Free Tier, both are tracked simultaneously. You will be blocked if you exceed **any** of these limits.

*   **Request Limits (RPM/RPD):** These count "how many times" you hit the Send button. RPM prevents spamming the API, while RPD is your total daily allowance. 
    *   *Standard chat users usually hit these first.*
*   **Token Limits (TPM):** These count "how much information" you process. One request can vary from 10 tokens to 1 million tokens (e.g., a long PDF or huge chat history).
    *   *Developers/Agents hit these if they process large documents or maintain very long chat sessions.*

**Summary:** Requests are your **tickets** (entry frequency), while Tokens are your **weight** (data volume).

---

Quota resets daily at **midnight Pacific Time (PT)**.

---

## Additional Resources

- [Types of tools](https://google.github.io/adk-docs/tools/#full-example-tavily-search)
- [ADK Function Tools Documentation](https://google.github.io/adk-docs/tools/function-tools/)
- [ADK Built-in Tools Documentation](https://google.github.io/adk-docs/tools/built-in-tools/)
- [Gemini API Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
