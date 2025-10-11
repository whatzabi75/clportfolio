import os
from dotenv import load_dotenv  # must load before importing modules that read env
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from emotion_detection import emotion_detector  # adjust import to your function
from stock_analyzer import stock_analyzer  # import the stock analyzer function

from rag_upload import process_pdf, answer_question  # import the RAG deployment function

from sentence_transformers import SentenceTransformer, util

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

model = SentenceTransformer('all-MiniLM-L6-v2')

GROUND_TRUTHS = {
    "return policy": "We accept returns within 30 days of delivery when the item is unused and in its original packaging. Start the process from your account portal or contact support for help.",
    "order status": "Orders typically ship within two business days. Use the tracking link in your confirmation email or visit the order history page to see the latest updates.",
    "subscription cancellation": "You can cancel your subscription at any time from the billing settings page. Your plan stays active until the end of the current billing cycle with no additional charges.",
    "technical support": "If you encounter a technical issue, restart the app and check for updates. If the problem persists, reach out to support with your device details and error message for faster assistance.",
}

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

#------------------------------------
# Emotion Detection Route
#------------------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400

    emotion = emotion_detector(text)  # your existing Python function
    return jsonify(emotion)

#------------------------------------
# Stock Analyzer Route
#------------------------------------
@app.route("/stock-analyzer", methods=["POST"])
def analyze_stock():
    data = request.get_json()
    symbol = data.get("symbol", "").upper()
    range_ = data.get("range", "6mo")
    
    if not symbol:
        return jsonify({"error": "No stock symbol provided"}), 400

    analysis = stock_analyzer(symbol, range_)  # call the stock analyzer function
    return jsonify(analysis)

#------------------------------------
# RAG upload Route
#------------------------------------
@app.route("/rag-upload", methods=["POST"])
def rag_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files["file"]
    print(f"[INFO] Upload received: {file.filename}")

    if not file.filename.endswith(".pdf"):
        print(f"[WARN] Rejected non-PDF file: {file.filename}")
        return jsonify({"error": "Only PDF files are allowed"}), 400
    
    # process_pdf should parse PDF, chunk, embed, and store in FAISS
    try:
       success = process_pdf(file)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    if success:
        return jsonify({"status": "ok", "message": "PDF processed and model trained"})
    else:
        return jsonify({"status": "failed", "message": "PDF could not be processed"}), 500

#------------------------------------
# RAG Chat with uploaded file Route
#------------------------------------
@app.route("/rag-chat", methods=["POST"])
def rag_chat():
    data = request.get_json()
    question = data.get("question", "")
    
    if not question:
        return jsonify({"error": "No question provided"}), 400

    answer = answer_question(question)  # retrieves from FAISS + calls LLM
    return jsonify({"status": "ok", "answer": answer})


@app.route("/api/temperature", methods=["POST"])
def temperature_demo():
    data = request.get_json()
    question = data.get("question", "").strip()
    temperature = float(data.get("temperature", 0.7))

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Identify closest topic (if any)
    question_emb = model.encode(question, convert_to_tensor=True)
    best_match = None
    best_score = 0.0
    for topic, truth in GROUND_TRUTHS.items():
        topic_emb = model.encode(topic, convert_to_tensor=True)
        score = float(util.cos_sim(question_emb, topic_emb))
        if score > best_score:
            best_score, best_match = score, topic

    expected_answer = GROUND_TRUTHS[best_match] if best_score > 0.55 else None

    # Generate LLM response
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful and factual customer support assistant."},
            {"role": "user", "content": question}
        ],
        temperature=temperature,
        max_tokens=200,
    )

    response_text = completion.choices[0].message.content.strip()

    # Similarity (if we have ground truth)
    similarity = None
    if expected_answer:
        emb1 = model.encode(expected_answer, convert_to_tensor=True)
        emb2 = model.encode(response_text, convert_to_tensor=True)
        similarity = round(float(util.cos_sim(emb1, emb2)[0][0]) * 100, 1)

    return jsonify({
        "temperature": temperature,
        "response": response_text,
        "expected_answer": expected_answer,
        "similarity": similarity,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
