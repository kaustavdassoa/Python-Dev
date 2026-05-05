package com.resumeoptimizer.agents;

import com.github.jknack.handlebars.Handlebars;
import com.github.jknack.handlebars.Template;
import com.resumeoptimizer.pipeline.DeterministicAgent;
import com.resumeoptimizer.util.JsonExtractor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

/**
 * Agent 8 of 9 — HTML Renderer (DeterministicAgent).
 * Converts rewritten resume JSON into styled HTML using Handlebars.
 */
public final class HtmlRendererAgent extends DeterministicAgent {

    private static final Logger logger = LoggerFactory.getLogger(HtmlRendererAgent.class);

    private HtmlRendererAgent() {
        super("HTMLRendererAgent",
              "Converts rewritten resume to a styled HTML document.",
              "html_renderer_output");
    }

    public static HtmlRendererAgent create() { return new HtmlRendererAgent(); }

    @Override
    protected Object execute(Map<String, Object> state) {
        Map<String, Object> rewriterOut = JsonExtractor.getDictFromState(state.get("rewriter_output"));

        // Ensure defaults
        if (!(rewriterOut.get("contact") instanceof Map)) {
            rewriterOut.put("contact", Map.of("name", "", "email", "", "phone", "", "location", "", "linkedin", ""));
        }
        rewriterOut.putIfAbsent("summary", "");
        rewriterOut.putIfAbsent("skills", List.of());
        rewriterOut.putIfAbsent("experience", List.of());
        rewriterOut.putIfAbsent("education", List.of());
        rewriterOut.putIfAbsent("certifications", List.of());

        try {
            Handlebars handlebars = new Handlebars();
            // Register eq helper for entry_type comparison
            handlebars.registerHelper("eq", (a, options) -> {
                String param = options.param(0).toString();
                return a != null && a.toString().equals(param) ? options.fn() : options.inverse();
            });

            Template template = handlebars.compile("templates/resume");
            String html = template.apply(rewriterOut);
            logger.info("HTML rendered successfully ({} chars)", html.length());
            return html;
        } catch (Exception e) {
            throw new RuntimeException("HTML Rendering Failed: " + e.getMessage(), e);
        }
    }
}
