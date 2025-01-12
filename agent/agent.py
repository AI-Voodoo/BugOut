import requests
import json
import re
from termcolor import colored

system = f"""
You are BugOut, an AI coding assistant.
You will explain your reasoning and produce Python code that solves the user's problem.
You will identify all code sections by using ```python\n[the code you generate]\n````
Do **not** add any additional comments int the ```python\n[the code you generate]\n````
If errors occur, you refine the code.
"""

class BugOutAgent:
    def __init__(self, llm_url, log_file):
        self.llm_url = llm_url
        self.conversation = []
        self.chain_of_thought = []
        self.max_iterations = 500
        self.log_file = log_file
        
        # Initial system message: instruct the LLM about its role.
        system_msg = {
            "role": "system",
            "content": system
        }
        self.conversation.append(system_msg)

    def add_message(self, role, input):
        msg = {
            "role": role,
            "content": input
            }
        return msg
    
    def call_llm(self):
        """Sends conversation to the LLM API and returns the generated code or message."""
        headers = {"Content-Type": "application/json"}

        code_marker = "```python"
        response = ""
        
        while code_marker not in response:
            data = {"messages": self.conversation}

            #logging 
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\nConversation:\n{self.conversation}")

            # Send the request to the LLM API
            try:
                response_json = requests.post(self.llm_url, headers=headers, data=json.dumps(data)).json()
                response = response_json.get("response", "")

                msg = self.add_message("assistant", response)
                self.conversation.append(msg)
                print(colored(f"\n\nRaw Response:\n{response}", "magenta"))

                #logging 
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\nLLM RAW Response:\n{response}")

            except Exception as e:
                print(colored(f"\n\nError during LLM API call:\n{str(e)}", "red"))
                return None, None

            # Attempt to extract Python code using regex
            code_match = re.search(r'```python(.*?)```', response, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                print(colored(f"\n\nGenerated Code:\n{code}", "cyan"))

                #logging 
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\nCode Generated:\n{code}")
                return response, code

            # If no valid code found, modify the LLM input to remind it to enclose the code
            reminder_msg = f"You forgot to properly enclose your code with {code_marker}.\nPlease resend the response with proper python code enclosures."
            msg = self.add_message("user", reminder_msg)
            self.conversation.append(msg)
    
    def run_code(self, code):
        """Executes code and returns success plus either local_env or error string."""
        try:
            global_env = {"__builtins__": __builtins__}  # Initialize global scope
            exec(code, global_env, global_env)

            # Log and inspect the environment
            print(colored(f"\n\nGood Code Execution!", "green"))
            print(f"Global Environment: {global_env.keys()}")

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\nGood Code Execution!")
                f.write(f"\nGlobal Environment: {list(global_env.keys())}")
            return True, global_env
        except Exception as e:
            # Log the error
            print(colored(f"\n\nError Encountered:\n{str(e)}", "red"))
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\nError Encountered:\n{str(e)}")
                f.write(f"\nGlobal Environment: {list(global_env.keys())}")
            return False, str(e)

    
    def generate_and_refine(self, user_request):
        """Main refinement loop."""
        self.conversation.append({"role": "user", "content": user_request})

        for iteration in range(self.max_iterations):
            # Step 1: Generate code
            response, code = self.call_llm()
            self.chain_of_thought.append(response)

            # Step 2: Execute the code
            success, result = self.run_code(code)

            if success:
                # Stop looping and return if the code executes successfully
                print(colored(f"\n\nCode ran successfully. Refinement complete.", "green"))
                #print(colored(f"Code Result:\n{result}", "green"))

                #with open(self.log_file, "a", encoding="utf-8") as f:
                    #f.write(f"\n\nCode Result:\n{result}")
                return code, result
            else:
                # Append feedback only on failure
                error_msg = result
                reminder_msg = f"Your code produced an error: {error_msg}.\nPlease fix the code."
                msg = self.add_message("user", reminder_msg)
                self.conversation.append(msg)
                print(colored(f"Error feedback sent to LLM: {reminder_msg}", "yellow"))

        return None, "Could not produce a working solution in time."

