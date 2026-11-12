from flask import Blueprint, request, jsonify
from .logic import emotion_detector

bp = Blueprint("emotion_detection", __name__)


@bp.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    return jsonify(emotion_detector(text))
