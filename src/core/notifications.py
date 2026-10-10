"""Email reminders and notification dispatch service."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Tuple
from sqlalchemy.orm import Session
from src.database.models import Appointment, BusinessSetting
from src.core.audit_logger import AuditLogger


class NotificationService:
    """Handles appointment confirmation and reminder dispatch."""

    @staticmethod
    def get_smtp_config(session: Session) -> dict:
        """Read SMTP settings from BusinessSetting table."""
        settings = session.query(BusinessSetting).all()
        data = {s.key: s.value for s in settings}
        return {
            "enabled": data.get("smtp_enabled", "false").lower() == "true",
            "server": data.get("smtp_server", "smtp.mailtrap.io"),
            "port": int(data.get("smtp_port", "587")),
            "username": data.get("smtp_username", ""),
            "password": data.get("smtp_password", ""),
            "from_email": data.get("smtp_from_email", "bookings@example.com"),
            "biz_name": data.get("business_name", "BookEase Practice"),
            "currency": data.get("currency_symbol", "$"),
        }

    @classmethod
    def send_booking_confirmation(
        cls, session: Session, appointment_id: int
    ) -> Tuple[bool, str]:
        """Dispatch or log a booking confirmation."""
        app = session.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not app:
            return False, "Appointment not found."

        if not app.customer or not app.customer.email:
            return False, "Customer does not have an email address."

        config = cls.get_smtp_config(session)
        subject = f"Booking Confirmation: {app.appointment_number} with {config['biz_name']}"
        body = f"""Dear {app.customer.name},

Your appointment has been successfully scheduled at {config['biz_name']}!

Details:
• Confirmation Ref: {app.appointment_number}
• Service: {app.service.name if app.service else 'Service'}
• Specialist: {app.staff.name if app.staff else 'Specialist'}
• Date: {app.date}
• Time: {app.start_time} - {app.end_time}
• Price: {config['currency']}{app.price:.2f}

If you need to reschedule or cancel your appointment, please contact us ahead of time.

Best regards,
{config['biz_name']} Team
"""

        if config["enabled"] and config["username"] and config["password"]:
            try:
                msg = MIMEMultipart()
                msg["From"] = config["from_email"]
                msg["To"] = app.customer.email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                server = smtplib.SMTP(config["server"], config["port"], timeout=10)
                server.starttls()
                server.login(config["username"], config["password"])
                server.sendmail(config["from_email"], [app.customer.email], msg.as_string())
                server.quit()

                AuditLogger.log(
                    session,
                    action="EMAIL_SENT",
                    entity_type="Appointment",
                    entity_id=str(app.id),
                    details=f"Confirmation email dispatched via SMTP to {app.customer.email}",
                )
                return True, f"Confirmation email sent to {app.customer.email}."
            except Exception as e:
                return False, f"Failed to send email via SMTP: {str(e)}"
        else:
            # Simulated / Local Desktop Log Mode
            AuditLogger.log(
                session,
                action="NOTIFICATION_LOGGED",
                entity_type="Appointment",
                entity_id=str(app.id),
                details=f"[Offline Mode] Confirmation logged for {app.customer.email}: {app.appointment_number}",
            )
            return True, f"[Offline Mode] Confirmation logged for {app.customer.email}."
