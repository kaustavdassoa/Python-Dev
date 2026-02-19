"""
Tests for the tool_agent module.

These tests verify the agent's configuration, structure, and tool bindings
without making actual LLM API calls.
"""

import os
import unittest
from unittest.mock import patch, MagicMock


class TestAgentConfiguration(unittest.TestCase):
    """Test that the agent is configured correctly."""

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-api-key-12345"})
    def setUp(self):
        """Import the agent module with a mocked API key."""
        # Re-import to pick up the patched env var
        import importlib
        import tool_agent.agent as agent_module

        importlib.reload(agent_module)
        self.agent = agent_module.root_agent

    def test_agent_name(self):
        """Agent should be named 'tool_agent'."""
        self.assertEqual(self.agent.name, "tool_agent")

    def test_agent_model(self):
        """Agent should use the gemini-2.0-flash model."""
        self.assertEqual(self.agent.model, "gemini-2.0-flash")

    def test_agent_description(self):
        """Agent should have a description set."""
        self.assertEqual(self.agent.description, "Tool agent")

    def test_agent_instruction_is_set(self):
        """Agent should have non-empty instructions."""
        self.assertIsNotNone(self.agent.instruction)
        self.assertIn("google_search", self.agent.instruction)

    def test_agent_has_tools(self):
        """Agent should have at least one tool configured."""
        self.assertIsNotNone(self.agent.tools)
        self.assertGreater(len(self.agent.tools), 0)

    def test_agent_has_google_search_tool(self):
        """Agent should have google_search in its tools list."""
        from google.adk.tools import google_search

        self.assertIn(google_search, self.agent.tools)

    def test_root_agent_is_agent_instance(self):
        """root_agent should be an instance of Agent."""
        from google.adk.agents import Agent

        self.assertIsInstance(self.agent, Agent)


class TestEnvironmentSetup(unittest.TestCase):
    """Test environment variable handling."""

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    def test_api_key_present(self):
        """No warning when GOOGLE_API_KEY is set."""
        self.assertIsNotNone(os.getenv("GOOGLE_API_KEY"))

    @patch.dict(os.environ, {}, clear=True)
    def test_api_key_missing_prints_warning(self, ):
        """Should print a warning when GOOGLE_API_KEY is missing."""
        import importlib

        with patch("builtins.print") as mock_print:
            import tool_agent.agent as agent_module
            importlib.reload(agent_module)
            mock_print.assert_any_call(
                "Warning: GOOGLE_API_KEY not found in environment"
            )


class TestModuleImports(unittest.TestCase):
    """Test that all required imports are available."""

    def test_import_agent_class(self):
        """Should be able to import Agent from google.adk.agents."""
        from google.adk.agents import Agent

        self.assertIsNotNone(Agent)

    def test_import_google_search(self):
        """Should be able to import google_search tool."""
        from google.adk.tools import google_search

        self.assertIsNotNone(google_search)

    def test_import_dotenv(self):
        """Should be able to import load_dotenv."""
        from dotenv import load_dotenv

        self.assertIsNotNone(load_dotenv)

    def test_import_root_agent(self):
        """Should be able to import root_agent from the agent module."""
        from tool_agent.agent import root_agent

        self.assertIsNotNone(root_agent)


if __name__ == "__main__":
    unittest.main()
