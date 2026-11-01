"""Dual-axis (Horizontal & Vertical) Scrollable Frame for CustomTkinter."""

import sys
import tkinter as tk
from typing import Optional
import customtkinter as ctk

from src.ui.theme import PALETTE


class DualScrollFrame(ctk.CTkFrame):
    """
    A robust scrollable container with BOTH vertical and interactive horizontal scrollbars.
    Exposes `self.inner_frame` where children widgets should be packed/gridded.
    Maintains perfect visual alignment with CustomTkinter cards.
    """

    def __init__(
        self,
        master,
        min_content_width: int = 1100,
        fg_color: Optional[str] = None,
        corner_radius: int = 12,
        border_width: int = 1,
        border_color: Optional[str] = None,
        show_h_scrollbar: bool = True,
        show_v_scrollbar: bool = True,
        **kwargs,
    ):
        card_bg = fg_color or PALETTE["dark"]["card_bg"]
        b_color = border_color or PALETTE["dark"]["border"]

        super().__init__(
            master,
            corner_radius=corner_radius,
            fg_color=card_bg,
            border_width=border_width,
            border_color=b_color,
            **kwargs,
        )

        self.min_content_width = min_content_width
        self.show_h_scrollbar = show_h_scrollbar
        self.show_v_scrollbar = show_v_scrollbar

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Underlying Tkinter Canvas
        self.canvas = tk.Canvas(
            self,
            bd=0,
            highlightthickness=0,
            bg=card_bg,
            relief="flat",
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=(border_width, 0), pady=(border_width, 0))

        # Vertical Scrollbar
        if self.show_v_scrollbar:
            self.v_scroller = ctk.CTkScrollbar(
                self,
                orientation="vertical",
                width=12,
                command=self.canvas.yview,
                fg_color="transparent",
                button_color=PALETTE["dark"]["card_secondary"],
                button_hover_color=PALETTE["dark"]["accent"],
            )
            self.v_scroller.grid(row=0, column=1, sticky="ns", padx=(2, 6), pady=6)
            self.canvas.configure(yscrollcommand=self.v_scroller.set)
        else:
            self.v_scroller = None

        # Horizontal Scroller
        if self.show_h_scrollbar:
            self.h_scroller = ctk.CTkScrollbar(
                self,
                orientation="horizontal",
                height=14,
                command=self.canvas.xview,
                fg_color="transparent",
                button_color=PALETTE["dark"]["card_secondary"],
                button_hover_color=PALETTE["dark"]["accent"],
            )
            self.h_scroller.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 8))
            self.canvas.configure(xscrollcommand=self.h_scroller.set)
        else:
            self.h_scroller = None

        # Inner Content Frame where all child widgets live
        self.inner_frame = ctk.CTkFrame(
            self.canvas,
            fg_color=card_bg,
            corner_radius=0,
        )
        self._window_id = self.canvas.create_window(
            (0, 0),
            window=self.inner_frame,
            anchor="nw",
        )

        # Event bindings
        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self._bind_mouse_wheel(self.canvas)
        self._bind_mouse_wheel(self.inner_frame)

    def _on_frame_configure(self, event=None):
        """Update scroll region to encompass inner content."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Expand frame width to canvas width if canvas is wider than min_content_width."""
        canvas_width = event.width
        target_width = max(canvas_width, self.min_content_width)
        self.canvas.itemconfigure(self._window_id, width=target_width)

    def _bind_mouse_wheel(self, widget):
        """Recursively bind mouse wheel and shift+wheel for horizontal scroll."""
        widget.bind("<MouseWheel>", self._on_mouse_wheel, add="+")
        widget.bind("<Shift-MouseWheel>", self._on_shift_mouse_wheel, add="+")

    def bind_child_scroll(self, child_widget):
        """Helper to bind mouse wheel events to dynamically added children."""
        self._bind_mouse_wheel(child_widget)

    def _on_mouse_wheel(self, event):
        """Vertical scroll on Windows."""
        if sys.platform.startswith("win"):
            delta = -int(event.delta / 120)
        else:
            delta = -1 if event.num == 4 else 1
        self.canvas.yview_scroll(delta * 2, "units")

    def _on_shift_mouse_wheel(self, event):
        """Horizontal scroll on Windows using Shift+Wheel."""
        if sys.platform.startswith("win"):
            delta = -int(event.delta / 120)
        else:
            delta = -1 if event.num == 4 else 1
        self.canvas.xview_scroll(delta * 2, "units")

    def reset_view(self):
        """Scroll back to top-left."""
        self.canvas.xview_moveto(0.0)
        self.canvas.yview_moveto(0.0)

    def clear(self):
        """Destroy all widgets inside inner frame and reset scroll."""
        for w in self.inner_frame.winfo_children():
            w.destroy()
        self.reset_view()
