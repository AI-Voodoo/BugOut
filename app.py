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

    user_query = "Write a quicksort algorithm in Python."
    final_code, result = agent.generate_and_refine(user_query)
    
    if final_code:
        print("=== Final Generated Code ===")
        print(final_code)
    else:
        print("=== No valid solution found ===")
        print(result)
