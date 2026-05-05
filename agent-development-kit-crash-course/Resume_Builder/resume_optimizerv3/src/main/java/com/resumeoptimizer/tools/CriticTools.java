package com.resumeoptimizer.tools;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Critic Tools — page length estimation and keyword stuffing detection.
 * Direct port of Python's critic/tools.py.
 */
public final class CriticTools {

    private CriticTools() {}

    public static Map<String, Object> estimatePageLength(String rewrittenResumeText) {
        int wordCount = rewrittenResumeText.split("\\s+").length;
        double estimatedPages = Math.round((wordCount / 400.0) * 10.0) / 10.0;
        String status, message;
        if (estimatedPages < 0.4) {
            status = "too_short";
            message = String.format("Estimated %.1f pages (%d words). Resume may be too brief.", estimatedPages, wordCount);
        } else if (estimatedPages > 2.3) {
            status = "too_long";
            message = String.format("Estimated %.1f pages (%d words). Resume exceeds 2-page limit.", estimatedPages, wordCount);
        } else {
            status = "ok";
            message = String.format("Estimated %.1f pages (%d words). Within 1-2 page target. ✅", estimatedPages, wordCount);
        }
        Map<String, Object> r = new LinkedHashMap<>();
        r.put("word_count", wordCount); r.put("estimated_pages", estimatedPages);
        r.put("status", status); r.put("message", message);
        return r;
    }

    public static Map<String, Object> detectKeywordStuffing(String rewrittenResumeText, String jdKeywordsCsv) {
        List<String> keywords = Arrays.stream(jdKeywordsCsv.split(","))
                .map(String::strip).map(String::toLowerCase).filter(s -> !s.isEmpty()).toList();
        String textLower = rewrittenResumeText.toLowerCase();
        List<Map<String, Object>> stuffed = new ArrayList<>();
        for (String keyword : keywords) {
            Matcher m = Pattern.compile("\\b" + Pattern.quote(keyword) + "\\b").matcher(textLower);
            int count = 0; while (m.find()) count++;
            if (count > 4) stuffed.add(Map.of("keyword", keyword, "count", count));
        }
        return Map.of("has_stuffing", !stuffed.isEmpty(), "stuffed_keywords", stuffed);
    }
}
