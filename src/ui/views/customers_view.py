"""Customer Management View with Profile Cards and Booking History."""

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
from src.database.models import Customer, Appointment
from src.core.audit_logger import AuditLogger
from src.config import STATUS_COLORS


class CustomersView(ctk.CTkFrame):
    """Customer directory with appointment history and notes."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.selected_customer_id: Optional[int] = None

        self.grid_columnconfigure(0, weight=4)  # Left list
        self.grid_columnconfigure(1, weight=6)  # Right profile
        self.grid_rowconfigure(1, weight=1)

        # Header Row
        self.create_header()

        # Left Column: Search & List
        self.create_left_list()

        # Right Column: Detailed Profile
        self.create_right_profile()

        self.refresh_customer_list()

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Client Profiles & History",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Manage customer contact records, notes, and booking histories",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="➕ Add New Client",
            width=140,
            height=36,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            hover_color=PALETTE["dark"]["accent_hover"],
            command=self.open_add_customer_modal,
        ).pack(side="right")

    def create_left_list(self):
        """Left pane with search and client rows."""
        left_box = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        left_box.grid(row=1, column=0, sticky="nsew", padx=(24, 10), pady=(0, 20))
        left_box.grid_columnconfigure(0, weight=1)
        left_box.grid_rowconfigure(1, weight=1)

        # Search bar
        self.search_entry = ctk.CTkEntry(
            left_box,
            placeholder_text="🔍 Search clients by name, phone, or email...",
            height=38,
            font=FONT_BODY,
            fg_color=PALETTE["dark"]["bg_primary"],
            border_color=PALETTE["dark"]["border"],
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_customer_list())

        # List Feed
        self.customers_feed = ctk.CTkScrollableFrame(left_box, fg_color="transparent")
        self.customers_feed.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def create_right_profile(self):
        """Right pane showing detailed selected client profile."""
        self.right_box = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            border_width=1,
            border_color=PALETTE["dark"]["border"],
        )
        self.right_box.grid(row=1, column=1, sticky="nsew", padx=(10, 24), pady=(0, 20))

    def refresh_customer_list(self):
        """Populate customer cards on left pane."""
        for w in self.customers_feed.winfo_children():
            w.destroy()

        search_query = self.search_entry.get().strip()

        with get_db() as session:
            query = session.query(Customer)
            if search_query:
                term = f"%{search_query}%"
                query = query.filter(
                    (Customer.name.ilike(term))
                    | (Customer.phone.ilike(term))
                    | (Customer.email.ilike(term))
                )
            customers = query.order_by(Customer.name.asc()).all()

            if not customers:
                ctk.CTkLabel(
                    self.customers_feed,
                    text="No clients found.",
                    font=FONT_BODY,
                    text_color=PALETTE["dark"]["text_secondary"],
                ).pack(pady=30)
                return

            if self.selected_customer_id is None and customers:
                self.selected_customer_id = customers[0].id

            for c in customers:
                is_selected = (c.id == self.selected_customer_id)
                card = ctk.CTkFrame(
                    self.customers_feed,
                    corner_radius=8,
                    fg_color=PALETTE["dark"]["card_secondary"] if is_selected else PALETTE["dark"]["bg_primary"],
                    border_width=1,
                    border_color=PALETTE["dark"]["accent"] if is_selected else PALETTE["dark"]["border"],
                )
                card.pack(fill="x", pady=4, padx=4)

                # Avatar initials
                initials = "".join([part[0] for part in c.name.split()[:2]]).upper() or "C"
                ctk.CTkLabel(
                    card,
                    text=initials,
                    font=FONT_SMALL_BOLD,
                    width=36,
                    height=36,
                    corner_radius=8,
                    fg_color=PALETTE["dark"]["purple"],
                    text_color="#FFFFFF",
                ).pack(side="left", padx=10, pady=10)

                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True)

                ctk.CTkLabel(info, text=c.name, font=FONT_BODY_BOLD, text_color=PALETTE["dark"]["text_primary"], anchor="w").pack(fill="x")
                ctk.CTkLabel(info, text=f"{c.phone} • {c.total_bookings} bookings", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"], anchor="w").pack(fill="x")

                card.bind("<Button-1>", lambda e, c_id=c.id: self.select_customer(c_id))

        self.render_customer_details()

    def select_customer(self, customer_id: int):
        self.selected_customer_id = customer_id
        self.refresh_customer_list()

    def render_customer_details(self):
        """Render details of active customer in right pane."""
        for w in self.right_box.winfo_children():
            w.destroy()

        if not self.selected_customer_id:
            ctk.CTkLabel(self.right_box, text="Select a client from the list to view profile.", font=FONT_BODY, text_color=PALETTE["dark"]["text_secondary"]).pack(pady=50)
            return

        from sqlalchemy.orm import joinedload
        with get_db() as session:
            c = session.query(Customer).filter(Customer.id == self.selected_customer_id).first()
            if not c:
                return

            appointments = session.query(Appointment).options(joinedload(Appointment.service)).filter(Appointment.customer_id == c.id).order_by(Appointment.date.desc()).all()

            # Profile Header
            head_card = ctk.CTkFrame(self.right_box, fg_color=PALETTE["dark"]["bg_primary"], corner_radius=10)
            head_card.pack(fill="x", padx=16, pady=(16, 16))

            top_row = ctk.CTkFrame(head_card, fg_color="transparent")
            top_row.pack(fill="x", padx=16, pady=14)

            ctk.CTkLabel(top_row, text=c.name, font=FONT_TITLE, text_color=PALETTE["dark"]["text_primary"]).pack(side="left")

            ctk.CTkButton(
                top_row,
                text="✏ Edit Profile",
                width=100,
                height=30,
                font=FONT_SMALL_BOLD,
                fg_color=PALETTE["dark"]["card_secondary"],
                command=lambda: self.open_edit_customer_modal(c.id),
            ).pack(side="right")

            info_row = ctk.CTkFrame(head_card, fg_color="transparent")
            info_row.pack(fill="x", padx=16, pady=(0, 14))

            ctk.CTkLabel(info_row, text=f"📞 Phone: {c.phone}   |   ✉ Email: {c.email or 'None'}", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w")

            # Metrics row
            metrics_frame = ctk.CTkFrame(self.right_box, fg_color="transparent")
            metrics_frame.pack(fill="x", padx=16, pady=(0, 16))
            metrics_frame.grid_columnconfigure((0, 1, 2), weight=1)

            total_spent = sum(a.price for a in appointments if a.status in ("confirmed", "completed"))

            # Total Bookings Card
            m1 = ctk.CTkFrame(metrics_frame, corner_radius=8, fg_color=PALETTE["dark"]["bg_primary"])
            m1.grid(row=0, column=0, padx=(0, 6), sticky="ew")
            ctk.CTkLabel(m1, text="TOTAL VISITS", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_muted"]).pack(pady=(10, 2))
            ctk.CTkLabel(m1, text=str(len(appointments)), font=FONT_SUBTITLE, text_color=PALETTE["dark"]["accent"]).pack(pady=(0, 10))

            # Total Spent Card
            m2 = ctk.CTkFrame(metrics_frame, corner_radius=8, fg_color=PALETTE["dark"]["bg_primary"])
            m2.grid(row=0, column=1, padx=6, sticky="ew")
            ctk.CTkLabel(m2, text="TOTAL VALUE", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_muted"]).pack(pady=(10, 2))
            ctk.CTkLabel(m2, text=f"${total_spent:.2f}", font=FONT_SUBTITLE, text_color=PALETTE["dark"]["success"]).pack(pady=(0, 10))

            # Reliability Card
            completed = sum(1 for a in appointments if a.status == "completed")
            m3 = ctk.CTkFrame(metrics_frame, corner_radius=8, fg_color=PALETTE["dark"]["bg_primary"])
            m3.grid(row=0, column=2, padx=(6, 0), sticky="ew")
            ctk.CTkLabel(m3, text="COMPLETED", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_muted"]).pack(pady=(10, 2))
            ctk.CTkLabel(m3, text=str(completed), font=FONT_SUBTITLE, text_color=PALETTE["dark"]["purple"]).pack(pady=(0, 10))

            # Client Notes
            notes_card = ctk.CTkFrame(self.right_box, fg_color=PALETTE["dark"]["bg_primary"], corner_radius=10)
            notes_card.pack(fill="x", padx=16, pady=(0, 16))

            ctk.CTkLabel(notes_card, text="Client Clinical / Preference Notes", font=FONT_BODY_BOLD, text_color=PALETTE["dark"]["text_primary"]).pack(anchor="w", padx=16, pady=(12, 6))
            notes_entry = ctk.CTkTextbox(notes_card, height=75, font=FONT_BODY)
            notes_entry.pack(fill="x", padx=16, pady=(0, 10))
            if c.notes:
                notes_entry.insert("1.0", c.notes)

            def save_notes():
                new_notes = notes_entry.get("1.0", "end").strip()
                with get_db() as s:
                    cust = s.query(Customer).filter(Customer.id == c.id).first()
                    cust.notes = new_notes
                show_toast(self.winfo_toplevel(), "Client notes saved!", level="success")

            ctk.CTkButton(
                notes_card,
                text="Save Notes",
                width=100,
                height=28,
                font=FONT_SMALL_BOLD,
                fg_color=PALETTE["dark"]["card_secondary"],
                hover_color=PALETTE["dark"]["accent"],
                command=save_notes,
            ).pack(anchor="e", padx=16, pady=(0, 12))

            # Booking History Table
            ctk.CTkLabel(self.right_box, text="Appointment History", font=FONT_HEADING, text_color=PALETTE["dark"]["text_primary"]).pack(anchor="w", padx=16, pady=(6, 8))

            if not appointments:
                ctk.CTkLabel(self.right_box, text="No bookings on record.", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", padx=16)
            else:
                for app in appointments:
                    h_row = ctk.CTkFrame(self.right_box, corner_radius=6, fg_color=PALETTE["dark"]["bg_primary"])
                    h_row.pack(fill="x", padx=16, pady=3)

                    ctk.CTkLabel(h_row, text=app.appointment_number, font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["accent"], width=100, anchor="w").pack(side="left", padx=10, pady=8)
                    ctk.CTkLabel(h_row, text=f"{app.date} ({app.start_time})", font=FONT_SMALL, width=120, anchor="w").pack(side="left", padx=6)
                    ctk.CTkLabel(h_row, text=app.service.name, font=FONT_SMALL, text_color=PALETTE["dark"]["text_primary"], width=150, anchor="w").pack(side="left", padx=6)
                    ctk.CTkLabel(h_row, text=f"${app.price:.2f}", font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["success"], width=70, anchor="w").pack(side="left", padx=6)

                    s_color = STATUS_COLORS.get(app.status, PALETTE["dark"]["accent"])
                    ctk.CTkLabel(h_row, text=app.status.upper(), font=("Segoe UI", 8, "bold"), fg_color=s_color, text_color="#FFFFFF", corner_radius=4, width=75, height=22).pack(side="right", padx=10)

    def open_add_customer_modal(self):
        diag = ctk.CTkToplevel(self.winfo_toplevel())
        diag.title("Add New Client")
        diag.geometry("440x360")
        diag.resizable(False, False)
        diag.transient(self.winfo_toplevel())
        diag.grab_set()
        diag.configure(fg_color=PALETTE["dark"]["card_bg"])

        ctk.CTkLabel(diag, text="New Client Profile", font=FONT_HEADING).pack(anchor="w", padx=24, pady=(20, 14))

        ctk.CTkLabel(diag, text="Full Name *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        name_entry = ctk.CTkEntry(diag, height=36)
        name_entry.pack(fill="x", padx=24, pady=(2, 10))

        ctk.CTkLabel(diag, text="Phone Number *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        phone_entry = ctk.CTkEntry(diag, height=36)
        phone_entry.pack(fill="x", padx=24, pady=(2, 10))

        ctk.CTkLabel(diag, text="Email Address", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        email_entry = ctk.CTkEntry(diag, height=36)
        email_entry.pack(fill="x", padx=24, pady=(2, 10))

        ctk.CTkLabel(diag, text="Notes & Preferences", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
        notes_entry = ctk.CTkEntry(diag, height=36)
        notes_entry.pack(fill="x", padx=24, pady=(2, 20))

        def submit():
            nm = name_entry.get().strip()
            ph = phone_entry.get().strip()
            em = email_entry.get().strip()
            nt = notes_entry.get().strip()

            if not nm or not ph:
                show_toast(diag, "Name and Phone are required.", level="warning")
                return

            with get_db() as s:
                existing = s.query(Customer).filter(Customer.phone == ph).first()
                if existing:
                    show_toast(diag, "Client with this phone already exists.", level="error")
                    return

                new_cust = Customer(name=nm, phone=ph, email=em or None, notes=nt or None)
                s.add(new_cust)
                s.flush()
                self.selected_customer_id = new_cust.id

            diag.destroy()
            show_toast(self.winfo_toplevel(), "Client profile created!", level="success")
            self.refresh_customer_list()

        btn_box = ctk.CTkFrame(diag, fg_color="transparent")
        btn_box.pack(fill="x", padx=24)
        ctk.CTkButton(btn_box, text="Cancel", width=100, height=36, fg_color=PALETTE["dark"]["card_secondary"], command=diag.destroy).pack(side="left")
        ctk.CTkButton(btn_box, text="Create Client", width=140, height=36, fg_color=PALETTE["dark"]["accent"], command=submit).pack(side="right")

    def open_edit_customer_modal(self, customer_id: int):
        with get_db() as session:
            c = session.query(Customer).filter(Customer.id == customer_id).first()
            if not c:
                return

            diag = ctk.CTkToplevel(self.winfo_toplevel())
            diag.title("Edit Client Profile")
            diag.geometry("440x320")
            diag.resizable(False, False)
            diag.transient(self.winfo_toplevel())
            diag.grab_set()
            diag.configure(fg_color=PALETTE["dark"]["card_bg"])

            ctk.CTkLabel(diag, text=f"Edit {c.name}", font=FONT_HEADING).pack(anchor="w", padx=24, pady=(20, 14))

            ctk.CTkLabel(diag, text="Full Name *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            name_entry = ctk.CTkEntry(diag, height=36)
            name_entry.insert(0, c.name)
            name_entry.pack(fill="x", padx=24, pady=(2, 10))

            ctk.CTkLabel(diag, text="Phone Number *", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            phone_entry = ctk.CTkEntry(diag, height=36)
            phone_entry.insert(0, c.phone)
            phone_entry.pack(fill="x", padx=24, pady=(2, 10))

            ctk.CTkLabel(diag, text="Email Address", font=FONT_SMALL_BOLD).pack(anchor="w", padx=24)
            email_entry = ctk.CTkEntry(diag, height=36)
            email_entry.insert(0, c.email or "")
            email_entry.pack(fill="x", padx=24, pady=(2, 20))

            def submit():
                with get_db() as s:
                    cust = s.query(Customer).filter(Customer.id == customer_id).first()
                    cust.name = name_entry.get().strip()
                    cust.phone = phone_entry.get().strip()
                    cust.email = email_entry.get().strip() or None

                diag.destroy()
                show_toast(self.winfo_toplevel(), "Profile updated!", level="success")
                self.refresh_customer_list()

            btn_box = ctk.CTkFrame(diag, fg_color="transparent")
            btn_box.pack(fill="x", padx=24)
            ctk.CTkButton(btn_box, text="Cancel", width=100, height=36, fg_color=PALETTE["dark"]["card_secondary"], command=diag.destroy).pack(side="left")
            ctk.CTkButton(btn_box, text="Save Changes", width=140, height=36, fg_color=PALETTE["dark"]["accent"], command=submit).pack(side="right")
