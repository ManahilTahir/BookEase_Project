"""Modern Login View with Quick Demo Role Badges."""

from typing import Callable
import customtkinter as ctk
from src.ui.theme import (
    PALETTE,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_SMALL_BOLD,
)
from src.database.connection import get_db
from src.database.models import User
from src.core.security import verify_password, SessionManager
from src.core.audit_logger import AuditLogger


class LoginView(ctk.CTkFrame):
    """Sleek authentication card view."""

    def __init__(self, master, on_login_success: Callable[[], None], **kwargs):
        super().__init__(master, fg_color=PALETTE["dark"]["bg_primary"], **kwargs)
        self.on_login_success = on_login_success

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Center Container
        center_frame = ctk.CTkFrame(
            self,
            width=480,
            corner_radius=16,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Header Block
        logo_lbl = ctk.CTkLabel(
            center_frame,
            text="✨",
            font=("Segoe UI", 36),
            text_color=PALETTE["dark"]["accent"],
        )
        logo_lbl.pack(pady=(28, 4))

        brand_lbl = ctk.CTkLabel(
            center_frame,
            text="BookEase",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        )
        brand_lbl.pack(pady=(0, 2))

        sub_lbl = ctk.CTkLabel(
            center_frame,
            text="Professional Universal Booking Agent",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        )
        sub_lbl.pack(pady=(0, 20))

        # Input Form
        form_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=36, pady=0)

        # Username
        ctk.CTkLabel(
            form_frame,
            text="Username or Email",
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w", pady=(0, 4))

        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter username",
            height=40,
            font=FONT_BODY,
            fg_color=PALETTE["dark"]["bg_primary"],
            border_color=PALETTE["dark"]["border"],
        )
        self.username_entry.pack(fill="x", pady=(0, 14))

        # Password
        ctk.CTkLabel(
            form_frame,
            text="Password",
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w", pady=(0, 4))

        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter password",
            show="•",
            height=40,
            font=FONT_BODY,
            fg_color=PALETTE["dark"]["bg_primary"],
            border_color=PALETTE["dark"]["border"],
        )
        self.password_entry.pack(fill="x", pady=(0, 8))
        self.password_entry.bind("<Return>", lambda e: self.attempt_login())

        # Error Banner
        self.error_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["danger"],
        )
        self.error_label.pack(fill="x", pady=(0, 8))

        # Sign In Button
        self.login_btn = ctk.CTkButton(
            form_frame,
            text="Sign In to Workspace",
            height=44,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            hover_color=PALETTE["dark"]["accent_hover"],
            command=self.attempt_login,
        )
        self.login_btn.pack(fill="x", pady=(0, 20))

        # Quick Role Demonstration Fillers
        demo_frame = ctk.CTkFrame(center_frame, fg_color=PALETTE["dark"]["card_secondary"], corner_radius=10)
        demo_frame.pack(fill="x", padx=36, pady=(0, 28))

        ctk.CTkLabel(
            demo_frame,
            text="QUICK LOGIN FOR DEMO / EVALUATION",
            font=("Segoe UI", 9, "bold"),
            text_color=PALETTE["dark"]["text_muted"],
        ).pack(pady=(10, 6))

        pills_frame = ctk.CTkFrame(demo_frame, fg_color="transparent")
        pills_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            pills_frame,
            text="👑 Admin",
            font=FONT_SMALL_BOLD,
            height=28,
            width=100,
            fg_color=PALETTE["dark"]["border"],
            hover_color=PALETTE["dark"]["accent"],
            command=lambda: self.quick_fill("admin", "admin123"),
        ).pack(side="left", expand=True, padx=2)

        ctk.CTkButton(
            pills_frame,
            text="🏢 Owner",
            font=FONT_SMALL_BOLD,
            height=28,
            width=100,
            fg_color=PALETTE["dark"]["border"],
            hover_color=PALETTE["dark"]["purple"],
            command=lambda: self.quick_fill("eleanor", "owner123"),
        ).pack(side="left", expand=True, padx=2)

        ctk.CTkButton(
            pills_frame,
            text="🩺 Staff",
            font=FONT_SMALL_BOLD,
            height=28,
            width=100,
            fg_color=PALETTE["dark"]["border"],
            hover_color=PALETTE["dark"]["success"],
            command=lambda: self.quick_fill("marcus", "staff123"),
        ).pack(side="left", expand=True, padx=2)

        # Pre-fill admin by default for convenience
        self.quick_fill("admin", "admin123")

    def quick_fill(self, username: str, passw: str):
        """Helper to quickly populate demo credentials."""
        self.username_entry.delete(0, "end")
        self.username_entry.insert(0, username)
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, passw)
        self.error_label.configure(text="")

    def attempt_login(self):
        """Validate credentials against database."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.error_label.configure(text="Please enter both username and password.")
            return

        with get_db() as session:
            user = (
                session.query(User)
                .filter(
                    (User.username == username) | (User.email == username),
                    User.is_active == True,
                )
                .first()
            )

            if not user or not verify_password(password, user.password_hash):
                self.error_label.configure(text="Invalid username or password.")
                return

            # Set session
            SessionManager.set_current_user(user)

            # Log audit
            AuditLogger.log(
                session,
                action="USER_LOGIN",
                entity_type="User",
                entity_id=str(user.id),
                details=f"User {user.username} logged in successfully.",
            )

        self.error_label.configure(text="")
        if self.on_login_success:
            self.on_login_success()
