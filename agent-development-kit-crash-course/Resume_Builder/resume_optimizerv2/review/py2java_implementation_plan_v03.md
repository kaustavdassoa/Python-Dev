# Python to Java Migration — Resume Optimizer v3 (ADK Java) — Rev 2

Migrate the 9-agent pipeline from **Python ADK** to **Java ADK** (`google/adk-java` v1.2.0).

**Rev 2 Changes**: Addresses all 5 architectural review items from user feedback.

---

## Rev 2 Changelog (vs Rev 1)

| # | Feedback | Rev 1 (Old) | Rev 2 (New) |
|---|----------|-------------|-------------|
| 1 | **Thread Blocking** | `Thread.sleep(15_000)` in ResumeRewriter | RxJava `Flowable.delay()` + genai Client retry with exponential backoff |
| 2 | **Thread-Safe State** | Assumed ADK handles it | ✅ Confirmed: ADK Java's `Session.Builder` uses `ConcurrentHashMap` by default (verified in source). No custom work needed. |
| 3 | **Hybrid Agent Observability** | `DeterministicAgent` + raw `genai.Client` calls (hidden from ADK) | **`LlmAgent` + `FunctionTool`** for all hybrid agents — ADK orchestrates LLM calls, full Dev UI observability |
| 4 | **JSON Schema Automation** | Manual schema strings | `victools/jsonschema-generator` + `jsonschema-module-jackson` for POJO → JSON Schema at runtime |
| 5 | **Pipeline Short-Circuiting** | Soft halt via `pipeline_halted` boolean checked inside each agent | **`beforeAgentCallback`** on each downstream agent — returns `Content` to trigger `endInvocation=true`, agent's `runAsyncImpl()` never executes |

---

## Agent Classification — Rev 2

| # | Agent | Rev 2 Java ADK Type | Rationale |
|---|-------|---------------------|-----------|
| 1 | DocumentParserAgent | `LlmAgent` + `FunctionTool` | Same as Rev 1 |
| 2 | JDAnalyzerAgent | **`LlmAgent` + `FunctionTool`** | ⚡ Changed: deterministic tools exposed as FunctionTools, ADK drives LLM call |
| 3 | AlignmentValidatorAgent | `DeterministicAgent` (custom BaseAgent) | Pure Java, no LLM — sets `pipeline_halted` in state |
| 4 | ATSPreCheckAgent | `DeterministicAgent` | Pure Java, no LLM |
| 5 | ResumeRewriterAgent | **`LlmAgent` + `FunctionTool`** | ⚡ Changed: map-reduce tools as FunctionTools, non-blocking delays via RxJava |
| 6 | ATSScorerAgent | `DeterministicAgent` | Pure Java, no LLM |
| 7 | CriticAgent | **`LlmAgent` + `FunctionTool`** | ⚡ Changed: critic tools as FunctionTools, ADK drives LLM |
| 8 | HTMLRendererAgent | `DeterministicAgent` | Pure Java, Handlebars template |
| 9 | ReportGeneratorAgent | `DeterministicAgent` | Pure Java, StringBuilder |

---

## Architecture Deep Dives (Rev 2)

### 1. Non-Blocking Rate Limiting (ResumeRewriterAgent)

**Problem**: `Thread.sleep()` blocks the RxJava scheduler thread, freezing Spring Boot under concurrent load.

**Solution**: The rewriter's map-reduce loop is implemented as a `FunctionTool` that the `LlmAgent` calls iteratively. Between iterations, we use RxJava's non-blocking delay:

```java
// Inside the FunctionTool method — non-blocking delay between entries
Flowable.fromIterable(experienceEntries)
    .concatMap(entry ->
        Flowable.just(entry)
            .delay(rateLimitMs, TimeUnit.MILLISECONDS)  // Non-blocking!
    )
```

Additionally, we configure the `com.google.genai.Client` with built-in retry + exponential backoff (available in the Java GenAI SDK) as a safety net for 429 errors.

### 2. Thread-Safe Session State — No Action Needed ✅

**Verified from ADK Java source** (`Session.java` line 66):
```java
private State state = new State(new ConcurrentHashMap<>());
```
And `InMemorySessionService` also creates sessions with `new ConcurrentHashMap<>()`. ADK Java handles this natively.

### 3. Hybrid Agents as LlmAgent + FunctionTool (Observability)

**Problem**: Raw `genai.Client` calls inside `DeterministicAgent` hide prompts/tokens from ADK Dev UI.

**Solution**: Refactor hybrid agents (JdAnalyzer, ResumeRewriter, Critic) to be full `LlmAgent` instances. The deterministic logic becomes `FunctionTool` methods that the LLM calls:

```java
// JdAnalyzerAgent — LlmAgent with deterministic tools
public static LlmAgent create() {
    return LlmAgent.builder()
        .name("JdAnalyzerAgent")
        .model("gemini-2.0-flash")
        .instruction("""
            You are a Job Description Analyzer. Use the provided tools to analyze the JD:
            1. Call check_jd_authenticity with the JD text
            2. Call extract_seniority_signals with the JD text
            3. Call extract_ats_keywords with the JD text
            4. Call extract_job_metadata with the JD text
            5. Synthesize all results into structured JSON output
            """)
        .tools(
            FunctionTool.create(JdAnalyzerTools.class, "checkJdAuthenticity"),
            FunctionTool.create(JdAnalyzerTools.class, "extractSenioritySignals"),
            FunctionTool.create(JdAnalyzerTools.class, "extractAtsKeywords"),
            FunctionTool.create(JdAnalyzerTools.class, "extractJobMetadata")
        )
        .outputKey("jd_analysis_output")
        .build();
}
```

This pattern preserves full ADK observability: tool calls, LLM prompts, and token usage all appear in `AdkWebServer` Dev UI.

### 4. Automated JSON Schema Generation

**Problem**: Hand-crafting JSON schema strings for Gemini's `response_schema` is brittle.

**Solution**: Add `victools/jsonschema-generator` + `jsonschema-module-jackson`:

```java
// SchemaUtil.java — generates JSON schema from any Jackson POJO
public class SchemaUtil {
    private static final SchemaGenerator GENERATOR;
    static {
        JacksonModule module = new JacksonModule(JacksonOption.RESPECT_JSONPROPERTY_REQUIRED);
        SchemaGeneratorConfig config = new SchemaGeneratorConfigBuilder(
                SchemaVersion.DRAFT_2020_12, OptionPreset.PLAIN_JSON)
            .with(module).build();
        GENERATOR = new SchemaGenerator(config);
    }
    
    public static JsonNode generateSchema(Class<?> pojoClass) {
        return GENERATOR.generateSchema(pojoClass);
    }
}

// Usage in agent config:
// .generateContentConfig(GenerateContentConfig.builder()
//     .responseMimeType("application/json")
//     .responseSchema(SchemaUtil.generateSchema(JdExtractionResult.class))
//     .build())
```

### 5. True Pipeline Short-Circuiting via `beforeAgentCallback`

**Problem**: Soft halt requires all 6 downstream agents to boot up just to check a flag.

**Solution**: From ADK Java source (`BaseAgent.run()`), when a `beforeAgentCallback` returns `Content`, the framework sets `endInvocation = true` and **skips `runAsyncImpl()` entirely**. We register a shared callback on every downstream agent:

```java
// Shared callback — checks session state, short-circuits if halted
BeforeAgentCallback pipelineHaltGuard = (callbackContext) -> {
    Object halted = callbackContext.state().get("pipeline_halted");
    if (Boolean.TRUE.equals(halted)) {
        String reason = (String) callbackContext.state().getOrDefault(
            "halt_reason", "Pipeline halted by upstream agent");
        return Maybe.just(Content.fromParts(Part.fromText("⏭️ Skipped: " + reason)));
    }
    return Maybe.empty();  // No Content = proceed normally
};

// Applied to each downstream agent:
AtsPreCheckAgent.builder()
    .beforeAgentCallback(pipelineHaltGuard)
    .build();
```

The `AlignmentValidatorAgent` (a `DeterministicAgent`) sets `pipeline_halted = true` in its state delta when alignment fails. All subsequent agents have the `pipelineHaltGuard` callback — they skip instantly without executing.

---

## Updated Project Structure

```
resume_optimizerv3/
├── pom.xml
├── src/main/java/com/resumeoptimizer/
│   ├── ResumeOptimizerApplication.java        # Spring Boot entry
│   ├── AdkDevServer.java                      # ADK Dev UI entry
│   ├── config/AppConfig.java
│   ├── pipeline/
│   │   ├── PipelineFactory.java               # Builds SequentialAgent root
│   │   ├── DeterministicAgent.java            # BaseAgent subclass (pure deterministic only)
│   │   ├── AbortPipelineException.java
│   │   └── PipelineHaltGuard.java             # Shared beforeAgentCallback
│   ├── agents/
│   │   ├── DocumentParserAgent.java           # LlmAgent + FunctionTool
│   │   ├── JdAnalyzerAgent.java               # LlmAgent + FunctionTool  ⚡
│   │   ├── AlignmentValidatorAgent.java       # DeterministicAgent (hard gate)
│   │   ├── AtsPreCheckAgent.java              # DeterministicAgent
│   │   ├── ResumeRewriterAgent.java           # LlmAgent + FunctionTool  ⚡
│   │   ├── AtsScorerAgent.java                # DeterministicAgent
│   │   ├── CriticAgent.java                   # LlmAgent + FunctionTool  ⚡
│   │   ├── HtmlRendererAgent.java             # DeterministicAgent
│   │   └── ReportGeneratorAgent.java          # DeterministicAgent
│   ├── tools/
│   │   ├── DocumentParserTools.java           # FunctionTool: PDF/DOCX/TXT
│   │   ├── JdAnalyzerTools.java               # FunctionTool: regex analysis
│   │   ├── AlignmentTools.java                # Internal: seniority/domain
│   │   ├── AtsTools.java                      # FunctionTool/Internal: ATS scoring
│   │   ├── CriticTools.java                   # FunctionTool: page/stuffing
│   │   └── RewriterTools.java                 # FunctionTool: experience rewrite
│   ├── model/                                 # Jackson POJOs
│   │   ├── ContactInfo.java, ExperienceEntry.java, EducationEntry.java
│   │   ├── ResumeData.java, JobDescription.java
│   │   ├── AlignmentResult.java, AtsScore.java
│   │   ├── RewriterResult.java, CriticResult.java
│   │   └── JdExtractionResult.java
│   ├── controller/ResumeOptimizerController.java
│   └── util/
│       ├── JsonExtractor.java
│       ├── SchemaUtil.java                    # victools schema generator ⚡ NEW
│       └── StateConstants.java
├── src/main/resources/
│   ├── application.properties
│   └── templates/resume.hbs
└── src/test/java/com/resumeoptimizer/
    └── ResumeOptimizerApplicationTests.java
```

---

## Updated Dependencies (`pom.xml`)

| Dependency | Version | Purpose |
|---|---|---|
| `com.google.adk:google-adk` | 1.2.0 | Core ADK framework |
| `com.google.adk:google-adk-dev` | 1.2.0 | Dev UI |
| `org.apache.pdfbox:pdfbox` | 3.0.3 | PDF parsing |
| `org.apache.poi:poi-ooxml` | 5.3.0 | DOCX parsing |
| `com.fasterxml.jackson.core:jackson-databind` | 2.17.x | JSON |
| `com.github.jknack:handlebars` | 4.4.0 | HTML templates |
| `com.github.victools:jsonschema-generator` | **4.38.0** | ⚡ NEW: POJO → JSON Schema |
| `com.github.victools:jsonschema-module-jackson` | **4.38.0** | ⚡ NEW: Jackson annotation support |
| `org.springframework.boot:spring-boot-starter-web` | 3.2.x | REST API |
| `io.github.cdimascio:dotenv-java` | 3.1.0 | .env loading |

---

## Verification Plan

### Automated Tests
1. `mvn clean compile` — All classes compile
2. `mvn test` — Spring Boot context loads, `PipelineFactory` produces valid `SequentialAgent`
3. Verify `pipelineHaltGuard` callback skips downstream agents when `pipeline_halted=true`

### Manual Verification
- Launch `AdkDevServer` → confirm tool calls/LLM prompts visible in Dev UI for hybrid agents
- Compare each agent's logic against Python equivalent
- Verify Handlebars template matches Jinja2 output
