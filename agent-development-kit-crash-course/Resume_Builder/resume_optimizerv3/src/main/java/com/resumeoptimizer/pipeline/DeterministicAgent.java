package com.resumeoptimizer.pipeline;

import com.google.adk.agents.BaseAgent;
import com.google.adk.agents.InvocationContext;
import com.google.adk.events.Event;
import com.google.adk.events.EventActions;
import com.google.genai.types.Content;
import com.google.genai.types.Part;
import com.resumeoptimizer.util.StateConstants;
import io.reactivex.rxjava3.core.Flowable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Abstract base class for deterministic (non-LLM) pipeline agents.
 * Replaces Python's PythonTaskNode pattern.
 *
 * Subclasses implement {@link #execute(Map)} with pure Java logic.
 * The result is stored in session state under the configured outputKey.
 *
 * If the pipeline has been halted by an upstream agent, execution is skipped.
 */
public abstract class DeterministicAgent extends BaseAgent {

    private static final Logger logger = LoggerFactory.getLogger(DeterministicAgent.class);

    private final String outputKey;

    protected DeterministicAgent(String name, String description, String outputKey) {
        super(name, description, List.of(), List.of(), List.of());
        this.outputKey = outputKey;
    }

    /**
     * Implement deterministic logic here.
     *
     * @param state The current session state (read-only view recommended).
     * @return The result object to store under outputKey.
     * @throws AbortPipelineException to halt the pipeline (hard gate).
     */
    protected abstract Object execute(Map<String, Object> state);

    @Override
    protected Flowable<Event> runAsyncImpl(InvocationContext invocationContext) {
        return Flowable.defer(() -> {
            Map<String, Object> state = invocationContext.session().state();

            // Check pipeline halt flag
            if (Boolean.TRUE.equals(state.get(StateConstants.PIPELINE_HALTED))) {
                logger.info("⏭️ Skipping {} — pipeline halted", name());
                return Flowable.empty();
            }

            Map<String, Object> stateDelta = new HashMap<>();
            String message;

            try {
                Object result = execute(state);
                stateDelta.put(outputKey, result);
                message = "✅ " + name() + " completed successfully.";
                logger.info(message);
            } catch (AbortPipelineException e) {
                stateDelta.put(StateConstants.PIPELINE_HALTED, true);
                stateDelta.put(StateConstants.HALT_REASON, e.getMessage());
                message = "🛑 " + name() + " halted pipeline: " + e.getMessage();
                logger.warn(message);
            } catch (Exception e) {
                stateDelta.put(StateConstants.PIPELINE_HALTED, true);
                stateDelta.put(StateConstants.HALT_REASON, name() + " error: " + e.getMessage());
                message = "❌ " + name() + " failed: " + e.getMessage();
                logger.error(message, e);
            }

            Event event = Event.builder()
                    .id(Event.generateEventId())
                    .invocationId(invocationContext.invocationId())
                    .author(name())
                    .actions(EventActions.builder().stateDelta(stateDelta).build())
                    .content(Content.fromParts(Part.fromText(message)))
                    .build();

            return Flowable.just(event);
        });
    }

    @Override
    protected Flowable<Event> runLiveImpl(InvocationContext invocationContext) {
        return runAsyncImpl(invocationContext);
    }
}
