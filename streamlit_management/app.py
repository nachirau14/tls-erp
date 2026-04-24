"""
Management Portal – Streamlit (Admin Only)
───────────────────────────────────────────
Dashboard · Invoicing & GST · Quotations · Projects & Stages
Time Tracking · Cost of Labour · Employees & Users · Settings
"""

import streamlit as st
import pandas as pd
import sys, os
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import api_client as api
from api_client import ApiError
from styles import get_management_css

st.set_page_config(page_title="Studio ERP – Management", page_icon="🏛",
                   layout="wide")

st.markdown(get_management_css(), unsafe_allow_html=True)

STAGES = ["2D Plans", "End Views", "Elevations", "3D Modeling",
          "Rendering", "Presentation", "Site", "Checking"]
STATUSES = ["Not Started", "In Progress", "Review", "Completed"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

def fmt(n):
    try: return f"{n:,.2f}"
    except: return str(n)
def inr(n): return f"₹{fmt(float(n))}"


# ── LOGIN ──
def show_login():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("""<div class="login-card">
            <div class="login-title">🏛 Management Portal</div>
            <div class="login-subtitle">Architectural Studio ERP</div>
        </div>""", unsafe_allow_html=True)

        with st.form("login"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True,
                                     type="primary"):
                if not username or not password:
                    st.error("Fill in both fields.")
                else:
                    try:
                        result = api.login(username, password)
                        if result["user"]["role"] != "admin":
                            st.error("Admin credentials required.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = result["user"]
                            st.rerun()
                    except ApiError as e:
                        st.error(f"Login failed: {e.message}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

        # Debug helper
        with st.expander("🔧 Debug: Test API connection"):
            if st.button("Test Health Endpoint"):
                try:
                    url = api.get_base_url()
                    st.code(f"API URL: {url}")
                    import requests
                    r = requests.get(f"{url}/health", timeout=10)
                    st.code(f"Status: {r.status_code}\n{r.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")


# ── APP ──
def show_app():
    user = st.session_state.user
    with st.sidebar:
        st.markdown("### 🏛 Studio ERP")
        st.caption(f"**{user['display_name']}** (admin)")
        st.divider()
        page = st.radio("Nav", [
            "📊 Dashboard", "💰 Invoicing & GST", "📝 Quotations",
            "📁 Projects & Stages", "⏱ Time Tracking",
            "📈 Cost of Labour", "👥 Employees & Users",
            "🏖️ Leaves & Expenses", "📅 Holiday List", "⚙️ Settings",
        ], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

    st.markdown(f"""<div class="mgmt-header"><h1>Studio ERP – Management</h1>
        <p>{datetime.now().strftime('%A, %d %B %Y')}</p></div>""",
        unsafe_allow_html=True)

    routes = {
        "Dashboard": pg_dashboard, "Invoicing": pg_invoicing,
        "Quotation": pg_quotations, "Projects": pg_projects,
        "Time": pg_time, "Cost": pg_labour,
        "Employees": pg_employees, "Leaves": pg_leaves_expenses,
        "Holiday": pg_holidays, "Settings": pg_settings,
    }
    for k, fn in routes.items():
        if k in page:
            fn()
            break


# ═══ DASHBOARD ═══
def pg_dashboard():
    st.markdown("### 📊 Dashboard")
    try:
        inv = api.list_invoices()
        proj = api.list_projects()
        logs = api.list_time_logs()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    ti = sum(float(i.get("total", 0)) for i in inv)
    rc = sum(float(i.get("receivable", 0)) for i in inv if i.get("received"))
    pn = sum(float(i.get("receivable", 0)) for i in inv if not i.get("received"))
    gs = sum(float(i.get("gst", 0)) for i in inv)
    ac = len([p for p in proj if p.get("status") == "active"])
    hr = sum(float(l.get("hours", 0)) for l in logs)

    r1 = st.columns(3)
    for c, l, v in zip(r1,
        ["Total Invoiced", "Received", "Pending"],
        [inr(ti), inr(rc), inr(pn)]):
        with c:
            st.markdown(f'<div class="stat-card"><div class="label">{l}</div>'
                        f'<div class="value">{v}</div></div>',
                        unsafe_allow_html=True)
    r2 = st.columns(3)
    for c, l, v in zip(r2,
        ["GST Collected", "Active Projects", "Hours Logged"],
        [inr(gs), str(ac), f"{hr:.0f}h"]):
        with c:
            st.markdown(f'<div class="stat-card"><div class="label">{l}</div>'
                        f'<div class="value">{v}</div></div>',
                        unsafe_allow_html=True)

    if proj:
        st.markdown("---")
        st.markdown("#### Project Progress")
        for p in proj:
            stg = p.get("stages", {})
            d = sum(1 for s in stg.values() if s == "Completed")
            pct = int(d / len(STAGES) * 100) if STAGES else 0
            a, b = st.columns([1, 3])
            with a:
                st.markdown(f"**{p['name']}** ({pct}%)")
            with b:
                st.progress(pct / 100)


# ═══ INVOICING & GST ═══
def pg_invoicing():
    st.markdown("### 💰 Invoicing & GST")
    try:
        invoices = api.list_invoices()
    except Exception as e:
        st.error(f"Error: {e}")
        invoices = []

    quarters = sorted(set(i.get("quarter", "") for i in invoices
                          if i.get("quarter")))
    fys = sorted(set(i.get("fy", "") for i in invoices if i.get("fy")))
    f1, f2, _ = st.columns([1, 1, 2])
    with f1:
        sq = st.selectbox("Quarter", ["All"] + quarters)
    with f2:
        sf = st.selectbox("FY", ["All"] + fys)

    fl = invoices
    if sq != "All":
        fl = [i for i in fl if i.get("quarter") == sq]
    if sf != "All":
        fl = [i for i in fl if i.get("fy") == sf]

    tg = sum(float(i.get("gst", 0)) for i in fl)
    tr = sum(float(i.get("receivable", 0)) for i in fl)
    tp = sum(float(i.get("receivable", 0)) for i in fl if i.get("received"))
    tt = sum(float(i.get("tds", 0)) for i in fl)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("GST Collected", inr(tg))
    with c2: st.metric("Total Receivable", inr(tr))
    with c3: st.metric("Received", inr(tp))
    with c4: st.metric("TDS Deducted", inr(tt))

    with st.expander("➕ Create New Invoice"):
        with st.form("new_inv"):
            a, b = st.columns(2)
            with a:
                cn = st.text_input("Client Name *")
                desc = st.text_input("Description")
                it = st.selectbox("Type", ["tax", "proforma"])
            with b:
                amt = st.number_input("Basic Amount (₹) *", min_value=0.0,
                                      step=1000.0, format="%.2f")
                dt = st.date_input("Date", value=date.today())
            if amt > 0:
                g = round(amt * 0.18, 2)
                t = round(amt * 0.10, 2)
                tot = round(amt + g, 2)
                r = round((amt - t) + g, 2)
                st.info(f"Basic: {inr(amt)} + GST: {inr(g)} = "
                        f"Total: {inr(tot)} | TDS: {inr(t)} | "
                        f"Client pays: {inr(r)}")
            if st.form_submit_button("Create Invoice", type="primary",
                                     use_container_width=True):
                if cn and amt > 0:
                    try:
                        res = api.create_invoice(cn, amt, dt.isoformat(),
                                                 desc, it)
                        st.success(
                            f"Invoice {res.get('invoice_number', '')} created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    for inv in fl:
        paid = "✅" if inv.get("received") else "⏳"
        label = (f"{paid} **{inv.get('invoice_number', '')}** | "
                 f"{inv.get('date', '')} | {inv.get('client_name', '')} | "
                 f"{'Tax' if inv.get('invoice_type') == 'tax' else 'Proforma'} | "
                 f"Total: {inr(inv.get('total', 0))}")
        with st.expander(label):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Basic:** {inr(inv.get('basic_amount', 0))}")
                st.markdown(f"**GST:** {inr(inv.get('gst', 0))}")
                st.markdown(f"**TDS:** {inr(inv.get('tds', 0))}")
            with c2:
                st.markdown(f"**Total:** {inr(inv.get('total', 0))}")
                st.markdown(f"**Receivable:** {inr(inv.get('receivable', 0))}")
                st.markdown(f"**Description:** {inv.get('description', '—')}")

            b1, b2, b3 = st.columns(3)
            with b1:
                if inv.get("received"):
                    if st.button("Mark Unpaid", key=f"up_{inv['id']}"):
                        api.update_invoice(inv["id"], {"received": False})
                        st.rerun()
                else:
                    if st.button("Mark Paid ✓", key=f"pd_{inv['id']}"):
                        api.update_invoice(inv["id"], {"received": True})
                        st.rerun()
            with b2:
                if st.button("📄 Generate PDF", key=f"ipdf_{inv['id']}"):
                    try:
                        result = api.generate_invoice_pdf(inv["id"])
                        url = result.get("download_url", "")
                        if url:
                            st.markdown(f"[⬇️ Download Invoice PDF]({url})")
                        st.success("PDF generated!")
                    except Exception as e:
                        st.error(f"Error: {e}")
            with b3:
                if st.button("🗑️ Delete", key=f"dinv_{inv['id']}"):
                    try:
                        api.delete_invoice(inv["id"])
                        st.success("Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    if quarters:
        st.markdown("---")
        st.markdown("#### 📋 Quarterly GST Summary (for Filing)")
        rows = []
        for q in quarters:
            qi = [i for i in invoices if i.get("quarter") == q]
            rows.append({
                "Quarter": q,
                "FY": qi[0].get("fy", "") if qi else "",
                "Invoices": len(qi),
                "Taxable (₹)": sum(float(i.get("basic_amount", 0))
                                   for i in qi),
                "GST (₹)": sum(float(i.get("gst", 0)) for i in qi),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True,
                     hide_index=True)


# ═══ QUOTATIONS ═══
def pg_quotations():
    st.markdown("### 📝 Quotations")
    try:
        quotations = api.list_quotations()
        bank = api.get_bank_details()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    dl = ("1. All designs remain IP of the Studio until full payment.\n"
          "2. Scope changes after approval billed separately.\n"
          "3. Client feedback within 5 business days.\n"
          "4. Cancellation incurs charges for completed work.\n"
          "5. Valid for 30 days.")
    dp = ("• 30% advance on confirmation\n"
          "• 30% on design development approval\n"
          "• 30% on final submission\n"
          "• 10% on completion & handover")

    with st.expander("➕ Create New Quotation"):
        with st.form("new_qtn"):
            a, b = st.columns(2)
            with a:
                qc = st.text_input("Client *")
                qp = st.text_input("Project *")
            with b:
                qa = st.number_input("Amount (₹)", min_value=0.0,
                                     step=10000.0, format="%.2f")
                qd = st.date_input("Date", value=date.today())
            qs = st.text_area("Scope of Work", height=120)
            qt = st.text_area("Timelines", height=80)
            qv = st.text_area("Deliverables", height=80)
            ql = st.text_area("Legal Clauses", value=dl, height=140)
            qpm = st.text_area("Payment Structure", value=dp, height=100)
            if st.form_submit_button("Create Quotation", type="primary",
                                     use_container_width=True):
                if qc and qp:
                    try:
                        api.create_quotation({
                            "client_name": qc, "project_name": qp,
                            "date": qd.isoformat(), "total_amount": qa,
                            "scope": qs, "timelines": qt,
                            "deliverables": qv, "legal_clauses": ql,
                            "payment_structure": qpm,
                        })
                        st.success("Created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    icons = {"draft": "🔘", "sent": "📤", "accepted": "✅", "rejected": "❌"}
    for q in quotations:
        with st.expander(
            f"{icons.get(q.get('status', 'draft'), '🔘')} "
            f"**{q.get('quotation_number', '')}** — "
            f"{q.get('client_name', '')} | {q.get('project_name', '')} | "
            f"{inr(q.get('total_amount', 0))}"
        ):
            # ── Edit all fields ──
            with st.form(f"edit_qtn_{q['id']}"):
                eq1, eq2 = st.columns(2)
                with eq1:
                    e_client = st.text_input("Client", value=q.get("client_name", ""), key=f"eqc_{q['id']}")
                    e_project = st.text_input("Project", value=q.get("project_name", ""), key=f"eqp_{q['id']}")
                    e_status = st.selectbox("Status", ["draft", "sent", "accepted", "rejected"],
                        index=["draft", "sent", "accepted", "rejected"].index(q.get("status", "draft")),
                        key=f"eqs_{q['id']}")
                with eq2:
                    e_amount = st.number_input("Amount (₹)", value=float(q.get("total_amount", 0)),
                        min_value=0.0, step=10000.0, format="%.2f", key=f"eqa_{q['id']}")
                e_scope = st.text_area("Scope of Work", value=q.get("scope", ""), height=100, key=f"eqsc_{q['id']}")
                e_timelines = st.text_area("Timelines", value=q.get("timelines", ""), height=60, key=f"eqt_{q['id']}")
                e_deliverables = st.text_area("Deliverables", value=q.get("deliverables", ""), height=60, key=f"eqd_{q['id']}")
                e_legal = st.text_area("Legal Clauses", value=q.get("legal_clauses", ""), height=100, key=f"eql_{q['id']}")
                e_payment = st.text_area("Payment Structure", value=q.get("payment_structure", ""), height=80, key=f"eqpm_{q['id']}")

                if st.form_submit_button("💾 Save All Changes", type="primary", use_container_width=True):
                    try:
                        api.update_quotation(q["id"], {
                            "client_name": e_client, "project_name": e_project,
                            "status": e_status, "total_amount": e_amount,
                            "scope": e_scope, "timelines": e_timelines,
                            "deliverables": e_deliverables, "legal_clauses": e_legal,
                            "payment_structure": e_payment,
                        })
                        st.success("Quotation updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            # ── PDF & Delete buttons ──
            b1, b2 = st.columns(2)
            with b1:
                if st.button("📄 Generate PDF", key=f"qpdf_{q['id']}"):
                    try:
                        result = api.generate_quotation_pdf(q["id"])
                        url = result.get("download_url", "")
                        if url:
                            st.markdown(f"[⬇️ Download Quotation PDF]({url})")
                        st.success("PDF generated!")
                    except Exception as e:
                        st.error(f"Error: {e}")
            with b2:
                if st.button("🗑️ Delete Quotation", key=f"dqtn_{q['id']}"):
                    try:
                        api.delete_quotation(q["id"])
                        st.success("Deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


# ═══ PROJECTS ═══
def pg_projects():
    st.markdown("### 📁 Projects & Stages")
    try:
        projects = api.list_projects()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    with st.expander("➕ Create New Project"):
        with st.form("new_proj"):
            a, b = st.columns(2)
            with a:
                pn = st.text_input("Name *")
                pc = st.text_input("Client")
            with b:
                pt = st.number_input("Receivable (₹)", min_value=0.0,
                                     step=10000.0, format="%.2f")
                pd_ = st.date_input("Start", value=date.today())
            pdesc = st.text_area("Description", height=80)
            if st.form_submit_button("Create", type="primary",
                                     use_container_width=True):
                if pn:
                    try:
                        api.create_project(pn, pc, pt, pd_.isoformat(),
                                           pdesc)
                        st.success(f"'{pn}' created!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    for proj in projects:
        stages = proj.get("stages", {})
        done = sum(1 for s in stages.values() if s == "Completed")
        pct = int(done / len(STAGES) * 100)
        with st.expander(
            f"**{proj['name']}** — {proj.get('client_name', '')} | "
            f"{pct}% | {inr(proj.get('total_cost', 0))}"
        ):
            st.progress(pct / 100)
            new_stages = {}
            cols = st.columns(4)
            for idx, sn in enumerate(STAGES):
                with cols[idx % 4]:
                    cur = stages.get(sn, "Not Started")
                    new_stages[sn] = st.selectbox(
                        sn, STATUSES,
                        index=(STATUSES.index(cur)
                               if cur in STATUSES else 0),
                        key=f"ms_{proj['id']}_{sn}",
                    )
            a, b = st.columns([3, 1])
            with a:
                if st.button("💾 Save", key=f"sv_{proj['id']}"):
                    api.update_project(proj["id"], {"stages": new_stages})
                    st.success("Updated!")
                    st.rerun()
            with b:
                if st.button("🗑️ Delete", key=f"dl_{proj['id']}"):
                    api.delete_project(proj["id"])
                    st.rerun()


# ═══ TIME TRACKING ═══
def pg_time():
    st.markdown("### ⏱ Time Tracking (All Employees)")
    try:
        logs = api.list_time_logs()
        employees = api.list_employees()
        projects = api.list_projects()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    em = {e["id"]: e["name"] for e in employees}
    pm = {p["id"]: p["name"] for p in projects}

    f1, f2 = st.columns(2)
    with f1:
        se = st.selectbox("Employee",
                          ["All"] + [e["name"] for e in employees])
    with f2:
        sp = st.selectbox("Project",
                          ["All"] + [p["name"] for p in projects])

    fl = logs
    if se != "All":
        eid = next((e["id"] for e in employees if e["name"] == se), None)
        if eid:
            fl = [l for l in fl
                  if str(l.get("employee_id")) == str(eid)]
    if sp != "All":
        pid = next((p["id"] for p in projects if p["name"] == sp), None)
        if pid:
            fl = [l for l in fl
                  if str(l.get("project_id")) == str(pid)]

    st.metric("Total Hours",
              f"{sum(float(l.get('hours', 0)) for l in fl):.1f}h")
    if fl:
        df = pd.DataFrame([{
            "Date": l.get("date", ""),
            "Employee": em.get(l.get("employee_id"), "?"),
            "Project": pm.get(l.get("project_id"), "?"),
            "Hours": float(l.get("hours", 0)),
            "Comments": l.get("comments", ""),
        } for l in fl]).sort_values(
            "Date", ascending=False
        ).reset_index(drop=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Charts ──
        st.markdown("---")
        st.markdown("#### 📊 Time Distribution Charts")

        # Chart 1: Hours per project (bar chart)
        proj_hours = df.groupby("Project")["Hours"].sum().sort_values(ascending=True)
        st.markdown("**Hours by Project**")
        st.bar_chart(proj_hours)

        # Chart 2: Hours per employee (bar chart)
        emp_hours = df.groupby("Employee")["Hours"].sum().sort_values(ascending=True)
        st.markdown("**Hours by Employee**")
        st.bar_chart(emp_hours)

        # Chart 3: Daily hours timeline (line chart)
        daily = df.groupby("Date")["Hours"].sum().sort_index()
        if len(daily) > 1:
            st.markdown("**Daily Hours Trend**")
            st.line_chart(daily)

        # Chart 4: Employee × Project heatmap-style breakdown
        pivot = df.pivot_table(values="Hours", index="Employee",
                               columns="Project", aggfunc="sum",
                               fill_value=0)
        if len(pivot) > 0 and len(pivot.columns) > 0:
            st.markdown("**Employee × Project Breakdown**")
            st.dataframe(pivot.style.background_gradient(cmap="Blues",
                         axis=None).format("{:.1f}"),
                         use_container_width=True)

        # Delete individual logs
        with st.expander("🗑️ Manage Individual Logs"):
            for l in fl[:50]:
                log_label = (f"{l.get('date', '')} · {em.get(l.get('employee_id'), '?')} · "
                             f"{pm.get(l.get('project_id'), '?')} · {float(l.get('hours', 0)):.1f}h")
                col_t, col_d = st.columns([6, 1])
                with col_t:
                    st.markdown(f"**{log_label}** — _{l.get('comments', '')}_")
                with col_d:
                    if st.button("🗑️", key=f"dtl_{l.get('id', '')}"):
                        try:
                            api.delete_time_log(l["id"])
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    with st.expander("➕ Log Time (Admin)"):
        with st.form("alog"):
            a, b = st.columns(2)
            with a:
                ae = (st.selectbox("Employee",
                                   [e["name"] for e in employees],
                                   key="ae")
                      if employees else None)
            with b:
                ap = (st.selectbox("Project",
                                   [p["name"] for p in projects],
                                   key="ap")
                      if projects else None)
            c, d = st.columns(2)
            with c:
                ah = st.number_input("Hours", min_value=0.5,
                                     max_value=16.0, step=0.5, value=1.0)
            with d:
                ad = st.date_input("Date", value=date.today(), key="adl")
            ac = st.text_area("Comments", key="acl")
            if st.form_submit_button("Log", type="primary",
                                     use_container_width=True):
                if ae and ap:
                    eid = next((e["id"] for e in employees
                                if e["name"] == ae), None)
                    pid = next((p["id"] for p in projects
                                if p["name"] == ap), None)
                    if eid and pid:
                        api.create_time_log(eid, pid, ah,
                                            ad.isoformat(), ac)
                        st.success("Logged!")
                        st.rerun()


# ═══ COST OF LABOUR ═══
def pg_labour():
    st.markdown("### 📈 Cost of Labour Analysis")
    try:
        projects = api.list_projects()
        employees = api.list_employees()
        logs = api.list_time_logs()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    em = {e["id"]: e for e in employees}

    st.markdown("#### Employee Cost Structure")
    if employees:
        st.dataframe(pd.DataFrame([{
            "Name": e["name"], "Role": e.get("role", ""),
            "Monthly (₹)": float(e.get("salary", 0)),
            "Daily (₹)": float(e.get("daily_cost", 0)),
            "Hourly (₹)": float(e.get("hourly_cost", 0)),
        } for e in employees]), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### Project Cost Breakdown")
    for proj in projects:
        pl = [l for l in logs
              if str(l.get("project_id")) == str(proj["id"])]
        eh = {}
        for l in pl:
            eid = l.get("employee_id", "")
            eh[eid] = eh.get(eid, 0) + float(l.get("hours", 0))

        costs = []
        tl = 0
        for eid, hrs in eh.items():
            e = em.get(eid)
            if e:
                c = round(hrs * float(e.get("hourly_cost", 0)), 2)
                costs.append({
                    "Name": e["name"], "Hours": hrs,
                    "Rate (₹)": float(e.get("hourly_cost", 0)),
                    "Cost (₹)": c,
                })
                tl += c

        recv = float(proj.get("total_cost", 0))
        profit = recv - tl
        util = (tl / recv * 100) if recv > 0 else 0

        with st.expander(
            f"**{proj['name']}** — Recv: {inr(recv)} | "
            f"Labour: {inr(tl)} | Profit: {inr(profit)}"
        ):
            a, b, c, d = st.columns(4)
            with a: st.metric("Receivable", inr(recv))
            with b: st.metric("Labour Cost", inr(tl))
            with c: st.metric("Profit", inr(profit))
            with d: st.metric("Utilization", f"{util:.1f}%")
            if util > 0:
                st.progress(min(util / 100, 1.0))
                clr = ("🟢" if util < 50
                        else "🟡" if util < 80
                        else "🔴")
                st.caption(f"{clr} {util:.1f}% of receivable consumed")
            if costs:
                st.dataframe(pd.DataFrame(costs),
                             use_container_width=True, hide_index=True)
            else:
                st.info("No time logged yet.")


# ═══ EMPLOYEES & USERS ═══
def pg_employees():
    st.markdown("### 👥 Employees & Users")
    try:
        employees = api.list_employees()
        users = api.list_users()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    t1, t2 = st.tabs(["👷 Employees", "🔐 User Accounts"])

    with t1:
        with st.expander("➕ Add Employee"):
            with st.form("add_e"):
                a, b = st.columns(2)
                with a:
                    en = st.text_input("Name *")
                    er = st.text_input("Role",
                                       placeholder="Architect, Draftsman")
                with b:
                    es = st.number_input("Monthly Salary (₹) *",
                                         min_value=0.0, step=1000.0,
                                         format="%.2f")
                    if es > 0:
                        st.info(f"Daily: ₹{es/30:,.2f} · "
                                f"Hourly: ₹{es/30/8:,.2f}")
                if st.form_submit_button("Add Employee", type="primary",
                                         use_container_width=True):
                    if en and es > 0:
                        try:
                            api.create_employee(en, er, es)
                            st.success(f"'{en}' added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        if employees:
            st.dataframe(pd.DataFrame([{
                "ID": e["id"], "Name": e["name"],
                "Role": e.get("role", ""),
                "Salary (₹)": float(e.get("salary", 0)),
                "Daily (₹)": float(e.get("daily_cost", 0)),
                "Hourly (₹)": float(e.get("hourly_cost", 0)),
            } for e in employees]),
                use_container_width=True, hide_index=True)

            # Edit employee
            with st.expander("✏️ Edit Employee"):
                edit_emp = st.selectbox("Select Employee to Edit",
                    [f"{e['name']} (ID:{e['id']})" for e in employees],
                    key="edit_emp_sel")
                edit_id = edit_emp.split("ID:")[1].rstrip(")")
                edit_obj = next((e for e in employees if str(e["id"]) == edit_id), None)
                if edit_obj:
                    with st.form("edit_emp_form"):
                        ea, eb = st.columns(2)
                        with ea:
                            new_name = st.text_input("Name", value=edit_obj.get("name", ""))
                            new_role = st.text_input("Role", value=edit_obj.get("role", ""))
                        with eb:
                            new_salary = st.number_input("Monthly Salary (₹)",
                                min_value=0.0, step=1000.0, format="%.2f",
                                value=float(edit_obj.get("salary", 0)))
                            if new_salary > 0:
                                st.info(f"Daily: ₹{new_salary/30:,.2f} · Hourly: ₹{new_salary/30/8:,.2f}")
                        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                            try:
                                api.update_employee(edit_id, {
                                    "name": new_name, "role": new_role, "salary": new_salary
                                })
                                st.success(f"'{new_name}' updated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

            de = st.selectbox(
                "Remove employee",
                ["—"] + [f"{e['name']} (ID:{e['id']})"
                         for e in employees])
            if de != "—" and st.button("🗑️ Remove"):
                eid = de.split("ID:")[1].rstrip(")")
                api.delete_employee(eid)
                st.rerun()

    with t2:
        st.markdown("Create login accounts for the Employee Portal.")
        with st.expander("➕ Create User Account"):
            with st.form("add_u"):
                a, b = st.columns(2)
                with a:
                    un = st.text_input("Username *")
                    up = st.text_input("Password *", type="password")
                with b:
                    ud = st.text_input("Display Name")
                    ur = st.selectbox("Role", ["employee", "admin"])
                    ue = st.selectbox(
                        "Link Employee",
                        ["None"] + [f"{e['name']} (ID:{e['id']})"
                                    for e in employees])
                if st.form_submit_button("Create Account", type="primary",
                                         use_container_width=True):
                    if un and up:
                        eid = ("" if ue == "None"
                               else ue.split("ID:")[1].rstrip(")"))
                        try:
                            api.register_user(un, up, ur, ud or un, eid)
                            st.success(f"User '{un}' created!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        if users:
            st.dataframe(pd.DataFrame([{
                "Username": u["username"], "Role": u["role"],
                "Display": u.get("display_name", ""),
                "Employee ID": u.get("employee_id", "—"),
            } for u in users]),
                use_container_width=True, hide_index=True)


# ═══ LEAVES & EXPENSES (Management view) ═══
def pg_leaves_expenses():
    st.markdown("### 🏖️ Leaves & Expenses Management")
    try:
        leaves = api.list_leaves()
        expenses = api.list_expenses()
        employees = api.list_employees()
        projects = api.list_projects()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    em = {e["id"]: e["name"] for e in employees}
    pm = {p["id"]: p["name"] for p in projects}

    tab_l, tab_e = st.tabs(["🏖️ Leave Requests", "💳 Expenses"])

    with tab_l:
        total_leaves = len(leaves)
        pending_l = len([l for l in leaves if l.get("status") == "pending"])
        st.markdown(f"**{total_leaves} total requests** · **{pending_l} pending approval**")

        for lv in leaves:
            status_icon = {"pending": "🟡", "approved": "✅", "rejected": "❌"}.get(lv.get("status", ""), "🔘")
            emp_name = em.get(lv.get("employee_id"), "?")
            with st.expander(f"{status_icon} {emp_name} — {lv.get('leave_type', '')} | {lv.get('start_date', '')} to {lv.get('end_date', '')} ({float(lv.get('days', 0)):.0f}d)"):
                st.markdown(f"**Reason:** {lv.get('reason', 'N/A')}")
                new_status = st.selectbox("Status",
                    ["pending", "approved", "rejected"],
                    index=["pending", "approved", "rejected"].index(lv.get("status", "pending")),
                    key=f"ls_{lv['id']}")
                col_u, col_d = st.columns([1, 1])
                with col_u:
                    if new_status != lv.get("status"):
                        if st.button("Update Status", key=f"lu_{lv['id']}"):
                            api.update_leave(lv["id"], {"status": new_status})
                            st.rerun()
                with col_d:
                    if st.button("🗑️ Delete", key=f"dlv_{lv['id']}"):
                        api.delete_leave(lv["id"])
                        st.rerun()

    with tab_e:
        total_exp = sum(float(x.get("amount", 0)) for x in expenses)
        pending_e = sum(float(x.get("amount", 0)) for x in expenses if x.get("status") == "pending")
        st.markdown(f"**Total: ₹{total_exp:,.2f}** · **Pending: ₹{pending_e:,.2f}**")

        if expenses:
            for exp in expenses:
                status_icon = {"pending": "🟡", "approved": "✅", "rejected": "❌"}.get(exp.get("status", ""), "🔘")
                emp_name = em.get(exp.get("employee_id"), "?")
                proj_name = pm.get(exp.get("project_id"), "—")
                with st.expander(f"{status_icon} {emp_name} — {exp.get('category', '')} | ₹{float(exp.get('amount', 0)):,.2f} | {exp.get('date', '')}"):
                    st.markdown(f"**Description:** {exp.get('description', 'N/A')}")
                    st.markdown(f"**Project:** {proj_name}")
                    new_status = st.selectbox("Status",
                        ["pending", "approved", "rejected"],
                        index=["pending", "approved", "rejected"].index(exp.get("status", "pending")),
                        key=f"es_{exp['id']}")
                    col_u, col_d = st.columns([1, 1])
                    with col_u:
                        if new_status != exp.get("status"):
                            if st.button("Update Status", key=f"eu_{exp['id']}"):
                                api.update_expense(exp["id"], {"status": new_status})
                                st.rerun()
                    with col_d:
                        if st.button("🗑️ Delete", key=f"dex_{exp['id']}"):
                            api.delete_expense(exp["id"])
                            st.rerun()

        # Expense summary by category
        if expenses:
            st.markdown("---")
            st.markdown("#### Expense Summary by Category")
            cat_totals = {}
            for exp in expenses:
                cat = exp.get("category", "Other")
                cat_totals[cat] = cat_totals.get(cat, 0) + float(exp.get("amount", 0))
            cat_df = pd.DataFrame([{"Category": k, "Total (₹)": v} for k, v in sorted(cat_totals.items(), key=lambda x: -x[1])])
            st.dataframe(cat_df, use_container_width=True, hide_index=True)
            st.bar_chart(pd.Series(cat_totals, name="Amount (₹)"))


# ═══ HOLIDAY LIST ═══
def pg_holidays():
    st.markdown("### 📅 Holiday List (Editable)")

    current_year = str(datetime.now().year)
    year_sel = st.selectbox("Year", [str(y) for y in range(2024, 2031)],
                            index=[str(y) for y in range(2024, 2031)].index(current_year)
                            if current_year in [str(y) for y in range(2024, 2031)] else 0)

    try:
        holidays = api.list_holidays(year=year_sel)
    except Exception as e:
        st.error(f"Error: {e}")
        return

    with st.expander("➕ Add Holiday"):
        with st.form("add_holiday"):
            a, b = st.columns(2)
            with a:
                h_name = st.text_input("Holiday Name *", placeholder="e.g. Republic Day")
                h_date = st.date_input("Date", value=date.today())
            with b:
                h_optional = st.checkbox("Optional / Restricted Holiday")
            if st.form_submit_button("Add Holiday", type="primary", use_container_width=True):
                if h_name:
                    try:
                        api.create_holiday(h_date.isoformat(), h_name, year_sel, h_optional)
                        st.success(f"'{h_name}' added!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    if holidays:
        st.caption(f"{len(holidays)} holidays in {year_sel}")
        for h in holidays:
            htype = "Optional" if h.get("optional") else "Gazetted"
            col_h, col_d = st.columns([6, 1])
            with col_h:
                st.markdown(f"**{h.get('date', '')}** — {h.get('name', '')} ({htype})")
            with col_d:
                if st.button("🗑️", key=f"hd_{h['id']}"):
                    api.delete_holiday(h["id"])
                    st.rerun()
    else:
        st.info(f"No holidays for {year_sel}. Add them above.")


# ═══ SETTINGS ═══
def pg_settings():
    st.markdown("### ⚙️ Settings")
    try:
        bank = api.get_bank_details()
    except Exception:
        bank = {}

    # ── Logo Upload ──
    st.markdown("#### 🖼️ Company Logo")
    st.caption("This logo appears at the top of generated Invoice and Quotation PDFs.")
    try:
        logo_info = api.get_logo_url()
        if logo_info.get("exists"):
            st.image(logo_info["url"], width=200)
            st.caption("Current logo uploaded.")
    except Exception:
        pass

    logo_file = st.file_uploader("Upload Logo (PNG or JPG)", type=["png", "jpg", "jpeg"])
    if logo_file:
        if st.button("Upload Logo", type="primary"):
            import base64
            b64 = base64.b64encode(logo_file.read()).decode()
            ct = "image/png" if logo_file.name.endswith(".png") else "image/jpeg"
            try:
                api.upload_logo(b64, ct)
                st.success("Logo uploaded!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")

    # ── Company & Signatory Details ──
    st.markdown("#### 🏢 Company & Signatory (for PDFs)")
    with st.form("company_details"):
        a, b = st.columns(2)
        with a:
            c_tagline = st.text_input("Company Tagline",
                value=bank.get("company_tagline", "Architecture | Design"))
            c_email = st.text_input("Email", value=bank.get("email", ""))
            c_phone = st.text_input("Phone", value=bank.get("phone", ""))
        with b:
            c_address = st.text_input("Address", value=bank.get("address", ""))
            c_signatory = st.text_input("Signatory Name", value=bank.get("signatory_name", ""))
            c_title = st.text_input("Signatory Title", value=bank.get("signatory_title", "Principal Architect"))
        if st.form_submit_button("Save Company Details", type="primary", use_container_width=True):
            try:
                updated = {**bank, "company_tagline": c_tagline, "email": c_email,
                    "phone": c_phone, "address": c_address,
                    "signatory_name": c_signatory, "signatory_title": c_title}
                api.update_bank_details(updated)
                st.success("Saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")

    # ── Bank Details ──
    st.markdown("#### 🏦 Bank Details (appears on Quotations & Invoices)")
    with st.form("bank"):
        a, b = st.columns(2)
        with a:
            bn = st.text_input("Bank Name",
                               value=bank.get("bank_name", ""))
            bb = st.text_input("Branch",
                               value=bank.get("branch", ""))
            ba = st.text_input("Account Name",
                               value=bank.get("account_name", ""))
            bnum = st.text_input("Account Number",
                                 value=bank.get("account_number", ""))
        with b:
            bi = st.text_input("IFSC Code",
                               value=bank.get("ifsc", ""))
            bp = st.text_input("PAN", value=bank.get("pan", ""))
            bg = st.text_input("GSTIN", value=bank.get("gstin", ""))
        if st.form_submit_button("Save Bank Details", type="primary",
                                 use_container_width=True):
            try:
                updated = {**bank, "bank_name": bn, "branch": bb,
                    "account_name": ba, "account_number": bnum,
                    "ifsc": bi, "pan": bp, "gstin": bg}
                api.update_bank_details(updated)
                st.success("Saved!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("#### ℹ️ System Info")
    st.markdown(
        "- **Backend:** AWS Lambda + DynamoDB + API Gateway\n"
        "- **Default Admin:** `admin` / `admin123`\n"
        "- **GST:** 18% auto-applied to all invoices\n"
        "- **TDS:** 10% auto-deducted from receivables\n"
        "- **Cost calc:** Salary ÷ 30 days ÷ 8 hours = hourly rate"
    )


# ── Entry ──
if not st.session_state.logged_in:
    show_login()
else:
    show_app()
