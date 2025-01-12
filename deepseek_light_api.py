from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# Initialize the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(
    "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
    trust_remote_code=True
)
model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16
).cuda()

# Initialize Flask app
app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    """
    Generate a response based on user-provided messages.
    Request JSON format:
    {
        "messages": [
            { "role": "user", "content": "Your prompt here." }
        ]
    }
    Response JSON format:
    {
        "response": "Generated response here."
    }
    """
    try:
        # Parse the request
        data = request.get_json()
        if "messages" not in data or not isinstance(data["messages"], list):
            return jsonify({"error": "Invalid input format. 'messages' must be a list."}), 400
        
        messages = data["messages"]
        
        # Prepare the inputs
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)
        
        # Generate response
        outputs = model.generate(
            inputs,
            max_new_tokens=2048,
            do_sample=False,
            top_k=50,
            top_p=0.95,
            num_return_sequences=1,
            eos_token_id=tokenizer.eos_token_id
        )
        
        # Decode and return the generated text
        generated_text = tokenizer.decode(
            outputs[0][len(inputs[0]):],
            skip_special_tokens=True
        )
        return jsonify({"response": generated_text})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

### curl to test
# curl -X POST http://127.0.0.1:5000/generate -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"write a quick sort algorithm in python.\"}]}"
