# BugOut: Your AI-Powered Pythonic Coding Agent 🐞💻
![BugOut Logo](images/bugout.png)

**BugOut** is a fairly early **proof-of-concept (PoC)** Python coding agent that demonstrates how you can build a local code-generation and execution agent from scratch. It leverages a locally running “DeepSeek Lite” API (`llm/deepseek_lite_api.py`) to generate code. The code is then automatically run and refined until it executes without errors, or until a set iteration limit is reached.

## 

## Key Features

1. **Local LLM API Integration**  
   - BugOut calls your locally running LLM endpoint (DeepSeek Lite) to generate Python code based on instructions and user prompts.  
   - Uses streaming responses to capture code as it’s generated.

2. **Conversation Management**  
   - Maintains a conversation list (`self.conversation`) with:
     - A “system” prompt that provides instructions to the LLM.
     - A sequence of user prompts or feedback.
     - The LLM’s replies, including any generated code.

3. **Iterative Refinement**  
   - If code execution returns an error, BugOut re-injects the error output into the conversation, prompting the LLM to provide a refined solution.  
   - Planning and Reflection
   - This loop continues until:
     - The code executes successfully, or  
     - The maximum iteration count (`max_iterations`) is reached.
   - Writes the code to a **temporary `.py` file**—rather than using `exec()`—and then runs it in a subprocess for safety and isolation.

# BugOut: Operating in a Multi-Agent Swarm 
![BugOut Multi-Agent Swarm Video](https://www.youtube.com/watch?v=KIvso5oaS8c&t=18s)

