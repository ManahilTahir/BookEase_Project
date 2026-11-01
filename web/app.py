"""BookEase Web Application Factory."""

import sys
import logging
from pathlib import Path

# Ensure project root is in path so src.* imports work
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask, render_template, jsonify
from web.config import WebConfig
from web.routes.public import public_bp
from web.routes.internal import internal_bp

logger = logging.getLogger("bookease.web")


def _init_server_sessions(app: Flask) -> None:
    """Initialize server-side sessions via Flask-Session if available.

    Flask-Session is a declared dependency (web_requirements.txt) and is
    installed in this environment. We initialize defensively so the app
    still boots (falling back to Flask's signed-cookie sessions) if the
    package or its backend is unavailable. This hardens internal staff
    sessions for public deployment without altering the login flow.
    """
    try:
        from flask_session import Session
        app.config.setdefault("SESSION_TYPE", "filesystem")
        Session(app)
        logger.info("Flask-Session (server-side) initialized.")
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning("Flask-Session unavailable, using signed-cookie sessions: %s", exc)


def create_app(config: type = WebConfig) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )
    app.config.from_object(config)

    # Server-side sessions for internal staff/admin auth (hardening for public launch)
    _init_server_sessions(app)

    # Register blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(internal_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        from src.database.connection import get_db
        from src.database.models import BusinessSetting
        try:
            with get_db() as session:
                settings = {r.key: r.value for r in session.query(BusinessSetting).all()}
        except Exception:
            settings = {}
        return render_template("not_found.html", settings=settings, page_title="Page Not Found", message="The page you are looking for does not exist."), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {e}")
        return jsonify({"error": "Internal server error. Please try again."}), 500

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "Too many requests. Please slow down and try again."}), 429

    logger.info("BookEase web application created successfully.")
    return app
