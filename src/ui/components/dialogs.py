"""Modal Dialogs for Confirmations, Prompts, and Details."""

from typing import Callable, Optional
import customtkinter as ctk
from src.ui.theme import PALETTE, FONT_SUBTITLE, FONT_BODY, FONT_BODY_BOLD


class ConfirmDialog(ctk.CTkToplevel):
    """Modern confirmation dialog."""

    def __init__(
        self,
        master,
        title: str,
        message: str,
        on_confirm: Callable[[], None],
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        is_destructive: bool = False,
    ):
        super().__init__(master)
        self.title(title)
        self.geometry("440x220")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.on_confirm = on_confirm
        self.configure(fg_color=PALETTE["dark"]["card_bg"])

        # Header
        header = ctk.CTkLabel(
            self,
            text=title,
            font=FONT_SUBTITLE,
            text_color=PALETTE["dark"]["danger"] if is_destructive else PALETTE["dark"]["text_primary"],
        )
        header.pack(pady=(24, 12), padx=24, anchor="w")

        # Message
        body = ctk.CTkLabel(
            self,
            text=message,
            font=FONT_BODY,
            text_color=PALETTE["dark"]["text_secondary"],
            wraplength=390,
            justify="left",
        )
        body.pack(pady=(0, 24), padx=24, anchor="w")

        # Actions
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            width=110,
            height=36,
            fg_color=PALETTE["dark"]["card_secondary"],
            hover_color=PALETTE["dark"]["border"],
            text_color=PALETTE["dark"]["text_primary"],
            command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            width=120,
            height=36,
            fg_color=PALETTE["dark"]["danger"] if is_destructive else PALETTE["dark"]["accent"],
            hover_color=PALETTE["dark"]["danger_hover"] if is_destructive else PALETTE["dark"]["accent_hover"],
            command=self._handle_confirm,
        )
        confirm_btn.pack(side="right")

        self.center_window()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 440) // 2
        y = (self.winfo_screenheight() - 220) // 2
        self.geometry(f"+{x}+{y}")

    def _handle_confirm(self):
        self.destroy()
        if self.on_confirm:
            self.on_confirm()


class PromptDialog(ctk.CTkToplevel):
    """Single input prompt dialog."""

    def __init__(
        self,
        master,
        title: str,
        prompt_label: str,
        on_submit: Callable[[str], None],
        default_value: str = "",
        submit_text: str = "Submit",
    ):
        super().__init__(master)
        self.title(title)
        self.geometry("450x240")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.on_submit = on_submit
        self.configure(fg_color=PALETTE["dark"]["card_bg"])

        ctk.CTkLabel(self, text=title, font=FONT_SUBTITLE).pack(pady=(20, 8), padx=24, anchor="w")
        ctk.CTkLabel(
            self,
            text=prompt_label,
            font=FONT_BODY,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(pady=(0, 8), padx=24, anchor="w")

        self.entry = ctk.CTkEntry(
            self,
            height=38,
            font=FONT_BODY,
            fg_color=PALETTE["dark"]["bg_primary"],
            border_color=PALETTE["dark"]["border"],
        )
        self.entry.pack(fill="x", padx=24, pady=(0, 20))
        if default_value:
            self.entry.insert(0, default_value)
        self.entry.focus()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            height=36,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame,
            text=submit_text,
            width=110,
            height=36,
            fg_color=PALETTE["dark"]["accent"],
            command=self._handle_submit,
        ).pack(side="right")

        self.center_window()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 450) // 2
        y = (self.winfo_screenheight() - 240) // 2
        self.geometry(f"+{x}+{y}")

    def _handle_submit(self):
        val = self.entry.get().strip()
        self.destroy()
        if self.on_submit:
            self.on_submit(val)
