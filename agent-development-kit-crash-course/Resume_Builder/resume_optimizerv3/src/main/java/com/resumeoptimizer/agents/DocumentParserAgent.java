package com.resumeoptimizer.agents;

import com.google.adk.agents.LlmAgent;
import com.google.adk.tools.FunctionTool;
import com.resumeoptimizer.tools.DocumentParserTools;

/**
 * Agent 1 of 9 — Document Parser (LlmAgent + FunctionTool).
 * Parses resume text from session state or file path.
 */
public final class DocumentParserAgent {

    private DocumentParserAgent() {}

    public static LlmAgent create() {
        return LlmAgent.builder()
                .name("DocumentParserAgent")
                .model("gemini-2.0-flash")
                .instruction("""
                    You are a Resume Document Parser. Your task is to extract and structure resume content.
                    
                    RULES:
                    1. If raw_resume_text is already present in the session state and is non-empty,
                       parse it directly — DO NOT call any tools.
                    2. If a file_path is provided, call the parseResumeFile tool to extract text.
                    3. Parse the extracted text into a structured JSON with these sections:
                       - contact: {name, email, phone, location, linkedin}
                       - summary: string
                       - skills: [string]
                       - experience: [{title, company, dates, bullets: [string], entry_type}]
                       - education: [{degree, institution, year}]
                       - certifications: [string]
                    4. entry_type should be "job", "project", or "volunteer" based on context.
                    5. Preserve ALL content — do NOT truncate or summarize.
                    6. Include page boundary markers if present.
                    
                    Return the complete structured resume as JSON with a top-level key "resume_sections".
                    """)
                .description("Parses resume text and structures it into sections.")
                .tools(FunctionTool.create(DocumentParserTools.class, "parseResumeFile"))
                .outputKey("document_parser_output")
                .disallowTransferToParent(true)
                .disallowTransferToPeers(true)
                .build();
    }
}
