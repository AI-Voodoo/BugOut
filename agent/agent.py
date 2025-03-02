import requests
import json
import re
import os
import tempfile
import subprocess
import sys
from termcolor import colored
from agent.prompts import SYSTEM_PROMPT, error_prompt

######################################################################
# 1) HELPER: Extract lines around the error
######################################################################
def detect_error_lines(code_str, error_msg, context_radius=3):
    """
    Given the raw code string and an error message, attempt to find any line number
    references in the error. For each line number found, capture a small snippet of code
    (context_radius lines before and after).

    Returns a string with the relevant lines, or an empty string if none found.
    """
    line_numbers = re.findall(r"line\s+(\d+)", error_msg)
    if not line_numbers:
        return ""  # no line info found

    lines = code_str.split("\n")
    snippets = []

    for ln_str in line_numbers:
        try:
            ln = int(ln_str)
        except ValueError:
            continue

        start_index = max(0, ln - 1 - context_radius)
        end_index = min(len(lines), ln - 1 + context_radius + 1)
        snippet_lines = lines[start_index:end_index]

        snippet_annotated = []
        for i, _ in enumerate(range(start_index, end_index)):
            real_line_num = start_index + i + 1
            prefix = "==> " if real_line_num == ln else "    "
            snippet_annotated.append(f"{prefix}{real_line_num}: {snippet_lines[i]}")

        snippet_block = "\n".join(snippet_annotated)
        snippets.append(f"Relevant code around line {ln}:\n{snippet_block}\n")

    return "\n".join(snippets)


######################################################################
# 2) HELPER: Summarize the attempt with the LLM
######################################################################
def summarize_attempt_with_llm(llm_url, code, error_msg, iteration, token_limit=200):
    """
    Calls the LLM *again* to produce a short summary (~200 tokens) of:
      - The code snippet
      - The lines around the error, if any
      - The error message
    Then returns that short summary string.
    """
    relevant_snippet = detect_error_lines(code, error_msg)
    system_instruction = {
        "role": "system",
        "content": (
            "You are a helpful assistant that summarizes code in 5 sentences. "
            "Include the key functionality only and the error to provide context."
        )
    }
    user_input = {
        "role": "user",
        "content": (
            f"This is attempt #{iteration}. Please summarize:\n\n"
            f"--- CODE ---\n{code}\n\n"
            f"--- RELEVANT SNIPPET ---\n{relevant_snippet}\n\n"
            f"--- ERROR ---\n{error_msg}\n\n"
            f"Please keep it under ~{token_limit} tokens."
        )
    }
    conversation = [system_instruction, user_input]
    headers = {"Content-Type": "application/json"}
    data = {"messages": conversation}

    try:
        resp = requests.post(llm_url, headers=headers, data=json.dumps(data))
        resp.raise_for_status()
        summary_text = resp.text.strip()
    except Exception as e:
        fallback_summary = (
            f"Attempt #{iteration} - Summarizer call failed. Error excerpt: {error_msg[:100]}"
        )
        return fallback_summary

    return f"[SUMMARY OF ATTEMPT #{iteration}]\n{summary_text}\n"


######################################################################
# 3) HELPER: Analyze unit test output using the LLM
######################################################################
def analyze_unit_test_with_llm(content, llm_url, token_limit=200, max_attempts=15):
    """
    Calls the LLM *again* to produce an analysis of:
      - The unit test output file.
    It keeps calling the LLM with a reminder message until the response is
    properly formatted with the required [BOOL] and [SUMMARY] tags.
    Then returns a BOOL and a short summary string.
    """
    system_instruction = {
        "role": "system",
        "content": (
            "You are a helpful assistant that analyzes unit test code results in 5 sentences. "
            "You follow a strict format of: "
            "[BOOL] a **bool value** if the results passed or failed [/BOOL] "
            "[SUMMARY] a short summary of the results [/SUMMARY] "
            "**Note: Only provide a TRUE or FALSE value in the [BOOL] wrapper."
        )
    }
    user_input = {
        "role": "user",
        "content": (
            f"Below is the content of the unit test log file. Please analyze the results to see if the code has passed tests:\n\n"
            f"--- UNIT TEST LOG CONTENT ---\n{content}\n\n"
            f"Please keep it under ~{token_limit} tokens."
        )
    }
    conversation = [system_instruction, user_input]
    headers = {"Content-Type": "application/json"}
    reminder_msg = (
        "You forgot to properly enclose your response with the required [BOOL] and [SUMMARY] tags. "
        "Please resend your answer in the correct format."
    )
    
    attempts = 0
    llm_full_res = ""
    while attempts < max_attempts:
        attempts += 1
        try:
            data = {"messages": conversation}
            resp = requests.post(llm_url, headers=headers, data=json.dumps(data))
            resp.raise_for_status()
            llm_full_res = resp.text.strip()
        except Exception as e:
            return False, "Unit test analyzer call failed."
        
        # Parse out [BOOL] and [SUMMARY]
        bool_match = re.search(r'\[BOOL\]\s*(TRUE|FALSE)\s*\[/BOOL\]', llm_full_res, re.IGNORECASE)
        summary_match = re.search(r'\[SUMMARY\]\s*(.*?)\s*\[/SUMMARY\]', llm_full_res, re.DOTALL)
        
        if bool_match and summary_match:
            bool_value = bool_match.group(1).strip().upper()
            pass_fail = True if bool_value == "TRUE" else False
            summary = summary_match.group(1).strip()
            return pass_fail, summary
        else:
            # Append reminder message for re-attempt
            conversation.append({"role": "user", "content": reminder_msg})
    
    return False, f"Max attempts reached. Last response: {llm_full_res}"


######################################################################
# 4) Updated BugOutAgent Class with Final Check of Unit Test Results
######################################################################
class BugOutAgent:
    def __init__(self, llm_url, log_file):
        self.llm_url = llm_url
        self.log_file = log_file
        
        self.conversation = []
        self.max_iterations = 50
        
        # The initial system message
        system_msg = {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
        self.conversation.append(system_msg)

        self.user_request_msg = None
        self.attempts_summary = ""
        self.last_code = None

    def add_message(self, role, input_text):
        return {"role": role, "content": input_text}

    def call_llm(self):
        """
        Sends self.conversation to the LLM API and returns (final_text, code).
        """
        headers = {"Content-Type": "application/json"}
        code_marker = "```python"
        final_text = ""

        while code_marker not in final_text:
            data = {"messages": self.conversation}

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\nConversation:\n{self.conversation}")

            try:
                with requests.post(self.llm_url, headers=headers, data=json.dumps(data), stream=True) as r:
                    r.raise_for_status()
                    chunk_texts = []
                    for chunk in r.iter_content(chunk_size=None):
                        token_str = chunk.decode("utf-8")
                        print(colored(token_str, "yellow"), end="", flush=True)
                        chunk_texts.append(token_str)
                    final_text = "".join(chunk_texts)

                msg = self.add_message("assistant", final_text)
                self.conversation.append(msg)

                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\nLLM RAW Response:\n{final_text}")

            except Exception as e:
                print(colored(f"\n\nError during LLM API call:\n{str(e)}", "red"))
                return None, None

            code_blocks = re.findall(r'```python(.*?)```', final_text, re.DOTALL)
            if code_blocks:
                if len(code_blocks) == 1:
                    print("\n\nSingle code block found")
                    code = code_blocks[0].strip()
                else:
                    print("\n\nMultiple code blocks found")
                    code = "\n\n".join(block.strip() for block in code_blocks)

                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\nCode Generated:\n{code}")

                return final_text, code

            reminder_msg = (
                f"You forgot to properly enclose your code with {code_marker}.\n"
                "Please resend the response with proper Python code enclosures."
            )
            self.conversation.append(self.add_message("user", reminder_msg))

        return final_text, None

    def run_code(self, code, timeout=90):
        """Executes code in a subprocess and returns (success, result)."""
        print(colored(f"\n\n===>Executing Code:\n\n", "cyan"))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".py", delete=False) as tmp_file:
            script_path = tmp_file.name
            tmp_file.write(code)

        try:
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                return_code = proc.returncode

                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n\n=== Subprocess Execution (Timed Out) ===\n")
                    f.write(f"Script: {script_path}\n")
                    f.write(f"Timeout: {timeout} seconds\n")
                    f.write(f"STDOUT:\n{stdout}\n")
                    f.write(f"STDERR:\n{stderr}\n")

                print(colored("\n\nError: Code execution timed out!", "red"))
                return False, f"Execution timed out after {timeout} seconds."

            return_code = proc.returncode
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n=== Subprocess Execution ===\n")
                f.write(f"Script: {script_path}\n")
                f.write(f"Return code: {return_code}\n")
                f.write(f"STDOUT:\n{stdout}\n")
                f.write(f"STDERR:\n{stderr}\n")

            if return_code == 0:
                print(colored("\n\nGood Code Execution (no Python error)!", "green"))
                print("STDOUT:", stdout)
            else:
                print(colored("\n\nError Encountered (subprocess non-zero exit)!", "red"))
                print("STDERR:", stderr)

            os.remove(script_path)

            if return_code != 0:
                return False, f"Script exited with code {return_code}\n\nSTDERR:\n{stderr}"

            return True, stdout

        except Exception as e:
            print(colored(f"\n\nError Encountered:\n{str(e)}", "red"))
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n\nError Encountered:\n{str(e)}\n")
            return False, str(e)
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

    def final_check_unit_tests(self):
        """
        Final check after successful execution:
        - Look for unit test result files in the output/ directory.
        - Verify that at least one file (e.g., one with 'test' in its name) exists.
        - Read the file's contents to determine if tests passed.
        Returns (True, message) if the unit test results are valid,
        or (False, error_message) if not.
        """
        output_dir = "output"
        if not os.path.isdir(output_dir):
            return False, "Output directory 'output/' not found. Unit tests did not run."

        files = os.listdir(output_dir)
        if not files:
            return False, "Output directory 'output/' is empty. No unit test results found."

        for f in files:
            if "test" in f.lower() and f.endswith(".txt"):
                test_file = os.path.join(output_dir, f)
                try:
                    with open(test_file, "r", encoding="utf-8") as tf:
                        content = tf.read()
                        pass_fail, summary = analyze_unit_test_with_llm(content, self.llm_url, token_limit=200)
                        if pass_fail:
                            return True, "Unit tests passed."
                        else:
                            return False, summary
                except Exception as e:
                    return False, f"Error reading unit test file {test_file}: {str(e)}"

        return False, "No unit test result file found in output/ directory."

    def generate_and_refine(self, user_request):
        """
        Main refinement loop with:
          - Additional LLM-based summarization (200 tokens) of code and error.
          - Excerpting lines near the error.
          - A final check step that loads unit test results from output/ and verifies their validity.
        """
        self.user_request_msg = {"role": "user", "content": user_request}
        self.conversation.append(self.user_request_msg)

        for iteration in range(1, self.max_iterations + 1):
            # 1) Ask the LLM for code
            _, code = self.call_llm()
            if not code:
                continue

            if self.last_code is not None and code.strip() == self.last_code.strip():
                self.conversation.append(
                    self.add_message("user", "This code is identical to the previous attempt. Please try a new approach.")
                )
                continue
            self.last_code = code

            # 2) Run the code in a subprocess
            success, result = self.run_code(code)
            if success:
                print("\n\n=== Saving Generated Code Before Test Result Analysis ===\n\n")
                generated_code_iteration_path = self.code_out = f"output/generated_code_iteration-{iteration}.py"
                # Write the iteration code to your specified output file
                with open(generated_code_iteration_path, "w", encoding="utf-8") as f:
                    f.write(code)

                # === Final Check: Verify unit test results ===
                final_ok, final_message = self.final_check_unit_tests()
                if final_ok:
                    print(colored("\n\nFinal Check Passed: Unit tests are valid.", "green"))
                    return code, result
                else:
                    print(colored(f"\n\nFinal Check Failed: {final_message}", "red"))
                    # Summarize final check failure and update summary
                    iteration_summary = summarize_attempt_with_llm(
                        llm_url=self.llm_url,
                        code=code,
                        error_msg=final_message,
                        iteration=iteration,
                        token_limit=200
                    )
                    # Remove any stale code marker from the cumulative summary
                    marker = "Last Code Generated with Errors:"
                    if marker in self.attempts_summary:
                        idx = self.attempts_summary.rfind(marker)
                        self.attempts_summary = self.attempts_summary[:idx]
                    self.attempts_summary += iteration_summary + "\nLast Code Generated with Errors: " + code + "\n"
                    debug_msg = error_prompt(final_message)
                    system_msg = self.conversation[0]  # system prompt
                    user_req = self.conversation[1]    # original user request
                    summary_msg = self.add_message(
                        "assistant",
                        f"Here is a summary of all attempts so far:\n{self.attempts_summary}"
                    )
                    debug_msg_struct = self.add_message("user", debug_msg)
                    self.conversation = [
                        system_msg,
                        user_req,
                        summary_msg,
                        debug_msg_struct
                    ]
                    print(colored(f"===>Error feedback (final check) sent to LLM. Iteration {iteration}", "red"))
                    continue
            else:
                iteration_summary = summarize_attempt_with_llm(
                    llm_url=self.llm_url,
                    code=code,
                    error_msg=result,
                    iteration=iteration,
                    token_limit=200
                )
                # Remove any stale code marker from the cumulative summary
                marker = "Last Code Generated with Errors:"
                if marker in self.attempts_summary:
                    idx = self.attempts_summary.rfind(marker)
                    self.attempts_summary = self.attempts_summary[:idx]
                self.attempts_summary += iteration_summary + "\nLast Code Generated with Errors: " + code + "\n"
                debug_msg = error_prompt(result)
                system_msg = self.conversation[0]
                user_req = self.conversation[1]
                summary_msg = self.add_message(
                    "assistant",
                    f"Here is a summary of all attempts so far:\n{self.attempts_summary}"
                )
                debug_msg_struct = self.add_message("user", debug_msg)
                self.conversation = [
                    system_msg,
                    user_req,
                    summary_msg,
                    debug_msg_struct
                ]
                print(colored(f"===>Error feedback sent to LLM. Iteration {iteration}", "red"))

        return None, "Could not produce a working solution in time."
