package com.resumeoptimizer;

import com.google.adk.agents.BaseAgent;
import com.resumeoptimizer.pipeline.PipelineFactory;

/**
 * ADK Dev UI entry point — equivalent of Python's `adk web`.
 * Launches the interactive Dev UI for testing the pipeline.
 *
 * Usage: java -cp ... com.resumeoptimizer.AdkDevServer
 */
import java.io.InputStream;
import java.util.Properties;

public class AdkDevServer {

    public static void main(String[] args) {
        String modelName = "gemini-2.5-flash";
        try (InputStream is = AdkDevServer.class.getResourceAsStream("/application.properties")) {
            if (is != null) {
                Properties props = new Properties();
                props.load(is);
                modelName = props.getProperty("model.name", modelName);
            }
        } catch (Exception e) {
            System.err.println("Could not load application.properties, using default model.");
        }

        BaseAgent pipeline = PipelineFactory.createPipeline(modelName);

        // The ADK Dev UI server — uncomment when google-adk-dev is on classpath
        // com.google.adk.dev.AdkWebServer.start(pipeline);

        System.out.println("Pipeline created: " + pipeline.name());
        System.out.println("Sub-agents: " + pipeline.subAgents().size());
        System.out.println("\nTo start the ADK Dev UI, ensure google-adk-dev is on classpath");
        System.out.println("and uncomment the AdkWebServer.start() call.");
    }
}
