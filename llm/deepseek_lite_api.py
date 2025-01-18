# deepseek_lite_api.py
from flask import Flask, request, Response, stream_with_context, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import torch
import threading

# Initialize tokenizer + model as before
tokenizer = AutoTokenizer.from_pretrained(
    "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
    trust_remote_code=True
)
model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16
).cuda()

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate():
    """
    Returns a chunked stream of tokens from the model.
    Each chunk is a bit of text that the model generates.
    The agent/client can read these chunks in real time.
    """
    try:
        data = request.get_json()
        if "messages" not in data or not isinstance(data["messages"], list):
            return jsonify({"error": "Invalid input format. 'messages' must be a list."}), 400
        
        messages = data["messages"]

        # Prepare the model inputs
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(model.device)

        # Create the streamer
        streamer = TextIteratorStreamer(
            tokenizer=tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        # Our generation kwargs
        generation_kwargs = dict(
            inputs=inputs,
            max_new_tokens=8192,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            num_return_sequences=1,
            eos_token_id=tokenizer.eos_token_id,
            streamer=streamer
        )

        # We'll generate in a separate thread
        generation_thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        generation_thread.start()

        def token_stream():
            # As tokens appear in the streamer, yield them to the client
            for new_token in streamer:
                # You can encode each token as needed; here we just yield raw text
                yield new_token
            # Make sure generation is done
            generation_thread.join()

        # Return a streaming response so the client sees tokens in real time
        return Response(stream_with_context(token_stream()), mimetype="text/plain")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
