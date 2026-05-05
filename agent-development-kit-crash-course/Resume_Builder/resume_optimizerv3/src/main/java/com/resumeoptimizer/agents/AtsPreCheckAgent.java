package com.resumeoptimizer.agents;

import com.resumeoptimizer.pipeline.DeterministicAgent;
import com.resumeoptimizer.tools.AtsTools;
import com.resumeoptimizer.util.JsonExtractor;

import java.util.*;

/**
 * Agent 4 of 9 — ATS Pre-Check (DeterministicAgent).
 * Detects ATS-unfriendly formatting and calculates BEFORE keyword score.
 */
public final class AtsPreCheckAgent extends DeterministicAgent {

    private AtsPreCheckAgent() {
        super("ATSPreCheckAgent",
              "Detects ATS-unfriendly formatting and calculates BEFORE keyword score.",
              "ats_precheck_output");
    }

    public static AtsPreCheckAgent create() { return new AtsPreCheckAgent(); }

    @Override
    @SuppressWarnings("unchecked")
    protected Object execute(Map<String, Object> state) {
        Map<String, Object> jdOut = JsonExtractor.getDictFromState(state.get("jd_analysis_output"));
        String rawText = String.valueOf(state.getOrDefault("raw_resume_text", ""));
        List<String> keywords = (List<String>) jdOut.getOrDefault("top_keywords", List.of());
        String jdKeywordsCsv = String.join(",", keywords);

        Map<String, Object> formattingCheck = AtsTools.detectAtsUnfriendlyFormatting(rawText);
        Map<String, Object> scoreResult = AtsTools.calculateAtsScore(rawText, jdKeywordsCsv);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("formatting_check", formattingCheck);
        result.put("ats_score_before", scoreResult.get("score"));
        result.put("matched_keywords_before", scoreResult.get("matched_keywords"));
        result.put("missing_keywords", scoreResult.get("missing_keywords"));
        result.put("total_jd_keywords", scoreResult.get("total_jd_keywords"));
        return result;
    }
}
