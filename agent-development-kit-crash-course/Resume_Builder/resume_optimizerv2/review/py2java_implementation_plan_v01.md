# Python to Java Migration — Resume Optimizer v3

Migrate the 9-agent sequential resume optimization pipeline from Python (Google ADK + FastAPI) to a production-ready, strictly-typed Java 17+ application using Maven, Spring Boot, and native Java design patterns.

---

## Source Analysis Summary

The Python v2 codebase contains:
- **9 sequential agents** orchestrated by Google ADK's `SequentialAgent`
- **3 agent archetypes**: LLM-backed (`LlmAgent`), Hybrid (deterministic + scoped LLM call via `PythonTaskNode`), and Fully Deterministic (`PythonTaskNode`)
- **State management**: Flat dictionary (`session.state`) with string constants for keys
- **API layer**: FastAPI with file upload (PDF/DOCX/TXT) + JD text
- **Dependencies**: pdfplumber, python-docx, Jinja2, Pydantic, Google GenAI client

### Agent Classification

| # | Agent | Python Type | Java Strategy |
|---|-------|------------|---------------|
| 1 | DocumentParserAgent | `LlmAgent` + tools | LLM call via LangChain4j |
| 2 | JDAnalyzerAgent | `PythonTaskNode` (hybrid) | Deterministic tools + scoped LLM call |
| 3 | AlignmentValidatorAgent | `PythonTaskNode` (deterministic) | Pure Java logic |
| 4 | ATSPreCheckAgent | `PythonTaskNode` (deterministic) | Pure Java logic |
| 5 | ResumeRewriterAgent | `PythonTaskNode` (hybrid, map-reduce) | Scoped LLM calls with sequential experience rewriting |
| 6 | ATSScorerAgent | `PythonTaskNode` (deterministic) | Pure Java logic |
| 7 | CriticAgent | `PythonTaskNode` (hybrid) | Deterministic tools + scoped LLM call |
| 8 | HTMLRendererAgent | `PythonTaskNode` (deterministic) | Handlebars.java template engine |
| 9 | ReportGeneratorAgent | `PythonTaskNode` (deterministic) | Java `String.format` / `StringBuilder` |

---

## User Review Required

> [!IMPORTANT]
> **LLM Client Choice**: The Python code uses `google.genai.Client` to call Gemini models directly. For Java, I will use **LangChain4j** with its Google Gemini integration (`langchain4j-google-ai-gemini`). This provides structured output, JSON schema enforcement, and a clean API. Please confirm this is acceptable or if you prefer a different LLM client library.

> [!IMPORTANT]
> **Build System**: I will use **Maven** with `pom.xml`. The project will target **Java 17** to leverage records, text blocks, and modern APIs.

> [!WARNING]
> **Template Engine**: The Python code uses Jinja2 for HTML rendering. I will use **Handlebars.java** as the Java equivalent, which has near-identical `{{ }}` syntax, making template porting trivial.

---

## Open Questions

> [!IMPORTANT]
> **Rate Limiting**: The Python `ResumeRewriterAgent` has a hardcoded `time.sleep(15)` between experience entries to respect RPM limits. Should I preserve this with `Thread.sleep(15000)` in Java, or would you prefer a configurable rate limiter?

> [!NOTE]
> **Alignment Gatekeeper**: The `alignment_gatekeeper` sub-agent exists in the directory but is NOT used in the root pipeline (only `alignment_validator` is used and it throws `AbortPipelineError` directly). I will omit it from the Java version. Confirm if this is correct.

---

## Proposed Changes

### Project Structure

```
resume_optimizerv3/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/com/resumeoptimizer/
│   │   │   ├── ResumeOptimizerApplication.java          # Spring Boot entry point
│   │   │   ├── config/
│   │   │   │   └── AppConfig.java                       # Bean configuration, LLM client setup
│   │   │   ├── model/                                   # Strongly-typed POJOs
│   │   │   │   ├── SessionState.java                    # Thread-safe pipeline state
│   │   │   │   ├── ContactInfo.java
│   │   │   │   ├── ExperienceEntry.java
│   │   │   │   ├── EducationEntry.java
│   │   │   │   ├── ResumeData.java                      # Parsed resume structure
│   │   │   │   ├── JobDescription.java                  # JD analysis output
│   │   │   │   ├── AlignmentResult.java
│   │   │   │   ├── AtsScore.java
│   │   │   │   ├── RewriterResult.java
│   │   │   │   ├── CriticResult.java
│   │   │   │   └── PipelineReport.java
│   │   │   ├── pipeline/                                # Orchestration
│   │   │   │   ├── PipelineOrchestrator.java            # Sequential agent runner
│   │   │   │   ├── PipelineAgent.java                   # Agent interface
│   │   │   │   └── AbortPipelineException.java          # Hard gate exception
│   │   │   ├── agents/                                  # All 9 agents
│   │   │   │   ├── DocumentParserAgent.java
│   │   │   │   ├── JdAnalyzerAgent.java
│   │   │   │   ├── AlignmentValidatorAgent.java
│   │   │   │   ├── AtsPreCheckAgent.java
│   │   │   │   ├── ResumeRewriterAgent.java
│   │   │   │   ├── AtsScorerAgent.java
│   │   │   │   ├── CriticAgent.java
│   │   │   │   ├── HtmlRendererAgent.java
│   │   │   │   └── ReportGeneratorAgent.java
│   │   │   ├── tools/                                   # Deterministic tool classes
│   │   │   │   ├── DocumentParserTools.java             # PDF/DOCX/TXT parsing
│   │   │   │   ├── JdAnalyzerTools.java                 # Authenticity, seniority, keywords
│   │   │   │   ├── AlignmentTools.java                  # Seniority ladder, domain overlap
│   │   │   │   ├── AtsTools.java                        # ATS scoring, formatting check
│   │   │   │   └── CriticTools.java                     # Page length, keyword stuffing
│   │   │   ├── controller/
│   │   │   │   └── ResumeOptimizerController.java       # REST API endpoint
│   │   │   └── util/
│   │   │       ├── JsonExtractor.java                   # Multi-strategy JSON from LLM output
│   │   │       └── StateConstants.java                  # State key constants
│   │   └── resources/
│   │       ├── application.properties                   # Spring config
│   │       └── templates/
│   │           └── resume.html                          # Handlebars template (ported from Jinja2)
│   └── test/
│       └── java/com/resumeoptimizer/
│           └── ResumeOptimizerApplicationTests.java
```

---

### Component 1: Build System (`pom.xml`)

#### [NEW] [pom.xml](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv3/pom.xml)

Maven POM with dependencies:
- **Spring Boot 3.2.x** — Web framework, REST API, dependency injection
- **Apache PDFBox 3.x** — PDF text extraction (replaces `pdfplumber`)
- **Apache POI 5.x** — DOCX text extraction (replaces `python-docx`)
- **Jackson** — JSON serialization/deserialization (replaces `json` + Pydantic)
- **LangChain4j** (`langchain4j-google-ai-gemini`) — LLM interaction (replaces `google.genai`)
- **Handlebars.java** — Template engine (replaces Jinja2)
- **Lombok** — Reduces boilerplate for POJOs

---

### Component 2: Model Layer (POJOs)

#### [NEW] `SessionState.java`
Thread-safe state container using `ConcurrentHashMap<String, Object>`. Replaces Python's `session.state` dictionary. Provides type-safe getter methods:
```java
public class SessionState {
    private final ConcurrentHashMap<String, Object> state = new ConcurrentHashMap<>();
    public void put(String key, Object value) { ... }
    public <T> T get(String key, Class<T> type) { ... }
    public boolean isPipelineHalted() { ... }
    public void haltPipeline(String reason) { ... }
}
```

#### [NEW] `ContactInfo.java`, `ExperienceEntry.java`, `EducationEntry.java`
Java Records mirroring Python Pydantic schemas:
```java
public record ContactInfo(String name, String email, String phone, String location, String linkedin) {}
public record ExperienceEntry(String title, String company, String dates, List<String> bullets, String entryType) {}
public record EducationEntry(String degree, String institution, String year) {}
```

#### [NEW] `ResumeData.java`, `JobDescription.java`, `AlignmentResult.java`, `AtsScore.java`, `RewriterResult.java`, `CriticResult.java`, `PipelineReport.java`
Strongly-typed POJOs for each agent's output, annotated with Jackson `@JsonProperty` for clean serialization.

---

### Component 3: Pipeline Orchestration

#### [NEW] `PipelineAgent.java` — Interface
```java
public interface PipelineAgent {
    String name();
    void execute(SessionState state) throws AbortPipelineException;
}
```

#### [NEW] `PipelineOrchestrator.java`
Sequential executor that runs all 9 agents in order, with pipeline-halt checking:
```java
public class PipelineOrchestrator {
    private final List<PipelineAgent> agents;
    
    public SessionState run(SessionState initialState) {
        for (PipelineAgent agent : agents) {
            if (initialState.isPipelineHalted()) {
                log.info("Skipping {} — pipeline halted", agent.name());
                continue;
            }
            agent.execute(initialState);
        }
        return initialState;
    }
}
```

#### [NEW] `AbortPipelineException.java`
Custom runtime exception for hard gates (replaces Python's `AbortPipelineError`).

---

### Component 4: Agent Implementations (9 agents)

Each agent implements `PipelineAgent`. Translation mappings:

| Python Pattern | Java Translation |
|---|---|
| `LlmAgent` with tools | Agent class calls `LangChain4j` client with JSON-structured output |
| `PythonTaskNode` (deterministic) | Agent class calls static tool methods directly |
| `PythonTaskNode` (hybrid) | Agent calls deterministic tools + one `LangChain4j` call |
| `state.get("key")` | `sessionState.get("key", Type.class)` |
| `state_delta[key] = value` | `sessionState.put(key, value)` |
| Pydantic `BaseModel` for LLM schema | Jackson-annotated POJOs passed to LangChain4j structured output |
| `asyncio.to_thread(func)` | Direct synchronous call (pipeline is sequential) |
| `time.sleep(15)` | `Thread.sleep(15_000)` with configurable property |

---

### Component 5: Tool Classes (deterministic logic)

#### [NEW] `DocumentParserTools.java`
- `parsePdf(byte[] fileBytes)` → Uses **Apache PDFBox** `PDDocument` + `PDFTextStripper` with page-boundary markers
- `parseDocx(byte[] fileBytes)` → Uses **Apache POI** `XWPFDocument`
- `parsePlainText(String text)` → Simple null/empty check

#### [NEW] `JdAnalyzerTools.java`
Direct port of regex-based tools:
- `checkJdAuthenticity(String jdText)` — regex marker scoring
- `extractSenioritySignals(String jdText)` — seniority ladder + years regex
- `extractAtsKeywords(String jdText)` — tech pattern regex matching
- `extractJobMetadata(String jdText)` — employment type + work model detection

#### [NEW] `AlignmentTools.java`
- `compareSeniorityLevels(String candidateLevel, String jdLevel, Integer jdScoreOverride)`
- `checkDomainAlignment(String resumeSkillsCsv, String jdRequiredSkillsCsv)`
- Static `SENIORITY_LADDER` map and `LEVEL_LABELS` map

#### [NEW] `AtsTools.java`
- `detectAtsUnfriendlyFormatting(String resumeText)` — ATS warning scanner
- `calculateAtsScore(String resumeText, String jdKeywordsCsv)` — keyword match scoring

#### [NEW] `CriticTools.java`
- `estimatePageLength(String text)` — word count → page estimate
- `detectKeywordStuffing(String text, String jdKeywordsCsv)` — stuffing detection

---

### Component 6: REST API

#### [NEW] `ResumeOptimizerController.java`
Spring MVC REST controller replacing the FastAPI endpoint:
```java
@PostMapping(value = "/api/v1/resume/optimize", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public ResponseEntity<String> optimizeResume(
    @RequestParam("file") MultipartFile file,
    @RequestParam("job_description") String jobDescription
) { ... }
```
- Validates file extension (.pdf, .docx, .txt)
- Parses document using `DocumentParserTools`
- Creates `SessionState`, runs `PipelineOrchestrator`
- Saves HTML resume and report to output directory
- Returns HTML with custom headers (X-ATS-Score, etc.)

---

### Component 7: Configuration & Resources

#### [NEW] `application.properties`
```properties
model.name=gemini-2.0-flash
google.api.key=${GOOGLE_API_KEY}
output.directory=./output
rewriter.sleep.ms=15000
server.port=8000
```

#### [NEW] `resume.html` (Handlebars template)
Ported from Jinja2 template. Syntax changes:
- `{% if %}` → `{{#if}}`
- `{% for %}` → `{{#each}}`
- `{{ var | default('') }}` → `{{var}}` (defaults handled in Java)
- `{% if job.entry_type is defined and job.entry_type == 'project' %}` → `{{#if isProject}}` (computed in Java)

---

## Verification Plan

### Automated Tests
- `mvn clean compile` — Verify all classes compile without errors
- `mvn test` — Run Spring Boot context load test
- Tree output of generated directory structure for visual verification

### Manual Verification
- Compare each Java agent's logic against its Python equivalent
- Review `pom.xml` for dependency completeness
- Verify Handlebars template renders identically to Jinja2 output

---

## Python → Java Workaround Notes

| Python Feature | Java Workaround |
|---|---|
| `pdfplumber.open(BytesIO(bytes))` | `PDDocument.load(InputStream)` with `PDFTextStripper` |
| `python-docx` `Document(BytesIO(bytes))` | `XWPFDocument(InputStream)` with paragraph extraction |
| Pydantic `BaseModel.model_json_schema()` | Jackson `ObjectMapper` with POJO class schemas |
| `re.findall()` with flags | `Pattern.compile(regex, Pattern.CASE_INSENSITIVE).matcher().find()` |
| `google.genai.Client().models.generate_content()` | LangChain4j `GoogleAiGeminiChatModel.builder()` with structured output |
| `response_mime_type="application/json"` + `response_schema` | LangChain4j `AiServices` with POJO return types for structured extraction |
| Python f-string templates | Java `String.format()` or text blocks |
| `async for event in runner.run_async()` | Synchronous sequential pipeline execution |
| `ConcurrentHashMap` not needed in Python (GIL) | Required in Java for thread-safe state access |
