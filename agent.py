from graph import app
import streamlit as st
from utils import create_initial_state


# ============================================================================================
# Streamlit App Configuration
# ============================================================================================

st.set_page_config(
    page_title="Multi-Step Reasoning Agent",
    layout="centered"
)

st.title("🧠 Multi-Step Reasoning Agent")
st.caption("Powered by LangGraph + OpenAI")



question = st.text_input(
    label="Enter your question",
    placeholder="e.g., If a train leaves at 14:30 and arrives at 18:05, how long is the journey?"
)

state = create_initial_state(question)

solve_clicked = st.button("Solve")

if solve_clicked:

    if question.lower().strip() in ['quit', 'exit', 'q']:
        st.info("Goodbye!")

    elif question.lower().strip() in ['graph']:
        st.subheader("🧭 Agent Workflow")
        # mermaid_code = app.get_graph().draw_mermaid()
        # st.markdown(f"""{mermaid_code}""", unsafe_allow_html=True)
        st.graphviz_chart(app.get_graph().draw_mermaid())

    elif not question.strip():
        st.warning("Please enter a question.")
        
    else:
        with st.spinner("Thinking..."):
            result = app.invoke(state)

        st.divider()

        st.subheader("✅ Final Answer")
        
        # Fixed: Handle None answer properly
        if result["final_answer"] is not None:
            st.success(result["final_answer"])
        else:
            st.error("No answer generated")

        st.markdown("**status:**")
        if result["verification"] == "passed":
            st.write("success")
        else:
            st.write("failed")

        st.markdown("**reasoning_visible_to_user:**")
        st.write(result["reasoning_visible_to_user"])

        with st.expander("🔍 Show Metadata (Debug / Evaluation)"):

            st.markdown("**Plan**")
            st.code(result["plan"])

            st.markdown("**Code**")
            st.code(result["code"])

            st.markdown("**Checks**")
            st.json(result["checks"])

            st.markdown("**Retries**")
            st.code(result["retries"])
            


























# def solve(question: str, max_retries=2):
#     retries = 0

#     while retries <= max_retries:
#         state = {
#             "question": question,
#             "retries": retries
#         }

#         result = app.invoke(state)

#         if result["verification"] == "passed":
#             return {
#                 "answer": str(result["final_answer"]),
#                 "status": "success",
#                 "reasoning_visible_to_user": result["reasoning_visible_to_user"],
#                 "metadata": {
#                     "plan": result["plan"],
#                     "checks": result["checks"],
#                     "retries": retries
#                 }
#             }

#         retries += 1

#     return {
#         "answer": None,
#         "status": "failed",
#         "reasoning_visible_to_user": "Unable to verify solution.",
#         "metadata": {
#             "checks": result["checks"],
#             "retries": retries
#         }
#     }


# if __name__ == "__main__":
#     while True:
#         q = input("Question: ")
#         print(solve(q))

