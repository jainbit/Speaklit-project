from __future__ import annotations

from flask import Flask, jsonify, request

from config import build_config
from models.database import Database
from routes.analytics import analytics_bp
from routes.auth import auth_bp
from routes.video import video_bp


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(build_config(overrides))

    database = Database(app.config)
    app.extensions["database"] = database
    app.extensions["active_jobs"] = set()

    if app.config["AUTO_INIT_DB"]:
        database.init_schema()

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(video_bp, url_prefix="/api/videos")
    app.register_blueprint(analytics_bp, url_prefix="/api")

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        response.headers["Access-Control-Allow-Origin"] = origin or app.config["CORS_ORIGIN"]
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(
            {
                "status": "ok",
                "app": "SpeakIt",
                "database_driver": app.config["DB_DRIVER"],
                "demo_pipeline": app.config["DEMO_PIPELINE"],
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=app.config["DEBUG"], use_reloader=False)
