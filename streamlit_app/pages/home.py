"""Home page for the BookEase Streamlit app."""

import streamlit as st

from streamlit_app.config import BRAND_COLORS
from streamlit_app.db import get_home_data
from streamlit_app.components import render_hero, render_service_card, render_staff_card

C = BRAND_COLORS


def render() -> None:
    settings = st.session_state.get("be_settings", {})
    currency = settings.get("currency_symbol", "$")
    data = get_home_data()
    categories = data["categories"]
    staff_list = data["staff_list"]

    render_hero(
        "Your Path to Radiant Wellbeing",
        "Expert specialists. Luxury treatments. Instant online booking.",
        "✦ Premium Wellness Experience",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅  Book Your Appointment", key="hero_book", use_container_width=True, type="primary"):
            st.query_params.update({"page": "book"})
            st.rerun()
    with col2:
        if st.button("💆  Explore Services", key="hero_services", use_container_width=True):
            st.query_params.update({"page": "services"})
            st.rerun()

    st.markdown("---")

    st.markdown("### 🏆 Treatments Tailored for You")
    if categories:
        for category, svcs in categories.items():
            st.markdown(f"**{category}**")
            for svc in svcs[:3]:
                render_service_card(svc, currency)
            st.markdown("")
    else:
        st.info("Services are being updated. Please check back soon.")

    if st.button("View All Services →", key="home_all_services"):
        st.query_params.update({"page": "services"})
        st.rerun()

    st.markdown("---")
    st.markdown("### 👩‍⚕️ Meet Our Specialists")
    for st_data in staff_list[:4]:
        render_staff_card(st_data, currency)

    if st.button("Meet All Specialists →", key="home_all_staff"):
        st.query_params.update({"page": "specialists"})
        st.rerun()

    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align:center;padding:2rem;background:{C['bg_card']};
            border-radius:1rem;border:1px solid {C['border']};'>
            <h2>Ready for Your Transformation?</h2>
            <p style='color:{C['text_sec']};'>Book your appointment in under 2 minutes. No account required.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("✦ Book Now — It's Free", key="home_cta_book", use_container_width=True, type="primary"):
        st.query_params.update({"page": "book"})
        st.rerun()