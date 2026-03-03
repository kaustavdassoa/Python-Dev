"""
Test runner for the Resume Evaluator (JSON) agent.

Runs the agent against all 3 test candidate profiles
(Strong Fit, Moderate Fit, Weak Fit) using the sample JD,
and saves each JSON result to the /data/ folder.

Usage:
    cd e:\GitHub\Python-Dev\agent-development-kit-crash-course\Resume_Builder
    python -m resume_evaluator_json.run_tests
"""

import asyncio
import json
import os
import sys

from dotenv import load_dotenv

# Load env before importing agent (needs GOOGLE_API_KEY)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import resume_evaluator_json_agent
from .test_data import TEST_CANDIDATES, SAMPLE_JD


OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "test_results"
)


async def run_evaluation(candidate_type: str, candidate_data: dict) -> dict:
    """Run the agent with one candidate profile and return the result."""

    session_service = InMemorySessionService()
    runner = Runner(
        agent=resume_evaluator_json_agent,
        app_name="resume_evaluator_json_test",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="resume_evaluator_json_test",
        user_id="test_user",
    )

    # Build the prompt — feed the candidate data directly as context
    prompt = (
        f"Here is the candidate's resume data (already extracted):\n\n"
        f"```json\n{json.dumps(candidate_data, indent=2)}\n```\n\n"
        f"Evaluate this candidate against the following Job Description:\n\n"
        f"{SAMPLE_JD}"
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    result = None
    async for event in runner.run_async(
        session_id=session.id,
        user_id="test_user",
        new_message=user_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                result = event.content.parts[0].text

    return result


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 60)
    print("  Resume Evaluator JSON — Test Runner")
    print("=" * 60)
    print(f"\nTesting {len(TEST_CANDIDATES)} candidate profiles...\n")

    for candidate_type, candidate_data in TEST_CANDIDATES.items():
        name = candidate_data["candidate_name"]
        print(f"  [{candidate_type.upper()}] {name}...")

        try:
            result = await run_evaluation(candidate_type, candidate_data)

            if result:
                # Try to parse and pretty-print the JSON
                try:
                    parsed = json.loads(result)
                    pretty = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    parsed = None
                    pretty = result

                # Save to file
                out_file = os.path.join(
                    OUTPUT_DIR, f"result_{candidate_type}.json"
                )
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(pretty)

                # Print summary
                if parsed:
                    score = parsed.get("overall_match_score", "N/A")
                    fit = parsed.get("fit_category", "N/A")
                    print(f"    → Score: {score}%  |  {fit}")
                    print(f"    → Saved: {out_file}")

                    # Validate it's well-formed JSON
                    print(f"    → JSON valid: ✓")
                else:
                    print(f"    → WARNING: Output is not valid JSON!")
                    print(f"    → Raw output saved: {out_file}")
            else:
                print(f"    → ERROR: No response from agent")

        except Exception as e:
            print(f"    → ERROR: {e}")

        print()

    print("=" * 60)
    print("  All tests complete! Check results in:")
    print(f"  {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
