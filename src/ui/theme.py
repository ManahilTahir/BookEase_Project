"""Modern UI Theme and Design Tokens for BookEase."""

from typing import Dict, Any, List, Optional
import customtkinter as ctk

# Color Palette Definitions for Multi-Theme Architecture
THEME_PALETTES: Dict[str, Dict[str, Any]] = {
    "midnight_teal": {
        "key": "midnight_teal",
        "name": "Midnight Navy & Vivid Teal",
        "icon": "🌊",
        "description": "Deep corporate midnight navy with crisp white cards, slate buttons and vivid teal accents",
        "ctk_theme": "blue",
        "dark": {
            "bg_primary": "#0A1626",       # Deepest Midnight Navy
            "bg_sidebar": "#07101C",       # Darkest Midnight Sidebar
            "header_bg": "#0F2238",        # Deep Navy Header Banner
            "card_bg": "#10243C",          # Rich Navy Blue Card
            "card_hover": "#163050",       # Card Hover
            "card_secondary": "#1B3658",   # Card Secondary / Slate
            "border": "#1E4268",           # Subtle Border
            "border_light": "#122A46",
            "text_primary": "#FFFFFF",     # Crisp White
            "text_secondary": "#A0B4CC",   # Soft Blue-Grey
            "text_muted": "#6886A6",       # Muted Blue
            "accent": "#0DA58E",           # Vivid Teal (from New Booking button)
            "accent_hover": "#0B8B77",     # Darker Teal
            "accent_light": "rgba(13, 165, 142, 0.15)",
            "button_secondary": "#1E3A58", # View Schedule dark slate button
            "button_secondary_hover": "#284A70",
            "success": "#10B981",          # Emerald 500
            "success_bg": "#064E3B",
            "warning": "#F59E0B",          # Amber 500
            "warning_bg": "#78350F",
            "danger": "#F43F5E",           # Rose 500
            "danger_hover": "#E11D48",
            "danger_bg": "#881337",
            "purple": "#8B5CF6",
            "cyan": "#0EA5E9",
        },
        "light": {
            "bg_primary": "#F1F5F9",       # Clean light slate
            "bg_sidebar": "#0F2238",       # Deep Navy Sidebar
            "header_bg": "#0F2238",        # Deep Navy Header Banner
            "card_bg": "#FFFFFF",          # Pure White Card
            "card_hover": "#F8FAFC",
            "card_secondary": "#F1F5F9",
            "border": "#E2E8F0",
            "border_light": "#CBD5E1",
            "text_primary": "#0F172A",     # Slate 900
            "text_secondary": "#475569",   # Slate 600
            "text_muted": "#94A3B8",       # Slate 400
            "accent": "#0DA58E",           # Vivid Teal
            "accent_hover": "#0B8B77",     # Darker Teal
            "accent_light": "#F0FDFA",
            "button_secondary": "#1E3A58",
            "button_secondary_hover": "#284A70",
            "success": "#10B981",
            "success_bg": "#ECFDF5",
            "warning": "#D97706",
            "warning_bg": "#FFFBEB",
            "danger": "#E11D48",
            "danger_hover": "#BE123C",
            "danger_bg": "#FFE4E6",
            "purple": "#7C3AED",
            "cyan": "#0D9488",
        },
    },
    "emerald": {
        "key": "emerald",
        "name": "Emerald & Mint Luxury",
        "icon": "🌿",
        "description": "Deep forest slate with vivid emerald & mint accents — tailored for wellness & spa",
        "ctk_theme": "green",
        "dark": {
            "bg_primary": "#0A1B16",       # Deep Forest Night
            "bg_sidebar": "#06120E",       # Deepest Pine Sidebar
            "card_bg": "#112620",          # Rich Emerald Card
            "card_hover": "#17342B",       # Card Hover
            "card_secondary": "#1A3930",   # Card Secondary
            "border": "#1E4B3E",           # Subtle Emerald Border
            "border_light": "#112620",
            "text_primary": "#F2FBF7",     # Mint Cream White
            "text_secondary": "#9ED2C0",   # Soft Sage
            "text_muted": "#5E9382",       # Muted Pine
            "accent": "#10B981",           # Vibrant Emerald 500
            "accent_hover": "#059669",     # Emerald 600
            "accent_light": "rgba(16, 185, 129, 0.15)",
            "success": "#34D399",          # Mint 400
            "success_bg": "#064E3B",
            "warning": "#F59E0B",          # Amber 500
            "warning_bg": "#78350F",
            "danger": "#F43F5E",           # Rose 500
            "danger_hover": "#E11D48",
            "danger_bg": "#881337",
            "purple": "#A78BFA",
            "cyan": "#2DD4BF",
        },
        "light": {
            "bg_primary": "#F0FDF4",       # Soft Mint Slate
            "bg_sidebar": "#E2F7EB",       # Sage Tint Sidebar
            "card_bg": "#FFFFFF",          # Pure White
            "card_hover": "#F0FDF4",
            "card_secondary": "#E6F4ED",
            "border": "#A7F3D0",
            "border_light": "#6EE7B7",
            "text_primary": "#064E3B",     # Deep Forest Text
            "text_secondary": "#047857",
            "text_muted": "#6EE7B7",
            "accent": "#059669",
            "accent_hover": "#047857",
            "accent_light": "#ECFDF5",
            "success": "#10B981",
            "success_bg": "#ECFDF5",
            "warning": "#D97706",
            "warning_bg": "#FFFBEB",
            "danger": "#E11D48",
            "danger_hover": "#BE123C",
            "danger_bg": "#FFE4E6",
            "purple": "#7C3AED",
            "cyan": "#0D9488",
        },
    },
    "violet": {
        "key": "violet",
        "name": "Royal Amethyst & Violet",
        "icon": "👑",
        "description": "Deep twilight with vibrant violet & purple accents — modern salon & beauty aesthetic",
        "ctk_theme": "blue",
        "dark": {
            "bg_primary": "#0F0B1A",
            "bg_sidebar": "#090612",
            "card_bg": "#19132E",
            "card_hover": "#221A3E",
            "card_secondary": "#251C44",
            "border": "#392B65",
            "border_light": "#19132E",
            "text_primary": "#FAF7FD",
            "text_secondary": "#C5BBE3",
            "text_muted": "#8173A5",
            "accent": "#8B5CF6",
            "accent_hover": "#7C3AED",
            "accent_light": "rgba(139, 92, 246, 0.15)",
            "success": "#10B981",
            "success_bg": "#064E3B",
            "warning": "#F59E0B",
            "warning_bg": "#78350F",
            "danger": "#EF4444",
            "danger_hover": "#DC2626",
            "danger_bg": "#7F1D1D",
            "purple": "#C084FC",
            "cyan": "#38BDF8",
        },
        "light": {
            "bg_primary": "#FAF5FF",
            "bg_sidebar": "#F3E8FF",
            "card_bg": "#FFFFFF",
            "card_hover": "#FAF5FF",
            "card_secondary": "#F3E8FF",
            "border": "#E9D5FF",
            "border_light": "#D8B4FE",
            "text_primary": "#3B0764",
            "text_secondary": "#6B21A8",
            "text_muted": "#A855F7",
            "accent": "#7C3AED",
            "accent_hover": "#6D28D9",
            "accent_light": "#F5F3FF",
            "success": "#059669",
            "success_bg": "#ECFDF5",
            "warning": "#D97706",
            "warning_bg": "#FFFBEB",
            "danger": "#DC2626",
            "danger_hover": "#B91C1C",
            "danger_bg": "#FEF2F2",
            "purple": "#7C3AED",
            "cyan": "#0891B2",
        },
    },
    "cyan": {
        "key": "cyan",
        "name": "Ocean Cyan & Midnight",
        "icon": "🌊",
        "description": "Deep navy with electric cyan & sky blue accents — clinical & dental precision",
        "ctk_theme": "blue",
        "dark": {
            "bg_primary": "#0B1524",
            "bg_sidebar": "#060E1A",
            "card_bg": "#122238",
            "card_hover": "#172D4A",
            "card_secondary": "#1B3454",
            "border": "#23446D",
            "border_light": "#122238",
            "text_primary": "#F0F9FF",
            "text_secondary": "#94BCE0",
            "text_muted": "#5B86AD",
            "accent": "#06B6D4",
            "accent_hover": "#0891B2",
            "accent_light": "rgba(6, 182, 212, 0.15)",
            "success": "#10B981",
            "success_bg": "#064E3B",
            "warning": "#F59E0B",
            "warning_bg": "#78350F",
            "danger": "#EF4444",
            "danger_hover": "#DC2626",
            "danger_bg": "#7F1D1D",
            "purple": "#8B5CF6",
            "cyan": "#22D3EE",
        },
        "light": {
            "bg_primary": "#ECFEFF",
            "bg_sidebar": "#CFFAFE",
            "card_bg": "#FFFFFF",
            "card_hover": "#ECFEFF",
            "card_secondary": "#CFFAFE",
            "border": "#A5F3FC",
            "border_light": "#67E8F9",
            "text_primary": "#164E63",
            "text_secondary": "#0E7490",
            "text_muted": "#06B6D4",
            "accent": "#0891B2",
            "accent_hover": "#0E7490",
            "accent_light": "#F0FDFA",
            "success": "#059669",
            "success_bg": "#ECFDF5",
            "warning": "#D97706",
            "warning_bg": "#FFFBEB",
            "danger": "#DC2626",
            "danger_hover": "#B91C1C",
            "danger_bg": "#FEF2F2",
            "purple": "#7C3AED",
            "cyan": "#0891B2",
        },
    },
    "rose": {
        "key": "rose",
        "name": "Sunset Rose & Coral",
        "icon": "🌅",
        "description": "Obsidian slate with rose pink & coral accents — elegant boutique style",
        "ctk_theme": "blue",
        "dark": {
            "bg_primary": "#190E14",
            "bg_sidebar": "#12080D",
            "card_bg": "#27141E",
            "card_hover": "#331B28",
            "card_secondary": "#391D2D",
            "border": "#52263F",
            "border_light": "#27141E",
            "text_primary": "#FFF1F2",
            "text_secondary": "#E2A9BB",
            "text_muted": "#9A6273",
            "accent": "#F43F5E",
            "accent_hover": "#E11D48",
            "accent_light": "rgba(244, 63, 94, 0.15)",
            "success": "#10B981",
            "success_bg": "#064E3B",
            "warning": "#F59E0B",
            "warning_bg": "#78350F",
            "danger": "#EF4444",
            "danger_hover": "#DC2626",
            "danger_bg": "#7F1D1D",
            "purple": "#C084FC",
            "cyan": "#06B6D4",
        },
        "light": {
            "bg_primary": "#FFF1F2",
            "bg_sidebar": "#FFE4E6",
            "card_bg": "#FFFFFF",
            "card_hover": "#FFF1F2",
            "card_secondary": "#FFE4E6",
            "border": "#FECDD3",
            "border_light": "#FDA4AF",
            "text_primary": "#881337",
            "text_secondary": "#BE123C",
            "text_muted": "#FB7185",
            "accent": "#E11D48",
            "accent_hover": "#BE123C",
            "accent_light": "#FFF1F2",
            "success": "#059669",
            "success_bg": "#ECFDF5",
            "warning": "#D97706",
            "warning_bg": "#FFFBEB",
            "danger": "#DC2626",
            "danger_hover": "#B91C1C",
            "danger_bg": "#FEF2F2",
            "purple": "#7C3AED",
            "cyan": "#0891B2",
        },
    },
    "amber": {
        "key": "amber",
        "name": "Warm Amber & Gold",
        "icon": "🏆",
        "description": "Dark charcoal with rich warm amber & gold accents — executive luxury",
        "ctk_theme": "dark-blue",
        "dark": {
            "bg_primary": "#191510",
            "bg_sidebar": "#120F0A",
            "card_bg": "#262016",
            "card_hover": "#332B1E",
            "card_secondary": "#3B3122",
            "border": "#53442C",
            "border_light": "#262016",
            "text_primary": "#FFFBEB",
            "text_secondary": "#D7C59E",
            "text_muted": "#92805E",
            "accent": "#F59E0B",
            "accent_hover": "#D97706",
            "accent_light": "rgba(245, 158, 11, 0.15)",
            "success": "#10B981",
            "success_bg": "#064E3B",
            "warning": "#F59E0B",
            "warning_bg": "#78350F",
            "danger": "#EF4444",
            "danger_hover": "#DC2626",
            "danger_bg": "#7F1D1D",
            "purple": "#8B5CF6",
            "cyan": "#06B6D4",
        },
        "light": {
            "bg_primary": "#FFFBEB",
            "bg_sidebar": "#FEF3C7",
            "card_bg": "#FFFFFF",
            "card_hover": "#FFFBEB",
            "card_secondary": "#FEF3C7",
            "border": "#FDE68A",
            "border_light": "#FCD34D",
            "text_primary": "#78350F",
            "text_secondary": "#B45309",
            "text_muted": "#F59E0B",
            "accent": "#D97706",
            "accent_hover": "#B45309",
            "accent_light": "#FFFBEB",
            "success": "#059669",
            "success_bg": "#ECFDF5",
            "warning": "#D97706",
            "warning_bg": "#FFFBEB",
            "danger": "#DC2626",
            "danger_hover": "#B91C1C",
            "danger_bg": "#FEF2F2",
            "purple": "#7C3AED",
            "cyan": "#0891B2",
        },
    },
    "slate": {
        "key": "slate",
        "name": "Classic Slate & Blue",
        "icon": "🔷",
        "description": "Original deep slate with electric blue accents",
        "ctk_theme": "blue",
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
    },
}

# The active mutable PALETTE dict (Defaulted to Midnight Navy & Vivid Teal)
DEFAULT_THEME_KEY = "midnight_teal"
CURRENT_THEME_KEY = "midnight_teal"

PALETTE: Dict[str, Dict[str, str]] = {
    "dark": dict(THEME_PALETTES[DEFAULT_THEME_KEY]["dark"]),
    "light": dict(THEME_PALETTES[DEFAULT_THEME_KEY]["light"]),
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


def get_available_themes() -> Dict[str, Dict[str, Any]]:
    """Return dictionary of all configured themes."""
    return THEME_PALETTES


def get_theme_display_names() -> List[str]:
    """Return list of formatted names for dropdown selectors."""
    return [f"{t['icon']} {t['name']}" for t in THEME_PALETTES.values()]


def theme_key_from_display_name(display_name: str) -> Optional[str]:
    """Resolve theme key from formatted dropdown display text."""
    for key, data in THEME_PALETTES.items():
        if display_name == f"{data['icon']} {data['name']}" or display_name == data["name"] or display_name == key:
            return key
    return None


def theme_display_name_from_key(key: str) -> str:
    """Return formatted display name for given theme key."""
    theme = THEME_PALETTES.get(key, THEME_PALETTES[DEFAULT_THEME_KEY])
    return f"{theme['icon']} {theme['name']}"


def get_current_theme_key() -> str:
    """Get active theme palette key."""
    return CURRENT_THEME_KEY


def get_saved_theme() -> str:
    """Fetch persisted theme from database or default to emerald."""
    try:
        from src.database.connection import get_db
        from src.database.models import BusinessSetting
        with get_db() as session:
            setting = session.query(BusinessSetting).filter(BusinessSetting.key == "color_theme").first()
            if setting and setting.value in THEME_PALETTES:
                return setting.value
    except Exception:
        pass
    return DEFAULT_THEME_KEY


def set_active_theme(key: str, persist: bool = True) -> str:
    """Apply and activate a color theme palette, updating PALETTE in-place."""
    global CURRENT_THEME_KEY
    if key not in THEME_PALETTES:
        key = DEFAULT_THEME_KEY

    CURRENT_THEME_KEY = key
    selected = THEME_PALETTES[key]

    PALETTE["dark"].clear()
    PALETTE["dark"].update(selected["dark"])
    PALETTE["light"].clear()
    PALETTE["light"].update(selected["light"])

    if persist:
        try:
            from src.database.connection import get_db
            from src.database.models import BusinessSetting
            with get_db() as session:
                setting = session.query(BusinessSetting).filter(BusinessSetting.key == "color_theme").first()
                if setting:
                    setting.value = key
                else:
                    session.add(BusinessSetting(key="color_theme", value=key))
                session.commit()
        except Exception:
            pass

    return key


def get_color(key: str, mode: str = "dark") -> str:
    """Safely fetch color token."""
    mode_palette = PALETTE.get(mode, PALETTE["dark"])
    return mode_palette.get(key, "#0DA58E")


def apply_global_styles():
    """Apply appearance mode and color theme for CustomTkinter."""
    saved_key = get_saved_theme()
    set_active_theme(saved_key, persist=False)
    ctk.set_appearance_mode("Dark")
    ctk_theme = THEME_PALETTES.get(saved_key, {}).get("ctk_theme", "green")
    try:
        ctk.set_default_color_theme(ctk_theme)
    except Exception:
        pass
