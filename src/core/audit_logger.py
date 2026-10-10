"""Audit Logging service for tracking administrative and booking events."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from src.database.models import AuditLog
from src.core.security import SessionManager


class AuditLogger:
    """Service to record and retrieve system audit logs."""

    @staticmethod
    def log(
        session: Session,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[str] = None,
        source: str = "Desktop App",
    ) -> AuditLog:
        """Create an immutable audit log entry."""
        current_user = SessionManager.get_current_user()
        user_id = current_user.id if current_user else None
        user_name = current_user.full_name if current_user else "System"

        entry = AuditLog(
            user_id=user_id,
            user_name=user_name,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            details=details,
            ip_or_source=source,
            created_at=datetime.utcnow(),
        )
        session.add(entry)
        session.flush()
        return entry

    @staticmethod
    def get_recent_logs(
        session: Session,
        limit: int = 100,
        action_filter: Optional[str] = None,
    ) -> List[AuditLog]:
        """Fetch latest audit entries sorted by timestamp descending."""
        query = session.query(AuditLog)
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
