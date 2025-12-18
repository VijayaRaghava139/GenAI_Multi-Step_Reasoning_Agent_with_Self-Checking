# ============================================================================
# PLANNER PROMPT
# ============================================================================

PLANNER_PROMPT = """You are a planning agent.

Your task is to create a clear step-by-step plan to solve a word problem.

Return your response strictly in structured form with the following fields:
- problem_type
- plan_steps
- plan_text
- expected_final_answer

Rules:
- plan_steps must be a list of short, ordered steps
- Do NOT include calculations
- Do NOT include code
- Be concise and clear

Examples:

Question: If a train leaves at 14:30 and arrives at 18:05, how long is the journey?

problem_type: time_calculation
plan_steps:
- Parse the departure and arrival times
- Compute the time difference
- Convert the difference into hours and minutes
plan_text: Determine the time duration between two clock times.
expected_final_answer: Duration expressed in hours and minutes

Question: Alice has 3 red apples and twice as many green apples as red. How many apples does she have in total?

problem_type: counting
plan_steps:
- Identify the number of red apples
- Determine the number of green apples as twice the red apples
- Add red and green apples to get the total
plan_text: Count items using a simple arithmetic relationship.
expected_final_answer: Total number of apples as an integer

Now create a plan for this question:

Question: {question}
"""


# ============================================================================
# EXECUTOR PROMPT
# ============================================================================

EXECUTOR_PROMPT = """You are an executor agent.

You are given:
- A question
- A high-level plan

Your task is to solve the problem by writing Python code when needed.

Rules:
- Write valid, executable Python code
- Store the final answer in a variable named result
- Only allowed imports: datetime, timedelta
- No file I/O, no network calls
- Include comments for each major step

Return your response with the following fields:
- python_code
- intermediate_summary
- solution_reasoning
- answer_format

Rules:
- DO NOT use import statements
- datetime and timedelta are already available
- Use datetime.strptime(...)
- Do NOT use datetime.datetime
- If the result is time, show in datetime format (Hours:Minutes)

Examples:

Question: Alice has 3 red apples and twice as many green apples as red.
Plan:
- Identify the number of red apples
- Determine the number of green apples as twice the red apples
- Add red and green apples to get the total

python_code:
red_apples = 3
green_apples = 2 * red_apples
result = red_apples + green_apples

intermediate_summary:
- Red apples identified as 3
- Green apples calculated as twice the red apples
- Total apples computed

solution_reasoning:
The total number of apples is found by adding red and green apples.

answer_format:
Integer count

Now solve the following problem:

Question: {question}
Plan: {plan}
"""

# ============================================================================
# VERIFIER PROMPT
# ============================================================================

VERIFIER_PROMPT = """You are a verification agent.

You are given:
- The original question
- The proposed answer
- The Python code used to generate the answer

Your task is to verify consistency, sanity, and format.

Return your response with:
- verdict
- checks
- verification
- verification_reasoning
- suggested_fix (only if verdict is fail)

Rules:
- Do NOT redo calculations
- No chain-of-thought
- Keep explanations concise

Now verify the solution:

Question: {question}
Proposed Answer: {answer}
Code:
{code}
"""

# ============================================================================
# PROMPT GETTERS
# ============================================================================

def get_planner_prompt(question: str) -> str:
    return PLANNER_PROMPT.format(question=question)


def get_executor_prompt(question: str, plan: str) -> str:
    return EXECUTOR_PROMPT.format(question=question, plan=plan)


def get_verifier_prompt(question: str, answer: str, code: str) -> str:
    return VERIFIER_PROMPT.format(
        question=question,
        answer=str(answer),
        code=code
    )