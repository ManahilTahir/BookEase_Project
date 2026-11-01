"""Booking wizard page for the BookEase Streamlit app.

Three-step wizard mirroring the Flask booking flow:
  1. Service + duration option + specialist
  2. Date + time slot
  3. Customer details + confirm
"""

from datetime import date, timedelta

import streamlit as st

from streamlit_app.config import BRAND_COLORS
from streamlit_app.db import (
    get_services_with_options,
    get_staff_for_service,
    get_available_slots,
    get_available_dates,
    create_booking,
)
from streamlit_app.components import render_hero
from streamlit_app.state import (
    get_booking_step,
    set_booking_step,
    get_booking_selection,
    update_booking_selection,
    reset_booking_wizard,
)

C = BRAND_COLORS


def render() -> None:
    settings = st.session_state.get("be_settings", {})
    currency = settings.get("currency_symbol", "$")
    services = get_services_with_options()

    render_hero("Book Your Appointment", "Complete in 3 simple steps. No account required.")

    step = get_booking_step()
    sel = get_booking_selection()

    _handle_preselect(services, sel)

    _render_progress(step)

    if step == 1:
        _render_step1(services, currency, sel)
    elif step == 2:
        _render_step2(currency, sel)
    elif step == 3:
        _render_step3(currency, sel)


def _handle_preselect(services, sel):
    """Apply service_id / staff_id from query params on first load."""
    if not sel and "service_id" in st.query_params:
        try:
            sid = int(st.query_params["service_id"])
            update_booking_selection(service_id=sid)
        except (ValueError, TypeError):
            pass
    if not sel and "staff_id" in st.query_params:
        try:
            fid = int(st.query_params["staff_id"])
            update_booking_selection(staff_id=fid)
        except (ValueError, TypeError):
            pass


def _render_progress(step: int) -> None:
    labels = ["Service & Specialist", "Date & Time", "Your Details"]
    cols = st.columns([1, 0.15, 1, 0.15, 1])
    for i, (col, label) in enumerate(zip([cols[0], cols[2], cols[4]], labels)):
        n = i + 1
        with col:
            active = n == step
            done = n < step
            dot_color = C["accent"] if (active or done) else C["border_strong"]
            text_color = C["text"] if (active or done) else C["text_muted"]
            weight = "700" if active else "400"
            check = "✓ " if done else ""
            st.markdown(
                f"<div style='text-align:center;'>"
                f"<span style='display:inline-block;width:28px;height:28px;border-radius:50%;"
                f"background:{dot_color};color:#fff;font-weight:700;line-height:28px;'>"
                f"{n if not done else '✓'}</span><br>"
                f"<span style='color:{text_color};font-weight:{weight};font-size:0.85rem;'>"
                f"{check}{label}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    st.markdown("---")


def _render_step1(services, currency, sel):
    st.markdown("#### Choose a Service")
    service_id = sel.get("service_id")

    service_names = {s["id"]: s["name"] for s in services}
    default_idx = 0
    if service_id and service_id in service_names:
        default_idx = list(service_names.keys()).index(service_id)

    col_a, col_b = st.columns([3, 2])
    with col_a:
        chosen_id = st.selectbox(
            "Service",
            list(service_names.keys()),
            format_func=lambda sid: service_names[sid],
            index=default_idx,
            key="wiz_service",
        )
    chosen_svc = next((s for s in services if s["id"] == chosen_id), None)
    if chosen_svc:
        update_booking_selection(service_id=chosen_id, service_name=chosen_svc["name"])

        with col_b:
            st.markdown(
                f"<div style='text-align:right;padding-top:1.5rem;'>"
                f"<span class='be-price'>{currency}{chosen_svc['price']:.0f}</span><br>"
                f"<span style='color:{C['text_sec']};'>🕐 {chosen_svc['duration_minutes']} min</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<p style='color:{C['text_sec']};font-size:0.9rem;'>{chosen_svc['description']}</p>",
            unsafe_allow_html=True,
        )

        option_id = None
        duration = chosen_svc["duration_minutes"]
        price = chosen_svc["price"]
        if chosen_svc.get("options"):
            st.markdown("#### Choose Duration")
            st.markdown(
                f"<p style='color:{C['text_sec']};font-size:0.85rem;'>"
                f"Select how long you'd like your appointment. Price adjusts automatically.</p>",
                unsafe_allow_html=True,
            )
            opt_labels = {
                o["id"]: f"{o['label']} — {currency}{o['price']:.0f}" for o in chosen_svc["options"]
            }
            opt_ids = list(opt_labels.keys())
            default_opt = 0
            if sel.get("option_id") and sel["option_id"] in opt_labels:
                default_opt = opt_ids.index(sel["option_id"])
            chosen_opt_id = st.selectbox(
                "Duration",
                opt_ids,
                format_func=lambda oid: opt_labels[oid],
                index=default_opt,
                key="wiz_option",
            )
            chosen_opt = next(o for o in chosen_svc["options"] if o["id"] == chosen_opt_id)
            option_id = chosen_opt_id
            duration = chosen_opt["duration_minutes"]
            price = chosen_opt["price"]
            update_booking_selection(option_id=option_id, duration=duration, price=price)
        else:
            update_booking_selection(option_id=None, duration=duration, price=price)

        st.markdown("#### Choose a Specialist")
        staff_list = get_staff_for_service(chosen_id)
        if not staff_list:
            st.warning("No specialists available for this service.")
            return
        staff_names = {f["id"]: f["name"] for f in staff_list}
        default_fidx = 0
        if sel.get("staff_id") and sel["staff_id"] in staff_names:
            default_fidx = list(staff_names.keys()).index(sel["staff_id"])
        chosen_fid = st.selectbox(
            "Specialist",
            list(staff_names.keys()),
            format_func=lambda fid: f"{staff_names[fid]} — {next(f['role_title'] for f in staff_list if f['id'] == fid)}",
            index=default_fidx,
            key="wiz_staff",
        )
        chosen_staff = next(f for f in staff_list if f["id"] == chosen_fid)
        update_booking_selection(staff_id=chosen_fid, staff_name=chosen_staff["name"])

        if st.button("Next: Pick a Time →", key="step1_next", type="primary", use_container_width=True):
            set_booking_step(2)
            st.rerun()


def _render_step2(currency, sel):
    service_name = sel.get("service_name", "—")
    staff_name = sel.get("staff_name", "—")
    staff_id = sel.get("staff_id")
    service_id = sel.get("service_id")
    duration = sel.get("duration")

    st.markdown(
        f"<div style='background:{C['bg_card']};border:1px solid {C['border']};"
        f"border-radius:0.625rem;padding:0.75rem 1rem;margin-bottom:1rem;'>"
        f"<span style='color:{C['text']};'><strong>{service_name}</strong> "
        f"<span style='color:{C['text_sec']};'>with</span> <strong>{staff_name}</strong></span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    today = date.today()
    max_date = today + timedelta(days=90)

    col_d, col_info = st.columns([2, 3])
    with col_d:
        chosen_date = st.date_input(
            "Select Date",
            min_value=today,
            max_value=max_date,
            value=today + timedelta(days=1),
            key="wiz_date",
        )
    with col_info:
        avail_dates = get_available_dates(staff_id, service_id) if staff_id and service_id else []
        if avail_dates:
            st.markdown(
                f"<p style='color:{C['text_sec']};font-size:0.85rem;padding-top:1.5rem;'>"
                f"Next available: {avail_dates[0]}</p>",
                unsafe_allow_html=True,
            )

    date_str = chosen_date.isoformat()
    update_booking_selection(date=date_str)

    slots = get_available_slots(staff_id, service_id, date_str, duration) if staff_id and service_id else []

    st.markdown("#### Available Time Slots")
    if not slots:
        st.info("No slots available on this date. Please try another date.")
    else:
        slot_labels = [f"{s['start']} – {s['end']}" for s in slots]
        chosen_slot = st.selectbox("Time", range(len(slots)), format_func=lambda i: slot_labels[i], key="wiz_slot")
        slot = slots[chosen_slot]
        update_booking_selection(start_time=slot["start"], end_time=slot["end"])

    col_back, col_next = st.columns([1, 1])
    with col_back:
        if st.button("← Back", key="step2_back", use_container_width=True):
            set_booking_step(1)
            st.rerun()
    with col_next:
        if slots:
            if st.button("Next: Your Details →", key="step2_next", type="primary", use_container_width=True):
                set_booking_step(3)
                st.rerun()


def _render_step3(currency, sel):
    st.markdown("#### Booking Summary")
    price = sel.get("price", 0)
    duration = sel.get("duration", "—")

    summary_rows = [
        ("Service", sel.get("service_name", "—")),
        ("Duration", f"{duration} min" if isinstance(duration, (int, float)) else str(duration)),
        ("Specialist", sel.get("staff_name", "—")),
        ("Date", sel.get("date", "—")),
        ("Time", f"{sel.get('start_time', '—')} – {sel.get('end_time', '—')}"),
    ]
    for label, value in summary_rows:
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:0.4rem 0;"
            f"border-bottom:1px solid {C['border']};'>"
            f"<span style='color:{C['text_sec']};'>{label}</span>"
            f"<span style='color:{C['text']};font-weight:500;'>{value}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;padding:0.6rem 0;margin-top:0.5rem;'>"
        f"<span style='color:{C['text']};font-weight:600;font-size:1.1rem;'>Total</span>"
        f"<span class='be-price' style='font-size:1.3rem;'>{currency}{price:.2f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### Your Details")

    col1, col2 = st.columns(2)
    with col1:
        customer_name = st.text_input("Full Name *", placeholder="e.g. Jane Smith", key="cust_name", max_chars=100)
    with col2:
        customer_phone = st.text_input("Phone Number *", placeholder="e.g. +1 555 123 4567", key="cust_phone", max_chars=30)

    customer_email = st.text_input("Email Address (optional)", placeholder="e.g. jane@example.com", key="cust_email", max_chars=100)
    notes = st.text_area("Notes (optional)", placeholder="Allergies, preferences, special requests…", key="cust_notes", max_chars=500)

    st.markdown(
        f"<p style='color:{C['text_muted']};font-size:0.8rem;'>"
        f"By confirming, you agree that your name, phone number, and notes will be stored to manage your booking."
        f"</p>",
        unsafe_allow_html=True,
    )

    col_back, col_confirm = st.columns([1, 1])
    with col_back:
        if st.button("← Back", key="step3_back", use_container_width=True):
            set_booking_step(2)
            st.rerun()
    with col_confirm:
        if st.button("✓ Confirm Booking", key="step3_confirm", type="primary", use_container_width=True):
            if not customer_name or len(customer_name) < 2:
                st.error("Please enter your full name (at least 2 characters).")
                return
            if not customer_phone or len(customer_phone) < 7:
                st.error("Please enter a valid phone number.")
                return

            payload = {
                "service_id": sel.get("service_id"),
                "staff_id": sel.get("staff_id"),
                "option_id": sel.get("option_id"),
                "date": sel.get("date"),
                "start_time": sel.get("start_time"),
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "notes": notes,
            }
            success, ref, error = create_booking(payload)
            if success:
                reset_booking_wizard()
                st.query_params.update({"page": "confirmation", "ref": ref})
                st.rerun()
            else:
                st.error(error)