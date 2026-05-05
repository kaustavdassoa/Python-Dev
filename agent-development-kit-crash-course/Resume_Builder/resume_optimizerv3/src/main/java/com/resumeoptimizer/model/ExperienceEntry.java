package com.resumeoptimizer.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * A single experience entry in a resume (job, project, or volunteer).
 */
public record ExperienceEntry(
    @JsonProperty("title") String title,
    @JsonProperty("company") String company,
    @JsonProperty("dates") String dates,
    @JsonProperty("bullets") List<String> bullets,
    @JsonProperty("entry_type") String entryType
) {}
