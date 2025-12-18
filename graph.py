from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from prompts import PLANNER_PROMPT, EXECUTOR_PROMPT, VERIFIER_PROMPT
from utils import run_python_code, retry_decision
from state import AgentState
import json
import config


llm = ChatOpenAI(
    model=config.MODEL_NAME, 
    api_key=config.OPENAI_API_KEY,
    temperature=0
)


#=========================================================================
# PLANNER, EXECUTOR AND VERIFIER NODES
#=========================================================================

def planner_node(state: AgentState):
    prompt = PLANNER_PROMPT.format(question=state["question"])
    plan = llm.invoke(prompt).content
    state["plan"] = plan
    return state


def executor_node(state: AgentState):
    prompt = EXECUTOR_PROMPT.format(
        question=state["question"],
        plan=state["plan"]
    )

    response = llm.invoke(prompt).content

    # Extract python code block
    code = response.split("```python")[1].split("```")[0]
    execution_result = run_python_code(code)
    
    state["code"] = code
    state["intermediate_results"] = execution_result
    state["final_answer"] = execution_result.get("result")
    return state


def verifier_node(state: AgentState):
    prompt = VERIFIER_PROMPT.format(
        question=state["question"],
        final_answer=state["final_answer"],
        intermediate_results=state["intermediate_results"]
    )

    response = json.loads(llm.invoke(prompt).content)
    state["reasoning_visible_to_user"] = response["reasoning_visible_to_user"]
    state["verification"] = response["verification"]
    state["checks"] = response["checks"]
    return state


#=========================================================================
# GRAPH DEFINITION
#=========================================================================

graph = StateGraph(AgentState)
graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("verifier", verifier_node)

graph.set_entry_point("planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", "verifier")
graph.add_conditional_edges(
    "verifier",
    retry_decision,
    {
        "retry": "planner",   
        "success": END,      
        "failed": END         
    }
)

app = graph.compile()
