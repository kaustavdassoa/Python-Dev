# Review # 05 : Lesson Leaned : LLM pipeline optimization, prompt engineering, and architectural FinOps

1.  **Prompt Engineering & Optimization**
    The goal of prompt engineering is to maximize LLM reliability while minimizing the input footprint.

	Be Terse, Not Conversational: LLMs do not need polite preamble. Replace verbose instructions and massive 40-line JSON examples with strict, compact schemas.

	Defeat LLM "Laziness" (Anti-Truncation): When asking an LLM to extract large amounts of data (like a 3-page resume), it will often try to save tokens by dropping older entries. You must use explicit "Anti-Truncation" guardrails in your prompt (e.g., "Extract every single role. Do not summarize or skip older roles.").

	Explicit Data Mapping: If an LLM encounters a weird header (like "Selected Projects" instead of "Work Experience"), it might ignore it. Explicitly tell the LLM how to map synonymous terms to your desired JSON keys.

2. ***Architectural FinOps (Cutting Token Waste)**
   How you chain your agents together dictates 90% of your API costs.

   Avoid the "Conversation History Snowball": Frameworks often default to passing the entire chat history to the next agent in the chain. By agent #4, you are paying to process 20,000+ tokens of redundant data.

   State-Based Routing: Instead of passing history, have agents save their output to a central dictionary (State). Subsequent agents should only pull the specific variables they need (e.g., state["jd_keywords"]) rather than reading the entire document again.

   Never Pay an LLM to do Math: If a decision involves basic arithmetic, string matching, or rule-based logic (like checking if a seniority gap is > 2), replace the AI agent with a standard Python script. Standard code is 100% reliable, executes instantly, and costs zero tokens.

   Calculate Diffs Deterministically: Never use an LLM to compare two documents to write a "changes summary." Use standard Python text comparison libraries to generate the diff instantly and for free.

3. **Advanced API Techniques**
   These are the heavy-hitting developer tools for making AI calls robust and cheap.

   Constrained Decoding (Strict JSON): Instead of just asking the LLM to output JSON, use features like Gemini's response_schema. This physically blocks the AI from outputting markdown backticks or conversational filler, guaranteeing 100% valid data extraction.

   Prefix Caching: When looping through items (like rewriting 5 job experiences), put your static instructions and Job Description at the absolute top of the prompt, and the dynamic job entry at the very bottom. Gemini will "memorize" the top section after the first call, massively discounting the token cost for the rest of the loop.

   Batching: If you have many small tasks, group 2 or 3 of them into a single prompt. This prevents you from paying the "instruction tax" (the cost of the system prompt) on every single item.