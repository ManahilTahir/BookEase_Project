"""Analytics & Reports Export View (PDF, Excel, CSV, Matplotlib Charts)."""

from datetime import date, timedelta, datetime
import os
from typing import Optional
import customtkinter as ctk
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
from src.ui.components.stat_card import StatCard
from src.database.connection import get_db
from src.database.models import Appointment, BusinessSetting
from src.core.booking_service import BookingService
from src.core.reports_service import ReportsService
from src.config import STATUS_CONFIRMED, STATUS_COMPLETED, STATUS_CANCELLED, STATUS_NO_SHOW


class ReportsView(ctk.CTkScrollableFrame):
    """Analytics, charts, and export center."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.start_date = (date.today() - timedelta(days=30)).isoformat()
        self.end_date = (date.today() + timedelta(days=7)).isoformat()

        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        self.create_header()

        # 2. Date Range Filter Bar
        self.create_filter_bar()

        # 3. Stat Cards for Range
        self.create_summary_cards()

        # 4. Action Export Hub
        self.create_export_hub()

        # 5. Charts Row
        self.create_charts_section()

        self.refresh_analytics()

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Reports & Financial Analytics",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Generate executive summaries, charts, PDF reports, and Excel/CSV spreadsheets",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

    def create_filter_bar(self):
        bar = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        bar.pack(fill="x", padx=24, pady=(0, 16))

        # Presets
        presets_box = ctk.CTkFrame(bar, fg_color="transparent")
        presets_box.pack(side="left", padx=14, pady=10)

        ctk.CTkLabel(presets_box, text="Quick Presets:", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(side="left", padx=(0, 6))

        presets = [
            ("Today", 0),
            ("Last 7 Days", 7),
            ("Last 30 Days", 30),
            ("Next 7 Days", -7),
        ]
        for label, delta in presets:
            btn = ctk.CTkButton(
                presets_box,
                text=label,
                font=FONT_SMALL_BOLD,
                width=85,
                height=30,
                fg_color=PALETTE["dark"]["card_secondary"],
                hover_color=PALETTE["dark"]["accent"],
                command=lambda d=delta: self.apply_preset(d),
            )
            btn.pack(side="left", padx=3)

        # Custom inputs
        custom_box = ctk.CTkFrame(bar, fg_color="transparent")
        custom_box.pack(side="right", padx=14, pady=10)

        ctk.CTkLabel(custom_box, text="From:", font=FONT_SMALL).pack(side="left", padx=(0, 2))
        self.start_entry = ctk.CTkEntry(custom_box, width=95, height=30, font=FONT_SMALL)
        self.start_entry.insert(0, self.start_date)
        self.start_entry.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(custom_box, text="To:", font=FONT_SMALL).pack(side="left", padx=(0, 2))
        self.end_entry = ctk.CTkEntry(custom_box, width=95, height=30, font=FONT_SMALL)
        self.end_entry.insert(0, self.end_date)
        self.end_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            custom_box,
            text="Apply ➔",
            width=75,
            height=30,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            command=self.apply_custom_dates,
        ).pack(side="left")

    def apply_preset(self, days_delta: int):
        today = date.today()
        if days_delta == 0:
            self.start_date = today.isoformat()
            self.end_date = today.isoformat()
        elif days_delta > 0:
            self.start_date = (today - timedelta(days=days_delta)).isoformat()
            self.end_date = today.isoformat()
        else:
            self.start_date = today.isoformat()
            self.end_date = (today + timedelta(days=abs(days_delta))).isoformat()

        self.start_entry.delete(0, "end")
        self.start_entry.insert(0, self.start_date)
        self.end_entry.delete(0, "end")
        self.end_entry.insert(0, self.end_date)
        self.refresh_analytics()

    def apply_custom_dates(self):
        self.start_date = self.start_entry.get().strip()
        self.end_date = self.end_entry.get().strip()
        self.refresh_analytics()

    def create_summary_cards(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=24, pady=(0, 16))
        for col in range(4):
            container.grid_columnconfigure(col, weight=1)

        self.card_range_count = StatCard(container, title="Filtered Bookings", value="0", subtext="In selected range", icon="📋", accent_color="#3B82F6")
        self.card_range_count.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.card_range_rev = StatCard(container, title="Gross Revenue", value="$0.00", subtext="Confirmed / Completed", icon="💰", accent_color="#10B981")
        self.card_range_rev.grid(row=0, column=1, padx=8, sticky="ew")

        self.card_range_avg = StatCard(container, title="Average Ticket", value="$0.00", subtext="Per appointment", icon="📈", accent_color="#8B5CF6")
        self.card_range_avg.grid(row=0, column=2, padx=8, sticky="ew")

        self.card_range_cancel = StatCard(container, title="Cancellation Rate", value="0.0%", subtext="Cancelled sessions", icon="⚠", accent_color="#EF4444")
        self.card_range_cancel.grid(row=0, column=3, padx=(8, 0), sticky="ew")

    def create_export_hub(self):
        """Quick Export Buttons Card."""
        hub = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        hub.pack(fill="x", padx=24, pady=(0, 20))

        head = ctk.CTkFrame(hub, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(head, text="One-Click Report Exports", font=FONT_HEADING, text_color=PALETTE["dark"]["text_primary"]).pack(side="left")
        ctk.CTkLabel(head, text="Generates publication-ready documents directly into reports folder", font=FONT_SMALL, text_color=PALETTE["dark"]["text_muted"]).pack(side="right")

        btns_row = ctk.CTkFrame(hub, fg_color="transparent")
        btns_row.pack(fill="x", padx=20, pady=(0, 16))
        btns_row.grid_columnconfigure((0, 1, 2), weight=1)

        # PDF Button
        ctk.CTkButton(
            btns_row,
            text="📄 Generate PDF Report (ReportLab)",
            font=FONT_BODY_BOLD,
            height=42,
            fg_color=PALETTE["dark"]["accent"],
            hover_color=PALETTE["dark"]["accent_hover"],
            command=self.export_pdf_report,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        # Excel Button
        ctk.CTkButton(
            btns_row,
            text="📊 Export Excel Spreadsheet (.xlsx)",
            font=FONT_BODY_BOLD,
            height=42,
            fg_color="#059669",
            hover_color="#047857",
            command=self.export_excel_report,
        ).grid(row=0, column=1, padx=8, sticky="ew")

        # CSV Button
        ctk.CTkButton(
            btns_row,
            text="📋 Export Raw CSV Dataset (.csv)",
            font=FONT_BODY_BOLD,
            height=42,
            fg_color=PALETTE["dark"]["card_secondary"],
            hover_color=PALETTE["dark"]["border"],
            command=self.export_csv_report,
        ).grid(row=0, column=2, padx=(8, 0), sticky="ew")

    def create_charts_section(self):
        """Two charts side by side: Service category breakdown + Staff distribution."""
        self.charts_row = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_row.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.charts_row.grid_columnconfigure((0, 1), weight=1)

        # Left chart wrapper
        self.cat_chart_frame = ctk.CTkFrame(
            self.charts_row,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.cat_chart_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(self.cat_chart_frame, text="Revenue by Service Category", font=FONT_HEADING).pack(anchor="w", padx=16, pady=(14, 8))
        self.cat_canvas_box = ctk.CTkFrame(self.cat_chart_frame, fg_color="transparent")
        self.cat_canvas_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.cat_canvas = None

        # Right chart wrapper
        self.staff_chart_frame = ctk.CTkFrame(
            self.charts_row,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.staff_chart_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(self.staff_chart_frame, text="Specialist Workload Distribution", font=FONT_HEADING).pack(anchor="w", padx=16, pady=(14, 8))
        self.staff_canvas_box = ctk.CTkFrame(self.staff_chart_frame, fg_color="transparent")
        self.staff_canvas_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.staff_canvas = None

    def refresh_analytics(self):
        """Query appointments in range and update cards and charts using Pandas/Matplotlib."""
        with get_db() as session:
            apps = BookingService.get_appointments(
                session=session,
                start_date=self.start_date,
                end_date=self.end_date,
            )

            cur_sym = "$"
            cur_setting = session.query(BusinessSetting).filter(BusinessSetting.key == "currency_symbol").first()
            if cur_setting:
                cur_sym = cur_setting.value

            total_count = len(apps)
            rev_apps = [a for a in apps if a.status in (STATUS_CONFIRMED, STATUS_COMPLETED)]
            total_rev = sum(a.price for a in rev_apps)
            avg_ticket = (total_rev / len(rev_apps)) if rev_apps else 0.0
            cancelled_count = sum(1 for a in apps if a.status == STATUS_CANCELLED)
            cancel_rate = (round((cancelled_count / total_count) * 100, 1)) if total_count > 0 else 0.0

            # Update Cards
            self.card_range_count.update_value(str(total_count), f"{len(rev_apps)} active/completed")
            self.card_range_rev.update_value(f"{cur_sym}{total_rev:,.2f}", "Total earnings in range")
            self.card_range_avg.update_value(f"{cur_sym}{avg_ticket:,.2f}", "Avg price per session")
            self.card_range_cancel.update_value(f"{cancel_rate}%", f"{cancelled_count} cancellations")

            # Render Charts with Pandas & Matplotlib
            self.render_category_chart(apps, cur_sym)
            self.render_staff_chart(apps)

    def render_category_chart(self, apps: list, cur_sym: str):
        if self.cat_canvas:
            self.cat_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(4.5, 2.5), dpi=100, facecolor="#1E293B")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1E293B")

        if not apps:
            ax.text(0.5, 0.5, "No data in range", ha="center", va="center", color="#94A3B8")
            ax.axis("off")
        else:
            # Pandas aggregation
            data = [{"Category": a.service.category if a.service else "Other", "Price": a.price} for a in apps]
            df = pd.DataFrame(data)
            cat_totals = df.groupby("Category")["Price"].sum().sort_values(ascending=True)

            categories = list(cat_totals.index)
            totals = list(cat_totals.values)

            bars = ax.barh(categories, totals, color="#8B5CF6", edgecolor="#A78BFA", height=0.5)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#475569")
            ax.spines["bottom"].set_color("#475569")
            ax.tick_params(colors="#94A3B8", labelsize=8)
            ax.grid(axis="x", color="#334155", linestyle="--", linewidth=0.7, alpha=0.6)

        fig.tight_layout()
        self.cat_canvas = FigureCanvasTkAgg(fig, master=self.cat_canvas_box)
        self.cat_canvas.draw()
        self.cat_canvas.get_tk_widget().pack(fill="both", expand=True)

    def render_staff_chart(self, apps: list):
        if self.staff_canvas:
            self.staff_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(4.5, 2.5), dpi=100, facecolor="#1E293B")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1E293B")

        if not apps:
            ax.text(0.5, 0.5, "No data in range", ha="center", va="center", color="#94A3B8")
            ax.axis("off")
        else:
            data = [{"Staff": a.staff.name if a.staff else "Other"} for a in apps]
            df = pd.DataFrame(data)
            counts = df["Staff"].value_counts()

            # Donut chart
            colors_palette = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899"]
            wedges, texts, autotexts = ax.pie(
                counts.values,
                labels=counts.index,
                autopct="%1.0f%%",
                startangle=140,
                colors=colors_palette[:len(counts)],
                wedgeprops=dict(width=0.45, edgecolor="#1E293B"),
                textprops=dict(color="#F8FAFC", fontsize=8),
            )
            for at in autotexts:
                at.set_color("#FFFFFF")
                at.set_weight("bold")

        fig.tight_layout()
        self.staff_canvas = FigureCanvasTkAgg(fig, master=self.staff_canvas_box)
        self.staff_canvas.draw()
        self.staff_canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_pdf_report(self):
        with get_db() as session:
            apps = BookingService.get_appointments(
                session=session,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            if not apps:
                show_toast(self.winfo_toplevel(), "No bookings in range to export.", level="warning")
                return

            out = ReportsService.export_appointments_pdf(
                session, apps, report_title=f"Performance Summary ({self.start_date} to {self.end_date})"
            )
            show_toast(self.winfo_toplevel(), f"PDF Report saved to {out.name}!", level="success")
            os.startfile(str(out))

    def export_excel_report(self):
        with get_db() as session:
            apps = BookingService.get_appointments(
                session=session,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            out = ReportsService.export_appointments_excel(session, apps)
            show_toast(self.winfo_toplevel(), f"Excel Report saved to {out.name}!", level="success")
            os.startfile(str(out))

    def export_csv_report(self):
        with get_db() as session:
            apps = BookingService.get_appointments(
                session=session,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            out = ReportsService.export_appointments_csv(apps)
            show_toast(self.winfo_toplevel(), f"CSV Export saved to {out.name}!", level="success")
            os.startfile(str(out))
