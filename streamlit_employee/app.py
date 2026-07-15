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

def _uid_short():
    import uuid
    return str(uuid.uuid4())[:6]

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
        tasks = proj.get("tasks", [])
        task_count = len(tasks) + sum(len(t.get("subtasks", [])) for t in tasks)
        count_label = f" — {task_count} tasks" if task_count > 0 else ""
        with st.expander(
            f"**{proj['name']}** — {proj.get('client_name', '')}{count_label}"
        ):
            if tasks:
                for task in tasks:
                    status = task.get("status", "Not Started")
                    assigned = task.get("assigned_to", "")
                    css = f"stage-{status.lower().replace(' ', '-')}"
                    assign_str = f" → {assigned}" if assigned else ""
                    st.markdown(
                        f'<span class="stage-badge {css}">{task.get("name", "")}: '
                        f'{status}{assign_str}</span>', unsafe_allow_html=True)
                    for sub in task.get("subtasks", []):
                        s_status = sub.get("status", "Not Started")
                        s_css = f"stage-{s_status.lower().replace(' ', '-')}"
                        s_assign = f" → {sub.get('assigned_to', '')}" if sub.get("assigned_to") else ""
                        st.markdown(
                            f'&nbsp;&nbsp;&nbsp;&nbsp;<span class="stage-badge {s_css}">↳ {sub.get("name", "")}: '
                            f'{s_status}{s_assign}</span>', unsafe_allow_html=True)
            else:
                st.caption("No tasks added yet.")
"""
EMPLOYEE APP PATCH
==================
Replace the entire `page_projects()` function in streamlit_employee/app.py
with the function below.

This version uses:
  - A project dropdown selector at the top
  - An editable table (st.data_editor) with columns:
    Description | Assigned To | Status | Rev | Reviewer | Review Status
  - Auto-fail duplication: if review_status = Fail, a new task with
    revision+1 is auto-created on save
  - Add Task / Add Subtask buttons below the table
  - Edit project name/client + delete at the bottom
"""


def page_projects():
    st.markdown("### 📁 Projects")
    try:
        projects = api.list_projects()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    try:
        employees = api.list_employees()
    except Exception:
        employees = []
    emp_names = ["Unassigned"] + [e["name"] for e in employees]
    STATUS_OPTS = ["Not Started", "In Progress", "Review", "Completed"]
    REVIEW_OPTS = ["Not Started", "In Progress", "Pass", "Fail"]

    with st.expander("➕ Create New Project"):
        with st.form("new_proj"):
            a, b = st.columns(2)
            with a:
                name = st.text_input("Project Name *")
                client = st.text_input("Client Name")
            with b:
                sd = st.date_input("Start Date", value=date.today())
            desc = st.text_area("Description", height=80)
            if st.form_submit_button("Create Project", type="primary",
                                     use_container_width=True):
                if name:
                    try:
                        api.create_project(name, client, 0,
                                           sd.isoformat(), desc)
                        st.success(f"'{name}' created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    if not projects:
        st.info("No projects yet.")
        return

    # ── Project selector ──
    proj_names = {f"{p['name']} — {p.get('client_name', '')}": p["id"] for p in projects}
    selected_label = st.selectbox("Select Project", list(proj_names.keys()))
    selected_id = proj_names[selected_label]
    proj = next(p for p in projects if p["id"] == selected_id)

    st.markdown(f"**Client:** {proj.get('client_name', '—')} · "
                f"**Started:** {proj.get('start_date', '—')}")

    # ── Flatten tasks into table rows ──
    tasks = proj.get("tasks", [])
    rows = []
    for tidx, task in enumerate(tasks):
        rows.append({
            "_idx": len(rows), "_task_idx": tidx, "_sub_idx": -1,
            "_id": task.get("id", f"t{tidx}"),
            "Description": task.get("description", task.get("name", "")),
            "Assigned To": task.get("assigned_to", "") or "Unassigned",
            "Status": task.get("status", "Not Started"),
            "Rev": int(task.get("revision", 1)),
            "Reviewer": task.get("reviewer", "") or "Unassigned",
            "Review Status": task.get("review_status", "Not Started"),
        })
        for sidx, sub in enumerate(task.get("subtasks", [])):
            rows.append({
                "_idx": len(rows), "_task_idx": tidx, "_sub_idx": sidx,
                "_id": sub.get("id", f"s{tidx}_{sidx}"),
                "Description": "  ↳ " + (sub.get("description", sub.get("name", ""))),
                "Assigned To": sub.get("assigned_to", "") or "Unassigned",
                "Status": sub.get("status", "Not Started"),
                "Rev": int(sub.get("revision", 1)),
                "Reviewer": sub.get("reviewer", "") or "Unassigned",
                "Review Status": sub.get("review_status", "Not Started"),
            })

    if rows:
        df = pd.DataFrame(rows)
        display_cols = ["Description", "Assigned To", "Status", "Rev", "Reviewer", "Review Status"]

        edited_df = st.data_editor(
            df[display_cols],
            column_config={
                "Description": st.column_config.TextColumn("Description", width="large"),
                "Assigned To": st.column_config.SelectboxColumn("Assigned To", options=emp_names, width="medium"),
                "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTS, width="medium"),
                "Rev": st.column_config.NumberColumn("Rev", min_value=1, step=1, width="small"),
                "Reviewer": st.column_config.SelectboxColumn("Reviewer", options=emp_names, width="medium"),
                "Review Status": st.column_config.SelectboxColumn("Review Status", options=REVIEW_OPTS, width="medium"),
            },
            use_container_width=True, hide_index=True, num_rows="dynamic",
            key=f"emp_task_table_{selected_id}",
        )

        if st.button("💾 Save Tasks", key=f"esave_{selected_id}", type="primary"):
            new_rows = []
            for i in range(len(edited_df)):
                row = edited_df.iloc[i]
                desc_raw = row["Description"] if isinstance(row["Description"], str) else str(row["Description"])
                desc_clean = desc_raw.lstrip(" ↳").strip()
                assigned = row.get("Assigned To", "Unassigned")
                if assigned == "Unassigned": assigned = ""
                reviewer = row.get("Reviewer", "Unassigned")
                if reviewer == "Unassigned": reviewer = ""
                is_sub = False
                orig_id = f"t_{_uid_short()}"
                if i < len(df):
                    is_sub = df.iloc[i]["_sub_idx"] >= 0
                    orig_id = df.iloc[i]["_id"]
                item = {
                    "id": orig_id, "description": desc_clean, "name": desc_clean,
                    "revision": int(row.get("Rev", 1)),
                    "assigned_to": assigned,
                    "status": row.get("Status", "Not Started"),
                    "reviewer": reviewer,
                    "review_status": row.get("Review Status", "Not Started"),
                }
                new_rows.append((is_sub, item))

            result_tasks = []
            current_task = None
            for is_sub, item in new_rows:
                if not is_sub:
                    if current_task is not None:
                        result_tasks.append(current_task)
                    current_task = {**item, "subtasks": []}
                else:
                    if current_task is not None:
                        current_task["subtasks"].append(item)
                    else:
                        result_tasks.append({**item, "subtasks": []})
            if current_task is not None:
                result_tasks.append(current_task)

            # Auto-create revision on Fail
            fail_dups = []
            for task in result_tasks:
                if task.get("status") == "Review" and task.get("review_status") == "Fail":
                    fail_dups.append({
                        "id": f"t_{_uid_short()}", "description": task["description"],
                        "name": task["description"], "revision": task.get("revision", 1) + 1,
                        "assigned_to": task["assigned_to"], "status": "Not Started",
                        "reviewer": "", "review_status": "Not Started", "subtasks": [],
                    })
                sub_dups = []
                for sub in task.get("subtasks", []):
                    if sub.get("status") == "Review" and sub.get("review_status") == "Fail":
                        sub_dups.append({
                            "id": f"s_{_uid_short()}", "description": sub["description"],
                            "name": sub["description"], "revision": sub.get("revision", 1) + 1,
                            "assigned_to": sub["assigned_to"], "status": "Not Started",
                            "reviewer": "", "review_status": "Not Started",
                        })
                task["subtasks"] = task.get("subtasks", []) + sub_dups
            result_tasks.extend(fail_dups)

            try:
                api.update_project(selected_id, {"tasks": result_tasks})
                st.success("Tasks saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("No tasks yet. Add one below.")

    # ── Add task / subtask ──
    st.markdown("---")
    ac1, ac2 = st.columns(2)
    with ac1:
        if st.button("➕ Add Task", key=f"eat_{selected_id}"):
            tasks.append({
                "id": f"t_{_uid_short()}", "description": "", "name": "",
                "revision": 1, "status": "Not Started", "assigned_to": "",
                "reviewer": "", "review_status": "Not Started", "subtasks": [],
            })
            api.update_project(selected_id, {"tasks": tasks})
            st.rerun()
    with ac2:
        if tasks:
            parent_names = [t.get("description", t.get("name", f"Task {i+1}"))
                           for i, t in enumerate(tasks)]
            add_to = st.selectbox("Add subtask to:", parent_names, key=f"east_{selected_id}")
            if st.button("➕ Add Subtask", key=f"eas_{selected_id}"):
                ti = parent_names.index(add_to)
                tasks[ti].setdefault("subtasks", []).append({
                    "id": f"s_{_uid_short()}", "description": "", "name": "",
                    "revision": 1, "status": "Not Started", "assigned_to": "",
                    "reviewer": "", "review_status": "Not Started",
                })
                api.update_project(selected_id, {"tasks": tasks})
                st.rerun()

    # ── Edit project details / delete ──
    st.markdown("---")
    with st.expander("✏️ Edit Project Details"):
        with st.form(f"edit_proj_{selected_id}"):
            new_name = st.text_input("Project Name", value=proj.get("name", ""))
            new_client = st.text_input("Client Name", value=proj.get("client_name", ""))
            if st.form_submit_button("Save Details"):
                try:
                    api.update_project(selected_id, {"name": new_name, "client_name": new_client})
                    st.success("Updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.button("🗑️ Delete Project", key=f"edp_{selected_id}"):
        try:
            api.delete_project(selected_id)
            st.success("Deleted!")
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

    # Project selection OUTSIDE form so task list updates dynamically
    proj_opts = {p["name"]: p["id"] for p in projects}
    sel_proj = st.selectbox("Project *", list(proj_opts.keys()), key="lt_proj")
    sel_proj_id = proj_opts[sel_proj]

    # Build task/subtask options from selected project
    sel_project_obj = next((p for p in projects if p["id"] == sel_proj_id), None)
    task_options = ["— No specific task —"]
    task_map = {}  # display_name -> (task_idx, subtask_idx or None)
    if sel_project_obj:
        tasks = sel_project_obj.get("tasks", [])
        for tidx, task in enumerate(tasks):
            t_name = task.get("name", f"Task {tidx+1}")
            label = f"📋 {t_name}"
            task_options.append(label)
            task_map[label] = (tidx, None)
            for sidx, sub in enumerate(task.get("subtasks", [])):
                s_name = sub.get("name", f"Subtask {sidx+1}")
                s_label = f"    ↳ {s_name}"
                task_options.append(s_label)
                task_map[s_label] = (tidx, sidx)

    with st.form("log_time"):
        a, b = st.columns(2)
        with a:
            sel_task_label = st.selectbox("Task / Subtask", task_options)
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
                    # Determine task name for the time log
                    task_name = ""
                    if sel_task_label in task_map:
                        tidx, sidx = task_map[sel_task_label]
                        tasks = sel_project_obj.get("tasks", [])
                        if sidx is not None:
                            task_name = tasks[tidx]["subtasks"][sidx].get("name", "")
                        else:
                            task_name = tasks[tidx].get("name", "")

                    api.create_time_log(
                        sel_emp_id, sel_proj_id,
                        hours, log_date.isoformat(), comments,
                        task_name=task_name,
                    )

                    # Auto-assign task if unassigned/not started
                    if sel_task_label in task_map and sel_project_obj:
                        tidx, sidx = task_map[sel_task_label]
                        tasks = sel_project_obj.get("tasks", [])
                        emp_name = emp_match["name"] if emp_match else next(
                            (e["name"] for e in employees if str(e["id"]) == str(sel_emp_id)), "")
                        changed = False
                        if sidx is not None:
                            sub = tasks[tidx]["subtasks"][sidx]
                            if sub.get("status") in ("Not Started", "") or not sub.get("assigned_to"):
                                tasks[tidx]["subtasks"][sidx]["status"] = "In Progress"
                                tasks[tidx]["subtasks"][sidx]["assigned_to"] = emp_name
                                changed = True
                        else:
                            t = tasks[tidx]
                            if t.get("status") in ("Not Started", "") or not t.get("assigned_to"):
                                tasks[tidx]["status"] = "In Progress"
                                tasks[tidx]["assigned_to"] = emp_name
                                changed = True
                        if changed:
                            api.update_project(sel_proj_id, {"tasks": tasks})

                    st.success(f"✅ Logged {hours}h on {sel_proj}" +
                               (f" → {task_name}" if task_name else ""))
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def page_my_logs(user):
    st.markdown("### 📋 My Time Logs")
    try:
        logs = api.list_time_logs()
        projects = api.list_projects()
        employees = api.list_employees()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    pm = {p["id"]: p["name"] for p in projects}
    em = {e["id"]: e["name"] for e in employees}

    # ── Filters ──
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_emp = st.selectbox("Filter Employee", ["All"] + [e["name"] for e in employees])
    with f2:
        sel_proj = st.selectbox("Filter Project", ["All"] + [p["name"] for p in projects])
    with f3:
        date_range = st.date_input("Date Range", value=[], key="date_filter")

    filtered = logs
    if sel_emp != "All":
        eid = next((e["id"] for e in employees if e["name"] == sel_emp), None)
        if eid:
            filtered = [l for l in filtered if str(l.get("employee_id")) == str(eid)]
    if sel_proj != "All":
        pid = next((p["id"] for p in projects if p["name"] == sel_proj), None)
        if pid:
            filtered = [l for l in filtered if str(l.get("project_id")) == str(pid)]
    if date_range:
        if len(date_range) == 2:
            start_d, end_d = date_range
            filtered = [l for l in filtered
                        if start_d.isoformat() <= l.get("date", "") <= end_d.isoformat()]
        elif len(date_range) == 1:
            filtered = [l for l in filtered if l.get("date", "") == date_range[0].isoformat()]

    if not filtered:
        st.info("No logs found for the selected filters.")
        return

    st.metric("Total Hours",
              f"{sum(float(l.get('hours', 0)) for l in filtered):.1f}h")

    sorted_logs = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

    # Table display
    df = pd.DataFrame([{
        "Date": l.get("date", ""),
        "Employee": em.get(l.get("employee_id"), "?"),
        "Project": pm.get(l.get("project_id"), "?"),
        "Task": l.get("task_name", "—") or "—",
        "Hours": float(l.get("hours", 0)),
        "Comments": l.get("comments", ""),
    } for l in sorted_logs])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Delete section
    with st.expander("🗑️ Delete Time Logs"):
        for l in sorted_logs[:50]:
            task_str = f" · {l.get('task_name')}" if l.get("task_name") else ""
            label = (f"{l.get('date', '')} · {em.get(l.get('employee_id'), '?')} · "
                     f"{pm.get(l.get('project_id'), '?')}{task_str} · "
                     f"{float(l.get('hours', 0)):.1f}h")
            col_t, col_d = st.columns([6, 1])
            with col_t:
                st.markdown(f"{label}")
            with col_d:
                if st.button("🗑️", key=f"dlog_{l['id']}"):
                    try:
                        api.delete_time_log(l["id"])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


def page_leaves(user):
    st.markdown("### 🏖️ Leave Tracker")
    try:
        leaves = api.list_leaves()
        employees = api.list_employees()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    emp_map = {e["id"]: e["name"] for e in employees}
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
                if employees:
                    emp_opts = {e["name"]: e["id"] for e in employees}
                    sel_emp_name = st.selectbox("Employee *", list(emp_opts.keys()))
                    sel_emp_id = emp_opts[sel_emp_name]
                else:
                    st.warning("No employees registered.")
                    sel_emp_id = None
                lt = st.selectbox("Leave Type *", LEAVE_TYPES)
            with b:
                sd = st.date_input("Start Date", value=date.today())
                ed = st.date_input("End Date", value=date.today())
            days = st.number_input("Number of Days", min_value=0.5, max_value=30.0, step=0.5, value=1.0)
            reason = st.text_area("Reason", height=80)
            if st.form_submit_button("Apply", type="primary", use_container_width=True):
                if not sel_emp_id:
                    st.error("Select an employee.")
                else:
                    try:
                        api.create_leave(sel_emp_id, sd.isoformat(), ed.isoformat(), lt, reason, days)
                        st.success("Leave applied!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    if leaves:
        status_icons = {"pending": "🟡", "approved": "✅", "rejected": "❌"}
        for l in leaves:
            icon = status_icons.get(l.get("status", ""), "🔘")
            emp_name = emp_map.get(l.get("employee_id"), "?")
            label = (f"{icon} {emp_name} · {l.get('leave_type', '')} · "
                     f"{l.get('start_date', '')} to {l.get('end_date', '')} · "
                     f"{float(l.get('days', 0)):.0f}d · {l.get('status', '').title()}")
            with st.expander(label):
                st.markdown(f"**Reason:** {l.get('reason', '—')}")
                col_del, _ = st.columns([1, 4])
                with col_del:
                    if st.button("🗑️ Delete", key=f"dlv_{l['id']}"):
                        try:
                            api.delete_leave(l["id"])
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    else:
        st.info("No leave records.")


def page_expenses(user):
    st.markdown("### 💳 Expense Tracker")
    try:
        expenses = api.list_expenses()
        employees = api.list_employees()
        projects = api.list_projects()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    emp_map = {e["id"]: e["name"] for e in employees}
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
                if employees:
                    emp_opts = {e["name"]: e["id"] for e in employees}
                    sel_emp_name = st.selectbox("Employee *", list(emp_opts.keys()))
                    sel_emp_id = emp_opts[sel_emp_name]
                else:
                    st.warning("No employees registered.")
                    sel_emp_id = None
                cat = st.selectbox("Category *", CATEGORIES)
            with b:
                amt = st.number_input("Amount (₹) *", min_value=0.0, step=100.0, format="%.2f")
                exp_date = st.date_input("Date", value=date.today())
            proj_opts = {"None": ""} | {p["name"]: p["id"] for p in projects}
            sel_proj = st.selectbox("Project (optional)", list(proj_opts.keys()))
            desc = st.text_area("Description", height=80, placeholder="e.g. Cab to site, flight to Mumbai...")
            if st.form_submit_button("Submit Expense", type="primary", use_container_width=True):
                if not sel_emp_id:
                    st.error("Select an employee.")
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
        for x in expenses:
            icon = status_icons.get(x.get("status", ""), "🔘")
            emp_name = emp_map.get(x.get("employee_id"), "?")
            label = (f"{icon} {emp_name} · {x.get('category', '')} · "
                     f"₹{float(x.get('amount', 0)):,.2f} · {x.get('date', '')} · "
                     f"{x.get('status', '').title()}")
            with st.expander(label):
                st.markdown(f"**Description:** {x.get('description', '—')}")
                st.markdown(f"**Project:** {pm.get(x.get('project_id'), '—')}")
                col_del, _ = st.columns([1, 4])
                with col_del:
                    if st.button("🗑️ Delete", key=f"dex_{x['id']}"):
                        try:
                            api.delete_expense(x["id"])
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
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
