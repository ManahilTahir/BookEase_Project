"""Services Management View with Durations, Buffer Times, and Pricing."""

from typing import Optional
import customtkinter as ctk

from src.ui.theme import (
    PALETTE,
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_HEADING,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_SMALL,
    FONT_SMALL_BOLD,
)
from src.ui.components.toast import show_toast
from src.database.connection import get_db
from src.database.models import Service, BusinessSetting


class ServicesView(ctk.CTkFrame):
    """Services catalog management with category grouping and pricing."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.selected_category = "All"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header
        self.create_header()

        # 2. Category Filter Chips
        self.create_category_bar()

        # 3. Services Grid Feed
        self.services_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.services_scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.refresh_services()

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Service Packages & Pricing",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Configure service durations, turnaround buffers, and treatment pricing",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="➕ Add New Service",
            width=150,
            height=36,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            hover_color=PALETTE["dark"]["accent_hover"],
            command=self.open_add_service_modal,
        ).pack(side="right")

    def create_category_bar(self):
        self.cat_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.cat_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))

    def refresh_services(self):
        # Refresh category chips
        for w in self.cat_bar.winfo_children():
            w.destroy()

        # Refresh cards
        for w in self.services_scroll.winfo_children():
            w.destroy()

        with get_db() as session:
            services = session.query(Service).order_by(Service.category.asc(), Service.name.asc()).all()
            
            cur_sym = "$"
            cur_setting = session.query(BusinessSetting).filter(BusinessSetting.key == "currency_symbol").first()
            if cur_setting:
                cur_sym = cur_setting.value

            categories = ["All"] + sorted(list({s.category for s in services}))

            for cat in categories:
                is_active = (cat == self.selected_category)
                btn = ctk.CTkButton(
                    self.cat_bar,
                    text=cat,
                    font=FONT_SMALL_BOLD,
                    height=30,
                    width=90,
                    fg_color=PALETTE["dark"]["accent"] if is_active else PALETTE["dark"]["card_bg"],
                    hover_color=PALETTE["dark"]["accent_hover"],
                    command=lambda c=cat: self.filter_category(c),
                )
                btn.pack(side="left", padx=4)

            # Filter services
            display_services = [s for s in services if (self.selected_category == "All" or s.category == self.selected_category)]

            if not display_services:
                ctk.CTkLabel(self.services_scroll, text="No services in this category.", font=FONT_BODY, text_color=PALETTE["dark"]["text_secondary"]).pack(pady=40)
                return

            for srv in display_services:
                card = ctk.CTkFrame(
                    self.services_scroll,
                    corner_radius=8,
                    fg_color=PALETTE["dark"]["bg_primary"],
                    border_width=1,
                    border_color=PALETTE["dark"]["border"],
                )
                card.pack(fill="x", padx=16, pady=5)

                left_info = ctk.CTkFrame(card, fg_color="transparent")
                left_info.pack(side="left", fill="both", expand=True, padx=16, pady=12)

                top_line = ctk.CTkFrame(left_info, fg_color="transparent")
                top_line.pack(fill="x")

                ctk.CTkLabel(top_line, text=srv.name, font=FONT_BODY_BOLD, text_color=PALETTE["dark"]["text_primary"]).pack(side="left")
                ctk.CTkLabel(top_line, text=srv.category.upper(), font=("Segoe UI", 9, "bold"), fg_color=PALETTE["dark"]["card_secondary"], text_color=PALETTE["dark"]["accent"], corner_radius=4, height=20, width=90).pack(side="left", padx=10)

                ctk.CTkLabel(
                    left_info,
                    text=f"⏱ {srv.duration_minutes} minutes  •  Buffer: +{srv.buffer_minutes}m  •  {srv.description or 'No description provided.'}",
                    font=FONT_SMALL,
                    text_color=PALETTE["dark"]["text_secondary"],
                    anchor="w",
                ).pack(fill="x", pady=(4, 0))

                # Price and actions
                right_box = ctk.CTkFrame(card, fg_color="transparent")
                right_box.pack(side="right", padx=16, pady=12)

                ctk.CTkLabel(right_box, text=f"{cur_sym}{srv.price:.2f}", font=FONT_SUBTITLE, text_color=PALETTE["dark"]["success"]).pack(side="left", padx=16)

                ctk.CTkButton(
                    right_box,
                    text="✏ Edit",
                    width=75,
                    height=30,
                    font=FONT_SMALL_BOLD,
                    fg_color=PALETTE["dark"]["card_secondary"],
                    command=lambda s_id=srv.id: self.open_edit_service_modal(s_id),
                ).pack(side="left", padx=4)

    def filter_category(self, cat: str):
        self.selected_category = cat
        self.refresh_services()

    def open_add_service_modal(self):
        diag = ctk.CTkToplevel(self.winfo_toplevel())
        diag.title("Add New Service")
        diag.geometry("450x420")
        diag.resizable(False, False)
        diag.transient(self.winfo_toplevel())
        diag.grab_set()
        diag.configure(fg_color=PALETTE["dark"]["card_bg"])

        ctk.CTkLabel(diag, text="New Service Package", font=FONT_HEADING).pack(anchor="w", padx=24, pady=(20, 14))

        ctk.CTkLabel(diag, text="Service Name *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        name_ent = ctk.CTkEntry(diag, height=36)
        name_ent.pack(fill="x", padx=24, pady=(2, 8))

        ctk.CTkLabel(diag, text="Category *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        cat_ent = ctk.CTkEntry(diag, height=36)
        cat_ent.insert(0, "General")
        cat_ent.pack(fill="x", padx=24, pady=(2, 8))

        # Duration & Buffer row
        num_row = ctk.CTkFrame(diag, fg_color="transparent")
        num_row.pack(fill="x", padx=24, pady=(0, 8))
        num_row.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(num_row, text="Duration (min) *", font=FONT_SMALL_BOLD).grid(row=0, column=0, sticky="w")
        dur_ent = ctk.CTkEntry(num_row, height=36)
        dur_ent.insert(0, "60")
        dur_ent.grid(row=1, column=0, padx=(0, 4), sticky="ew")

        ctk.CTkLabel(num_row, text="Buffer (min)", font=FONT_SMALL_BOLD).grid(row=0, column=1, sticky="w")
        buf_ent = ctk.CTkEntry(num_row, height=36)
        buf_ent.insert(0, "15")
        buf_ent.grid(row=1, column=1, padx=4, sticky="ew")

        ctk.CTkLabel(num_row, text="Price ($) *", font=FONT_SMALL_BOLD).grid(row=0, column=2, sticky="w")
        price_ent = ctk.CTkEntry(num_row, height=36)
        price_ent.insert(0, "100.00")
        price_ent.grid(row=1, column=2, padx=(4, 0), sticky="ew")

        ctk.CTkLabel(diag, text="Description", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        desc_ent = ctk.CTkEntry(diag, height=36)
        desc_ent.pack(fill="x", padx=24, pady=(2, 20))

        def submit():
            nm = name_ent.get().strip()
            ct = cat_ent.get().strip() or "General"
            dur = int(dur_ent.get().strip() or "60")
            buf = int(buf_ent.get().strip() or "15")
            pr = float(price_ent.get().strip() or "0")
            ds = desc_ent.get().strip()

            if not nm:
                show_toast(diag, "Service Name is required.", level="warning")
                return

            with get_db() as s:
                srv = Service(name=nm, category=ct, duration_minutes=dur, buffer_minutes=buf, price=pr, description=ds)
                s.add(srv)

            diag.destroy()
            show_toast(self.winfo_toplevel(), "Service added to catalog!", level="success")
            self.refresh_services()

        btn_box = ctk.CTkFrame(diag, fg_color="transparent")
        btn_box.pack(fill="x", padx=24)
        ctk.CTkButton(btn_box, text="Cancel", width=100, height=36, fg_color=PALETTE["dark"]["card_secondary"], command=diag.destroy).pack(side="left")
        ctk.CTkButton(btn_box, text="Save Service", width=140, height=36, fg_color=PALETTE["dark"]["accent"], command=submit).pack(side="right")

    def open_edit_service_modal(self, service_id: int):
        with get_db() as session:
            srv = session.query(Service).filter(Service.id == service_id).first()
            if not srv:
                return

            diag = ctk.CTkToplevel(self.winfo_toplevel())
            diag.title("Edit Service Package")
            diag.geometry("450x420")
            diag.resizable(False, False)
            diag.transient(self.winfo_toplevel())
            diag.grab_set()
            diag.configure(fg_color=PALETTE["dark"]["card_bg"])

            ctk.CTkLabel(diag, text=f"Edit {srv.name}", font=FONT_HEADING).pack(anchor="w", padx=24, pady=(20, 14))

            ctk.CTkLabel(diag, text="Service Name *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            name_ent = ctk.CTkEntry(diag, height=36)
            name_ent.insert(0, srv.name)
            name_ent.pack(fill="x", padx=24, pady=(2, 8))

            ctk.CTkLabel(diag, text="Category *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            cat_ent = ctk.CTkEntry(diag, height=36)
            cat_ent.insert(0, srv.category)
            cat_ent.pack(fill="x", padx=24, pady=(2, 8))

            # Duration & Buffer row
            num_row = ctk.CTkFrame(diag, fg_color="transparent")
            num_row.pack(fill="x", padx=24, pady=(0, 8))
            num_row.grid_columnconfigure((0, 1, 2), weight=1)

            ctk.CTkLabel(num_row, text="Duration (min) *", font=FONT_SMALL_BOLD).grid(row=0, column=0, sticky="w")
            dur_ent = ctk.CTkEntry(num_row, height=36)
            dur_ent.insert(0, str(srv.duration_minutes))
            dur_ent.grid(row=1, column=0, padx=(0, 4), sticky="ew")

            ctk.CTkLabel(num_row, text="Buffer (min)", font=FONT_SMALL_BOLD).grid(row=0, column=1, sticky="w")
            buf_ent = ctk.CTkEntry(num_row, height=36)
            buf_ent.insert(0, str(srv.buffer_minutes))
            buf_ent.grid(row=1, column=1, padx=4, sticky="ew")

            ctk.CTkLabel(num_row, text="Price ($) *", font=FONT_SMALL_BOLD).grid(row=0, column=2, sticky="w")
            price_ent = ctk.CTkEntry(num_row, height=36)
            price_ent.insert(0, f"{srv.price:.2f}")
            price_ent.grid(row=1, column=2, padx=(4, 0), sticky="ew")

            ctk.CTkLabel(diag, text="Description", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            desc_ent = ctk.CTkEntry(diag, height=36)
            desc_ent.insert(0, srv.description or "")
            desc_ent.pack(fill="x", padx=24, pady=(2, 20))

            def submit():
                with get_db() as s:
                    t = s.query(Service).filter(Service.id == service_id).first()
                    t.name = name_ent.get().strip()
                    t.category = cat_ent.get().strip()
                    t.duration_minutes = int(dur_ent.get().strip() or "60")
                    t.buffer_minutes = int(buf_ent.get().strip() or "15")
                    t.price = float(price_ent.get().strip() or "0")
                    t.description = desc_ent.get().strip()

                diag.destroy()
                show_toast(self.winfo_toplevel(), "Service updated!", level="success")
                self.refresh_services()

            btn_box = ctk.CTkFrame(diag, fg_color="transparent")
            btn_box.pack(fill="x", padx=24)
            ctk.CTkButton(btn_box, text="Cancel", width=100, height=36, fg_color=PALETTE["dark"]["card_secondary"], command=diag.destroy).pack(side="left")
            ctk.CTkButton(btn_box, text="Save Changes", width=140, height=36, fg_color=PALETTE["dark"]["accent"], command=submit).pack(side="right")
