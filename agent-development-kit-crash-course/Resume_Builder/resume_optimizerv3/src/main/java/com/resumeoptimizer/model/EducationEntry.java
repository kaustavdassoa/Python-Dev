package com.resumeoptimizer.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * A single education entry in a resume.
 */
public record EducationEntry(
    @JsonProperty("degree") String degree,
    @JsonProperty("institution") String institution,
    @JsonProperty("year") String year
) {}
