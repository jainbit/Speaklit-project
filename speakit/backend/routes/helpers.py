from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable

from flask import current_app, g, jsonify, request

from models.user import UserRepository


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${derived.hex()}"


def verify_password(password: str, stored_value: str) -> bool:
    try:
        salt, hash_hex = stored_value.split("$", 1)
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return hmac.compare_digest(hash_hex, derived.hex())


def create_jwt(payload: dict[str, Any], secret: str, expires_in_seconds: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    body = dict(payload)
    body["exp"] = int((datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)).timestamp())
    header_part = _urlsafe_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    body_part = _urlsafe_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{body_part}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_part}.{body_part}.{_urlsafe_encode(signature)}"


def decode_jwt(token: str, secret: str) -> dict[str, Any]:
    try:
        header_part, body_part, signature_part = token.split(".")
    except ValueError as exc:
        raise ValueError("Invalid token format.") from exc

    signing_input = f"{header_part}.{body_part}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual = _urlsafe_decode(signature_part)
    if not hmac.compare_digest(expected, actual):
        raise ValueError("Invalid token signature.")

    payload = json.loads(_urlsafe_decode(body_part).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Token has expired.")
    return payload


def jwt_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if request.method == "OPTIONS":
            return ("", 204)

        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
        elif request.args.get("token"):
            token = request.args.get("token")

        if not token:
            return jsonify({"message": "Authorization token is required."}), 401

        try:
            payload = decode_jwt(token, current_app.config["JWT_SECRET"])
        except ValueError as exc:
            return jsonify({"message": str(exc)}), 401

        users = UserRepository(current_app.extensions["database"])
        user = users.get_by_id(int(payload["user_id"]))
        if not user:
            return jsonify({"message": "User not found."}), 401

        g.current_user = user
        g.current_token = token
        return view(*args, **kwargs)

    return wrapped


def _urlsafe_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("utf-8")


def _urlsafe_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode((payload + padding).encode("utf-8"))
