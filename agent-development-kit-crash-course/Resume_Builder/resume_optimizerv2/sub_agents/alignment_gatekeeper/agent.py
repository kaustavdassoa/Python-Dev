import json
from ...shared.python_task_node import PythonTaskNode
from ...shared.utils import get_dict_from_state

class AbortPipelineError(Exception):
    pass

def run_gatekeeper(state: dict) -> str:
    val = get_dict_from_state(state.get("alignment_validator_output", {}))
            
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
