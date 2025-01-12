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

    user_query = "Write a program in Python to open the file located at input/test.txt parse out the sentence which conatains the phrase \"nearly 9,000\" and save a new file with the sentence to output/ folder. Both folders are in the application root where this code is running. Lastly, define a test which should be executed at the end to ensure the task was coded properly."
    final_code, result = agent.generate_and_refine(user_query)
    
    if final_code:
        print("=== Final Generated Code ===\n\n")
        print(final_code+"\n\n")
    else:
        print("=== No valid solution found ===\n\n")
        print(result+"\n\n")
