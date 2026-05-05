package com.resumeoptimizer.pipeline;

/**
 * Custom exception for pipeline hard gate failures.
 * Replaces Python's AbortPipelineError.
 */
public class AbortPipelineException extends RuntimeException {

    public AbortPipelineException(String message) {
        super(message);
    }

    public AbortPipelineException(String message, Throwable cause) {
        super(message, cause);
    }
}
