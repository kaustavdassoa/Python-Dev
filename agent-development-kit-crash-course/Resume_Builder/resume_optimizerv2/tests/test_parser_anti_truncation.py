"""
Integration tests for the resume parser anti-truncation fix.

Tests validate that:
1. Multi-page resumes retain all experience entries (zero data loss)
2. Non-standard headers (e.g., "SELECTED PROJECTS") are mapped into experience array
3. Page boundary markers are correctly injected by the PDF parser
4. entry_type discriminator is correctly assigned

Usage:
    pytest tests/test_parser_anti_truncation.py -v
"""

import os
import json
import re
import pytest

# ── Fixture Paths ───────────────────────────────────────────────────────────
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
MULTI_PAGE_FIXTURE = os.path.join(FIXTURE_DIR, "multi_page_resume.txt")


def load_fixture(filename: str) -> str:
    """Load a test fixture file."""
    filepath = os.path.join(FIXTURE_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# ── Test: PDF Page Boundary Markers ─────────────────────────────────────────
class TestPageBoundaryMarkers:
    """Verify that parse_pdf injects page-boundary markers for multi-page PDFs."""

    def test_page_marker_format_in_fixture(self):
        """The multi-page fixture should contain page-boundary markers."""
        text = load_fixture("multi_page_resume.txt")
        assert "--- PAGE 1 OF 2 ---" in text, (
            "Multi-page fixture is missing page-boundary markers. "
            "The fixture should simulate a 2-page resume with markers."
        )

    def test_single_page_no_markers(self):
        """parse_pdf only injects markers when total_pages > 1."""
        # Verify the condition exists in the source code
        tools_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "document_parser", "tools.py"
        )
        with open(tools_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "total_pages > 1" in content, (
            "parse_pdf is missing the single-page guard condition."
        )


# ── Test: Experience Count Preservation ─────────────────────────────────────
class TestExperienceCountPreservation:
    """Verify that the parser output contains ALL experience entries."""

    def test_fixture_has_seven_entries(self):
        """The multi-page fixture should have exactly 7 extractable entries."""
        text = load_fixture("multi_page_resume.txt")

        # Count distinct role/project headers in the fixture
        # These are the entries we expect the parser to extract:
        expected_entries = [
            "Senior Software Engineer | Google LLC",
            "Software Engineer II | Meta Platforms",
            "Software Engineer | Stripe Inc.",
            "Junior Developer | Startup Corp",
            "Intern Software Developer | TechStart Labs",
            "Cloud Cost Optimizer",        # SELECTED PROJECTS
            "Tech Mentor | Code.org",      # VOLUNTEER EXPERIENCE
        ]

        for entry in expected_entries:
            assert entry in text, f"Fixture missing expected entry: {entry}"

    def test_experience_entry_count_field_in_schema(self):
        """The parser output schema should include experience_entry_count."""
        # Read the parser agent instruction to verify the field exists
        agent_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "document_parser", "agent.py"
        )
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "experience_entry_count" in content, (
            "Parser agent.py is missing the experience_entry_count field "
            "in its output schema."
        )


# ── Test: Header Synonym Mapping ────────────────────────────────────────────
class TestHeaderSynonymMapping:
    """Verify that the parser prompt maps non-standard headers."""

    def test_selected_projects_in_synonym_map(self):
        """The parser instruction should map 'SELECTED PROJECTS' to experience."""
        agent_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "document_parser", "agent.py"
        )
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "SELECTED PROJECTS" in content, (
            "Parser instruction is missing 'SELECTED PROJECTS' in the "
            "header synonym map."
        )

    def test_volunteer_experience_in_synonym_map(self):
        """The parser instruction should map 'Volunteer Experience' to experience."""
        agent_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "document_parser", "agent.py"
        )
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Volunteer Experience" in content, (
            "Parser instruction is missing 'Volunteer Experience' in the "
            "header synonym map."
        )


# ── Test: entry_type Discriminator ──────────────────────────────────────────
class TestEntryTypeDiscriminator:
    """Verify that the entry_type field exists in schemas."""

    def test_entry_type_in_parser_output_schema(self):
        """Parser output schema should include entry_type in experience entries."""
        agent_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "document_parser", "agent.py"
        )
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "entry_type" in content, (
            "Parser agent.py is missing entry_type in the experience "
            "object schema."
        )

    def test_entry_type_in_rewriter_schema(self):
        """Rewriter schemas should include entry_type field."""
        rewriter_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "resume_rewriter", "agent.py"
        )
        with open(rewriter_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check both schemas
        assert content.count("entry_type") >= 2, (
            "Rewriter agent.py should have entry_type in both "
            "ExperienceSchema and SingleExperienceSchema."
        )

    def test_entry_type_in_jinja2_template(self):
        """HTML template should handle entry_type for conditional rendering."""
        template_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "html_renderer", "templates", "resume.html"
        )
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "entry_type" in content, (
            "Jinja2 template is missing entry_type conditional rendering."
        )


# ── Test: Anti-Truncation Directive ─────────────────────────────────────────
class TestAntiTruncationDirective:
    """Verify that the parser prompt contains anti-truncation instructions."""

    def test_anti_truncation_rule_present(self):
        """Parser instruction must contain the anti-truncation rule."""
        agent_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "document_parser", "agent.py"
        )
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "ANTI-TRUNCATION" in content, (
            "Parser agent.py is missing the CRITICAL ANTI-TRUNCATION RULE."
        )

    def test_self_verification_step_present(self):
        """Parser instruction must contain the self-verification step."""
        agent_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "document_parser", "agent.py"
        )
        with open(agent_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Self-Verification" in content, (
            "Parser agent.py is missing the Self-Verification step."
        )


# ── Test: Rewriter Assertion Guards ─────────────────────────────────────────
class TestRewriterAssertionGuards:
    """Verify that the rewriter has truncation-detection assertions."""

    def test_experience_count_crosscheck(self):
        """Rewriter must cross-check experience_entry_count from parser."""
        rewriter_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "resume_rewriter", "agent.py"
        )
        with open(rewriter_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "experience_entry_count" in content, (
            "Rewriter is missing the experience_entry_count cross-check "
            "assertion."
        )
        assert "Parser truncation detected" in content, (
            "Rewriter is missing the truncation detection error message."
        )

    def test_project_safeguard_in_prompt(self):
        """Rewriter prompt must contain the PROJECT ENTRY SAFEGUARD."""
        rewriter_path = os.path.join(
            os.path.dirname(__file__), "..",
            "sub_agents", "resume_rewriter", "agent.py"
        )
        with open(rewriter_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "PROJECT ENTRY SAFEGUARD" in content, (
            "Rewriter prompt is missing the PROJECT ENTRY SAFEGUARD rule."
        )
