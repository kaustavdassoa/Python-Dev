package com.resumeoptimizer.agents;

import com.resumeoptimizer.pipeline.DeterministicAgent;
import com.resumeoptimizer.tools.AtsTools;
import com.resumeoptimizer.util.JsonExtractor;

import java.util.*;

/**
 * Agent 6 of 9 — ATS Scorer AFTER (DeterministicAgent).
 * Re-scores the rewritten resume against JD keywords.
 */
public final class AtsScorerAgent extends DeterministicAgent {

    private AtsScorerAgent() {
        super("ATSScorerAgent",
              "Re-scores the rewritten resume and calculates ATS score delta.",
              "ats_scorer_output");
    }

    public static AtsScorerAgent create() { return new AtsScorerAgent(); }

    @Override
    @SuppressWarnings("unchecked")
    protected Object execute(Map<String, Object> state) {
        Map<String, Object> rewriterOut = JsonExtractor.getDictFromState(state.get("rewriter_output"));
        Map<String, Object> jdOut = JsonExtractor.getDictFromState(state.get("jd_analysis_output"));
        Map<String, Object> precheckOut = JsonExtractor.getDictFromState(state.get("ats_precheck_output"));

        // Build combined text from rewritten resume
        StringBuilder combinedParts = new StringBuilder();
        combinedParts.append(rewriterOut.getOrDefault("summary", "")).append(" ");
        Object skillsObj = rewriterOut.getOrDefault("skills", List.of());
        if (skillsObj instanceof List<?> skillsList) {
            combinedParts.append(String.join(" ", skillsList.stream().map(String::valueOf).toList())).append(" ");
        }
        Object expObj = rewriterOut.getOrDefault("experience", List.of());
        if (expObj instanceof List<?> expList) {
            for (Object e : expList) {
                if (e instanceof Map<?, ?> exp) {
                    Object bullets = exp.get("bullets");
                    if (bullets instanceof List<?> bulletList) {
                        combinedParts.append(String.join(" ", bulletList.stream().map(String::valueOf).toList())).append(" ");
                    }
                }
            }
        }
        Object certsObj = rewriterOut.getOrDefault("certifications", List.of());
        if (certsObj instanceof List<?> certsList) {
            combinedParts.append(String.join(" ", certsList.stream().map(String::valueOf).toList()));
        }

        List<String> keywords = (List<String>) jdOut.getOrDefault("top_keywords", List.of());
        String jdKeywordsCsv = String.join(",", keywords);

        Map<String, Object> scoreResult = AtsTools.calculateAtsScoreAfter(combinedParts.toString(), jdKeywordsCsv);

        int scoreBefore = precheckOut.get("ats_score_before") instanceof Number n ? n.intValue() : 0;
        int scoreAfter = scoreResult.get("score_after") instanceof Number n ? n.intValue() : 0;
        int delta = scoreAfter - scoreBefore;
        String deltaStr = (delta >= 0 ? "+" : "") + delta + " points";

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("ats_score_before", scoreBefore);
        result.put("ats_score_after", scoreAfter);
        result.put("score_delta", deltaStr);
        result.put("matched_keywords_after", scoreResult.get("matched_keywords"));
        result.put("still_missing_keywords", scoreResult.get("still_missing_keywords"));
        result.put("total_jd_keywords", scoreResult.get("total_jd_keywords"));
        return result;
    }
}
