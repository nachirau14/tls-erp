"""
AWS Lambda – REST API for Architectural Studio ERP.

Deployed behind API Gateway HTTP API (v2 payload format).
Uses DynamoDB for all storage.
"""

import json
import hashlib
import uuid
import os
import re
from datetime import datetime
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

# ─── DynamoDB setup ───
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION_NAME", "ap-south-1"))

TABLE_USERS       = dynamodb.Table("erp_users")
TABLE_EMPLOYEES   = dynamodb.Table("erp_employees")
TABLE_PROJECTS    = dynamodb.Table("erp_projects")
TABLE_TIMELOGS    = dynamodb.Table("erp_timelogs")
TABLE_INVOICES    = dynamodb.Table("erp_invoices")
TABLE_QUOTATIONS  = dynamodb.Table("erp_quotations")
TABLE_SETTINGS    = dynamodb.Table("erp_settings")
TABLE_COUNTERS    = dynamodb.Table("erp_counters")

GST_RATE = Decimal("0.18")
TDS_RATE = Decimal("0.10")

PROJECT_STAGES = [
    "2D Plans", "End Views", "Elevations", "3D Modeling",
    "Rendering", "Presentation", "Site", "Checking",
]

# ─── Helpers ───

def _uid():
    return str(uuid.uuid4())[:12]

def _now():
    return datetime.utcnow().isoformat()

def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def _dec(val):
    """Convert to Decimal for DynamoDB."""
    if isinstance(val, float):
        return Decimal(str(val))
    return val

def _json_serial(obj):
    """Handle Decimal serialization."""
    if isinstance(obj, Decimal):
        f = float(obj)
        return int(f) if f == int(f) else f
    raise TypeError(f"Type {type(obj)} not serializable")

def _resp(body, status=200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
        "body": json.dumps(body, default=_json_serial),
    }

def _err(msg, status=400):
    return _resp({"error": msg}, status)

def _body(event):
    raw = event.get("body", "") or ""
    if event.get("isBase64Encoded"):
        import base64
        raw = base64.b64decode(raw).decode()
    try:
        return json.loads(raw) if raw else {}
    except:
        return {}

def _qs(event):
    return event.get("queryStringParameters") or {}

def _require(data, fields):
    missing = [f for f in fields if not data.get(f)]
    if missing:
        return f"Missing: {', '.join(missing)}"
    return None

def _get_next_number(prefix):
    """Atomic counter via DynamoDB update expression."""
    resp = TABLE_COUNTERS.update_item(
        Key={"pk": prefix},
        UpdateExpression="SET #v = if_not_exists(#v, :zero) + :one",
        ExpressionAttributeNames={"#v": "value"},
        ExpressionAttributeValues={":zero": 0, ":one": 1},
        ReturnValues="UPDATED_NEW",
    )
    return int(resp["Attributes"]["value"])

def _scan_all(table):
    """Full table scan (fine for <1000 items)."""
    items = []
    resp = table.scan()
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    return items


# ─── Auth / Users ───

def _seed_admin():
    resp = TABLE_USERS.query(
        IndexName="username-index",
        KeyConditionExpression=Key("username").eq("admin"),
    )
    if not resp.get("Items"):
        TABLE_USERS.put_item(Item={
            "pk": _uid(),
            "username": "admin",
            "password": _hash("admin123"),
            "role": "admin",
            "display_name": "Administrator",
            "employee_id": "",
            "created_at": _now(),
        })

def _login(data):
    err = _require(data, ["username", "password"])
    if err:
        return _err(err)
    resp = TABLE_USERS.query(
        IndexName="username-index",
        KeyConditionExpression=Key("username").eq(data["username"]),
    )
    users = resp.get("Items", [])
    if not users or users[0]["password"] != _hash(data["password"]):
        return _err("Invalid credentials", 401)
    u = users[0]
    return _resp({
        "message": "Login successful",
        "user": {
            "id": u["pk"], "username": u["username"], "role": u["role"],
            "display_name": u.get("display_name", u["username"]),
            "employee_id": u.get("employee_id", ""),
        }
    })

def _register(data):
    err = _require(data, ["username", "password", "role"])
    if err:
        return _err(err)
    resp = TABLE_USERS.query(
        IndexName="username-index",
        KeyConditionExpression=Key("username").eq(data["username"]),
    )
    if resp.get("Items"):
        return _err("Username already exists")
    TABLE_USERS.put_item(Item={
        "pk": _uid(),
        "username": data["username"],
        "password": _hash(data["password"]),
        "role": data["role"],
        "display_name": data.get("display_name", data["username"]),
        "employee_id": data.get("employee_id", ""),
        "created_at": _now(),
    })
    return _resp({"message": "User created"})

def _list_users():
    items = _scan_all(TABLE_USERS)
    return _resp([{
        "id": u["pk"], "username": u["username"], "role": u["role"],
        "display_name": u.get("display_name", ""),
        "employee_id": u.get("employee_id", ""),
    } for u in items])


# ─── Employees ───

def _create_employee(data):
    err = _require(data, ["name", "salary"])
    if err:
        return _err(err)
    salary = Decimal(str(data["salary"]))
    daily = (salary / 30).quantize(Decimal("0.01"))
    hourly = (daily / 8).quantize(Decimal("0.01"))
    pk = _uid()
    TABLE_EMPLOYEES.put_item(Item={
        "pk": pk,
        "name": data["name"],
        "role": data.get("role", ""),
        "salary": salary,
        "daily_cost": daily,
        "hourly_cost": hourly,
        "created_at": _now(),
    })
    return _resp({"message": "Employee created", "id": pk})

def _list_employees():
    items = _scan_all(TABLE_EMPLOYEES)
    return _resp([{**item, "id": item["pk"]} for item in items])

def _delete_employee(emp_id):
    TABLE_EMPLOYEES.delete_item(Key={"pk": emp_id})
    return _resp({"message": "Deleted"})


# ─── Projects ───

def _create_project(data):
    err = _require(data, ["name"])
    if err:
        return _err(err)
    stages = {s: "Not Started" for s in PROJECT_STAGES}
    pk = _uid()
    TABLE_PROJECTS.put_item(Item={
        "pk": pk,
        "name": data["name"],
        "client_name": data.get("client_name", ""),
        "total_cost": _dec(float(data.get("total_cost", 0))),
        "start_date": data.get("start_date", _now()[:10]),
        "status": "active",
        "description": data.get("description", ""),
        "stages": stages,
        "created_at": _now(),
    })
    return _resp({"message": "Project created", "id": pk})

def _list_projects():
    items = _scan_all(TABLE_PROJECTS)
    return _resp([{**item, "id": item["pk"]} for item in items])

def _update_project(proj_id, data):
    item = TABLE_PROJECTS.get_item(Key={"pk": proj_id}).get("Item")
    if not item:
        return _err("Not found", 404)
    for field in ["name", "client_name", "start_date", "status", "description"]:
        if field in data:
            item[field] = data[field]
    if "total_cost" in data:
        item["total_cost"] = _dec(float(data["total_cost"]))
    if "stages" in data:
        item["stages"] = data["stages"]
    TABLE_PROJECTS.put_item(Item=item)
    return _resp({"message": "Updated"})

def _delete_project(proj_id):
    TABLE_PROJECTS.delete_item(Key={"pk": proj_id})
    return _resp({"message": "Deleted"})


# ─── Time Logs ───

def _create_timelog(data):
    err = _require(data, ["employee_id", "project_id", "hours", "date"])
    if err:
        return _err(err)
    pk = _uid()
    TABLE_TIMELOGS.put_item(Item={
        "pk": pk,
        "employee_id": str(data["employee_id"]),
        "project_id": str(data["project_id"]),
        "hours": _dec(float(data["hours"])),
        "date": data["date"],
        "comments": data.get("comments", ""),
        "created_at": _now(),
    })
    return _resp({"message": "Logged", "id": pk})

def _list_timelogs(params):
    emp_id = params.get("employee_id")
    proj_id = params.get("project_id")

    if emp_id:
        resp = TABLE_TIMELOGS.query(
            IndexName="employee-index",
            KeyConditionExpression=Key("employee_id").eq(str(emp_id)),
        )
        items = resp.get("Items", [])
    elif proj_id:
        resp = TABLE_TIMELOGS.query(
            IndexName="project-index",
            KeyConditionExpression=Key("project_id").eq(str(proj_id)),
        )
        items = resp.get("Items", [])
    else:
        items = _scan_all(TABLE_TIMELOGS)

    return _resp([{**item, "id": item["pk"]} for item in items])

def _delete_timelog(log_id):
    TABLE_TIMELOGS.delete_item(Key={"pk": log_id})
    return _resp({"message": "Deleted"})


# ─── Invoices ───

def _create_invoice(data):
    err = _require(data, ["client_name", "amount", "date"])
    if err:
        return _err(err)

    amt = Decimal(str(data["amount"]))
    gst = (amt * GST_RATE).quantize(Decimal("0.01"))
    tds = (amt * TDS_RATE).quantize(Decimal("0.01"))
    total = amt + gst
    receivable = (amt - tds) + gst

    inv_num = _get_next_number("INV")
    dt = datetime.strptime(data["date"], "%Y-%m-%d")
    m = dt.month

    quarter = "Q1" if m in (4,5,6) else "Q2" if m in (7,8,9) else "Q3" if m in (10,11,12) else "Q4"
    fy = f"FY{dt.year}-{str(dt.year+1)[2:]}" if m >= 4 else f"FY{dt.year-1}-{str(dt.year)[2:]}"

    pk = _uid()
    TABLE_INVOICES.put_item(Item={
        "pk": pk,
        "invoice_number": f"INV-{str(inv_num).zfill(4)}",
        "client_name": data["client_name"],
        "description": data.get("description", ""),
        "invoice_type": data.get("invoice_type", "tax"),
        "date": data["date"],
        "basic_amount": amt,
        "gst": gst, "tds": tds, "total": total, "receivable": receivable,
        "received": False,
        "received_date": "",
        "quarter": quarter, "fy": fy,
        "project_id": data.get("project_id", ""),
        "created_at": _now(),
    })
    return _resp({"message": "Invoice created", "id": pk, "invoice_number": f"INV-{str(inv_num).zfill(4)}"})

def _list_invoices(params):
    items = _scan_all(TABLE_INVOICES)
    q = params.get("quarter")
    fy = params.get("fy")
    if q:
        items = [i for i in items if i.get("quarter") == q]
    if fy:
        items = [i for i in items if i.get("fy") == fy]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    return _resp([{**item, "id": item["pk"]} for item in items])

def _update_invoice(inv_id, data):
    item = TABLE_INVOICES.get_item(Key={"pk": inv_id}).get("Item")
    if not item:
        return _err("Not found", 404)
    if "received" in data:
        item["received"] = data["received"]
        item["received_date"] = _now()[:10] if data["received"] else ""
    for f in ["client_name", "description", "invoice_type"]:
        if f in data:
            item[f] = data[f]
    TABLE_INVOICES.put_item(Item=item)
    return _resp({"message": "Updated"})


# ─── Quotations ───

def _create_quotation(data):
    err = _require(data, ["client_name", "project_name"])
    if err:
        return _err(err)
    qtn_num = _get_next_number("QTN")
    pk = _uid()
    TABLE_QUOTATIONS.put_item(Item={
        "pk": pk,
        "quotation_number": f"QTN-{str(qtn_num).zfill(4)}",
        "client_name": data["client_name"],
        "project_name": data["project_name"],
        "date": data.get("date", _now()[:10]),
        "total_amount": _dec(float(data.get("total_amount", 0))),
        "scope": data.get("scope", ""),
        "timelines": data.get("timelines", ""),
        "deliverables": data.get("deliverables", ""),
        "legal_clauses": data.get("legal_clauses", ""),
        "payment_structure": data.get("payment_structure", ""),
        "status": "draft",
        "created_at": _now(),
    })
    return _resp({"message": "Quotation created", "id": pk})

def _list_quotations():
    items = _scan_all(TABLE_QUOTATIONS)
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    return _resp([{**item, "id": item["pk"]} for item in items])

def _update_quotation(qtn_id, data):
    item = TABLE_QUOTATIONS.get_item(Key={"pk": qtn_id}).get("Item")
    if not item:
        return _err("Not found", 404)
    for f in ["client_name", "project_name", "scope", "timelines",
              "deliverables", "legal_clauses", "payment_structure", "status"]:
        if f in data:
            item[f] = data[f]
    if "total_amount" in data:
        item["total_amount"] = _dec(float(data["total_amount"]))
    TABLE_QUOTATIONS.put_item(Item=item)
    return _resp({"message": "Updated"})


# ─── Bank Details (singleton) ───

def _get_bank_details():
    item = TABLE_SETTINGS.get_item(Key={"pk": "bank_details"}).get("Item")
    if item:
        return _resp({k: v for k, v in item.items() if k != "pk"})
    return _resp({
        "bank_name": "", "branch": "", "account_name": "",
        "account_number": "", "ifsc": "", "pan": "", "gstin": ""
    })

def _update_bank_details(data):
    item = {"pk": "bank_details"}
    for f in ["bank_name", "branch", "account_name", "account_number", "ifsc", "pan", "gstin"]:
        item[f] = data.get(f, "")
    TABLE_SETTINGS.put_item(Item=item)
    return _resp({"message": "Saved"})


# ═══════════════════════════════════════════════
# Lambda handler / Router
# ═══════════════════════════════════════════════

def lambda_handler(event, context):
    """Entry point – API Gateway HTTP API v2 payload format."""

    # Seed admin on cold start
    _seed_admin()

    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/").rstrip("/")

    # Strip stage prefix if present (e.g. /prod/health -> /health)
    stage = event.get("requestContext", {}).get("stage", "")
    if stage and path.startswith(f"/{stage}"):
        path = path[len(f"/{stage}"):]
    if not path:
        path = "/"

    if method == "OPTIONS":
        return _resp({"status": "ok"})

    try:
        # ── Auth ──
        if path == "/auth/login" and method == "POST":
            return _login(_body(event))
        if path == "/auth/register" and method == "POST":
            return _register(_body(event))
        if path == "/auth/users" and method == "GET":
            return _list_users()

        # ── Employees ──
        if path == "/employees" and method == "GET":
            return _list_employees()
        if path == "/employees" and method == "POST":
            return _create_employee(_body(event))
        if re.match(r"^/employees/[\w-]+$", path) and method == "DELETE":
            return _delete_employee(path.split("/")[-1])

        # ── Projects ──
        if path == "/projects" and method == "GET":
            return _list_projects()
        if path == "/projects" and method == "POST":
            return _create_project(_body(event))
        if re.match(r"^/projects/[\w-]+$", path) and method == "PUT":
            return _update_project(path.split("/")[-1], _body(event))
        if re.match(r"^/projects/[\w-]+$", path) and method == "DELETE":
            return _delete_project(path.split("/")[-1])

        # ── Time Logs ──
        if path == "/timelogs" and method == "GET":
            return _list_timelogs(_qs(event))
        if path == "/timelogs" and method == "POST":
            return _create_timelog(_body(event))
        if re.match(r"^/timelogs/[\w-]+$", path) and method == "DELETE":
            return _delete_timelog(path.split("/")[-1])

        # ── Invoices ──
        if path == "/invoices" and method == "GET":
            return _list_invoices(_qs(event))
        if path == "/invoices" and method == "POST":
            return _create_invoice(_body(event))
        if re.match(r"^/invoices/[\w-]+$", path) and method == "PUT":
            return _update_invoice(path.split("/")[-1], _body(event))

        # ── Quotations ──
        if path == "/quotations" and method == "GET":
            return _list_quotations()
        if path == "/quotations" and method == "POST":
            return _create_quotation(_body(event))
        if re.match(r"^/quotations/[\w-]+$", path) and method == "PUT":
            return _update_quotation(path.split("/")[-1], _body(event))

        # ── Bank Details ──
        if path == "/bank-details" and method == "GET":
            return _get_bank_details()
        if path == "/bank-details" and method == "PUT":
            return _update_bank_details(_body(event))

        # ── Health ──
        if path == "/health":
            return _resp({"status": "healthy", "timestamp": _now()})

        return _err("Not found", 404)

    except Exception as e:
        return _err(f"Internal error: {str(e)}", 500)
