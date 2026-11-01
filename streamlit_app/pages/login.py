"""Internal staff login page for the BookEase Streamlit app."""

import streamlit as st

from streamlit_app.config import BRAND_COLORS
from streamlit_app.db import authenticate_internal
from streamlit_app.components import render_hero
from streamlit_app.state import set_authenticated_user, is_authenticated

C = BRAND_COLORS


def render() -> None:
    if is_authenticated():
        st.query_params.update({"page": "dashboard"})
        st.rerun()
        return

    settings = st.session_state.get("be_settings", {})
    biz_name = settings.get("business_name", "BookEase")

    render_hero("Staff Portal", f"{biz_name} — Internal Access Only", "✦")

    with st.container():
        username = st.text_input("Username", key="login_username", max_chars=50)
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Sign In", key="login_submit", type="primary", use_container_width=True):
            if not username or not password:
                st.error("Please enter username and password.")
                return
            success, user, error = authenticate_internal(username, password)
            if success:
                set_authenticated_user(user)
                st.success(f"Welcome, {user['full_name']}! Redirecting to dashboard…")
                st.query_params.update({"page": "dashboard"})
                st.rerun()
            else:
                st.error(error)

    st.markdown(
        f"<p style='color:{C['text_muted']};font-size:0.85rem;text-align:center;margin-top:1rem;'>"
        f"This portal is for authorized staff only. For appointments, "
        f"<a href='javascript:void(0)' onclick='window.parent.location.search=\"?page=book\"'>book online here</a>."
        f"</p>",
        unsafe_allow_html=True,
    )