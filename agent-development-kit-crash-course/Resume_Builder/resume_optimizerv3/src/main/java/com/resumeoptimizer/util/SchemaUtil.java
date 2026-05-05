package com.resumeoptimizer.util;

import com.fasterxml.jackson.databind.JsonNode;
import com.github.victools.jsonschema.generator.*;
import com.github.victools.jsonschema.module.jackson.JacksonModule;
import com.github.victools.jsonschema.module.jackson.JacksonOption;

/**
 * Generates JSON Schema from Jackson-annotated POJOs at runtime.
 * Replaces Pydantic's model_json_schema() for Gemini's response_schema config.
 */
public final class SchemaUtil {

    private static final SchemaGenerator GENERATOR;

    static {
        JacksonModule module = new JacksonModule(JacksonOption.RESPECT_JSONPROPERTY_REQUIRED);
        SchemaGeneratorConfig config = new SchemaGeneratorConfigBuilder(
                SchemaVersion.DRAFT_2020_12, OptionPreset.PLAIN_JSON)
                .with(module)
                .build();
        GENERATOR = new SchemaGenerator(config);
    }

    private SchemaUtil() {}

    /**
     * Generate a JSON Schema from a Java class (record, POJO, etc.).
     *
     * @param pojoClass The class to generate schema for.
     * @return JsonNode representing the JSON Schema.
     */
    public static JsonNode generateSchema(Class<?> pojoClass) {
        return GENERATOR.generateSchema(pojoClass);
    }

    /**
     * Generate a JSON Schema as a string.
     */
    public static String generateSchemaString(Class<?> pojoClass) {
        return GENERATOR.generateSchema(pojoClass).toPrettyString();
    }
}
