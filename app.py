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
    delete_file(log_file)

    agent = BugOutAgent("http://127.0.0.1:5000/generate", log_file)

    user_query = """
Write a Python script that performs a local Windows security audit without making any external network requests. Specifically:

Process Enumeration: List every running process. For each process, try to retrieve its:

Process ID (PID)
Executable path
Whether the file is signed (if possible with built-in modules or libraries you specify)
Basic integrity level (if available)
Auto-Run Locations: Enumerate common persistence points in the Windows Registry (e.g., HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run, HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run) and any scheduled tasks or services that automatically start with Windows.

For each entry, record the name and path.
Try to label anything that looks suspicious, e.g., blank file paths, references to non-existent files, or weird Unicode in the path.
Privilege/Group Checks: Determine if the current user is in the Administrators group or has elevated privileges. Also, list local groups for the current user session if possible.

Output:

Create a structured JSON (or CSV) file named local_audit_report.json summarizing all the collected data.
In that file, highlight any suspicious or potentially anomalous items (e.g., unverified signatures, unusual registry entries).
Print a short summary at the end of the script, e.g., total number of running processes, how many suspicious items were found, etc.
Testing:

Write a test (using unittest or pytest) that checks:
The JSON file exists.
The JSON file is not empty and has at least one process entry.
(Optional) If you flagged any suspicious items, confirm the data structure for them is correct.
Show how to run the test at the end of the script (or just run it in if __name__ == "__main__":).
Important:

Wrap your final Python code inside triple backticks like this: ```python [your complete solution] ```
If you require external libraries (e.g., win32api, win32security, ctypes, or any other modules), please mention them.
Focus on local enumeration with minimal overhead or logging (i.e., try not to be too “noisy”).
If there are any errors, refine your code until it runs successfully and passes your test.
Do not include any extra commentary inside the triple backticks—just the code.


**NOTE: ** 
    - The only non-standard pyhton library dependency you can use is pywin32. 
    - **DO NOT** import any non-standard pyhton dependencies besides pywin32.
    - You are **NOT ALLOWED** to `pip install` any additional dependencies. 
"""
    final_code, result = agent.generate_and_refine(user_query)
    
    if final_code:
        print("=== Final Generated Code ===\n\n")
        print(final_code+"\n\n")
    else:
        print("=== No valid solution found ===\n\n")
        print(result+"\n\n")
