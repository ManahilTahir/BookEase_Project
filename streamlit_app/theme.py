"""Theme / CSS injection for the BookEase Streamlit app.

Injects the BookEase brand identity (dark burgundy + rose/pink, Playfair
Display + Inter typography) into the Streamlit runtime via ``st.markdown``
with a ``<style>`` block.  Streamlit's default light/dark theme is overridden
to match the existing Flask portal's look.
"""

import streamlit as st

from streamlit_app.config import BRAND_COLORS, FONT_BODY, FONT_DISPLAY

C = BRAND_COLORS


def apply_theme() -> None:
    """Inject global CSS to brand the Streamlit app."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap');

        /* ── Root / body ─────────────────────────────────────────────── */
        .stApp {{
            background: {C['bg']};
            color: {C['text']};
            font-family: {FONT_BODY};
        }}

        /* ── Typography ──────────────────────────────────────────────── */
        h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
            font-family: {FONT_DISPLAY};
            color: {C['text']};
        }}
        h1 {{ font-weight: 700; }}
        h2 {{ font-weight: 600; }}

        /* ── Sidebar ─────────────────────────────────────────────────── */
        section[data-testid="stSidebar"] {{
            background: {C['bg_surface']};
            border-right: 1px solid {C['border']};
        }}
        section[data-testid="stSidebar"] * {{
            color: {C['text']} !important;
        }}

        /* ── Buttons ─────────────────────────────────────────────────── */
        .stButton > button, div[data-testid="stButton"] > button {{
            background: {C['primary']};
            color: {C['text']};
            border: 1px solid {C['border_strong']};
            border-radius: 0.625rem;
            font-weight: 600;
            padding: 0.5rem 1.25rem;
            transition: all 150ms ease;
        }}
        .stButton > button:hover, div[data-testid="stButton"] > button:hover {{
            background: {C['primary_light']};
            border-color: {C['accent']};
            color: {C['text']};
        }}
        /* Primary / accent button variant */
        .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {{
            background: {C['accent']};
            color: #fff;
            border: none;
        }}
        .stButton > button[kind="primary"]:hover {{
            background: {C['accent_light']};
        }}

        /* ── Cards / containers ──────────────────────────────────────── */
        .stContainer, div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {C['bg_card']};
            border: 1px solid {C['border']};
            border-radius: 1rem;
        }}

        /* ── Inputs ──────────────────────────────────────────────────── */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stDateInput > div > div > input {{
            background: {C['bg_deep']};
            color: {C['text']};
            border: 1px solid {C['border_strong']};
            border-radius: 0.5rem;
        }}
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: {C['accent']};
            box-shadow: 0 0 0 2px {C['accent']}33;
        }}

        /* ── Select / Selectbox ──────────────────────────────────────── */
        .stSelectbox > div > div > div {{
            background: {C['bg_deep']};
            color: {C['text']};
            border: 1px solid {C['border_strong']};
            border-radius: 0.5rem;
        }}

        /* ── Radio ───────────────────────────────────────────────────── */
        .stRadio > div {{
            background: {C['bg_card']};
            border-radius: 0.625rem;
            padding: 0.5rem;
        }}

        /* ── Metrics ─────────────────────────────────────────────────── */
        div[data-testid="stMetric"] {{
            background: {C['bg_card']};
            border: 1px solid {C['border']};
            border-radius: 0.625rem;
            padding: 1rem;
        }}
        div[data-testid="stMetricLabel"] {{
            color: {C['text_sec']};
        }}
        div[data-testid="stMetricValue"] {{
            color: {C['text']};
            font-family: {FONT_DISPLAY};
        }}

        /* ── Dataframe / table ───────────────────────────────────────── */
        .stDataFrame, .stTable {{
            background: {C['bg_card']};
        }}
        .stDataFrame table, .stTable table {{
            background: {C['bg_card']};
            color: {C['text']};
        }}
        .stDataFrame th, .stTable th {{
            background: {C['bg_surface']};
            color: {C['text']};
        }}

        /* ── Alerts ──────────────────────────────────────────────────── */
        .stAlert {{
            border-radius: 0.625rem;
        }}
        div[data-testid="stAlertContainerError"] {{
            background: {C['error']}22;
            border: 1px solid {C['error']};
        }}
        div[data-testid="stAlertContainerSuccess"] {{
            background: {C['success']}22;
            border: 1px solid {C['success']};
        }}
        div[data-testid="stAlertContainerWarning"] {{
            background: {C['warning']}22;
            border: 1px solid {C['warning']};
        }}

        /* ── Expander ────────────────────────────────────────────────── */
        .stExpander {{
            background: {C['bg_card']};
            border: 1px solid {C['border']};
            border-radius: 0.625rem;
        }}

        /* ── Divider ─────────────────────────────────────────────────── */
        .stDivider > div {{
            border-color: {C['border']};
        }}

        /* ── Hide default Streamlit chrome ───────────────────────────── */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header[data-testid="stHeader"] {{
            background: {C['bg_surface']};
            border-bottom: 1px solid {C['border']};
        }}

        /* ── Custom card classes ─────────────────────────────────────── */
        .be-card {{
            background: {C['bg_card']};
            border: 1px solid {C['border']};
            border-radius: 1rem;
            padding: 1.25rem;
            margin-bottom: 1rem;
            transition: border-color 220ms ease;
        }}
        .be-card:hover {{
            border-color: {C['accent']};
        }}
        .be-card-selected {{
            border: 2px solid {C['accent']};
            background: {C['bg_card']};
        }}
        .be-hero {{
            background: linear-gradient(135deg, {C['bg_surface']} 0%, {C['bg_card']} 100%);
            border-radius: 1.5rem;
            padding: 2.5rem 1.5rem;
            text-align: center;
            margin-bottom: 2rem;
        }}
        .be-badge {{
            display: inline-block;
            background: {C['accent']}22;
            color: {C['accent_light']};
            border: 1px solid {C['accent']}44;
            border-radius: 9999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }}
        .be-price {{
            color: {C['accent_light']};
            font-family: {FONT_DISPLAY};
            font-size: 1.25rem;
            font-weight: 700;
        }}
        .be-muted {{
            color: {C['text_sec']};
        }}
        .be-ref-box {{
            background: {C['bg_deep']};
            border: 2px dashed {C['accent']};
            border-radius: 0.75rem;
            padding: 1rem;
            text-align: center;
            margin: 1rem 0;
        }}
        .be-ref-number {{
            font-family: {FONT_DISPLAY};
            font-size: 1.75rem;
            font-weight: 700;
            color: {C['accent_light']};
            letter-spacing: 1px;
        }}

        /* ── Responsive ──────────────────────────────────────────────── */
        @media (max-width: 768px) {{
            .be-hero {{ padding: 1.5rem 1rem; }}
            h1 {{ font-size: 1.75rem; }}
            h2 {{ font-size: 1.4rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
