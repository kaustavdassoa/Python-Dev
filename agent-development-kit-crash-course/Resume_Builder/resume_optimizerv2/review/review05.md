I need to perform a strict FinOps audit of my Resume Optimizer pipeline (located in the `resume_optimizerv2` directory). Currently, our token consumption is far too high. 

**DO NOT write or modify any application code today.** Please execute an architectural review based on the following phases:

### Phase 1: The Token Audit
Read through my project files in `resume_optimizerv2` (specifically the ADK agent definitions and state management). Identify the areas with the highest token bloat. Are we passing redundant data between agents? 

### Phase 2: Compression & Optimization Strategy
Use the **`@context-compression`** and **`@llm-prompt-optimizer`** skills. 
1. Suggest exactly how we can shrink the state payload being passed between agents.
2. Identify which agent `INSTRUCTION` prompts are too verbose and can be optimized to save tokens.

### Phase 3: Advanced Caching
Use the **`@prompt-caching`** skill to evaluate if we can implement system-level context caching for large, static data (such as the Job Description, the base resume text, or heavy system instructions) across the pipeline. 

**Output:** Synthesize your findings into a detailed markdown report named `token_optimization_report.md`. Wait for my review of this document before we plan any actual code changes.