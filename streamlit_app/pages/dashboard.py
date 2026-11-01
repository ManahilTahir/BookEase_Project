"""Internal dashboard page for the BookEase Streamlit app.

Preserves the Flask dashboard's role: a lightweight landing for authenticated
staff that points to the desktop app for full management features.
Shows live dashboard metrics (reusing BookingService.get_dashboard_metrics)
so staff get at-a-glance visibility in the browser too.
"""

import streamlit as st

from streamlit_app.config import BRAND_COLORS
from streamlit_app.db import get_dashboard_summary
from streamlit_app.components import render_hero
from streamlit_app.state import is_authenticated, get_current_user, has_permission, logout

C = BRAND_COLORS


def render() -> None:
    if not is_authenticated():
        st.query_params.update({"page": "login"})
        st.rerun()
        return

    user = get_current_user()
    render_hero(
        "Internal Dashboard",
        f"Welcome back, {user['full_name']} ({user['role'].title()})",
    )

    if st.button("🚪  Sign Out", key="dash_logout"):
        logout()
        st.query_params.update({"page": "home"})
        st.rerun()

    st.markdown("---")

    try:
        m = get_dashboard_summary()
    except Exception:
        m = {}

    if m:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Today's Bookings", m.get("today_count", 0))
        with col2:
            st.metric("Total Revenue", f"${m.get('total_revenue', 0):.0f}")
        with col3:
            st.metric("Active Staff", m.get("active_staff", 0))
        with col4:
            st.metric("Completion Rate", f"{m.get('completion_rate', 0)}%")

        st.markdown("---")

        col5, col6 = st.columns(2)
        with col5:
            st.markdown("#### Status Distribution")
            sd = m.get("status_distribution", {})
            for status, count in sd.items():
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;'>"
                    f"<span style='color:{C['text_sec']};'>{status}</span>"
                    f"<span style='color:{C['text']};font-weight:600;'>{count}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        with col6:
            st.markdown("#### Popular Services")
            sp = m.get("service_popularity", {})
            for svc_name, count in sorted(sp.items(), key=lambda x: -x[1])[:5]:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;padding:0.3rem 0;'>"
                    f"<span style='color:{C['text_sec']};'>{svc_name}</span>"
                    f"<span style='color:{C['text']};font-weight:600;'>{count}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")

    st.markdown(
        f"""
        <div style='background:{C['bg_card']};border:1px solid {C['border']};
            border-radius:1rem;padding:1.5rem;'>
            <h3>Desktop Application Required</h3>
            <p style='color:{C['text_sec']};'>
            Full staff management, scheduling, reporting, and customer management features
            are available in the <strong style='color:{C['text']};'>BookEase Desktop Application</strong>.
            </p>
            <p style='color:{C['text_sec']};'>
            This web portal is for customer-facing bookings. Use the desktop app for internal operations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("View Public Website", key="dash_public", use_container_width=True):
            st.query_params.update({"page": "home"})
            st.rerun()
    with col_b:
        if st.button("Test Booking Flow", key="dash_test_book", use_container_width=True):
            st.query_params.update({"page": "book"})
            st.rerun()