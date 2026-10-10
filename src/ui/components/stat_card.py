"""Modern Metric Stat Card Component for Dashboard."""

import customtkinter as ctk
from src.ui.theme import PALETTE, FONT_METRIC, FONT_SMALL_BOLD, FONT_SMALL


class StatCard(ctk.CTkFrame):
    """Sleek metric summary card with icon badge and trend subtext."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtext: str = "",
        icon: str = "📊",
        accent_color: str = "#3B82F6",
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
            **kwargs,
        )

        self.grid_columnconfigure(0, weight=1)

        # Header Row: Title & Icon Pill
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 6))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text=title.upper(),
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["text_secondary"],
        )
        title_lbl.pack(side="left")

        # Icon pill
        icon_box = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=("Segoe UI", 14),
            width=32,
            height=32,
            corner_radius=8,
            fg_color=PALETTE["dark"]["card_secondary"],
            text_color=accent_color,
        )
        icon_box.pack(side="right")

        # Metric Value
        self.val_lbl = ctk.CTkLabel(
            self,
            text=value,
            font=FONT_METRIC,
            text_color=PALETTE["dark"]["text_primary"],
            anchor="w",
        )
        self.val_lbl.pack(fill="x", padx=16, pady=(0, 4))

        # Subtitle / Trend
        if subtext:
            self.sub_lbl = ctk.CTkLabel(
                self,
                text=subtext,
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_muted"],
                anchor="w",
            )
            self.sub_lbl.pack(fill="x", padx=16, pady=(0, 14))
        else:
            self.sub_lbl = None

    def update_value(self, new_val: str, new_subtext: str = None):
        """Dynamically update value and subtext."""
        self.val_lbl.configure(text=new_val)
        if new_subtext and self.sub_lbl:
            self.sub_lbl.configure(text=new_subtext)
