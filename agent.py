import streamlit as st
import json
import sys
from typing import Dict, Any
from graph import create_reasoning_graph
from state import create_initial_state, get_state_for_output
import config


class LangGraphReasoningAgent:

    def __init__(self):
        self.graph = create_reasoning_graph()
    
    def solve(self, question: str) -> Dict[str, Any]:

        initial_state = create_initial_state(question)

        try:
            final_state = self.graph.invoke(
                initial_state,
                config={"recursion_limit": config.MAX_ITERATIONS}
            )
            
            result = get_state_for_output(final_state)
            
            # Add debug info
            result["debug_info"] = {
                "final_state_status": final_state.get("status"),
                "error_message": final_state.get("error_message", ""),
                "retry_reasons": final_state.get("retry_reasons", []),
                "execution_error": final_state.get("execution_error", "")
            }
            
            return result
            
        except Exception as e:
            error_details = f"Error during execution: {str(e)}"
            if config.DEBUG_MODE:
                import traceback
                error_details += "\n" + traceback.format_exc()
                print(f"\n[ERROR] {error_details}")
            
            return {
                "answer": None,
                "status": "failed",
                "reasoning_visible_to_user": error_details,
                "metadata": {
                    "plan": "",
                    "checks": [],
                    "retries": 0
                },
                "debug_info": {
                    "exception": str(e)
                }
            }
    
    def solve_with_streaming(self, question: str):
       
        initial_state = create_initial_state(question)
        
        for state in self.graph.stream(initial_state):
            yield state

    def get_graph_visualization(self) -> str:

        try:
            return self.graph.get_graph().draw_mermaid()
        except Exception as e:
            return f"Visualization not available: {e}"


# ============================================================================================
# Streamlit App Configuration
# ============================================================================================


st.set_page_config(
    page_title="Multi-Step Reasoning Agent",
    layout="centered"
)

st.title("🧠 Multi-Step Reasoning Agent")
st.caption("Powered by LangGraph + OpenAI")

# Show API key status
if config.OPENAI_API_KEY and len(config.OPENAI_API_KEY) > 10:
    st.sidebar.success("✓ OpenAI API Key configured")
else:
    st.sidebar.error("✗ OpenAI API Key not found or invalid")
    st.error("Please configure your OPENAI_API_KEY in the .env file")

# Debug toggle
debug_mode = st.sidebar.checkbox("Enable Debug Mode", value=config.DEBUG_MODE)
if debug_mode:
    config.DEBUG_MODE = True
    st.sidebar.info("Debug mode enabled - check console for detailed logs")

# Initialize Agent
try:
    agent = LangGraphReasoningAgent()
    st.sidebar.success("✓ Agent initialized")
except Exception as e:
    st.sidebar.error(f"✗ Agent initialization failed: {e}")
    st.error(f"Failed to initialize agent: {e}")
    st.stop()

question = st.text_input(
    label="Enter your question",
    placeholder="e.g., If a train leaves at 14:30 and arrives at 18:05, how long is the journey?"
)

solve_clicked = st.button("Solve")

if solve_clicked:

    if question.lower().strip() in ['quit', 'exit', 'q']:
        st.info("Goodbye!")
    
    elif question.lower().strip() == 'graph':
        st.code(agent.get_graph_visualization())

    elif not question.strip():
        st.warning("Please enter a question.")

    else:
        with st.spinner("Thinking..."):
            result = agent.solve(question)

        st.divider()

        st.subheader("✅ Final Answer")
        
        # Fixed: Handle None answer properly
        if result["answer"] is not None:
            st.success(result["answer"])
        else:
            st.error("No answer generated")

        st.markdown("**Explanation:**")
        st.write(result["reasoning_visible_to_user"])

        with st.expander("🔍 Show Metadata (Debug / Evaluation)"):
            st.markdown("**Status**")
            st.code(result["status"])

            st.markdown("**Plan**")
            st.code(result["metadata"]["plan"])

            st.markdown("**Code**")
            st.code(result["code"])

            st.markdown("**Verification Checks**")
            st.json(result["metadata"]["checks"])

            st.markdown("**Retries**")
            st.code(result["metadata"]["retries"])
            
            # Show debug info
            if "debug_info" in result:
                st.markdown("**Debug Information**")
                st.json(result["debug_info"])
