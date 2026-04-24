"""
api_client.py – HTTP wrapper for both Streamlit apps.
Calls the Lambda backend via API Gateway.
"""

import requests
import streamlit as st


def get_base_url():
    """Read API base URL from Streamlit secrets or env var."""
    try:
        return st.secrets["API_BASE_URL"].rstrip("/")
    except Exception:
        import os
        return os.environ.get("API_BASE_URL", "http://localhost:8080").rstrip("/")


class ApiError(Exception):
    """Raised when the backend returns an error."""
    def __init__(self, message, status_code=None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def _handle_response(r):
    """Parse response – raise ApiError with real message on failure."""
    try:
        data = r.json()
    except Exception:
        # Response is not JSON
        if r.status_code >= 400:
            raise ApiError(
                f"HTTP {r.status_code}: {r.text[:300]}",
                r.status_code,
            )
        raise ApiError(f"Non-JSON response: {r.text[:300]}")

    if r.status_code >= 400:
        msg = data.get("error", data.get("message", f"HTTP {r.status_code}"))
        raise ApiError(msg, r.status_code)

    return data


def _get(path, params=None):
    url = f"{get_base_url()}{path}"
    r = requests.get(url, params=params, timeout=30)
    return _handle_response(r)


def _post(path, data):
    url = f"{get_base_url()}{path}"
    r = requests.post(url, json=data, timeout=30)
    return _handle_response(r)


def _put(path, data):
    url = f"{get_base_url()}{path}"
    r = requests.put(url, json=data, timeout=30)
    return _handle_response(r)


def _delete(path):
    url = f"{get_base_url()}{path}"
    r = requests.delete(url, timeout=30)
    return _handle_response(r)


# ─── Auth ───

def login(username, password):
    return _post("/auth/login", {"username": username, "password": password})


def register_user(username, password, role, display_name="", employee_id=""):
    return _post("/auth/register", {
        "username": username, "password": password, "role": role,
        "display_name": display_name, "employee_id": employee_id,
    })


def list_users():
    return _get("/auth/users")


# ─── Employees ───

def list_employees():
    return _get("/employees")


def create_employee(name, role, salary):
    return _post("/employees", {"name": name, "role": role, "salary": salary})


def delete_employee(emp_id):
    return _delete(f"/employees/{emp_id}")


def update_employee(emp_id, data):
    return _put(f"/employees/{emp_id}", data)


# ─── Projects ───

def list_projects():
    return _get("/projects")


def create_project(name, client_name, total_cost, start_date, description=""):
    return _post("/projects", {
        "name": name, "client_name": client_name,
        "total_cost": total_cost, "start_date": start_date,
        "description": description,
    })


def update_project(proj_id, data):
    return _put(f"/projects/{proj_id}", data)


def delete_project(proj_id):
    return _delete(f"/projects/{proj_id}")


# ─── Time Logs ───

def list_time_logs(employee_id=None, project_id=None):
    params = {}
    if employee_id:
        params["employee_id"] = employee_id
    if project_id:
        params["project_id"] = project_id
    return _get("/timelogs", params=params)


def create_time_log(employee_id, project_id, hours, date, comments=""):
    return _post("/timelogs", {
        "employee_id": employee_id, "project_id": project_id,
        "hours": hours, "date": date, "comments": comments,
    })


def delete_time_log(log_id):
    return _delete(f"/timelogs/{log_id}")


# ─── Invoices ───

def list_invoices(quarter=None, fy=None):
    params = {}
    if quarter:
        params["quarter"] = quarter
    if fy:
        params["fy"] = fy
    return _get("/invoices", params=params)


def create_invoice(client_name, amount, date, description="",
                   invoice_type="tax", project_id=""):
    return _post("/invoices", {
        "client_name": client_name, "amount": amount, "date": date,
        "description": description, "invoice_type": invoice_type,
        "project_id": project_id,
    })


def update_invoice(inv_id, data):
    return _put(f"/invoices/{inv_id}", data)


def delete_invoice(inv_id):
    return _delete(f"/invoices/{inv_id}")


def generate_invoice_pdf(inv_id):
    return _post(f"/invoices/{inv_id}/pdf", {})


# ─── Quotations ───

def list_quotations():
    return _get("/quotations")


def create_quotation(data):
    return _post("/quotations", data)


def update_quotation(qtn_id, data):
    return _put(f"/quotations/{qtn_id}", data)


def delete_quotation(qtn_id):
    return _delete(f"/quotations/{qtn_id}")


def generate_quotation_pdf(qtn_id):
    return _post(f"/quotations/{qtn_id}/pdf", {})


# ─── Logo ───

def get_logo_url():
    return _get("/logo")


def upload_logo(base64_data, content_type="image/png"):
    return _post("/logo", {"base64": base64_data, "content_type": content_type})


# ─── Bank Details ───

def get_bank_details():
    return _get("/bank-details")


def update_bank_details(data):
    return _put("/bank-details", data)


# ─── Leaves ───

def list_leaves(employee_id=None):
    params = {}
    if employee_id:
        params["employee_id"] = employee_id
    return _get("/leaves", params=params)


def create_leave(employee_id, start_date, end_date, leave_type,
                 reason="", days=1):
    return _post("/leaves", {
        "employee_id": employee_id, "start_date": start_date,
        "end_date": end_date, "leave_type": leave_type,
        "reason": reason, "days": days,
    })


def update_leave(leave_id, data):
    return _put(f"/leaves/{leave_id}", data)


def delete_leave(leave_id):
    return _delete(f"/leaves/{leave_id}")


# ─── Expenses ───

def list_expenses(employee_id=None):
    params = {}
    if employee_id:
        params["employee_id"] = employee_id
    return _get("/expenses", params=params)


def create_expense(employee_id, date, amount, category,
                   description="", project_id=""):
    return _post("/expenses", {
        "employee_id": employee_id, "date": date, "amount": amount,
        "category": category, "description": description,
        "project_id": project_id,
    })


def update_expense(exp_id, data):
    return _put(f"/expenses/{exp_id}", data)


def delete_expense(exp_id):
    return _delete(f"/expenses/{exp_id}")


# ─── Holidays ───

def list_holidays(year=None):
    params = {}
    if year:
        params["year"] = year
    return _get("/holidays", params=params)


def create_holiday(date, name, year=None, optional=False):
    return _post("/holidays", {
        "date": date, "name": name,
        "year": year or date[:4], "optional": optional,
    })


def update_holiday(hol_id, data):
    return _put(f"/holidays/{hol_id}", data)


def delete_holiday(hol_id):
    return _delete(f"/holidays/{hol_id}")
