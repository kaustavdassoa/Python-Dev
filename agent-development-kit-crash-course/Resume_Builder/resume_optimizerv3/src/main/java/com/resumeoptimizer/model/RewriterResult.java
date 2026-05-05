package com.resumeoptimizer.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * The full rewritten resume structure — used as the structured output schema
 * for the ResumeRewriterAgent (Path A single-shot generation).
 */
public record RewriterResult(
    @JsonProperty("contact") ContactInfo contact,
    @JsonProperty("summary") String summary,
    @JsonProperty("skills") List<String> skills,
    @JsonProperty("experience") List<ExperienceEntry> experience,
    @JsonProperty("education") List<EducationEntry> education,
    @JsonProperty("certifications") List<String> certifications,
    @JsonProperty("changes_summary") List<String> changesSummary,
    @JsonProperty("keywords_injected") List<String> keywordsInjected
) {}
