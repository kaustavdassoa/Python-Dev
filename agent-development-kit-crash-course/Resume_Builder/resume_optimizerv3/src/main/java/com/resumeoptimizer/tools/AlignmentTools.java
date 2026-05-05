package com.resumeoptimizer.tools;

import java.util.*;
import java.util.regex.Pattern;

/**
 * Alignment Validator Tools — seniority ladder and domain overlap.
 * Direct port of Python's alignment_validator/tools.py.
 */
public final class AlignmentTools {

    private AlignmentTools() {}

    public static final Map<String, Integer> SENIORITY_LADDER = new LinkedHashMap<>();
    static {
        SENIORITY_LADDER.put("intern", 0); SENIORITY_LADDER.put("internship", 0);
        SENIORITY_LADDER.put("entry", 1); SENIORITY_LADDER.put("entry-level", 1);
        SENIORITY_LADDER.put("junior", 1); SENIORITY_LADDER.put("jr", 1);
        SENIORITY_LADDER.put("associate", 1); SENIORITY_LADDER.put("mid", 2);
        SENIORITY_LADDER.put("mid-level", 2); SENIORITY_LADDER.put("intermediate", 2);
        SENIORITY_LADDER.put("senior", 3); SENIORITY_LADDER.put("sr", 3);
        SENIORITY_LADDER.put("lead", 4); SENIORITY_LADDER.put("principal", 5);
        SENIORITY_LADDER.put("staff", 5); SENIORITY_LADDER.put("architect", 5);
        SENIORITY_LADDER.put("director", 6); SENIORITY_LADDER.put("vp", 7);
        SENIORITY_LADDER.put("vice president", 7); SENIORITY_LADDER.put("c-suite", 8);
        SENIORITY_LADDER.put("cto", 8); SENIORITY_LADDER.put("ceo", 8);
    }

    private static final Map<Integer, String> LEVEL_LABELS = Map.of(
            0, "Intern", 1, "Junior / Entry-Level", 2, "Mid-Level",
            3, "Senior", 4, "Lead", 5, "Principal / Staff",
            6, "Director", 7, "VP", 8, "C-Suite");

    private static final int MAX_GAP = 2;

    public static Map<String, Object> compareSeniorityLevels(
            String candidateLevel, String jdLevel, Integer jdScoreOverride) {
        int cScore = SENIORITY_LADDER.getOrDefault(candidateLevel.toLowerCase().strip(), 2);
        int jScore = (jdScoreOverride != null) ? jdScoreOverride
                : SENIORITY_LADDER.getOrDefault(jdLevel.toLowerCase().strip(), 2);
        int gap = Math.abs(jScore - cScore);
        String direction = gap == 0 ? "match" : (jScore > cScore ? "under-qualified" : "over-qualified");
        boolean isAcceptable = gap <= MAX_GAP;
        Map<String, Object> r = new LinkedHashMap<>();
        r.put("candidate_score", cScore); r.put("jd_score", jScore);
        r.put("candidate_label", LEVEL_LABELS.getOrDefault(cScore, candidateLevel));
        r.put("jd_label", LEVEL_LABELS.getOrDefault(jScore, jdLevel));
        r.put("gap", gap); r.put("direction", direction);
        r.put("is_acceptable", isAcceptable);
        r.put("verdict", isAcceptable ? "aligned" : "rejected");
        return r;
    }

    public static Map<String, Object> checkDomainAlignment(String resumeSkillsCsv, String jdRequiredSkillsCsv) {
        List<String> resumeList = splitAndLower(resumeSkillsCsv);
        List<String> jdList = splitAndLower(jdRequiredSkillsCsv);
        if (jdList.isEmpty()) {
            return Map.of("overlap_count", 0, "overlap_pct", 100.0,
                    "is_domain_match", true, "matched_skills", List.of(), "unmatched_jd_skills", List.of());
        }
        List<String> matched = new ArrayList<>(), unmatched = new ArrayList<>();
        for (String jdSkill : jdList) {
            boolean found = resumeList.stream().anyMatch(r -> jdSkill.contains(r) || r.contains(jdSkill));
            (found ? matched : unmatched).add(jdSkill);
        }
        double overlapPct = (matched.size() / (double) jdList.size()) * 100;
        Map<String, Object> r = new LinkedHashMap<>();
        r.put("overlap_count", matched.size());
        r.put("overlap_pct", Math.round(overlapPct * 10.0) / 10.0);
        r.put("is_domain_match", overlapPct >= 15.0);
        r.put("matched_skills", matched); r.put("unmatched_jd_skills", unmatched);
        return r;
    }

    private static List<String> splitAndLower(String csv) {
        if (csv == null || csv.isBlank()) return List.of();
        return Arrays.stream(csv.split(",")).map(String::strip).map(String::toLowerCase)
                .filter(s -> !s.isEmpty()).toList();
    }
}
