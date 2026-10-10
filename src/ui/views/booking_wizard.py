"""Guided Booking Assistant Wizard (Step-by-step logic-based booking agent)."""

from datetime import date, timedelta
from typing import Callable, Optional, List, Dict
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
from src.database.models import Service, Staff, Customer, BusinessSetting
from src.core.availability import AvailabilityEngine
from src.core.booking_service import BookingService
from src.core.notifications import NotificationService


class BookingWizardView(ctk.CTkFrame):
    """4-Step guided assistant for booking appointments."""

    def __init__(
        self,
        master,
        on_booking_complete: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_booking_complete = on_booking_complete

        self.current_step = 1

        # Selected state
        self.selected_service: Optional[Service] = None
        self.selected_staff: Optional[Staff] = None
        self.selected_date: str = date.today().isoformat()
        self.selected_slot: Optional[Dict[str, str]] = None
        self.selected_customer: Optional[Customer] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header with Steps Stepper
        self.create_stepper_header()

        # Dynamic Content Container
        self.step_container = ctk.CTkFrame(self, fg_color="transparent")
        self.step_container.grid(row=1, column=0, sticky="nsew", padx=24, pady=10)
        self.step_container.grid_columnconfigure(0, weight=1)
        self.step_container.grid_rowconfigure(0, weight=1)

        # Render Step 1 initially
        self.render_step_1_services()

    def create_stepper_header(self):
        """Top progress bar indicating the 4 booking steps."""
        self.header_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 12))

        # Title
        top_row = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(14, 10))

        ctk.CTkLabel(
            top_row,
            text="Guided Booking Assistant",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text="Deterministic logic-based scheduling",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["accent"],
        ).pack(side="right")

        # Step pills
        self.steps_bar = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.steps_bar.pack(fill="x", padx=20, pady=(0, 14))

        self.step_labels = []
        step_names = [
            "1. Select Service",
            "2. Select Specialist",
            "3. Choose Date & Slot",
            "4. Client & Confirm",
        ]

        for i, name in enumerate(step_names, 1):
            pill = ctk.CTkLabel(
                self.steps_bar,
                text=name,
                font=FONT_SMALL_BOLD,
                corner_radius=6,
                height=30,
                width=160,
                fg_color=PALETTE["dark"]["accent"] if i == 1 else PALETTE["dark"]["card_secondary"],
                text_color="#FFFFFF" if i == 1 else PALETTE["dark"]["text_secondary"],
            )
            pill.pack(side="left", padx=4, expand=True)
            self.step_labels.append(pill)

    def update_stepper(self, active_step: int):
        """Update step highlight styling."""
        self.current_step = active_step
        for i, pill in enumerate(self.step_labels, 1):
            if i == active_step:
                pill.configure(
                    fg_color=PALETTE["dark"]["accent"],
                    text_color="#FFFFFF",
                )
            elif i < active_step:
                pill.configure(
                    fg_color=PALETTE["dark"]["success"],
                    text_color="#FFFFFF",
                )
            else:
                pill.configure(
                    fg_color=PALETTE["dark"]["card_secondary"],
                    text_color=PALETTE["dark"]["text_secondary"],
                )

    def clear_container(self):
        """Clear current step widgets."""
        for widget in self.step_container.winfo_children():
            widget.destroy()

    # =========================================================================
    # STEP 1: SELECT SERVICE
    # =========================================================================
    def render_step_1_services(self):
        self.clear_container()
        self.update_stepper(1)

        scroll = ctk.CTkScrollableFrame(
            self.step_container,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text="Step 1: Choose Service",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w", padx=20, pady=(16, 6))

        ctk.CTkLabel(
            scroll,
            text="Select the service package for this appointment session.",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(0, 16))

        with get_db() as session:
            services = session.query(Service).filter(Service.is_active == True).all()
            cur_sym = "$"
            cur_setting = session.query(BusinessSetting).filter(BusinessSetting.key == "currency_symbol").first()
            if cur_setting:
                cur_sym = cur_setting.value

            # Group by category
            categories = {}
            for s in services:
                categories.setdefault(s.category, []).append(s)

            for cat_name, cat_services in categories.items():
                ctk.CTkLabel(
                    scroll,
                    text=f"📂 {cat_name.upper()}",
                    font=FONT_SMALL_BOLD,
                    text_color=PALETTE["dark"]["text_muted"],
                ).pack(anchor="w", padx=20, pady=(10, 6))

                for srv in cat_services:
                    card = ctk.CTkFrame(
                        scroll,
                        corner_radius=8,
                        fg_color=PALETTE["dark"]["bg_primary"],
                        border_width=1,
                        border_color=PALETTE["dark"]["border"],
                    )
                    card.pack(fill="x", padx=20, pady=4)

                    left_info = ctk.CTkFrame(card, fg_color="transparent")
                    left_info.pack(side="left", padx=16, pady=12, fill="x", expand=True)

                    ctk.CTkLabel(
                        left_info,
                        text=srv.name,
                        font=FONT_BODY_BOLD,
                        text_color=PALETTE["dark"]["text_primary"],
                        anchor="w",
                    ).pack(fill="x")

                    ctk.CTkLabel(
                        left_info,
                        text=f"⏱ {srv.duration_minutes} min duration (+{srv.buffer_minutes}m buffer)  •  {srv.description or ''}",
                        font=FONT_SMALL,
                        text_color=PALETTE["dark"]["text_secondary"],
                        anchor="w",
                    ).pack(fill="x", pady=(2, 0))

                    # Price & Select button
                    right_box = ctk.CTkFrame(card, fg_color="transparent")
                    right_box.pack(side="right", padx=16, pady=12)

                    ctk.CTkLabel(
                        right_box,
                        text=f"{cur_sym}{srv.price:.2f}",
                        font=FONT_BODY_BOLD,
                        text_color=PALETTE["dark"]["success"],
                    ).pack(side="left", padx=12)

                    ctk.CTkButton(
                        right_box,
                        text="Select ➔",
                        width=90,
                        height=32,
                        font=FONT_SMALL_BOLD,
                        fg_color=PALETTE["dark"]["accent"],
                        hover_color=PALETTE["dark"]["accent_hover"],
                        command=lambda s_obj=srv: self.on_service_selected(s_obj),
                    ).pack(side="left")

    def on_service_selected(self, srv: Service):
        self.selected_service = srv
        self.render_step_2_staff()

    # =========================================================================
    # STEP 2: SELECT STAFF
    # =========================================================================
    def render_step_2_staff(self):
        self.clear_container()
        self.update_stepper(2)

        scroll = ctk.CTkScrollableFrame(
            self.step_container,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        scroll.pack(fill="both", expand=True)

        # Step header
        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(
            head,
            text=f"Step 2: Choose Specialist for '{self.selected_service.name}'",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            head,
            text="⬅ Back to Services",
            width=130,
            height=30,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.render_step_1_services,
        ).pack(side="right")

        with get_db() as session:
            # Query staff assigned to this service, or all active staff if no direct link
            service = session.query(Service).filter(Service.id == self.selected_service.id).first()
            qualified_staff = [s for s in service.staff_members if s.is_active] if service.staff_members else session.query(Staff).filter(Staff.is_active == True).all()

            if not qualified_staff:
                ctk.CTkLabel(
                    scroll,
                    text="No active specialists are currently assigned to this service.",
                    font=FONT_BODY,
                    text_color=PALETTE["dark"]["warning"],
                ).pack(pady=40)
                return

            for staff in qualified_staff:
                card = ctk.CTkFrame(
                    scroll,
                    corner_radius=8,
                    fg_color=PALETTE["dark"]["bg_primary"],
                    border_width=1,
                    border_color=PALETTE["dark"]["border"],
                )
                card.pack(fill="x", padx=20, pady=6)

                # Avatar Color Pill
                avatar = ctk.CTkLabel(
                    card,
                    text="👤",
                    font=("Segoe UI", 16),
                    width=42,
                    height=42,
                    corner_radius=8,
                    fg_color=staff.color_code,
                    text_color="#FFFFFF",
                )
                avatar.pack(side="left", padx=14, pady=14)

                # Details
                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True, padx=6)

                ctk.CTkLabel(
                    info,
                    text=staff.name,
                    font=FONT_BODY_BOLD,
                    text_color=PALETTE["dark"]["text_primary"],
                    anchor="w",
                ).pack(fill="x")

                ctk.CTkLabel(
                    info,
                    text=f"{staff.role_title} • {staff.phone or ''} • {staff.bio or ''}",
                    font=FONT_SMALL,
                    text_color=PALETTE["dark"]["text_secondary"],
                    anchor="w",
                ).pack(fill="x", pady=(2, 0))

                # Select Button
                ctk.CTkButton(
                    card,
                    text="Select Specialist ➔",
                    width=140,
                    height=34,
                    font=FONT_SMALL_BOLD,
                    fg_color=PALETTE["dark"]["accent"],
                    hover_color=PALETTE["dark"]["accent_hover"],
                    command=lambda st=staff: self.on_staff_selected(st),
                ).pack(side="right", padx=16)

    def on_staff_selected(self, staff: Staff):
        self.selected_staff = staff
        self.render_step_3_date_and_slots()

    # =========================================================================
    # STEP 3: CHOOSE DATE & SLOTS
    # =========================================================================
    def render_step_3_date_and_slots(self):
        self.clear_container()
        self.update_stepper(3)

        wrapper = ctk.CTkFrame(
            self.step_container,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        wrapper.pack(fill="both", expand=True)

        head = ctk.CTkFrame(wrapper, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(
            head,
            text=f"Step 3: Pick Date & Time Slot for {self.selected_staff.name}",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            head,
            text="⬅ Back to Specialist",
            width=140,
            height=30,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.render_step_2_staff,
        ).pack(side="right")

        # Date Selector Chips (Next 7 days)
        date_bar = ctk.CTkFrame(wrapper, fg_color="transparent")
        date_bar.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            date_bar,
            text="Select Date:",
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))

        chips_scroll = ctk.CTkFrame(date_bar, fg_color="transparent")
        chips_scroll.pack(fill="x")

        self.date_buttons = []
        today = date.today()
        for i in range(7):
            d = today + timedelta(days=i)
            d_str = d.isoformat()
            label_text = d.strftime("%a, %b %d")
            if i == 0:
                label_text = f"Today\n{d.strftime('%b %d')}"
            elif i == 1:
                label_text = f"Tomorrow\n{d.strftime('%b %d')}"
            else:
                label_text = f"{d.strftime('%a')}\n{d.strftime('%b %d')}"

            is_active = (d_str == self.selected_date)
            btn = ctk.CTkButton(
                chips_scroll,
                text=label_text,
                font=FONT_SMALL_BOLD,
                width=85,
                height=44,
                fg_color=PALETTE["dark"]["accent"] if is_active else PALETTE["dark"]["bg_primary"],
                hover_color=PALETTE["dark"]["accent_hover"],
                command=lambda d_val=d_str: self.change_selected_date(d_val),
            )
            btn.pack(side="left", padx=4)
            self.date_buttons.append((d_str, btn))

        # Dynamic Slots Grid Container
        ctk.CTkLabel(
            wrapper,
            text="Available Time Slots (Calculated in real-time, zero overlaps):",
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w", padx=20, pady=(10, 6))

        self.slots_scroll = ctk.CTkScrollableFrame(
            wrapper,
            height=260,
            fg_color=PALETTE["dark"]["bg_primary"],
            corner_radius=8,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.slots_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self.load_slots_for_date()

    def change_selected_date(self, new_date: str):
        self.selected_date = new_date
        for d_str, btn in self.date_buttons:
            if d_str == new_date:
                btn.configure(fg_color=PALETTE["dark"]["accent"])
            else:
                btn.configure(fg_color=PALETTE["dark"]["bg_primary"])
        self.load_slots_for_date()

    def load_slots_for_date(self):
        """Query AvailabilityEngine for available slots."""
        for widget in self.slots_scroll.winfo_children():
            widget.destroy()

        with get_db() as session:
            slots = AvailabilityEngine.get_available_slots(
                session=session,
                staff_id=self.selected_staff.id,
                service_id=self.selected_service.id,
                target_date=self.selected_date,
                slot_interval=30,
            )

        if not slots:
            msg_box = ctk.CTkFrame(self.slots_scroll, fg_color="transparent")
            msg_box.pack(pady=40)
            ctk.CTkLabel(
                msg_box,
                text="❌ No available slots on this date.",
                font=FONT_BODY_BOLD,
                text_color=PALETTE["dark"]["warning"],
            ).pack()
            ctk.CTkLabel(
                msg_box,
                text="The specialist may be off duty, on approved leave, or fully booked.",
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_muted"],
            ).pack(pady=(4, 0))
            return

        # Render slots in grid of buttons
        grid_frame = ctk.CTkFrame(self.slots_scroll, fg_color="transparent")
        grid_frame.pack(fill="x", padx=10, pady=10)

        cols = 4
        for idx, slot in enumerate(slots):
            r = idx // cols
            c = idx % cols

            slot_btn = ctk.CTkButton(
                grid_frame,
                text=f"🕐 {slot['start']} - {slot['end']}",
                font=FONT_SMALL_BOLD,
                height=38,
                fg_color=PALETTE["dark"]["card_secondary"],
                hover_color=PALETTE["dark"]["accent"],
                command=lambda sl=slot: self.on_slot_selected(sl),
            )
            slot_btn.grid(row=r, column=c, padx=6, pady=6, sticky="ew")
            grid_frame.grid_columnconfigure(c, weight=1)

    def on_slot_selected(self, slot: dict):
        self.selected_slot = slot
        self.render_step_4_customer_confirm()

    # =========================================================================
    # STEP 4: CUSTOMER DETAILS & FINAL CONFIRMATION
    # =========================================================================
    def render_step_4_customer_confirm(self):
        self.clear_container()
        self.update_stepper(4)

        scroll = ctk.CTkScrollableFrame(
            self.step_container,
            fg_color=PALETTE["dark"]["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        scroll.pack(fill="both", expand=True)

        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(
            head,
            text="Step 4: Client Information & Booking Confirmation",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            head,
            text="⬅ Back to Slots",
            width=120,
            height=30,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.render_step_3_date_and_slots,
        ).pack(side="right")

        # Two-column layout: Left = Summary Card, Right = Client Form
        cols_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cols_frame.pack(fill="both", expand=True, padx=20, pady=0)
        cols_frame.grid_columnconfigure(0, weight=1)
        cols_frame.grid_columnconfigure(1, weight=1)

        # 1. Summary Card
        summary_card = ctk.CTkFrame(
            cols_frame,
            fg_color=PALETTE["dark"]["bg_primary"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        summary_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew", pady=6)

        ctk.CTkLabel(
            summary_card,
            text="Appointment Summary",
            font=FONT_BODY_BOLD,
            text_color=PALETTE["dark"]["accent"],
        ).pack(anchor="w", padx=16, pady=(16, 10))

        items = [
            ("Service", self.selected_service.name),
            ("Specialist", self.selected_staff.name),
            ("Date", self.selected_date),
            ("Time Window", f"{self.selected_slot['start']} - {self.selected_slot['end']}"),
            ("Duration", f"{self.selected_service.duration_minutes} minutes"),
            ("Standard Price", f"${self.selected_service.price:.2f}"),
        ]

        for k, v in items:
            row = ctk.CTkFrame(summary_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text=k, font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"]).pack(side="left")
            ctk.CTkLabel(row, text=v, font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_primary"]).pack(side="right")

        # 2. Client Details Form
        form_card = ctk.CTkFrame(
            cols_frame,
            fg_color=PALETTE["dark"]["bg_primary"],
            corner_radius=10,
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        form_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew", pady=6)

        ctk.CTkLabel(
            form_card,
            text="Client Details",
            font=FONT_BODY_BOLD,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w", padx=16, pady=(16, 10))

        # Select Existing Customer Option
        with get_db() as session:
            existing_customers = session.query(Customer).order_by(Customer.name.asc()).all()
            cust_names = ["-- Or Select Existing Client --"] + [f"{c.name} ({c.phone})" for c in existing_customers]

        self.cust_dropdown = ctk.CTkOptionMenu(
            form_card,
            values=cust_names,
            height=36,
            font=FONT_SMALL,
            command=self.on_existing_customer_selected,
        )
        self.cust_dropdown.pack(fill="x", padx=16, pady=(0, 10))

        # Client Name
        ctk.CTkLabel(form_card, text="Full Name *", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=16)
        self.cust_name_entry = ctk.CTkEntry(form_card, height=36, font=FONT_BODY)
        self.cust_name_entry.pack(fill="x", padx=16, pady=(2, 8))

        # Phone
        ctk.CTkLabel(form_card, text="Phone Number *", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=16)
        self.cust_phone_entry = ctk.CTkEntry(form_card, height=36, font=FONT_BODY)
        self.cust_phone_entry.pack(fill="x", padx=16, pady=(2, 8))

        # Email
        ctk.CTkLabel(form_card, text="Email Address (for confirmation)", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=16)
        self.cust_email_entry = ctk.CTkEntry(form_card, height=36, font=FONT_BODY)
        self.cust_email_entry.pack(fill="x", padx=16, pady=(2, 8))

        # Notes
        ctk.CTkLabel(form_card, text="Appointment Notes", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=16)
        self.notes_entry = ctk.CTkEntry(form_card, height=36, font=FONT_BODY)
        self.notes_entry.pack(fill="x", padx=16, pady=(2, 16))

        # Final Submit Button
        self.confirm_btn = ctk.CTkButton(
            scroll,
            text="✨ Confirm & Schedule Appointment",
            height=44,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["success"],
            hover_color="#059669",
            command=self.confirm_booking,
        )
        self.confirm_btn.pack(fill="x", padx=20, pady=(16, 20))

    def on_existing_customer_selected(self, choice: str):
        if choice.startswith("--"):
            return
        # Extract phone from parenthesis
        phone = choice.split("(")[-1].replace(")", "").strip()
        with get_db() as session:
            c = session.query(Customer).filter(Customer.phone == phone).first()
            if c:
                self.selected_customer = c
                self.cust_name_entry.delete(0, "end")
                self.cust_name_entry.insert(0, c.name)
                self.cust_phone_entry.delete(0, "end")
                self.cust_phone_entry.insert(0, c.phone)
                self.cust_email_entry.delete(0, "end")
                self.cust_email_entry.insert(0, c.email or "")

    def confirm_booking(self):
        """Create customer if new, then create appointment inside transaction."""
        c_name = self.cust_name_entry.get().strip()
        c_phone = self.cust_phone_entry.get().strip()
        c_email = self.cust_email_entry.get().strip()
        notes = self.notes_entry.get().strip()

        if not c_name or not c_phone:
            show_toast(self.winfo_toplevel(), "Please enter client name and phone.", level="warning")
            return

        with get_db() as session:
            # 1. Lookup or create customer
            customer = session.query(Customer).filter(Customer.phone == c_phone).first()
            if not customer:
                customer = Customer(
                    name=c_name,
                    phone=c_phone,
                    email=c_email or None,
                    notes=notes or None,
                )
                session.add(customer)
                session.flush()
            else:
                customer.name = c_name
                if c_email:
                    customer.email = c_email

            # 2. Book appointment using BookingService (double-booking validation inside!)
            ok, appointment, err = BookingService.create_appointment(
                session=session,
                customer_id=customer.id,
                staff_id=self.selected_staff.id,
                service_id=self.selected_service.id,
                booking_date=self.selected_date,
                start_time=self.selected_slot["start"],
                end_time=self.selected_slot["end"],
                notes=notes or None,
            )

            if not ok:
                show_toast(self.winfo_toplevel(), f"Booking Collision: {err}", level="error")
                return

            app_ref = appointment.appointment_number

            # Trigger optional email confirmation
            if c_email:
                NotificationService.send_booking_confirmation(session, appointment.id)

        show_toast(
            self.winfo_toplevel(),
            f"🎉 Success! Appointment booked: {app_ref}",
            level="success",
        )

        if self.on_booking_complete:
            self.on_booking_complete(app_ref)
