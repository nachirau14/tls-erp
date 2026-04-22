"""Shared constants and helpers for the Studio ERP."""

PROJECT_STAGES = [
    "2D Plans", "End Views", "Elevations", "3D Modeling",
    "Rendering", "Presentation", "Site", "Checking",
]
STAGE_STATUS_OPTIONS = ["Not Started", "In Progress", "Review", "Completed"]
GST_RATE = 0.18
TDS_RATE = 0.10
ROLE_ADMIN = "admin"
ROLE_EMPLOYEE = "employee"

def compute_invoice_amounts(basic_amount: float) -> dict:
    gst = round(basic_amount * GST_RATE, 2)
    tds = round(basic_amount * TDS_RATE, 2)
    total = round(basic_amount + gst, 2)
    receivable = round((basic_amount - tds) + gst, 2)
    return {"basic_amount": basic_amount, "gst": gst, "tds": tds, "total": total, "receivable": receivable}

def compute_hourly_cost(monthly_salary: float) -> dict:
    daily = round(monthly_salary / 30, 2)
    hourly = round(daily / 8, 2)
    return {"monthly": monthly_salary, "daily": daily, "hourly": hourly}

def quarter_label(month: int) -> str:
    if month in (4,5,6): return "Q1"
    if month in (7,8,9): return "Q2"
    if month in (10,11,12): return "Q3"
    return "Q4"

def fy_label(year: int, month: int) -> str:
    if month >= 4: return f"FY{year}-{str(year+1)[2:]}"
    return f"FY{year-1}-{str(year)[2:]}"
