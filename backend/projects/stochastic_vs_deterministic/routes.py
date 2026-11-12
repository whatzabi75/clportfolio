from flask import Blueprint, request, jsonify

from .logic import GROUND_TRUTHS, model, util, client, ANTHROPIC_MODEL

bp = Blueprint("stochastic_vs_deterministic", __name__)


@bp.route("/api/temperature", methods=["POST"])
def temperature_demo():
    data = request.get_json()
    question = data.get("question", "").strip()
    temperature = float(data.get("temperature", 0.7))

    if not question:
        return jsonify({"error": "Question is required"}), 400

    # Step 1: Identify closest known ground truth topic
    question_emb = model.encode(question, convert_to_tensor=True)
    best_match = None
    best_score = 0.0

    for topic, truth in GROUND_TRUTHS.items():
        topic_emb = model.encode(topic, convert_to_tensor=True)
        score = float(util.cos_sim(question_emb, topic_emb))
        if score > best_score:
            best_score, best_match = score, topic

    expected_answer = GROUND_TRUTHS[best_match] if best_score > 0.50 else None

    # Step 2: Generate LLM response
    completion = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=200,
        system="You are a helpful, factual support assistant.",
        messages=[{"role": "user", "content": question}],
        temperature=temperature,
    )

    response_text = completion.content[0].text.strip()

    # Step 3: Similarity comparison
    similarity = None
    if expected_answer:
        emb1 = model.encode(expected_answer, convert_to_tensor=True)
        emb2 = model.encode(response_text, convert_to_tensor=True)
        similarity = round(float(util.cos_sim(emb1, emb2)[0][0]) * 100, 1)

    return jsonify({
        "temperature": temperature,
        "response": response_text,
        "expected_answer": expected_answer,
        "similarity": similarity
    })
