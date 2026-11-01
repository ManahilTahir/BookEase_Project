"""BookEase Streamlit Web Application — Entry Point.

Run locally:
    streamlit run streamlit_app.py

Deploy on Streamlit Community Cloud:
    Push this repo and point the app at ``streamlit_app.py``.

This app reuses the existing ``src/`` backend (models, availability engine,
booking service, security, audit logger) and shares the same SQLite database
(``data/bookease.db``) as the desktop application — no data duplication.
"""

import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("BookEase.Streamlit")

import streamlit as st

from src.database.connection import init_db
from streamlit_app.config import APP_NAME, APP_VERSION, BRAND_COLORS
from streamlit_app.theme import apply_theme
from streamlit_app.state import init_state
from streamlit_app.components import render_navbar, render_footer
from streamlit_app.db import get_settings

C = BRAND_COLORS


def main():
    st.set_page_config(
        page_title=f"{APP_NAME} — Book Online",
        page_icon="✦",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": f"{APP_NAME} v{APP_VERSION} — Professional Booking Management",
        },
    )

    if "be_db_initialized" not in st.session_state:
        logger.info("Initializing BookEase database…")
        init_db()
        st.session_state.be_db_initialized = True

    if "be_settings" not in st.session_state:
        st.session_state.be_settings = get_settings()

    init_state()
    apply_theme()
    render_navbar()

    page = st.query_params.get("page", "home")

    if page == "home":
        from streamlit_app.pages.home import render
    elif page == "services":
        from streamlit_app.pages.services import render
    elif page == "specialists":
        from streamlit_app.pages.specialists import render
    elif page == "book":
        from streamlit_app.pages.book import render
    elif page == "confirmation":
        from streamlit_app.pages.confirmation import render
    elif page == "login":
        from streamlit_app.pages.login import render
    elif page == "dashboard":
        from streamlit_app.pages.dashboard import render
    else:
        from streamlit_app.pages.home import render

    render()

    render_footer()


if __name__ == "__main__":
    main()
