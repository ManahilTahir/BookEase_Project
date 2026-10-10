"""Security, Authentication, and RBAC utilities for BookEase."""

from typing import Optional
import bcrypt
from src.config import ROLE_PERMISSIONS, ROLE_ADMIN, ROLE_OWNER, ROLE_STAFF


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


class SessionManager:
    """Singleton session tracker for the active desktop user."""

    _instance = None
    _current_user = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._current_user = None
        return cls._instance

    @classmethod
    def set_current_user(cls, user):
        """Set active authenticated user."""
        cls._current_user = user

    @classmethod
    def get_current_user(cls):
        """Get active user."""
        return cls._current_user

    @classmethod
    def clear_session(cls):
        """Log out current user."""
        cls._current_user = None

    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if any user is logged in."""
        return cls._current_user is not None

    @classmethod
    def has_permission(cls, permission_key: str) -> bool:
        """Check if logged in user has the requested privilege."""
        if not cls._current_user:
            return False
        role = getattr(cls._current_user, "role", ROLE_STAFF)
        role_privileges = ROLE_PERMISSIONS.get(role, {})
        return role_privileges.get(permission_key, False)

    @classmethod
    def is_admin(cls) -> bool:
        if not cls._current_user:
            return False
        return cls._current_user.role == ROLE_ADMIN

    @classmethod
    def is_owner_or_admin(cls) -> bool:
        if not cls._current_user:
            return False
        return cls._current_user.role in (ROLE_ADMIN, ROLE_OWNER)
