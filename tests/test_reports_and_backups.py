"""Tests for reports export, backup management, and audit logging."""

import os
from pathlib import Path
from src.core.booking_service import BookingService
from src.core.reports_service import ReportsService
from src.core.backup_manager import BackupManager
from src.core.audit_logger import AuditLogger
from src.database.models import Appointment


def test_reports_generation(db_session, sample_data, tmp_path):
    staff = sample_data["staff"]
    service = sample_data["service"]
    customer = sample_data["customer"]

    BookingService.create_appointment(
        session=db_session,
        customer_id=customer.id,
        staff_id=staff.id,
        service_id=service.id,
        booking_date="2026-10-15",
        start_time="10:00",
    )

    apps = db_session.query(Appointment).all()
    assert len(apps) > 0

    # 1. Test CSV Export
    csv_file = tmp_path / "test_export.csv"
    res_csv = ReportsService.export_appointments_csv(apps, csv_file)
    assert res_csv.exists()
    assert res_csv.stat().st_size > 50

    # 2. Test Excel Export
    xlsx_file = tmp_path / "test_export.xlsx"
    res_xlsx = ReportsService.export_appointments_excel(db_session, apps, xlsx_file)
    assert res_xlsx.exists()
    assert res_xlsx.stat().st_size > 100

    # 3. Test PDF Export
    pdf_file = tmp_path / "test_export.pdf"
    res_pdf = ReportsService.export_appointments_pdf(db_session, apps, "Test Run", pdf_file)
    assert res_pdf.exists()
    assert res_pdf.stat().st_size > 100


def test_audit_logger(db_session, sample_data):
    entry = AuditLogger.log(
        session=db_session,
        action="TEST_ACTION",
        entity_type="UnitTesting",
        entity_id="123",
        details="Sample log details for automated test",
    )
    assert entry.id is not None
    assert entry.action == "TEST_ACTION"

    logs = AuditLogger.get_recent_logs(db_session, limit=10, action_filter="TEST_ACTION")
    assert len(logs) >= 1
    assert logs[0].entity_id == "123"


def test_backup_and_integrity():
    # Database integrity check
    valid, msg = BackupManager.verify_integrity()
    assert valid is True

    # Create backup snapshot
    ok, msg, meta = BackupManager.create_backup("Pytest snapshot")
    assert ok is True
    assert "sha256" in meta

    # List backups
    backups = BackupManager.list_backups()
    assert len(backups) > 0
    assert any(b["backup_filename"] == meta["backup_filename"] for b in backups)
