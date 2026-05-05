package com.resumeoptimizer.pipeline;

import com.google.adk.agents.BaseAgent;
import com.google.adk.agents.Callbacks;
import com.google.adk.agents.CallbackContext;
import com.google.genai.types.Content;
import com.google.genai.types.Part;
import com.resumeoptimizer.util.StateConstants;
import io.reactivex.rxjava3.core.Maybe;

/**
 * Shared beforeAgentCallback that short-circuits any agent when the pipeline is halted.
 *
 * When registered on a sub-agent, if session state contains pipeline_halted=true,
 * this callback returns Content which causes ADK to set endInvocation=true,
 * skipping the agent's runAsyncImpl() entirely.
 *
 * This replaces the soft halt pattern where each agent checks the flag internally.
 */
public class PipelineHaltGuard implements Callbacks.BeforeAgentCallback {

    public static final PipelineHaltGuard INSTANCE = new PipelineHaltGuard();

    private PipelineHaltGuard() {}

    @Override
    public Maybe<Content> call(CallbackContext callbackContext) {
        Object halted = callbackContext.state().get(StateConstants.PIPELINE_HALTED);
        if (Boolean.TRUE.equals(halted)) {
            String reason = String.valueOf(
                    callbackContext.state().getOrDefault(
                            StateConstants.HALT_REASON, "Pipeline halted by upstream agent"));
            return Maybe.just(
                    Content.fromParts(Part.fromText("⏭️ Skipped: " + reason)));
        }
        return Maybe.empty();
    }
}
