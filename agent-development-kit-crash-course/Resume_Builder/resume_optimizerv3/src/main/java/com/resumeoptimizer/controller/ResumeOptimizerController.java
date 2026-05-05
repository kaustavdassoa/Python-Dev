package com.resumeoptimizer.controller;

import com.google.adk.agents.BaseAgent;
import com.google.adk.runner.InMemoryRunner;
import com.google.adk.sessions.Session;
import com.google.genai.types.Content;
import com.google.genai.types.Part;
import com.resumeoptimizer.pipeline.PipelineFactory;
import com.resumeoptimizer.tools.DocumentParserTools;
import com.resumeoptimizer.util.StateConstants;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * REST API controller for the Resume Optimizer pipeline.
 * Replaces Python's FastAPI main.py endpoints.
 */
@RestController
@RequestMapping("/api/v1")
public class ResumeOptimizerController {

    private static final Logger logger = LoggerFactory.getLogger(ResumeOptimizerController.class);
    private static final String OUTPUT_DIR = System.getProperty("output.directory", "./output");

    @PostMapping(value = "/resume/optimize", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Map<String, Object>> optimizeResume(
            @RequestParam("file") MultipartFile file,
            @RequestParam("job_description") String jobDescription) throws IOException {

        logger.info("Received optimization request: file={}, jdLength={}",
                file.getOriginalFilename(), jobDescription.length());

        // 1. Parse the uploaded document
        String rawResumeText = extractText(file);
        if (rawResumeText.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "Failed to extract text from uploaded file."));
        }

        // 2. Create pipeline and runner
        BaseAgent pipeline = PipelineFactory.createPipeline();
        InMemoryRunner runner = new InMemoryRunner(pipeline);

        // 3. Create session with initial state
        ConcurrentHashMap<String, Object> initialState = new ConcurrentHashMap<>();
        initialState.put(StateConstants.RAW_RESUME_TEXT, rawResumeText);
        initialState.put(StateConstants.RAW_JD_TEXT, jobDescription);

        Session session = runner.sessionService()
                .createSession(pipeline.name(), "api-user", initialState, null)
                .blockingGet();

        logger.info("Session created: {}", session.id());

        // 4. Run pipeline
        Content userContent = Content.fromParts(
                Part.fromText("Optimize this resume for the provided job description."));

        runner.runAsync("api-user", session.id(), userContent)
                .doOnNext(event -> logger.info("Event from {}: {}", event.author(),
                        event.content().map(c -> c.parts().map(parts ->
                                parts.isEmpty() ? "" : parts.get(0).text().orElse("")).orElse("")).orElse("")))
                .blockingSubscribe();

        // 5. Extract results from session state
        Map<String, Object> finalState = session.state();
        String htmlOutput = String.valueOf(finalState.getOrDefault(StateConstants.HTML_RENDERER_OUTPUT, ""));
        String report = String.valueOf(finalState.getOrDefault(StateConstants.FINAL_REPORT, ""));

        // 6. Save outputs
        Path outputPath = Path.of(OUTPUT_DIR);
        Files.createDirectories(outputPath);
        if (!htmlOutput.isEmpty()) {
            Files.writeString(outputPath.resolve("optimized_resume.html"), htmlOutput);
        }
        if (!report.isEmpty()) {
            Files.writeString(outputPath.resolve("optimization_report.md"), report);
        }

        // 7. Build response
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("status", Boolean.TRUE.equals(finalState.get(StateConstants.PIPELINE_HALTED)) ? "halted" : "success");
        response.put("session_id", session.id());
        response.put("report", report);
        response.put("html_length", htmlOutput.length());
        response.put("output_directory", outputPath.toAbsolutePath().toString());

        logger.info("Pipeline complete. Status: {}", response.get("status"));
        return ResponseEntity.ok(response);
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "ok", "version", "3.0.0", "framework", "Google ADK Java 1.2.0"));
    }

    private String extractText(MultipartFile file) throws IOException {
        String filename = file.getOriginalFilename();
        if (filename == null) return "";

        String ext = filename.substring(filename.lastIndexOf('.')).toLowerCase();
        byte[] bytes = file.getBytes();

        Map<String, Object> result = switch (ext) {
            case ".pdf" -> DocumentParserTools.parsePdf(bytes);
            case ".docx" -> DocumentParserTools.parseDocx(bytes);
            case ".txt" -> DocumentParserTools.parsePlainText(new String(bytes));
            default -> Map.of("success", false, "text", "", "error", "Unsupported file type: " + ext);
        };

        if (Boolean.TRUE.equals(result.get("success"))) {
            return String.valueOf(result.get("text"));
        }
        logger.error("Document extraction failed: {}", result.get("error"));
        return "";
    }
}
