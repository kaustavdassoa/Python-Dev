import json
from ...shared.python_task_node import PythonTaskNode

class AbortPipelineError(Exception):
    pass

def run_gatekeeper(state: dict) -> str:
    val = state.get("alignment_validator_output", {})
    
    if isinstance(val, str):
        import re
        match = re.search(r'```json\s*(.*?)\s*```', val, re.DOTALL)
        if match:
            clean_str = match.group(1)
        else:
            clean_str = val.strip()
        try:
            val = json.loads(clean_str)
        except Exception:
            val = {}
            
    if val.get("alignment_result") == "reject":
        reason = val.get("rejection_reason", "Candidate profile is not aligned with JD.")
        raise AbortPipelineError(f"Alignment check failed: {reason}")
    
    return "✅ Alignment approved. Continuing pipeline."

alignment_gatekeeper_node = PythonTaskNode(
    name="AlignmentGatekeeper",
    task_func=run_gatekeeper,
    output_key="alignment_gatekeeper_output",
    description="Deterministic node that halts the pipeline if alignment fails."
)
