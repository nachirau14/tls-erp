"""
Employee Portal – Streamlit
────────────────────────────
• Login (employee / admin role)
• Dashboard with personal stats
• View / create / edit projects & stages
• Log daily time entries
• View own time log history
"""

import streamlit as st
import pandas as pd
import sys, os
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import api_client as api
from api_client import ApiError
from styles import get_employee_css

st.set_page_config(page_title="Studio ERP – Employee", page_icon="⏱", layout="wide")

st.markdown(get_employee_css(), unsafe_allow_html=True)

STAGES = ["2D Plans","End Views","Elevations","3D Modeling",
          "Rendering","Presentation","Site","Checking"]
STATUSES = ["Not Started","In Progress","Review","Completed"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None


# ── LOGIN ──
def show_login():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("""<div class="login-card">
            <div class="login-title">⏱ Employee Portal</div>
            <div class="login-subtitle">Architectural Studio ERP</div>
        </div>""", unsafe_allow_html=True)

        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True,
                                     type="primary"):
                if not username or not password:
                    st.error("Enter both fields.")
                else:
                    try:
                        result = api.login(username, password)
                        u = result["user"]
                        if u["role"] not in ("employee", "admin"):
                            st.error("Access denied.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = u
                            st.rerun()
                    except ApiError as e:
                        st.error(f"Login failed: {e.message}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")


# ── APP ──
def show_app():
    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"### 👤 {user['display_name']}")
        st.caption(f"Role: {user['role'].title()}")
        st.divider()
        page = st.radio("Nav",
                        ["🏠 Dashboard", "📁 Projects", "⏱ Log Time",
                         "📋 My Time Logs", "🏖️ Leave Tracker",
                         "💳 Expenses", "📅 Holidays"],
                        label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    st.markdown(f"""<div class="emp-header">
        <h1>Welcome, {user['display_name']} 👋</h1>
        <p>{datetime.now().strftime('%A, %d %B %Y')}</p>
    </div>""", unsafe_allow_html=True)

    if "Dashboard" in page:
        page_dashboard(user)
    elif "Projects" in page:
        page_projects()
    elif "Log Time" in page:
        page_log_time(user)
    elif "My Time" in page:
        page_my_logs(user)
    elif "Leave" in page:
        page_leaves(user)
    elif "Expense" in page:
        page_expenses(user)
    elif "Holiday" in page:
        page_holidays()


def page_dashboard(user):
    try:
        projects = api.list_projects()
        logs = api.list_time_logs()
        emp_id = user.get("employee_id", "")
        my = ([l for l in logs
               if str(l.get("employee_id")) == str(emp_id)]
              if emp_id else [])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    active = len([p for p in projects if p.get("status") == "active"])
    total_h = sum(l.get("hours", 0) for l in my)
    this_m = datetime.now().strftime("%Y-%m")
    month_h = sum(l.get("hours", 0) for l in my
                  if l.get("date", "").startswith(this_m))
    today_s = datetime.now().strftime("%Y-%m-%d")
    today_h = sum(l.get("hours", 0) for l in my
                  if l.get("date") == today_s)

    c1, c2, c3, c4 = st.columns(4)
    for c, lbl, v in [
        (c1, "Active Projects", active),
        (c2, "Total Hours", f"{total_h:.1f}h"),
        (c3, "This Month", f"{month_h:.1f}h"),
        (c4, "Today", f"{today_h:.1f}h"),
    ]:
        with c:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="label">{lbl}</div>'
                f'<div class="value">{v}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("### 📁 Active Projects")
    for proj in [p for p in projects if p.get("status") == "active"]:
        stages = proj.get("stages", {})
        done = sum(1 for s in stages.values() if s == "Completed")
        pct = int(done / len(STAGES) * 100)
        with st.expander(
            f"**{proj['name']}** — {proj.get('client_name','')} ({pct}%)"
        ):
            st.progress(pct / 100)
            html = ""
            for sn in STAGES:
                status = stages.get(sn, "Not Started")
                css = f"stage-{status.lower().replace(' ', '-')}"
                html += f'<span class="stage-badge {css}">{sn}: {status}</span> '
            st.markdown(html, unsafe_allow_html=True)


def page_projects():
    st.markdown("### 📁 Projects")
    try:
        projects = api.list_projects()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    with st.expander("➕ Create New Project"):
        with st.form("new_proj"):
            a, b = st.columns(2)
            with a:
                name = st.text_input("Project Name *")
                client = st.text_input("Client Name")
            with b:
                cost = st.number_input("Total Receivable (₹)",
                                       min_value=0.0, step=10000.0,
                                       format="%.2f")
                sd = st.date_input("Start Date", value=date.today())
            desc = st.text_area("Description", height=80)
            if st.form_submit_button("Create Project", type="primary",
                                     use_container_width=True):
                if name:
                    try:
                        api.create_project(name, client, cost,
                                           sd.isoformat(), desc)
                        st.success(f"'{name}' created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    for proj in projects:
        stages = proj.get("stages", {})
        done = sum(1 for s in stages.values() if s == "Completed")
        pct = int(done / len(STAGES) * 100)
        with st.expander(
            f"**{proj['name']}** — {proj.get('client_name','')} "
            f"| {pct}% | ₹{float(proj.get('total_cost', 0)):,.2f}"
        ):
            st.progress(pct / 100)
            st.markdown("**Update Stages:**")
            new_stages = {}
            cols = st.columns(4)
            for idx, sn in enumerate(STAGES):
                with cols[idx % 4]:
                    cur = stages.get(sn, "Not Started")
                    new_stages[sn] = st.selectbox(
                        sn, STATUSES,
                        index=(STATUSES.index(cur)
                               if cur in STATUSES else 0),
                        key=f"s_{proj['id']}_{sn}",
                    )
            if st.button("💾 Save Stages", key=f"sv_{proj['id']}"):
                try:
                    api.update_project(proj["id"], {"stages": new_stages})
                    st.success("Updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def page_log_time(user):
    st.markdown("### ⏱ Log Time")
    try:
        projects = api.list_projects()
        employees = api.list_employees()
    except Exception as e:
        st.error(f"Error: {e}")
        return
    if not projects:
        st.warning("No projects found.")
        return

    emp_id = user.get("employee_id", "")
    emp_match = (next((e for e in employees
                       if str(e["id"]) == str(emp_id)), None)
                 if emp_id else None)

    with st.form("log_time"):
        a, b = st.columns(2)
        with a:
            proj_opts = {p["name"]: p["id"] for p in projects}
            sel_proj = st.selectbox("Project *", list(proj_opts.keys()))
            if emp_match:
                st.text_input("Employee", value=emp_match["name"],
                              disabled=True)
                sel_emp_id = emp_match["id"]
            else:
                emp_opts = {e["name"]: e["id"] for e in employees}
                if emp_opts:
                    sel_emp_id = emp_opts[
                        st.selectbox("Employee *", list(emp_opts.keys()))
                    ]
                else:
                    st.warning("No employees registered.")
                    sel_emp_id = None
        with b:
            hours = st.number_input("Hours *", min_value=0.5,
                                    max_value=16.0, step=0.5, value=1.0)
            log_date = st.date_input("Date", value=date.today())
        comments = st.text_area("What did you work on? *", height=100)
        if st.form_submit_button("📝 Log Time", type="primary",
                                 use_container_width=True):
            if not sel_emp_id:
                st.error("No employee profile linked.")
            elif not comments.strip():
                st.error("Describe your work.")
            else:
                try:
                    api.create_time_log(
                        sel_emp_id, proj_opts[sel_proj],
                        hours, log_date.isoformat(), comments,
                    )
                    st.success(f"✅ Logged {hours}h on {sel_proj}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def page_my_logs(user):
    st.markdown("### 📋 My Time Logs")
    emp_id = user.get("employee_id", "")
    try:
        logs = (api.list_time_logs(employee_id=emp_id)
                if emp_id else api.list_time_logs())
        projects = api.list_projects()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    pm = {p["id"]: p["name"] for p in projects}
    if not logs:
        st.info("No logs yet.")
        return

    st.metric("Total Hours",
              f"{sum(l.get('hours', 0) for l in logs):.1f}h")
    df = pd.DataFrame([{
        "Date": l.get("date", ""),
        "Project": pm.get(l.get("project_id"), "?"),
        "Hours": l.get("hours", 0),
        "Comments": l.get("comments", ""),
    } for l in logs]).sort_values(
        "Date", ascending=False
    ).reset_index(drop=True)
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_leaves(user):
    st.markdown("### 🏖️ Leave Tracker")
    emp_id = user.get("employee_id", "")
    try:
        leaves = api.list_leaves(employee_id=emp_id) if emp_id else api.list_leaves()
        employees = api.list_employees()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    emp_match = next((e for e in employees if str(e["id"]) == str(emp_id)), None) if emp_id else None
    LEAVE_TYPES = ["Casual Leave", "Sick Leave", "Earned Leave", "Comp Off", "Work From Home", "Half Day", "Other"]

    # Summary
    total_days = sum(float(l.get("days", 0)) for l in leaves)
    approved = sum(float(l.get("days", 0)) for l in leaves if l.get("status") == "approved")
    pending = sum(float(l.get("days", 0)) for l in leaves if l.get("status") == "pending")

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Requested", f"{total_days:.0f} days")
    with c2: st.metric("Approved", f"{approved:.0f} days")
    with c3: st.metric("Pending", f"{pending:.0f} days")

    with st.expander("➕ Apply for Leave"):
        with st.form("apply_leave"):
            a, b = st.columns(2)
            with a:
                lt = st.selectbox("Leave Type *", LEAVE_TYPES)
                sd = st.date_input("Start Date", value=date.today())
            with b:
                days = st.number_input("Number of Days", min_value=0.5, max_value=30.0, step=0.5, value=1.0)
                ed = st.date_input("End Date", value=date.today())
            reason = st.text_area("Reason", height=80)
            if st.form_submit_button("Apply", type="primary", use_container_width=True):
                sel_emp_id = emp_match["id"] if emp_match else emp_id
                if not sel_emp_id:
                    st.error("No employee profile linked.")
                else:
                    try:
                        api.create_leave(sel_emp_id, sd.isoformat(), ed.isoformat(), lt, reason, days)
                        st.success("Leave applied!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    if leaves:
        status_icons = {"pending": "🟡", "approved": "✅", "rejected": "❌"}
        df = pd.DataFrame([{
            "Status": status_icons.get(l.get("status", ""), "🔘") + " " + l.get("status", "").title(),
            "Type": l.get("leave_type", ""),
            "From": l.get("start_date", ""),
            "To": l.get("end_date", ""),
            "Days": float(l.get("days", 0)),
            "Reason": l.get("reason", ""),
        } for l in leaves])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No leave records.")


def page_expenses(user):
    st.markdown("### 💳 Expense Tracker")
    emp_id = user.get("employee_id", "")
    try:
        expenses = api.list_expenses(employee_id=emp_id) if emp_id else api.list_expenses()
        employees = api.list_employees()
        projects = api.list_projects()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    emp_match = next((e for e in employees if str(e["id"]) == str(emp_id)), None) if emp_id else None
    CATEGORIES = ["Site Visit", "Travel / Flight", "Cab / Transport", "Food & Meals", "Office Supplies", "Printing / Plotting", "Software / License", "Other"]
    pm = {p["id"]: p["name"] for p in projects}

    # Summary
    total = sum(float(x.get("amount", 0)) for x in expenses)
    approved = sum(float(x.get("amount", 0)) for x in expenses if x.get("status") == "approved")
    pending = sum(float(x.get("amount", 0)) for x in expenses if x.get("status") == "pending")

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Claimed", f"₹{total:,.2f}")
    with c2: st.metric("Approved", f"₹{approved:,.2f}")
    with c3: st.metric("Pending", f"₹{pending:,.2f}")

    with st.expander("➕ Add Expense"):
        with st.form("add_expense"):
            a, b = st.columns(2)
            with a:
                cat = st.selectbox("Category *", CATEGORIES)
                amt = st.number_input("Amount (₹) *", min_value=0.0, step=100.0, format="%.2f")
            with b:
                exp_date = st.date_input("Date", value=date.today())
                proj_opts = {"None": ""} | {p["name"]: p["id"] for p in projects}
                sel_proj = st.selectbox("Project (optional)", list(proj_opts.keys()))
            desc = st.text_area("Description", height=80, placeholder="e.g. Cab to site, flight to Mumbai...")
            if st.form_submit_button("Submit Expense", type="primary", use_container_width=True):
                sel_emp_id = emp_match["id"] if emp_match else emp_id
                if not sel_emp_id:
                    st.error("No employee profile linked.")
                elif amt <= 0:
                    st.error("Enter a valid amount.")
                else:
                    try:
                        api.create_expense(sel_emp_id, exp_date.isoformat(), amt, cat, desc, proj_opts[sel_proj])
                        st.success("Expense submitted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    if expenses:
        status_icons = {"pending": "🟡", "approved": "✅", "rejected": "❌"}
        df = pd.DataFrame([{
            "Status": status_icons.get(x.get("status", ""), "🔘") + " " + x.get("status", "").title(),
            "Date": x.get("date", ""),
            "Category": x.get("category", ""),
            "Amount (₹)": float(x.get("amount", 0)),
            "Project": pm.get(x.get("project_id"), "—"),
            "Description": x.get("description", ""),
        } for x in expenses])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No expenses recorded.")


def page_holidays():
    st.markdown("### 📅 Holiday Calendar")
    try:
        current_year = str(datetime.now().year)
        holidays = api.list_holidays(year=current_year)
    except Exception as e:
        st.error(f"Error: {e}")
        return

    year_sel = st.selectbox("Year", [str(y) for y in range(2024, 2031)],
                            index=[str(y) for y in range(2024, 2031)].index(current_year)
                            if current_year in [str(y) for y in range(2024, 2031)] else 0)
    if year_sel != current_year:
        try:
            holidays = api.list_holidays(year=year_sel)
        except Exception as e:
            st.error(f"Error: {e}")
            return

    if holidays:
        df = pd.DataFrame([{
            "Date": h.get("date", ""),
            "Holiday": h.get("name", ""),
            "Type": "Optional" if h.get("optional") else "Gazetted",
        } for h in holidays])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(holidays)} holidays in {year_sel}")
    else:
        st.info(f"No holidays added for {year_sel} yet. Ask your admin to add them.")


# ── Entry ──
if not st.session_state.logged_in:
    show_login()
else:
    show_app()
