# Architectural Studio ERP

A complete ERP system for small architectural studios in India, built on
**AWS Lambda + DynamoDB + API Gateway** with two separate **Streamlit** interfaces.

---

## Architecture

```
┌────────────────────────────┐      ┌────────────────────────────┐
│   Streamlit Employee App   │      │  Streamlit Management App  │
│   (Streamlit Cloud)        │      │  (Streamlit Cloud)         │
│                            │      │                            │
│  • Login (employee/admin)  │      │  • Login (admin only)      │
│  • Dashboard               │      │  • Dashboard               │
│  • Projects & stages       │      │  • Invoicing & GST         │
│  • Log daily time          │      │  • Quotations (6 sections) │
│  • My time log history     │      │  • Projects & stages       │
│  • Leave tracker           │      │  • Time tracking + charts  │
│  • Expense tracker         │      │  • Cost of labour analysis │
│  • Holiday calendar        │      │  • Employee mgmt (edit)    │
│                            │      │  • User account mgmt      │
│                            │      │  • Leave/expense approvals │
│                            │      │  • Holiday list (editable) │
│                            │      │  • Bank details / settings │
└─────────────┬──────────────┘      └─────────────┬──────────────┘
              │                                   │
              └─────────────┬─────────────────────┘
                            │  HTTPS  (REST API)
                            ▼
              ┌──────────────────────────┐
              │   AWS API Gateway        │
              │   (HTTP API, CORS)       │
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │   AWS Lambda             │
              │   erp-api (Python 3.11)  │
              │   ap-south-1             │
              └────────────┬─────────────┘
                           │
              ┌────────────┴─────────────┐
              │                          │
              ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│   DynamoDB (11 tables)│   │   S3 Bucket          │
│   PAY_PER_REQUEST     │   │   Leave attachments  │
│                       │   │                      │
│   • erp_users         │   └──────────────────────┘
│   • erp_employees     │
│   • erp_projects      │
│   • erp_timelogs      │
│   • erp_invoices      │
│   • erp_quotations    │
│   • erp_settings      │
│   • erp_counters      │
│   • erp_leaves        │
│   • erp_expenses      │
│   • erp_holidays      │
└───────────────────────┘
```

---

## File Structure

```
erp/
├── README.md                              ← this file
├── cloudformation.yaml                    ← full AWS stack (DynamoDB + Lambda + API GW + S3 + IAM)
│
├── lambda_function/
│   ├── lambda_function.py                 ← Lambda handler – all API routes
│   ├── pdf_generator.py                   ← PDF generation (invoices & quotations)
│   └── requirements.txt                   ← Lambda dependencies (reportlab, boto3)
│
├── shared/
│   ├── __init__.py
│   ├── models.py                          ← constants (GST/TDS rates, project stages)
│   ├── api_client.py                      ← HTTP client used by both Streamlit apps
│   └── styles.py                          ← shared CSS (glass morphism, textures, typography)
│
├── streamlit_employee/
│   ├── app.py                             ← employee portal UI (466 lines)
│   ├── requirements.txt
│   └── .streamlit/
│       ├── config.toml                    ← Streamlit theme (terracotta + cream)
│       └── secrets.toml                   ← API_BASE_URL (edit this)
│
└── streamlit_management/
    ├── app.py                             ← management portal UI (898 lines)
    ├── requirements.txt
    └── .streamlit/
        ├── config.toml                    ← Streamlit theme (charcoal + cream)
        └── secrets.toml                   ← API_BASE_URL (edit this)
```

---

## Prerequisites

- **AWS account** with admin access
- **AWS CLI v2** installed and configured (`aws configure`)
- **Python 3.11+**
- **GitHub account** (for Streamlit Community Cloud)

---

## Deployment

### Step 1 — Deploy AWS Infrastructure

```bash
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name studio-erp \
  --region ap-south-1 \
  --capabilities CAPABILITY_NAMED_IAM
```

Get the API URL:

```bash
aws cloudformation describe-stacks \
  --stack-name studio-erp \
  --region ap-south-1 \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text
```

This gives you something like:
`https://abc123xyz.execute-api.ap-south-1.amazonaws.com/prod`

### Step 2 — Deploy Lambda Code

The Lambda needs `reportlab` for PDF generation, so we use a layer or package it with dependencies:

```bash
cd lambda_function/

# Install dependencies into a package directory
pip install -r requirements.txt -t package/

# Copy Lambda code into package
cp lambda_function.py pdf_generator.py package/

# Create zip from inside the package directory
cd package/
zip -r ../lambda_deploy.zip .
cd ..

# Deploy
aws lambda update-function-code \
  --function-name erp-api \
  --zip-file fileb://lambda_deploy.zip \
  --region ap-south-1
```

### Step 3 — Test

```bash
# Health check
curl https://YOUR-API-URL/health

# Login (admin auto-created on first call)
curl -X POST https://YOUR-API-URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Step 4 — Deploy Streamlit to Community Cloud

1. Push code to GitHub (the full `erp/` directory).
   **Do NOT push `.streamlit/secrets.toml`** — add it to `.gitignore`.

2. Go to **https://share.streamlit.io** → sign in with GitHub.

3. **Employee Portal:**
   - Repository: your repo
   - Main file: `streamlit_employee/app.py`
   - Advanced settings → Secrets:
     ```toml
     API_BASE_URL = "https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/prod"
     ```

4. **Management Portal:**
   - Main file: `streamlit_management/app.py`
   - Same secret as above.

Both apps need the `shared/` folder accessible in the same repo.

### Step 5 — First-Time Setup

1. Open Management Portal → login with `admin` / `admin123`
2. **Settings** → enter bank details (GSTIN, PAN, etc.)
3. **Employees & Users → Employees** → add each employee (name, role, salary)
4. **Employees & Users → User Accounts** → create logins, link to employee records
5. **Projects** → create active projects
6. **Holiday List** → add holidays for the current year
7. Share the Employee Portal URL with your team

---

## Default Credentials

| Portal     | Username | Password  |
|------------|----------|-----------|
| Management | admin    | admin123  |

**Change the admin password immediately after first login.**

---

## Feature Matrix

| Feature                  | Employee Portal | Management Portal |
|--------------------------|:---------------:|:-----------------:|
| Login                    | ✅              | ✅ (admin only)   |
| Dashboard                | ✅              | ✅                |
| View / create projects   | ✅              | ✅                |
| Update project stages    | ✅              | ✅                |
| Delete projects          | ❌              | ✅                |
| Log time                 | ✅ (own)        | ✅ (any employee) |
| View time logs           | ✅ (own)        | ✅ (all + charts) |
| Time distribution charts | ❌              | ✅                |
| Create invoices          | ❌              | ✅                |
| Mark invoices paid       | ❌              | ✅                |
| GST quarterly summary    | ❌              | ✅                |
| Create quotations        | ❌              | ✅                |
| Cost of labour analysis  | ❌              | ✅                |
| Add employees            | ❌              | ✅                |
| Edit employees           | ❌              | ✅                |
| Remove employees         | ❌              | ✅                |
| Create user accounts     | ❌              | ✅                |
| Apply for leave          | ✅              | ❌                |
| Approve/reject leave     | ❌              | ✅                |
| Submit expenses          | ✅              | ❌                |
| Approve/reject expenses  | ❌              | ✅                |
| View holiday calendar    | ✅ (read only)  | ✅ (editable)     |

---

## Business Logic

### Invoice Calculation

```
Basic amount:        ₹1,00,000
+ GST @ 18%:         ₹   18,000
= Total Invoice:     ₹1,18,000

Client deducts TDS @ 10% on basic:   -₹10,000

Client pays:    ₹90,000 + ₹18,000  =  ₹1,08,000
TDS credit:     ₹10,000 (filed in your company name)
```

Indian Financial Year Quarters:
- Q1: April – June
- Q2: July – September
- Q3: October – December
- Q4: January – March

### Cost of Labour

```
Salary:   ₹30,000 / month
Daily:    ₹30,000 ÷ 30 = ₹1,000
Hourly:   ₹1,000 ÷ 8   = ₹125

100 hours on project → ₹12,500 labour cost
Profit = Receivable − Total labour cost
```

### Project Stages

Each project tracks 8 stages, each with status (Not Started / In Progress / Review / Completed):

1. 2D Plans
2. End Views
3. Elevations
4. 3D Modeling
5. Rendering
6. Presentation
7. Site
8. Checking

---

## Time Tracking Charts (Management Portal)

The Time Tracking page includes four visualizations:

- **Hours by Project** — bar chart showing total hours logged per project
- **Hours by Employee** — bar chart showing total hours logged per employee
- **Daily Hours Trend** — line chart of hours over time
- **Employee × Project Breakdown** — heatmap-style table showing who spent how much time on which project

---

## Expense Categories

- Site Visit
- Travel / Flight
- Cab / Transport
- Food & Meals
- Office Supplies
- Printing / Plotting
- Software / License
- Other

---

## Leave Types

- Casual Leave
- Sick Leave
- Earned Leave
- Comp Off
- Work From Home
- Half Day
- Other

---

## API Endpoints

| Method | Path                 | Description                        |
|--------|----------------------|------------------------------------|
| POST   | /auth/login          | Login                              |
| POST   | /auth/register       | Create user account                |
| GET    | /auth/users          | List all users                     |
| GET    | /employees           | List employees                     |
| POST   | /employees           | Add employee                       |
| PUT    | /employees/:id       | Edit employee (name, role, salary) |
| DELETE | /employees/:id       | Remove employee                    |
| GET    | /projects            | List projects (with stages)        |
| POST   | /projects            | Create project                     |
| PUT    | /projects/:id        | Update project / stages            |
| DELETE | /projects/:id        | Delete project                     |
| GET    | /timelogs            | List time logs (?employee_id=)     |
| POST   | /timelogs            | Create time log                    |
| DELETE | /timelogs/:id        | Delete time log                    |
| GET    | /invoices            | List invoices (?quarter=&fy=)      |
| POST   | /invoices            | Create invoice                     |
| PUT    | /invoices/:id        | Update (mark paid/unpaid)          |
| GET    | /quotations          | List quotations                    |
| POST   | /quotations          | Create quotation                   |
| PUT    | /quotations/:id      | Update quotation                   |
| GET    | /bank-details        | Get bank details                   |
| PUT    | /bank-details        | Update bank details                |
| GET    | /leaves              | List leaves (?employee_id=)        |
| POST   | /leaves              | Apply for leave                    |
| PUT    | /leaves/:id          | Update leave (approve/reject)      |
| DELETE | /leaves/:id          | Delete leave                       |
| POST   | /leaves/upload-url   | Get S3 presigned upload URL        |
| GET    | /expenses            | List expenses (?employee_id=)      |
| POST   | /expenses            | Submit expense                     |
| PUT    | /expenses/:id        | Update expense (approve/reject)    |
| DELETE | /expenses/:id        | Delete expense                     |
| GET    | /holidays            | List holidays (?year=)             |
| POST   | /holidays            | Add holiday                        |
| PUT    | /holidays/:id        | Update holiday                     |
| DELETE | /holidays/:id        | Delete holiday                     |
| GET    | /health              | Health check                       |

---

## Design System

Both apps share a cohesive visual identity via `shared/styles.py`:

- **Typography:** Playfair Display (serif) for headings + Source Sans 3 for body
- **Palette:** Terracotta (#c4704b), Sage (#7a9a7e), Gold (#c9a96e), Charcoal (#2c2825), Cream (#f7f4ef)
- **Glass morphism:** Stat cards, expanders, login cards use backdrop-filter blur
- **Textures:** SVG pattern overlays + radial gradient washes on backgrounds
- **Hover effects:** Cards lift with translateY + shadow expansion
- **Sidebar:** Deep charcoal gradient with terracotta accent on hover/selection
- **Progress bars:** Gradient from terracotta → gold → sage

---

## AWS Cost Estimate

For a 5-person studio with light usage:

| Service      | Monthly Cost         |
|--------------|----------------------|
| Lambda       | Free tier (1M req)   |
| DynamoDB     | < $1 (PAY_PER_REQUEST) |
| API Gateway  | Free tier (1M req)   |
| S3           | < $0.10              |
| **Total**    | **~$1/month**        |

---

## Cleanup

```bash
# Delete everything
aws cloudformation delete-stack --stack-name studio-erp --region ap-south-1
```

Note: The S3 bucket must be empty before CloudFormation can delete it.

---

## Security Notes

- Passwords are SHA-256 hashed before storage in DynamoDB
- For production, consider adding:
  - AWS Cognito or JWT-based authentication
  - CORS origin restrictions (replace `*` with your Streamlit domains)
  - WAF on API Gateway
  - DynamoDB encryption at rest (enabled by default)
  - CloudWatch alarms for error rates
  - Input validation and sanitization
