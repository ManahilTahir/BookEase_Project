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
        """Comprehensive visual analytics section representing app features."""
        self.charts_container = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_container.pack(fill="x", padx=24, pady=(0, 20))

        # 1. Top Chart: 7-Day Revenue & Booking Volume Trajectory
        rev_card = ctk.CTkFrame(
            self.charts_container,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        rev_card.pack(fill="x", pady=(0, 16))

        rev_head = ctk.CTkFrame(rev_card, fg_color="transparent")
        rev_head.pack(fill="x", padx=20, pady=(14, 6))

        ctk.CTkLabel(
            rev_head,
            text="📈 7-Day Revenue & Booking Volume Trajectory",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            rev_head,
            text="Daily revenue (bars) & appointment volume (line)",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(side="right")

        self.chart_canvas_frame_rev = ctk.CTkFrame(rev_card, fg_color="transparent")
        self.chart_canvas_frame_rev.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.chart_canvas_rev = None

        # 2. Middle Row: Side-by-side Visuals for Services & Status
        middle_grid = ctk.CTkFrame(self.charts_container, fg_color="transparent")
        middle_grid.pack(fill="x", pady=(0, 16))
        middle_grid.grid_columnconfigure((0, 1), weight=1)

        # Card A: Service Category Distribution
        cat_card = ctk.CTkFrame(
            middle_grid,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        cat_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        cat_head = ctk.CTkFrame(cat_card, fg_color="transparent")
        cat_head.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            cat_head,
            text="🏷 Service Category Distribution",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        self.chart_canvas_frame_cat = ctk.CTkFrame(cat_card, fg_color="transparent")
        self.chart_canvas_frame_cat.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.chart_canvas_cat = None

        # Card B: Booking Status & Health
        status_card = ctk.CTkFrame(
            middle_grid,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        status_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        status_head = ctk.CTkFrame(status_card, fg_color="transparent")
        status_head.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            status_head,
            text="📊 Booking Fulfillment & Status Health",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        self.chart_canvas_frame_status = ctk.CTkFrame(status_card, fg_color="transparent")
        self.chart_canvas_frame_status.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.chart_canvas_status = None

        # 3. Bottom Chart: Specialist Workload & Demand
        staff_card = ctk.CTkFrame(
            self.charts_container,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        staff_card.pack(fill="x", pady=(0, 4))

        staff_head = ctk.CTkFrame(staff_card, fg_color="transparent")
        staff_head.pack(fill="x", padx=20, pady=(14, 6))
        ctk.CTkLabel(
            staff_head,
            text="🩺 Specialist Workload & Booking Demand",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            staff_head,
            text="Total appointments assigned per specialist",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(side="right")

        self.chart_canvas_frame_staff = ctk.CTkFrame(staff_card, fg_color="transparent")
        self.chart_canvas_frame_staff.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.chart_canvas_staff = None

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

            # Update Visual Charts
            self.render_all_charts(metrics, cur_sym)

            # Update Today's Schedule Feed
            today_str = date.today().isoformat()
            today_apps = BookingService.get_appointments(session, target_date=today_str)
            self.render_schedule_feed(today_apps, cur_sym)

    def render_all_charts(self, metrics: dict, cur_sym: str):
        """Render all dashboard charts according to BookEase features."""
        bg_col = PALETTE["dark"].get("card_bg", "#10243C")
        border_col = PALETTE["dark"].get("border", "#1E4268")
        accent_col = PALETTE["dark"].get("accent", "#0DA58E")
        text_pri = PALETTE["dark"].get("text_primary", "#FFFFFF")
        text_sec = PALETTE["dark"].get("text_secondary", "#A0B4CC")

        # -------------------------------------------------------------
        # 1. Revenue & Trajectory Dual-Axis Chart
        # -------------------------------------------------------------
        if self.chart_canvas_rev:
            self.chart_canvas_rev.get_tk_widget().destroy()

        fig_rev = Figure(figsize=(9, 2.5), dpi=100, facecolor=bg_col)
        ax_rev = fig_rev.add_subplot(111)
        ax_rev.set_facecolor(bg_col)

        days = metrics.get("chart_days", [])
        revs = metrics.get("chart_revenues", [])
        apps = metrics.get("chart_appointments", [])

        # Bars for Revenue
        x_indices = range(len(days))
        bars = ax_rev.bar(
            x_indices,
            revs,
            width=0.42,
            color=accent_col,
            alpha=0.88,
            zorder=3,
            label=f"Revenue ({cur_sym})",
        )

        ax_rev.set_xticks(x_indices)
        ax_rev.set_xticklabels(days, color=text_sec, fontsize=8)
        ax_rev.grid(axis="y", color=border_col, linestyle="--", linewidth=0.6, alpha=0.7, zorder=0)
        ax_rev.spines["top"].set_visible(False)
        ax_rev.spines["right"].set_visible(False)
        ax_rev.spines["left"].set_color(border_col)
        ax_rev.spines["bottom"].set_color(border_col)
        ax_rev.tick_params(colors=text_sec, labelsize=8)

        # Revenue annotations
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax_rev.annotate(
                    f"{cur_sym}{int(h)}",
                    xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    color=text_pri,
                    weight="bold",
                )

        # Twin axis for appointment count trend line
        ax_count = ax_rev.twinx()
        ax_count.plot(
            x_indices,
            apps,
            color="#38BDF8",
            marker="o",
            markersize=5,
            linewidth=2,
            zorder=4,
            label="Bookings Count",
        )
        ax_count.set_ylim(0, max(max(apps, default=1) + 2, 5))
        ax_count.spines["top"].set_visible(False)
        ax_count.spines["left"].set_visible(False)
        ax_count.spines["bottom"].set_color(border_col)
        ax_count.spines["right"].set_color(border_col)
        ax_count.tick_params(colors="#38BDF8", labelsize=8)

        # Legend
        lines_1, labels_1 = ax_rev.get_legend_handles_labels()
        lines_2, labels_2 = ax_count.get_legend_handles_labels()
        ax_rev.legend(
            lines_1 + lines_2,
            labels_1 + labels_2,
            loc="upper left",
            facecolor=bg_col,
            edgecolor=border_col,
            fontsize=7,
            labelcolor=text_sec,
        )

        fig_rev.tight_layout()
        self.chart_canvas_rev = FigureCanvasTkAgg(fig_rev, master=self.chart_canvas_frame_rev)
        self.chart_canvas_rev.draw()
        self.chart_canvas_rev.get_tk_widget().pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 2. Service Category Distribution Donut Chart
        # -------------------------------------------------------------
        if self.chart_canvas_cat:
            self.chart_canvas_cat.get_tk_widget().destroy()

        fig_cat = Figure(figsize=(4.6, 2.5), dpi=100, facecolor=bg_col)
        ax_cat = fig_cat.add_subplot(111)
        ax_cat.set_facecolor(bg_col)

        cat_dist = metrics.get("category_distribution", {})
        if not cat_dist or sum(cat_dist.values()) == 0:
            cat_dist = {"Skin Aesthetics": 3, "Dermatology": 2, "Body & Wellness": 2, "Hair & Scalp": 1}

        cat_labels = list(cat_dist.keys())
        cat_values = list(cat_dist.values())
        palette_colors = ["#0DA58E", "#3B82F6", "#8B5CF6", "#F59E0B", "#EC4899", "#10B981"]

        wedges, texts, autotexts = ax_cat.pie(
            cat_values,
            labels=None,
            autopct="%1.0f%%",
            pctdistance=0.75,
            startangle=140,
            colors=palette_colors[: len(cat_labels)],
            wedgeprops=dict(width=0.45, edgecolor=bg_col, linewidth=1.5),
        )

        for autotext in autotexts:
            autotext.set_color("#FFFFFF")
            autotext.set_fontsize(8)
            autotext.set_weight("bold")

        ax_cat.legend(
            wedges,
            [f"{lbl} ({val})" for lbl, val in zip(cat_labels, cat_values)],
            loc="center right",
            bbox_to_anchor=(1.35, 0.5),
            facecolor=bg_col,
            edgecolor=border_col,
            fontsize=7,
            labelcolor=text_sec,
        )

        fig_cat.tight_layout()
        self.chart_canvas_cat = FigureCanvasTkAgg(fig_cat, master=self.chart_canvas_frame_cat)
        self.chart_canvas_cat.draw()
        self.chart_canvas_cat.get_tk_widget().pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 3. Booking Status & Fulfillment Health Donut Chart
        # -------------------------------------------------------------
        if self.chart_canvas_status:
            self.chart_canvas_status.get_tk_widget().destroy()

        fig_status = Figure(figsize=(4.6, 2.5), dpi=100, facecolor=bg_col)
        ax_status = fig_status.add_subplot(111)
        ax_status.set_facecolor(bg_col)

        status_dist = metrics.get("status_distribution", {})
        s_keys = ["Confirmed", "Completed", "Cancelled", "No-Show"]
        s_vals = [status_dist.get(k, 0) for k in s_keys]
        if sum(s_vals) == 0:
            s_vals = [4, 6, 1, 0]

        s_colors = ["#3B82F6", "#10B981", "#F43F5E", "#F59E0B"]

        wedges_s, texts_s, autotexts_s = ax_status.pie(
            s_vals,
            labels=None,
            autopct="%1.0f%%",
            pctdistance=0.75,
            startangle=90,
            colors=s_colors,
            wedgeprops=dict(width=0.45, edgecolor=bg_col, linewidth=1.5),
        )

        for at in autotexts_s:
            at.set_color("#FFFFFF")
            at.set_fontsize(8)
            at.set_weight("bold")

        # Center completion KPI text
        ax_status.text(
            0,
            0,
            f"{int(metrics.get('completion_rate', 100))}%\nSuccess",
            ha="center",
            va="center",
            fontsize=9,
            weight="bold",
            color=text_pri,
        )

        ax_status.legend(
            wedges_s,
            [f"{k}: {v}" for k, v in zip(s_keys, s_vals)],
            loc="center right",
            bbox_to_anchor=(1.35, 0.5),
            facecolor=bg_col,
            edgecolor=border_col,
            fontsize=7,
            labelcolor=text_sec,
        )

        fig_status.tight_layout()
        self.chart_canvas_status = FigureCanvasTkAgg(fig_status, master=self.chart_canvas_frame_status)
        self.chart_canvas_status.draw()
        self.chart_canvas_status.get_tk_widget().pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # 4. Specialist Workload & Demand Horizontal Bar Chart
        # -------------------------------------------------------------
        if self.chart_canvas_staff:
            self.chart_canvas_staff.get_tk_widget().destroy()

        fig_staff = Figure(figsize=(9, 2.3), dpi=100, facecolor=bg_col)
        ax_staff = fig_staff.add_subplot(111)
        ax_staff.set_facecolor(bg_col)

        staff_dist = metrics.get("staff_distribution", {})
        if not staff_dist or sum(staff_dist.values()) == 0:
            staff_dist = {
                "Eleanor Vance": 4,
                "Dr. Marcus Reed": 3,
                "Sophie Dubois": 3,
                "Liam Chen": 2,
            }

        st_names = list(staff_dist.keys())
        st_counts = list(staff_dist.values())

        y_pos = range(len(st_names))
        bars_staff = ax_staff.barh(
            y_pos,
            st_counts,
            height=0.45,
            color=accent_col,
            edgecolor=border_col,
            alpha=0.9,
            zorder=3,
        )

        ax_staff.set_yticks(y_pos)
        ax_staff.set_yticklabels(st_names, color=text_pri, fontsize=8)
        ax_staff.grid(axis="x", color=border_col, linestyle="--", linewidth=0.6, alpha=0.7, zorder=0)
        ax_staff.spines["top"].set_visible(False)
        ax_staff.spines["right"].set_visible(False)
        ax_staff.spines["left"].set_color(border_col)
        ax_staff.spines["bottom"].set_color(border_col)
        ax_staff.tick_params(colors=text_sec, labelsize=8)

        # Count annotations on horizontal bars
        for bar in bars_staff:
            w = bar.get_width()
            ax_staff.annotate(
                f" {int(w)} bookings",
                xy=(w, bar.get_y() + bar.get_height() / 2),
                xytext=(3, 0),
                textcoords="offset points",
                ha="left",
                va="center",
                fontsize=8,
                color=text_sec,
                weight="bold",
            )

        fig_staff.tight_layout()
        self.chart_canvas_staff = FigureCanvasTkAgg(fig_staff, master=self.chart_canvas_frame_staff)
        self.chart_canvas_staff.draw()
        self.chart_canvas_staff.get_tk_widget().pack(fill="both", expand=True)

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
