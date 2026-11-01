"""Booking confirmation page for the BookEase Streamlit app."""

import streamlit as st

from streamlit_app.config import BRAND_COLORS
from streamlit_app.db import get_confirmation_data
from streamlit_app.components import render_hero

C = BRAND_COLORS


def render() -> None:
    settings = st.session_state.get("be_settings", {})
    currency = settings.get("currency_symbol", "$")
    ref = st.query_params.get("ref", "")

    appt = get_confirmation_data(ref) if ref else None

    if not appt:
        render_hero("Booking Not Found", "")
        st.error(f"No booking found with reference {ref}.")
        if st.button("← Back to Home", key="conf_home"):
            st.query_params.clear()
            st.rerun()
        return

    st.markdown(
        f"""
        <div style='text-align:center;padding:2rem;background:{C['bg_card']};
            border-radius:1.5rem;border:1px solid {C['border']};margin-bottom:1.5rem;'>
            <div style='font-size:3rem;color:{C['success']};'>✓</div>
            <h2 style='margin:0.5rem 0;'>Booking Confirmed!</h2>
            <p style='color:{C['text_sec']};'>Your appointment has been successfully booked.</p>
            <div class='be-ref-box'>
                <span style='color:{C['text_sec']};font-size:0.85rem;'>Booking Reference</span><br>
                <span class='be-ref-number'>{appt['appointment_number']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    details = [
        ("💆", "Service", appt["service_name"]),
        ("👤", "Specialist", f"{appt['staff_name']} — {appt['staff_role']}"),
        ("📅", "Date", appt["date"]),
        ("🕐", "Time", f"{appt['start_time']} – {appt['end_time']}"),
        ("💰", "Total Amount", f"{currency}{appt['price']:.2f}"),
        ("📇", "Booked For", appt["customer_name"]),
    ]
    for icon, label, value in details:
        st.markdown(
            f"""
            <div style='display:flex;align-items:center;gap:0.75rem;padding:0.6rem 1rem;
                background:{C['bg_card']};border:1px solid {C['border']};
                border-radius:0.625rem;margin-bottom:0.5rem;'>
                <span style='font-size:1.3rem;'>{icon}</span>
                <div>
                    <span style='color:{C['text_sec']};font-size:0.8rem;'>{label}</span><br>
                    <span style='color:{C['text']};font-weight:500;'>{value}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    phone = settings.get("phone", "our office")
    st.markdown(
        f"""
        <div style='background:{C['bg_surface']};border:1px solid {C['border']};
            border-radius:0.625rem;padding:1rem;margin-top:1rem;'>
            <p style='color:{C['text_sec']};'>📞 To reschedule or cancel, please call us at
            <strong style='color:{C['text']};'>{phone}</strong> with your booking reference.</p>
            {f"<p style='color:{C['text_sec']};'>📝 Your notes: <em>{appt['notes']}</em></p>" if appt.get('notes') else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Book Another Appointment", key="conf_book_again", use_container_width=True):
            st.query_params.update({"page": "book"})
            st.rerun()
    with col2:
        if st.button("Back to Home", key="conf_home", type="primary", use_container_width=True):
            st.query_params.clear()
            st.rerun()