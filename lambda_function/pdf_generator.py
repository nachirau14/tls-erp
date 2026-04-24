"""
pdf_generator.py – Generate professional Invoice and Quotation PDFs.
Matches the proforma invoice template style from theLOCALSTUDIO.

Called by the Lambda function. Uses reportlab.
"""

import io
import textwrap
from datetime import datetime
from decimal import Decimal

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image,
)
from reportlab.pdfgen import canvas


# ── Colors ──
CLR_DARK = HexColor("#2c2825")
CLR_TERRACOTTA = HexColor("#c4704b")
CLR_GREY = HexColor("#666666")
CLR_LIGHT = HexColor("#f5f2ec")
CLR_LINE = HexColor("#cccccc")


def _styles():
    """Build custom paragraph styles."""
    ss = getSampleStyleSheet()

    ss.add(ParagraphStyle("CompanyName", parent=ss["Normal"],
        fontName="Helvetica-Bold", fontSize=18, textColor=CLR_DARK,
        spaceAfter=2, alignment=TA_CENTER))

    ss.add(ParagraphStyle("CompanyTag", parent=ss["Normal"],
        fontName="Helvetica", fontSize=9, textColor=CLR_GREY,
        spaceAfter=12, alignment=TA_CENTER))

    ss.add(ParagraphStyle("DocTitle", parent=ss["Normal"],
        fontName="Helvetica-Bold", fontSize=16, textColor=CLR_DARK,
        spaceBefore=6, spaceAfter=12, alignment=TA_CENTER))

    ss.add(ParagraphStyle("SectionHead", parent=ss["Normal"],
        fontName="Helvetica-Bold", fontSize=10, textColor=CLR_DARK,
        spaceBefore=14, spaceAfter=6))

    ss.add(ParagraphStyle("Body", parent=ss["Normal"],
        fontName="Helvetica", fontSize=9, textColor=CLR_DARK,
        leading=13, spaceAfter=3))

    ss.add(ParagraphStyle("BodyBold", parent=ss["Normal"],
        fontName="Helvetica-Bold", fontSize=9, textColor=CLR_DARK,
        leading=13, spaceAfter=3))

    ss.add(ParagraphStyle("BodyRight", parent=ss["Normal"],
        fontName="Helvetica", fontSize=9, textColor=CLR_DARK,
        leading=13, spaceAfter=3, alignment=TA_RIGHT))

    ss.add(ParagraphStyle("BodyBoldRight", parent=ss["Normal"],
        fontName="Helvetica-Bold", fontSize=9, textColor=CLR_DARK,
        leading=13, spaceAfter=3, alignment=TA_RIGHT))

    ss.add(ParagraphStyle("Small", parent=ss["Normal"],
        fontName="Helvetica", fontSize=7.5, textColor=CLR_GREY,
        leading=10, alignment=TA_CENTER))

    ss.add(ParagraphStyle("AmountWords", parent=ss["Normal"],
        fontName="Helvetica-BoldOblique", fontSize=9, textColor=CLR_DARK,
        leading=13, spaceAfter=3, alignment=TA_RIGHT))

    return ss


def _num_to_words_inr(n):
    """Simple Indian number to words (handles up to crores)."""
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen",
            "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty",
            "Sixty", "Seventy", "Eighty", "Ninety"]

    if n == 0:
        return "Zero"

    def _chunk(num):
        if num < 20:
            return ones[num]
        if num < 100:
            return tens[num // 10] + ("" if num % 10 == 0 else " " + ones[num % 10])
        return ones[num // 100] + " Hundred" + ("" if num % 100 == 0 else " " + _chunk(num % 100))

    result = ""
    if n >= 10000000:
        result += _chunk(n // 10000000) + " Crore "
        n %= 10000000
    if n >= 100000:
        result += _chunk(n // 100000) + " Lakh "
        n %= 100000
    if n >= 1000:
        result += _chunk(n // 1000) + " Thousand "
        n %= 1000
    if n > 0:
        result += _chunk(n)

    return "Rupees " + result.strip() + " Only"


def _fmt_inr(amount):
    """Format as Indian Rupees."""
    return f"{float(amount):,.2f}"


def _header_footer(canvas_obj, doc, settings, doc_type, logo_bytes=None):
    """Draw header (logo, company info) and footer on each page."""
    canvas_obj.saveState()
    w, h = A4

    # ── Footer line ──
    contact_parts = []
    if settings.get("email"):
        contact_parts.append(settings["email"])
    if settings.get("phone"):
        contact_parts.append(settings["phone"])
    if settings.get("address"):
        contact_parts.append(settings["address"])
    footer_text = "  |  ".join(contact_parts) if contact_parts else ""

    if footer_text:
        canvas_obj.setStrokeColor(CLR_LINE)
        canvas_obj.line(20*mm, 18*mm, w - 20*mm, 18*mm)
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(CLR_GREY)
        canvas_obj.drawCentredString(w / 2, 13*mm, footer_text)

    canvas_obj.restoreState()


def generate_invoice_pdf(invoice, settings, logo_bytes=None):
    """Generate a professional invoice PDF. Returns bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm,
        topMargin=20*mm, bottomMargin=25*mm)

    ss = _styles()
    story = []

    # ── Logo ──
    if logo_bytes:
        try:
            logo_stream = io.BytesIO(logo_bytes)
            img = Image(logo_stream, width=60*mm, height=20*mm)
            img.hAlign = "CENTER"
            story.append(img)
            story.append(Spacer(1, 6*mm))
        except Exception:
            # Fallback to text if logo fails
            company_name = settings.get("account_name", "Studio")
            story.append(Paragraph(company_name, ss["CompanyName"]))
            tag = settings.get("company_tagline", "Architecture | Design")
            story.append(Paragraph(tag, ss["CompanyTag"]))
    else:
        # No logo uploaded — show company name as text
        company_name = settings.get("account_name", "Studio")
        story.append(Paragraph(company_name, ss["CompanyName"]))
        tag = settings.get("company_tagline", "Architecture | Design")
        story.append(Paragraph(tag, ss["CompanyTag"]))

    # ── Document title ──
    inv_type = invoice.get("invoice_type", "tax")
    title = "PROFORMA INVOICE" if inv_type == "proforma" else "TAX INVOICE"
    story.append(Paragraph(title, ss["DocTitle"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=CLR_LINE))
    story.append(Spacer(1, 3*mm))

    # ── TO / DATE row ──
    date_str = invoice.get("date", "")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_formatted = dt.strftime("%d.%m.%Y")
    except Exception:
        date_formatted = date_str

    to_data = [[
        Paragraph(f"<b>TO:</b><br/>{invoice.get('client_name', '')}", ss["Body"]),
        Paragraph(f"<b>DATE</b> {date_formatted}", ss["BodyBoldRight"]),
    ]]
    t = Table(to_data, colWidths=["60%", "40%"])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t)
    story.append(Spacer(1, 4*mm))

    # ── Invoice details ──
    inv_num = invoice.get("invoice_number", "")
    details = [
        ["BILL NO:", inv_num],
        ["PROJECT NAME:", invoice.get("description", "")],
    ]
    if invoice.get("client_gst"):
        details.append(["CLIENT GST:", invoice["client_gst"]])
    details.append(["GST NO:", settings.get("gstin", "")])

    for label, val in details:
        row = [[Paragraph(f"<b>{label}</b>", ss["Body"]),
                Paragraph(str(val), ss["BodyBold"])]]
        t = Table(row, colWidths=["35%", "65%"])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        story.append(t)

    story.append(Spacer(1, 5*mm))

    # ── Custom Notes (multi-line free text like TOTAL DESIGN FEE, AMOUNT PAID etc.) ──
    custom_notes = invoice.get("custom_notes", "")
    if custom_notes and custom_notes.strip():
        for line in custom_notes.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, ss["Body"]))
        story.append(Spacer(1, 4*mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=CLR_LINE))
    story.append(Spacer(1, 3*mm))

    # ── Amounts ──
    basic = float(invoice.get("basic_amount", 0))
    gst = float(invoice.get("gst", 0))
    tds = float(invoice.get("tds", 0))
    total = float(invoice.get("total", 0))
    receivable = float(invoice.get("receivable", 0))
    cgst = gst / 2
    sgst = gst / 2

    amount_rows = [
        [Paragraph("<b>BASIC AMOUNT</b>", ss["Body"]),
         Paragraph(f"<b>{_fmt_inr(basic)}</b>", ss["BodyBoldRight"])],
        [Paragraph("CGST @9%", ss["Body"]),
         Paragraph(f"{_fmt_inr(cgst)}", ss["BodyRight"])],
        [Paragraph("SGST @9%", ss["Body"]),
         Paragraph(f"{_fmt_inr(sgst)}", ss["BodyRight"])],
    ]
    t = Table(amount_rows, colWidths=["65%", "35%"])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)

    story.append(HRFlowable(width="100%", thickness=1, color=CLR_DARK))
    story.append(Spacer(1, 2*mm))

    total_row = [[
        Paragraph("<b>TOTAL AMOUNT WITH GST</b>", ss["BodyBold"]),
        Paragraph(f"<b>{_fmt_inr(total)}</b>", ss["BodyBoldRight"]),
    ]]
    t = Table(total_row, colWidths=["65%", "35%"])
    story.append(t)

    # TDS note
    tds_row = [[
        Paragraph("Less: TDS @10% (deducted by client)", ss["Body"]),
        Paragraph(f"-{_fmt_inr(tds)}", ss["BodyRight"]),
    ]]
    t = Table(tds_row, colWidths=["65%", "35%"])
    story.append(t)

    story.append(Spacer(1, 2*mm))
    recv_row = [[
        Paragraph("<b>NET RECEIVABLE</b>", ss["BodyBold"]),
        Paragraph(f"<b>{_fmt_inr(receivable)}</b>", ss["BodyBoldRight"]),
    ]]
    t = Table(recv_row, colWidths=["65%", "35%"])
    story.append(t)

    # Amount in words
    story.append(Spacer(1, 2*mm))
    words = _num_to_words_inr(int(round(total)))
    story.append(Paragraph(words, ss["AmountWords"]))

    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Kindly release at the earliest.", ss["Body"]))
    story.append(Paragraph("Thank you,", ss["Body"]))
    story.append(Spacer(1, 8*mm))

    # Signatory
    story.append(Paragraph("<b>Authorized Signatory</b>", ss["Body"]))
    if settings.get("signatory_name"):
        story.append(Paragraph(f"<b>{settings['signatory_name']}</b>", ss["BodyBold"]))
    if settings.get("signatory_title"):
        story.append(Paragraph(settings["signatory_title"], ss["Body"]))

    # ── Bank details ──
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=CLR_LINE))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("<b>BANK DETAILS</b>", ss["SectionHead"]))

    bank_rows = []
    for label, key in [("Name:", "account_name"), ("Bank Name:", "bank_name"),
                        ("Branch:", "branch"), ("Account Number:", "account_number"),
                        ("IFSC Code:", "ifsc")]:
        val = settings.get(key, "")
        if val:
            bank_rows.append([Paragraph(label, ss["Body"]),
                              Paragraph(val, ss["BodyBold"])])
    if bank_rows:
        t = Table(bank_rows, colWidths=["35%", "65%"])
        t.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        story.append(t)

    doc.build(story, onFirstPage=lambda c, d: _header_footer(c, d, settings, "invoice", logo_bytes),
              onLaterPages=lambda c, d: _header_footer(c, d, settings, "invoice", logo_bytes))
    return buf.getvalue()


def generate_quotation_pdf(quotation, settings, logo_bytes=None):
    """Generate a professional quotation PDF. Returns bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm,
        topMargin=20*mm, bottomMargin=25*mm)

    ss = _styles()
    story = []

    # ── Logo ──
    if logo_bytes:
        try:
            logo_stream = io.BytesIO(logo_bytes)
            img = Image(logo_stream, width=60*mm, height=20*mm)
            img.hAlign = "CENTER"
            story.append(img)
            story.append(Spacer(1, 6*mm))
        except Exception:
            company_name = settings.get("account_name", "Studio")
            story.append(Paragraph(company_name, ss["CompanyName"]))
            tag = settings.get("company_tagline", "Architecture | Design")
            story.append(Paragraph(tag, ss["CompanyTag"]))
    else:
        company_name = settings.get("account_name", "Studio")
        story.append(Paragraph(company_name, ss["CompanyName"]))
        tag = settings.get("company_tagline", "Architecture | Design")
        story.append(Paragraph(tag, ss["CompanyTag"]))

    # ── Title ──
    story.append(Paragraph("QUOTATION", ss["DocTitle"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=CLR_LINE))
    story.append(Spacer(1, 3*mm))

    # ── TO / DATE ──
    date_str = quotation.get("date", "")
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_formatted = dt.strftime("%d.%m.%Y")
    except Exception:
        date_formatted = date_str

    to_data = [[
        Paragraph(f"<b>TO:</b><br/>{quotation.get('client_name', '')}", ss["Body"]),
        Paragraph(f"<b>DATE</b> {date_formatted}", ss["BodyBoldRight"]),
    ]]
    t = Table(to_data, colWidths=["60%", "40%"])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t)
    story.append(Spacer(1, 3*mm))

    # ── Quotation details ──
    qtn_num = quotation.get("quotation_number", "")
    details = [
        ["QUOTATION NO:", qtn_num],
        ["PROJECT:", quotation.get("project_name", "")],
    ]
    if quotation.get("total_amount"):
        details.append(["QUOTED AMOUNT:", f"{_fmt_inr(float(quotation['total_amount']))}"])

    for label, val in details:
        row = [[Paragraph(f"<b>{label}</b>", ss["Body"]),
                Paragraph(str(val), ss["BodyBold"])]]
        t = Table(row, colWidths=["35%", "65%"])
        t.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        story.append(t)

    story.append(Spacer(1, 4*mm))

    # ── Subject line ──
    subject = quotation.get("subject", "")
    if subject and subject.strip():
        story.append(HRFlowable(width="100%", thickness=0.3, color=CLR_LINE))
        story.append(Paragraph(f"<b>SUBJECT</b>", ss["SectionHead"]))
        story.append(Paragraph(subject, ss["Body"]))
        story.append(Spacer(1, 3*mm))

    # ── Sections ──
    sections = [
        ("SCOPE OF WORK", quotation.get("scope", "")),
        ("TIMELINES", quotation.get("timelines", "")),
        ("DELIVERABLES", quotation.get("deliverables", "")),
        ("LEGAL CLAUSES", quotation.get("legal_clauses", "")),
        ("PAYMENT STRUCTURE", quotation.get("payment_structure", "")),
    ]

    for title, content in sections:
        if content and content.strip():
            story.append(HRFlowable(width="100%", thickness=0.3, color=CLR_LINE))
            story.append(Paragraph(f"<b>{title}</b>", ss["SectionHead"]))
            for line in content.split("\n"):
                line = line.strip()
                if line:
                    story.append(Paragraph(line, ss["Body"]))
            story.append(Spacer(1, 3*mm))

    # ── Signatory ──
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("We look forward to working with you.", ss["Body"]))
    story.append(Paragraph("Thank you,", ss["Body"]))
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("<b>Authorized Signatory</b>", ss["Body"]))
    if settings.get("signatory_name"):
        story.append(Paragraph(f"<b>{settings['signatory_name']}</b>", ss["BodyBold"]))
    if settings.get("signatory_title"):
        story.append(Paragraph(settings["signatory_title"], ss["Body"]))

    # ── Bank details ──
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=CLR_LINE))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("<b>BANK DETAILS</b>", ss["SectionHead"]))

    bank_rows = []
    for label, key in [("Name:", "account_name"), ("Bank Name:", "bank_name"),
                        ("Branch:", "branch"), ("Account Number:", "account_number"),
                        ("IFSC Code:", "ifsc"), ("PAN:", "pan"), ("GSTIN:", "gstin")]:
        val = settings.get(key, "")
        if val:
            bank_rows.append([Paragraph(label, ss["Body"]),
                              Paragraph(val, ss["BodyBold"])])
    if bank_rows:
        t = Table(bank_rows, colWidths=["35%", "65%"])
        t.setStyle(TableStyle([("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
        story.append(t)

    doc.build(story, onFirstPage=lambda c, d: _header_footer(c, d, settings, "quotation", logo_bytes),
              onLaterPages=lambda c, d: _header_footer(c, d, settings, "quotation", logo_bytes))
    return buf.getvalue()
