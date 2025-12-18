from typing import Dict, Any
from langchain_openai import ChatOpenAI
import config
from state import ReasoningState
from prompts import get_planner_prompt, get_executor_prompt, get_verifier_prompt
from utils import safe_execute_code, planner_llm, executor_llm, verifier_llm
import traceback


# ============================================================================
# PLANNER NODE
# ============================================================================

def planner_node(state: ReasoningState) -> Dict[str, Any]:
    
    try:
        prompt = get_planner_prompt(state["question"])
        
        if config.DEBUG_MODE:
            print(f"\n[PLANNER] Processing question: {state['question']}")
        
        response = planner_llm.invoke(prompt)
        
        if config.DEBUG_MODE:
            print(f"[PLANNER] Response type: {type(response)}")
            print(f"[PLANNER] Response: {response}")
        
        plan_steps = response.plan_steps  # This is now List[str]
        
        if not plan_steps:
            error_msg = "Could not parse plan from LLM - plan_steps is empty"
            if config.DEBUG_MODE:
                print(f"[PLANNER] ERROR: {error_msg}")
            return {
                "status": "planning_failed",
                "error_message": error_msg,
                "retries": 1
            }
        
        plan_text = response.plan_text
        
        if config.DEBUG_MODE:
            print(f"[PLANNER] Success! Generated {len(plan_steps)} steps")
        
        return {
            "plan_steps": plan_steps,
            "plan_text": plan_text,
            "status": "planned"
        }
        
    except Exception as e:
        error_msg = f"Planner error: {str(e)}"
        if config.DEBUG_MODE:
            print(f"[PLANNER] EXCEPTION: {error_msg}")
            traceback.print_exc()
        return {
            "status": "planning_failed",
            "error_message": error_msg,
            "retries": 1
        }


# ============================================================================
# EXECUTOR NODE
# ============================================================================

def executor_node(state: ReasoningState) -> Dict[str, Any]:

    try:
        if config.DEBUG_MODE:
            print(f"\n[EXECUTOR] Starting execution")
            print(f"[EXECUTOR] Plan steps: {state['plan_steps']}")
        
        # Format plan steps as a string
        plan_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(state["plan_steps"])])
        
        prompt = get_executor_prompt(state["question"], plan_str)
        
        response = executor_llm.invoke(prompt)
        
        if config.DEBUG_MODE:
            print(f"[EXECUTOR] Response received")
        
        code = response.python_code
        
        if not code:
            error_msg = "No code generated"
            if config.DEBUG_MODE:
                print(f"[EXECUTOR] ERROR: {error_msg}")
            return {
                "execution_error": error_msg,
                "code": "",
                "status": "execution_failed",
                "retries": 1,
                "retry_reasons": [error_msg]
            }
        
        code = code.strip()
        
        # Remove markdown code blocks if present
        if code.startswith("```python"):
            code = code.replace("```python", "").replace("```", "").strip()
        elif code.startswith("```"):
            code = code.replace("```", "").strip()
        
        if config.DEBUG_MODE:
            print(f"[EXECUTOR] Executing code:\n{code}")
        
        execution_result = safe_execute_code(code)
        
        if not execution_result['success']:
            error_msg = execution_result['error']
            if config.DEBUG_MODE:
                print(f"[EXECUTOR] Execution failed: {error_msg}")
            return {
                "execution_error": error_msg,
                "code": code,
                "status": "execution_failed",
                "retries": 1,
                "retry_reasons": [f"Execution error: {error_msg}"]
            }
        
        answer = execution_result['result']
        reasoning_of_the_solution = response.solution_reasoning
        
        if config.DEBUG_MODE:
            print(f"[EXECUTOR] Success! Answer: {answer}")
        
        return {
            "answer": answer,
            "code": code,
            "execution_error": "",
            "status": "executed",
            "solution_reasoning": reasoning_of_the_solution
        }
        
    except Exception as e:
        error_msg = f"Executor error: {str(e)}"
        if config.DEBUG_MODE:
            print(f"[EXECUTOR] EXCEPTION: {error_msg}")
            traceback.print_exc()
        return {
            "execution_error": error_msg,
            "status": "execution_failed",
            "retries": 1,
            "retry_reasons": [error_msg]
        }


# ============================================================================
# VERIFIER NODE
# ============================================================================

def verifier_node(state: ReasoningState) -> Dict[str, Any]:
    
    try:
        if config.DEBUG_MODE:
            print(f"\n[VERIFIER] Verifying answer: {state['answer']}")
        
        prompt = get_verifier_prompt(state["question"], state["answer"], state["code"])
        
        response = verifier_llm.invoke(prompt)
        verification_data = response.verification
        verification_reasoning = response.verification_reasoning
        
        if not verification_data:
            if config.DEBUG_MODE:
                print(f"[VERIFIER] ERROR: No verification data")
            return {
                "verification": {},
                "verification_passed": False,
                "status": "verification_failed",
                "retries": 1
            }
        
        verdict = response.verdict
        checks = [check.model_dump() for check in response.checks]
        
        if config.DEBUG_MODE:
            print(f"[VERIFIER] Verdict: {verdict}, Checks: {len(checks)}")
        
        sanity_checks = perform_sanity_checks(state["answer"])
        all_checks = checks + sanity_checks
        
        # Determine if passed
        passed = verdict == "pass" and all(c.get("passed", False) for c in sanity_checks)

        if config.DEBUG_MODE:
            print(f"[VERIFIER] Final result: {'PASSED' if passed else 'FAILED'}")
        
        # If failed, prepare retry reason
        updates = {
            "verification": verification_data,
            "verification_passed": passed,
            "checks": all_checks,
            "status": "verified" if passed else "verification_failed",
            "verification_reasoning": verification_reasoning
        }
        
        if not passed:
            reasoning = response.verification_reasoning
            suggested_fix = response.suggested_fix or "Please review the solution"
            retry_reason = f"{reasoning}. {suggested_fix}".strip()
            updates["retry_reasons"] = [retry_reason]
            updates["retries"] = 1
        
        return updates
        
    except Exception as e:
        error_msg = f"Verifier error: {str(e)}"
        if config.DEBUG_MODE:
            print(f"[VERIFIER] EXCEPTION: {error_msg}")
            traceback.print_exc()
        return {
            "verification": "",
            "verification_passed": False,
            "status": "verification_failed",
            "retries": 1,
            "retry_reasons": [error_msg]
        }


def perform_sanity_checks(answer: Any) -> list:

    checks = []
    
    # Check 1: Not empty
    if answer is None or (isinstance(answer, str) and answer.strip() == ""):
        checks.append({
            'check_name': 'sanity_not_empty',
            'passed': False,
            'details': 'Answer is empty or None'
        })
    else:
        checks.append({
            'check_name': 'sanity_not_empty',
            'passed': True,
            'details': 'Answer is not empty'
        })
    
    # Check 2: Reasonable magnitude for numbers
    if isinstance(answer, (int, float)):
        if answer < -1000000 or answer > 1000000:
            checks.append({
                'check_name': 'sanity_reasonable_magnitude',
                'passed': False,
                'details': f'Number {answer} seems unreasonably large or small'
            })
        else:
            checks.append({
                'check_name': 'sanity_reasonable_magnitude',
                'passed': True,
                'details': 'Number magnitude is reasonable'
            })
    
    # Check 3: No error messages in answer
    if isinstance(answer, str):
        if any(word in answer.lower() for word in ['error', 'exception', 'traceback']):
            checks.append({
                'check_name': 'sanity_no_error_message',
                'passed': False,
                'details': 'Answer contains error-like text'
            })
        else:
            checks.append({
                'check_name': 'sanity_no_error_message',
                'passed': True,
                'details': 'Answer does not contain error messages'
            })
    
    return checks


# ============================================================================
# FINALIZER NODE
# ============================================================================

def finalizer_node(state: ReasoningState) -> Dict[str, Any]:

    if config.DEBUG_MODE:
        print(f"\n[FINALIZER] Final status determination")
        print(f"[FINALIZER] Verification passed: {state.get('verification_passed')}")
        print(f"[FINALIZER] Total retries: {state.get('retries')}")
    
    if state["verification_passed"]:
        # Success case
        reasoning = state.get("solution_reasoning", "") or state.get("verification_reasoning", "Solution verified successfully")
        if config.DEBUG_MODE:
            print(f"[FINALIZER] SUCCESS")
        return {
            "status": "success",
            "reasoning": reasoning
        }
    else:
        # Failure case
        verification_reasoning = state.get("verification_reasoning", "")
        solution_reasoning = state.get("solution_reasoning", "")
        error_message = state.get("error_message", "")
        retry_reasons = state.get("retry_reasons", [])
        
        # Construct reasoning from available information
        if verification_reasoning:
            reasoning = f"Unable to verify the solution. {verification_reasoning}"
        elif error_message:
            reasoning = f"Error: {error_message}"
        elif retry_reasons:
            reasoning = f"Failed after retries. Last reason: {retry_reasons[-1]}"
        elif solution_reasoning:
            reasoning = f"Solution attempted but verification failed. {solution_reasoning}"
        else:
            reasoning = "Unable to solve the problem after multiple attempts"
        
        if config.DEBUG_MODE:
            print(f"[FINALIZER] FAILED: {reasoning}")
        
        return {
            "status": "failed",
            "reasoning": reasoning,
            "error_message": "Failed after all retries"
        }
