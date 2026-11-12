"""
Shared backend for the clportfolio.me projects (deployed on Railway).

Each project lives in projects/<name>/ with:
  logic.py   – the actual work
  routes.py  – its API endpoints (a Flask Blueprint)

To add a project: create projects/<new_name>/ and register its blueprint below.
"""
from dotenv import load_dotenv  # must load before importing modules that read env
load_dotenv()

from flask import Flask
from flask_cors import CORS

from projects.emotion_detection.routes import bp as emotion_detection_bp
from projects.stock_analyzer.routes import bp as stock_analyzer_bp
from projects.custom_llm_chatbot.routes import bp as custom_llm_chatbot_bp
from projects.stochastic_vs_deterministic.routes import bp as stochastic_vs_deterministic_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

app.register_blueprint(emotion_detection_bp)           # POST /analyze
app.register_blueprint(stock_analyzer_bp)              # POST /stock-analyzer
app.register_blueprint(custom_llm_chatbot_bp)          # POST /rag-upload, /rag-chat
app.register_blueprint(stochastic_vs_deterministic_bp) # POST /api/temperature


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(debug=True)
