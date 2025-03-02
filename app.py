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

    # this prompt was created by a multi-agent swarm
    user_query = """
- write python code to find which binaries on the windows system may be suseptible to dll hijacking.
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
