"""Specialists listing page for the BookEase Streamlit app."""

import streamlit as st

from streamlit_app.config import BRAND_COLORS
from streamlit_app.db import get_specialists_with_services
from streamlit_app.components import render_hero, render_staff_card

C = BRAND_COLORS


def render() -> None:
    settings = st.session_state.get("be_settings", {})
    currency = settings.get("currency_symbol", "$")
    staff_list = get_specialists_with_services()

    render_hero(
        "Meet Our Specialists",
        "Experienced, certified professionals dedicated to your wellbeing.",
        "Our Team",
    )

    for staff in staff_list:
        render_staff_card(staff, currency)
        if staff.get("bio"):
            st.markdown(
                f"<p style='color:{C['text_sec']};font-size:0.9rem;margin:-0.5rem 0 0.5rem 0.5rem;'>{staff['bio']}</p>",
                unsafe_allow_html=True,
            )
        if staff.get("services"):
            with st.expander("Services offered", expanded=False):
                for svc in staff["services"]:
                    st.markdown(
                        f"**{svc['name']}** — {currency}{svc['price']:.0f} ({svc['duration_minutes']} min)"
                    )
        if st.button(f"Book with {staff['name'].split()[0]}", key=f"book_staff_{staff['id']}", use_container_width=True):
            st.query_params.update({"page": "book", "staff_id": str(staff["id"])})
            st.rerun()
        st.markdown("")