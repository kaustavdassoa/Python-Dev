from google.adk.agents import Agent
from google.adk.tools import google_search
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Ensure keys are set (User's preferred method)
if not os.getenv("GOOGLE_API_KEY"):
    print("Warning: GOOGLE_API_KEY not found in environment")

# def get_current_time() -> dict:
#     """
#     Get the current time in the format YYYY-MM-DD HH:MM:SS
#     """
#     return {
#         "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#     }

root_agent = Agent(
    name="tool_agent",
    # model="gemini-2.0-flash",
    model="gemini-2.5-flash-lite",
    description="Tool agent",
    instruction="""
    You are a helpful assistant that can use the following tools: google_search ()
    """,
    tools=[google_search],
    # tools=[get_current_time],
    # tools=[google_search, get_current_time], # <--- Doesn't work
)

#adding it to prevent acidental calling of the below code when pagage is imported.
if __name__ == "__main__":
    import asyncio
    import uuid
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    APP_NAME = "tool_agent_test"
    USER_ID = "test_user"
    SESSION_ID = str(uuid.uuid4())

    # Create session and runner
    session_service = InMemorySessionService()

    # create_session is async in newer ADK versions
    asyncio.run(session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    ))

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    
    #adding print statements to debug
    print("=" * 50)
    print(f"🤖 Agent Name:  {root_agent.name}")
    print(f"🧠 Model:       {root_agent.model}")
    print(f"📝 Description: {root_agent.description}")
    print(f"📜 Instruction: {root_agent.instruction.strip()}")
    print(f"🛠️ Tools:       {[getattr(t, 'name', type(t).__name__) for t in root_agent.tools] if root_agent.tools else 'None'}")
    print("=" * 50)

    # Interactive loop - keep chatting until user types 'quit'
    while True:
        user_input = input("\n📝 You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            print("👋 Goodbye!")
            break

        message = types.Content(
            role="user",
            parts=[types.Part(text=user_input)],
        )

        print("\n💬 Agent: ", end="", flush=True)
        for event in runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=message,
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    print(event.content.parts[0].text)
                else:
                    print("(no response)")
                
                # Show token usage if available - checking both 'usage_metadata' (SDK) and 'usage' (ADK)
                usage = getattr(event, "usage_metadata", None) or getattr(event, "usage", None)
                if usage:
                    # Handle both UsageMetadata (SDK) and potential ADK wrappers
                    prompt_tokens = getattr(usage, "prompt_token_count", 0)
                    candidate_tokens = getattr(usage, "candidates_token_count", getattr(usage, "candidate_token_count", 0))
                    total_tokens = getattr(usage, "total_token_count", 0)
                    print(f"\n📊 Usage: Prompt: {prompt_tokens} | Completion: {candidate_tokens} | Total: {total_tokens}")

