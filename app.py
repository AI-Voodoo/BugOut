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
    Write a Python script that identifies Windows binaries that may be susceptible to DLL hijacking. Your solution should use techniques like:
    - Ensure to do a system-wide audit - not just the current process.
    - Identify modules that are loaded from non-standard directories.
    - Look for modules calling non-existent DLLs.
    - Robustly validate the digital signatures and file permissions if they are potentially tamperable.
    - Privilege-aware checks for file security descriptors
    - Add any further checks you deem relivent.
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
