"""Settings, Business Customization, Backup/Restore, and Audit Logs View."""

from typing import Optional, Dict
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
from src.database.models import BusinessSetting, AuditLog
from src.core.backup_manager import BackupManager
from src.core.audit_logger import AuditLogger
from src.core.security import SessionManager


class SettingsView(ctk.CTkFrame):
    """Business settings, system policies, backups, and audit trail."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.create_header()

        # Tabview
        self.create_tabs()

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Settings & Administration",
            font=FONT_TITLE,
            text_color=PALETTE["dark"]["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Configure branding, currency, booking rules, backups, and review audit trail",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
        ).pack(anchor="w")

    def create_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=12,
            fg_color=PALETTE["dark"]["card_bg"],
            segmented_button_selected_color=PALETTE["dark"]["accent"],
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))

        t_biz = self.tabview.add("🏢 Business Profile")
        t_policy = self.tabview.add("⚙ Policies & Rules")
        t_smtp = self.tabview.add("✉ Email & SMTP")
        t_backup = self.tabview.add("💾 Backups & Recovery")
        t_audit = self.tabview.add("📜 Audit Trail")

        self.setup_business_tab(t_biz)
        self.setup_policy_tab(t_policy)
        self.setup_smtp_tab(t_smtp)
        self.setup_backup_tab(t_backup)
        self.setup_audit_tab(t_audit)

    # =========================================================================
    # TAB 1: BUSINESS PROFILE
    # =========================================================================
    def setup_business_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=10)

        with get_db() as session:
            settings = {s.key: s.value for s in session.query(BusinessSetting).all()}

        fields = [
            ("business_name", "Business / Clinic Name *", settings.get("business_name", "Lumière Wellness & Spa")),
            ("business_category", "Business Category / Industry", settings.get("business_category", "Salon & Wellness Spa")),
            ("owner_name", "Primary Director / Owner Name", settings.get("owner_name", "Eleanor Vance")),
            ("phone", "Contact Phone Number", settings.get("phone", "+1 (555) 328-9400")),
            ("email", "Public Contact Email", settings.get("email", "contact@lumierewellness.com")),
            ("address", "Physical Address", settings.get("address", "742 Evergreen Terrace, Suite 100")),
            ("currency_symbol", "Currency Symbol (e.g. $, €, £, PKR, AED)", settings.get("currency_symbol", "$")),
            ("currency_code", "Currency Code (e.g. USD, EUR, GBP)", settings.get("currency_code", "USD")),
            ("timezone", "Timezone (e.g. UTC, EST, GMT)", settings.get("timezone", "UTC")),
        ]

        self.biz_entries = {}
        for key, label, val in fields:
            ctk.CTkLabel(scroll, text=label, font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", pady=(8, 2))
            ent = ctk.CTkEntry(scroll, height=36, font=FONT_BODY)
            ent.insert(0, val)
            ent.pack(fill="x", pady=(0, 4))
            self.biz_entries[key] = ent

        def save_biz_profile():
            with get_db() as s:
                for k, entry in self.biz_entries.items():
                    val = entry.get().strip()
                    setting = s.query(BusinessSetting).filter(BusinessSetting.key == k).first()
                    if setting:
                        setting.value = val
                    else:
                        s.add(BusinessSetting(key=k, value=val))
                AuditLogger.log(s, "UPDATE_SETTINGS", "BusinessSetting", "Profile", "Updated business profile preferences")

            show_toast(self.winfo_toplevel(), "Business profile saved successfully!", level="success")

        ctk.CTkButton(
            scroll,
            text="💾 Save Business Profile",
            height=40,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            command=save_biz_profile,
        ).pack(anchor="e", pady=(20, 20))

    # =========================================================================
    # TAB 2: POLICIES & RULES
    # =========================================================================
    def setup_policy_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=10)

        with get_db() as session:
            settings = {s.key: s.value for s in session.query(BusinessSetting).all()}

        ctk.CTkLabel(scroll, text="Turnaround Buffer Time (Minutes)", font=FONT_SMALL_BOLD).pack(anchor="w", pady=(10, 2))
        self.buffer_entry = ctk.CTkEntry(scroll, height=36)
        self.buffer_entry.insert(0, settings.get("default_appointment_buffer", "15"))
        self.buffer_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(scroll, text="Slot Granularity Interval (Minutes)", font=FONT_SMALL_BOLD).pack(anchor="w", pady=(10, 2))
        self.interval_entry = ctk.CTkEntry(scroll, height=36)
        self.interval_entry.insert(0, settings.get("default_slot_interval", "15"))
        self.interval_entry.pack(fill="x", pady=(0, 16))

        # Concurrency safety info box
        info_card = ctk.CTkFrame(scroll, fg_color=PALETTE["dark"]["bg_primary"], corner_radius=8)
        info_card.pack(fill="x", pady=10)

        ctk.CTkLabel(info_card, text="🛡 Concurrency & Double-Booking Protection", font=FONT_BODY_BOLD, text_color=PALETTE["dark"]["success"]).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            info_card,
            text="BookEase enforces strict ACID database transactions and double-checking algorithms to guarantee no specialist is ever double-booked across overlapping appointment windows.",
            font=FONT_SMALL,
            text_color=PALETTE["dark"]["text_secondary"],
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        def save_policies():
            with get_db() as s:
                b_set = s.query(BusinessSetting).filter(BusinessSetting.key == "default_appointment_buffer").first()
                if b_set:
                    b_set.value = self.buffer_entry.get().strip()
                i_set = s.query(BusinessSetting).filter(BusinessSetting.key == "default_slot_interval").first()
                if i_set:
                    i_set.value = self.interval_entry.get().strip()
            show_toast(self.winfo_toplevel(), "Booking policies updated!", level="success")

        ctk.CTkButton(
            scroll,
            text="💾 Save Policies",
            height=40,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            command=save_policies,
        ).pack(anchor="e", pady=(20, 20))

    # =========================================================================
    # TAB 3: EMAIL & SMTP
    # =========================================================================
    def setup_smtp_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=10)

        with get_db() as session:
            settings = {s.key: s.value for s in session.query(BusinessSetting).all()}

        self.smtp_enabled_var = ctk.BooleanVar(value=settings.get("smtp_enabled", "false").lower() == "true")
        chk = ctk.CTkCheckBox(scroll, text="Enable Automated Email Confirmations (SMTP)", variable=self.smtp_enabled_var, font=FONT_BODY_BOLD)
        chk.pack(anchor="w", pady=(10, 16))

        fields = [
            ("smtp_server", "SMTP Server Host", settings.get("smtp_server", "smtp.mailtrap.io")),
            ("smtp_port", "SMTP Port (e.g. 587, 465)", settings.get("smtp_port", "587")),
            ("smtp_username", "SMTP Username", settings.get("smtp_username", "")),
            ("smtp_password", "SMTP Password", settings.get("smtp_password", "")),
            ("smtp_from_email", "Sender Email Address", settings.get("smtp_from_email", "bookings@example.com")),
        ]

        self.smtp_entries = {}
        for key, label, val in fields:
            ctk.CTkLabel(scroll, text=label, font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["text_secondary"]).pack(anchor="w", pady=(6, 2))
            ent = ctk.CTkEntry(scroll, height=36, show="•" if "password" in key else "")
            ent.insert(0, val)
            ent.pack(fill="x", pady=(0, 4))
            self.smtp_entries[key] = ent

        def save_smtp():
            with get_db() as s:
                en_set = s.query(BusinessSetting).filter(BusinessSetting.key == "smtp_enabled").first()
                if en_set:
                    en_set.value = str(self.smtp_enabled_var.get()).lower()

                for k, entry in self.smtp_entries.items():
                    setting = s.query(BusinessSetting).filter(BusinessSetting.key == k).first()
                    if setting:
                        setting.value = entry.get().strip()
                    else:
                        s.add(BusinessSetting(key=k, value=entry.get().strip()))
            show_toast(self.winfo_toplevel(), "SMTP configuration updated!", level="success")

        ctk.CTkButton(
            scroll,
            text="💾 Save SMTP Settings",
            height=40,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            command=save_smtp,
        ).pack(anchor="e", pady=(20, 20))

    # =========================================================================
    # TAB 4: BACKUPS & RECOVERY
    # =========================================================================
    def setup_backup_tab(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=12)

        ctk.CTkButton(
            top_bar,
            text="💾 Create Instant Backup",
            height=36,
            font=FONT_BODY_BOLD,
            fg_color=PALETTE["dark"]["accent"],
            command=self.create_instant_backup,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            top_bar,
            text="🔍 Run Database Diagnostic",
            height=36,
            font=FONT_SMALL_BOLD,
            fg_color=PALETTE["dark"]["card_secondary"],
            command=self.run_integrity_check,
        ).pack(side="left")

        # Backups List Feed
        self.backups_scroll = ctk.CTkScrollableFrame(parent, fg_color=PALETTE["dark"]["bg_primary"], corner_radius=10)
        self.backups_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.refresh_backups_list()

    def refresh_backups_list(self):
        for w in self.backups_scroll.winfo_children():
            w.destroy()

        backups = BackupManager.list_backups()
        if not backups:
            ctk.CTkLabel(self.backups_scroll, text="No backups found in backups folder.", font=FONT_BODY, text_color=PALETTE["dark"]["text_secondary"]).pack(pady=30)
            return

        for b in backups:
            row = ctk.CTkFrame(self.backups_scroll, corner_radius=8, fg_color=PALETTE["dark"]["card_bg"])
            row.pack(fill="x", padx=10, pady=4)

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, padx=12, pady=10)

            ctk.CTkLabel(info, text=f"📦 {b['backup_filename']}", font=FONT_BODY_BOLD, text_color=PALETTE["dark"]["text_primary"], anchor="w").pack(fill="x")
            ctk.CTkLabel(
                info,
                text=f"Created: {b.get('created_at_formatted', 'N/A')}  •  Size: {b.get('size_kb', 0)} KB  •  SHA256: {b.get('sha256', '')[:16]}...",
                font=FONT_SMALL,
                text_color=PALETTE["dark"]["text_secondary"],
                anchor="w",
            ).pack(fill="x")

            ctk.CTkButton(
                row,
                text="Restore ↺",
                width=90,
                height=30,
                font=FONT_SMALL_BOLD,
                fg_color=PALETTE["dark"]["danger"],
                hover_color=PALETTE["dark"]["danger_hover"],
                command=lambda fname=b["backup_filename"]: self.confirm_restore(fname),
            ).pack(side="right", padx=12)

    def create_instant_backup(self):
        ok, msg, meta = BackupManager.create_backup("Manual backup via Settings")
        if ok:
            show_toast(self.winfo_toplevel(), f"Backup created ({meta.get('size_kb')} KB)!", level="success")
            self.refresh_backups_list()
        else:
            show_toast(self.winfo_toplevel(), f"Backup failed: {msg}", level="error")

    def run_integrity_check(self):
        ok, msg = BackupManager.verify_integrity()
        if ok:
            show_toast(self.winfo_toplevel(), f"Health Check: {msg}", level="success")
        else:
            show_toast(self.winfo_toplevel(), f"Health Warning: {msg}", level="error")

    def confirm_restore(self, backup_filename: str):
        def do_restore():
            ok, msg = BackupManager.restore_backup(backup_filename)
            if ok:
                show_toast(self.winfo_toplevel(), "Database restored successfully!", level="success")
                self.refresh_backups_list()
            else:
                show_toast(self.winfo_toplevel(), f"Restore failed: {msg}", level="error")

        ConfirmDialog(
            master=self.winfo_toplevel(),
            title="Restore Database",
            message=f"Are you sure you want to restore from {backup_filename}? Any changes made after this backup was taken will be overwritten.",
            on_confirm=do_restore,
            confirm_text="Yes, Restore DB",
            is_destructive=True,
        )

    # =========================================================================
    # TAB 5: AUDIT TRAIL
    # =========================================================================
    def setup_audit_tab(self, parent):
        self.audit_scroll = ctk.CTkScrollableFrame(parent, fg_color=PALETTE["dark"]["bg_primary"], corner_radius=10)
        self.audit_scroll.pack(fill="both", expand=True, padx=16, pady=12)

        with get_db() as session:
            logs = AuditLogger.get_recent_logs(session, limit=50)

        if not logs:
            ctk.CTkLabel(self.audit_scroll, text="No audit records yet.", font=FONT_BODY, text_color=PALETTE["dark"]["text_secondary"]).pack(pady=30)
            return

        for l in logs:
            row = ctk.CTkFrame(self.audit_scroll, corner_radius=6, fg_color=PALETTE["dark"]["card_bg"])
            row.pack(fill="x", padx=8, pady=3)

            time_str = l.created_at.strftime("%b %d, %H:%M:%S")
            ctk.CTkLabel(row, text=time_str, font=FONT_SMALL, text_color=PALETTE["dark"]["text_muted"], width=120, anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=l.action, font=FONT_SMALL_BOLD, text_color=PALETTE["dark"]["accent"], width=180, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=f"by {l.user_name or 'System'}", font=FONT_SMALL, text_color=PALETTE["dark"]["text_secondary"], width=130, anchor="w").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=l.details or "", font=FONT_SMALL, text_color=PALETTE["dark"]["text_primary"], anchor="w").pack(side="left", padx=6, fill="x", expand=True)
