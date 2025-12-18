from state import AgentState
import config

def run_python_code(code: str):
    local_env = {}
    exec(code, {}, local_env)
    return local_env


def create_initial_state(question: str) -> AgentState:
    return AgentState(
        question=question,
        plan= "",
        reasoning_visible_to_user= "", 
        code= "",              
        intermediate_results= {},  
        final_answer= "",
        verification= "",  
        checks= [],      
        retries= 0,
        status= "",
    )    



def retry_decision(state: AgentState) -> str:
    
    if state["verification"] == "passed":
        state["status"] = "success"
        return "success"
    
    state["retries"] += 1

    if state["retries"] <= config.MAX_RETRIES:
        return "retry"
    
    if state["verification"] == "failed":
        state["status"] = "failed"
        return "failed"


