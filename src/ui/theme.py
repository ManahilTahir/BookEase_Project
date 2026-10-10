"""Modern UI Theme and Design Tokens for BookEase."""

import customtkinter as ctk

# Color Palette Definitions
PALETTE = {
    "dark": {
        "bg_primary": "#0F172A",       # Slate 900
        "bg_sidebar": "#0B1120",       # Darkest slate
        "card_bg": "#1E293B",          # Slate 800
        "card_hover": "#243248",
        "card_secondary": "#283548",   # Slate 750
        "border": "#334155",           # Slate 700
        "border_light": "#1E293B",
        "text_primary": "#F8FAFC",     # White/Slate 50
        "text_secondary": "#94A3B8",   # Slate 400
        "text_muted": "#64748B",       # Slate 500
        "accent": "#3B82F6",           # Blue 500
        "accent_hover": "#2563EB",     # Blue 600
        "accent_light": "rgba(59, 130, 246, 0.15)",
        "success": "#10B981",          # Emerald 500
        "success_bg": "#064E3B",
        "warning": "#F59E0B",          # Amber 500
        "warning_bg": "#78350F",
        "danger": "#EF4444",           # Rose 500
        "danger_hover": "#DC2626",
        "danger_bg": "#7F1D1D",
        "purple": "#8B5CF6",           # Violet 500
        "cyan": "#06B6D4",
    },
    "light": {
        "bg_primary": "#F8FAFC",       # Slate 50
        "bg_sidebar": "#F1F5F9",       # Slate 100
        "card_bg": "#FFFFFF",          # Pure white
        "card_hover": "#F8FAFC",
        "card_secondary": "#F1F5F9",   # Slate 100
        "border": "#E2E8F0",           # Slate 200
        "border_light": "#CBD5E1",
        "text_primary": "#0F172A",     # Slate 900
        "text_secondary": "#475569",   # Slate 600
        "text_muted": "#94A3B8",       # Slate 400
        "accent": "#2563EB",           # Blue 600
        "accent_hover": "#1D4ED8",     # Blue 700
        "accent_light": "#EFF6FF",
        "success": "#059669",          # Emerald 600
        "success_bg": "#ECFDF5",
        "warning": "#D97706",          # Amber 600
        "warning_bg": "#FFFBEB",
        "danger": "#DC2626",           # Rose 600
        "danger_hover": "#B91C1C",
        "danger_bg": "#FEF2F2",
        "purple": "#7C3AED",           # Violet 600
        "cyan": "#0891B2",
    },
}

# Typography Presets
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUBTITLE = ("Segoe UI", 16, "bold")
FONT_HEADING = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 12)
FONT_BODY_BOLD = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 10)
FONT_SMALL_BOLD = ("Segoe UI", 10, "bold")
FONT_METRIC = ("Segoe UI", 26, "bold")
FONT_ICON = ("Segoe UI", 16)


def get_color(key: str, mode: str = "dark") -> str:
    """Safely fetch color token."""
    mode_palette = PALETTE.get(mode, PALETTE["dark"])
    return mode_palette.get(key, "#3B82F6")


def apply_global_styles():
    """Apply default appearance mode and color theme for CustomTkinter."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
