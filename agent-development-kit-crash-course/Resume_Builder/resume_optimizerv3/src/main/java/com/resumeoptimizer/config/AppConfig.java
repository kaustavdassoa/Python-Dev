package com.resumeoptimizer.config;

import io.github.cdimascio.dotenv.Dotenv;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;

/**
 * Loads environment variables from .env file at startup.
 * ADK Java reads GOOGLE_API_KEY from the JVM's system environment,
 * so we must set it as a system property before the first LLM call.
 */
@Configuration
public class AppConfig {

    private static final Logger logger = LoggerFactory.getLogger(AppConfig.class);

    @PostConstruct
    public void loadEnv() {
        // dotenv-java reads .env from the project root
        Dotenv dotenv = Dotenv.configure()
                .ignoreIfMissing()
                .load();

        // Propagate .env values into JVM system properties
        // ADK Java checks System.getenv() first, then system properties
        setIfPresent(dotenv, "GOOGLE_API_KEY");
        setIfPresent(dotenv, "GOOGLE_GENAI_USE_VERTEXAI");
        setIfPresent(dotenv, "MODEL_NAME");

        String apiKey = dotenv.get("GOOGLE_API_KEY", System.getenv("GOOGLE_API_KEY"));
        if (apiKey == null || apiKey.isBlank() || apiKey.equals("YOUR_API_KEY_HERE")) {
            logger.error("⚠️  GOOGLE_API_KEY is not set! Set it in .env or as an environment variable.");
            logger.error("   Get your key at: https://aistudio.google.com/app/apikey");
        } else {
            logger.info("✅ GOOGLE_API_KEY loaded ({} chars, starts with {}...)",
                    apiKey.length(), apiKey.substring(0, Math.min(8, apiKey.length())));
        }
    }

    private void setIfPresent(Dotenv dotenv, String key) {
        String value = dotenv.get(key);
        if (value != null && !value.isBlank()) {
            System.setProperty(key, value);
        }
    }
}
