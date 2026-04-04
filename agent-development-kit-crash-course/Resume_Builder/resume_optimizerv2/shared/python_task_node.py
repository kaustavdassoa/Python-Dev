import time
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
            print(f"  ⏭️  {self.name}: Skipping — pipeline was halted by a previous agent.")
            return

        # Inject session_id into state so tasks can use it for file generation
        state["__session_id"] = getattr(ctx.session, "id", "unknown_session")

        print(f"\n  ⚙️  {self.name}: Executing deterministic task...")
        start_time = time.time()
        
        import asyncio
        state_delta = {}
        try:
            # Execute the deterministic function in a separate thread so it doesn't block the event loop
            result = await asyncio.to_thread(self.task_func, state)
            
            # Write result
            state_delta[self.output_key] = result
            
            elapsed = time.time() - start_time
            result_type = type(result).__name__
            result_size = len(result) if isinstance(result, (str, list, dict)) else "N/A"
            #Add list of keyInfo 
            keys_info = ""
            if isinstance(result, dict):
                keys_info = f" | New keys: {list(result.keys())}"

            #print(f"  ✅  {self.name}: Completed in {elapsed:.2f}s → {self.output_key} ({result_type}, size={result_size})")
            print(f"  ✅  {self.name}: Completed in {elapsed:.2f}s → {self.output_key} ({result_type}, size={result_size}){keys_info}")
            
        except Exception as e:
            # Catch all errors (e.g. malformed JSON parsing) and set error flag
            error_msg = f"Error in {self.name}: {str(e)}"
            state_delta["pipeline_halted"] = True
            state_delta["halt_reason"] = error_msg
            state_delta[self.output_key] = {"success": False, "error": error_msg}
            
            elapsed = time.time() - start_time
            print(f"  ❌  {self.name}: FAILED in {elapsed:.2f}s — {e}")
            traceback.print_exc()
            
        from google.adk.events.event import Event
        from google.adk.events.event_actions import EventActions
        from google.genai import types
        
        # Determine what to display in the UI for this deterministic node
        content_str = ""
        # Provide a default result variable in case of exception
        eval_result = result if 'result' in locals() else state_delta[self.output_key]
        
        if isinstance(eval_result, str):
            if eval_result.startswith("---") or eval_result.startswith("#"):
                # Markdown content (e.g., Report Generator)
                content_str = eval_result
            elif "<html" in eval_result.lower() or "<!doctype html" in eval_result.lower():
                # HTML content (e.g., HTML Renderer)
                path_info = ""
                if eval_result.startswith("File saved to:"):
                    path_info = eval_result.split("\n")[0] + " | "
                content_str = f"✅ HTML Resume successfully rendered! {path_info}(Length: {len(eval_result)} chars)"
            else:
                content_str = eval_result
        elif isinstance(eval_result, dict):
            import json
            content_str = f"```json\n{json.dumps(eval_result, indent=2)}\n```"
        else:
            content_str = f"✅ Task completed successfully. Returned type: {type(eval_result).__name__}"
            
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(parts=[types.Part.from_text(text=content_str)], role="model"),
            actions=EventActions(state_delta=state_delta)
        )
