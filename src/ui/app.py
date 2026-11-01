"""BookEase Main Application Window and Navigation Shell."""

import tkinter as tk
from datetime import date
from typing import Dict, Any, Optional
import customtkinter as ctk

from src.config import APP_NAME, APP_VERSION
from src.ui.theme import (
    PALETTE,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_HEADING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_SMALL_BOLD,
    apply_global_styles,
)
from src.core.security import SessionManager
from src.database.connection import get_db
from src.database.models import BusinessSetting
from src.ui.views import (
    LoginView,
    DashboardView,
    BookingWizardView,
    CalendarView,
    AppointmentsView,
    CustomersView,
    StaffView,
    CustomerBookingView,
    ServicesView,
    ReportsView,
    SettingsView,
)


class BookEaseApp(ctk.CTk):
    """Master application shell with responsive sidebar navigation."""

    def __init__(self):
        super().__init__()

        # Window Configuration
        self.title(f"{APP_NAME} — Professional Universal Booking Agent v{APP_VERSION}")
        self.geometry("1280x820")
        self.minsize(1050, 700)

        apply_global_styles()

        self.current_theme = "Dark"
        self.active_nav_key = "dashboard"

        # Container for screens
        self.main_container = ctk.CTkFrame(self, fg_color=PALETTE["dark"]["bg_primary"])
        self.main_container.pack(fill="both", expand=True)

        # Check authentication
        if not SessionManager.is_authenticated():
            self.show_login()
        else:
            self.show_workspace()

    def show_login(self):
        """Show full-screen login view."""
        for w in self.main_container.winfo_children():
            w.destroy()

        login_view = LoginView(
            self.main_container,
            on_login_success=self.on_login_success,
        )
        login_view.pack(fill="both", expand=True)

    def on_login_success(self):
        """Callback when user successfully logs in."""
        self.show_workspace()

    def show_workspace(self):
        """Build the full desktop workspace with sidebar and content router."""
        for w in self.main_container.winfo_children():
            w.destroy()

        self.main_container.grid_columnconfigure(0, weight=0)  # Sidebar
        self.main_container.grid_columnconfigure(1, weight=1)  # Content
        self.main_container.grid_rowconfigure(0, weight=1)

        # 1. Sidebar Navigation
        self.create_sidebar()

        # 2. Main Content Canvas
        self.content_canvas = ctk.CTkFrame(self.main_container, fg_color=PALETTE["dark"]["bg_primary"])
        self.content_canvas.grid(row=0, column=1, sticky="nsew")
        self.content_canvas.grid_columnconfigure(0, weight=1)
        self.content_canvas.grid_rowconfigure(0, weight=1)

        # Navigate to Dashboard by default
        self.navigate("dashboard")

    def create_sidebar(self):
        """Create sleek modern sidebar navigation."""
        self.sidebar = ctk.CTkFrame(
            self.main_container,
            width=240,
            corner_radius=0,
            fg_color=PALETTE["dark"]["bg_sidebar"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Brand Logo Header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(20, 16))

        logo_title_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        logo_title_row.pack(anchor="w")

        ctk.CTkLabel(
            logo_title_row,
            text="✨",
            font=("Segoe UI", 22),
            text_color=PALETTE["dark"]["accent"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_title_row,
            text=APP_NAME,
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        # Business Name Tag
        with get_db() as session:
            b_setting = session.query(BusinessSetting).filter(BusinessSetting.key == "business_name").first()
            biz_name = b_setting.value if b_setting else "Professional Practice"

        ctk.CTkLabel(
            brand_frame,
            text=biz_name,
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=PALETTE["dark"]["border"]).pack(fill="x", padx=16, pady=(0, 12))

        # Nav Items List
        self.nav_items_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_items_frame.pack(fill="both", expand=True, padx=10)

        nav_definitions = [
            ("dashboard", "📊  Dashboard", "view_dashboard"),
            ("calendar", "📅  Calendar", "view_calendar"),
            ("wizard", "✨  Booking Wizard", "manage_appointments"),
            ("appointments", "📋  Appointments", "manage_appointments"),
            ("customers", "👥  Clients", "manage_customers"),
            ("customer", "👤  Customer", "manage_appointments"),
            ("services", "🏷  Services", "manage_services"),
            ("reports", "📈  Reports & Analytics", "view_reports"),
            ("settings", "⚙  Settings", "manage_settings"),
        ]

        self.nav_buttons = {}
        for key, label, perm in nav_definitions:
            # Check RBAC permission
            if perm and not SessionManager.has_permission(perm):
                continue

            btn = ctk.CTkButton(
                self.nav_items_frame,
                text=label,
                font=FONT_BODY_BOLD,
                height=38,
                corner_radius=8,
                anchor="w",
                fg_color="transparent",
                hover_color=PALETTE["dark"]["card_secondary"],
                text_color=PALETTE["dark"]["text_secondary"],
                command=lambda k=key: self.navigate(k),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[key] = btn

        # Sidebar Bottom Footer
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=12, pady=16)

        # User profile chip
        curr_user = SessionManager.get_current_user()
        if curr_user:
            user_chip = ctk.CTkFrame(bottom_frame, corner_radius=8, fg_color=PALETTE["dark"]["card_bg"])
            user_chip.pack(fill="x", pady=(0, 10))

            u_info = ctk.CTkFrame(user_chip, fg_color="transparent")
            u_info.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(
                u_info,
                text=curr_user.full_name,
                font=FONT_BODY_BOLD,
                text_color=PALETTE["dark"]["text_primary"],
                anchor="w",
            ).pack(fill="x")

            ctk.CTkLabel(
                u_info,
                text=f"Role: {curr_user.role.upper()}",
                font=("Segoe UI", 9, "bold"),
                text_color=PALETTE["dark"]["accent"],
                anchor="w",
            ).pack(fill="x")

        # Color Theme Palette Selector
        palette_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        palette_row.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            palette_row,
            text="Theme",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(side="left")

        from src.ui.theme import (
            get_theme_display_names,
            theme_display_name_from_key,
            get_current_theme_key,
        )

        display_names = get_theme_display_names()
        current_display = theme_display_name_from_key(get_current_theme_key())

        self.palette_menu = ctk.CTkOptionMenu(
            palette_row,
            values=display_names,
            font=FONT_SMALL,
            width=140,
            height=26,
            fg_color=PALETTE["dark"]["card_secondary"],
            button_color=PALETTE["dark"]["accent"],
            button_hover_color=PALETTE["dark"]["accent_hover"],
            dropdown_fg_color=PALETTE["dark"]["card_bg"],
            dropdown_hover_color=PALETTE["dark"]["card_secondary"],
            dropdown_text_color=PALETTE["dark"]["text_primary"],
            command=self.set_theme_palette,
        )
        self.palette_menu.set(current_display)
        self.palette_menu.pack(side="right")

        # Theme toggle
        theme_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        theme_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            theme_row,
            text="Dark Mode",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(side="left")

        self.theme_switch = ctk.CTkSwitch(
            theme_row,
            text="",
            width=40,
            command=self.toggle_theme,
        )
        if self.current_theme == "Dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()
        self.theme_switch.pack(side="right")

        # Sign out button
        ctk.CTkButton(
            bottom_frame,
            text="🚪  Sign Out",
            font=FONT_SMALL_BOLD,
            height=32,
            fg_color=PALETTE["dark"]["card_secondary"],
            hover_color=PALETTE["dark"]["danger"],
            command=self.handle_logout,
        ).pack(fill="x")

    def set_theme_palette(self, theme_key_or_name: str):
        """Change color palette and live refresh the workspace shell."""
        from src.ui.theme import (
            set_active_theme,
            theme_key_from_display_name,
            THEME_PALETTES,
        )
        key = theme_key_from_display_name(theme_key_or_name)
        if not key:
            key = theme_key_or_name if theme_key_or_name in THEME_PALETTES else "emerald"

        set_active_theme(key, persist=True)

        # Refresh entire workspace so all sidebar and canvas elements take new palette
        self.show_workspace()

        from src.ui.components.toast import show_toast
        theme_info = THEME_PALETTES.get(key, {})
        t_name = theme_info.get("name", key.capitalize())
        show_toast(self, f"Color theme switched to {t_name}! ✨", level="success")

    def toggle_theme(self):
        """Toggle between Dark and Light CustomTkinter modes."""
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.current_theme = "Dark"
        else:
            ctk.set_appearance_mode("Light")
            self.current_theme = "Light"
        mode = "dark" if self.current_theme == "Dark" else "light"
        self.main_container.configure(fg_color=PALETTE[mode]["bg_primary"])
        if hasattr(self, "content_canvas") and self.content_canvas.winfo_exists():
            self.content_canvas.configure(fg_color=PALETTE[mode]["bg_primary"])
            self.navigate(self.active_nav_key)

    def handle_logout(self):
        """Clear session and return to login view."""
        SessionManager.clear_session()
        self.show_login()

    def navigate(self, key: str):
        """Switch active view."""
        self.active_nav_key = key

        # Update button highlights
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=PALETTE["dark"]["accent"],
                    text_color="#FFFFFF",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=PALETTE["dark"]["text_secondary"],
                )

        # Clear canvas
        for w in self.content_canvas.winfo_children():
            w.destroy()

        # Render chosen view
        if key == "dashboard":
            view = DashboardView(self.content_canvas, on_navigate=self.navigate)
        elif key == "calendar":
            view = CalendarView(self.content_canvas, on_navigate_wizard=lambda: self.navigate("wizard"))
        elif key == "wizard":
            view = BookingWizardView(self.content_canvas, on_booking_complete=lambda ref: self.navigate("appointments"))
        elif key == "appointments":
            view = AppointmentsView(self.content_canvas, on_navigate_wizard=lambda: self.navigate("wizard"))
        elif key == "customers":
            view = CustomersView(self.content_canvas)
        elif key in ("customer", "staff"):
            view = CustomerBookingView(self.content_canvas, on_navigate=self.navigate)
        elif key == "staff_admin":
            view = StaffView(self.content_canvas)
        elif key == "services":
            view = ServicesView(self.content_canvas)
        elif key == "reports":
            view = ReportsView(self.content_canvas)
        elif key == "settings":
            view = SettingsView(self.content_canvas)
        else:
            view = DashboardView(self.content_canvas, on_navigate=self.navigate)

        view.pack(fill="both", expand=True)


def launch():
    """Application launcher."""
    app = BookEaseApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
