package com.resumeoptimizer;

import com.google.adk.agents.BaseAgent;
import com.resumeoptimizer.pipeline.PipelineFactory;

/**
 * ADK Dev UI entry point — equivalent of Python's `adk web`.
 * Launches the interactive Dev UI for testing the pipeline.
 *
 * Usage: java -cp ... com.resumeoptimizer.AdkDevServer
 */
public class AdkDevServer {

    public static void main(String[] args) {
        BaseAgent pipeline = PipelineFactory.createPipeline();

        // The ADK Dev UI server — uncomment when google-adk-dev is on classpath
        // com.google.adk.dev.AdkWebServer.start(pipeline);

        System.out.println("Pipeline created: " + pipeline.name());
        System.out.println("Sub-agents: " + pipeline.subAgents().size());
        System.out.println("\nTo start the ADK Dev UI, ensure google-adk-dev is on classpath");
        System.out.println("and uncomment the AdkWebServer.start() call.");
    }
}
