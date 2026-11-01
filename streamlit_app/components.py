"""Reusable UI components for the BookEase Streamlit app."""

import streamlit as st

from streamlit_app.config import BRAND_COLORS, PAGES, INTERNAL_PAGES
from streamlit_app.state import is_authenticated, get_current_user

C = BRAND_COLORS


def render_navbar() -> None:
    """Render the top navigation bar in the sidebar."""
    settings = st.session_state.get("be_settings", {})
    biz_name = settings.get("business_name", "Lumière Wellness")

    with st.sidebar:
        st.markdown(
            f"<div style='text-align:center;padding:0.5rem 0 1rem 0;'>"
            f"<span style='font-size:1.5rem;color:{C['accent']};'>✦</span><br>"
            f"<span style='font-family:\"Playfair Display\",Georgia,serif;font-size:1.15rem;"
            f"color:{C['text']};font-weight:600;'>{biz_name}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.divider()

        for page_key, label, icon in PAGES:
            if st.button(f"{icon}  {label}", key=f"nav_{page_key}", use_container_width=True):
                _navigate(page_key)

        st.divider()

        if is_authenticated():
            user = get_current_user()
            st.markdown(
                f"<p style='color:{C['text_sec']};font-size:0.85rem;'>"
                f"Signed in as<br><strong>{user['full_name']}</strong> ({user['role']})"
                f"</p>",
                unsafe_allow_html=True,
            )
            if st.button("📊  Dashboard", key="nav_dashboard", use_container_width=True):
                _navigate("dashboard")
            if st.button("🚪  Sign Out", key="nav_logout", use_container_width=True):
                from streamlit_app.state import logout
                logout()
                _navigate("home")
                st.rerun()
        else:
            if st.button("🔐  Staff Login", key="nav_login", use_container_width=True):
                _navigate("login")


def render_footer() -> None:
    """Render the site footer."""
    settings = st.session_state.get("be_settings", {})
    biz_name = settings.get("business_name", "Lumière Wellness & Spa")
    biz_cat = settings.get("business_category", "Wellness & Spa")
    phone = settings.get("phone", "")
    email = settings.get("email", "")
    address = settings.get("address", "")

    contact_lines = []
    if address:
        contact_lines.append(f"📍 {address}")
    if phone:
        contact_lines.append(f"📞 {phone}")
    if email:
        contact_lines.append(f"✉️ {email}")
    contact_html = "<br>".join(contact_lines)

    st.markdown(
        f"""
        <div style='margin-top:3rem;padding:2rem 0;border-top:1px solid {C['border']};'>
            <div style='display:flex;flex-wrap:wrap;gap:2rem;justify-content:space-between;'>
                <div>
                    <span style='font-size:1.2rem;color:{C['accent']};'>✦</span>
                    <span style='font-family:\"Playfair Display\",Georgia,serif;font-size:1.1rem;
                        color:{C['text']};font-weight:600;'>{biz_name}</span>
                    <p style='color:{C['text_sec']};font-size:0.85rem;margin-top:0.25rem;'>{biz_cat}</p>
                </div>
                <div>
                    <p style='color:{C['text_sec']};font-size:0.85rem;line-height:1.8;'>
                    {contact_html}
                    </p>
                </div>
                <div>
                    <p style='color:{C['text_sec']};font-size:0.85rem;line-height:1.8;'>
                    Mon–Fri: 9:00 AM – 6:00 PM<br>
                    Saturday: 10:00 AM – 4:00 PM<br>
                    Sunday: Closed
                    </p>
                </div>
            </div>
            <div style='text-align:center;margin-top:1.5rem;'>
                <p style='color:{C['text_muted']};font-size:0.8rem;'>
                    © 2026 {biz_name}. All rights reserved. · Powered by <strong>BookEase</strong>
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str = "", badge: str = "") -> None:
    """Render a page hero section."""
    badge_html = f"<span class='be-badge'>{badge}</span><br>" if badge else ""
    st.markdown(
        f"""
        <div class='be-hero'>
            {badge_html}
            <h1 style='margin:0;'>{title}</h1>
            <p style='color:{C['text_sec']};margin-top:0.5rem;font-size:1.05rem;'>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_service_card(svc: dict, currency: str = "$", selected: bool = False) -> None:
    """Render a service card as HTML."""
    desc = svc.get("description", "")
    if len(desc) > 120:
        desc = desc[:120] + "…"
    opts_hint = ""
    if svc.get("options"):
        opts_hint = f"<br><span style='color:{C['accent']};font-size:0.8rem;'>⏱ Multiple durations available</span>"
    card_cls = "be-card be-card-selected" if selected else "be-card"
    st.markdown(
        f"""
        <div class='{card_cls}'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div>
                    <span style='color:{C['text_sec']};font-size:0.8rem;'>{svc.get('category','')}</span><br>
                    <strong style='font-size:1.1rem;color:{C['text']};'>{svc['name']}</strong>
                </div>
                <div style='text-align:right;'>
                    <span class='be-price'>{currency}{svc['price']:.0f}</span><br>
                    <span style='color:{C['text_sec']};font-size:0.85rem;'>🕐 {svc['duration_minutes']} min</span>
                </div>
            </div>
            <p style='color:{C['text_sec']};margin-top:0.5rem;font-size:0.9rem;'>{desc}</p>
            {opts_hint}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_staff_card(staff: dict, currency: str = "$") -> None:
    """Render a specialist card as HTML."""
    name = staff["name"]
    initials = "".join(w[0] for w in name.split()[:2])
    color = staff.get("color_code", C["accent"])
    specs = staff.get("specialties", "")
    if len(specs) > 80:
        specs = specs[:80] + "…"
    services = staff.get("services", [])
    svc_tags = " ".join(
        f"<span style='background:{C['accent']}22;color:{C['accent_light']};"
        f"border-radius:9999px;padding:0.15rem 0.5rem;font-size:0.75rem;margin:0.1rem;'>{s['name']}</span>"
        for s in services[:3]
    )
    st.markdown(
        f"""
        <div class='be-card'>
            <div style='display:flex;align-items:center;gap:1rem;'>
                <div style='width:48px;height:48px;border-radius:50%;background:{color}22;
                    border:2px solid {color};display:flex;align-items:center;justify-content:center;'>
                    <span style='color:{color};font-weight:700;font-size:1.1rem;'>{initials}</span>
                </div>
                <div>
                    <strong style='color:{C['text']};font-size:1.05rem;'>{name}</strong><br>
                    <span style='color:{C['text_sec']};font-size:0.85rem;'>{staff.get('role_title','')}</span>
                </div>
            </div>
            {f"<p style='color:{C['text_sec']};margin-top:0.5rem;font-size:0.85rem;'>{specs}</p>" if specs else ""}
            {f"<div style='margin-top:0.5rem;'>{svc_tags}</div>" if svc_tags else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _navigate(page: str, **params) -> None:
    """Set query params to navigate to a page."""
    from streamlit_app.state import reset_booking_wizard
    if page == "book":
        pass
    elif page != "book":
        reset_booking_wizard()
    qp = {"page": page}
    qp.update(params)
    st.query_params.update(qp)