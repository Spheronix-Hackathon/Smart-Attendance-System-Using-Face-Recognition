import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

from typing import Any

def generate_excel_report(records: list[dict | Any]) -> io.BytesIO:
    """
    Generates an Excel report from a list of attendance records.
    """
    processed = []
    for r in records:
        if hasattr(r, "model_dump"):
            processed.append(r.model_dump())
        elif hasattr(r, "dict"):
            processed.append(r.dict())
        else:
            processed.append(r)
            
    df = pd.DataFrame(processed)
    
    # Rename columns for better readability if they exist
    column_mapping = {
        "id": "Student ID",
        "roll_number": "Roll Number",
        "full_name": "Student Name",
        "email": "Email",
        "department": "Department",
        "date": "Date",
        "status": "Status",
        "check_in": "Check-in Time",
        "method": "Method",
        "marked_by_name": "Marked By",
    }
    
    # Filter to only existing columns in the data
    existing_cols = [col for col in column_mapping.keys() if col in df.columns]
    df = df[existing_cols].rename(columns={col: column_mapping[col] for col in existing_cols})
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance Report')
    
    output.seek(0)
    return output

def generate_pdf_report(records: list[dict | Any], title: str) -> io.BytesIO:
    """
    Generates a PDF report from a list of attendance records using reportlab.
    """
    processed = []
    for r in records:
        if hasattr(r, "model_dump"):
            processed.append(r.model_dump())
        elif hasattr(r, "dict"):
            processed.append(r.dict())
        else:
            processed.append(r)
            
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=1, # Center
        spaceAfter=20,
        textColor=colors.HexColor("#00d1c7") # SmartFace Cyan
    )
    
    # Add Title
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Prepare Table Data
    headers = ["Student ID", "Roll Number", "Name", "Email", "Department", "Date", "Status", "Time", "Method", "Marked By"]
    data = [headers]
    
    for r in processed:
        data.append([
            str(r.get("id", "--")),
            str(r.get("roll_number", "---")),
            str(r.get("full_name") or r.get("email", "Unknown")),
            str(r.get("email", "Unknown")),
            str(r.get("department", "Unknown")),
            str(r.get("date", "--")),
            str(r.get("status", "Absent")),
            str(r.get("check_in", "--:--")),
            str(r.get("method", "System")),
            str(r.get("marked_by_name") or "--")
        ])
    
    # Create Table
    table = Table(data, colWidths=[60, 70, 100, 110, 80, 60, 60, 65, 70, 90])
    
    # Add Table Style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    table.setStyle(style)
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    output.seek(0)
    return output
