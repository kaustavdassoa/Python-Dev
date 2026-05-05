package com.resumeoptimizer.model;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Contact information extracted from a resume.
 */
public record ContactInfo(
    @JsonProperty("name") String name,
    @JsonProperty("email") String email,
    @JsonProperty("phone") String phone,
    @JsonProperty("location") String location,
    @JsonProperty("linkedin") String linkedin
) {}
