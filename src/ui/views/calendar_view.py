"""Interactive Calendar View with Day, Week, and Month Perspectives."""

from datetime import date, datetime, timedelta
import calendar
from typing import Callable, Optional, List
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
from src.ui.components.dialogs import ConfirmDialog, PromptDialog
from src.database.connection import get_db
from src.database.models import Appointment, Staff
from src.core.booking_service import BookingService
from src.config import STATUS_COLORS, STATUS_COMPLETED, STATUS_CANCELLED


class CalendarView(ctk.CTkFrame):
    """Visual booking calendar supporting Day, Week, and Month perspectives."""

    def __init__(
        self,
        master,
        on_navigate_wizard: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_navigate_wizard = on_navigate_wizard

        self.current_date = date.today()
        self.view_mode = "week"  # 'day', 'week', 'month'
        self.selected_staff_id = None  # None = All

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header Control Bar
        self.create_controls_bar()

        # Dynamic Calendar Body
        self.calendar_body = ctk.CTkFrame(self, fg_color="transparent")
        self.calendar_body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.calendar_body.grid_columnconfigure(0, weight=1)
        self.calendar_body.grid_rowconfigure(0, weight=1)

        self.refresh_calendar()

    def create_controls_bar(self):
        """Top navigation bar for views and dates."""
        bar = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 12))

        # Left: Prev, Today, Next + Date Label
        nav_box = ctk.CTkFrame(bar, fg_color="transparent")
        nav_box.pack(side="left", padx=16, pady=12)

        ctk.CTkButton(
            nav_box,
            text="◀",
            width=36,
            height=34,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.nav_prev,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            nav_box,
            text="Today",
            width=65,
            height=34,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.nav_today,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            nav_box,
            text="▶",
            width=36,
            height=34,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.nav_next,
        ).pack(side="left", padx=(0, 14))

        self.date_label = ctk.CTkLabel(
            nav_box,
            text="",
            font=FONT_SUBTITLE,
            text_color=PALETTE["dark"]["text_primary"],
        )
        self.date_label.pack(side="left")

        # Right: Staff Filter & Mode Switcher
        actions_box = ctk.CTkFrame(bar, fg_color="transparent")
        actions_box.pack(side="right", padx=16, pady=12)

        # Staff dropdown
        with get_db() as session:
            staff_list = session.query(Staff).filter(Staff.is_active == True).all()
            self.staff_map = {"All Specialists": None}
            for s in staff_list:
                self.staff_map[s.name] = s.id

        self.staff_selector = ctk.CTkOptionMenu(
            actions_box,
            values=list(self.staff_map.keys()),
            width=160,
            height=34,
            font=FONT_SMALL,
            command=self.on_staff_filter_change,
        )
        self.staff_selector.pack(side="left", padx=(0, 12))

        # View Mode Pills: Day | Week | Month
        modes_frame = ctk.CTkFrame(actions_box, fg_color=PALETTE["dark"]["bg_primary"], corner_radius=8)
        modes_frame.pack(side="left")

        self.day_btn = ctk.CTkButton(
            modes_frame,
            text="Day",
            width=60,
            height=30,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=lambda: self.switch_mode("day"),
        )
        self.day_btn.pack(side="left", padx=2, pady=2)

        self.week_btn = ctk.CTkButton(
            modes_frame,
            text="Week",
            width=60,
            height=30,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            command=lambda: self.switch_mode("week"),
        )
        self.week_btn.pack(side="left", padx=2, pady=2)

        self.month_btn = ctk.CTkButton(
            modes_frame,
            text="Month",
            width=65,
            height=30,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=lambda: self.switch_mode("month"),
        )
        self.month_btn.pack(side="left", padx=2, pady=2)

    def switch_mode(self, mode: str):
        self.view_mode = mode
        self.day_btn.configure(fg_color=PALETTE["dark"]["accent"] if mode == "day" else PALETTE["dark"]["card_secondary"])
        self.week_btn.configure(fg_color=PALETTE["dark"]["accent"] if mode == "week" else PALETTE["dark"]["card_secondary"])
        self.month_btn.configure(fg_color=PALETTE["dark"]["accent"] if mode == "month" else PALETTE["dark"]["card_secondary"])
        self.refresh_calendar()

    def nav_today(self):
        self.current_date = date.today()
        self.refresh_calendar()

    def nav_prev(self):
        if self.view_mode == "day":
            self.current_date -= timedelta(days=1)
        elif self.view_mode == "week":
            self.current_date -= timedelta(days=7)
        elif self.view_mode == "month":
            first = self.current_date.replace(day=1)
            self.current_date = (first - timedelta(days=1)).replace(day=1)
        self.refresh_calendar()

    def nav_next(self):
        if self.view_mode == "day":
            self.current_date += timedelta(days=1)
        elif self.view_mode == "week":
            self.current_date += timedelta(days=7)
        elif self.view_mode == "month":
            days_in_month = calendar.monthrange(self.current_date.year, self.current_date.month)[1]
            self.current_date = (self.current_date.replace(day=days_in_month) + timedelta(days=1))
        self.refresh_calendar()

    def on_staff_filter_change(self, choice: str):
        self.selected_staff_id = self.staff_map.get(choice)
        self.refresh_calendar()

    def refresh_calendar(self):
        """Redraw calendar based on view mode."""
        for w in self.calendar_body.winfo_children():
            w.destroy()

        if self.view_mode == "day":
            self.render_day_view()
        elif self.view_mode == "week":
            self.render_week_view()
        elif self.view_mode == "month":
            self.render_month_view()

    # =========================================================================
    # DAY VIEW
    # =========================================================================
    def render_day_view(self):
        date_str = self.current_date.isoformat()
        self.date_label.configure(text=self.current_date.strftime("%A, %B %d, %Y"))

        scroll = ctk.CTkScrollableFrame(
            self.calendar_body,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        scroll.pack(fill="both", expand=True)

        with get_db() as session:
            appointments = BookingService.get_appointments(
                session, target_date=date_str, staff_id=self.selected_staff_id
            )

        if not appointments:
            ctk.CTkLabel(
                scroll,
                text="No appointments scheduled for this date.",
                font=FONT_BODY,
                text_color=PALETTE["dark"]["text_secondary"],
            ).pack(pady=40)
            return

        for app in appointments:
            self.create_appointment_card(scroll, app)

    # =========================================================================
    # WEEK VIEW
    # =========================================================================
    def render_week_view(self):
        start_of_week = self.current_date - timedelta(days=self.current_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        self.date_label.configure(
            text=f"{start_of_week.strftime('%b %d')} – {end_of_week.strftime('%b %d, %Y')}"
        )

        grid_wrapper = ctk.CTkFrame(
            self.calendar_body,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        grid_wrapper.pack(fill="both", expand=True)

        for col in range(7):
            grid_wrapper.grid_columnconfigure(col, weight=1)
        grid_wrapper.grid_rowconfigure(1, weight=1)

        with get_db() as session:
            all_apps = BookingService.get_appointments(
                session,
                start_date=start_of_week.isoformat(),
                end_date=end_of_week.isoformat(),
                staff_id=self.selected_staff_id,
            )

        for i in range(7):
            day_d = start_of_week + timedelta(days=i)
            day_str = day_d.isoformat()
            is_today = (day_d == date.today())

            # Header Column
            head_col = ctk.CTkFrame(
                grid_wrapper,
                height=48,
                corner_radius=6,
                fg_color=PALETTE["dark"]["card_secondary"] if is_today else "transparent",
            )
            head_col.grid(row=0, column=i, sticky="ew", padx=2, pady=4)

            ctk.CTkLabel(
                head_col,
                text=day_d.strftime("%a"),
                font=FONT_SMALL_BOLD,
                text_color=PALETTE["dark"]["accent"] if is_today else PALETTE["dark"]["text_secondary"],
            ).pack(pady=(4, 0))

            ctk.CTkLabel(
                head_col,
                text=str(day_d.day),
                font=FONT_BODY_BOLD,
                text_color=PALETTE["dark"]["text_primary"],
            ).pack(pady=(0, 4))

            # Column Scrollable Feed
            day_feed = ctk.CTkScrollableFrame(
                grid_wrapper,
                fg_color=PALETTE["dark"]["bg_primary"],
                corner_radius=6,
            )
            day_feed.grid(row=1, column=i, sticky="nsew", padx=2, pady=(0, 4))

            day_apps = [a for a in all_apps if a.date == day_str]
            if not day_apps:
                ctk.CTkLabel(
                    day_feed,
                    text="-",
                    font=FONT_SMALL,
                    text_color=PALETTE["dark"]["text_muted"],
                ).pack(pady=20)
            else:
                for app in day_apps:
                    self.create_mini_appointment_card(day_feed, app)

    # =========================================================================
    # MONTH VIEW
    # =========================================================================
    def render_month_view(self):
        year = self.current_date.year
        month = self.current_date.month
        self.date_label.configure(text=self.current_date.strftime("%B %Y"))

        month_frame = ctk.CTkFrame(
            self.calendar_body,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        month_frame.pack(fill="both", expand=True)

        for col in range(7):
            month_frame.grid_columnconfigure(col, weight=1)

        # Days of week header
        days_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col_idx, d_name in enumerate(days_headers):
            lbl = ctk.CTkLabel(
                month_frame,
                text=d_name,
                font=FONT_SMALL_BOLD,
                text_color=PALETTE["dark"]["text_muted"],
            )
            lbl.grid(row=0, column=col_idx, pady=8)

        # Fetch all appointments for month
        first_day_str = f"{year:04d}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        last_day_str = f"{year:04d}-{month:02d}-{last_day:02d}"

        with get_db() as session:
            month_apps = BookingService.get_appointments(
                session,
                start_date=first_day_str,
                end_date=last_day_str,
                staff_id=self.selected_staff_id,
            )

        cal = calendar.monthcalendar(year, month)
        for r_idx, week in enumerate(cal, 1):
            month_frame.grid_rowconfigure(r_idx, weight=1)
            for c_idx, day_num in enumerate(week):
                if day_num == 0:
                    empty_box = ctk.CTkFrame(month_frame, fg_color="transparent")
                    empty_box.grid(row=r_idx, column=c_idx, padx=2, pady=2, sticky="nsew")
                    continue

                d_str = f"{year:04d}-{month:02d}-{day_num:02d}"
                day_apps = [a for a in month_apps if a.date == d_str]
                is_today = (d_str == date.today().isoformat())

                day_box = ctk.CTkFrame(
                    month_frame,
                    corner_radius=8,
                    fg_color=PALETTE["dark"]["card_secondary"] if is_today else PALETTE["dark"]["bg_primary"],
                    border_width=1,
                    border_color=PALETTE["dark"]["accent"] if is_today else PALETTE["dark"]["border"],
                )
                day_box.grid(row=r_idx, column=c_idx, padx=2, pady=2, sticky="nsew")

                # Day number
                ctk.CTkLabel(
                    day_box,
                    text=str(day_num),
                    font=FONT_SMALL_BOLD,
                    text_color=PALETTE["dark"]["accent"] if is_today else PALETTE["dark"]["text_primary"],
                ).pack(anchor="nw", padx=6, pady=4)

                if day_apps:
                    count_pill = ctk.CTkButton(
                        day_box,
                        text=f"📅 {len(day_apps)} bookings",
                        font=("Segoe UI", 9, "bold"),
                        height=22,
                        fg_color=PALETTE["dark"]["accent"],
                        hover_color=PALETTE["dark"]["accent_hover"],
                        command=lambda ds=d_str: self.switch_to_day_view(ds),
                    )
                    count_pill.pack(fill="x", padx=4, pady=2)

    def switch_to_day_view(self, date_str: str):
        self.current_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        self.switch_mode("day")

    def create_appointment_card(self, parent, app: Appointment):
        """Card for Day view with full details."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=8,
            fg_color=PALETTE["dark"]["bg_primary"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        card.pack(fill="x", padx=16, pady=4)

        # Time pill
        ctk.CTkLabel(
            card,
            text=f"{app.start_time}\n{app.end_time}",
            font=FONT_SMALL_BOLD,
            width=65,
            height=38,
            corner_radius=6,
            fg_color=PALETTE["dark"]["card_secondary"],
        ).pack(side="left", padx=12, pady=8)

        # Info
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=6)

        ctk.CTkLabel(
            info,
            text=f"{app.customer.name} • {app.service.name}",
            font=FONT_BODY_BOLD,
            text_color=PALETTE["dark"]["text_primary"],
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            info,
            text=f"Specialist: {app.staff.name}  |  Price: ${app.price:.2f}  |  Notes: {app.notes or 'None'}",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
            anchor="w",
        ).pack(fill="x")

        # Actions
        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="right", padx=12)

        ctk.CTkButton(
            actions,
            text="Manage ➔",
            width=90,
            height=28,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            hover_color=PALETTE["dark"]["accent"],
            command=lambda a_id=app.id: self.manage_appointment_dialog(a_id),
        ).pack(side="left")

    def create_mini_appointment_card(self, parent, app: Appointment):
        """Compact card for Week view column."""
        status_color = STATUS_COLORS.get(app.status, PALETTE["dark"]["accent"])

        card = ctk.CTkFrame(
            parent,
            corner_radius=6,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        card.pack(fill="x", pady=3)

        ctk.CTkLabel(
            card,
            text=f"{app.start_time}-{app.end_time}",
            font=("Segoe UI", 9, "bold"),
            text_color=PALETTE["dark"]["accent"],
            anchor="w",
        ).pack(fill="x", padx=6, pady=(4, 0))

        ctk.CTkLabel(
            card,
            text=app.customer.name,
            font=("Segoe UI", 10, "bold"),
            text_color=PALETTE["dark"]["text_primary"],
            anchor="w",
        ).pack(fill="x", padx=6)

        ctk.CTkLabel(
            card,
            text=app.service.name,
            font=("Segoe UI", 8),
            text_color=PALETTE["dark"]["text_muted"],
            anchor="w",
        ).pack(fill="x", padx=6, pady=(0, 4))

        # Clickable to manage
        card.bind("<Button-1>", lambda e, a_id=app.id: self.manage_appointment_dialog(a_id))

    def manage_appointment_dialog(self, appointment_id: int):
        """Open modal to reschedule, cancel, or mark completed."""
        with get_db() as session:
            app = session.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not app:
                return

            diag = ctk.CTkToplevel(self.winfo_toplevel())
            diag.title(f"Manage Booking: {app.appointment_number}")
            diag.geometry("450x380")
            diag.resizable(False, False)
            diag.transient(self.winfo_toplevel())
            diag.grab_set()
            diag.configure(fg_color=PALETTE["dark"]["card_bg"])

            ctk.CTkLabel(
                diag,
                text=f"Booking Ref: {app.appointment_number}",
                font=FONT_HEADING,
                text_color=PALETTE["dark"]["text_primary"],
            ).pack(anchor="w", padx=24, pady=(20, 4))

            details = [
                f"Client: {app.customer.name} ({app.customer.phone})",
                f"Service: {app.service.name} (${app.price:.2f})",
                f"Specialist: {app.staff.name}",
                f"Date & Time: {app.date} from {app.start_time} to {app.end_time}",
                f"Current Status: {app.status.upper()}",
            ]
            for d in details:
                ctk.CTkLabel(diag, text=d, font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=24, pady=2)

            # Action Buttons
            btn_box = ctk.CTkFrame(diag, fg_color="transparent")
            btn_box.pack(fill="x", padx=24, pady=24)

            # Mark Completed
            def do_complete():
                diag.destroy()
                with get_db() as s:
                    BookingService.update_status(s, appointment_id, STATUS_COMPLETED)
                show_toast(self.winfo_toplevel(), "Marked as completed!", level="success")
                self.refresh_calendar()

            ctk.CTkButton(
                btn_box,
                text="✔ Mark Completed",
                height=36,
                fg_color=PALETTE["dark"]["success"],
                command=do_complete,
            ).pack(fill="x", pady=4)

            # Cancel
            def do_cancel():
                diag.destroy()
                with get_db() as s:
                    BookingService.cancel_appointment(s, appointment_id, "Cancelled by user")
                show_toast(self.winfo_toplevel(), "Booking cancelled.", level="info")
                self.refresh_calendar()

            ctk.CTkButton(
                btn_box,
                text="✕ Cancel Booking",
                height=36,
                fg_color=PALETTE["dark"]["danger"],
                hover_color=PALETTE["dark"]["danger_hover"],
                command=do_cancel,
            ).pack(fill="x", pady=4)

            # Close
            ctk.CTkButton(
                btn_box,
                text="Close",
                height=34,
                fg_color=PALETTE["dark"]["card_secondary"],
                command=diag.destroy,
            ).pack(fill="x", pady=4)
