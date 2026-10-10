"""Reports and Analytics Export Service (PDF, Excel, CSV)."""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether

from src.config import REPORTS_DIR
from src.database.models import Appointment, Customer, Service, Staff, BusinessSetting


class ReportsService:
    """Generates professional PDF, Excel, and CSV business reports."""

    @staticmethod
    def get_business_info(session: Session) -> dict:
        """Fetch business profile info from settings."""
        settings = session.query(BusinessSetting).all()
        data = {s.key: s.value for s in settings}
        return {
            "name": data.get("business_name", "BookEase Practice"),
            "category": data.get("business_category", "Professional Services"),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "address": data.get("address", ""),
            "currency": data.get("currency_symbol", "$"),
        }

    @classmethod
    def export_appointments_csv(cls, appointments: List[Appointment], output_path: Optional[Path] = None) -> Path:
        """Export appointments to a clean CSV file."""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = REPORTS_DIR / f"appointments_export_{timestamp}.csv"

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Booking Ref",
                "Date",
                "Start Time",
                "End Time",
                "Status",
                "Customer Name",
                "Customer Phone",
                "Customer Email",
                "Staff Member",
                "Service Name",
                "Price",
                "Notes",
            ])
            for app in appointments:
                writer.writerow([
                    app.appointment_number,
                    app.date,
                    app.start_time,
                    app.end_time,
                    app.status.upper(),
                    app.customer.name if app.customer else "",
                    app.customer.phone if app.customer else "",
                    app.customer.email if app.customer else "",
                    app.staff.name if app.staff else "",
                    app.service.name if app.service else "",
                    f"{app.price:.2f}",
                    app.notes or "",
                ])

        return output_path

    @classmethod
    def export_appointments_excel(
        cls, session: Session, appointments: List[Appointment], output_path: Optional[Path] = None
    ) -> Path:
        """Export appointments to a beautifully formatted Excel workbook with openpyxl."""
        biz = cls.get_business_info(session)
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = REPORTS_DIR / f"appointments_report_{timestamp}.xlsx"

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Appointments"

        # Styling tokens
        primary_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        title_font = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
        sub_font = Font(name="Calibri", size=10, italic=True, color="64748B")
        regular_font = Font(name="Calibri", size=10)
        bold_font = Font(name="Calibri", size=10, bold=True)
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1"),
        )

        # Title Rows
        ws["A1"] = biz["name"]
        ws["A1"].font = title_font
        ws["A2"] = f"Appointments Report | Generated {datetime.now().strftime('%b %d, %Y %I:%M %p')}"
        ws["A2"].font = sub_font

        headers = [
            "Ref #", "Date", "Time", "Status", "Customer", "Phone",
            "Staff", "Service", f"Price ({biz['currency']})", "Notes"
        ]

        # Header Row
        header_row = 4
        for col_idx, header_text in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_idx, value=header_text)
            cell.fill = primary_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        current_row = 5
        total_revenue = 0.0

        for app in appointments:
            ws.cell(row=current_row, column=1, value=app.appointment_number).font = regular_font
            ws.cell(row=current_row, column=2, value=app.date).font = regular_font
            ws.cell(row=current_row, column=3, value=f"{app.start_time} - {app.end_time}").font = regular_font
            
            status_cell = ws.cell(row=current_row, column=4, value=app.status.upper())
            status_cell.font = bold_font
            status_cell.alignment = Alignment(horizontal="center")

            ws.cell(row=current_row, column=5, value=app.customer.name if app.customer else "").font = regular_font
            ws.cell(row=current_row, column=6, value=app.customer.phone if app.customer else "").font = regular_font
            ws.cell(row=current_row, column=7, value=app.staff.name if app.staff else "").font = regular_font
            ws.cell(row=current_row, column=8, value=app.service.name if app.service else "").font = regular_font

            price_cell = ws.cell(row=current_row, column=9, value=app.price)
            price_cell.font = regular_font
            price_cell.number_format = f"{biz['currency']}#,##0.00"
            price_cell.alignment = Alignment(horizontal="right")

            ws.cell(row=current_row, column=10, value=app.notes or "").font = regular_font

            for c in range(1, len(headers) + 1):
                ws.cell(row=current_row, column=c).border = thin_border

            if app.status in ("confirmed", "completed"):
                total_revenue += app.price

            current_row += 1

        # Summary Row
        summary_row = current_row + 1
        ws.cell(row=summary_row, column=8, value="Total Revenue:").font = bold_font
        rev_cell = ws.cell(row=summary_row, column=9, value=total_revenue)
        rev_cell.font = bold_font
        rev_cell.number_format = f"{biz['currency']}#,##0.00"

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val = str(cell.value or "")
                max_len = max(max_len, len(val))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(output_path)
        return output_path

    @classmethod
    def export_appointments_pdf(
        cls,
        session: Session,
        appointments: List[Appointment],
        report_title: str = "Appointments Performance Report",
        output_path: Optional[Path] = None,
    ) -> Path:
        """Export appointments to a professional, publication-quality PDF report."""
        biz = cls.get_business_info(session)
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = REPORTS_DIR / f"appointments_summary_{timestamp}.pdf"

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1E3A8A"),
        )
        sub_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B"),
        )
        h2_style = ParagraphStyle(
            "DocH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=6,
        )
        cell_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
        )
        cell_bold = ParagraphStyle(
            "TableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
        )

        elements = []

        # Business Header
        elements.append(Paragraph(biz["name"], title_style))
        elements.append(Paragraph(f"{biz['category']} • {biz['address']} • {biz['phone']}", sub_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"<b>{report_title}</b>", h2_style))
        elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", sub_style))
        elements.append(Spacer(1, 12))

        # Table data
        data = [
            [
                Paragraph("<b>Ref #</b>", cell_bold),
                Paragraph("<b>Date / Time</b>", cell_bold),
                Paragraph("<b>Customer</b>", cell_bold),
                Paragraph("<b>Staff</b>", cell_bold),
                Paragraph("<b>Service</b>", cell_bold),
                Paragraph("<b>Status</b>", cell_bold),
                Paragraph("<b>Price</b>", cell_bold),
            ]
        ]

        total_rev = 0.0
        for app in appointments:
            ref_p = Paragraph(app.appointment_number, cell_style)
            time_p = Paragraph(f"{app.date}<br/>{app.start_time}-{app.end_time}", cell_style)
            cust_p = Paragraph(f"<b>{app.customer.name}</b><br/>{app.customer.phone}", cell_style) if app.customer else Paragraph("-", cell_style)
            staff_p = Paragraph(app.staff.name if app.staff else "-", cell_style)
            srv_p = Paragraph(app.service.name if app.service else "-", cell_style)
            
            # Status badge
            status_text = app.status.upper()
            status_p = Paragraph(f"<b>{status_text}</b>", cell_style)
            price_p = Paragraph(f"{biz['currency']}{app.price:.2f}", cell_bold)

            data.append([ref_p, time_p, cust_p, staff_p, srv_p, status_p, price_p])
            if app.status in ("confirmed", "completed"):
                total_rev += app.price

        table = Table(data, colWidths=[75, 75, 100, 85, 110, 55, 50])
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#3B82F6")),
            ])
        )
        elements.append(table)
        elements.append(Spacer(1, 15))

        # Metrics Summary Block
        summary_text = (
            f"<b>Total Bookings:</b> {len(appointments)} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Confirmed/Completed Revenue:</b> {biz['currency']}{total_rev:,.2f}"
        )
        elements.append(Paragraph(summary_text, h2_style))

        doc.build(elements)
        return output_path
