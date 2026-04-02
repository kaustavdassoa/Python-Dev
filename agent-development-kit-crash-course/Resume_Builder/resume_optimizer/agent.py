"""
Resume Optimizer — Root Agent

A 9-agent sequential pipeline that rewrites resumes to maximize
ATS compatibility and job description alignment.

Usage:
    adk web
    
    In the chat, use this format:
    
    [RESUME]
    <paste your resume text here, OR provide the full path to your .pdf or .docx file>

    [JOB DESCRIPTION]
    <paste the full job description here>
"""

import os
from dotenv import load_dotenv
from google.adk.agents import SequentialAgent

# Load environment variables (.env file)
load_dotenv()

# Import all sub-agents in pipeline order
from .sub_agents.document_parser.agent import document_parser_agent
from .sub_agents.jd_analyzer.agent import jd_analyzer_agent
from .sub_agents.alignment_validator.agent import alignment_validator_agent
from .sub_agents.alignment_gatekeeper.agent import alignment_gatekeeper_node
from .sub_agents.ats_precheck.agent import ats_precheck_agent
from .sub_agents.resume_rewriter.agent import resume_rewriter_agent
from .sub_agents.ats_scorer.agent import ats_scorer_agent
from .sub_agents.critic.agent import critic_agent
from .sub_agents.html_renderer.agent import html_renderer_agent
from .sub_agents.report_generator.agent import report_generator_agent

# ── Root Sequential Agent ───────────────────────────────────────────────────
root_agent = SequentialAgent(
    name="ResumeOptimizerPipeline",
    description="""
A multi-agent pipeline that rewrites your resume to maximize ATS compatibility
for a specific job description.

How to use — paste your input using this format:

[RESUME]
<paste your resume text here, OR provide full path to .pdf or .docx>

[JOB DESCRIPTION]
<paste the full job description here>

The pipeline will:
1. Parse your resume (PDF/DOCX/text)
2. Analyze the job description
3. Validate career-level alignment (HARD GATE)
4. Score your original resume against ATS keywords
5. Rewrite every section for maximum keyword match and impact
6. Re-score the optimized resume
7. Quality-review the rewrite for fabrications and page length (HARD GATE)
8. Render a clean HTML resume preview
9. Generate a full ATS analysis report
""",
    sub_agents=[
        document_parser_agent,       # Agent 1: Parse resume, check completeness
        jd_analyzer_agent,           # Agent 2: Analyze JD, check authenticity
        alignment_validator_agent,   # Agent 3: HARD GATE — career level match
        alignment_gatekeeper_node,   # Agent 3.5: Execute hard gate logic
        ats_precheck_agent,          # Agent 4: Formatting check + BEFORE score
        resume_rewriter_agent,       # Agent 5: Core rewriting engine
        ats_scorer_agent,            # Agent 6: AFTER score + delta
        critic_agent,                # Agent 7: HARD GATE — quality review
        html_renderer_agent,         # Agent 8: HTML resume output
        report_generator_agent,      # Agent 9: Full analysis report
    ]
)
