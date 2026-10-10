"""Staff Management View with Weekly Hours, Lunch Breaks, and Leaves."""

from typing import Optional, List, Dict
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
from src.database.models import Staff, StaffSchedule, StaffLeave, Service
from src.config import DAYS_OF_WEEK


class StaffView(ctk.CTkFrame):
    """Staff profiles, weekly schedules, breaks, and leaves."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.selected_staff_id: Optional[int] = None

        self.grid_columnconfigure(0, weight=4)  # Left list
        self.grid_columnconfigure(1, weight=6)  # Right tabs
        self.grid_rowconfigure(1, weight=1)

        # 1. Header
        self.create_header()

        # 2. Left List
        self.create_left_list()

        # 3. Right Management Pane
        self.create_right_pane()

        self.refresh_staff_list()

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Specialists & Schedules",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Manage staff profiles, weekly working hours, lunch breaks, and leaves",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="➕ Add Specialist",
            width=140,
            height=36,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            hover_color=PALETTE["dark"]["accent_hover"],
            command=self.open_add_staff_modal,
        ).pack(side="right")

    def create_left_list(self):
        left_box = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        left_box.grid(row=1, column=0, sticky="nsew", padx=(24, 10), pady=(0, 20))
        left_box.grid_columnconfigure(0, weight=1)
        left_box.grid_rowconfigure(0, weight=1)

        self.staff_feed = ctk.CTkScrollableFrame(left_box, fg_color="transparent")
        self.staff_feed.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def create_right_pane(self):
        self.right_box = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.right_box.grid(row=1, column=1, sticky="nsew", padx=(10, 24), pady=(0, 20))

    def refresh_staff_list(self):
        for w in self.staff_feed.winfo_children():
            w.destroy()

        with get_db() as session:
            staff_members = session.query(Staff).order_by(Staff.name.asc()).all()
            if not staff_members:
                ctk.CTkLabel(self.staff_feed, text="No staff members registered.", font=FONT_BODY, text_color=PALETTE["dark"]["text_secondary"]).pack(pady=30)
                return

            if self.selected_staff_id is None and staff_members:
                self.selected_staff_id = staff_members[0].id

            for s in staff_members:
                is_selected = (s.id == self.selected_staff_id)
                card = ctk.CTkFrame(
                    self.staff_feed,
                    corner_radius=8,
                    fg_color=PALETTE["dark"]["card_secondary"] if is_selected else PALETTE["dark"]["bg_primary"],
                    border_width=1,
                    border_color=PALETTE["dark"]["accent"] if is_selected else PALETTE["dark"]["border"],
                )
                card.pack(fill="x", pady=4, padx=4)

                # Avatar
                avatar = ctk.CTkLabel(
                    card,
                    text="👤",
                    font=("Segoe UI", 16),
                    width=38,
                    height=38,
                    corner_radius=8,
                    fg_color=s.color_code,
                    text_color="#FFFFFF",
                )
                avatar.pack(side="left", padx=10, pady=10)

                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True)

                ctk.CTkLabel(info, text=s.name, font=FONT_BODY_BOLD, text_color=PALETTE["dark"]["text_primary"], anchor="w").pack(fill="x")
                ctk.CTkLabel(info, text=f"{s.role_title} • {s.phone or ''}", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"], anchor="w").pack(fill="x")

                card.bind("<Button-1>", lambda e, s_id=s.id: self.select_staff(s_id))

        self.render_staff_details()

    def select_staff(self, staff_id: int):
        self.selected_staff_id = staff_id
        self.refresh_staff_list()

    def render_staff_details(self):
        for w in self.right_box.winfo_children():
            w.destroy()

        if not self.selected_staff_id:
            ctk.CTkLabel(self.right_box, text="Select a specialist to view schedule and services.", font=FONT_BODY, text_color=PALETTE["dark"]["text_secondary"]).pack(pady=50)
            return

        with get_db() as session:
            staff = session.query(Staff).filter(Staff.id == self.selected_staff_id).first()
            if not staff:
                return

            # Header info card
            top_card = ctk.CTkFrame(self.right_box, fg_color=PALETTE["dark"]["bg_primary"], corner_radius=10)
            top_card.pack(fill="x", padx=16, pady=(16, 16))

            ctk.CTkLabel(top_card, text=staff.name, font=FONT_TITLE, text_color=PALETTE["dark"]["text_primary"]).pack(anchor="w", padx=16, pady=(12, 2))
            ctk.CTkLabel(top_card, text=f"{staff.role_title}   |   {staff.email or ''}   |   {staff.phone or ''}", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=16, pady=(0, 12))

            # Tabview: 1. Hours & Breaks, 2. Leaves, 3. Services
            tabview = ctk.CTkTabview(self.right_box, fg_color=PALETTE["dark"]["bg_primary"])
            tabview.pack(fill="both", expand=True, padx=16, pady=(0, 16))

            t_hours = tabview.add("Weekly Working Hours & Breaks")
            t_leaves = tabview.add("Leaves & Vacations")
            t_services = tabview.add("Assigned Services")

            # -------------------------------------------------------------
            # TAB 1: WEEKLY HOURS & BREAKS
            # -------------------------------------------------------------
            ctk.CTkLabel(t_hours, text="Configure weekly shift times and break intervals:", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", pady=(6, 12))

            scheds = {s.day_of_week: s for s in staff.schedules}
            self.sched_rows = []

            for day_idx, day_name in enumerate(DAYS_OF_WEEK):
                sc = scheds.get(day_idx)
                row = ctk.CTkFrame(t_hours, fg_color="transparent")
                row.pack(fill="x", pady=4)

                # Active Checkbox
                chk_var = ctk.BooleanVar(value=sc.is_working if sc else (day_idx < 6))
                chk = ctk.CTkCheckBox(row, text=day_name, variable=chk_var, font=FONT_SMALL_BOLD, width=110)
                chk.pack(side="left")

                # Work Shift
                ctk.CTkLabel(row, text="Shift:", font=FONT_SMALL, text_color=PALETTE["dark"]["text_muted"]).pack(side="left", padx=(8, 2))
                start_ent = ctk.CTkEntry(row, width=60, height=28, font=FONT_SMALL)
                start_ent.insert(0, sc.start_time if sc else "09:00")
                start_ent.pack(side="left")

                ctk.CTkLabel(row, text="–", font=FONT_SMALL).pack(side="left", padx=2)
                end_ent = ctk.CTkEntry(row, width=60, height=28, font=FONT_SMALL)
                end_ent.insert(0, sc.end_time if sc else "18:00")
                end_ent.pack(side="left")

                # Break Shift
                ctk.CTkLabel(row, text="Break:", font=FONT_SMALL, text_color=PALETTE["dark"]["text_muted"]).pack(side="left", padx=(14, 2))
                b_start_ent = ctk.CTkEntry(row, width=60, height=28, font=FONT_SMALL)
                b_start_ent.insert(0, sc.break_start if sc else "13:00")
                b_start_ent.pack(side="left")

                ctk.CTkLabel(row, text="–", font=FONT_SMALL).pack(side="left", padx=2)
                b_end_ent = ctk.CTkEntry(row, width=60, height=28, font=FONT_SMALL)
                b_end_ent.insert(0, sc.break_end if sc else "14:00")
                b_end_ent.pack(side="left")

                self.sched_rows.append((day_idx, chk_var, start_ent, end_ent, b_start_ent, b_end_ent))

            def save_schedule():
                with get_db() as s:
                    st = s.query(Staff).filter(Staff.id == self.selected_staff_id).first()
                    # Clear existing
                    s.query(StaffSchedule).filter(StaffSchedule.staff_id == st.id).delete()
                    for d_idx, is_work, s_ent, e_ent, bs_ent, be_ent in self.sched_rows:
                        new_sched = StaffSchedule(
                            staff_id=st.id,
                            day_of_week=d_idx,
                            is_working=is_work.get(),
                            start_time=s_ent.get().strip(),
                            end_time=e_ent.get().strip(),
                            break_start=bs_ent.get().strip(),
                            break_end=be_ent.get().strip(),
                        )
                        s.add(new_sched)
                show_toast(self.winfo_toplevel(), "Working hours and breaks updated!", level="success")

            ctk.CTkButton(
                t_hours,
                text="💾 Save Weekly Hours & Breaks",
                height=34,
                font=FONT_SMALL_BOLD,
                fg_color=PALETTE["dark"]["accent"],
                command=save_schedule,
            ).pack(anchor="e", pady=(16, 10))

            # -------------------------------------------------------------
            # TAB 2: LEAVES & VACATIONS
            # -------------------------------------------------------------
            leaves_box = ctk.CTkFrame(t_leaves, fg_color="transparent")
            leaves_box.pack(fill="both", expand=True, pady=6)

            ctk.CTkLabel(leaves_box, text="Record Leave / Vacation:", font=FONT_SMALL_BOLD).pack(anchor="w")

            form_row = ctk.CTkFrame(leaves_box, fg_color="transparent")
            form_row.pack(fill="x", pady=(4, 12))

            ctk.CTkLabel(form_row, text="From (YYYY-MM-DD):", font=FONT_SMALL).pack(side="left")
            l_start_ent = ctk.CTkEntry(form_row, width=100, height=30)
            l_start_ent.pack(side="left", padx=(4, 10))

            ctk.CTkLabel(form_row, text="To:", font=FONT_SMALL).pack(side="left")
            l_end_ent = ctk.CTkEntry(form_row, width=100, height=30)
            l_end_ent.pack(side="left", padx=(4, 10))

            ctk.CTkLabel(form_row, text="Reason:", font=FONT_SMALL).pack(side="left")
            l_reason_ent = ctk.CTkEntry(form_row, width=120, height=30)
            l_reason_ent.pack(side="left", padx=(4, 10))

            def add_leave():
                s_d = l_start_ent.get().strip()
                e_d = l_end_ent.get().strip()
                rsn = l_reason_ent.get().strip() or "Personal Leave"
                if not s_d or not e_d:
                    show_toast(self.winfo_toplevel(), "Start and End dates are required.", level="warning")
                    return
                with get_db() as s:
                    leave = StaffLeave(staff_id=self.selected_staff_id, start_date=s_d, end_date=e_d, reason=rsn, status="approved")
                    s.add(leave)
                show_toast(self.winfo_toplevel(), "Leave recorded! Slots blocked.", level="success")
                self.render_staff_details()

            ctk.CTkButton(form_row, text="Add Leave", width=90, height=30, fg_color=PALETTE["dark"]["accent"], command=add_leave).pack(side="left")

            ctk.CTkLabel(leaves_box, text="Current & Upcoming Leaves:", font=FONT_SMALL_BOLD).pack(anchor="w", pady=(10, 4))
            for l in staff.leaves:
                l_row = ctk.CTkFrame(leaves_box, corner_radius=6, fg_color=PALETTE["dark"]["card_bg"])
                l_row.pack(fill="x", pady=2)
                ctk.CTkLabel(l_row, text=f"📅 {l.start_date} to {l.end_date}  —  {l.reason} ({l.status.upper()})", font=FONT_SMALL).pack(side="left", padx=10, pady=6)

                def remove_leave(lid=l.id):
                    with get_db() as s:
                        s.query(StaffLeave).filter(StaffLeave.id == lid).delete()
                    show_toast(self.winfo_toplevel(), "Leave removed.", level="info")
                    self.render_staff_details()

                ctk.CTkButton(l_row, text="✕", width=28, height=24, fg_color=PALETTE["dark"]["danger"], command=remove_leave).pack(side="right", padx=6)

            # -------------------------------------------------------------
            # TAB 3: ASSIGNED SERVICES
            # -------------------------------------------------------------
            all_services = session.query(Service).filter(Service.is_active == True).all()
            assigned_ids = {srv.id for srv in staff.services}
            self.service_checkboxes = []

            for srv in all_services:
                v = ctk.BooleanVar(value=(srv.id in assigned_ids))
                cb = ctk.CTkCheckBox(t_services, text=f"{srv.name} (${srv.price:.2f}, {srv.duration_minutes}m)", variable=v, font=FONT_SMALL)
                cb.pack(anchor="w", padx=10, pady=4)
                self.service_checkboxes.append((srv.id, v))

            def save_services():
                with get_db() as s:
                    st = s.query(Staff).filter(Staff.id == self.selected_staff_id).first()
                    st.services.clear()
                    for srv_id, checked in self.service_checkboxes:
                        if checked.get():
                            srv_obj = s.query(Service).filter(Service.id == srv_id).first()
                            st.services.append(srv_obj)
                show_toast(self.winfo_toplevel(), "Assigned services updated!", level="success")

            ctk.CTkButton(
                t_services,
                text="💾 Save Assigned Services",
                height=34,
                font=FONT_SMALL_BOLD,
                fg_color=PALETTE["dark"]["accent"],
                command=save_services,
            ).pack(anchor="e", pady=(16, 10))

    def open_add_staff_modal(self):
        diag = ctk.CTkToplevel(self.winfo_toplevel())
        diag.title("Add Specialist Profile")
        diag.geometry("440x360")
        diag.resizable(False, False)
        diag.transient(self.winfo_toplevel())
        diag.grab_set()
        diag.configure(fg_color=PALETTE["dark"]["card_bg"])

        ctk.CTkLabel(diag, text="New Specialist Profile", font=FONT_HEADING).pack(anchor="w", padx=24, pady=(20, 14))

        ctk.CTkLabel(diag, text="Full Name *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        name_entry = ctk.CTkEntry(diag, height=36)
        name_entry.pack(fill="x", padx=24, pady=(2, 8))

        ctk.CTkLabel(diag, text="Role Title *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        role_entry = ctk.CTkEntry(diag, height=36)
        role_entry.insert(0, "Senior Specialist")
        role_entry.pack(fill="x", padx=24, pady=(2, 8))

        ctk.CTkLabel(diag, text="Phone Number", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        phone_entry = ctk.CTkEntry(diag, height=36)
        phone_entry.pack(fill="x", padx=24, pady=(2, 8))

        ctk.CTkLabel(diag, text="Color Code (Hex)", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        color_entry = ctk.CTkEntry(diag, height=36)
        color_entry.insert(0, "#3B82F6")
        color_entry.pack(fill="x", padx=24, pady=(2, 16))

        def submit():
            nm = name_entry.get().strip()
            rl = role_entry.get().strip()
            ph = phone_entry.get().strip()
            col = color_entry.get().strip() or "#3B82F6"

            if not nm:
                show_toast(diag, "Name is required.", level="warning")
                return

            with get_db() as s:
                new_st = Staff(name=nm, role_title=rl, phone=ph, color_code=col, is_active=True)
                s.add(new_st)
                s.flush()

                # Add default Mon-Fri working schedule
                for d in range(7):
                    sched = StaffSchedule(
                        staff_id=new_st.id,
                        day_of_week=d,
                        is_working=(d < 5),
                        start_time="09:00",
                        end_time="18:00",
                        break_start="13:00",
                        break_end="14:00",
                    )
                    s.add(sched)
                self.selected_staff_id = new_st.id

            diag.destroy()
            show_toast(self.winfo_toplevel(), "Specialist added!", level="success")
            self.refresh_staff_list()

        btn_box = ctk.CTkFrame(diag, fg_color="transparent")
        btn_box.pack(fill="x", padx=24)
        ctk.CTkButton(btn_box, text="Cancel", width=100, height=36, fg_color=PALETTE["dark"]["card_secondary"], command=diag.destroy).pack(side="left")
        ctk.CTkButton(btn_box, text="Save Specialist", width=140, height=36, fg_color=PALETTE["dark"]["accent"], command=submit).pack(side="right")
