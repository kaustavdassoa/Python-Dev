# Resume Optimizer — ADK Multi-Agent System

An ATS-optimized resume bullet generator built on the **Google Agent Development Kit (ADK)**. It cross-references a candidate's master experience against a Job Description to produce high-impact bullets in the **Google XYZ format**.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│          ResumeOptimizer (Root Orchestrator)              │
│                   gemini-2.5-pro                         │
│                                                          │
│  Tools:                                                  │
│  ├── retrieve_master_experience()                        │
│  └── audit_hallucination()                               │
│                                                          │
│  Sub-Agents:                                             │
│  ├── GapAnalyzerAgent (gemini-2.5-flash)                 │
│  │   └── Tool: retrieve_master_experience()              │
│  └── ImpactWriterAgent (gemini-2.5-flash)                │
│       └── Output: optimized_bullets                      │
└──────────────────────────────────────────────────────────┘
```

### Agent Flow

1. **User** pastes a Job Description  
2. **ResumeOptimizer** calls `retrieve_master_experience` → loads candidate profile  
3. **GapAnalyzerAgent** receives JD + experience → outputs structured gap analysis  
4. **ImpactWriterAgent** receives gaps + experience → outputs XYZ-formatted bullets  
5. **ResumeOptimizer** calls `audit_hallucination` → verifies all claims are grounded  
6. **User** receives audited, ATS-optimized resume bullets  

## Project Structure

```
resume_optimizer/
├── __init__.py          # Exposes root_agent for ADK discovery
├── agent.py             # Root orchestrator (ResumeOptimizer)
├── config.py            # Model configuration dataclass
├── prompts.py           # System prompts for all agents
├── tools.py             # retrieve_master_experience, audit_hallucination
├── .env                 # GOOGLE_API_KEY (user-provided)
├── sub_agents/
│   ├── __init__.py      # Re-exports sub-agents
│   ├── gap_analyzer.py  # GapAnalyzerAgent
│   └── impact_writer.py # ImpactWriterAgent
└── README.md            # This file
```

## Setup

### 1. Install Dependencies

From the repo root (`agent-development-kit-crash-course/`):

```bash
pip install -r requirements.txt
```

> The `requirements.txt` already includes `google-adk`, `python-dotenv`, and other dependencies.

### 2. Configure API Key

Edit `resume_optimizer/.env` and replace the placeholder:

```env
GOOGLE_API_KEY=your-actual-api-key-here
```

Get a key from [Google AI Studio](https://aistudio.google.com/apikey).

### 3. Run with ADK Web

From the **parent directory** (not inside `resume_optimizer/`):

```bash
cd E:\GitHub\Python-Dev\agent-development-kit-crash-course
adk web resume_optimizer
```

The ADK web UI will open in your browser. Select **resume_optimizer** from the agent list.

## Usage

Paste a Job Description into the chat. For example:

> **Senior Backend Engineer — FinTech Startup**  
> Requirements: 5+ years Python, microservices architecture, AWS, Kafka,  
> PostgreSQL, CI/CD pipelines, team leadership experience.

The system will:
1. Load the candidate's master experience
2. Produce a gap analysis mapping JD requirements to experience
3. Generate 8-12 ATS-optimized bullets in Google XYZ format
4. Audit all bullets for hallucinations before presenting results

## The Google XYZ Bullet Format

Every bullet follows this structure:

> **"Accomplished [X] as measured by [Y], by doing [Z]"**

- **X** = The impact or result achieved  
- **Y** = The quantifiable metric proving the impact  
- **Z** = The specific action or method used  

## Customization

| What | Where | How |
|------|-------|-----|
| Candidate data | `tools.py` → `retrieve_master_experience()` | Replace the sample dict with your real data source |
| Models | `config.py` → `ResumeOptimizerConfig` | Change `orchestrator_model` / `worker_model` |
| Agent behavior | `prompts.py` | Edit the system prompts directly |
| Audit logic | `tools.py` → `audit_hallucination()` | Swap keyword-overlap with embeddings or LLM-as-judge |
