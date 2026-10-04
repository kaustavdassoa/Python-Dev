from google.adk.agents import LoopAgent, LlmAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

def exit_loop(tool_context: ToolContext):
  tool_context.actions.escalate = True
  return {}

code_writer_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="code_writer_agent",
    description="Writes Python code based on a user condition.",
	instruction="When given a condition, write the working python code. Make sure not to add comments and you don't need to adhere to Python best practices",
	output_key = 'python_program'
)

code_reviewer_agent = LlmAgent(
    model = 'gemini-2.5-flash',
    name="code_reviewer_agent",
    description="Reviews the provided Python code provides the review comment. ",
	instruction="""Review the python code {{python_program}} and provide your review comment. 
    Please make sure you are checking if proper comments are given and Python best practices are followed.
     When you think the code meets the required condition, respond exactly with the phrase "No Issues Found" """,
	output_key = 'reviewed_comments',
)
code_refiner_agent = LlmAgent(
    model = 'gemini-2.5-flash',
    name="code_refiner_agent",
    include_contents='none',
    description="Refines the provided Python code based on review comment provided.",
	instruction=""" Refine the provided Python code {{python_program}} based on review comments {{reviewed_comments}}.  
	If the review comment is *exactly* "No Issues Found" you MUST call the 'exit_loop' function. Do not output any text. 
	Do not add explanations. Either output the refined program OR call the exit_loop function.
	 """,
	tools=[exit_loop],
	output_key = 'python_program'
)

refinement_loop_agent = LoopAgent(
    name="refinement_loop_agent",
    sub_agents=[
        code_reviewer_agent,
        code_refiner_agent,
    ],
    max_iterations=5
)

root_agent = SequentialAgent(
    name="python_code_writter_agent",
    sub_agents=[
        code_writer_agent, # Run first to create initial doc
        refinement_loop_agent       # Then run the critique/refine loop
    ],
    description="Writes an initial python program and then iteratively refines it with review comments and exits using an exit tool."
)


