from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from models.analytics import AnalyticsRepository
from models.feedback import FeedbackRepository
from routes.helpers import jwt_required


analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/feedback", methods=["POST", "OPTIONS"])
@jwt_required
def submit_feedback():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    comments = (payload.get("comments") or "").strip()
    rating = int(payload.get("rating") or 0)
    if rating < 1 or rating > 5:
        return jsonify({"message": "Rating must be between 1 and 5."}), 400

    feedback = FeedbackRepository(current_app.extensions["database"])
    feedback_id = feedback.create(g.current_user["user_id"], comments, rating)
    return jsonify({"message": "Feedback submitted.", "feedback_id": feedback_id}), 201


@analytics_bp.route("/analytics/<int:user_id>", methods=["GET"])
@jwt_required
def get_analytics(user_id: int):
    if g.current_user["role"] != "admin" and int(g.current_user["user_id"]) != user_id:
        return jsonify({"message": "You are not allowed to view this analytics dashboard."}), 403

    analytics = AnalyticsRepository(current_app.extensions["database"])
    return jsonify(analytics.get_user_dashboard(user_id))
