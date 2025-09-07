import os
from flask import Flask, render_template, request, session, redirect
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.ai.agents import AgentsClient
from dotenv import load_dotenv
from azure.ai.agents.models import FunctionTool, ToolSet, ListSortOrder, MessageRole
from azure.ai.agents.models import FilePurpose, CodeInterpreterTool
from user_functions_ip import user_functions

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")  # Set a secret key for session

load_dotenv()
project_endpoint= os.getenv("PROJECT_ENDPOINT")
model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")   

# Connect to the Agent client    
agent_client = AgentsClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential
            (exclude_environment_credential=True,
            exclude_managed_identity_credential=True)
    )    


@app.route('/', methods=['GET', 'POST'])
def index():
    messages = None
    # Set up agent and thread if not already in session
    if 'agent_id' not in session or 'thread_id' not in session:
        code_interpreter = CodeInterpreterTool()
        functions = FunctionTool(user_functions)
        toolset = ToolSet()
        toolset.add(functions)
        agent_client.enable_auto_function_calls(toolset)
        agent = agent_client.create_agent(
            model=model_deployment,
            name="employee-agent",
            instructions="""You are an analyst agent for employees with primary task to recommened the best suitable employees for a project based on the skill prompted by analyzing employee skillsets, utilization and leave balance.
                            Follow these steps to answer the user query:
                            
                            1. Prompt the user to provide:
                                - The skill to be searched (e.g., "tester with Selinium", "Java developer").
                                - The desired availability window in days (e.g. "available in 15 days").
                                
                                After receiving the input:
                                - Extract the skill as a string.
                                - Extract the availability window as an integer using pattern matching (e.g., extract only  `15` which is integer from "available in 15 days").
                                - If either value is missing or ambiguous, prompt the user again for clarification before proceeding.

                            2.  Get the employee id's using the toolset by passing parameters from step 1 (skill as string and availability window as integer) to the toolset function. This step returns a list of dictionaries with 4 columns namely EmployeeId, EmployeeName, Employee Role and their Skills
                               
                            3.  for employees returned from step 2, you should should perform a skill reassessment using semantic matching and provide the distinct employeeid's along with their name
                            4.  for each of the employee returned, get their utilized hours using the toolset. This output is a list of dictionaries with 2 columns: 'EmployeeId' and 'UtilizedHours'.
                            5.  for each of the employee returned, also get their utilization target hours using the toolset. This output is a list of dictionaries with 2 columns: 'EmployeeId' and 'UtilizationTargetHours'.
                            6.  for each of the employee returned, also get their leave balance using the toolset. This output is a list of dictionaries with 2 columns: 'EmployeeId' and 'LeaveBalance'. Also if leave balance can be considered as 0, if no data available for an employee.
                            7.  Using the Code Interpretor Tool, for every employee matching the skill set , return the difference between UtilizationTargetHours and Utilized hours along will Employee Id , Employee Name and Leave Balance in a tabular format
                            8.  Also, rank the employee availability by considering the Target Hours, Utilized hours and Leave Balance
                        """,             
            tools=code_interpreter.definitions,            
            toolset=toolset,
        )
        thread = agent_client.threads.create()
        session['agent_id'] = agent.id
        session['thread_id'] = thread.id
    else:
        agent = agent_client.get_agent(session['agent_id'])
        thread = agent_client.threads.get(session['thread_id'])

    if request.method == 'POST':
        user_prompt = request.form.get('message')
        if user_prompt:
            # Send a prompt to the agent
            message = agent_client.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_prompt
            )
            run = agent_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
            # Check the run status for failures
            if run.status == "failed":
                last_msg = f"Run failed: {run.last_error}"
            else:
                # Show the latest response from the agent
                last_msg_obj = agent_client.messages.get_last_message_text_by_role(
                    thread_id=thread.id,
                    role=MessageRole.AGENT,
                )
                last_msg = last_msg_obj.text.value if last_msg_obj else None
            session['last_msg'] = last_msg

    # Get the conversation history
    messages = agent_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    return render_template('chat.html', messages=messages, last_msg=session.get('last_msg'))

@app.route('/clear')
def clear():
    session.pop('agent_id', None)
    session.pop('thread_id', None)
    session.pop('last_msg', None)
    return redirect('/')

if __name__ == '__main__':
    app.run()
