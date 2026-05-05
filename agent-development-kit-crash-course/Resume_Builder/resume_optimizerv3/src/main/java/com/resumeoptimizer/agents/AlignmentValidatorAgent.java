package com.resumeoptimizer.agents;

import com.resumeoptimizer.pipeline.AbortPipelineException;
import com.resumeoptimizer.pipeline.DeterministicAgent;
import com.resumeoptimizer.tools.AlignmentTools;
import com.resumeoptimizer.util.JsonExtractor;

import java.util.*;

/**
 * Agent 3 of 9 — Alignment Validator (DeterministicAgent — HARD GATE).
 * Throws AbortPipelineException if career level gap is too large.
 */
public final class AlignmentValidatorAgent extends DeterministicAgent {

    private AlignmentValidatorAgent() {
        super("AlignmentValidatorAgent",
              "HARD GATE: validates career-level and domain alignment between resume and JD.",
              "alignment_validator_output");
    }

    public static AlignmentValidatorAgent create() { return new AlignmentValidatorAgent(); }

    @Override
    @SuppressWarnings("unchecked")
    protected Object execute(Map<String, Object> state) {
        Map<String, Object> docOut = JsonExtractor.getDictFromState(state.get("document_parser_output"));
        Map<String, Object> jdOut = JsonExtractor.getDictFromState(state.get("jd_analysis_output"));

        Map<String, Object> resumeSections = JsonExtractor.getDictFromState(docOut.get("resume_sections"));
        List<Map<String, Object>> experience = (List<Map<String, Object>>) resumeSections.getOrDefault("experience", List.of());
        List<String> skillsList = (List<String>) resumeSections.getOrDefault("skills", List.of());
        String resumeSkillsCsv = String.join(",", skillsList);
        String candidateLevel = inferSeniorityFromExperience(experience);

        String jdLevel = String.valueOf(jdOut.getOrDefault("seniority_level", "mid"));
        Object jdLevelScoreObj = jdOut.get("level_score");
        Integer jdLevelScore = jdLevelScoreObj instanceof Number n ? n.intValue() : null;
        List<String> jdRequiredSkills = (List<String>) jdOut.getOrDefault("required_skills",
                jdOut.getOrDefault("top_keywords", List.of()));
        String jdRequiredSkillsCsv = String.join(",", jdRequiredSkills);

        Map<String, Object> seniorityResult = AlignmentTools.compareSeniorityLevels(candidateLevel, jdLevel, jdLevelScore);
        Map<String, Object> domainResult = AlignmentTools.checkDomainAlignment(resumeSkillsCsv, jdRequiredSkillsCsv);

        boolean isAcceptable = Boolean.TRUE.equals(seniorityResult.get("is_acceptable"))
                && Boolean.TRUE.equals(domainResult.get("is_domain_match"));

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("alignment_result", isAcceptable ? "pass" : "reject");
        result.put("candidate_level", candidateLevel);
        result.put("candidate_label", seniorityResult.getOrDefault("candidate_label", ""));
        result.put("jd_level", jdLevel);
        result.put("jd_label", seniorityResult.getOrDefault("jd_label", ""));
        result.put("seniority_gap", seniorityResult.getOrDefault("gap", 0));
        result.put("domain_overlap_pct", domainResult.getOrDefault("overlap_pct", 0.0));
        result.put("matched_skills", domainResult.getOrDefault("matched_skills", List.of()));

        if (!isAcceptable) {
            List<String> reasons = new ArrayList<>();
            if (!Boolean.TRUE.equals(seniorityResult.get("is_acceptable"))) reasons.add("seniority_gap_too_large");
            if (!Boolean.TRUE.equals(domainResult.get("is_domain_match"))) reasons.add("low_domain_overlap");
            String reason = String.join(", ", reasons);
            result.put("rejection_reason", reason);
            throw new AbortPipelineException(String.format(
                    "Alignment check failed: %s. Candidate: %s. JD: %s. Domain overlap: %s%%",
                    reason, candidateLevel, jdLevel, domainResult.getOrDefault("overlap_pct", 0.0)));
        }
        result.put("verdict", "Resume is alignable with the job description.");
        return result;
    }

    private static String inferSeniorityFromExperience(List<Map<String, Object>> experienceList) {
        int maxScore = -1;
        String bestLevel = "entry";
        for (Map<String, Object> exp : experienceList) {
            String title = String.valueOf(exp.getOrDefault("title", "")).toLowerCase();
            if (title.isEmpty()) continue;
            for (Map.Entry<String, Integer> entry : AlignmentTools.SENIORITY_LADDER.entrySet()) {
                if (title.contains(entry.getKey()) && entry.getValue() > maxScore) {
                    maxScore = entry.getValue();
                    bestLevel = entry.getKey();
                }
            }
        }
        return bestLevel;
    }
}
