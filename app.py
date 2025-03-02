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
    delete_file("output/test.txt")

    agent = BugOutAgent("http://127.0.0.1:5000/generate", log_file)

    user_query = """
Write a Python script designed for Windows environments that comprehensively identifies DLL hijacking vulnerabilities. Your script must perform the following tasks:

1. **Module Enumeration:**
   - Enumerate loaded modules (DLLs) from running processes and identify their exact file paths.
   - Allow users to specify specific processes (by name or PID) to analyze as an option but test the program system-wide.

2. **Directory Checks:**
   - Identify DLLs loaded from non-standard directories (directories other than standard Windows directories like `C:\Windows\System32`, `C:\Program Files`, etc.).

3. **Missing or Non-existent DLLs:**
   - Detect any modules that reference non-existent DLL files.
   - Clearly list modules and processes referencing these DLLs.

4. **Privilege-Aware Security Descriptor Checks:**
   - Inspect the file permissions (DACL) of each loaded DLL.
   - Explicitly identify DLL files that grant write, modify, or delete permissions to non-privileged groups or users (e.g., "Everyone", "Users", "Authenticated Users").
   - Clearly differentiate between permissions granted to privileged accounts/groups (SYSTEM, Administrators, TrustedInstaller) and those granted to non-privileged groups.

5. **Digital Signature Validation:**
   - Accurately verify the digital signatures of loaded DLL files using proper Windows API calls (e.g., `WinVerifyTrust`).
   - Flag DLLs that are unsigned or have invalid signatures.

6. **Environment Variable Analysis:**
   - Analyze environment variables (e.g., PATH, AppInit_DLLs) to identify paths susceptible to manipulation that may lead to DLL hijacking.

7. **False Positive Mitigation:**
   - Include logic or configuration (such as allowlists or filtering known safe DLLs) to reduce false positives.

8. **Reporting:**
   - Generate a clear, structured report (e.g., printed to console, CSV, or JSON format) detailing potential vulnerabilities, specifying:
     - DLL path
     - Associated process
     - Reason flagged (non-standard directory, insecure permissions, missing file, invalid signature, etc.)

Ensure your code is well-commented, clearly structured, and robust enough to handle exceptions gracefully. Include comments indicating what each key function or block of code is intended to achieve.

**Always call the main() function in addition to unittest.**
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
