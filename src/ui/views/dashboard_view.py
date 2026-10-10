"""Modern Interactive Dashboard View with Real Data & Embedded Charts."""

from datetime import date
from typing import Callable, Optional
import customtkinter as ctk
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
from src.ui.components.stat_card import StatCard
from src.ui.components.toast import show_toast
from src.ui.components.dialogs import ConfirmDialog
from src.database.connection import get_db
from src.database.models import Appointment, BusinessSetting
from src.core.booking_service import BookingService
from src.core.reports_service import ReportsService
from src.config import STATUS_CONFIRMED, STATUS_COMPLETED, STATUS_CANCELLED, STATUS_COLORS


class DashboardView(ctk.CTkScrollableFrame):
    """Main executive dashboard with live metrics, charts, and today's schedule."""

    def __init__(
        self,
        master,
        on_navigate: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_navigate = on_navigate

        self.grid_columnconfigure(0, weight=1)

        # 1. Header Row
        self.create_header()

        # 2. Stat Cards Grid
        self.create_stat_cards()

        # 3. Middle Section: Analytics Chart + Quick Actions
        self.create_chart_section()

        # 4. Bottom Section: Today's Schedule Feed
        self.create_today_schedule()

        # Load initial data
        self.refresh_dashboard()

    def create_header(self):
        """Top action bar of dashboard."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(16, 16))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Executive Dashboard",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        today_formatted = date.today().strftime("%A, %B %d, %Y")
        ctk.CTkLabel(
            title_box,
            text=f"Live business overview for {today_formatted}",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        # Refresh
        ctk.CTkButton(
            actions_box,
            text="🔄 Refresh",
            width=100,
            height=36,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            hover_color=PALETTE["dark"]["border"],
            command=self.refresh_dashboard,
        ).pack(side="left", padx=(0, 10))

        # PDF Daily Schedule
        ctk.CTkButton(
            actions_box,
            text="📄 Today's PDF",
            width=120,
            height=36,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            hover_color=PALETTE["dark"]["border"],
            command=self.export_today_pdf,
        ).pack(side="left", padx=(0, 10))

        # New Booking Wizard
        ctk.CTkButton(
            actions_box,
            text="➕ New Booking",
            width=130,
            height=36,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            hover_color=PALETTE["dark"]["accent_hover"],
            command=lambda: self.on_navigate("wizard"),
        ).pack(side="left")

    def create_stat_cards(self):
        """Top 4 metric summary cards."""
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="x", padx=24, pady=(0, 20))
        for col in range(4):
            cards_container.grid_columnconfigure(col, weight=1)

        self.card_today_apps = StatCard(
            cards_container,
            title="Today's Appointments",
            value="0",
            subtext="Active today",
            icon="📅",
            accent_color="#3B82F6",
        )
        self.card_today_apps.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.card_today_rev = StatCard(
            cards_container,
            title="Today's Projected",
            value="$0.00",
            subtext="From active bookings",
            icon="💰",
            accent_color="#10B981",
        )
        self.card_today_rev.grid(row=0, column=1, padx=10, sticky="ew")

        self.card_total_cust = StatCard(
            cards_container,
            title="Total Registered Clients",
            value="0",
            subtext="Profiles in system",
            icon="👥",
            accent_color="#8B5CF6",
        )
        self.card_total_cust.grid(row=0, column=2, padx=10, sticky="ew")

        self.card_comp_rate = StatCard(
            cards_container,
            title="Completion Rate",
            value="100%",
            subtext="Historical reliability",
            icon="⭐",
            accent_color="#F59E0B",
        )
        self.card_comp_rate.grid(row=0, column=3, padx=(10, 0), sticky="ew")

    def create_chart_section(self):
        """Chart row containing 7-day revenue trend."""
        chart_wrapper = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        chart_wrapper.pack(fill="x", padx=24, pady=(0, 20))

        chart_head = ctk.CTkFrame(chart_wrapper, fg_color="transparent")
        chart_head.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            chart_head,
            text="7-Day Revenue & Booking Trajectory",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        # Container for matplotlib canvas
        self.chart_canvas_frame = ctk.CTkFrame(chart_wrapper, fg_color="transparent")
        self.chart_canvas_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.chart_canvas = None

    def create_today_schedule(self):
        """Today's appointments timeline and feed."""
        schedule_wrapper = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        schedule_wrapper.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        head_frame = ctk.CTkFrame(schedule_wrapper, fg_color="transparent")
        head_frame.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(
            head_frame,
            text="Today's Scheduled Clients",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            head_frame,
            text="View Full Calendar ➔",
            font=FONT_SMALL_BOLD,
            height=28,
            fg_color="transparent",
            hover_color=PALETTE["dark"]["card_secondary"],
            text_color=PALETTE["dark"]["accent"],
            command=lambda: self.on_navigate("calendar"),
        ).pack(side="right")

        # Feed list container
        self.schedule_feed = ctk.CTkFrame(schedule_wrapper, fg_color="transparent")
        self.schedule_feed.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def refresh_dashboard(self):
        """Fetch updated data from database and refresh cards, charts, and feed."""
        with get_db() as session:
            metrics = BookingService.get_dashboard_metrics(session)
            
            # Fetch business currency
            cur_sym = "$"
            cur_setting = session.query(BusinessSetting).filter(BusinessSetting.key == "currency_symbol").first()
            if cur_setting:
                cur_sym = cur_setting.value

            # Update Stat Cards
            self.card_today_apps.update_value(str(metrics["today_count"]), f"{metrics['confirmed_count']} pending/confirmed")
            self.card_today_rev.update_value(f"{cur_sym}{metrics['today_revenue']:,.2f}", "Today's scheduled total")
            self.card_total_cust.update_value(str(metrics["total_customers"]), f"{metrics['total_services']} services offered")
            self.card_comp_rate.update_value(f"{metrics['completion_rate']}%", f"{metrics['completed_count']} completed all-time")

            # Update Chart
            self.render_chart(metrics, cur_sym)

            # Update Today's Schedule Feed
            today_str = date.today().isoformat()
            today_apps = BookingService.get_appointments(session, target_date=today_str)
            self.render_schedule_feed(today_apps, cur_sym)

    def render_chart(self, metrics: dict, cur_sym: str):
        """Draw modern Matplotlib bar chart inside canvas frame."""
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(9, 2.8), dpi=100, facecolor="#1E293B")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#1E293B")

        days = metrics["chart_days"]
        revs = metrics["chart_revenues"]
        apps = metrics["chart_appointments"]

        # Bar chart for revenue
        bars = ax.bar(
            days,
            revs,
            width=0.45,
            color="#3B82F6",
            edgecolor="#60A5FA",
            linewidth=1,
            alpha=0.9,
            zorder=3,
        )

        # Styling grid & spines
        ax.grid(axis="y", color="#334155", linestyle="--", linewidth=0.7, alpha=0.7, zorder=0)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#475569")
        ax.spines["bottom"].set_color("#475569")
        ax.tick_params(colors="#94A3B8", labelsize=8)

        # Value annotations on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(
                    f"{cur_sym}{int(height)}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color="#F8FAFC",
                    weight="bold",
                )

        fig.tight_layout()
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_canvas_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    def render_schedule_feed(self, appointments: list, cur_sym: str):
        """Render list of today's appointments or empty state."""
        for widget in self.schedule_feed.winfo_children():
            widget.destroy()

        if not appointments:
            empty_box = ctk.CTkFrame(self.schedule_feed, fg_color="transparent")
            empty_box.pack(pady=30)
            ctk.CTkLabel(
                empty_box,
                text="🎉",
                font=("Segoe UI", 28),
            ).pack()
            ctk.CTkLabel(
                empty_box,
                text="No appointments scheduled for today.",
                font=FONT_BODY_BOLD,
                text_color=PALETTE["dark"]["text_secondary"],
            ).pack(pady=(4, 2))
            ctk.CTkLabel(
                empty_box,
                text="Use the booking assistant to schedule client sessions.",
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_muted"],
            ).pack()
            return

        for app in appointments:
            row = ctk.CTkFrame(
                self.schedule_feed,
                corner_radius=8,
                fg_color=PALETTE["dark"]["bg_primary"],
                border_width=1,
                border_color=PALETTE["dark"]["border"],
            )
            row.pack(fill="x", pady=4, padx=4)

            # Left: Time Badge
            time_pill = ctk.CTkLabel(
                row,
                text=f"{app.start_time}\n{app.end_time}",
                font=FONT_SMALL_BOLD,
                width=65,
                height=38,
                corner_radius=6,
                fg_color=PALETTE["dark"]["card_secondary"],
                text_color=PALETTE["dark"]["text_primary"],
            )
            time_pill.pack(side="left", padx=12, pady=10)

            # Center Info: Client, Service, Specialist
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=6)

            ctk.CTkLabel(
                info_frame,
                text=f"{app.customer.name} • {app.service.name}",
                font=FONT_BODY_BOLD,
                text_color=PALETTE["dark"]["text_primary"],
                anchor="w",
            ).pack(fill="x")

            staff_name = app.staff.name if app.staff else "Unassigned"
            ctk.CTkLabel(
                info_frame,
                text=f"Ref: {app.appointment_number} | Specialist: {staff_name} | {cur_sym}{app.price:.2f}",
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_secondary"],
                anchor="w",
            ).pack(fill="x")

            # Status Badge
            status_color = STATUS_COLORS.get(app.status, PALETTE["dark"]["accent"])
            ctk.CTkLabel(
                row,
                text=app.status.upper(),
                font=FONT_SMALL_BOLD,
                corner_radius=6,
                width=85,
                height=26,
                fg_color=status_color,
                text_color="#FFFFFF",
            ).pack(side="left", padx=10)

            # Action Buttons
            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=12)

            if app.status == STATUS_CONFIRMED:
                ctk.CTkButton(
                    btn_box,
                    text="✔ Complete",
                    width=85,
                    height=28,
                    font=FONT_SMALL_BOLD,
                    fg_color=PALETTE["dark"]["success"],
                    hover_color="#059669",
                    command=lambda a_id=app.id: self.quick_complete(a_id),
                ).pack(side="left", padx=3)

                ctk.CTkButton(
                    btn_box,
                    text="✕ Cancel",
                    width=75,
                    height=28,
                    font=FONT_SMALL_BOLD,
                    fg_color=PALETTE["dark"]["card_secondary"],
                    hover_color=PALETTE["dark"]["danger"],
                    command=lambda a_id=app.id: self.quick_cancel(a_id),
                ).pack(side="left", padx=3)

    def quick_complete(self, appointment_id: int):
        """Mark appointment as completed."""
        with get_db() as session:
            ok, _, err = BookingService.update_status(session, appointment_id, STATUS_COMPLETED)
            if ok:
                show_toast(self.winfo_toplevel(), "Appointment marked as completed!", level="success")
            else:
                show_toast(self.winfo_toplevel(), f"Error: {err}", level="error")
        self.refresh_dashboard()

    def quick_cancel(self, appointment_id: int):
        """Confirm and cancel appointment."""
        def do_cancel():
            with get_db() as session:
                ok, _, err = BookingService.cancel_appointment(session, appointment_id, "Cancelled from dashboard")
                if ok:
                    show_toast(self.winfo_toplevel(), "Appointment cancelled.", level="info")
                else:
                    show_toast(self.winfo_toplevel(), f"Error: {err}", level="error")
            self.refresh_dashboard()

        ConfirmDialog(
            master=self.winfo_toplevel(),
            title="Cancel Appointment",
            message="Are you sure you want to cancel this booking? This will free the slot.",
            on_confirm=do_cancel,
            confirm_text="Yes, Cancel",
            is_destructive=True,
        )

    def export_today_pdf(self):
        """Export today's schedule to PDF."""
        today_str = date.today().isoformat()
        with get_db() as session:
            apps = BookingService.get_appointments(session, target_date=today_str)
            if not apps:
                show_toast(self.winfo_toplevel(), "No appointments today to export.", level="warning")
                return

            out_path = ReportsService.export_appointments_pdf(
                session, apps, report_title=f"Daily Schedule — {date.today().strftime('%B %d, %Y')}"
            )
            show_toast(
                self.winfo_toplevel(),
                f"Exported today's PDF to {out_path.name}!",
                level="success",
            )
            import os
            os.startfile(str(out_path))
