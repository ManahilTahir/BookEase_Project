import customtkinter as ctk
from src.ui.theme import PALETTE, FONT_METRIC, FONT_BODY, FONT_SMALL_BOLD, FONT_SMALL


class StatCard(ctk.CTkFrame):
    """Sleek metric summary card with icon, metric value, and label."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtext: str = "",
        icon: str = "📊",
        accent_color: str = "#0DA58E",
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

        # Top row: icon
        icon_frame = ctk.CTkFrame(self, fg_color="transparent")
        icon_frame.pack(fill="x", padx=18, pady=(16, 6))

        self.icon_lbl = ctk.CTkLabel(
            icon_frame,
            text=icon,
            font=("Segoe UI", 18),
            text_color=accent_color,
            anchor="w",
        )
        self.icon_lbl.pack(side="left")

        # Metric Value (e.g. "24", "08", "16")
        self.val_lbl = ctk.CTkLabel(
            self,
            text=value,
            font=("Segoe UI", 28, "bold"),
            text_color=PALETTE["dark"]["text_primary"],
            anchor="w",
        )
        self.val_lbl.pack(fill="x", padx=18, pady=(0, 2))

        # Title / Label (e.g. "Bookings", "Pending", "Confirmed")
        self.title_lbl = ctk.CTkLabel(
            self,
            text=title,
            font=FONT_BODY,
            text_color=PALETTE["dark"]["text_secondary"],
            anchor="w",
        )
        self.title_lbl.pack(fill="x", padx=18, pady=(0, 4))

        # Optional subtext / badge
        if subtext:
            self.sub_lbl = ctk.CTkLabel(
                self,
                text=subtext,
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_muted"],
                anchor="w",
            )
            self.sub_lbl.pack(fill="x", padx=18, pady=(0, 14))
        else:
            self.sub_lbl = None
            ctk.CTkFrame(self, height=8, fg_color="transparent").pack()

    def update_value(self, new_val: str, new_subtext: str = None):
        """Dynamically update value and subtext."""
        self.val_lbl.configure(text=new_val)
        if new_subtext and self.sub_lbl:
            self.sub_lbl.configure(text=new_subtext)
