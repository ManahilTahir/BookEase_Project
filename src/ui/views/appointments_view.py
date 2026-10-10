"""Appointments List & Management View with Filters, Search, and Exports."""

from datetime import date
from typing import Callable, Optional
import os
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
from src.ui.components.dialogs import ConfirmDialog
from src.database.connection import get_db
from src.database.models import Appointment, Staff
from src.core.booking_service import BookingService
from src.core.reports_service import ReportsService
from src.core.availability import AvailabilityEngine
from src.config import (
    STATUS_CONFIRMED,
    STATUS_COMPLETED,
    STATUS_CANCELLED,
    STATUS_NO_SHOW,
    STATUS_COLORS,
)


class AppointmentsView(ctk.CTkFrame):
    """Full-featured appointments management table with search and filters."""

    def __init__(
        self,
        master,
        on_navigate_wizard: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_navigate_wizard = on_navigate_wizard

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header Row
        self.create_header()

        # 2. Search & Filter Bar
        self.create_filter_bar()

        # 3. Appointments Table Feed
        self.table_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.table_scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.refresh_table()

    def create_header(self):
        """Top action bar."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Appointments Directory",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Search, filter, reschedule, and manage customer bookings",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        # Export Excel
        ctk.CTkButton(
            actions_box,
            text="📊 Export Excel",
            width=110,
            height=36,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.export_excel,
        ).pack(side="left", padx=(0, 8))

        # Export CSV
        ctk.CTkButton(
            actions_box,
            text="📋 Export CSV",
            width=100,
            height=36,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.export_csv,
        ).pack(side="left", padx=(0, 8))

        # New Booking
        if self.on_navigate_wizard:
            ctk.CTkButton(
                actions_box,
                text="➕ New Booking",
                width=120,
                height=36,
                font=FONT_BODY_BOLD,
                fg_color=PALETTE["dark"]["accent"],
                command=self.on_navigate_wizard,
            ).pack(side="left")

    def create_filter_bar(self):
        """Search field and status/staff filters."""
        bar = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))

        # Search box
        self.search_entry = ctk.CTkEntry(
            bar,
            placeholder_text="🔍 Search by Ref #, client name, phone, or specialist...",
            height=38,
            font=FONT_BODY,
            fg_color=PALETTE["dark"]["bg_primary"],
            border_color=PALETTE["dark"]["border"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_table())

        # Status filter
        ctk.CTkLabel(bar, text="Status:", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(side="left", padx=(8, 4))
        self.status_var = ctk.StringVar(value="All")
        self.status_dropdown = ctk.CTkOptionMenu(
            bar,
            values=["All", STATUS_CONFIRMED, STATUS_COMPLETED, STATUS_CANCELLED, STATUS_NO_SHOW],
            variable=self.status_var,
            width=120,
            height=36,
            font=FONT_SMALL,
            command=lambda v: self.refresh_table(),
        )
        self.status_dropdown.pack(side="left", padx=(0, 12))

    def refresh_table(self):
        """Fetch filtered appointments from database and render table."""
        for w in self.table_scroll.winfo_children():
            w.destroy()

        search_query = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        status_filter = self.status_var.get() if hasattr(self, "status_var") else "All"

        with get_db() as session:
            appointments = BookingService.get_appointments(
                session=session,
                status=status_filter if status_filter != "All" else None,
                search_query=search_query if search_query else None,
            )

            if not appointments:
                empty = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
                empty.pack(pady=40)
                ctk.CTkLabel(empty, text="🔍 No appointments matched your search criteria.", font=FONT_BODY, text_color=PALETTE["dark"]["text_secondary"]).pack()
                return

            # Table Header
            head_row = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            head_row.pack(fill="x", padx=16, pady=(10, 6))

            headers = [
                ("Ref #", 110),
                ("Date & Time", 120),
                ("Client", 160),
                ("Specialist", 130),
                ("Service", 160),
                ("Price", 80),
                ("Status", 100),
                ("Actions", 160),
            ]
            for title, w in headers:
                ctk.CTkLabel(
                    head_row,
                    text=title,
                    font=FONT_SMALL_BOLD,
                    text_color=PALETTE["dark"]["text_muted"],
                    width=w,
                    anchor="w",
                ).pack(side="left", padx=4)

            # Table Rows
            for app in appointments:
                row = ctk.CTkFrame(
                    self.table_scroll,
                    corner_radius=6,
                    fg_color=PALETTE["dark"]["bg_primary"],
                    border_width=1,
                    border_color=PALETTE["dark"]["border"],
                )
                row.pack(fill="x", padx=16, pady=3)

                # Ref #
                ctk.CTkLabel(row, text=app.appointment_number, font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["accent"], width=110, anchor="w").pack(side="left", padx=4, pady=10)

                # Date & Time
                time_str = f"{app.date}\n{app.start_time}-{app.end_time}"
                ctk.CTkLabel(row, text=time_str, font=FONT_SMALL, text_color=PALETTE["dark"]["text_primary"], width=120, anchor="w").pack(side="left", padx=4)

                # Client
                client_str = f"{app.customer.name}\n{app.customer.phone}" if app.customer else "N/A"
                ctk.CTkLabel(row, text=client_str, font=FONT_SMALL, text_color=PALETTE["dark"]["text_primary"], width=160, anchor="w").pack(side="left", padx=4)

                # Specialist
                staff_name = app.staff.name if app.staff else "Unassigned"
                ctk.CTkLabel(row, text=staff_name, font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"], width=130, anchor="w").pack(side="left", padx=4)

                # Service
                srv_name = app.service.name if app.service else "Service"
                ctk.CTkLabel(row, text=srv_name, font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"], width=160, anchor="w").pack(side="left", padx=4)

                # Price
                ctk.CTkLabel(row, text=f"${app.price:.2f}", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["success"], width=80, anchor="w").pack(side="left", padx=4)

                # Status pill
                s_color = STATUS_COLORS.get(app.status, PALETTE["dark"]["accent"])
                ctk.CTkLabel(
                    row,
                    text=app.status.upper(),
                    font=("Segoe UI", 9, "bold"),
                    width=90,
                    height=24,
                    corner_radius=6,
                    fg_color=s_color,
                    text_color="#FFFFFF",
                ).pack(side="left", padx=4)

                # Actions Box
                act_box = ctk.CTkFrame(row, fg_color="transparent", width=160)
                act_box.pack(side="left", padx=4)

                # Manage / Reschedule
                ctk.CTkButton(
                    act_box,
                    text="Reschedule",
                    width=75,
                    height=26,
                    font=("Segoe UI", 9, "bold"),
                    fg_color=PALETTE["dark"]["card_secondary"],
                    hover_color=PALETTE["dark"]["accent"],
                    command=lambda a_id=app.id: self.open_reschedule_modal(a_id),
                ).pack(side="left", padx=2)

                # Cancel / Status
                if app.status == STATUS_CONFIRMED:
                    ctk.CTkButton(
                        act_box,
                        text="Done",
                        width=45,
                        height=26,
                        font=("Segoe UI", 9, "bold"),
                        fg_color=PALETTE["dark"]["success"],
                        hover_color="#059669",
                        command=lambda a_id=app.id: self.mark_done(a_id),
                    ).pack(side="left", padx=2)
                elif app.status == STATUS_COMPLETED:
                    ctk.CTkLabel(act_box, text="Finished", font=("Segoe UI", 9), text_color=PALETTE["dark"]["text_muted"]).pack(side="left", padx=6)

    def mark_done(self, appointment_id: int):
        with get_db() as session:
            BookingService.update_status(session, appointment_id, STATUS_COMPLETED)
        show_toast(self.winfo_toplevel(), "Appointment completed!", level="success")
        self.refresh_table()

    def open_reschedule_modal(self, appointment_id: int):
        """Modal dialog to reschedule an appointment."""
        with get_db() as session:
            app = session.query(Appointment).filter(Appointment.id == appointment_id).first()
            if not app:
                return

            diag = ctk.CTkToplevel(self.winfo_toplevel())
            diag.title(f"Reschedule: {app.appointment_number}")
            diag.geometry("440x360")
            diag.resizable(False, False)
            diag.transient(self.winfo_toplevel())
            diag.grab_set()
            diag.configure(fg_color=PALETTE["dark"]["card_bg"])

            ctk.CTkLabel(diag, text=f"Reschedule {app.appointment_number}", font=FONT_HEADING).pack(anchor="w", padx=24, pady=(20, 4))
            ctk.CTkLabel(diag, text=f"Client: {app.customer.name} | Staff: {app.staff.name}", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=24, pady=(0, 16))

            ctk.CTkLabel(diag, text="New Date (YYYY-MM-DD):", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            date_entry = ctk.CTkEntry(diag, height=36)
            date_entry.insert(0, app.date)
            date_entry.pack(fill="x", padx=24, pady=(2, 10))

            ctk.CTkLabel(diag, text="New Start Time (HH:MM):", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            time_entry = ctk.CTkEntry(diag, height=36)
            time_entry.insert(0, app.start_time)
            time_entry.pack(fill="x", padx=24, pady=(2, 10))

            ctk.CTkLabel(diag, text="Reason for Rescheduling:", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            reason_entry = ctk.CTkEntry(diag, height=36)
            reason_entry.insert(0, "Client request")
            reason_entry.pack(fill="x", padx=24, pady=(2, 20))

            def submit_reschedule():
                new_d = date_entry.get().strip()
                new_t = time_entry.get().strip()
                reason = reason_entry.get().strip()

                with get_db() as s:
                    ok, _, err = BookingService.reschedule_appointment(
                        session=s,
                        appointment_id=appointment_id,
                        new_date=new_d,
                        new_start_time=new_t,
                        reason=reason,
                    )
                    if not ok:
                        show_toast(diag, f"Error: {err}", level="error")
                        return

                diag.destroy()
                show_toast(self.winfo_toplevel(), "Rescheduled successfully!", level="success")
                self.refresh_table()

            btn_box = ctk.CTkFrame(diag, fg_color="transparent")
            btn_box.pack(fill="x", padx=24)

            ctk.CTkButton(btn_box, text="Cancel", width=100, height=36, fg_color=PALETTE["dark"]["card_secondary"], command=diag.destroy).pack(side="left")
            ctk.CTkButton(btn_box, text="Confirm New Time", width=160, height=36, fg_color=PALETTE["dark"]["accent"], command=submit_reschedule).pack(side="right")

    def export_excel(self):
        """Export current filtered view to Excel."""
        with get_db() as session:
            apps = BookingService.get_appointments(
                session=session,
                status=self.status_var.get() if self.status_var.get() != "All" else None,
                search_query=self.search_entry.get().strip() or None,
            )
            out = ReportsService.export_appointments_excel(session, apps)
            show_toast(self.winfo_toplevel(), f"Excel exported to {out.name}!", level="success")
            os.startfile(str(out))

    def export_csv(self):
        """Export current filtered view to CSV."""
        with get_db() as session:
            apps = BookingService.get_appointments(
                session=session,
                status=self.status_var.get() if self.status_var.get() != "All" else None,
                search_query=self.search_entry.get().strip() or None,
            )
            out = ReportsService.export_appointments_csv(apps)
            show_toast(self.winfo_toplevel(), f"CSV exported to {out.name}!", level="success")
            os.startfile(str(out))
