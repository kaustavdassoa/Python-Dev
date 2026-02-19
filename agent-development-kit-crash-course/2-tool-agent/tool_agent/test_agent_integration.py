"""
Integration tests for the tool_agent that make actual LLM calls.

Requirements:
    - A valid GOOGLE_API_KEY in the .env file
    - Internet access (for Gemini API + Google Search)
    - They will consume API quota

Run with:
    cd e:/GitHub/Python-Dev/agent-development-kit-crash-course/2-tool-agent
    python -m unittest tool_agent.test_agent_integration -v
"""

import asyncio
import importlib
import time
import uuid
import unittest

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load .env before importing the agent
load_dotenv()

import tool_agent.agent as agent_module  # noqa: E402

# Force reload so any model changes in agent.py are picked up
importlib.reload(agent_module)
root_agent = agent_module.root_agent

APP_NAME = "tool_agent_test"
USER_ID = "test_user"

# Delay (in seconds) between tests to avoid hitting rate limits
DELAY_BETWEEN_TESTS = 5


def run_agent(user_message: str) -> str:
    """
    Helper: sends a single message to the agent and returns
    the final text response. Raises on API errors instead of
    silently returning empty.
    """
    session_service = InMemorySessionService()
    session_id = str(uuid.uuid4())

    # create_session is async in newer ADK versions
    asyncio.run(session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    ))

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=user_message)],
    )

    final_text = ""
    try:
        for event in runner.run(
            user_id=USER_ID,
            session_id=session_id,
            new_message=message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_text = event.content.parts[0].text
    except Exception as e:
        raise RuntimeError(f"Agent call failed: {e}") from e

    if not final_text:
        raise RuntimeError(
            "Agent returned empty response — likely a background thread error "
            "(check stderr for details, often a 429 quota error)."
        )

    return final_text


class TestAgentLLMIntegration(unittest.TestCase):
    """Integration tests that call the actual Gemini LLM."""

    def setUp(self):
        """Add a delay between tests to respect rate limits."""
        time.sleep(DELAY_BETWEEN_TESTS)

    def _run_or_skip(self, message: str) -> str:
        """Run the agent with the given message; skip test on quota errors."""
        try:
            return run_agent(message)
        except RuntimeError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "empty response" in str(e):
                self.skipTest(f"API quota exhausted or empty response: {e}")
            raise

    def test_simple_greeting(self):
        """Agent should respond to a simple greeting."""
        response = self._run_or_skip("Hello, how are you?")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0, "Agent returned an empty response")
        print(f"\n💬 Greeting response:\n{response}")

    def test_factual_question(self):
        """Agent should answer a factual question (may use google_search)."""
        response = self._run_or_skip("What is the capital of France?")
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        self.assertIn("Paris", response, "Expected 'Paris' in the response")
        print(f"\n💬 Factual response:\n{response}")

    def test_search_query(self):
        """Agent should handle a search-oriented query using google_search tool."""
        response = self._run_or_skip(
            "Search for the latest news about Python programming language"
        )
        self.assertIsInstance(response, str)
        self.assertGreater(
            len(response), 0, "Agent returned an empty response for search query"
        )
        print(f"\n🔍 Search response:\n{response}")

    def test_response_is_not_error(self):
        """Agent response should not contain common error indicators."""
        response = self._run_or_skip("Tell me a fun fact about space")
        self.assertIsInstance(response, str)
        self.assertNotIn("Error", response, "Response contains an error message")
        self.assertNotIn(
            "exception", response.lower(), "Response contains exception text"
        )
        print(f"\n🚀 Fun fact response:\n{response}")


class TestAgentMultiTurn(unittest.TestCase):
    """Test multi-turn conversation with the agent."""

    def test_multi_turn_conversation(self):
        """Agent should maintain context across multiple turns in a session."""
        session_service = InMemorySessionService()
        session_id = str(uuid.uuid4())

        # create_session is async in newer ADK versions
        asyncio.run(session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        ))

        runner = Runner(
            agent=root_agent,
            app_name=APP_NAME,
            session_service=session_service,
        )

        # Turn 1: introduce a topic
        msg1 = types.Content(
            role="user",
            parts=[types.Part(text="My favorite programming language is Python.")],
        )
        response1 = ""
        try:
            for event in runner.run(
                user_id=USER_ID, session_id=session_id, new_message=msg1
            ):
                if (
                    event.is_final_response()
                    and event.content
                    and event.content.parts
                ):
                    response1 = event.content.parts[0].text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                self.skipTest(f"API quota exhausted: {e}")
            raise

        if not response1:
            self.skipTest("Turn 1 returned empty — likely quota or background error")

        print(f"\n💬 Turn 1 response:\n{response1}")

        # Small delay before turn 2
        time.sleep(3)

        # Turn 2: refer back to the topic
        msg2 = types.Content(
            role="user",
            parts=[types.Part(text="What is my favorite programming language?")],
        )
        response2 = ""
        try:
            for event in runner.run(
                user_id=USER_ID, session_id=session_id, new_message=msg2
            ):
                if (
                    event.is_final_response()
                    and event.content
                    and event.content.parts
                ):
                    response2 = event.content.parts[0].text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                self.skipTest(f"API quota exhausted: {e}")
            raise

        if not response2:
            self.skipTest("Turn 2 returned empty — likely quota or background error")

        self.assertIn(
            "Python",
            response2,
            "Agent did not remember the favorite language from turn 1",
        )
        print(f"\n💬 Turn 2 response:\n{response2}")


if __name__ == "__main__":
    unittest.main()
