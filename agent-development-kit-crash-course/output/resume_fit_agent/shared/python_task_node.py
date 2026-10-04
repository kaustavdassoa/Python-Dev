import traceback
from typing import Callable, Any
from pydantic import Field
from google.adk.agents import BaseAgent

class PythonTaskNode(BaseAgent):
    """
    A deterministic agent node that wraps a standard Python callable.
    It executes without making LLM API calls, drastically reducing token usage.
    
    If the callable raises an exception, the node catches it and sets a 
    'pipeline_halted' state flag so downstream agents can gracefully skip execution.
    """
    
    task_func: Callable[[dict], Any] = Field(
        description="The deterministic Python function to run. It should accept the state dictionary and return whatever needs to be written to the output_key."
    )
    output_key: str = Field(
        description="The state key to write the result to."
    )

    async def _run_async_impl(self, ctx: Any) -> Any:
        state = ctx.session.state
        # Check if pipeline was already halted
        if state.get("pipeline_halted"):
            return

        # Inject session_id into state so tasks can use it for file generation
        state["__session_id"] = getattr(ctx.session, "id", "unknown_session")

        try:
            # Execute the deterministic function
            result = self.task_func(state)
            
            # Write result
            state[self.output_key] = result
            
        except Exception as e:
            # Catch all errors (e.g. malformed JSON parsing) and set error flag
            state["pipeline_halted"] = True
            error_msg = f"Error in {self.name}: {str(e)}"
            state["halt_reason"] = error_msg
            state[self.output_key] = {"success": False, "error": error_msg}
            print(f"❌ PIPELINE HALTED in {self.name}: {e}")
            traceback.print_exc()
            
        from google.adk.events.event import Event
        from google.genai import types
        
        # Determine what to display in the UI for this deterministic node
        content_str = ""
        if isinstance(result, str):
            if result.startswith("---") or result.startswith("#"):
                # Markdown content (e.g., Report Generator)
                content_str = result
            elif "<html" in result.lower() or "<!doctype html" in result.lower():
                # HTML content (e.g., HTML Renderer)
                path_info = ""
                if result.startswith("File saved to:"):
                    path_info = result.split("\n")[0] + " | "
                content_str = f"✅ HTML Resume successfully rendered! {path_info}(Length: {len(result)} chars)"
            else:
                content_str = result
        elif isinstance(result, dict):
            import json
            content_str = f"```json\n{json.dumps(result, indent=2)}\n```"
        else:
            content_str = f"✅ Task completed successfully. Returned type: {type(result).__name__}"
            
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(parts=[types.Part.from_text(text=content_str)], role="model"),
            actions={}
        )
