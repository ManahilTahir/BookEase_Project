"""Branding, colours, and configuration for the BookEase Streamlit app.

Mirrors the Flask web layer's design tokens (dark burgundy + rose/pink)
so the Streamlit UI preserves the existing BookEase visual identity.
"""

import os

APP_NAME = "BookEase"
APP_VERSION = "1.0.0"

BRAND_COLORS = {
    "primary": "#4A1728",
    "primary_light": "#6B2040",
    "accent": "#C4627A",
    "accent_light": "#E8899A",
    "bg": "#1A0A0E",
    "bg_card": "#2A1118",
    "bg_surface": "#1F0D12",
    "bg_deep": "#0D0507",
    "text": "#F5E6EA",
    "text_sec": "#B8848F",
    "text_muted": "#7A5560",
    "border": "#3D1820",
    "border_strong": "#5A2535",
    "success": "#10B981",
    "error": "#EF4444",
    "warning": "#F59E0B",
}

FONT_DISPLAY = "'Playfair Display', Georgia, serif"
FONT_BODY = "'Inter', system-ui, -apple-system, sans-serif"

SECRET_KEY = os.environ.get("BOOKEASE_SECRET_KEY", "bookease-streamlit-dev-secret")
SESSION_LIFETIME_HOURS = 8

PAGES = [
    ("home", "Home", "🏠"),
    ("services", "Services", "💆"),
    ("specialists", "Specialists", "👩‍⚕️"),
    ("book", "Book Now", "📅"),
]

INTERNAL_PAGES = [
    ("login", "Staff Login", "🔐"),
    ("dashboard", "Dashboard", "📊"),
]