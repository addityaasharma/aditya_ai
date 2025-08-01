import os
import requests
from flask import Blueprint, request, jsonify
from models import db, Prompt
from dotenv import load_dotenv
from flask import render_template_string
from datetime import datetime

load_dotenv()

routes = Blueprint("routes", __name__)


app_start_time = datetime.now()

@routes.route("/")
def index():
    uptime = datetime.now() - app_start_time
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Aditya's AI Prompt Tool</title>
        <style>
            body {
                background-color: #f0f4f8;
                font-family: 'Segoe UI', Tahoma, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            h1 {
                color: #0055aa;
                margin-bottom: 10px;
            }
            .info {
                margin-top: 10px;
                font-size: 16px;
                color: #444;
            }
            .link {
                margin-top: 20px;
            }
            .link a {
                text-decoration: none;
                color: #0077cc;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚀 Aditya's AI Prompt Tool</h1>
            <div class="info">
                <p>Status: <strong style="color: green;">Running</strong></p>
                <p>Version: <strong>v1.0.0</strong></p>
                <p>Uptime: <strong>{{ uptime }}</strong></p>
            </div>
            <div class="link">
                <a href="www.linkedin.com/in/addityaasharma">Profile</a>
            </div>
        </div>
    </body>
    </html>
    """, uptime=str(uptime).split('.')[0])  # Removing microseconds for cleaner display

# lama prompt generator 
@routes.route("/prompts", methods=["POST"])
def create_prompt():
    data = request.get_json()
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Question is required"}), 400

    def build_prompt_template(question):
        q_lower = question.lower()

        if "buyer persona" in q_lower:
            return f"""
You are a persuasive marketing copywriter. When someone gives you a task like:
"Create a buyer persona for a mobile phone for Ayush"

You should respond with a vivid, emotionally compelling paragraph that includes:
- The persona’s name, age, location, and job
- Their habits, needs, dislikes, and decision-making behavior
- How to persuade them using targeted language and offers

Example Output:
"Meet Ayush, a dynamic 26-year-old digital marketer from Mumbai who lives on his smartphone! He demands blazing-fast performance for gaming, a stunning camera for social media, and a battery that lasts all day..."

Now respond to this:
"{question}"
"""

        elif "ad" in q_lower and "children" in q_lower:
            return f"""
You are an expert persuasive copywriter. When someone asks you to write an advertisement for a **mobile phone for children**, create a vivid, emotionally compelling product ad copy paragraph. It should:

- Highlight benefits to **children** (fun, games, design)
- Reassure **parents** (safety, parental controls, learning)
- Sound professional but playful
- Include **a product name**
- End with a motivational CTA or benefit-driven punchline

Example Output:
"Meet the WonderKid Mobile – where fun meets learning! Designed for curious young minds, it’s loaded with vibrant games, creative tools, and a safe digital playground parents can trust. With parental controls, eye-friendly display, and all-day battery, it’s more than just a phone—it’s your child’s first smart companion. Let your little explorer discover, play, and grow—one tap at a time!"

Now write an ad based on this:
"{question}"
"""
        else:
            return f"""Write a compelling, creative response to the following input:\n\n"{question}"\n"""

    system_prompt = build_prompt_template(user_question)

    model_id = "phi"
    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_id,
        "prompt": system_prompt,
        "stream": False
    }

    try:
        response = requests.post(ollama_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        answer = result.get("response", "No response generated.")

        prompt = Prompt(question=user_question, answer=answer)
        db.session.add(prompt)
        db.session.commit()

        return jsonify({
            "id": prompt.id,
            "question": prompt.question,
            "answer": prompt.answer
        }), 201

    except Exception as e:
        return jsonify({
            "error": "Ollama model call failed",
            "details": str(e)
        }), 500


@routes.route("/prompts", methods=["GET"])
def get_all_prompts():
    try:
        # Get page and per_page from query parameters with defaults
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Order by id DESC to show latest first
        pagination = Prompt.query.order_by(Prompt.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        prompts = pagination.items

        result = [{
            "id": prompt.id,
            "question": prompt.question,
            "answer": prompt.answer
        } for prompt in prompts]

        return jsonify(result), 200

    except Exception as e:
        print("Error fetching prompts:", str(e))
        return jsonify({"error": "Failed to fetch prompts"}), 500


@routes.route("/prompt", methods=["POST"])
def create():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    url = "https://api.deepinfra.com/v1/inference/mistralai/Mistral-7B-Instruct-v0.1"
    headers = {
        "Authorization": "Bearer fi30jBazxFh1uFrLHKvVrytWyfqx8NE9",
        "Content-Type": "application/json"
    }
    payload = {
        "input": question,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        answer = result.get("generated_text", "No answer returned.")

        return jsonify({
            "question": question,
            "answer": answer
        }), 200

    except Exception as e:
        return jsonify({
            "error": "DeepInfra model call failed",
            "details": str(e)
        }), 500


# open router prompt generator 
@routes.route("/openrouter", methods=["POST"])
def ask_question():
    question = request.json.get("question")
    if not question:
        return jsonify({"error": "Question is required"}), 400

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "Missing OpenRouter API key"}), 500

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        return jsonify({"question": question, "answer": answer})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "OpenRouter API call failed", "details": str(e)}), 500