package com.resumeoptimizer.tools;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * ATS Tools — formatting detection and keyword scoring.
 * Direct port of ats_precheck/tools.py and ats_scorer/tools.py.
 */
public final class AtsTools {

    private AtsTools() {}

    public static Map<String, Object> detectAtsUnfriendlyFormatting(String resumeText) {
        List<Map<String, String>> warnings = new ArrayList<>();
        int tabCount = countMatches(resumeText, "\\t{2,}|\\s{6,}");
        if (tabCount > 5) warnings.add(Map.of("type", "multi_column", "severity", "critical",
                "message", "Possible multi-column layout detected (excessive tabs/spaces)."));
        if (Pattern.compile("\\|.{3,}\\|").matcher(resumeText).find())
            warnings.add(Map.of("type", "table", "severity", "critical",
                    "message", "Table structure detected (pipe characters)."));
        Matcher specialMatcher = Pattern.compile("[•◦▪▸►→■□✓✗✦★☆❖◆]").matcher(resumeText);
        Set<String> specialChars = new HashSet<>();
        while (specialMatcher.find()) specialChars.add(specialMatcher.group());
        if (!specialChars.isEmpty()) warnings.add(Map.of("type", "special_characters", "severity", "warning",
                "message", "Special bullet/arrow characters found: " + specialChars));
        String[] lines = Arrays.stream(resumeText.split("\n")).map(String::strip).filter(l -> !l.isEmpty()).toArray(String[]::new);
        if (lines.length > 0 && lines[0].length() > 3) {
            long count = Arrays.stream(lines).filter(l -> l.equals(lines[0])).count();
            if (count > 1) warnings.add(Map.of("type", "repeated_header", "severity", "warning",
                    "message", "First line appears more than once — possible repeated header/footer."));
        }
        int wordCount = resumeText.split("\\s+").length;
        if (wordCount < 100) warnings.add(Map.of("type", "insufficient_content", "severity", "critical",
                "message", "Only " + wordCount + " words extracted. Possible parsing failure."));
        long criticalCount = warnings.stream().filter(w -> "critical".equals(w.get("severity"))).count();
        return Map.of("has_warnings", !warnings.isEmpty(), "warning_count", warnings.size(),
                "critical_count", (int) criticalCount, "warnings", warnings);
    }

    public static Map<String, Object> calculateAtsScore(String resumeText, String jdKeywordsCsv) {
        List<String> jdKeywords = splitAndLower(jdKeywordsCsv);
        if (jdKeywords.isEmpty()) return Map.of("score", 0, "matched_keywords", List.of(),
                "missing_keywords", List.of(), "total_jd_keywords", 0);
        String resumeLower = resumeText.toLowerCase();
        List<String> matched = new ArrayList<>(), missing = new ArrayList<>();
        for (String kw : jdKeywords) (resumeLower.contains(kw) ? matched : missing).add(kw);
        int score = (int) ((matched.size() / (double) jdKeywords.size()) * 100);
        return Map.of("score", score, "matched_keywords", matched,
                "missing_keywords", missing, "total_jd_keywords", jdKeywords.size());
    }

    public static Map<String, Object> calculateAtsScoreAfter(String rewrittenText, String jdKeywordsCsv) {
        List<String> jdKeywords = splitAndLower(jdKeywordsCsv);
        if (jdKeywords.isEmpty()) return Map.of("score_after", 0, "matched_keywords", List.of(),
                "still_missing_keywords", List.of(), "total_jd_keywords", 0);
        String textLower = rewrittenText.toLowerCase();
        List<String> matched = new ArrayList<>(), stillMissing = new ArrayList<>();
        for (String kw : jdKeywords) (textLower.contains(kw) ? matched : stillMissing).add(kw);
        int score = (int) ((matched.size() / (double) jdKeywords.size()) * 100);
        return Map.of("score_after", score, "matched_keywords", matched,
                "still_missing_keywords", stillMissing, "total_jd_keywords", jdKeywords.size());
    }

    private static int countMatches(String text, String regex) {
        Matcher m = Pattern.compile(regex).matcher(text);
        int count = 0; while (m.find()) count++;
        return count;
    }

    private static List<String> splitAndLower(String csv) {
        if (csv == null || csv.isBlank()) return List.of();
        return Arrays.stream(csv.split(",")).map(String::strip).map(String::toLowerCase)
                .filter(s -> !s.isEmpty()).toList();
    }
}
