"""Customer View with Service Selection, Specialist Choice, and Real-Time Slot Booking."""

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
from src.ui.views.staff_view import StaffView


class CustomerBookingView(ctk.CTkFrame):
    """
    Dedicated Customer Section:
    1. Customer chooses their service of choice.
    2. View dynamically displays qualified specialist person(s) offering that service.
    3. Customer selects their preferred specialist person.
    4. View calculates and displays real-time available conflict-free time slots for that service & specialist.
    5. Customer confirms and books their appointment seamlessly.
    Also provides a tab to access Specialist Admin management so existing features are 100% preserved.
    """

    def __init__(
        self,
        master,
        on_navigate: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_navigate = on_navigate

        # Active state
        self.active_tab = "customer_booking"  # 'customer_booking' or 'staff_admin'
        self.selected_service: Optional[Service] = None
        self.selected_staff: Optional[Staff] = None
        self.selected_date: str = date.today().isoformat()
        self.selected_slot: Optional[Dict[str, str]] = None
        self.search_service_query = ""
        self.selected_category = "All"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Header with Mode Toggle
        self.create_header()

        # 2. Horizontal divider bar
        self.h_bar = ctk.CTkFrame(
            self,
            height=2,
            fg_color=PALETTE["dark"]["border"],
            corner_radius=1,
        )
        self.h_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 14))

        # 3. Main Body Container
        self.body_container = ctk.CTkFrame(self, fg_color="transparent")
        self.body_container.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.body_container.grid_columnconfigure(0, weight=1)
        self.body_container.grid_rowconfigure(0, weight=1)

        # Render customer booking workflow
        self.render_view()

    def create_header(self):
        """Header with title, subtitle, and seamless switch between Customer Portal and Staff Admin."""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Customer Booking Portal",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Select your desired service, pick your preferred specialist, and book available time slots",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

        # Top Right: Tab Switcher (Customer Booking vs Specialist Admin)
        tab_box = ctk.CTkFrame(header, fg_color=PALETTE["dark"]["card_bg"], corner_radius=8)
        tab_box.pack(side="right")

        self.btn_customer_tab = ctk.CTkButton(
            tab_box,
            text="👤 Customer Booking",
            width=160,
            height=34,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            hover_color=PALETTE["dark"]["accent_hover"],
            command=lambda: self.switch_tab("customer_booking"),
        )
        self.btn_customer_tab.pack(side="left", padx=3, pady=3)

        self.btn_staff_tab = ctk.CTkButton(
            tab_box,
            text="🩺 Specialist Profiles & Shifts",
            width=200,
            height=34,
            font=FONT_SMALL_BOLD,
            fg_color="transparent",
            hover_color=PALETTE["dark"]["card_secondary"],
            text_color=PALETTE["dark"]["text_secondary"],
            command=lambda: self.switch_tab("staff_admin"),
        )
        self.btn_staff_tab.pack(side="left", padx=3, pady=3)

    def switch_tab(self, tab_key: str):
        """Switch between Customer Booking and Staff Admin management."""
        self.active_tab = tab_key
        if tab_key == "customer_booking":
            self.btn_customer_tab.configure(
                fg_color=PALETTE["dark"]["accent"],
                text_color="#FFFFFF",
            )
            self.btn_staff_tab.configure(
                fg_color="transparent",
                text_color=PALETTE["dark"]["text_secondary"],
            )
        else:
            self.btn_customer_tab.configure(
                fg_color="transparent",
                text_color=PALETTE["dark"]["text_secondary"],
            )
            self.btn_staff_tab.configure(
                fg_color=PALETTE["dark"]["accent"],
                text_color="#FFFFFF",
            )
        self.render_view()

    def render_view(self):
        """Clear body and render active view."""
        for w in self.body_container.winfo_children():
            w.destroy()

        if self.active_tab == "staff_admin":
            # Render full existing Staff Management View to preserve all features
            staff_admin_view = StaffView(self.body_container)
            staff_admin_view.pack(fill="both", expand=True)
        else:
            self.render_customer_flow()

    def render_customer_flow(self):
        """
        Build the 3-column reactive customer booking experience:
        Col 0: Service Selection
        Col 1: Specialists for Selected Service
        Col 2: Available Slots & Booking Form
        """
        grid_frame = ctk.CTkFrame(self.body_container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)

        grid_frame.grid_columnconfigure(0, weight=3)  # Services
        grid_frame.grid_columnconfigure(1, weight=3)  # Specialists
        grid_frame.grid_columnconfigure(2, weight=4)  # Slots & Booking
        grid_frame.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # COLUMN 0: SELECT SERVICE
        # -------------------------------------------------------------
        self.create_services_column(grid_frame)

        # -------------------------------------------------------------
        # COLUMN 1: SELECT SPECIALIST PERSON FOR SERVICE
        # -------------------------------------------------------------
        self.create_specialists_column(grid_frame)

        # -------------------------------------------------------------
        # COLUMN 2: AVAILABLE SLOTS & BOOKING CONFIRMATION
        # -------------------------------------------------------------
        self.create_slots_column(grid_frame)

    # =========================================================================
    # COLUMN 0: SERVICE SELECTION
    # =========================================================================
    def create_services_column(self, parent):
        col_frame = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        col_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
        col_frame.grid_columnconfigure(0, weight=1)
        col_frame.grid_rowconfigure(2, weight=1)

        # Header
        head_box = ctk.CTkFrame(col_frame, fg_color="transparent")
        head_box.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            head_box,
            text="1️⃣ Choose Service",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            head_box,
            text="Select the service you wish to book",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

        # Search bar
        search_box = ctk.CTkFrame(col_frame, fg_color="transparent")
        search_box.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))

        self.service_search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="🔍 Search service name...",
            height=34,
            font=FONT_SMALL,
            fg_color=PALETTE["dark"]["bg_primary"],
            border_color=PALETTE["dark"]["border"],
        )
        self.service_search_entry.pack(fill="x")
        self.service_search_entry.bind("<KeyRelease>", self.on_service_search_changed)

        # Scrollable Feed of Services
        self.services_feed = ctk.CTkScrollableFrame(col_frame, fg_color="transparent")
        self.services_feed.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.populate_services_list()

    def on_service_search_changed(self, event=None):
        self.search_service_query = self.service_search_entry.get().strip().lower()
        self.populate_services_list()

    def populate_services_list(self):
        for w in self.services_feed.winfo_children():
            w.destroy()

        with get_db() as session:
            services = session.query(Service).filter(Service.is_active == True).order_by(Service.category.asc(), Service.name.asc()).all()

            cur_sym = "$"
            cur_setting = session.query(BusinessSetting).filter(BusinessSetting.key == "currency_symbol").first()
            if cur_setting:
                cur_sym = cur_setting.value

            if self.search_service_query:
                services = [s for s in services if self.search_service_query in s.name.lower() or self.search_service_query in s.category.lower()]

            if not services:
                empty = ctk.CTkFrame(self.services_feed, fg_color="transparent")
                empty.pack(pady=30)
                ctk.CTkLabel(empty, text="No services found.", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"]).pack()
                return

            # Group or list
            for srv in services:
                is_selected = (self.selected_service and self.selected_service.id == srv.id)

                card = ctk.CTkFrame(
                    self.services_feed,
                    corner_radius=8,
                    fg_color=PALETTE["dark"]["card_secondary"] if is_selected else PALETTE["dark"]["bg_primary"],
                    border_width=2 if is_selected else 1,
                    border_color=PALETTE["dark"]["accent"] if is_selected else PALETTE["dark"]["border"],
                )
                card.pack(fill="x", pady=4, padx=4)

                # Content inside card
                top_row = ctk.CTkFrame(card, fg_color="transparent")
                top_row.pack(fill="x", padx=10, pady=(8, 2))

                ctk.CTkLabel(
                    top_row,
                    text=srv.name,
                    font=FONT_BODY_BOLD,
                    text_color=PALETTE["dark"]["text_primary"],
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    top_row,
                    text=f"{cur_sym}{srv.price:.2f}",
                    font=FONT_BODY_BOLD,
                    text_color=PALETTE["dark"]["success"],
                ).pack(side="right")

                # Category & Duration
                sub_row = ctk.CTkFrame(card, fg_color="transparent")
                sub_row.pack(fill="x", padx=10, pady=(0, 6))

                ctk.CTkLabel(
                    sub_row,
                    text=f"📂 {srv.category}   •   ⏱ {srv.duration_minutes}m",
                    font=FONT_SMALL,
                    text_color=PALETTE["dark"]["text_secondary"],
                    anchor="w",
                ).pack(side="left")

                if is_selected:
                    ctk.CTkLabel(
                        sub_row,
                        text="✓ Selected",
                        font=FONT_SMALL_BOLD,
                        text_color=PALETTE["dark"]["accent"],
                    ).pack(side="right")

                # Description
                if srv.description:
                    desc_text = srv.description[:75] + ("..." if len(srv.description) > 75 else "")
                    ctk.CTkLabel(
                        card,
                        text=desc_text,
                        font=("Segoe UI", 9),
                        text_color=PALETTE["dark"]["text_muted"],
                        anchor="w",
                        justify="left",
                        wraplength=250,
                    ).pack(fill="x", padx=10, pady=(0, 8))

                # Make card and its labels clickable
                def make_click_handler(s_item=srv):
                    return lambda e: self.select_service(s_item)

                card.bind("<Button-1>", make_click_handler(srv))
                for child in card.winfo_children():
                    child.bind("<Button-1>", make_click_handler(srv))
                    for sub_c in child.winfo_children():
                        sub_c.bind("<Button-1>", make_click_handler(srv))

    def select_service(self, service: Service):
        """User selected a service."""
        self.selected_service = service
        # Reset staff and slot when service changes
        self.selected_staff = None
        self.selected_slot = None
        self.populate_services_list()
        self.populate_specialists_list()
        self.populate_slots_list()

    # =========================================================================
    # COLUMN 1: SPECIALIST PERSON FOR SERVICE
    # =========================================================================
    def create_specialists_column(self, parent):
        self.specialists_col_frame = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.specialists_col_frame.grid(row=0, column=1, sticky="nsew", padx=4, pady=0)
        self.specialists_col_frame.grid_columnconfigure(0, weight=1)
        self.specialists_col_frame.grid_rowconfigure(1, weight=1)

        # Header
        self.specialists_head_box = ctk.CTkFrame(self.specialists_col_frame, fg_color="transparent")
        self.specialists_head_box.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))

        self.specialists_title_label = ctk.CTkLabel(
            self.specialists_head_box,
            text="2️⃣ Choose Specialist",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        )
        self.specialists_title_label.pack(anchor="w")

        self.specialists_sub_label = ctk.CTkLabel(
            self.specialists_head_box,
            text="Specialists providing the selected service",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        )
        self.specialists_sub_label.pack(anchor="w")

        # Scrollable Feed of Specialists
        self.specialists_feed = ctk.CTkScrollableFrame(self.specialists_col_frame, fg_color="transparent")
        self.specialists_feed.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.populate_specialists_list()

    def populate_specialists_list(self):
        for w in self.specialists_feed.winfo_children():
            w.destroy()

        if not self.selected_service:
            # Prompt user to select service first
            prompt_box = ctk.CTkFrame(self.specialists_feed, fg_color="transparent")
            prompt_box.pack(pady=60, padx=16)

            ctk.CTkLabel(
                prompt_box,
                text="👈 Select Service First",
                font=FONT_BODY_BOLD,
                text_color=PALETTE["dark"]["text_secondary"],
            ).pack()

            ctk.CTkLabel(
                prompt_box,
                text="Select a service from column 1 to view all specialists offering that service.",
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_muted"],
                wraplength=220,
                justify="center",
            ).pack(pady=(6, 0))

            self.specialists_sub_label.configure(text="Please choose a service first")
            return

        self.specialists_sub_label.configure(text=f"Specialists for '{self.selected_service.name}'")

        with get_db() as session:
            service = session.query(Service).filter(Service.id == self.selected_service.id).first()
            if not service:
                return

            # Qualified specialists linked to this service
            qualified_staff = [s for s in service.staff_members if s.is_active]
            # If no staff specifically linked, show all active staff as fallback
            if not qualified_staff:
                qualified_staff = session.query(Staff).filter(Staff.is_active == True).order_by(Staff.name.asc()).all()

            if not qualified_staff:
                ctk.CTkLabel(
                    self.specialists_feed,
                    text="No active specialists currently available for this service.",
                    font=FONT_SMALL,
                    text_color=PALETTE["dark"]["warning"],
                ).pack(pady=40)
                return

            for staff in qualified_staff:
                is_selected = (self.selected_staff and self.selected_staff.id == staff.id)

                card = ctk.CTkFrame(
                    self.specialists_feed,
                    corner_radius=8,
                    fg_color=PALETTE["dark"]["card_secondary"] if is_selected else PALETTE["dark"]["bg_primary"],
                    border_width=2 if is_selected else 1,
                    border_color=PALETTE["dark"]["accent"] if is_selected else PALETTE["dark"]["border"],
                )
                card.pack(fill="x", pady=5, padx=4)

                top_info = ctk.CTkFrame(card, fg_color="transparent")
                top_info.pack(fill="x", padx=10, pady=(10, 4))

                # Avatar Circle / Badge
                avatar = ctk.CTkLabel(
                    top_info,
                    text="👤",
                    font=("Segoe UI", 16),
                    width=38,
                    height=38,
                    corner_radius=8,
                    fg_color=staff.color_code or PALETTE["dark"]["accent"],
                    text_color="#FFFFFF",
                )
                avatar.pack(side="left", padx=(0, 10))

                text_col = ctk.CTkFrame(top_info, fg_color="transparent")
                text_col.pack(side="left", fill="both", expand=True)

                ctk.CTkLabel(
                    text_col,
                    text=staff.name,
                    font=FONT_BODY_BOLD,
                    text_color=PALETTE["dark"]["text_primary"],
                    anchor="w",
                ).pack(fill="x")

                ctk.CTkLabel(
                    text_col,
                    text=staff.role_title,
                    font=FONT_SMALL,
                    text_color=PALETTE["dark"]["accent"],
                    anchor="w",
                ).pack(fill="x")

                # Specialties badge or bio
                if staff.specialties:
                    ctk.CTkLabel(
                        card,
                        text=f"✨ {staff.specialties}",
                        font=("Segoe UI", 9),
                        text_color=PALETTE["dark"]["text_secondary"],
                        anchor="w",
                        justify="left",
                        wraplength=230,
                    ).pack(fill="x", padx=10, pady=(0, 4))

                # Selection indicator row
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=10, pady=(2, 8))

                if is_selected:
                    ctk.CTkLabel(
                        btn_row,
                        text="✓ Selected Specialist",
                        font=FONT_SMALL_BOLD,
                        text_color=PALETTE["dark"]["accent"],
                    ).pack(side="right")
                else:
                    ctk.CTkLabel(
                        btn_row,
                        text="Click to select ➔",
                        font=FONT_SMALL,
                        text_color=PALETTE["dark"]["text_muted"],
                    ).pack(side="right")

                def make_staff_click(st_item=staff):
                    return lambda e: self.select_staff(st_item)

                card.bind("<Button-1>", make_staff_click(staff))
                for child in card.winfo_children():
                    child.bind("<Button-1>", make_staff_click(staff))
                    for sub_c in child.winfo_children():
                        sub_c.bind("<Button-1>", make_staff_click(staff))

    def select_staff(self, staff: Staff):
        """User selected their preferred specialist."""
        self.selected_staff = staff
        self.selected_slot = None
        self.populate_specialists_list()
        self.populate_slots_list()

    # =========================================================================
    # COLUMN 2: AVAILABLE SLOTS & BOOKING CONFIRMATION
    # =========================================================================
    def create_slots_column(self, parent):
        self.slots_col_frame = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.slots_col_frame.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=0)
        self.slots_col_frame.grid_columnconfigure(0, weight=1)
        self.slots_col_frame.grid_rowconfigure(2, weight=1)

        # Header
        self.slots_head_box = ctk.CTkFrame(self.slots_col_frame, fg_color="transparent")
        self.slots_head_box.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

        self.slots_title_label = ctk.CTkLabel(
            self.slots_head_box,
            text="3️⃣ Available Slots & Booking",
            font=FONT_HEADING,
            text_color=PALETTE["dark"]["text_primary"],
        )
        self.slots_title_label.pack(anchor="w")

        self.slots_sub_label = ctk.CTkLabel(
            self.slots_head_box,
            text="Real-time conflict-free slots for chosen specialist",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        )
        self.slots_sub_label.pack(anchor="w")

        # Date Selector Bar
        self.date_bar_frame = ctk.CTkFrame(self.slots_col_frame, fg_color="transparent")
        self.date_bar_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 6))

        # Scrollable Feed of Slots and Booking Form
        self.slots_feed = ctk.CTkScrollableFrame(self.slots_col_frame, fg_color="transparent")
        self.slots_feed.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 10))

        self.populate_slots_list()

    def populate_slots_list(self):
        for w in self.date_bar_frame.winfo_children():
            w.destroy()
        for w in self.slots_feed.winfo_children():
            w.destroy()

        if not self.selected_service or not self.selected_staff:
            # Inform user what to do next
            prompt_box = ctk.CTkFrame(self.slots_feed, fg_color="transparent")
            prompt_box.pack(pady=60, padx=16)

            ctk.CTkLabel(
                prompt_box,
                text="👈 Select Service & Specialist",
                font=FONT_BODY_BOLD,
                text_color=PALETTE["dark"]["text_secondary"],
            ).pack()

            msg = "Please select both a service and a specialist to compute and view live available time slots."
            ctk.CTkLabel(
                prompt_box,
                text=msg,
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_muted"],
                wraplength=260,
                justify="center",
            ).pack(pady=(6, 0))

            self.slots_sub_label.configure(text="Awaiting service and specialist selection")
            return

        self.slots_sub_label.configure(
            text=f"Slots for {self.selected_staff.name} — {self.selected_service.name} ({self.selected_service.duration_minutes}m)"
        )

        # 1. Render Date Selector Chips (Next 7 days)
        ctk.CTkLabel(
            self.date_bar_frame,
            text="Select Appointment Date:",
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w", pady=(0, 4))

        chips_row = ctk.CTkFrame(self.date_bar_frame, fg_color="transparent")
        chips_row.pack(fill="x")

        today = date.today()
        self.date_buttons = []
        for i in range(7):
            d = today + timedelta(days=i)
            d_str = d.isoformat()
            if i == 0:
                lbl = f"Today\n{d.strftime('%b %d')}"
            elif i == 1:
                lbl = f"Tmrw\n{d.strftime('%b %d')}"
            else:
                lbl = f"{d.strftime('%a')}\n{d.strftime('%b %d')}"

            is_active = (d_str == self.selected_date)
            btn = ctk.CTkButton(
                chips_row,
                text=lbl,
                font=("Segoe UI", 9, "bold"),
                width=48,
                height=38,
                fg_color=PALETTE["dark"]["accent"] if is_active else PALETTE["dark"]["bg_primary"],
                hover_color=PALETTE["dark"]["accent_hover"],
                text_color="#FFFFFF" if is_active else PALETTE["dark"]["text_secondary"],
                command=lambda ds=d_str: self.change_date(ds),
            )
            btn.pack(side="left", padx=2, expand=True, fill="x")
            self.date_buttons.append((d_str, btn))

        # 2. Compute Available Slots via AvailabilityEngine
        with get_db() as session:
            slots = AvailabilityEngine.get_available_slots(
                session=session,
                staff_id=self.selected_staff.id,
                service_id=self.selected_service.id,
                target_date=self.selected_date,
                slot_interval=15,
            )

        slots_section = ctk.CTkFrame(self.slots_feed, fg_color="transparent")
        slots_section.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(
            slots_section,
            text=f"Available Slots on {self.selected_date}:",
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w", pady=(4, 6))

        if not slots:
            no_slot_box = ctk.CTkFrame(slots_section, corner_radius=8, fg_color=PALETTE["dark"]["bg_primary"])
            no_slot_box.pack(fill="x", pady=12, padx=4)

            ctk.CTkLabel(
                no_slot_box,
                text="❌ No Slots Available on This Date",
                font=FONT_BODY_BOLD,
                text_color=PALETTE["dark"]["warning"],
            ).pack(pady=(12, 2))

            ctk.CTkLabel(
                no_slot_box,
                text=f"{self.selected_staff.name} is either fully booked, on approved leave, or off-duty. Please select another date above.",
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_secondary"],
                wraplength=260,
                justify="center",
            ).pack(padx=10, pady=(0, 12))
            return

        # Render Slot Grid
        grid_slots = ctk.CTkFrame(slots_section, fg_color="transparent")
        grid_slots.pack(fill="x")

        cols = 3
        for idx, slot in enumerate(slots):
            r = idx // cols
            c = idx % cols

            is_slot_sel = (self.selected_slot and self.selected_slot["start"] == slot["start"])

            btn = ctk.CTkButton(
                grid_slots,
                text=f"🕐 {slot['start']}-{slot['end']}",
                font=FONT_SMALL_BOLD,
                height=32,
                fg_color=PALETTE["dark"]["accent"] if is_slot_sel else PALETTE["dark"]["bg_primary"],
                hover_color=PALETTE["dark"]["accent_hover"],
                text_color="#FFFFFF" if is_slot_sel else PALETTE["dark"]["text_primary"],
                border_width=1,
                border_color=PALETTE["dark"]["accent"] if is_slot_sel else PALETTE["dark"]["border"],
                command=lambda sl=slot: self.select_slot(sl),
            )
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="ew")
            grid_slots.grid_columnconfigure(c, weight=1)

        # 3. Render Booking Form if a slot is selected
        if self.selected_slot:
            self.render_booking_form()

    def change_date(self, new_date: str):
        self.selected_date = new_date
        self.selected_slot = None
        self.populate_slots_list()

    def select_slot(self, slot: dict):
        self.selected_slot = slot
        self.populate_slots_list()

    def render_booking_form(self):
        """Render client details input and final confirm button."""
        form_wrapper = ctk.CTkFrame(
            self.slots_feed,
            corner_radius=10,
            fg_color=PALETTE["dark"]["bg_primary"],
            border_width=1,
            border_color=PALETTE["dark"]["accent"],
        )
        form_wrapper.pack(fill="x", pady=(14, 10), padx=4)

        # Summary Badge
        summary_top = ctk.CTkFrame(form_wrapper, fg_color="transparent")
        summary_top.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(
            summary_top,
            text="Selected Appointment Time",
            font=FONT_SMALL_BOLD,
            text_color=PALETTE["dark"]["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            summary_top,
            text=f"📅 {self.selected_date}   •   🕐 {self.selected_slot['start']} to {self.selected_slot['end']}   •   ${self.selected_service.price:.2f}",
            font=FONT_BODY_BOLD,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w", pady=(2, 6))

        # Client selection or creation
        with get_db() as session:
            existing_customers = session.query(Customer).order_by(Customer.name.asc()).all()
            cust_names = ["-- Or Select Existing Client --"] + [f"{c.name} ({c.phone})" for c in existing_customers]

        self.client_dropdown = ctk.CTkOptionMenu(
            form_wrapper,
            values=cust_names,
            height=32,
            font=FONT_SMALL,
            fg_color=PALETTE["dark"]["card_secondary"],
            button_color=PALETTE["dark"]["accent"],
            dropdown_fg_color=PALETTE["dark"]["card_bg"],
            command=self.on_existing_client_chosen,
        )
        self.client_dropdown.pack(fill="x", padx=12, pady=(0, 8))

        # Customer Name
        ctk.CTkLabel(form_wrapper, text="Customer Full Name *", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=12)
        self.cust_name_ent = ctk.CTkEntry(form_wrapper, height=32, font=FONT_SMALL)
        self.cust_name_ent.pack(fill="x", padx=12, pady=(2, 6))

        # Customer Phone
        ctk.CTkLabel(form_wrapper, text="Phone Number *", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=12)
        self.cust_phone_ent = ctk.CTkEntry(form_wrapper, height=32, font=FONT_SMALL)
        self.cust_phone_ent.pack(fill="x", padx=12, pady=(2, 6))

        # Customer Email
        ctk.CTkLabel(form_wrapper, text="Email Address", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=12)
        self.cust_email_ent = ctk.CTkEntry(form_wrapper, height=32, font=FONT_SMALL)
        self.cust_email_ent.pack(fill="x", padx=12, pady=(2, 6))

        # Notes
        ctk.CTkLabel(form_wrapper, text="Special Requests / Notes", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=12)
        self.cust_notes_ent = ctk.CTkEntry(form_wrapper, height=32, font=FONT_SMALL)
        self.cust_notes_ent.pack(fill="x", padx=12, pady=(2, 12))

        # Confirm Button
        ctk.CTkButton(
            form_wrapper,
            text="✨ Schedule Appointment Now",
            height=40,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["success"],
            hover_color="#059669",
            command=self.confirm_customer_booking,
        ).pack(fill="x", padx=12, pady=(0, 12))

    def on_existing_client_chosen(self, choice: str):
        if choice.startswith("--"):
            return
        phone = choice.split("(")[-1].replace(")", "").strip()
        with get_db() as session:
            c = session.query(Customer).filter(Customer.phone == phone).first()
            if c:
                self.cust_name_ent.delete(0, "end")
                self.cust_name_ent.insert(0, c.name)
                self.cust_phone_ent.delete(0, "end")
                self.cust_phone_ent.insert(0, c.phone)
                self.cust_email_ent.delete(0, "end")
                self.cust_email_ent.insert(0, c.email or "")

    def confirm_customer_booking(self):
        """Execute booking transaction and show success card."""
        c_name = self.cust_name_ent.get().strip()
        c_phone = self.cust_phone_ent.get().strip()
        c_email = self.cust_email_ent.get().strip()
        notes = self.cust_notes_ent.get().strip()

        if not c_name or not c_phone:
            show_toast(self.winfo_toplevel(), "Please provide both Name and Phone Number.", level="warning")
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

            # 2. Book with collision protection
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
                show_toast(self.winfo_toplevel(), f"Collision Error: {err}", level="error")
                return

            app_ref = appointment.appointment_number

            # Trigger notification
            if c_email:
                NotificationService.send_booking_confirmation(session, appointment.id)

        show_toast(
            self.winfo_toplevel(),
            f"🎉 Appointment Booked! Ref: {app_ref}",
            level="success",
        )

        # Clear active slot and refresh
        self.selected_slot = None
        self.populate_slots_list()
