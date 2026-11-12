from flask import Blueprint, request, jsonify
from .logic import process_pdf, answer_question

bp = Blueprint("custom_llm_chatbot", __name__)


@bp.route("/rag-upload", methods=["POST"])
def rag_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    print(f"[INFO] Upload received: {file.filename}")

    if not file.filename.endswith(".pdf"):
        print(f"[WARN] Rejected non-PDF file: {file.filename}")
        return jsonify({"error": "Only PDF files are allowed"}), 400

    try:
        success = process_pdf(file)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if success:
        return jsonify({"status": "ok", "message": "PDF processed and model trained"})
    return jsonify({"status": "failed", "message": "PDF could not be processed"}), 500


@bp.route("/rag-chat", methods=["POST"])
def rag_chat():
    data = request.get_json()
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    return jsonify({"status": "ok", "answer": answer_question(question)})
