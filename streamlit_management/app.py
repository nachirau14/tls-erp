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

st.set_page_config(page_title="Studio ERP – Management", page_icon="🏛", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
.stApp { font-family: 'DM Sans', sans-serif; }
.mgmt-header { background: linear-gradient(135deg, #0f0a2e 0%, #1e1b4b 50%, #312e81 100%);
    color: white; padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem; }
.mgmt-header h1 { margin: 0; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px; }
.mgmt-header p { margin: 0.3rem 0 0; opacity: 0.7; font-size: 0.85rem; }
.stat-card { background: white; border: 1px solid #e8e6f0; border-radius: 14px;
    padding: 1.2rem 1.5rem; text-align: center; }
.stat-card .label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;
    letter-spacing: 1px; font-weight: 600; }
.stat-card .value { font-size: 1.7rem; font-weight: 700; color: #1e1b4b; margin-top: 0.2rem; }
div[data-testid="stSidebar"] { background: #0f0a2e; }
div[data-testid="stSidebar"] * { color: #c7d2fe !important; }
.block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

STAGES = ["2D Plans","End Views","Elevations","3D Modeling","Rendering","Presentation","Site","Checking"]
STATUSES = ["Not Started","In Progress","Review","Completed"]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

def fmt(n):
    try: return f"{n:,.2f}"
    except: return str(n)
def inr(n): return f"₹{fmt(n)}"

# ── LOGIN ──
def show_login():
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("""<div style="text-align:center; margin-top:3rem;">
            <h1 style="font-size:2.2rem; color:#1e1b4b;">🏛 Management Portal</h1>
            <p style="color:#64748b; margin-bottom:2rem;">Architectural Studio ERP – Admin Access</p>
        </div>""", unsafe_allow_html=True)
        with st.form("login"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                if not username or not password: st.error("Fill in both fields.")
                else:
                    try:
                        result = api.login(username, password)
                        if result["user"]["role"] != "admin": st.error("Admin credentials required.")
                        else:
                            st.session_state.logged_in = True; st.session_state.user = result["user"]; st.rerun()
                    except: st.error("Invalid credentials.")

# ── APP ──
def show_app():
    user = st.session_state.user
    with st.sidebar:
        st.markdown("### 🏛 Studio ERP")
        st.caption(f"**{user['display_name']}** (admin)")
        st.divider()
        page = st.radio("Nav", [
            "📊 Dashboard", "💰 Invoicing & GST", "📝 Quotations",
            "📁 Projects & Stages", "⏱ Time Tracking", "📈 Cost of Labour",
            "👥 Employees & Users", "⚙️ Settings",
        ], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False; st.session_state.user = None; st.rerun()

    st.markdown(f"""<div class="mgmt-header"><h1>Studio ERP – Management</h1>
        <p>{datetime.now().strftime('%A, %d %B %Y')}</p></div>""", unsafe_allow_html=True)

    pages = {"Dashboard": pg_dashboard, "Invoicing": pg_invoicing, "Quotation": pg_quotations,
        "Projects": pg_projects, "Time": pg_time, "Cost": pg_labour,
        "Employees": pg_employees, "Settings": pg_settings}
    for k, fn in pages.items():
        if k in page: fn(); break


# ═══ DASHBOARD ═══
def pg_dashboard():
    st.markdown("### 📊 Dashboard")
    try:
        inv = api.list_invoices(); proj = api.list_projects()
        emp = api.list_employees(); logs = api.list_time_logs()
    except Exception as e: st.error(f"Error: {e}"); return

    ti = sum(i.get("total",0) for i in inv)
    rc = sum(i.get("receivable",0) for i in inv if i.get("received"))
    pn = sum(i.get("receivable",0) for i in inv if not i.get("received"))
    gs = sum(i.get("gst",0) for i in inv)
    ac = len([p for p in proj if p.get("status")=="active"])
    hr = sum(l.get("hours",0) for l in logs)

    r1 = st.columns(3)
    for c,l,v in zip(r1,["Total Invoiced","Received","Pending"],[inr(ti),inr(rc),inr(pn)]):
        with c: st.markdown(f'<div class="stat-card"><div class="label">{l}</div><div class="value">{v}</div></div>', unsafe_allow_html=True)
    r2 = st.columns(3)
    for c,l,v in zip(r2,["GST Collected","Active Projects","Hours Logged"],[inr(gs),str(ac),f"{hr:.0f}h"]):
        with c: st.markdown(f'<div class="stat-card"><div class="label">{l}</div><div class="value">{v}</div></div>', unsafe_allow_html=True)

    if proj:
        st.markdown("---"); st.markdown("#### Project Progress")
        for p in proj:
            stg = p.get("stages",{})
            d = sum(1 for s in stg.values() if s=="Completed")
            pct = int(d/len(STAGES)*100)
            a,b = st.columns([1,3])
            with a: st.markdown(f"**{p['name']}** ({pct}%)")
            with b: st.progress(pct/100)


# ═══ INVOICING & GST ═══
def pg_invoicing():
    st.markdown("### 💰 Invoicing & GST")
    try: invoices = api.list_invoices()
    except Exception as e: st.error(f"Error: {e}"); invoices = []

    quarters = sorted(set(i.get("quarter","") for i in invoices if i.get("quarter")))
    fys = sorted(set(i.get("fy","") for i in invoices if i.get("fy")))
    f1,f2,_ = st.columns([1,1,2])
    with f1: sq = st.selectbox("Quarter", ["All"]+quarters)
    with f2: sf = st.selectbox("FY", ["All"]+fys)

    fl = invoices
    if sq != "All": fl = [i for i in fl if i.get("quarter")==sq]
    if sf != "All": fl = [i for i in fl if i.get("fy")==sf]

    tg = sum(i.get("gst",0) for i in fl)
    tr = sum(i.get("receivable",0) for i in fl)
    tp = sum(i.get("receivable",0) for i in fl if i.get("received"))
    tt = sum(i.get("tds",0) for i in fl)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("GST Collected", inr(tg))
    with c2: st.metric("Total Receivable", inr(tr))
    with c3: st.metric("Received", inr(tp))
    with c4: st.metric("TDS Deducted", inr(tt))

    # Create invoice
    with st.expander("➕ Create New Invoice"):
        with st.form("new_inv"):
            a,b = st.columns(2)
            with a:
                cn = st.text_input("Client Name *"); desc = st.text_input("Description")
                it = st.selectbox("Type", ["tax","proforma"])
            with b:
                amt = st.number_input("Basic Amount (₹) *", min_value=0.0, step=1000.0, format="%.2f")
                dt = st.date_input("Date", value=date.today())
            if amt > 0:
                g = round(amt*0.18,2); t = round(amt*0.10,2); tot = round(amt+g,2); r = round((amt-t)+g,2)
                st.info(f"Basic: {inr(amt)} + GST: {inr(g)} = Total: {inr(tot)} | TDS: {inr(t)} | Client pays: {inr(r)}")
            if st.form_submit_button("Create Invoice", type="primary", use_container_width=True):
                if cn and amt > 0:
                    try:
                        res = api.create_invoice(cn, amt, dt.isoformat(), desc, it)
                        st.success(f"Invoice {res.get('invoice_number','')} created!"); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

    # Invoice list with paid/unpaid toggle
    for inv in fl:
        paid = "✅" if inv.get("received") else "⏳"
        ci, cb = st.columns([8,1])
        with ci:
            st.markdown(
                f"**{inv.get('invoice_number','')}** | {inv.get('date','')} | {inv.get('client_name','')} | "
                f"{'Tax' if inv.get('invoice_type')=='tax' else 'Proforma'} | "
                f"Basic: {inr(inv.get('basic_amount',0))} | Total: {inr(inv.get('total',0))} | "
                f"Receivable: {inr(inv.get('receivable',0))} | {paid}")
        with cb:
            if inv.get("received"):
                if st.button("Unpaid", key=f"up_{inv['id']}"):
                    api.update_invoice(inv["id"], {"received": False}); st.rerun()
            else:
                if st.button("Paid ✓", key=f"pd_{inv['id']}"):
                    api.update_invoice(inv["id"], {"received": True}); st.rerun()

    # GST quarterly summary
    if quarters:
        st.markdown("---"); st.markdown("#### 📋 Quarterly GST Summary (for Filing)")
        rows = []
        for q in quarters:
            qi = [i for i in invoices if i.get("quarter")==q]
            rows.append({"Quarter": q, "FY": qi[0].get("fy","") if qi else "",
                "Invoices": len(qi), "Taxable (₹)": sum(i.get("basic_amount",0) for i in qi),
                "GST (₹)": sum(i.get("gst",0) for i in qi)})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ═══ QUOTATIONS ═══
def pg_quotations():
    st.markdown("### 📝 Quotations")
    try: quotations = api.list_quotations(); bank = api.get_bank_details()
    except Exception as e: st.error(f"Error: {e}"); return

    dl = "1. All designs remain IP of the Studio until full payment.\n2. Scope changes after approval billed separately.\n3. Client feedback within 5 business days.\n4. Cancellation incurs charges for completed work.\n5. Valid for 30 days."
    dp = "• 30% advance on confirmation\n• 30% on design development approval\n• 30% on final submission\n• 10% on completion & handover"

    with st.expander("➕ Create New Quotation"):
        with st.form("new_qtn"):
            a,b = st.columns(2)
            with a: qc = st.text_input("Client *"); qp = st.text_input("Project *")
            with b: qa = st.number_input("Amount (₹)", min_value=0.0, step=10000.0, format="%.2f"); qd = st.date_input("Date", value=date.today())
            qs = st.text_area("Scope of Work", height=120)
            qt = st.text_area("Timelines", height=80)
            qv = st.text_area("Deliverables", height=80)
            ql = st.text_area("Legal Clauses", value=dl, height=140)
            qpm = st.text_area("Payment Structure", value=dp, height=100)
            if st.form_submit_button("Create Quotation", type="primary", use_container_width=True):
                if qc and qp:
                    try:
                        api.create_quotation({"client_name":qc,"project_name":qp,"date":qd.isoformat(),
                            "total_amount":qa,"scope":qs,"timelines":qt,"deliverables":qv,
                            "legal_clauses":ql,"payment_structure":qpm})
                        st.success("Created!"); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

    icons = {"draft":"🔘","sent":"📤","accepted":"✅","rejected":"❌"}
    for q in quotations:
        with st.expander(f"{icons.get(q.get('status','draft'),'🔘')} **{q.get('quotation_number','')}** — {q.get('client_name','')} | {q.get('project_name','')} | {inr(q.get('total_amount',0))}"):
            ns = st.selectbox("Status", ["draft","sent","accepted","rejected"],
                index=["draft","sent","accepted","rejected"].index(q.get("status","draft")), key=f"qs_{q['id']}")
            if ns != q.get("status"):
                if st.button("Update Status", key=f"qu_{q['id']}"):
                    api.update_quotation(q["id"], {"status": ns}); st.rerun()
            st.markdown("---")
            for sec, lbl in [("scope","Scope of Work"),("timelines","Timelines"),("deliverables","Deliverables"),
                             ("legal_clauses","Legal Clauses"),("payment_structure","Payment Structure")]:
                if q.get(sec): st.markdown(f"**{lbl}:**"); st.text(q[sec])
            if any(bank.get(k) for k in ["bank_name","account_number","ifsc"]):
                st.markdown("---"); st.markdown("**🏦 Bank Details:**")
                st.markdown(f"Bank: {bank.get('bank_name','')} | Branch: {bank.get('branch','')} | A/C: {bank.get('account_name','')} {bank.get('account_number','')} | IFSC: {bank.get('ifsc','')} | PAN: {bank.get('pan','')} | GSTIN: {bank.get('gstin','')}")


# ═══ PROJECTS ═══
def pg_projects():
    st.markdown("### 📁 Projects & Stages")
    try: projects = api.list_projects()
    except Exception as e: st.error(f"Error: {e}"); return

    with st.expander("➕ Create New Project"):
        with st.form("new_proj"):
            a,b = st.columns(2)
            with a: pn = st.text_input("Name *"); pc = st.text_input("Client")
            with b: pt = st.number_input("Receivable (₹)", min_value=0.0, step=10000.0, format="%.2f"); pd_ = st.date_input("Start", value=date.today())
            pdesc = st.text_area("Description", height=80)
            if st.form_submit_button("Create", type="primary", use_container_width=True):
                if pn:
                    try: api.create_project(pn, pc, pt, pd_.isoformat(), pdesc); st.success(f"'{pn}' created!"); st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

    for proj in projects:
        stages = proj.get("stages", {})
        done = sum(1 for s in stages.values() if s == "Completed")
        pct = int(done / len(STAGES) * 100)
        with st.expander(f"**{proj['name']}** — {proj.get('client_name','')} | {pct}% | {inr(proj.get('total_cost',0))}"):
            st.progress(pct / 100)
            new_stages = {}
            cols = st.columns(4)
            for idx, sn in enumerate(STAGES):
                with cols[idx % 4]:
                    cur = stages.get(sn, "Not Started")
                    new_stages[sn] = st.selectbox(sn, STATUSES,
                        index=STATUSES.index(cur) if cur in STATUSES else 0, key=f"ms_{proj['id']}_{sn}")
            a,b = st.columns([3,1])
            with a:
                if st.button("💾 Save", key=f"sv_{proj['id']}"):
                    api.update_project(proj["id"], {"stages": new_stages}); st.success("Updated!"); st.rerun()
            with b:
                if st.button("🗑️ Delete", key=f"dl_{proj['id']}"):
                    api.delete_project(proj["id"]); st.rerun()


# ═══ TIME TRACKING ═══
def pg_time():
    st.markdown("### ⏱ Time Tracking (All Employees)")
    try:
        logs = api.list_time_logs(); employees = api.list_employees(); projects = api.list_projects()
    except Exception as e: st.error(f"Error: {e}"); return

    em = {e["id"]: e["name"] for e in employees}
    pm = {p["id"]: p["name"] for p in projects}

    f1,f2 = st.columns(2)
    with f1: se = st.selectbox("Employee", ["All"]+[e["name"] for e in employees])
    with f2: sp = st.selectbox("Project", ["All"]+[p["name"] for p in projects])

    fl = logs
    if se != "All":
        eid = next((e["id"] for e in employees if e["name"]==se), None)
        if eid: fl = [l for l in fl if str(l.get("employee_id"))==str(eid)]
    if sp != "All":
        pid = next((p["id"] for p in projects if p["name"]==sp), None)
        if pid: fl = [l for l in fl if str(l.get("project_id"))==str(pid)]

    st.metric("Total Hours", f"{sum(l.get('hours',0) for l in fl):.1f}h")
    if fl:
        df = pd.DataFrame([{"Date": l.get("date",""), "Employee": em.get(l.get("employee_id"),"?"),
            "Project": pm.get(l.get("project_id"),"?"), "Hours": l.get("hours",0),
            "Comments": l.get("comments","")} for l in fl]).sort_values("Date", ascending=False).reset_index(drop=True)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("➕ Log Time (Admin)"):
        with st.form("alog"):
            a,b = st.columns(2)
            with a:
                ae = st.selectbox("Employee", [e["name"] for e in employees], key="ae") if employees else None
            with b:
                ap = st.selectbox("Project", [p["name"] for p in projects], key="ap") if projects else None
            c,d = st.columns(2)
            with c: ah = st.number_input("Hours", min_value=0.5, max_value=16.0, step=0.5, value=1.0)
            with d: ad = st.date_input("Date", value=date.today(), key="adl")
            ac = st.text_area("Comments", key="acl")
            if st.form_submit_button("Log", type="primary", use_container_width=True):
                if ae and ap:
                    eid = next((e["id"] for e in employees if e["name"]==ae), None)
                    pid = next((p["id"] for p in projects if p["name"]==ap), None)
                    if eid and pid:
                        api.create_time_log(eid, pid, ah, ad.isoformat(), ac); st.success("Logged!"); st.rerun()


# ═══ COST OF LABOUR ═══
def pg_labour():
    st.markdown("### 📈 Cost of Labour Analysis")
    try:
        projects = api.list_projects(); employees = api.list_employees(); logs = api.list_time_logs()
    except Exception as e: st.error(f"Error: {e}"); return

    em = {e["id"]: e for e in employees}

    st.markdown("#### Employee Cost Structure")
    if employees:
        st.dataframe(pd.DataFrame([{"Name": e["name"], "Role": e.get("role",""),
            "Monthly (₹)": e.get("salary",0), "Daily (₹)": e.get("daily_cost",0),
            "Hourly (₹)": e.get("hourly_cost",0)} for e in employees]),
            use_container_width=True, hide_index=True)

    st.markdown("---"); st.markdown("#### Project Cost Breakdown")
    for proj in projects:
        pl = [l for l in logs if str(l.get("project_id")) == str(proj["id"])]
        eh = {}
        for l in pl:
            eid = l.get("employee_id","")
            eh[eid] = eh.get(eid, 0) + float(l.get("hours", 0))

        costs = []; tl = 0
        for eid, hrs in eh.items():
            e = em.get(eid)
            if e:
                c = round(hrs * float(e.get("hourly_cost", 0)), 2)
                costs.append({"Name": e["name"], "Hours": hrs, "Rate (₹)": float(e.get("hourly_cost",0)), "Cost (₹)": c})
                tl += c

        recv = float(proj.get("total_cost", 0)); profit = recv - tl
        util = (tl / recv * 100) if recv > 0 else 0

        with st.expander(f"**{proj['name']}** — Recv: {inr(recv)} | Labour: {inr(tl)} | Profit: {inr(profit)}"):
            a,b,c,d = st.columns(4)
            with a: st.metric("Receivable", inr(recv))
            with b: st.metric("Labour Cost", inr(tl))
            with c: st.metric("Profit", inr(profit))
            with d: st.metric("Utilization", f"{util:.1f}%")
            if util > 0:
                st.progress(min(util / 100, 1.0))
                clr = "🟢" if util < 50 else "🟡" if util < 80 else "🔴"
                st.caption(f"{clr} {util:.1f}% of receivable consumed")
            if costs:
                st.dataframe(pd.DataFrame(costs), use_container_width=True, hide_index=True)
            else:
                st.info("No time logged yet.")


# ═══ EMPLOYEES & USERS ═══
def pg_employees():
    st.markdown("### 👥 Employees & Users")
    try: employees = api.list_employees(); users = api.list_users()
    except Exception as e: st.error(f"Error: {e}"); return

    t1, t2 = st.tabs(["👷 Employees", "🔐 User Accounts"])

    with t1:
        with st.expander("➕ Add Employee"):
            with st.form("add_e"):
                a,b = st.columns(2)
                with a: en = st.text_input("Name *"); er = st.text_input("Role", placeholder="Architect, Draftsman, Intern")
                with b:
                    es = st.number_input("Monthly Salary (₹) *", min_value=0.0, step=1000.0, format="%.2f")
                    if es > 0: st.info(f"Daily: ₹{es/30:,.2f} · Hourly: ₹{es/30/8:,.2f}")
                if st.form_submit_button("Add Employee", type="primary", use_container_width=True):
                    if en and es > 0:
                        try: api.create_employee(en, er, es); st.success(f"'{en}' added!"); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")

        if employees:
            st.dataframe(pd.DataFrame([{"ID": e["id"], "Name": e["name"], "Role": e.get("role",""),
                "Salary (₹)": e.get("salary",0), "Daily (₹)": e.get("daily_cost",0),
                "Hourly (₹)": e.get("hourly_cost",0)} for e in employees]),
                use_container_width=True, hide_index=True)
            de = st.selectbox("Remove employee", ["—"]+[f"{e['name']} (ID:{e['id']})" for e in employees])
            if de != "—" and st.button("🗑️ Remove"):
                eid = de.split("ID:")[1].rstrip(")")
                api.delete_employee(eid); st.rerun()

    with t2:
        st.markdown("Create login accounts for the Employee Portal.")
        with st.expander("➕ Create User Account"):
            with st.form("add_u"):
                a,b = st.columns(2)
                with a: un = st.text_input("Username *"); up = st.text_input("Password *", type="password")
                with b:
                    ud = st.text_input("Display Name"); ur = st.selectbox("Role", ["employee","admin"])
                    ue = st.selectbox("Link Employee", ["None"]+[f"{e['name']} (ID:{e['id']})" for e in employees])
                if st.form_submit_button("Create Account", type="primary", use_container_width=True):
                    if un and up:
                        eid = "" if ue == "None" else ue.split("ID:")[1].rstrip(")")
                        try: api.register_user(un, up, ur, ud or un, eid); st.success(f"User '{un}' created!"); st.rerun()
                        except Exception as e: st.error(f"Error: {e}")
        if users:
            st.dataframe(pd.DataFrame([{"Username": u["username"], "Role": u["role"],
                "Display": u.get("display_name",""), "Employee ID": u.get("employee_id","—")}
                for u in users]), use_container_width=True, hide_index=True)


# ═══ SETTINGS ═══
def pg_settings():
    st.markdown("### ⚙️ Settings")
    try: bank = api.get_bank_details()
    except: bank = {}

    st.markdown("#### 🏦 Bank Details (appears on Quotations)")
    with st.form("bank"):
        a,b = st.columns(2)
        with a:
            bn = st.text_input("Bank Name", value=bank.get("bank_name",""))
            bb = st.text_input("Branch", value=bank.get("branch",""))
            ba = st.text_input("Account Name", value=bank.get("account_name",""))
            bnum = st.text_input("Account Number", value=bank.get("account_number",""))
        with b:
            bi = st.text_input("IFSC Code", value=bank.get("ifsc",""))
            bp = st.text_input("PAN", value=bank.get("pan",""))
            bg = st.text_input("GSTIN", value=bank.get("gstin",""))
        if st.form_submit_button("Save Bank Details", type="primary", use_container_width=True):
            try:
                api.update_bank_details({"bank_name":bn,"branch":bb,"account_name":ba,
                    "account_number":bnum,"ifsc":bi,"pan":bp,"gstin":bg})
                st.success("Saved!")
            except Exception as e: st.error(f"Error: {e}")

    st.markdown("---"); st.markdown("#### ℹ️ System Info")
    st.markdown("""
- **Backend:** AWS Lambda + DynamoDB + API Gateway
- **Default Admin:** `admin` / `admin123`
- **GST:** 18% auto-applied to all invoices
- **TDS:** 10% auto-deducted from receivables
- **Cost calc:** Salary ÷ 30 days ÷ 8 hours = hourly rate
    """)

# ── Entry ──
if not st.session_state.logged_in: show_login()
else: show_app()
