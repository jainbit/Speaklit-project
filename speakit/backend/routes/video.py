from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Blueprint, current_app, g, jsonify, request, send_file
from werkzeug.utils import secure_filename

from models.analytics import AnalyticsRepository
from models.history import LocalizationHistoryRepository
from models.video import VideoRepository
from pipeline.common import SUPPORTED_LANGUAGES
from pipeline.runner import run_pipeline_async
from routes.helpers import jwt_required


video_bp = Blueprint("video", __name__)


def _is_allowed_file(filename: str) -> bool:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return extension in current_app.config["ALLOWED_VIDEO_EXTENSIONS"]


def _parse_target_languages(raw_value) -> list[str]:
    if not raw_value:
        return []

    values: list[str] = []
    candidates = raw_value if isinstance(raw_value, list) else [raw_value]
    for candidate in candidates:
        normalized = str(candidate).strip()
        if not normalized:
            continue
        if normalized.startswith("["):
            try:
                decoded = json.loads(normalized)
                values.extend(str(item).strip() for item in decoded)
            except json.JSONDecodeError:
                continue
        else:
            values.extend(item.strip() for item in normalized.split(","))

    return [item for item in values if item in SUPPORTED_LANGUAGES and item != "en"]


@video_bp.route("", methods=["GET"])
@jwt_required
def list_videos():
    videos = VideoRepository(current_app.extensions["database"])
    return jsonify({"videos": [videos.serialize(item) for item in videos.list_by_user(g.current_user["user_id"])]})


@video_bp.route("/upload", methods=["POST", "OPTIONS"])
@jwt_required
def upload_video():
    if request.method == "OPTIONS":
        return ("", 204)

    if "video" not in request.files:
        return jsonify({"message": "A video file is required."}), 400

    file = request.files["video"]
    if not file or not file.filename:
        return jsonify({"message": "Please choose a video file."}), 400
    if not _is_allowed_file(file.filename):
        return jsonify({"message": "Supported file types are MP4, MOV, MKV, WEBM, AVI, and M4V."}), 400

    source_language = (request.form.get("source_language") or "en").strip().lower()
    target_languages = _parse_target_languages(request.form.getlist("target_languages") or request.form.get("target_languages"))
    if source_language != "en":
        return jsonify({"message": "The current MVP expects English source videos."}), 400
    if not target_languages:
        return jsonify({"message": "Select at least one target language."}), 400

    filename = secure_filename(file.filename)
    stem = Path(filename).stem
    destination = Path(current_app.config["UPLOAD_FOLDER"]) / f"{stem}_{g.current_user['user_id']}{Path(filename).suffix}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    file.save(destination)

    title = (request.form.get("video_title") or stem).strip()
    storage_size_mb = round(os.path.getsize(destination) / (1024 * 1024), 3)

    videos = VideoRepository(current_app.extensions["database"])
    video_id = videos.create(
        user_id=g.current_user["user_id"],
        video_title=title,
        file_path=str(destination),
        source_language=source_language,
        target_languages=target_languages,
        original_filename=filename,
        storage_size=storage_size_mb,
    )
    return jsonify({"message": "Video uploaded successfully.", "video": videos.serialize(videos.get_by_id(video_id))}), 201


@video_bp.route("/<int:video_id>", methods=["GET"])
@jwt_required
def get_video(video_id: int):
    database = current_app.extensions["database"]
    videos = VideoRepository(database)
    histories = LocalizationHistoryRepository(database)
    analytics = AnalyticsRepository(database)

    video = videos.get_by_id(video_id)
    if not video or int(video["user_id"]) != int(g.current_user["user_id"]):
        return jsonify({"message": "Video not found."}), 404

    token = g.current_token
    payload = videos.serialize(video)
    payload["source_preview_url"] = f"/api/videos/{video_id}/source?token={token}"
    payload["localized_outputs"] = [
        {
            **item,
            "is_demo_output": item.get("is_demo_output", current_app.config["DEMO_PIPELINE"]),
            "merge_engine": item.get("merge_engine", "demo-copy" if current_app.config["DEMO_PIPELINE"] else "unknown"),
            "synthesis_engine": item.get("synthesis_engine", "demo-fallback" if current_app.config["DEMO_PIPELINE"] else "unknown"),
            "preview_url": f"/api/videos/{video_id}/output?language={item['target_language']}&token={token}",
            "audio_preview_url": f"/api/videos/{video_id}/audio?language={item['target_language']}&token={token}",
        }
        for item in (payload.get("output_manifest") or [])
    ]
    return jsonify({"video": payload, "histories": histories.list_by_video(video_id), "analytics": analytics.get_video_analytics(video_id)})


@video_bp.route("/<int:video_id>/status", methods=["GET"])
@jwt_required
def get_video_status(video_id: int):
    videos = VideoRepository(current_app.extensions["database"])
    video = videos.get_by_id(video_id)
    if not video or int(video["user_id"]) != int(g.current_user["user_id"]):
        return jsonify({"message": "Video not found."}), 404
    return jsonify({"video": videos.serialize(video)})


@video_bp.route("/<int:video_id>/process", methods=["POST", "OPTIONS"])
@jwt_required
def process_video(video_id: int):
    if request.method == "OPTIONS":
        return ("", 204)

    videos = VideoRepository(current_app.extensions["database"])
    video = videos.get_by_id(video_id)
    if not video or int(video["user_id"]) != int(g.current_user["user_id"]):
        return jsonify({"message": "Video not found."}), 404
    if video["status"] == "processing":
        return jsonify({"message": "This video is already being processed."}), 409

    run_pipeline_async(current_app._get_current_object(), video_id)
    return jsonify({"message": "Localization pipeline started.", "video_id": video_id}), 202


@video_bp.route("/<int:video_id>/output", methods=["GET"])
@jwt_required
def download_output(video_id: int):
    videos = VideoRepository(current_app.extensions["database"])
    histories = LocalizationHistoryRepository(current_app.extensions["database"])
    video = videos.get_by_id(video_id)
    if not video or int(video["user_id"]) != int(g.current_user["user_id"]):
        return jsonify({"message": "Video not found."}), 404

    item = histories.find_output(video_id, request.args.get("language"))
    if not item or not item.get("output_path"):
        return jsonify({"message": "Localized output is not available yet."}), 404
    return send_file(item["output_path"], as_attachment=True, download_name=Path(item["output_path"]).name)


@video_bp.route("/<int:video_id>/source", methods=["GET"])
@jwt_required
def source_video(video_id: int):
    videos = VideoRepository(current_app.extensions["database"])
    video = videos.get_by_id(video_id)
    if not video or int(video["user_id"]) != int(g.current_user["user_id"]):
        return jsonify({"message": "Video not found."}), 404
    return send_file(video["file_path"], as_attachment=False, download_name=Path(video["file_path"]).name)


@video_bp.route("/<int:video_id>/audio", methods=["GET"])
@jwt_required
def dubbed_audio(video_id: int):
    videos = VideoRepository(current_app.extensions["database"])
    video = videos.get_by_id(video_id)
    if not video or int(video["user_id"]) != int(g.current_user["user_id"]):
        return jsonify({"message": "Video not found."}), 404

    requested_language = request.args.get("language")
    manifest = videos._load_json(video.get("output_manifest"), default=[])  # noqa: SLF001
    item = next(
        (
            output
            for output in manifest
            if not requested_language or output.get("target_language") == requested_language
        ),
        None,
    )
    if not item or not item.get("audio_path"):
        return jsonify({"message": "Dubbed audio is not available yet."}), 404
    return send_file(item["audio_path"], as_attachment=False, download_name=Path(item["audio_path"]).name)
