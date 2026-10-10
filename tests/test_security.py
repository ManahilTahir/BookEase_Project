"""Tests for security, hashing, and RBAC."""

from src.core.security import hash_password, verify_password, SessionManager
from src.config import ROLE_ADMIN, ROLE_OWNER, ROLE_STAFF


def test_password_hashing():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False


def test_rbac_permissions(sample_data):
    admin = sample_data["admin"]
    staff_user = sample_data["staff_user"]

    # Test Admin Privileges
    SessionManager.set_current_user(admin)
    assert SessionManager.is_authenticated() is True
    assert SessionManager.is_admin() is True
    assert SessionManager.has_permission("manage_settings") is True
    assert SessionManager.has_permission("manage_users") is True
    assert SessionManager.has_permission("manage_backups") is True

    # Test Staff Privileges
    SessionManager.set_current_user(staff_user)
    assert SessionManager.is_admin() is False
    assert SessionManager.has_permission("manage_appointments") is True
    assert SessionManager.has_permission("manage_settings") is False
    assert SessionManager.has_permission("manage_users") is False
    assert SessionManager.has_permission("manage_backups") is False

    # Logout
    SessionManager.clear_session()
    assert SessionManager.is_authenticated() is False
    assert SessionManager.has_permission("view_dashboard") is False
