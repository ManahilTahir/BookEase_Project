"""Toast Notification Banners for Feedback Messages."""

import customtkinter as ctk
from src.ui.theme import PALETTE, FONT_BODY_BOLD, FONT_SMALL


class ToastNotification(ctk.CTkFrame):
    """Temporary notification banner that appears at the top of the window."""

    def __init__(
        self,
        master,
        message: str,
        level: str = "success",  # 'success', 'error', 'info', 'warning'
        duration_ms: int = 3500,
        **kwargs,
    ):
        colors_map = {
            "success": (PALETTE["dark"]["success"], "✔"),
            "error": (PALETTE["dark"]["danger"], "✖"),
            "warning": (PALETTE["dark"]["warning"], "⚠"),
            "info": (PALETTE["dark"]["accent"], "ℹ"),
        }
        accent_color, icon_char = colors_map.get(level, (PALETTE["dark"]["accent"], "ℹ"))

        super().__init__(
            master,
            corner_radius=10,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=2,
            border_color=accent_color,
            **kwargs,
        )

        self.duration_ms = duration_ms

        # Content Layout
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="x", padx=14, pady=10)

        # Icon
        icon_lbl = ctk.CTkLabel(
            content_frame,
            text=icon_char,
            font=("Segoe UI", 14, "bold"),
            text_color=accent_color,
            width=24,
        )
        icon_lbl.pack(side="left", padx=(0, 10))

        # Message
        msg_lbl = ctk.CTkLabel(
            content_frame,
            text=message,
            font=FONT_BODY_BOLD,
            text_color=PALETTE["dark"]["text_primary"],
            wraplength=500,
            justify="left",
        )
        msg_lbl.pack(side="left", fill="x", expand=True)

        # Close button
        close_btn = ctk.CTkButton(
            content_frame,
            text="✕",
            width=24,
            height=24,
            font=("Segoe UI", 10, "bold"),
            fg_color="transparent",
            hover_color=PALETTE["dark"]["card_secondary"],
            text_color=PALETTE["dark"]["text_secondary"],
            command=self.dismiss,
        )
        close_btn.pack(side="right", padx=(8, 0))

        # Position toast at top-center of master
        self.place(relx=0.5, y=20, anchor="n")
        self.lift()

        # Schedule auto-dismiss
        if self.duration_ms > 0:
            self.after(self.duration_ms, self.dismiss)

    def dismiss(self):
        """Fade out and destroy toast."""
        try:
            self.destroy()
        except Exception:
            pass


def show_toast(master, message: str, level: str = "success", duration_ms: int = 3500):
    """Convenience helper to show a toast message."""
    return ToastNotification(master=master, message=message, level=level, duration_ms=duration_ms)
