"""UI Automated Tests verifying widgets and view transitions."""

import pytest
from src.database.connection import init_db
from src.core.security import SessionManager
from src.database.models import User
from src.database.connection import get_db
from src.ui.app import BookEaseApp


@pytest.fixture(scope="module", autouse=True)
def setup_app_db():
    init_db()


def test_app_lifecycle_and_view_navigation():
    # Login as admin in session
    with get_db() as s:
        admin_user = s.query(User).filter(User.username == "admin").first()
        SessionManager.set_current_user(admin_user)

    app = BookEaseApp()
    app.update()

    # Verify workspace is shown
    assert hasattr(app, "sidebar")
    assert hasattr(app, "content_canvas")

    # Navigate to all views to test rendering without exceptions
    views_to_test = [
        "dashboard",
        "calendar",
        "wizard",
        "appointments",
        "customers",
        "customer",
        "staff",
        "services",
        "reports",
        "settings",
    ]

    for view_key in views_to_test:
        app.navigate(view_key)
        app.update()
        assert app.active_nav_key == view_key
        # Verify content was injected
        assert len(app.content_canvas.winfo_children()) > 0

    # Test Theme Toggle
    app.theme_switch.deselect()
    app.toggle_theme()
    assert app.current_theme == "Light"

    app.theme_switch.select()
    app.toggle_theme()
    assert app.current_theme == "Dark"

    # Test Logout flow
    app.handle_logout()
    app.update()
    assert SessionManager.is_authenticated() is False

    app.destroy()
