"""Session-state helpers for the BookEase Streamlit app.

Manages internal-staff auth state and booking-wizard state using
``st.session_state`` so the multi-step wizard survives reruns.
"""

import streamlit as st

from streamlit_app.config import SESSION_LIFETIME_HOURS


def init_state() -> None:
    """Initialise default session-state keys (call once at app start)."""
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "booking_step" not in st.session_state:
        st.session_state.booking_step = 1
    if "booking_selection" not in st.session_state:
        st.session_state.booking_selection = {}


def is_authenticated() -> bool:
    return st.session_state.get("auth_user") is not None


def get_current_user() -> dict | None:
    return st.session_state.get("auth_user")


def set_authenticated_user(user: dict) -> None:
    st.session_state.auth_user = user


def logout() -> None:
    st.session_state.auth_user = None
    st.session_state.booking_step = 1
    st.session_state.booking_selection = {}


def has_permission(permission: str) -> bool:
    from src.config import ROLE_PERMISSIONS
    user = get_current_user()
    if not user:
        return False
    role = user.get("role", "staff")
    return ROLE_PERMISSIONS.get(role, {}).get(permission, False)


def get_booking_step() -> int:
    return st.session_state.get("booking_step", 1)


def set_booking_step(step: int) -> None:
    st.session_state.booking_step = step


def get_booking_selection() -> dict:
    return st.session_state.get("booking_selection", {})


def update_booking_selection(**kwargs) -> None:
    sel = st.session_state.get("booking_selection", {})
    sel.update(kwargs)
    st.session_state.booking_selection = sel


def reset_booking_wizard() -> None:
    st.session_state.booking_step = 1
    st.session_state.booking_selection = {}