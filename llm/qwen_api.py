# qwen_api.py
from flask import Flask, request, Response, stream_with_context, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import torch
import threading

# Define the Qwen model name
model_name = "Qwen/Qwen2.5-Coder-32B-Instruct"

# Load tokenizer and model using device_map="auto" and torch_dtype="auto"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    """
    Returns a chunked stream of tokens from the Qwen model.
    Each chunk is a bit of text that the model generates in real time.
    """
    try:
        data = request.get_json()
        if "messages" not in data or not isinstance(data["messages"], list):
            return jsonify({"error": "Invalid input format. 'messages' must be a list."}), 400
        
        messages = data["messages"]

        # Create the prompt text using Qwen's chat template
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        # Tokenize the prompt text and move tensors to the model device
        model_inputs = tokenizer([prompt_text], return_tensors="pt").to(model.device)

        # Create the streamer for real-time token generation
        streamer = TextIteratorStreamer(
            tokenizer=tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        # Set up generation parameters (adjusted for Qwen)
        generation_kwargs = dict(
            **model_inputs,
            max_new_tokens=8192,
            #do_sample=True,
            #top_k=50,
            #top_p=0.95,
            num_return_sequences=1,
            eos_token_id=tokenizer.eos_token_id,
            streamer=streamer
        )

        # Generate tokens in a separate thread for streaming response
        generation_thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        generation_thread.start()

        def token_stream():
            # Yield tokens as they are generated
            for new_token in streamer:
                yield new_token
            generation_thread.join()

        return Response(stream_with_context(token_stream()), mimetype="text/plain")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
