# Architectural Studio ERP – AWS + Streamlit

## Architecture

```
┌──────────────────────────┐     ┌──────────────────────────┐
│  Streamlit Employee      │     │  Streamlit Management    │
│  (Streamlit Cloud)       │     │  (Streamlit Cloud)       │
│                          │     │                          │
│  • Login (employee/admin)│     │  • Login (admin only)    │
│  • View/create projects  │     │  • Dashboard             │
│  • Update project stages │     │  • Invoicing & GST       │
│  • Log daily time        │     │  • Quotations            │
│  • View own time logs    │     │  • Projects & Stages     │
│                          │     │  • Time Tracking (all)   │
│                          │     │  • Cost of Labour        │
│                          │     │  • Employee & User Mgmt  │
│                          │     │  • Bank Details/Settings │
└───────────┬──────────────┘     └───────────┬──────────────┘
            │                                │
            └──────────┬─────────────────────┘
                       │  HTTPS (REST API)
                       ▼
            ┌──────────────────────┐
            │  API Gateway HTTP API│
            │  (CORS enabled)      │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  AWS Lambda          │
            │  (Python 3.11)       │
            │  erp-api             │
            └──────────┬───────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  DynamoDB Tables     │
            │  (PAY_PER_REQUEST)   │
            │                      │
            │  • erp_users         │
            │  • erp_employees     │
            │  • erp_projects      │
            │  • erp_timelogs      │
            │  • erp_invoices      │
            │  • erp_quotations    │
            │  • erp_settings      │
            │  • erp_counters      │
            └──────────────────────┘
```

## File Structure

```
erp/
├── cloudformation.yaml               # Full stack: DynamoDB + Lambda + API Gateway + IAM
├── lambda_function/
│   └── lambda_function.py            # Lambda handler – all API routes
├── shared/
│   ├── __init__.py
│   ├── models.py                     # Constants (GST/TDS rates, stages)
│   └── api_client.py                 # HTTP client for Streamlit → Lambda
├── streamlit_employee/
│   ├── app.py                        # Employee portal
│   ├── requirements.txt
│   └── .streamlit/secrets.toml       # API_BASE_URL
├── streamlit_management/
│   ├── app.py                        # Management portal
│   ├── requirements.txt
│   └── .streamlit/secrets.toml       # API_BASE_URL
└── README.md
```

---

## Prerequisites

1. **AWS account** with admin access
2. **AWS CLI v2** installed and configured (`aws configure`)
3. **Python 3.11+**
4. **GitHub account** (for Streamlit Community Cloud deployment)

---

## Step 1: Deploy AWS Infrastructure (CloudFormation)

```bash
# Deploy the full stack (DynamoDB + Lambda + API Gateway + IAM)
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name studio-erp \
  --region ap-south-1 \
  --capabilities CAPABILITY_NAMED_IAM

# Get the API URL from the stack outputs
aws cloudformation describe-stacks \
  --stack-name studio-erp \
  --region ap-south-1 \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text
```

This prints something like:
```
https://abc123xyz.execute-api.ap-south-1.amazonaws.com/prod
```

Save this URL – you'll need it for both Streamlit apps.

## Step 2: Deploy Lambda Code

The CloudFormation template creates a placeholder Lambda. Now deploy the actual code:

```bash
# Package the Lambda function
cd lambda_function/
zip lambda_function.zip lambda_function.py

# Deploy the code
aws lambda update-function-code \
  --function-name erp-api \
  --zip-file fileb://lambda_function.zip \
  --region ap-south-1
```

### Test it:
```bash
# Health check
curl https://YOUR-API-URL/health

# Login (admin auto-created on first call)
curl -X POST https://YOUR-API-URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

You should get: `{"message": "Login successful", "user": {...}}`

---

## Step 3: Deploy Streamlit Apps to Community Cloud

### 3a. Push to GitHub

Create a GitHub repository with this exact structure:

```
your-repo/
├── shared/
│   ├── __init__.py
│   ├── models.py
│   └── api_client.py
├── streamlit_employee/
│   ├── app.py
│   └── requirements.txt
├── streamlit_management/
│   ├── app.py
│   └── requirements.txt
```

**Do NOT push the `.streamlit/secrets.toml` files** – secrets are set in the
Streamlit Cloud dashboard.

### 3b. Deploy on Streamlit Community Cloud

1. Go to **https://share.streamlit.io** and sign in with GitHub
2. Click **"New app"**

**Employee Portal:**
- Repository: `your-username/your-repo`
- Branch: `main`
- Main file path: `streamlit_employee/app.py`
- Click **"Advanced settings"** → Secrets → paste:
  ```toml
  API_BASE_URL = "https://YOUR-API-ID.execute-api.ap-south-1.amazonaws.com/prod"
  ```
- Click **Deploy**

**Management Portal:**
- Repeat the same steps but set main file to: `streamlit_management/app.py`
- Add the same `API_BASE_URL` secret

Both apps will be live at URLs like:
- `https://your-app-employee.streamlit.app`
- `https://your-app-management.streamlit.app`

---

## Step 4: First-Time Setup

1. Open the **Management Portal** → login with `admin` / `admin123`
2. Go to **⚙️ Settings** → enter your bank details (GSTIN, PAN, etc.)
3. Go to **👥 Employees & Users** → **Employees** tab:
   - Add each employee with name, role, and monthly salary
   - The system auto-computes daily cost (salary ÷ 30) and hourly cost (daily ÷ 8)
4. Go to **🔐 User Accounts** tab:
   - Create a login for each employee (username + password)
   - Set role = `employee`
   - Link each account to the corresponding employee record
5. Go to **📁 Projects & Stages** → create your active projects
6. Share the **Employee Portal URL** with your team

---

## Default Credentials

| Portal     | Username | Password  |
|------------|----------|-----------|
| Management | admin    | admin123  |

⚠️ **Change the admin password immediately after first login.**

---

## Feature Matrix

| Feature                | Employee Portal | Management Portal |
|------------------------|:---------------:|:-----------------:|
| Login                  | ✅              | ✅ (admin only)   |
| Dashboard              | ✅              | ✅                |
| View Projects          | ✅              | ✅                |
| Create Projects        | ✅              | ✅                |
| Update Project Stages  | ✅              | ✅                |
| Delete Projects        | ❌              | ✅                |
| Log Time               | ✅ (own)        | ✅ (any employee) |
| View Time Logs         | ✅ (own)        | ✅ (all)          |
| Create Invoices        | ❌              | ✅                |
| Mark Invoices Paid     | ❌              | ✅                |
| GST Quarterly Summary  | ❌              | ✅                |
| Create Quotations      | ❌              | ✅                |
| Cost of Labour         | ❌              | ✅                |
| Add/Remove Employees   | ❌              | ✅                |
| Create User Accounts   | ❌              | ✅                |
| Bank Details           | ❌              | ✅                |

---

## Invoice Calculation Logic

```
Example: Basic amount = ₹1,00,000

  Basic Amount:                   ₹1,00,000
+ GST @ 18%:                     ₹   18,000
= Total Invoice:                 ₹1,18,000

  Client deducts TDS @ 10%:     -₹   10,000  (on basic amount)

  Client pays you:               ₹1,08,000  (₹90,000 + ₹18,000 GST)
  TDS credited to your account:  ₹   10,000  (filed in your company name)
```

Indian Financial Year Quarters:
- Q1: April–June
- Q2: July–September
- Q3: October–December
- Q4: January–March

---

## Cost of Labour Calculation

```
Employee salary:   ₹30,000 / month
Daily cost:        ₹30,000 ÷ 30 = ₹1,000
Hourly cost:       ₹1,000 ÷ 8   = ₹125

If employee logs 100 hours on a project:
Labour cost:       100 × ₹125 = ₹12,500

Profit = Project receivable − Total labour cost
```

---

## API Endpoints Reference

| Method | Path                 | Description                     |
|--------|----------------------|---------------------------------|
| POST   | /auth/login          | Login                           |
| POST   | /auth/register       | Create user account             |
| GET    | /auth/users          | List all users                  |
| GET    | /employees           | List employees                  |
| POST   | /employees           | Add employee                    |
| DELETE | /employees/:id       | Remove employee                 |
| GET    | /projects            | List projects (with stages)     |
| POST   | /projects            | Create project                  |
| PUT    | /projects/:id        | Update project / stages         |
| DELETE | /projects/:id        | Delete project                  |
| GET    | /timelogs            | List time logs (?employee_id=)  |
| POST   | /timelogs            | Create time log                 |
| DELETE | /timelogs/:id        | Delete time log                 |
| GET    | /invoices            | List invoices (?quarter=&fy=)   |
| POST   | /invoices            | Create invoice                  |
| PUT    | /invoices/:id        | Update (mark paid/unpaid)       |
| GET    | /quotations          | List quotations                 |
| POST   | /quotations          | Create quotation                |
| PUT    | /quotations/:id      | Update quotation                |
| GET    | /bank-details        | Get bank details                |
| PUT    | /bank-details        | Update bank details             |
| GET    | /health              | Health check                    |

---

## AWS Costs (Estimate)

With ~5 employees and light usage:
- **Lambda:** Free tier covers 1M requests/month
- **DynamoDB:** PAY_PER_REQUEST, typically < $1/month
- **API Gateway:** Free tier covers 1M requests/month
- **Total:** Effectively **free** for a small studio

---

## Cleanup

To tear down everything:

```bash
aws cloudformation delete-stack --stack-name studio-erp --region ap-south-1
```

---

## Security Notes

- Passwords are SHA-256 hashed before storage
- For production hardening, consider:
  - API Gateway authorizers (JWT/Cognito)
  - Restricting CORS origins to your Streamlit app domains
  - Lambda environment encryption
  - DynamoDB encryption at rest (enabled by default)
  - WAF on API Gateway
  - CloudWatch alarms
