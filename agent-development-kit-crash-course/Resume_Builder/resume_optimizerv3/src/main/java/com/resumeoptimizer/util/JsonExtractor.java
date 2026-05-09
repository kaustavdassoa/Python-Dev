package com.resumeoptimizer.util;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Multi-strategy JSON extractor for LLM output.
 * Mirrors shared/utils.py get_dict_from_state() from the Python codebase.
 *
 * LLM responses may arrive as:
 *   - A plain Map (already parsed by ADK)
 *   - A raw JSON string
 *   - A markdown-wrapped JSON string (```json ... ```)
 */
public final class JsonExtractor {

    private static final Logger logger = LoggerFactory.getLogger(JsonExtractor.class);
    private static final ObjectMapper MAPPER = new ObjectMapper();

    // Pattern for markdown code-block extraction (greedy)
    private static final Pattern MARKDOWN_BLOCK = Pattern.compile(
            "```(?:json)?\\s*(\\{.*})\\s*```", Pattern.DOTALL);

    private JsonExtractor() {}

    /**
     * Extract a Map from a raw state value using multiple strategies.
     *
     * @param val The raw value read from session state.
     * @return Parsed map, or empty map if all strategies fail.
     */
    @SuppressWarnings("unchecked")
    public static Map<String, Object> getDictFromState(Object val) {
        if (val == null) {
            return new HashMap<>();
        }

        // Already a Map
        if (val instanceof Map) {
            return (Map<String, Object>) val;
        }

        if (val instanceof String text) {
            // Strategy 1: Markdown code-block extraction
            Matcher matcher = MARKDOWN_BLOCK.matcher(text);
            if (matcher.find()) {
                try {
                    return MAPPER.readValue(matcher.group(1), Map.class);
                } catch (JsonProcessingException e) {
                    logger.debug("Markdown block extraction failed: {}", e.getMessage());
                }
            }

            // Strategy 2: Outermost brace matching
            int firstBrace = text.indexOf('{');
            int lastBrace = text.lastIndexOf('}');
            if (firstBrace != -1 && lastBrace > firstBrace) {
                String candidate = text.substring(firstBrace, lastBrace + 1);
                try {
                    return MAPPER.readValue(candidate, Map.class);
                } catch (JsonProcessingException e) {
                    logger.debug("Brace matching extraction failed: {}", e.getMessage());
                }
            }

            // Strategy 3: Raw string parse
            try {
                return MAPPER.readValue(text.strip(), Map.class);
            } catch (JsonProcessingException e) {
                logger.debug("Raw JSON parse failed: {}", e.getMessage());
            }

            logger.warn("getDictFromState: all strategies failed (input length={}, preview={})",
                    text.length(), text.substring(0, Math.min(100, text.length())));
        }

        return new HashMap<>();
    }

    /**
     * Parse a JSON string into a JsonNode tree.
     */
    public static JsonNode parseJson(String json) throws JsonProcessingException {
        return MAPPER.readTree(json);
    }

    /**
     * Serialize an object to JSON string.
     */
    public static String toJson(Object obj) throws JsonProcessingException {
        return MAPPER.writeValueAsString(obj);
    }

    /**
     * Get the shared ObjectMapper instance.
     */
    public static ObjectMapper mapper() {
        return MAPPER;
    }
}
