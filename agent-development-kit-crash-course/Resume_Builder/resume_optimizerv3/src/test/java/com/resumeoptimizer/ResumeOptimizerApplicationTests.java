package com.resumeoptimizer;

import com.google.adk.agents.SequentialAgent;
import com.resumeoptimizer.pipeline.PipelineFactory;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Basic tests to verify project structure and pipeline assembly.
 */
class ResumeOptimizerApplicationTests {

    @Test
    void pipelineFactoryCreatesValidSequentialAgent() {
        SequentialAgent pipeline = PipelineFactory.createPipeline("gemini-2.5-flash");

        assertNotNull(pipeline);
        assertEquals("ResumeOptimizerPipeline", pipeline.name());
        assertEquals(9, pipeline.subAgents().size());
    }

    @Test
    void agentNamesAreCorrect() {
        SequentialAgent pipeline = PipelineFactory.createPipeline("gemini-2.5-flash");
        var names = pipeline.subAgents().stream()
                .map(a -> a.name())
                .toList();

        assertEquals("DocumentParserAgent", names.get(0));
        assertEquals("JdAnalyzerAgent", names.get(1));
        assertEquals("AlignmentValidatorAgent", names.get(2));
        assertEquals("ATSPreCheckAgent", names.get(3));
        assertEquals("ResumeRewriterAgent", names.get(4));
        assertEquals("ATSScorerAgent", names.get(5));
        assertEquals("CriticAgent", names.get(6));
        assertEquals("HTMLRendererAgent", names.get(7));
        assertEquals("ReportGeneratorAgent", names.get(8));
    }
}
