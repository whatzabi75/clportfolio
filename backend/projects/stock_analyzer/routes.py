from flask import Blueprint, request, jsonify
from .logic import stock_analyzer

bp = Blueprint("stock_analyzer", __name__)


@bp.route("/stock-analyzer", methods=["POST"])
def analyze_stock():
    data = request.get_json()
    symbol = data.get("symbol", "").upper()
    range_ = data.get("range", "6mo")

    if not symbol:
        return jsonify({"error": "No stock symbol provided"}), 400

    return jsonify(stock_analyzer(symbol, range_))
