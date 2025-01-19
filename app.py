import os
from agent.agent import BugOutAgent

os.system("cls || clear")

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)  # Remove the file
        print(f"File '{file_path}' has been removed.")
    else:
        print(f"File '{file_path}' does not exist.")


if __name__ == "__main__":
    log_file = "logs/agent_log.txt"
    code_out = "output/generated_code.py"
    delete_file(log_file)

    agent = BugOutAgent("http://127.0.0.1:5000/generate", log_file)

    # this prompt was created by a multi-agent swarm
    user_query = """
**Instructions for the Coding Agent:**

Write Python scripts and unit tests using only Python standard libraries, Windows built-in commands, and pywin32 to accomplish the following red team–style tasks within a medium privilege context:

1. **Enumerate Services with Unquoted Paths**: Write a script that uses the 'sc query' command to list all services and checks for unquoted paths in their executable paths. Output should be in JSON format, listing the service name and its executable path.

2. **Enumerate Scheduled Tasks**: Write a script that uses the 'schtasks' command to list all scheduled tasks and their triggers. Output should be in JSON format, listing the task name, its trigger, and any other relevant details.

3. **Check Token Privileges**: Write a script that uses the 'whoami' command to list the privileges of the current token. Output should be in JSON format, listing each privilege.

4. **Enumerate and Analyze WMI Classes**: Write a script that uses the 'wmic' command to enumerate all WMI classes and their associated security descriptors. Output should be in JSON format, listing the class name, its associated security descriptor, and any misconfigurations or suspicious permissions.

5. **Enumerate and Analyze Local Accounts with Blank or Weak Passwords**: Write a script that uses the 'net user' command to enumerate all local accounts and checks their passwords for weakness using a simple strength check. Output should be in JSON format, listing the account name, its password status (blank or weak), and any other relevant details.

6. **ACL Misconfigurations**: Scan ACLs for misconfigurations in critical directories (e.g., C:\\Program Files, C:\\Windows) and report any findings.\n\nEnsure that your scripts do not rely on external tools or bypass UAC. The final results should be reported in a structured JSON format, with each task's findings clearly separated.

7. **Privilege Escalation Vulnerabilities:* Check for known privilege escalation vulnerabilities that can be exploited without bypassing UAC. This could provide more control over the system for potential future operations. 

8. Additionally, considering tasks that help us better understand the system's defenses could be beneficial.

**Constraints**:
- The scripts should not rely on external tools or dependencies.
- The scripts should not assume administrative rights.

**Desired Output/Format**:
- Each task's output should be in JSON format, with the structure specified above.
- The scripts should be written in Python, using the standard library and pywin32 for Windows-specific functionality.

**Unit Test**:
- **You must include unit tests** for each script to ensure their functionality and usability.
- The unit tests should be written in Python and use the 'unittest' module.

**Notes:**
- *Use pywin32 or native Windows commands as needed.
- Provide your solution as a single Python script **with embedded unit tests**
- Follow the PEP 8 style guide.**
"""
    final_code, result = agent.generate_and_refine(user_query)
    
    if final_code:
        print("\n\n=== Final Generated Code ===")
        print(final_code+"\n")
        print("=== Final Generated Code ===\n\n")

        # Write the final code to your specified output file
        with open(code_out, "w", encoding="utf-8") as f:
            f.write(final_code)
    else:
        print("=== No valid solution found ===\n\n")
        print(result+"\n\n")
