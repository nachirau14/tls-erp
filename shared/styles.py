"""
Shared UI styling for the Studio ERP Streamlit apps.
Premium editorial aesthetic with glass morphism, subtle textures, and rich typography.
"""

# ─── Color Palette ───
# Warm charcoal + terracotta + sage + cream — inspired by architectural materials

COLORS = {
    "bg_dark": "#1a1714",
    "bg_warm": "#f7f4ef",
    "charcoal": "#2c2825",
    "terracotta": "#c4704b",
    "terracotta_light": "#e8956e",
    "sage": "#7a9a7e",
    "sage_light": "#a8c5ab",
    "cream": "#faf6f0",
    "gold": "#c9a96e",
    "slate": "#64605a",
    "mist": "#e8e4de",
}


def get_employee_css():
    """Return CSS for the Employee Portal — warm, light theme."""
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Source+Sans+3:wght@300;400;500;600;700&display=swap');

/* ── Global ── */
.stApp {
    font-family: 'Source Sans 3', sans-serif;
    background: #f7f4ef;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(196,112,75,0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(122,154,126,0.05) 0%, transparent 50%),
        url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c4704b' fill-opacity='0.02'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

/* ── Sidebar ── */
div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2c2825 0%, #1a1714 100%) !important;
    border-right: 1px solid rgba(201,169,110,0.15);
}
div[data-testid="stSidebar"] * {
    color: #e8e4de !important;
}
div[data-testid="stSidebar"] .stRadio > label {
    transition: all 0.2s ease;
}
div[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
    background: rgba(196,112,75,0.15) !important;
    border-radius: 8px;
    padding-left: 8px !important;
}
div[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
    background: rgba(196,112,75,0.2) !important;
    border-radius: 8px;
}

/* ── Header Banner ── */
.emp-header {
    background: linear-gradient(135deg, #2c2825 0%, #3d3630 40%, #4a3f37 100%);
    color: #faf6f0;
    padding: 2rem 2.5rem;
    border-radius: 20px;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(201,169,110,0.1);
    box-shadow: 0 8px 32px rgba(26,23,20,0.12);
}
.emp-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(196,112,75,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.emp-header::after {
    content: '';
    position: absolute;
    bottom: -40%;
    left: 10%;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(122,154,126,0.1) 0%, transparent 70%);
    border-radius: 50%;
}
.emp-header h1 {
    margin: 0;
    font-family: 'Playfair Display', serif;
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    position: relative;
    z-index: 1;
}
.emp-header p {
    margin: 0.4rem 0 0;
    opacity: 0.6;
    font-size: 0.85rem;
    font-weight: 300;
    letter-spacing: 0.5px;
    position: relative;
    z-index: 1;
}

/* ── Stat Cards ── */
.stat-card {
    background: rgba(255,255,255,0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(201,169,110,0.12);
    border-radius: 16px;
    padding: 1.4rem 1.5rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 12px rgba(26,23,20,0.04);
}
.stat-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(26,23,20,0.08);
    border-color: rgba(196,112,75,0.25);
}
.stat-card .label {
    font-size: 0.65rem;
    color: #64605a;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
}
.stat-card .value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #2c2825;
    margin-top: 0.3rem;
}
.stat-card .value.terracotta { color: #c4704b; }
.stat-card .value.sage { color: #5a8a5e; }
.stat-card .value.gold { color: #b08d4a; }

/* ── Stage Badges ── */
.stage-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    margin: 3px;
    transition: all 0.2s ease;
    cursor: default;
}
.stage-badge:hover {
    transform: scale(1.05);
}
.stage-not-started { background: #f0ece6; color: #8a857e; border: 1px solid #ddd8d0; }
.stage-in-progress { background: #fef3e2; color: #b87a1a; border: 1px solid #f5deb3; }
.stage-review { background: #e6f0eb; color: #3d7a52; border: 1px solid #c0d9ca; }
.stage-completed { background: #e0efe2; color: #2d6b3f; border: 1px solid #a8d5b3; }

/* ── Containers & Expanders ── */
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(201,169,110,0.1) !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 8px rgba(26,23,20,0.03);
    transition: all 0.3s ease;
    margin-bottom: 8px;
}
div[data-testid="stExpander"]:hover {
    border-color: rgba(196,112,75,0.2) !important;
    box-shadow: 0 4px 16px rgba(26,23,20,0.06);
}

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #c4704b, #a85d3a) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Source Sans 3', sans-serif !important;
    letter-spacing: 0.3px;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(196,112,75,0.25);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #b5633f, #964f2e) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(196,112,75,0.35) !important;
}
.stButton > button:not([kind="primary"]) {
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
    border-color: #d5d0c8 !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #c4704b !important;
    color: #c4704b !important;
}

/* ── Form inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    border-radius: 10px !important;
    border-color: #ddd8d0 !important;
    font-family: 'Source Sans 3', sans-serif !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #c4704b !important;
    box-shadow: 0 0 0 1px rgba(196,112,75,0.2) !important;
}

/* ── Data tables ── */
div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(201,169,110,0.12);
}

/* ── Metrics ── */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.5);
    backdrop-filter: blur(8px);
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid rgba(201,169,110,0.1);
}
div[data-testid="stMetric"] label {
    color: #64605a !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-size: 0.7rem !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    color: #2c2825 !important;
}

/* ── Progress bars ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #c4704b, #7a9a7e) !important;
    border-radius: 10px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(255,255,255,0.4);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    transition: all 0.2s ease;
    font-weight: 500;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(196,112,75,0.08);
}
.stTabs [aria-selected="true"] {
    background: rgba(196,112,75,0.12) !important;
}

/* ── Dividers ── */
hr {
    border-color: rgba(201,169,110,0.15) !important;
}

/* ── Section titles ── */
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #2c2825 !important;
}

/* ── Login card ── */
.login-card {
    background: rgba(255,255,255,0.8);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(201,169,110,0.15);
    border-radius: 24px;
    padding: 3rem 2.5rem;
    box-shadow: 0 12px 48px rgba(26,23,20,0.08);
    margin-top: 2rem;
}
.login-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #2c2825;
    text-align: center;
    margin-bottom: 0.3rem;
    letter-spacing: -0.5px;
}
.login-subtitle {
    color: #8a857e;
    text-align: center;
    font-size: 0.9rem;
    font-weight: 400;
    margin-bottom: 2rem;
    letter-spacing: 0.5px;
}

.block-container { padding-top: 2rem; }
</style>
"""


def get_management_css():
    """Return CSS for the Management Portal — dark, luxe editorial theme."""
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Source+Sans+3:wght@300;400;500;600;700&display=swap');

/* ── Global ── */
.stApp {
    font-family: 'Source Sans 3', sans-serif;
    background: #f5f2ec;
    background-image:
        radial-gradient(ellipse at 10% 90%, rgba(196,112,75,0.05) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 10%, rgba(122,154,126,0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(201,169,110,0.03) 0%, transparent 70%),
        url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%232c2825' fill-opacity='0.015'%3E%3Cpath fill-rule='evenodd' d='M0 38.59l2.83-2.83 1.41 1.41L1.41 40H0v-1.41zM0 1.4l2.83 2.83 1.41-1.41L1.41 0H0v1.41zM38.59 40l-2.83-2.83 1.41-1.41L40 38.59V40h-1.41zM40 1.41l-2.83 2.83-1.41-1.41L38.59 0H40v1.41zM20 18.6l2.83-2.83 1.41 1.41L21.41 20l2.83 2.83-1.41 1.41L20 21.41l-2.83 2.83-1.41-1.41L18.59 20l-2.83-2.83 1.41-1.41L20 18.59z'/%3E%3C/g%3E%3C/svg%3E");
}

/* ── Sidebar – deep architectural dark ── */
div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1714 0%, #13110f 60%, #0d0c0a 100%) !important;
    border-right: 1px solid rgba(201,169,110,0.08);
    box-shadow: 4px 0 24px rgba(0,0,0,0.15);
}
div[data-testid="stSidebar"] * {
    color: #c8c0b4 !important;
}
div[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 10px;
    margin: 1px 0;
    padding: 6px 8px !important;
    border-left: 3px solid transparent;
}
div[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
    background: rgba(201,169,110,0.08) !important;
    border-left-color: rgba(196,112,75,0.4);
    padding-left: 12px !important;
    color: #faf6f0 !important;
}
div[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
    background: rgba(196,112,75,0.12) !important;
    border-left-color: #c4704b;
    color: #faf6f0 !important;
}

/* ── Header Banner ── */
.mgmt-header {
    background: linear-gradient(135deg, #1a1714 0%, #2c2825 30%, #3d3630 70%, #2c2825 100%);
    color: #faf6f0;
    padding: 2.2rem 2.5rem;
    border-radius: 20px;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(201,169,110,0.08);
    box-shadow: 0 12px 40px rgba(26,23,20,0.15);
}
.mgmt-header::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 40%;
    height: 100%;
    background: linear-gradient(135deg, transparent 0%, rgba(196,112,75,0.06) 50%, rgba(201,169,110,0.08) 100%);
}
.mgmt-header::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, #c4704b, #c9a96e, #7a9a7e);
}
.mgmt-header h1 {
    margin: 0;
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    position: relative;
    z-index: 1;
}
.mgmt-header p {
    margin: 0.4rem 0 0;
    opacity: 0.5;
    font-size: 0.82rem;
    font-weight: 300;
    letter-spacing: 1px;
    text-transform: uppercase;
    position: relative;
    z-index: 1;
}

/* ── Stat Cards – glass morphism ── */
.stat-card {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(201,169,110,0.1);
    border-radius: 18px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 16px rgba(26,23,20,0.04);
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba(196,112,75,0.3), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(26,23,20,0.1);
    border-color: rgba(196,112,75,0.2);
}
.stat-card:hover::before {
    opacity: 1;
}
.stat-card .label {
    font-size: 0.62rem;
    color: #8a857e;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-weight: 600;
}
.stat-card .value {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #2c2825;
    margin-top: 0.35rem;
    line-height: 1.2;
}

/* ── Containers & Expanders ── */
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(201,169,110,0.08) !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 8px rgba(26,23,20,0.03);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 10px;
}
div[data-testid="stExpander"]:hover {
    border-color: rgba(196,112,75,0.18) !important;
    box-shadow: 0 6px 20px rgba(26,23,20,0.06);
    background: rgba(255,255,255,0.7);
}

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2c2825, #3d3630) !important;
    color: #faf6f0 !important;
    border: 1px solid rgba(201,169,110,0.15) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-family: 'Source Sans 3', sans-serif !important;
    letter-spacing: 0.5px;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(26,23,20,0.15);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #3d3630, #4a3f37) !important;
    border-color: rgba(196,112,75,0.3) !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(26,23,20,0.2) !important;
}
.stButton > button:not([kind="primary"]) {
    border-radius: 10px !important;
    transition: all 0.25s ease !important;
    border-color: #d5d0c8 !important;
    font-family: 'Source Sans 3', sans-serif !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: #c4704b !important;
    color: #c4704b !important;
    background: rgba(196,112,75,0.04) !important;
}

/* ── Form inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    border-radius: 10px !important;
    border-color: #d5d0c8 !important;
    font-family: 'Source Sans 3', sans-serif !important;
    background: rgba(255,255,255,0.6) !important;
    transition: all 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #c4704b !important;
    box-shadow: 0 0 0 2px rgba(196,112,75,0.1) !important;
    background: rgba(255,255,255,0.9) !important;
}

/* ── Data tables ── */
div[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(201,169,110,0.1);
    box-shadow: 0 2px 12px rgba(26,23,20,0.03);
}

/* ── Metrics ── */
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.5);
    backdrop-filter: blur(10px);
    padding: 1.1rem;
    border-radius: 14px;
    border: 1px solid rgba(201,169,110,0.1);
    transition: all 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    background: rgba(255,255,255,0.7);
}
div[data-testid="stMetric"] label {
    color: #8a857e !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-size: 0.65rem !important;
    font-weight: 600 !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    color: #2c2825 !important;
}

/* ── Progress bars ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #c4704b, #c9a96e, #7a9a7e) !important;
    border-radius: 10px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: rgba(44,40,37,0.04);
    border-radius: 14px;
    padding: 5px;
    border: 1px solid rgba(201,169,110,0.08);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    font-weight: 500;
    font-family: 'Source Sans 3', sans-serif;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(196,112,75,0.06);
}
.stTabs [aria-selected="true"] {
    background: rgba(44,40,37,0.08) !important;
    font-weight: 600;
}

/* ── Dividers ── */
hr {
    border-color: rgba(201,169,110,0.12) !important;
}

/* ── Section titles ── */
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #2c2825 !important;
}
h3 {
    position: relative;
    padding-bottom: 0.5rem;
}

/* ── Login card ── */
.login-card {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(201,169,110,0.12);
    border-radius: 28px;
    padding: 3.5rem 3rem;
    box-shadow: 0 20px 60px rgba(26,23,20,0.1);
    margin-top: 2rem;
    position: relative;
    overflow: hidden;
}
.login-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #c4704b, #c9a96e, #7a9a7e);
}
.login-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #2c2825;
    text-align: center;
    margin-bottom: 0.3rem;
    letter-spacing: -1px;
}
.login-subtitle {
    color: #8a857e;
    text-align: center;
    font-size: 0.9rem;
    font-weight: 400;
    margin-bottom: 2.5rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

/* ── Charts ── */
div[data-testid="stVegaLiteChart"],
div[data-testid="stArrowVegaLiteChart"] {
    background: rgba(255,255,255,0.4);
    border-radius: 14px;
    padding: 12px;
    border: 1px solid rgba(201,169,110,0.08);
}

.block-container { padding-top: 2rem; }
</style>
"""
