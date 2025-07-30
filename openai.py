from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")  # Or set directly like: openai.api_key = "sk-..."

@app.route("/prompts", methods=["POST"])
def create_prompt():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    try:
        # Send to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or "gpt-4" if you have access
            messages=[
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=300
        )

        answer = response['choices'][0]['message']['content'].strip()

        # (Optional) Save to DB if using SQLAlchemy
        # prompt = Prompt(question=question, answer=answer)
        # db.session.add(prompt)
        # db.session.commit()

        return jsonify({
            "question": question,
            "answer": answer
        }), 201

    except Exception as e:
        return jsonify({"error": "OpenAI API call failed", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
