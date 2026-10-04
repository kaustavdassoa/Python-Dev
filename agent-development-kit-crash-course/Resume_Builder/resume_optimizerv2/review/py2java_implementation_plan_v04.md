# Python to Java Migration — Resume Optimizer v3 (ADK Java) — Rev 3

**Rev 3 Change**: ResumeRewriterAgent adopts **Path A** (single-shot generation). Eliminates map-reduce loop, RxJava delays, rate-limiting logic, and `RewriterTools.java` entirely.

---

## Rev 3 Changelog (vs Rev 2)

| # | Item | Rev 2 | Rev 3 |
|---|------|-------|-------|
| 1 | **ResumeRewriter strategy** | `LlmAgent` + `FunctionTool` with `Flowable.delay()` map-reduce loop | **`LlmAgent` with single-shot generation** — no tools, no loop |
| 2 | **RewriterTools.java** | Contained map-reduce FunctionTool methods | **DELETED** — no longer needed |
| 3 | **Rate limiting** | `Flowable.delay()` between experience entries | **Eliminated** — one LLM call replaces N calls |
| 4 | **Prompt injection** | Standard `{key}` instruction template | `Instruction.Provider` (required because instruction contains literal JSON braces) |

All Rev 2 items preserved: thread-safe state ✅, `beforeAgentCallback` short-circuiting ✅, hybrid agents as `LlmAgent+FunctionTool` ✅, victools schema gen ✅.

---

## Updated Agent Classification — Rev 3

| # | Agent | Java ADK Type | Tools? | Change |
|---|-------|---------------|--------|--------|
| 1 | DocumentParserAgent | `LlmAgent` | `FunctionTool` (parse files) | — |
| 2 | JDAnalyzerAgent | `LlmAgent` | `FunctionTool` (regex tools) | — |
| 3 | AlignmentValidatorAgent | `DeterministicAgent` | None | — |
| 4 | ATSPreCheckAgent | `DeterministicAgent` | None | — |
| 5 | **ResumeRewriterAgent** | **`LlmAgent`** | **None** | ⚡ Path A: single-shot, no tools |
| 6 | ATSScorerAgent | `DeterministicAgent` | None | — |
| 7 | CriticAgent | `LlmAgent` | `FunctionTool` (critic tools) | — |
| 8 | HTMLRendererAgent | `DeterministicAgent` | None | — |
| 9 | ReportGeneratorAgent | `DeterministicAgent` | None | — |

---

## Path A Deep Dive: ResumeRewriterAgent

### Why Path A

- Gemini 2.0 Flash has **1M+ token context** — bulk rewriting all experiences in one call is trivial
- Eliminates N sequential LLM calls → **1 call** (massive latency reduction)
- No rate limiting, no `Flowable.delay()`, no `Thread.sleep()` — zero concurrency risk
- No `RewriterTools.java` class needed — radical simplification

### Implementation: `Instruction.Provider` (not `{key}` template)

ADK Java's `{state_key}` injection in plain `instruction()` strings would conflict with literal JSON curly braces in the prompt. We use `Instruction.Provider` which receives a `ReadonlyContext` and manually reads session state:

```java
public class ResumeRewriterAgent {
    
    public static LlmAgent create() {
        // Instruction.Provider gives us full control over state injection
        // and avoids conflicts with literal JSON braces in the prompt
        Instruction.Provider instructionProvider = (ReadonlyContext ctx) -> {
            String parsedResume = String.valueOf(ctx.state().get("parsed_resume"));
            String jdAnalysis = String.valueOf(ctx.state().get("jd_analysis_output"));
            String gapReport = String.valueOf(ctx.state().get("gap_report"));
            
            return Single.just(String.format("""
                You are an expert Resume Rewriter. Rewrite the ENTIRE resume below
                to perfectly align with the Job Description.
                
                Rules:
                - Apply the XYZ formula (Accomplished X, measured by Y, by doing Z)
                - Naturally integrate missing keywords from the Gap Report
                - Preserve all factual data (dates, companies, degrees)
                - Keep the same number of experience entries
                - Return the COMPLETE rewritten resume as JSON
                
                === ORIGINAL RESUME ===
                %s
                
                === JOB DESCRIPTION ANALYSIS ===
                %s
                
                === GAP REPORT ===
                %s
                """, parsedResume, jdAnalysis, gapReport));
        };

        return LlmAgent.builder()
            .name("ResumeRewriterAgent")
            .model("gemini-2.0-flash")
            .instruction(instructionProvider)
            .generateContentConfig(GenerateContentConfig.builder()
                .responseMimeType("application/json")
                .responseSchema(SchemaUtil.generateSchema(RewriterResult.class))
                .build())
            .outputKey("rewriter_output")
            .disallowTransferToParent(true)
            .disallowTransferToPeers(true)
            .build();
    }
}
```

### What RewriterResult.java looks like

```java
public record RewriterResult(
    @JsonProperty("contact") ContactInfo contact,
    @JsonProperty("summary") String summary,
    @JsonProperty("skills") List<String> skills,
    @JsonProperty("experience") List<ExperienceEntry> experience,
    @JsonProperty("education") List<EducationEntry> education,
    @JsonProperty("certifications") List<String> certifications
) {}
```

The victools `SchemaUtil` generates the JSON schema from this record at runtime, which is passed to `responseSchema()` to enforce structured output from Gemini.

---

## Updated Project Structure — Rev 3

```
resume_optimizerv3/
├── pom.xml
├── src/main/java/com/resumeoptimizer/
│   ├── ResumeOptimizerApplication.java
│   ├── AdkDevServer.java
│   ├── config/AppConfig.java
│   ├── pipeline/
│   │   ├── PipelineFactory.java
│   │   ├── DeterministicAgent.java
│   │   ├── AbortPipelineException.java
│   │   └── PipelineHaltGuard.java
│   ├── agents/
│   │   ├── DocumentParserAgent.java       # LlmAgent + FunctionTool
│   │   ├── JdAnalyzerAgent.java           # LlmAgent + FunctionTool
│   │   ├── AlignmentValidatorAgent.java   # DeterministicAgent
│   │   ├── AtsPreCheckAgent.java          # DeterministicAgent
│   │   ├── ResumeRewriterAgent.java       # LlmAgent (Path A, no tools)
│   │   ├── AtsScorerAgent.java            # DeterministicAgent
│   │   ├── CriticAgent.java               # LlmAgent + FunctionTool
│   │   ├── HtmlRendererAgent.java         # DeterministicAgent
│   │   └── ReportGeneratorAgent.java      # DeterministicAgent
│   ├── tools/
│   │   ├── DocumentParserTools.java       # FunctionTool: PDF/DOCX/TXT
│   │   ├── JdAnalyzerTools.java           # FunctionTool: regex analysis
│   │   ├── AlignmentTools.java            # Internal: seniority/domain
│   │   ├── AtsTools.java                  # Internal: ATS scoring
│   │   └── CriticTools.java               # FunctionTool: page/stuffing
│   │   # ⚡ RewriterTools.java DELETED
│   ├── model/
│   │   ├── ContactInfo.java
│   │   ├── ExperienceEntry.java
│   │   ├── EducationEntry.java
│   │   ├── ResumeData.java
│   │   ├── JobDescription.java
│   │   ├── AlignmentResult.java
│   │   ├── AtsScore.java
│   │   ├── RewriterResult.java            # Used for structured output schema
│   │   ├── CriticResult.java
│   │   └── JdExtractionResult.java
│   ├── controller/ResumeOptimizerController.java
│   └── util/
│       ├── JsonExtractor.java
│       ├── SchemaUtil.java                # victools schema generator
│       └── StateConstants.java
├── src/main/resources/
│   ├── application.properties
│   └── templates/resume.hbs
└── src/test/java/com/resumeoptimizer/
    └── ResumeOptimizerApplicationTests.java
```

---

## Dependencies — Rev 3 (unchanged from Rev 2)

| Dependency | Version | Purpose |
|---|---|---|
| `com.google.adk:google-adk` | 1.2.0 | Core ADK |
| `com.google.adk:google-adk-dev` | 1.2.0 | Dev UI |
| `org.apache.pdfbox:pdfbox` | 3.0.3 | PDF parsing |
| `org.apache.poi:poi-ooxml` | 5.3.0 | DOCX parsing |
| `com.fasterxml.jackson.core:jackson-databind` | 2.17.x | JSON |
| `com.github.jknack:handlebars` | 4.4.0 | HTML templates |
| `com.github.victools:jsonschema-generator` | 4.38.0 | POJO → JSON Schema |
| `com.github.victools:jsonschema-module-jackson` | 4.38.0 | Jackson annotation support |
| `org.springframework.boot:spring-boot-starter-web` | 3.2.x | REST API |
| `io.github.cdimascio:dotenv-java` | 3.1.0 | .env loading |

---

## Remaining Open Questions

> [!NOTE]
> **Alignment Gatekeeper**: Exists in Python directory but NOT used in pipeline. Omitting it. Confirm.

---

## Verification Plan

### Automated Tests
1. `mvn clean compile` — All classes compile
2. `mvn test` — Spring Boot context loads, `PipelineFactory` valid
3. Verify `PipelineHaltGuard` callback skips agents when `pipeline_halted=true`

### Manual Verification
- Launch `AdkDevServer` → confirm ResumeRewriter LLM call visible in Dev UI
- Verify single-shot output matches `RewriterResult` schema
- Compare Handlebars template output against Jinja2 original
