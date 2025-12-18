from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Optional
from datetime import datetime, timedelta
import config

def safe_execute_code(code: str) -> Dict[str, Any]:

    # 1. Length safety check
    if len(code) > config.MAX_CODE_LENGTH:
        return {
            "success": False,
            "result": None,
            "error": "Code exceeds maximum length"
        }

    # 2. Restricted execution namespace
    namespace = {
        # Pre-injected safe modules (NO IMPORTS REQUIRED)
        "datetime": datetime,
        "timedelta": timedelta,

        "__builtins__": {
            # Allowed built-ins only
            "abs": abs,
            "int": int,
            "float": float,
            "str": str,
            "len": len,
            "min": min,
            "max": max,
            "sum": sum,
            "round": round,
            "range": range,
            "list": list,
            "dict": dict,
        },
    }

    try:
        # 3. Execute code safely
        exec(code, namespace)

        # 4. Extract result (preferred)
        if "result" in namespace:
            return {
                "success": True,
                "result": namespace["result"],
                "error": None
            }

        # 5. Fallback: last assigned variable
        result = None
        for line in reversed(code.strip().split("\n")):
            if "=" in line and not line.strip().startswith("#"):
                var_name = line.split("=", 1)[0].strip()
                if var_name in namespace:
                    result = namespace[var_name]
                    break

        return {
            "success": True,
            "result": result,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": str(e)
        }



# ============================================================================
# STRUCTURED LLM's
# ============================================================================

llm = ChatOpenAI(
    model=config.MODEL_NAME,
    api_key=config.OPENAI_API_KEY,
    max_tokens=2000
)

# ============================================================================
# PLANNER LLM
# ============================================================================

class PlannerOutput(BaseModel):
    problem_type: Literal["arithmetic", "time_calculation", "logic_constraints", "counting", "mixed", "unknown"] = Field(..., description="High-level classification of the problem domain")
    plan_steps: List[str] = Field(..., min_items=1, description="Concise ordered steps to solve the problem. No calculations.")  # Fixed: min_items instead of min_length
    plan_text: str = Field(..., description="High-level description of the plan as a short summarized explanation")
    expected_final_answer: str = Field(..., description=("High-level description of the expected final answer(e.g., 'duration in hours and minutes', 'total count of items'). Not the actual computed value."))
    

planner_llm = llm.with_structured_output(PlannerOutput)

# ============================================================================
# EXECUTOR LLM
# ============================================================================

class ExecutorOutput(BaseModel):
    python_code: str = Field(..., description=( "Write Python code if needed with following specifications,"
            "Executable Python code that follows the plan. "
            "Must store the final answer in a variable named `result`. "
            "Only allowed imports: datetime, timedelta. "
            "No file I/O or network calls. "
            "Must include comments for each major step.")
        )
    intermediate_summary: List[str] = Field(..., min_items=1, description=("High-level bullet summary of intermediate results or deductions. No calculations, no chain-of-thought."))
    solution_reasoning: str = Field(..., max_length=500, description=("Short, safe explanation of the approach in plain language. Must not include chain-of-thought, calculations, or hidden reasoning."))  # Increased max_length
    answer_format: str = Field(..., description=("Description of how the final answer is represented(e.g., 'string with hours and minutes', 'integer count')."))

executor_llm = llm.with_structured_output(ExecutorOutput)

# ============================================================================
# VERIFIER LLM
# ============================================================================

class VerificationCheck(BaseModel):
    check_name: Literal["correctness", "consistency", "sanity", "format"] = Field(..., description="Type of validation performed")
    passed: bool = Field(..., description="Whether this specific check passed")
    details: str = Field(..., min_length=5, max_length=500, description="Brief explanation of the check result. No chain-of-thought.")  # Increased max_length

class VerifierOutput(BaseModel):
    verification: str = Field(..., description="Explanation of the verification done")
    verdict: Literal["pass", "fail"] = Field(..., description="Overall verification outcome")
    checks: List[VerificationCheck] = Field(..., min_items=1, description="List of individual verification checks")
    verification_reasoning: str = Field(..., min_length=10, max_length=1000, description="High-level explanation of the overall verification result")  # Increased max_length
    suggested_fix: Optional[str] = Field(None, max_length=500, description=("If verdict is 'fail', suggest what should be corrected. Omit or leave null if verdict is 'pass'."))  # Increased max_length

verifier_llm = llm.with_structured_output(VerifierOutput)
