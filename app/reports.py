"""
PDF report generation using reportlab.
"""
# Complexity overview:
# - Time: O(n) where n is rows rendered into report tables.
# - Space: O(n) for in-memory PDF buffer/content.
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def generate_report_pdf(stats: dict, user_name: str) -> bytes:
    """Generate a PDF financial report from dashboard stats."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=24, textColor=colors.HexColor("#4A6741")
    )
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Heading2"],
        fontSize=14, textColor=colors.HexColor("#4A6741")
    )

    elements = []
    elements.append(Paragraph("Personal Finance Report", title_style))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        f"Prepared for: <b>{user_name}</b>", styles["Normal"]
    ))
    elements.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%B %d, %Y')}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 24))

    # Summary
    elements.append(Paragraph("Financial Summary", heading_style))
    elements.append(Spacer(1, 8))
    summary_data = [
        ["Metric", "Value"],
        ["Total Transactions", str(stats["total_transactions"])],
        ["Total Income", f"${stats['total_income']:,.2f}"],
        ["Total Expenses", f"${stats['total_expenses']:,.2f}"],
        ["Net Balance", f"${stats['net_balance']:,.2f}"],
    ]
    t = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A6741")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9F8F6")),
        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E8E6E1")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 24))

    # Category breakdown
    if stats["by_category"]:
        elements.append(Paragraph("Spending by Category", heading_style))
        elements.append(Spacer(1, 8))
        data = [["Category", "Amount"]]
        for c in stats["by_category"][:15]:
            data.append([c["name"], f"${c['value']:,.2f}"])
        t = Table(data, colWidths=[3 * inch, 2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C07C5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9F8F6")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E8E6E1")),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 24))

    # Trends
    if stats["trends"]:
        elements.append(Paragraph("Monthly Trends", heading_style))
        elements.append(Spacer(1, 8))
        data = [["Month", "Income", "Expenses"]]
        for t_row in stats["trends"][-12:]:
            data.append([
                t_row["month"],
                f"${t_row['income']:,.2f}",
                f"${t_row['expenses']:,.2f}",
            ])
        t = Table(data, colWidths=[2 * inch, 2 * inch, 2 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D4A373")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2C302B")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9F8F6")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#E8E6E1")),
        ]))
        elements.append(t)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
