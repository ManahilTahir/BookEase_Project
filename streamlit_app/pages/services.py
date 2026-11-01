"""Services listing page for the BookEase Streamlit app."""

import streamlit as st

from streamlit_app.config import BRAND_COLORS
from streamlit_app.db import get_services_with_specialists
from streamlit_app.components import render_hero, render_service_card

C = BRAND_COLORS


def render() -> None:
    settings = st.session_state.get("be_settings", {})
    currency = settings.get("currency_symbol", "$")
    services = get_services_with_specialists()

    render_hero(
        "Premium Wellness Services",
        "All prices include consultation. Book directly online with instant confirmation.",
        "Our Services",
    )

    all_cats = sorted({s["category"] for s in services})
    filter_options = ["All Services"] + all_cats
    selected_cat = st.selectbox("Filter by category", filter_options, key="svc_filter")

    filtered = services if selected_cat == "All Services" else [s for s in services if s["category"] == selected_cat]

    for svc in filtered:
        render_service_card(svc, currency)
        if svc.get("specialists"):
            specs = ", ".join(sp["name"] for sp in svc["specialists"])
            st.markdown(
                f"<p style='color:{C['text_sec']};font-size:0.85rem;margin:-0.5rem 0 1rem 0.5rem;'>"
                f"Available with: {specs}</p>",
                unsafe_allow_html=True,
            )
        if st.button(f"Book This Service", key=f"book_svc_{svc['id']}", use_container_width=True):
            st.query_params.update({"page": "book", "service_id": str(svc["id"])})
            st.rerun()
        st.markdown("")