from typing import TypedDict, Any, Annotated, List
import operator


class ReasoningState(TypedDict):

    question: str  
    plan_steps: List[str] 
    plan_text: str 
    answer: Any  
    code: str  
    execution_error: str 
    verification: str  
    verification_passed: bool 
    solution_reasoning: str
    retries: Annotated[int, operator.add]  
    retry_reasons: Annotated[List[str], operator.add]  
    status: str  
    error_message: str  
    checks: Annotated[List[dict], operator.add] 
    verification_reasoning: str 


# Helper function to create initial state
def create_initial_state(question: str) -> ReasoningState:
    return ReasoningState(
        question=question,
        plan_steps=[],
        plan_text="",
        answer=None,
        code="",
        execution_error="",
        verification="",
        verification_passed=False,
        solution_reasoning="",
        retries=0,
        retry_reasons=[],
        status="started",
        error_message="",
        checks=[],
        verification_reasoning=""
    )


def get_state_for_output(state: ReasoningState) -> dict:
    
    return {
        "answer": str(state.get("answer", "Unable to solve")),
        "status": "success" if state.get("status") == "success" else "failed",
        "code": state.get("code", ""),
        "reasoning_visible_to_user": state.get("solution_reasoning", "No reasoning available"),
        "metadata": {
            "plan": state.get("plan_text", ""),
            "checks": state.get("checks", []),
            "retries": state.get("retries", 0)
        }
    }
