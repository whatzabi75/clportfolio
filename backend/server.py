import os
from dotenv import load_dotenv  # must load before importing modules that read env
load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
from emotion_detection import emotion_detector  # adjust import to your function
from stock_analyzer import stock_analyzer  # import the stock analyzer function

from rag_upload import process_pdf, answer_question  # import the RAG deployment function

from sentence_transformers import SentenceTransformer, util

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

model = SentenceTransformer('all-MiniLM-L6-v2')

GROUND_TRUTHS = {
    "What is Meeting Digest?": (
        "Meeting Digests is a feature within Salesforce Meetings that enhances sales reps' "
        "interactions with prospects and customers by providing a unified view of meeting information. "
        "It helps sales reps prepare for meetings by gathering and sharing insights about attendees, "
        "meeting details, and related activities on a single page."
    ),

    "How can I use Meeting Digest?": (
        "To start using Meeting Digest, here are some steps:\n"
        "1. Enable Salesforce Meetings: Ensure that Meeting Digest is enabled.\n"
        "2. Assign Permissions: Reassign users to the permission set.\n"
        "3. Utilize Einstein Activity Capture: Implement an activity sync.\n"
        "4. Prepare for Meetings: Use the Meeting Digest to gather and share information before meetings.\n"
        "5. Take Action on Attendee Details: Update attendee details, start emails, or add new records."
    ),

    "How can Meeting Digest drive value?": (
        "Here are some ways it can add value:\n\n"
        "1. Unified Information: Meeting Digest unifies all relevant information about meeting attendees.\n"
        "2. Enhanced Engagement: The Meeting Studio feature within Meeting Digest allows reps to keep attendees engaged during virtual meetings.\n"
        "3. Actionable Insights: Meeting Digest provides insights into high-priority cases and outstanding customer requests.\n"
        "4. Streamlined Follow-Up: After the meeting, Meeting Digest offers reminders and quick actions for follow-up tasks.\n"
        "5. Improved Collaboration: With the ability to update attendee details directly from the Meeting Digest, sales reps can stay focused on meeting preparation and execution."
    )
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


#------------------------------------
# Temperature Demo Route
#------------------------------------
@app.route("/api/temperature", methods=["POST"])
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
        model="claude-haiku-4-5-20251001",
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

if __name__ == "__main__":
    app.run(debug=True)