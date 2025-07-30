import os
import requests
from flask import Blueprint, request, jsonify
from models import db, Prompt
from dotenv import load_dotenv

load_dotenv()

routes = Blueprint("routes", __name__)

@routes.route("/")
def index():
    return "Aditya's AI Prompt Tool Running"

@routes.route("/prompts", methods=["POST"])
def create_prompt():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    model_id = "phi"
    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_id,
        "prompt": question,
        "stream": False
    }

    try:
        response = requests.post(ollama_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        answer = result.get("response", "No response generated.")

        prompt = Prompt(question=question, answer=answer)
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
    prompts = Prompt.query.order_by(Prompt.id.desc()).all()

    result = []
    for prompt in prompts:
        result.append({
            "id": prompt.id,
            "question": prompt.question,
            "answer": prompt.answer
        })

    return jsonify(result), 200


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