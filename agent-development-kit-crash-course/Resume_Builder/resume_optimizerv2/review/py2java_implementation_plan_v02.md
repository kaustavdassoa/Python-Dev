# Python to Java Migration — Resume Optimizer v3 (ADK Java)

Migrate the 9-agent sequential resume optimization pipeline from **Python ADK** (`google-adk` Python) to **Java ADK** (`google/adk-java` v1.2.0), preserving the exact same framework semantics: `SequentialAgent`, `LlmAgent`, `BaseAgent`, `FunctionTool`, `InMemoryRunner`, and session state.

---

## Source Analysis Summary

The Python v2 codebase contains:
- **9 sequential agents** orchestrated by Google ADK's `SequentialAgent`
- **3 agent archetypes**: LLM-backed (`LlmAgent`), Hybrid (deterministic + scoped LLM call via `PythonTaskNode`), and Fully Deterministic (`PythonTaskNode`)
- **State management**: Flat dictionary (`session.state`) with string constants for keys
- **API layer**: FastAPI with file upload (PDF/DOCX/TXT) + JD text
- **Dependencies**: pdfplumber, python-docx, Jinja2, Pydantic, Google GenAI client

### Agent Classification & Java ADK Mapping

| # | Agent | Python Type | Java ADK Strategy |
|---|-------|------------|-------------------|
| 1 | DocumentParserAgent | `LlmAgent` + tools | `LlmAgent` with `FunctionTool` (1:1 port) |
| 2 | JDAnalyzerAgent | `PythonTaskNode` (hybrid) | Custom `BaseAgent` subclass + direct Gemini call |
| 3 | AlignmentValidatorAgent | `PythonTaskNode` (deterministic) | Custom `BaseAgent` subclass (pure Java) |
| 4 | ATSPreCheckAgent | `PythonTaskNode` (deterministic) | Custom `BaseAgent` subclass (pure Java) |
| 5 | ResumeRewriterAgent | `PythonTaskNode` (hybrid, map-reduce) | Custom `BaseAgent` subclass + scoped Gemini calls |
| 6 | ATSScorerAgent | `PythonTaskNode` (deterministic) | Custom `BaseAgent` subclass (pure Java) |
| 7 | CriticAgent | `PythonTaskNode` (hybrid) | Custom `BaseAgent` subclass + scoped Gemini call |
| 8 | HTMLRendererAgent | `PythonTaskNode` (deterministic) | Custom `BaseAgent` subclass (Handlebars template) |
| 9 | ReportGeneratorAgent | `PythonTaskNode` (deterministic) | Custom `BaseAgent` subclass (StringBuilder) |

---

## User Review Required

> [!IMPORTANT]
> **Framework**: Using **Google ADK Java** (`com.google.adk:google-adk:1.2.0`) as requested. This gives us the same `SequentialAgent`, `LlmAgent`, `BaseAgent`, `FunctionTool`, `InMemoryRunner`, and session state APIs as the Python version — a near-1:1 framework mapping.

> [!IMPORTANT]
> **PythonTaskNode Equivalent**: ADK Java has no built-in `PythonTaskNode`. I will create a **`DeterministicAgent`** abstract class that extends `BaseAgent`, overrides `runAsyncImpl()` to execute a deterministic Java function, and emits state deltas via `Event` — exactly mirroring the Python `PythonTaskNode` pattern.

> [!IMPORTANT]
> **Hybrid Agents (JD Analyzer, Rewriter, Critic)**: These need direct Gemini API calls inside deterministic code. I will use `com.google.genai.Client` (the Java Google GenAI SDK, same as Python's `google.genai.Client`) for these scoped LLM calls, keeping them inside the `DeterministicAgent.execute()` method.

> [!WARNING]
> **Template Engine**: Jinja2 → **Handlebars.java** (near-identical `{{ }}` syntax for trivial porting).

---

## Open Questions

> [!IMPORTANT]
> **Rate Limiting**: The Python `ResumeRewriterAgent` has a hardcoded `Thread.sleep(15_000)` between experience entries to respect RPM limits. Should I preserve this or make it configurable via `application.properties`? **Default plan**: configurable with `rewriter.sleep.ms=15000`.

> [!NOTE]
> **Alignment Gatekeeper**: Exists in Python directory but is NOT used in the root pipeline (only `alignment_validator` is). I will omit it. Confirm.

> [!NOTE]
> **Dev UI**: ADK Java includes `AdkWebServer` for the same Dev UI as Python. I'll wire this up as an alternative entry point alongside the Spring Boot REST API.

---

## Proposed Changes

### Project Structure

```
resume_optimizerv3/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/com/resumeoptimizer/
│   │   │   ├── ResumeOptimizerApplication.java          # Spring Boot entry point (REST API)
│   │   │   ├── AdkDevServer.java                        # ADK Dev UI entry point (adk web equivalent)
│   │   │   ├── config/
│   │   │   │   └── AppConfig.java                       # Bean configuration
│   │   │   ├── pipeline/                                # ADK Pipeline wiring
│   │   │   │   ├── PipelineFactory.java                 # Builds the SequentialAgent root
│   │   │   │   ├── DeterministicAgent.java              # BaseAgent subclass (PythonTaskNode equiv)
│   │   │   │   └── AbortPipelineException.java          # Hard gate exception
│   │   │   ├── agents/                                  # All 9 agents
│   │   │   │   ├── DocumentParserAgent.java             # LlmAgent + FunctionTool
│   │   │   │   ├── JdAnalyzerAgent.java                 # DeterministicAgent (hybrid)
│   │   │   │   ├── AlignmentValidatorAgent.java         # DeterministicAgent (pure)
│   │   │   │   ├── AtsPreCheckAgent.java                # DeterministicAgent (pure)
│   │   │   │   ├── ResumeRewriterAgent.java             # DeterministicAgent (hybrid)
│   │   │   │   ├── AtsScorerAgent.java                  # DeterministicAgent (pure)
│   │   │   │   ├── CriticAgent.java                     # DeterministicAgent (hybrid)
│   │   │   │   ├── HtmlRendererAgent.java               # DeterministicAgent (pure)
│   │   │   │   └── ReportGeneratorAgent.java            # DeterministicAgent (pure)
│   │   │   ├── tools/                                   # Deterministic tool classes
│   │   │   │   ├── DocumentParserTools.java             # PDF/DOCX/TXT parsing (FunctionTool targets)
│   │   │   │   ├── JdAnalyzerTools.java                 # Authenticity, seniority, keywords
│   │   │   │   ├── AlignmentTools.java                  # Seniority ladder, domain overlap
│   │   │   │   ├── AtsTools.java                        # ATS scoring, formatting check
│   │   │   │   └── CriticTools.java                     # Page length, keyword stuffing
│   │   │   ├── model/                                   # Strongly-typed POJOs
│   │   │   │   ├── ContactInfo.java
│   │   │   │   ├── ExperienceEntry.java
│   │   │   │   ├── EducationEntry.java
│   │   │   │   ├── ResumeData.java
│   │   │   │   ├── JobDescription.java
│   │   │   │   ├── AlignmentResult.java
│   │   │   │   ├── AtsScore.java
│   │   │   │   ├── RewriterResult.java
│   │   │   │   └── CriticResult.java
│   │   │   ├── controller/
│   │   │   │   └── ResumeOptimizerController.java       # Spring REST API endpoint
│   │   │   └── util/
│   │   │       ├── JsonExtractor.java                   # Multi-strategy JSON extraction (from LLM output)
│   │   │       └── StateConstants.java                  # State key string constants
│   │   └── resources/
│   │       ├── application.properties                   # Spring Boot + custom config
│   │       └── templates/
│   │           └── resume.hbs                           # Handlebars template (ported from Jinja2)
│   └── test/
│       └── java/com/resumeoptimizer/
│           └── ResumeOptimizerApplicationTests.java
```

---

### Component 1: Build System (`pom.xml`)

#### [NEW] [pom.xml](file:///e:/GitHub/Python-Dev/agent-development-kit-crash-course/Resume_Builder/resume_optimizerv3/pom.xml)

Maven POM with Java 17 and dependencies:

| Dependency | Purpose | Replaces |
|---|---|---|
| `com.google.adk:google-adk:1.2.0` | **Core ADK framework** — SequentialAgent, LlmAgent, BaseAgent, FunctionTool, InMemoryRunner, Session | `google-adk` (Python) |
| `com.google.adk:google-adk-dev:1.2.0` | **Dev UI** — `AdkWebServer` for interactive testing | `adk web` CLI |
| `org.apache.pdfbox:pdfbox:3.0.3` | PDF text extraction | `pdfplumber` |
| `org.apache.poi:poi-ooxml:5.3.0` | DOCX text extraction | `python-docx` |
| `com.fasterxml.jackson.core:jackson-databind:2.17.x` | JSON serialization | `json` + Pydantic |
| `com.github.jknack:handlebars:4.4.0` | HTML template engine | `jinja2` |
| `org.springframework.boot:spring-boot-starter-web` | REST API framework | `fastapi` |
| `io.github.cdimascio:dotenv-java:3.1.0` | .env file loading | `python-dotenv` |

---

### Component 2: Pipeline Architecture (`DeterministicAgent`)

#### [NEW] `DeterministicAgent.java` — PythonTaskNode Equivalent

This is the critical framework bridge. Extends ADK Java's `BaseAgent`, implementing `runAsyncImpl()`:

```java
public abstract class DeterministicAgent extends BaseAgent {
    
    private final String outputKey;

    @Override
    protected Flowable<Event> runAsyncImpl(InvocationContext ctx) {
        Map<String, Object> state = ctx.session().state();
        
        // Check pipeline_halted
        if (Boolean.TRUE.equals(state.get("pipeline_halted"))) {
            return Flowable.empty();
        }
        
        Map<String, Object> stateDelta = new HashMap<>();
        try {
            Object result = execute(state);           // Subclass implements this
            stateDelta.put(outputKey, result);
        } catch (AbortPipelineException e) {
            stateDelta.put("pipeline_halted", true);
            stateDelta.put("halt_reason", e.getMessage());
        }
        
        Event event = Event.builder()
            .invocationId(ctx.invocationId())
            .author(name())
            .actions(EventActions.builder().stateDelta(stateDelta).build())
            .content(Content.fromParts(Part.fromText("✅ " + name() + " complete")))
            .build();
        
        return Flowable.just(event);
    }
    
    /** Subclasses implement deterministic logic here */
    protected abstract Object execute(Map<String, Object> state);
}
```

#### [NEW] `PipelineFactory.java` — Root Agent Assembly

```java
public class PipelineFactory {
    public static SequentialAgent createPipeline() {
        return SequentialAgent.builder()
            .name("ResumeOptimizerPipeline")
            .description("9-agent sequential resume optimization pipeline")
            .subAgents(
                DocumentParserAgent.create(),       // Agent 1: LlmAgent
                JdAnalyzerAgent.create(),            // Agent 2: DeterministicAgent (hybrid)
                AlignmentValidatorAgent.create(),    // Agent 3: DeterministicAgent (hard gate)
                AtsPreCheckAgent.create(),           // Agent 4: DeterministicAgent
                ResumeRewriterAgent.create(),        // Agent 5: DeterministicAgent (hybrid)
                AtsScorerAgent.create(),             // Agent 6: DeterministicAgent
                CriticAgent.create(),                // Agent 7: DeterministicAgent (hybrid)
                HtmlRendererAgent.create(),          // Agent 8: DeterministicAgent
                ReportGeneratorAgent.create()        // Agent 9: DeterministicAgent
            )
            .build();
    }
}
```

---

### Component 3: Agent Implementations (9 agents)

#### Agent 1: `DocumentParserAgent.java` — ADK `LlmAgent`

Direct 1:1 port using ADK Java's `LlmAgent.builder()`:

```java
public class DocumentParserAgent {
    public static LlmAgent create() {
        return LlmAgent.builder()
            .name("DocumentParserAgent")
            .model("gemini-2.0-flash")
            .instruction(DocumentParserPrompts.INSTRUCTION)
            .description("Parses resume text from state or file path and checks completeness.")
            .tools(FunctionTool.create(DocumentParserTools.class, "parseResumeFile"))
            .outputKey("document_parser_output")
            .build();
    }
}
```

#### Agents 2-9: `DeterministicAgent` subclasses

Each extends `DeterministicAgent` and implements `execute(Map<String, Object> state)`:

| Agent | `execute()` Logic |
|---|---|
| JdAnalyzerAgent | Calls `JdAnalyzerTools` methods + one `com.google.genai.Client` call for extraction |
| AlignmentValidatorAgent | Calls `AlignmentTools` methods, throws `AbortPipelineException` on reject |
| AtsPreCheckAgent | Calls `AtsTools` methods |
| ResumeRewriterAgent | Map-reduce loop with `com.google.genai.Client` calls per experience entry |
| AtsScorerAgent | Calls `AtsTools.calculateAtsScoreAfter()` |
| CriticAgent | Calls `CriticTools` methods + one `com.google.genai.Client` call for fabrication |
| HtmlRendererAgent | Renders Handlebars template to HTML string |
| ReportGeneratorAgent | Builds markdown report via `StringBuilder` |

---

### Component 4: Tool Classes

#### [NEW] `DocumentParserTools.java`
Methods annotated for `FunctionTool` registration:
- `parsePdf(byte[] fileBytes)` → **Apache PDFBox** `PDDocument` + `PDFTextStripper` with page-boundary markers
- `parseDocx(byte[] fileBytes)` → **Apache POI** `XWPFDocument`
- `parsePlainText(String text)` → passthrough
- `parseResumeFile(String filePath)` → file read + dispatch

#### [NEW] `JdAnalyzerTools.java`
Regex-based, direct port:
- `checkJdAuthenticity(String jdText)` — JD marker scoring
- `extractSenioritySignals(String jdText)` — seniority ladder + years regex
- `extractAtsKeywords(String jdText)` — tech pattern matching
- `extractJobMetadata(String jdText)` — employment type, work model

#### [NEW] `AlignmentTools.java`
- `compareSeniorityLevels()` with `SENIORITY_LADDER` map
- `checkDomainAlignment()` with fuzzy substring matching

#### [NEW] `AtsTools.java`
- `detectAtsUnfriendlyFormatting()` — multi-column, tables, special chars, repeated headers
- `calculateAtsScore()` / `calculateAtsScoreAfter()` — keyword match percentage

#### [NEW] `CriticTools.java`
- `estimatePageLength()` — word count → pages
- `detectKeywordStuffing()` — threshold > 4 occurrences

---

### Component 5: Model Layer (POJOs)

Jackson-annotated POJOs replacing Pydantic `BaseModel`:

```java
// Used for LLM structured output in JD Analyzer
public record JdExtractionResult(
    @JsonProperty("job_title") String jobTitle,
    @JsonProperty("required_skills") List<String> requiredSkills,
    @JsonProperty("preferred_skills") List<String> preferredSkills,
    @JsonProperty("core_responsibilities") List<String> coreResponsibilities
) {}

// Used for Resume Rewriter structured output
public record ContactInfo(String name, String email, String phone, String location, String linkedin) {}
public record ExperienceEntry(String title, String company, String dates, List<String> bullets, String entryType) {}
public record EducationEntry(String degree, String institution, String year) {}
```

---

### Component 6: REST API & Entry Points

#### [NEW] `ResumeOptimizerController.java` — Spring MVC

```java
@PostMapping(value = "/api/v1/resume/optimize", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
public ResponseEntity<String> optimizeResume(
    @RequestParam("file") MultipartFile file,
    @RequestParam("job_description") String jobDescription
) {
    // 1. Parse document bytes via DocumentParserTools
    // 2. Create InMemoryRunner with PipelineFactory.createPipeline()
    // 3. Create session with initial state (raw_resume_text, raw_jd_text)
    // 4. Run pipeline via runner.run()
    // 5. Extract HTML output + report from session state
    // 6. Save to output directory, return with custom headers
}
```

#### [NEW] `AdkDevServer.java` — Dev UI entry point

```java
public class AdkDevServer {
    public static void main(String[] args) {
        BaseAgent pipeline = PipelineFactory.createPipeline();
        AdkWebServer.start(pipeline);  // Same Dev UI as Python's `adk web`
    }
}
```

---

### Component 7: Configuration & Resources

#### [NEW] `application.properties`
```properties
# Model
model.name=gemini-2.0-flash
google.api.key=${GOOGLE_API_KEY}

# Pipeline
rewriter.sleep.ms=15000
output.directory=./output

# Server
server.port=8000
```

#### [NEW] `resume.hbs` (Handlebars template)
Ported from Jinja2 with syntax changes:
| Jinja2 | Handlebars |
|---|---|
| `{% if contact %}` | `{{#if contact}}` |
| `{% for job in experience %}` | `{{#each experience}}` |
| `{{ contact.name }}` | `{{contact.name}}` |
| `{% if job.entry_type is defined and job.entry_type == 'project' %}` | `{{#if (eq this.entryType "project")}}` |
| `{{ skill \| default('') }}` | `{{skill}}` (defaults in Java) |

---

## Translation Mapping Summary

### Python ADK → Java ADK (1:1 Framework Port)

| Python ADK | Java ADK |
|---|---|
| `from google.adk.agents import SequentialAgent` | `import com.google.adk.agents.SequentialAgent` |
| `from google.adk.agents import LlmAgent` | `import com.google.adk.agents.LlmAgent` |
| `from google.adk.agents import BaseAgent` | `import com.google.adk.agents.BaseAgent` |
| `from google.adk.runners import InMemoryRunner` | `import com.google.adk.runner.InMemoryRunner` |
| `from google.adk.events.event import Event` | `import com.google.adk.events.Event` |
| `from google.adk.events.event_actions import EventActions` | `import com.google.adk.events.EventActions` |
| `session.state["key"] = value` | `ctx.session().state().put("key", value)` |
| `state.get("key")` | `state.get("key")` |
| `output_key="..."` | `.outputKey("...")` |
| `SequentialAgent(sub_agents=[...])` | `SequentialAgent.builder().subAgents(...).build()` |
| `LlmAgent(name=..., model=..., instruction=...)` | `LlmAgent.builder().name(...).model(...).instruction(...).build()` |

### Library Replacements

| Python Library | Java Replacement |
|---|---|
| `pdfplumber` | Apache PDFBox 3.x (`PDDocument`, `PDFTextStripper`) |
| `python-docx` | Apache POI 5.x (`XWPFDocument`) |
| `jinja2` | Handlebars.java 4.x |
| `json` + Pydantic | Jackson `ObjectMapper` + Java Records |
| `re` (regex) | `java.util.regex.Pattern` + `Matcher` |
| `fastapi` + `uvicorn` | Spring Boot + embedded Tomcat |
| `python-dotenv` | dotenv-java |
| `google.genai.Client` | `com.google.genai.Client` (same SDK, Java version) |

---

## Verification Plan

### Automated Tests
1. `mvn clean compile` — Verify all 30+ classes compile without errors
2. `mvn test` — Spring Boot context loads, `PipelineFactory.createPipeline()` returns valid `SequentialAgent`
3. Tree output of generated `resume_optimizerv3/` directory

### Manual Verification
- Compare each Java agent's `execute()` logic against its Python `run_*()` function
- Verify Handlebars template renders identically to Jinja2 output
- Test `AdkDevServer` entry point to confirm ADK Dev UI launches

---

## Python → Java Workaround Notes

| Python Feature | Java Workaround | Risk |
|---|---|---|
| `PythonTaskNode(BaseAgent)` | Custom `DeterministicAgent extends BaseAgent` with `runAsyncImpl()` override | Low — clean ADK extension point |
| `pdfplumber.open(BytesIO(bytes))` | `Loader.loadPDF(InputStream)` + `PDFTextStripper` | Low — standard PDFBox API |
| `python-docx` `Document(BytesIO)` | `new XWPFDocument(InputStream)` | Low — standard POI API |
| Pydantic `BaseModel.model_json_schema()` for structured LLM output | Jackson ObjectMapper + manual JSON schema string construction | Medium — no auto-schema from POJOs for Gemini's `response_schema` |
| `re.findall()` with `re.IGNORECASE` | `Pattern.compile(regex, CASE_INSENSITIVE)` + `Matcher.find()` loop | Low |
| `async for event in runner.run_async()` | RxJava `Flowable` subscription (ADK Java is reactive) | Low — same framework |
| `time.sleep(15)` between LLM calls | `Thread.sleep(15_000)` with configurable property | Low |
| `asyncio.to_thread(func)` | Direct synchronous call inside `DeterministicAgent.execute()` | Low — pipeline is sequential |
