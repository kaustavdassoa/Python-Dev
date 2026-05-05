package com.resumeoptimizer.tools;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * JD Analyzer Tools — regex-based FunctionTool targets.
 * Direct port of Python's jd_analyzer/tools.py.
 */
public final class JdAnalyzerTools {

    private JdAnalyzerTools() {}

    // ── Seniority Ladder ─────────────────────────────────────────────
    private static final Map<String, Integer> SENIORITY_LEVELS = new LinkedHashMap<>();
    static {
        SENIORITY_LEVELS.put("intern", 0);
        SENIORITY_LEVELS.put("internship", 0);
        SENIORITY_LEVELS.put("entry", 1);
        SENIORITY_LEVELS.put("entry-level", 1);
        SENIORITY_LEVELS.put("junior", 1);
        SENIORITY_LEVELS.put("jr", 1);
        SENIORITY_LEVELS.put("associate", 1);
        SENIORITY_LEVELS.put("mid", 2);
        SENIORITY_LEVELS.put("mid-level", 2);
        SENIORITY_LEVELS.put("intermediate", 2);
        SENIORITY_LEVELS.put("senior", 3);
        SENIORITY_LEVELS.put("sr", 3);
        SENIORITY_LEVELS.put("lead", 4);
        SENIORITY_LEVELS.put("principal", 5);
        SENIORITY_LEVELS.put("staff", 5);
        SENIORITY_LEVELS.put("architect", 5);
        SENIORITY_LEVELS.put("director", 6);
        SENIORITY_LEVELS.put("vp", 7);
        SENIORITY_LEVELS.put("vice president", 7);
        SENIORITY_LEVELS.put("c-suite", 8);
        SENIORITY_LEVELS.put("cto", 8);
        SENIORITY_LEVELS.put("ceo", 8);
        SENIORITY_LEVELS.put("cpo", 8);
    }

    // ── Tech Keyword Patterns ────────────────────────────────────────
    private static final List<Pattern> TECH_PATTERNS = List.of(
        Pattern.compile("\\b(Python|Java|JavaScript|TypeScript|C\\+\\+|C#|Go|Rust|Swift|Kotlin|Ruby|PHP|Scala|R|MATLAB)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(AWS|Azure|GCP|Google Cloud|Docker|Kubernetes|Terraform|Jenkins|CI/CD|GitLab|GitHub Actions|Ansible|Helm)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(React|Angular|Vue|Node\\.js|Django|Flask|FastAPI|Spring|\\.NET|Express|Next\\.js|NestJS|Rails)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Cassandra|DynamoDB|BigQuery|Snowflake|Redshift)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(Machine Learning|Deep Learning|TensorFlow|PyTorch|scikit-learn|NLP|LLM|GenAI|AI|MLOps|Spark)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(Agile|Scrum|Kanban|DevOps|RESTful|GraphQL|Microservices|SOA|TDD|BDD|SOLID)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(Git|Jira|Confluence|Linux|Unix|Bash|PowerShell|Postman|Grafana|Prometheus|Datadog)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(leadership|communication|collaboration|problem.solving|analytical|critical thinking|mentoring)\\b", Pattern.CASE_INSENSITIVE)
    );

    // ── JD Marker Patterns ───────────────────────────────────────────
    private static final List<Pattern> JD_MARKERS = List.of(
        Pattern.compile("\\b(responsibilities|duties|what you'll do|your role)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(requirements|qualifications|what we're looking for|we are looking for)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(skills|experience|background|expertise)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(job description|about the role|about this role|position overview)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(engineer|developer|manager|analyst|designer|director|vp|lead|architect|specialist)\\b", Pattern.CASE_INSENSITIVE)
    );

    /**
     * Rule-based check: does the text look like a real job description?
     */
    public static Map<String, Object> checkJdAuthenticity(String jdText) {
        int wordCount = jdText.split("\\s+").length;
        int score = 0;

        for (Pattern marker : JD_MARKERS) {
            if (marker.matcher(jdText).find()) {
                score++;
            }
        }

        boolean lengthOk = wordCount >= 50;
        double confidence = (score / (double) JD_MARKERS.size()) * 0.7 + (lengthOk ? 0.3 : 0.0);
        boolean isAuthentic = confidence >= 0.35;

        String reason = isAuthentic
                ? "Text appears to be a valid job description."
                : String.format("Text does not appear to be a job description. Only %d/%d JD markers found and word count is %d.",
                        score, JD_MARKERS.size(), wordCount);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("is_authentic", isAuthentic);
        result.put("confidence", Math.round(confidence * 100.0) / 100.0);
        result.put("signals_found", score);
        result.put("word_count", wordCount);
        result.put("reason", reason);
        return result;
    }

    /**
     * Extract seniority level from JD using keywords and years-of-experience patterns.
     */
    public static Map<String, Object> extractSenioritySignals(String jdText) {
        // Extract years of experience
        Pattern yearsPattern = Pattern.compile(
                "(\\d+)\\+?\\s*(?:to\\s*\\d+)?\\s*years?\\s*(?:of\\s+)?(?:experience|exp\\.?)",
                Pattern.CASE_INSENSITIVE);
        Matcher yearsMatcher = yearsPattern.matcher(jdText);
        List<Integer> yearsList = new ArrayList<>();
        while (yearsMatcher.find()) {
            yearsList.add(Integer.parseInt(yearsMatcher.group(1)));
        }

        String detectedLevel = "mid";
        int levelScore = 2;
        List<String> detectedSignals = new ArrayList<>();

        for (Map.Entry<String, Integer> entry : SENIORITY_LEVELS.entrySet()) {
            Pattern keywordPattern = Pattern.compile(
                    "\\b" + Pattern.quote(entry.getKey()) + "\\b", Pattern.CASE_INSENSITIVE);
            if (keywordPattern.matcher(jdText).find()) {
                detectedSignals.add(entry.getKey());
                if (entry.getValue() > levelScore) {
                    levelScore = entry.getValue();
                    detectedLevel = entry.getKey();
                }
            }
        }

        // Override with max years if found
        if (!yearsList.isEmpty()) {
            int maxYears = Collections.max(yearsList);
            if (maxYears >= 15) { detectedLevel = "director"; levelScore = 6; }
            else if (maxYears >= 10) { detectedLevel = "lead"; levelScore = 4; }
            else if (maxYears >= 5) { detectedLevel = "senior"; levelScore = 3; }
            else if (maxYears >= 2) { detectedLevel = "mid"; levelScore = 2; }
            else { detectedLevel = "junior"; levelScore = 1; }
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("detected_level", detectedLevel);
        result.put("level_score", levelScore);
        result.put("signals_found", detectedSignals);
        result.put("years_required", yearsList);
        return result;
    }

    /**
     * Extract ATS-relevant keywords from JD using regex patterns.
     */
    public static Map<String, Object> extractAtsKeywords(String jdText) {
        Set<String> keywords = new TreeSet<>(String.CASE_INSENSITIVE_ORDER);

        for (Pattern pattern : TECH_PATTERNS) {
            Matcher matcher = pattern.matcher(jdText);
            while (matcher.find()) {
                String match = matcher.group(1).strip();
                if (!match.isEmpty()) {
                    keywords.add(match);
                }
            }
        }

        // Cap at top 30
        List<String> keywordList = new ArrayList<>(keywords);
        if (keywordList.size() > 30) {
            keywordList = keywordList.subList(0, 30);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("keywords", keywordList);
        result.put("total_found", keywordList.size());
        return result;
    }

    /**
     * Extract employment type and work model from JD.
     */
    public static Map<String, Object> extractJobMetadata(String jdText) {
        // Employment type
        String employmentType = "full-time";
        if (matches(jdText, "\\b(contract|contractor|freelance|1099)\\b")) {
            employmentType = "contract";
        } else if (matches(jdText, "\\b(part.time|part time)\\b")) {
            employmentType = "part-time";
        } else if (matches(jdText, "\\b(intern|internship)\\b")) {
            employmentType = "internship";
        }

        // Work model
        String workModel = "unspecified";
        if (matches(jdText, "\\b(remote|work from home|wfh)\\b")) {
            workModel = "remote";
        } else if (matches(jdText, "\\b(hybrid)\\b")) {
            workModel = "hybrid";
        } else if (matches(jdText, "\\b(on.site|onsite|in.office)\\b")) {
            workModel = "on-site";
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("employment_type", employmentType);
        result.put("work_model", workModel);
        return result;
    }

    private static boolean matches(String text, String regex) {
        return Pattern.compile(regex, Pattern.CASE_INSENSITIVE).matcher(text).find();
    }
}
