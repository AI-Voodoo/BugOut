import requests
import json
import re
import os
import tempfile
import subprocess
import sys
from termcolor import colored
from agent.prompts import SYSTEM_PROMPT, error_prompt

class BugOutAgent:
    def __init__(self, llm_url, log_file):
        self.llm_url = llm_url
        self.conversation = []
        self.max_iterations = 5000
        self.log_file = log_file
        
        # Initial system message: instruct the LLM about its role.
        system_msg = {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
        self.conversation.append(system_msg)

    def add_message(self, role, input):
        return {
            "role": role,
            "content": input
        }

    def call_llm(self):
        """
        Sends conversation to the LLM API and reads
        the response in streaming chunks.
        """
        headers = {"Content-Type": "application/json"}
        code_marker = "```python"
        final_text = ""

        while code_marker not in final_text:
            data = {"messages": self.conversation}

            # Logging
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\nConversation:\n{self.conversation}")

            # Use stream=True for chunked response
            try:
                with requests.post(self.llm_url, headers=headers, data=json.dumps(data), stream=True) as r:
                    r.raise_for_status()
                    # Read the chunks as they arrive
                    chunk_texts = []
                    for chunk in r.iter_content(chunk_size=None):
                        # Decode chunk
                        token_str = chunk.decode("utf-8")
                        # Print partial tokens to console
                        print(colored(token_str, "yellow"), end="", flush=True)
                        chunk_texts.append(token_str)

                    final_text = "".join(chunk_texts)

                # Now we have the full text for this iteration
                msg = self.add_message("assistant", final_text)
                self.conversation.append(msg)

                # Log the raw response
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\nLLM RAW Response:\n{final_text}")

            except Exception as e:
                print(colored(f"\n\nError during LLM API call:\n{str(e)}", "red"))
                return None, None

            # Extract Python code if present
            code_match = re.search(r'```python(.*?)```', final_text, re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\nCode Generated:\n{code}")
                return final_text, code

            # If no code found, ask again
            reminder_msg = (
                f"You forgot to properly enclose your code with {code_marker}.\n"
                "Please resend the response with proper Python code enclosures."
            )
            self.conversation.append(self.add_message("user", reminder_msg))

        return final_text, None
    
    def run_code(self, code):
        """Executes code in a subprocess and returns (success, result)."""
        # Create a temp .py file to run
        with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as tmp_file:
            script_path = tmp_file.name
            tmp_file.write(code)

        try:
            # Run the code in a new Python subprocess
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = proc.communicate()
            return_code = proc.returncode

            # Logging
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n=== Subprocess Execution ===\n")
                f.write(f"Script: {script_path}\n")
                f.write(f"Return code: {return_code}\n")
                f.write(f"STDOUT:\n{stdout}\n")
                f.write(f"STDERR:\n{stderr}\n")

            # Print to console as well
            if return_code == 0:
                print(colored("\n\nGood Code Execution (no Python error)!", "green"))
                print("STDOUT:", stdout)
            else:
                print(colored("\n\nError Encountered (subprocess non-zero exit)!", "red"))
                print("STDERR:", stderr)

            # Remove the temp file
            os.remove(script_path)

            # Decide success/failure
            if return_code != 0:
                # Non-zero exit => fail
                return False, f"Script exited with code {return_code}\n\nSTDERR:\n{stderr}"

            # (Optional) Add any further checks here
            # e.g., "Did the code produce a certain file?" 
            # If not, raise an error. For example:
            # 
            # if not os.path.exists("local_audit_report.json"):
            #     return False, "No local_audit_report.json file was created."

            # Return True with collected logs
            return True, stdout

        except Exception as e:
            # If we had a bigger-level error
            print(colored(f"\n\nError Encountered:\n{str(e)}", "red"))
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\nError Encountered:\n{str(e)}\n")
            return False, str(e)
        finally:
            # Cleanup in case something went wrong
            if os.path.exists(script_path):
                os.remove(script_path)

    def generate_and_refine(self, user_request):
        """Main refinement loop."""
        self.conversation.append({"role": "user", "content": user_request})

        for iteration in range(self.max_iterations):
            # 1. Generate code
            _, code = self.call_llm()

            # 2. Execute the code
            success, result = self.run_code(code)

            if success:
                # If no error from the script or our checks
                print(colored(f"\n\nCode ran successfully. Refinement complete.", "green"))
                return code, result
            else:
                # Append feedback on failure
                error_msg = result
                debug_msg = error_prompt(error_msg)
                self.conversation.append(self.add_message("user", debug_msg))

                # Trim older conversation, preserving system prompt at index 0
                while len(self.conversation) > 5:
                    self.conversation.pop(1)

                print(colored(f"===>Error feedback sent to LLM: {error_msg}", "red"))

        return None, "Could not produce a working solution in time."
