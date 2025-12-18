from langgraph.graph import StateGraph, START, END
from state import ReasoningState
from nodes import planner_node, executor_node, verifier_node, finalizer_node
import config


def should_retry(state: ReasoningState) -> str:
    retries = state.get("retries", 0)

    if state.get("verification_passed", False) or retries >= config.MAX_RETRIES:
        return "finalizer"

    return "planner"


def should_continue_after_execution(state: ReasoningState) -> str:
    retries = state.get("retries", 0)

    if state.get("status") == "executed":
        return "verifier"
    
    if retries >= config.MAX_RETRIES:
        return "finalizer"
    
    return "planner"


def create_reasoning_graph() -> StateGraph:
    
    workflow = StateGraph(ReasoningState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("finalizer", finalizer_node)
    
    # Add edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_conditional_edges(
        "executor", should_continue_after_execution, 
        {
            "verifier": "verifier",
            "planner": "planner",
            "finalizer": "finalizer"
        }
    )
    workflow.add_conditional_edges(
        "verifier", should_retry,
        {
            "finalizer": "finalizer",
            "planner": "planner"
        }
    )
    workflow.add_edge("finalizer", END)
    

    # Compile Graph
    app = workflow.compile()
    
    return app

if __name__ == "__main__":
    
    print("Creating reasoning graph...")
    graph = create_reasoning_graph()
    print("✓ Graph created successfully")
    