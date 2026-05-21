from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from models.feedback import FeedbackRepository
from models.user import UserRepository
from routes.helpers import create_jwt, hash_password, jwt_required, verify_password


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    role = payload.get("role") or "user"

    if not username or not email or not password:
        return jsonify({"message": "Username, email, and password are required."}), 400

    users = UserRepository(current_app.extensions["database"])
    if users.get_by_username(username):
        return jsonify({"message": "Username is already in use."}), 409
    if users.get_by_email(email):
        return jsonify({"message": "Email is already registered."}), 409

    user_id = users.create(username=username, email=email, password=hash_password(password), role=role)
    user = users.get_by_id(user_id)
    token = create_jwt(
        {"user_id": user_id, "username": username, "role": role},
        current_app.config["JWT_SECRET"],
        current_app.config["JWT_EXPIRY_SECONDS"],
    )
    return jsonify({"message": "Registration successful.", "token": token, "user": users.serialize_public(user)}), 201


@auth_bp.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True) or {}
    identifier = (payload.get("identifier") or payload.get("email") or payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not identifier or not password:
        return jsonify({"message": "Email/username and password are required."}), 400

    users = UserRepository(current_app.extensions["database"])
    user = users.get_by_email(identifier.lower()) or users.get_by_username(identifier)
    if not user or not verify_password(password, user["password"]):
        return jsonify({"message": "Invalid credentials."}), 401

    token = create_jwt(
        {"user_id": user["user_id"], "username": user["username"], "role": user["role"]},
        current_app.config["JWT_SECRET"],
        current_app.config["JWT_EXPIRY_SECONDS"],
    )
    return jsonify({"message": "Login successful.", "token": token, "user": users.serialize_public(user)})


@auth_bp.route("/profile", methods=["GET"])
@jwt_required
def profile():
    feedback = FeedbackRepository(current_app.extensions["database"])
    return jsonify(
        {
            "user": UserRepository.serialize_public(g.current_user),
            "feedback": feedback.list_by_user(g.current_user["user_id"]),
        }
    )
