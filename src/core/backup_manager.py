"""Database Backup and Restoration Management."""

import shutil
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sqlalchemy import text
from src.config import BACKUP_DIR, DB_PATH
from src.database.connection import engine, SessionLocal, get_db
from src.core.audit_logger import AuditLogger


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


class BackupManager:
    """Service to create, verify, list, and restore database backups."""

    @classmethod
    def create_backup(cls, note: str = "Manual Backup") -> Tuple[bool, str, Dict[str, Any]]:
        """Create a point-in-time snapshot of the SQLite database."""
        if not DB_PATH.exists():
            return False, "Database file does not exist to back up.", {}

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"bookease_backup_{timestamp_str}.db"
        meta_filename = f"bookease_backup_{timestamp_str}.json"
        
        backup_file = BACKUP_DIR / backup_filename
        meta_file = BACKUP_DIR / meta_filename

        try:
            # Checkpoint WAL log into main DB file before copying
            with engine.connect() as conn:
                conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
                conn.commit()

            # Copy database file safely
            shutil.copy2(DB_PATH, backup_file)

            # Compute hash
            file_hash = compute_file_sha256(backup_file)
            file_size = backup_file.stat().st_size

            metadata = {
                "backup_filename": backup_filename,
                "timestamp": datetime.now().isoformat(),
                "created_at_formatted": datetime.now().strftime("%b %d, %Y %I:%M %p"),
                "note": note,
                "sha256": file_hash,
                "size_bytes": file_size,
                "size_kb": round(file_size / 1024, 2),
            }

            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Record audit log
            with get_db() as session:
                AuditLogger.log(
                    session,
                    action="DATABASE_BACKUP",
                    entity_type="Database",
                    entity_id=backup_filename,
                    details=f"Created backup {backup_filename} ({metadata['size_kb']} KB). Note: {note}",
                )

            return True, f"Backup successfully created: {backup_filename}", metadata

        except Exception as e:
            return False, f"Failed to create backup: {str(e)}", {}

    @classmethod
    def list_backups(cls) -> List[Dict[str, Any]]:
        """List all available backups sorted newest first."""
        if not BACKUP_DIR.exists():
            return []

        backups = []
        for db_file in BACKUP_DIR.glob("*.db"):
            meta_file = db_file.with_suffix(".json")
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    data["filepath"] = str(db_file)
                    backups.append(data)
                except Exception:
                    pass
            else:
                # Fallback for backup files without explicit json
                backups.append({
                    "backup_filename": db_file.name,
                    "filepath": str(db_file),
                    "created_at_formatted": datetime.fromtimestamp(db_file.stat().st_mtime).strftime("%b %d, %Y %I:%M %p"),
                    "note": "Standalone backup",
                    "size_kb": round(db_file.stat().st_size / 1024, 2),
                    "sha256": compute_file_sha256(db_file),
                })

        backups.sort(key=lambda x: x.get("timestamp", x.get("created_at_formatted", "")), reverse=True)
        return backups

    @classmethod
    def restore_backup(cls, backup_filename: str) -> Tuple[bool, str]:
        """Restore database from an existing backup with hash verification."""
        backup_file = BACKUP_DIR / backup_filename
        if not backup_file.exists():
            return False, f"Backup file {backup_filename} does not exist."

        # Check metadata hash if available
        meta_file = backup_file.with_suffix(".json")
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                expected_hash = meta.get("sha256")
                actual_hash = compute_file_sha256(backup_file)
                if expected_hash and expected_hash != actual_hash:
                    return False, "Backup integrity error: Checksum mismatch. File may be corrupted."
            except Exception as e:
                return False, f"Error reading backup metadata: {str(e)}"

        try:
            # Dispose of existing engine connection pool
            SessionLocal.remove()
            engine.dispose()

            # Create an emergency backup of the current database before overwriting
            if DB_PATH.exists():
                pre_restore_backup = BACKUP_DIR / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(DB_PATH, pre_restore_backup)

            # Restore the database
            shutil.copy2(backup_file, DB_PATH)

            # Verify integrity of newly restored DB
            with engine.connect() as conn:
                res = conn.execute(text("PRAGMA integrity_check")).scalar()
                if res != "ok":
                    return False, f"Restored database failed integrity check: {res}"

            # Log audit trail
            with get_db() as session:
                AuditLogger.log(
                    session,
                    action="DATABASE_RESTORE",
                    entity_type="Database",
                    entity_id=backup_filename,
                    details=f"Restored database from backup {backup_filename}",
                )

            return True, f"Database successfully restored from {backup_filename}."

        except Exception as e:
            return False, f"Failed to restore database: {str(e)}"

    @classmethod
    def verify_integrity(cls) -> Tuple[bool, str]:
        """Run SQLite integrity check."""
        try:
            with engine.connect() as conn:
                res = conn.execute(text("PRAGMA integrity_check")).scalar()
                if res == "ok":
                    return True, "Database integrity verified. All tables and indexes are healthy."
                else:
                    return False, f"Database integrity issues detected: {res}"
        except Exception as e:
            return False, f"Failed to verify database: {str(e)}"
