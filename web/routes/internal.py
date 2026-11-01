"""Internal staff/admin routes for BookEase web portal."""

import logging
from functools import wraps
from flask import Blueprint, jsonify, request, render_template, session, redirect, url_for

from src.database.connection import get_db
from src.database.models import User, BusinessSetting
from src.core.security import verify_password, SessionManager
from src.config import ROLE_PERMISSIONS

logger = logging.getLogger("bookease.web.internal")
internal_bp = Blueprint("internal", __name__, url_prefix="/internal")


def _require_internal_login(f):
    """Decorator: redirect to login if not authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("internal_user_id"):
            return redirect(url_for("internal.login_page"))
        return f(*args, **kwargs)
    return decorated


def _require_permission(permission: str):
    """Decorator factory: require a specific RBAC permission."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("internal_user_id"):
                return redirect(url_for("internal.login_page"))
            role = session.get("internal_user_role", "staff")
            if not ROLE_PERMISSIONS.get(role, {}).get(permission, False):
                return jsonify({"error": "Forbidden — insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


@internal_bp.route("/login", methods=["GET"])
def login_page():
    """Internal staff login page."""
    if session.get("internal_user_id"):
        return redirect(url_for("internal.dashboard"))
    with get_db() as db:
        settings = {r.key: r.value for r in db.query(BusinessSetting).all()}
    return render_template("internal/login.html", settings=settings, page_title="Staff Login — BookEase")


@internal_bp.route("/login", methods=["POST"])
def login_post():
    """Authenticate a staff/admin user."""
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()[:50]
    password = str(data.get("password", ""))

    if not username or not password:
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    with get_db() as db:
        user = db.query(User).filter(User.username == username, User.is_active == True).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"success": False, "error": "Invalid username or password"}), 401

        session.permanent = True
        session["internal_user_id"] = user.id
        session["internal_user_name"] = user.full_name
        session["internal_user_role"] = user.role
        session["internal_username"] = user.username

    logger.info(f"Internal login: {username} ({user.role})")
    return jsonify({"success": True, "redirect": url_for("internal.dashboard"), "role": user.role})


@internal_bp.route("/logout", methods=["POST", "GET"])
def logout():
    """Clear staff session."""
    session.clear()
    return redirect(url_for("internal.login_page"))


@internal_bp.route("/dashboard")
@_require_internal_login
def dashboard():
    """Simple internal dashboard redirect — staff use the desktop app primarily."""
    with get_db() as db:
        settings = {r.key: r.value for r in db.query(BusinessSetting).all()}
    return render_template(
        "internal/dashboard.html",
        settings=settings,
        user_name=session.get("internal_user_name"),
        user_role=session.get("internal_user_role"),
        page_title="Internal Dashboard — BookEase",
    )
