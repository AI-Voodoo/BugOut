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
1. Write code to access the OANDA public trading platform api using oandapyV20 library.
2. Pull down historical data for intra-day trading for instrument="WTICO_USD".
3. Devise an ML model to analyze this historical data to make trade recommendations.
4. ALL output should be saved to path "output/".
5. Save the training data to path "output/".
6. Save the model to path "output/".
7. Test the model's accuracy and save to path "output/".
8. Create unit tests to ensure proper outputs.

Account credentials:
api_token = ""
account_id = ""
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
