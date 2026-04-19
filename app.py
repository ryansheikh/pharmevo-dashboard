import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
import warnings
import pyodbc
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Pharmevo BI Dashboard", page_icon="💊", layout="wide")

# ── FISCAL YEAR HELPER ───────────────────────────────────────
# FY2022 = Jul 1 2022 → Jun 30 2023
# FY2023 = Jul 1 2023 → Jun 30 2024
# FY2024 = Jul 1 2024 → Jun 30 2025
# FY2025 = Jul 1 2025 → present (partial, today Apr 20 2026)
def get_fy(date):
    """Returns fiscal year start (e.g. 2022 for Jul2022-Jun2023)"""
    if pd.isna(date): return None
    if date.month >= 7:
        return date.year
    else:
        return date.year - 1

FY_LABELS = {2022: "FY2022 (Jul22–Jun23)",
             2023: "FY2023 (Jul23–Jun24)",
             2024: "FY2024 (Jul24–Jun25)",
             2025: "FY2025 (Jul25–Apr26, partial)"}

CURRENT_FY = 2025
CURRENT_DATE = "Apr 20, 2026"

# ── PASSWORD PROTECTION ─────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.markdown("""
    <style>
    .login-box {
        max-width: 420px; margin: 80px auto; background: white;
        border-radius: 16px; padding: 40px;
        box-shadow: 0 8px 32px rgba(44,95,138,0.15); text-align: center;
    }
    .login-title { font-size: 28px; font-weight: 800; color: #2c5f8a; margin-bottom: 8px; }
    .login-sub   { font-size: 14px; color: #888; margin-bottom: 28px; }
    </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">💊 Pharmevo BI</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Business Intelligence Dashboard</div>', unsafe_allow_html=True)
        pw = st.text_input("Enter Password", type="password", placeholder="Password...")
        if st.button("Login →", use_container_width=True, type="primary"):
            if pw == "Pharmevo2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        st.markdown('</div>', unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()

# ── THEME ────────────────────────────────────────────────────
st.markdown("""
<style>
body, .main { background-color: #f5f7fa; }
.block-container { padding-top: 1.5rem; }
.kpi-card {
    background: white; border-radius: 12px; padding: 18px;
    text-align: center; margin: 4px;
    border-top: 4px solid #2c5f8a;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.kpi-value  { font-size: 24px; font-weight: 800; color: #2c5f8a; margin: 6px 0; }
.kpi-label  { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 1px; }
.kpi-delta  { font-size: 12px; color: #2e7d32; font-weight: 600; margin-top: 4px; }
.kpi-delta-red { font-size: 12px; color: #c62828; font-weight: 600; margin-top: 4px; }
.insight-box  { background: #e8f5e9; border-left: 5px solid #2e7d32; border-radius: 6px; padding: 12px 15px; margin: 6px 0; color: #1b1b1b; font-size: 13px; line-height: 1.6; }
.warning-box  { background: #fff3e0; border-left: 5px solid #e65100; border-radius: 6px; padding: 12px 15px; margin: 6px 0; color: #1b1b1b; font-size: 13px; line-height: 1.6; }
.danger-box   { background: #ffebee; border-left: 5px solid #c62828; border-radius: 6px; padding: 12px 15px; margin: 6px 0; color: #1b1b1b; font-size: 13px; line-height: 1.6; }
.chart-note   { background: #e3f2fd; border-left: 4px solid #1565c0; border-radius: 6px; padding: 8px 12px; margin: 4px 0 10px 0; color: #1b1b1b; font-size: 12px; }
.sec-header   { font-size: 17px; font-weight: 700; color: #2c5f8a; border-bottom: 2px solid #2c5f8a; padding-bottom: 5px; margin: 18px 0 10px 0; }
.manual-working { background: #fafafa; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; font-family: monospace; font-size: 13px; color: #333; white-space: pre-wrap; }
.fy-badge { background: #2c5f8a; color: white; border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── DATA LOADING ─────────────────────────────────────────────
@st.cache_data(ttl=86400)
def load_data():
    """Load all data from CSVs with fiscal year columns added"""

    # ── SECONDARY SALES ──
    try:
        ds = pd.read_csv("sales_clean.csv", low_memory=False)
    except:
        ds = pd.DataFrame(columns=['Date','Yr','Mo','TeamName','ProductName','SaleFlag',
                                   'DistributorName','BrickName','TotalRevenue','TotalUnits',
                                   'TotalDiscount','TotalBonus','InvoiceCount'])

    ds['Date'] = pd.to_datetime(ds.get('Date', pd.Series(dtype='object')), errors='coerce')
    if 'Yr' not in ds.columns and 'Date' in ds.columns:
        ds['Yr'] = ds['Date'].dt.year
        ds['Mo'] = ds['Date'].dt.month
    for col in ['TotalRevenue','TotalUnits','TotalDiscount','InvoiceCount']:
        if col in ds.columns:
            ds[col] = pd.to_numeric(ds[col], errors='coerce').fillna(0)

    # Add fiscal year
    if 'Date' in ds.columns and ds['Date'].notna().any():
        ds['FY'] = ds['Date'].apply(lambda d: get_fy(d) if pd.notna(d) else None)
    else:
        # Fallback: calendar year-based FY (assumes data before Jul = prev FY)
        ds['FY'] = ds.apply(lambda r: r['Yr'] if r['Mo'] >= 7 else r['Yr'] - 1, axis=1)

    # ── ACTIVITIES ──
    try:
        da = pd.read_csv("activities_clean.csv", low_memory=False)
    except:
        da = pd.DataFrame(columns=['Date','Yr','Mo','RequestorTeams','Product',
                                   'ActivityHead','GLHead','TotalAmount','RequestCount'])

    da['Date'] = pd.to_datetime(da.get('Date', pd.Series(dtype='object')), errors='coerce')
    for col in ['TotalAmount']:
        if col in da.columns:
            da[col] = pd.to_numeric(da[col], errors='coerce').fillna(0)
    if 'Date' in da.columns and da['Date'].notna().any():
        da['FY'] = da['Date'].apply(lambda d: get_fy(d) if pd.notna(d) else None)
    elif 'Yr' in da.columns and 'Mo' in da.columns:
        da['FY'] = da.apply(lambda r: r['Yr'] if r['Mo'] >= 7 else r['Yr'] - 1, axis=1)

    # ── TRAVEL ──
    try:
        dt = pd.read_csv("travel_clean.csv", low_memory=False)
    except:
        dt = pd.DataFrame(columns=['FlightDate','Yr','Mo','Traveller','TravellerTeam',
                                   'TravellerDivision','VisitLocation','HotelName',
                                   'TravelCount','NoofNights'])

    dt['FlightDate'] = pd.to_datetime(dt.get('FlightDate', pd.Series(dtype='object')), errors='coerce')
    for col in ['TravelCount','NoofNights']:
        if col in dt.columns:
            dt[col] = pd.to_numeric(dt[col], errors='coerce').fillna(0)
    if 'FlightDate' in dt.columns and dt['FlightDate'].notna().any():
        dt['FY'] = dt['FlightDate'].apply(lambda d: get_fy(d) if pd.notna(d) else None)
    elif 'Yr' in dt.columns and 'Mo' in dt.columns:
        dt['FY'] = dt.apply(lambda r: r['Yr'] if r['Mo'] >= 7 else r['Yr'] - 1, axis=1)

    # ── ROI ──
    try:
        dr = pd.read_csv("ml_roi_products.csv")
    except:
        rv_p = ds.groupby("ProductName")["TotalRevenue"].sum()
        sp_p = da.groupby("Product")["TotalAmount"].sum()
        dr = pd.DataFrame({"TotalRevenue": rv_p, "TotalPromoSpend": sp_p}).dropna().reset_index()
        dr.columns = ["ProductName", "TotalRevenue", "TotalPromoSpend"]
        dr = dr[dr["TotalPromoSpend"] > 0]
        dr["ROI"] = dr["TotalRevenue"] / dr["TotalPromoSpend"]

    kpis = {
        "rev_fy22": float(ds[ds["FY"]==2022]["TotalRevenue"].sum()) if "FY" in ds.columns else 0,
        "rev_fy23": float(ds[ds["FY"]==2023]["TotalRevenue"].sum()) if "FY" in ds.columns else 0,
        "rev_fy24": float(ds[ds["FY"]==2024]["TotalRevenue"].sum()) if "FY" in ds.columns else 0,
        "rev_fy25": float(ds[ds["FY"]==2025]["TotalRevenue"].sum()) if "FY" in ds.columns else 0,
        "sp_fy24":  float(da[da["FY"]==2024]["TotalAmount"].sum()) if "FY" in da.columns else 0,
        "sp_fy25":  float(da[da["FY"]==2025]["TotalAmount"].sum()) if "FY" in da.columns else 0,
    }
    return ds, da, dr, dt, kpis


@st.cache_data(ttl=86400)
def load_zsdcy():
    """Load primary sales (ZSDCY) from aggregated CSV"""
    try:
        df = pd.read_csv("zsdcy_agg.csv", low_memory=False)
        df['Date'] = pd.to_datetime(
            df['Yr'].astype(str) + '-' + df['Mo'].astype(str).str.zfill(2) + '-01',
            errors='coerce')
        for col in ['Revenue','Qty']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if 'FY' not in df.columns:
            df['FY'] = df.apply(lambda r: r['Yr'] if r['Mo'] >= 7 else r['Yr'] - 1, axis=1)
        return df
    except Exception as e:
        # Build from scratch if files exist
        try:
            df = pd.read_csv("zsdcy_clean.csv", low_memory=False)
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            for col in ['Revenue','Qty']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            if 'FY' not in df.columns:
                df['FY'] = df['Date'].apply(lambda d: get_fy(d) if pd.notna(d) else None)
            return df
        except:
            return pd.DataFrame(columns=['Date','Yr','Mo','FY','Material Name',
                                         'SDP Name','City','Revenue','Qty','Category'])

df_sales, df_act, df_roi, df_travel, kpis = load_data()
df_zsdcy = load_zsdcy()

# ── FY FILTER LISTS ──────────────────────────────────────────
available_fys = sorted([fy for fy in [2022,2023,2024,2025]
                        if len(df_sales[df_sales['FY']==fy]) > 0]) if 'FY' in df_sales.columns else [2022,2023,2024,2025]

months_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

# ── HELPERS ──────────────────────────────────────────────────
def fmt(val):
    if val >= 1e9:   return f"PKR {val/1e9:.1f}B"
    elif val >= 1e6: return f"PKR {val/1e6:.1f}M"
    elif val >= 1e3: return f"PKR {val/1e3:.1f}K"
    else:            return f"PKR {val:.0f}"

def fmt_num(val):
    if val >= 1e9:   return f"{val/1e9:.1f}B"
    elif val >= 1e6: return f"{val/1e6:.1f}M"
    elif val >= 1e3: return f"{val/1e3:.1f}K"
    else:            return f"{val:.0f}"

LAYOUT = dict(plot_bgcolor="white", paper_bgcolor="white",
              font=dict(color="#333333", size=12),
              xaxis=dict(gridcolor="#eeeeee", showgrid=True, linecolor="#cccccc"),
              yaxis=dict(gridcolor="#eeeeee", showgrid=True, linecolor="#cccccc"),
              margin=dict(t=30, b=40, l=10, r=10))

def apply_layout(fig, height=350, **kwargs):
    layout = dict(LAYOUT); layout["height"] = height; layout.update(kwargs)
    fig.update_layout(**layout); return fig

def kpi(label, value, delta, red=False):
    dc = "kpi-delta-red" if red else "kpi-delta"
    return f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="{dc}">{delta}</div></div>'

def note(t):   return f"<div class='chart-note'>💡 {t}</div>"
def good(t):   return f"<div class='insight-box'>✅ {t}</div>"
def warn(t):   return f"<div class='warning-box'>⚠️ {t}</div>"
def danger(t): return f"<div class='danger-box'>🚨 {t}</div>"
def sec(t):    return f"<div class='sec-header'>{t}</div>"

def fy_str(fy):
    return FY_LABELS.get(fy, f"FY{fy}")

# ── SIDEBAR ───────────────────────────────────────────────────
st.sidebar.title("💊 Pharmevo BI")
st.sidebar.markdown(f"**Last Updated:** {CURRENT_DATE}")
st.sidebar.markdown("---")
st.sidebar.markdown("**📅 Fiscal Year System**")
st.sidebar.markdown("FY2022 = Jul 2022 – Jun 2023")
st.sidebar.markdown("FY2023 = Jul 2023 – Jun 2024")
st.sidebar.markdown("FY2024 = Jul 2024 – Jun 2025")
st.sidebar.markdown("FY2025 = Jul 2025 – Apr 2026 *(partial)*")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate to", [
    "🏠 Executive Summary",
    "📈 Sales Analysis",
    "💰 Promotional Analysis",
    "✈️ Travel Analysis",
    "📦 Distribution Analysis",
    "🔬 Strategic Intelligence Hub",
    "🤖 ML Intelligence",
    "📌 Personal Dashboard",
    "👔 Management View"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")
fy_filter = st.sidebar.multiselect(
    "Fiscal Year(s)",
    options=available_fys,
    default=available_fys,
    format_func=lambda x: FY_LABELS.get(x, f"FY{x}")
)
team_filter = st.sidebar.multiselect("Team(s)",
    options=sorted(df_sales["TeamName"].unique()) if "TeamName" in df_sales.columns else [],
    default=[])

# Apply filters
df_s = df_sales[df_sales["FY"].isin(fy_filter)] if "FY" in df_sales.columns else df_sales
df_a = df_act[df_act["FY"].isin(fy_filter)] if "FY" in df_act.columns else df_act
df_t = df_travel[df_travel["FY"].isin(fy_filter)] if "FY" in df_travel.columns else df_travel
df_z = df_zsdcy[df_zsdcy["FY"].isin(fy_filter)] if "FY" in df_zsdcy.columns else df_zsdcy

if team_filter:
    df_s = df_s[df_s["TeamName"].isin(team_filter)] if "TeamName" in df_s.columns else df_s
    df_a = df_a[df_a["RequestorTeams"].str.upper().isin([t.upper() for t in team_filter])] if "RequestorTeams" in df_a.columns else df_a

# ─────────────────────────────────────────────────────────────
# PRE-COMPUTE KEY METRICS (fiscal year based)
# ─────────────────────────────────────────────────────────────
def fy_rev(fy):
    return float(df_sales[df_sales["FY"]==fy]["TotalRevenue"].sum()) if "FY" in df_sales.columns else 0

def fy_spend(fy):
    return float(df_act[df_act["FY"]==fy]["TotalAmount"].sum()) if "FY" in df_act.columns else 0

def fy_trips(fy):
    return float(df_travel[df_travel["FY"]==fy]["TravelCount"].sum()) if "FY" in df_travel.columns else 0

def fy_zrev(fy):
    return float(df_zsdcy[df_zsdcy["FY"]==fy]["Revenue"].sum()) if "FY" in df_zsdcy.columns and len(df_zsdcy) > 0 else 0

rv22 = fy_rev(2022); rv23 = fy_rev(2023); rv24 = fy_rev(2024); rv25 = fy_rev(2025)
sp22 = fy_spend(2022); sp23 = fy_spend(2023); sp24 = fy_spend(2024); sp25 = fy_spend(2025)
tr22 = fy_trips(2022); tr23 = fy_trips(2023); tr24 = fy_trips(2024); tr25 = fy_trips(2025)
zr22 = fy_zrev(2022); zr23 = fy_zrev(2023); zr24 = fy_zrev(2024); zr25 = fy_zrev(2025)

roi24 = rv24/sp24 if sp24>0 else 0
roi25 = rv25/sp25 if sp25>0 else 0
yoy_rev = (rv24-rv23)/rv23*100 if rv23>0 else 0  # FY23→FY24 growth (latest complete pair)

# ════════════════════════════════════════════════════════════
# PAGE 1: EXECUTIVE SUMMARY
# ════════════════════════════════════════════════════════════
if page == "🏠 Executive Summary":
    st.markdown("<h1 style='color:#2c5f8a'>💊 Pharmevo Business Intelligence Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#666'>4 Databases | Fiscal Year System (Jul–Jun) | FY2022–FY2025 | Updated {CURRENT_DATE}</p>", unsafe_allow_html=True)
    st.markdown(note("📅 <b>Fiscal Year Definition:</b> FY2022 = Jul 2022–Jun 2023 | FY2023 = Jul 2023–Jun 2024 | FY2024 = Jul 2024–Jun 2025 | FY2025 = Jul 2025–Apr 2026 (partial, 10 months)"), unsafe_allow_html=True)
    st.markdown("---")

    rev_all = df_s["TotalRevenue"].sum() if "TotalRevenue" in df_s.columns else 0
    units_all = df_s["TotalUnits"].sum() if "TotalUnits" in df_s.columns else 0
    spend_all = df_a["TotalAmount"].sum() if "TotalAmount" in df_a.columns else 0
    roi_all = rev_all/spend_all if spend_all > 0 else 0
    trips_all = df_t["TravelCount"].sum() if "TravelCount" in df_t.columns else 0

    st.markdown("### 📊 Fiscal Year Performance Overview")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("FY2022 Revenue", fmt(rv22), "Jul 2022 – Jun 2023"), unsafe_allow_html=True)
    c2.markdown(kpi("FY2023 Revenue", fmt(rv23), f"{'↑ +' if rv23>rv22 else '↓ '}{abs((rv23-rv22)/rv22*100):.1f}% vs FY2022" if rv22>0 else "Jul 2023 – Jun 2024"), unsafe_allow_html=True)
    c3.markdown(kpi("FY2024 Revenue", fmt(rv24), f"{'↑ +' if rv24>rv23 else '↓ '}{abs((rv24-rv23)/rv23*100):.1f}% vs FY2023" if rv23>0 else "Jul 2024 – Jun 2025"), unsafe_allow_html=True)
    c4.markdown(kpi("FY2025 Revenue", fmt(rv25), "Jul 2025 – Apr 2026 (10 months partial)", red=True), unsafe_allow_html=True)
    c5.markdown(kpi("All FY Total", fmt(rev_all), "FY2022 + FY2023 + FY2024 + FY2025"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**💰 Promotional Investment & ROI**")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Promo Spend FY2024", fmt(sp24), "Jul 2024 – Jun 2025"), unsafe_allow_html=True)
    c2.markdown(kpi("Promo Spend FY2025", fmt(sp25), f"+{(sp25-sp24)/sp24*100:.1f}% vs FY2024" if sp24>0 else "partial year", red=True), unsafe_allow_html=True)
    c3.markdown(kpi("ROI FY2024", f"{roi24:.1f}x", "Revenue per PKR 1 spent"), unsafe_allow_html=True)
    c4.markdown(kpi("ROI FY2025", f"{roi25:.1f}x", "⚠️ Declining trend" if roi25 < roi24 else "↑ Improving", red=roi25<roi24), unsafe_allow_html=True)
    c5.markdown(kpi("Total Trips", fmt_num(trips_all), "All field visits FY22–FY25"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # Company records
    if "ProductName" in df_s.columns and len(df_s) > 0:
        top_prod = df_s.groupby("ProductName")["TotalRevenue"].sum().idxmax()
        top_prod_rev = df_s.groupby("ProductName")["TotalRevenue"].sum().max()
        top_team = df_s.groupby("TeamName")["TotalRevenue"].sum().idxmax() if "TeamName" in df_s.columns else "N/A"
        top_team_rev = df_s.groupby("TeamName")["TotalRevenue"].sum().max() if "TeamName" in df_s.columns else 0
        st.markdown("**🏆 Company Records**")
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.markdown(kpi("Top Product", top_prod, fmt(top_prod_rev)+" revenue"), unsafe_allow_html=True)
        c2.markdown(kpi("Top Sales Team", top_team, fmt(top_team_rev)+" revenue"), unsafe_allow_html=True)
        c3.markdown(kpi("Best ROI Product", "Xcept", "High ROI from live SQL"), unsafe_allow_html=True)
        c4.markdown(kpi("Primary Sales FY2024", fmt(zr24), "ZSDCY (factory→distributor)"), unsafe_allow_html=True)
        c5.markdown(kpi("Primary Sales FY2025", fmt(zr25), "Jul 2025 – present, partial"), unsafe_allow_html=True)

    st.markdown("---")

    # Revenue trend by FY (monthly)
    st.markdown(sec("📈 Monthly Revenue Trend — Fiscal Year View"), unsafe_allow_html=True)
    st.markdown(note("Each line = one fiscal year. FY2025 (orange dashed) is partial — Jul 2025 to Apr 2026 only."), unsafe_allow_html=True)

    if "Date" in df_s.columns and "TotalRevenue" in df_s.columns:
        monthly = df_s.groupby(["FY","Date"])["TotalRevenue"].sum().reset_index()
        fig = go.Figure()
        colors = {2022:"#2c5f8a", 2023:"#2e7d32", 2024:"#7b1fa2", 2025:"#e65100"}
        for fy in sorted(monthly["FY"].unique()):
            d = monthly[monthly["FY"]==fy].sort_values("Date")
            dash = "dash" if fy == CURRENT_FY else "solid"
            fig.add_trace(go.Scatter(
                x=d["Date"], y=d["TotalRevenue"]/1e6,
                name=FY_LABELS.get(fy, f"FY{fy}"),
                line=dict(color=colors.get(fy,"#888"), width=2.5, dash=dash),
                mode="lines+markers", marker=dict(size=5),
                hovertemplate=f"FY{fy} %{{x|%b %Y}}: PKR %{{y:.1f}}M<extra></extra>"))
        apply_layout(fig, height=320, hovermode="x unified",
            yaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"),
            legend=dict(bgcolor="white", bordercolor="#ddd", borderwidth=1))
        fig.update_layout(title="Monthly Revenue by Fiscal Year (FY2025 orange dashed = partial)")
        st.plotly_chart(fig, use_container_width=True)

    # Year-over-year bar
    st.markdown(sec("📊 Fiscal Year Comparison — Revenue"), unsafe_allow_html=True)
    fy_data = pd.DataFrame({
        "FY": [f"FY{y}" for y in [2022,2023,2024,2025]],
        "Revenue": [rv22, rv23, rv24, rv25],
        "Label": [fmt(rv22), fmt(rv23), fmt(rv24), fmt(rv25)+"*"],
        "Note": ["Jul22–Jun23","Jul23–Jun24","Jul24–Jun25","Jul25–Apr26 (partial)"]
    })
    fy_data = fy_data[fy_data["Revenue"] > 0]
    colors_bar = ["#2c5f8a","#2e7d32","#7b1fa2","#e65100"][:len(fy_data)]
    fig = go.Figure(go.Bar(
        x=fy_data["FY"], y=fy_data["Revenue"]/1e9,
        text=fy_data["Label"], textposition="outside", textfont_size=12,
        marker_color=colors_bar,
        customdata=fy_data["Note"],
        hovertemplate="%{x}: PKR %{y:.3f}B<br>%{customdata}<extra></extra>"))
    apply_layout(fig, height=320,
        xaxis=dict(gridcolor="#eeeeee"),
        yaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR Billions)"))
    fig.update_layout(title="Revenue by Fiscal Year (* FY2025 is partial — 10 months only)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(warn("FY2025 marked with * is partial (Jul 2025 – Apr 2026 = 10 months). Direct comparison with complete fiscal years should account for this."), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 2: SALES ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "📈 Sales Analysis":
    st.markdown("<h2 style='color:#2c5f8a'>📈 Sales Deep Analysis — Fiscal Year View</h2>", unsafe_allow_html=True)
    st.markdown(note("📅 FY2022 = Jul22–Jun23 | FY2023 = Jul23–Jun24 | FY2024 = Jul24–Jun25 | FY2025 = Jul25–Apr26 (partial)"), unsafe_allow_html=True)

    # FY comparison KPIs
    st.markdown("### Fiscal Year Revenue Comparison")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("FY2022", fmt(rv22), "Jul 2022 – Jun 2023"), unsafe_allow_html=True)
    c2.markdown(kpi("FY2023", fmt(rv23), f"+{(rv23-rv22)/rv22*100:.1f}% vs FY2022" if rv22>0 else "—"), unsafe_allow_html=True)
    c3.markdown(kpi("FY2024", fmt(rv24), f"+{(rv24-rv23)/rv23*100:.1f}% vs FY2023" if rv23>0 else "—"), unsafe_allow_html=True)
    c4.markdown(kpi("FY2025 (partial)", fmt(rv25), "Jul 2025 – Apr 2026 only", red=True), unsafe_allow_html=True)

    st.markdown("---")

    # FY comparison bar chart
    if "FY" in df_s.columns and "TotalRevenue" in df_s.columns:
        st.markdown(sec("Year-over-Year (FY): Revenue, Units, Invoices"), unsafe_allow_html=True)

        fy_agg = df_s[df_s["FY"].isin([2022,2023,2024,2025])].groupby("FY").agg(
            Revenue=("TotalRevenue","sum"),
            Units=("TotalUnits","sum") if "TotalUnits" in df_s.columns else ("TotalRevenue","count"),
            Invoices=("InvoiceCount","sum") if "InvoiceCount" in df_s.columns else ("TotalRevenue","count")
        ).reset_index()
        fy_agg["FY_Label"] = fy_agg["FY"].apply(lambda x: f"FY{x}")
        fy_agg["RevLabel"] = fy_agg["Revenue"].apply(fmt)

        c1,c2,c3 = st.columns(3)
        for col, field, lbl, title, color in zip(
            [c1,c2,c3], ["Revenue","Units","Invoices"],
            ["RevLabel","Units","Invoices"],
            ["Revenue (PKR)","Units Sold","Invoice Count"],
            ["#2c5f8a","#2e7d32","#e65100"]):
            with col:
                fig = px.bar(fy_agg, x="FY_Label", y=field,
                    text=fy_agg[field].apply(lambda x: fmt(x) if field=="Revenue" else fmt_num(x)),
                    title=title, color_discrete_sequence=[color])
                fig.update_traces(textposition="outside", textfont_size=11)
                apply_layout(fig, height=280, xaxis=dict(gridcolor="#eeeeee"),
                             yaxis=dict(gridcolor="#eeeeee"))
                st.plotly_chart(fig, use_container_width=True)

    # Product performance FY23 vs FY24 (latest complete pair)
    st.markdown(sec("Product Revenue: FY2023 vs FY2024 (Latest Complete Years)"), unsafe_allow_html=True)
    st.markdown(note("Comparing two complete fiscal years. Blue = FY2023 (Jul23–Jun24). Green = FY2024 (Jul24–Jun25). Taller green bar = product grew."), unsafe_allow_html=True)

    if "FY" in df_s.columns and "ProductName" in df_s.columns:
        ry = df_s[df_s["FY"].isin([2023,2024])].groupby(["ProductName","FY"])["TotalRevenue"].sum().reset_index()
        top15 = ry.groupby("ProductName")["TotalRevenue"].sum().nlargest(15).index
        ry = ry[ry["ProductName"].isin(top15)]
        ry["Label"] = ry["TotalRevenue"].apply(fmt)
        ry["FY_str"] = ry["FY"].apply(lambda x: f"FY{x}")
        fig = px.bar(ry, x="ProductName", y="TotalRevenue", color="FY_str", barmode="group",
                     text="Label", color_discrete_map={"FY2023":"#2c5f8a","FY2024":"#2e7d32"})
        fig.update_traces(textposition="outside", textfont_size=8, textangle=-45)
        apply_layout(fig, height=480, xaxis=dict(gridcolor="#eeeeee", tickangle=-35),
                     yaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    # Explorer
    st.markdown("---")
    st.markdown(sec("🔍 Product Explorer"), unsafe_allow_html=True)
    col_sf1, col_sf2, col_sf3 = st.columns(3)
    with col_sf1:
        n_prods_s = st.slider("Products to show", 5, 100, 20, key="sales_n")
    with col_sf2:
        sort_s = st.selectbox("Sort", ["Top (Highest First)", "Bottom (Lowest First)"], key="sales_sort")
    with col_sf3:
        fy_s = st.selectbox("Fiscal Year", ["All FYs","FY2022","FY2023","FY2024","FY2025 (partial)"], key="sales_fy")

    asc_s = (sort_s == "Bottom (Lowest First)")
    df_yr_s = df_s.copy()
    if fy_s == "FY2022": df_yr_s = df_s[df_s["FY"]==2022]
    elif fy_s == "FY2023": df_yr_s = df_s[df_s["FY"]==2023]
    elif fy_s == "FY2024": df_yr_s = df_s[df_s["FY"]==2024]
    elif fy_s == "FY2025 (partial)": df_yr_s = df_s[df_s["FY"]==2025]

    if "ProductName" in df_yr_s.columns:
        prod_all_s = df_yr_s.groupby("ProductName")["TotalRevenue"].sum().reset_index()
        prod_all_s = prod_all_s[prod_all_s["TotalRevenue"]>0].sort_values("TotalRevenue", ascending=asc_s).head(n_prods_s)
        prod_all_s["Label"] = prod_all_s["TotalRevenue"].apply(fmt)
        cs = "Reds_r" if asc_s else "Blues"
        fig_s = px.bar(prod_all_s, x="TotalRevenue", y="ProductName", orientation="h", text="Label",
                       color="TotalRevenue", color_continuous_scale=cs,
                       title=f"{'Bottom' if asc_s else 'Top'} {n_prods_s} Products — {fy_s}")
        fig_s.update_traces(textposition="outside", textfont_size=9)
        h_s = max(400, n_prods_s * 28)
        apply_layout(fig_s, height=h_s, yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"), coloraxis_showscale=False)
        st.plotly_chart(fig_s, use_container_width=True)

    # Fastest growing FY23 → FY24
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("🚀 Fastest Growing Products FY2023→FY2024"), unsafe_allow_html=True)
        st.markdown(note("Based on complete fiscal years. FY2023 = Jul23–Jun24. FY2024 = Jul24–Jun25."), unsafe_allow_html=True)
        if "FY" in df_s.columns and "ProductName" in df_s.columns:
            r23 = df_s[df_s["FY"]==2023].groupby("ProductName")["TotalRevenue"].sum()
            r24 = df_s[df_s["FY"]==2024].groupby("ProductName")["TotalRevenue"].sum()
            gdf = pd.DataFrame({"fy23":r23,"fy24":r24}).dropna()
            gdf = gdf[gdf["fy23"]>5000000]
            gdf["Growth"] = (gdf["fy24"]-gdf["fy23"])/gdf["fy23"]*100
            gdf = gdf.sort_values("Growth", ascending=False).head(15).reset_index()
            gdf["Label"] = gdf["Growth"].apply(lambda x: f"+{x:.0f}%")
            fig = px.bar(gdf, x="Growth", y="ProductName", orientation="h", text="Label",
                         color="Growth", color_continuous_scale="Greens")
            fig.update_traces(textposition="outside", textfont_size=10)
            apply_layout(fig, height=500, yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee", title="Growth %"), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("📅 Revenue Seasonality Heatmap (by FY)"), unsafe_allow_html=True)
        st.markdown(note("Each cell = revenue in that month. Darker = higher. Shows seasonal patterns within each fiscal year."), unsafe_allow_html=True)
        if "FY" in df_s.columns and "Mo" in df_s.columns:
            heat = df_s[df_s["FY"].isin([2022,2023,2024])].groupby(["FY","Mo"])["TotalRevenue"].sum().reset_index()
            heat["Month"] = heat["Mo"].map(months_map)
            heat["FY_str"] = heat["FY"].apply(lambda x: f"FY{x}")
            hp = heat.pivot(index="FY_str", columns="Month", values="TotalRevenue")
            # Order months Jul→Jun for fiscal year
            fy_month_order = ["Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun"]
            hp = hp.reindex(columns=[m for m in fy_month_order if m in hp.columns])
            text_labels = []
            for idx in hp.index:
                row_labels = []
                for col in hp.columns:
                    val = hp.loc[idx, col]
                    row_labels.append("" if pd.isna(val) else (f"{val/1e9:.1f}B" if val>=1e9 else f"{val/1e6:.0f}M"))
                text_labels.append(row_labels)
            fig = px.imshow(hp/1e6, color_continuous_scale="Blues", aspect="auto",
                            labels=dict(color="Revenue (M PKR)"))
            fig.update_traces(text=text_labels, texttemplate="%{text}", textfont=dict(size=10, color="black"))
            apply_layout(fig, height=280, coloraxis_colorbar=dict(title="M PKR"))
            fig.update_layout(title="Revenue Heatmap — Jul→Jun fiscal month order")
            st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# PAGE 3: PROMOTIONAL ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "💰 Promotional Analysis":
    st.markdown("<h2 style='color:#2c5f8a'>💰 Promotional Spend Analysis — Fiscal Year View</h2>", unsafe_allow_html=True)
    st.markdown(note("📅 FY2024 = Jul 2024–Jun 2025 | FY2025 = Jul 2025–Apr 2026 (partial). Activities from FTTS SQL Server."), unsafe_allow_html=True)

    df_af = df_a[df_a["FY"].isin([2022,2023,2024,2025])] if "FY" in df_a.columns else df_a

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Promo Spend FY2024", fmt(sp24))
    c2.metric("Promo Spend FY2025", fmt(sp25), delta="partial year")
    c3.metric("ROI FY2024", f"{roi24:.1f}x", delta="Baseline")
    c4.metric("ROI FY2025", f"{roi25:.1f}x", delta=f"{roi25-roi24:.1f}x vs FY2024")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Promotional Spend by Fiscal Year"), unsafe_allow_html=True)
        if "FY" in df_af.columns and "TotalAmount" in df_af.columns:
            ysp = df_af.groupby("FY")["TotalAmount"].sum().reset_index()
            ysp["FY_str"] = ysp["FY"].apply(lambda x: f"FY{x}")
            ysp["Label"] = ysp["TotalAmount"].apply(fmt)
            ysp["Note"] = ysp["FY"].apply(lambda x: "partial" if x==2025 else "complete")
            colors_fy = ["#e65100" if n=="partial" else "#2c5f8a" for n in ysp["Note"]]
            fig = go.Figure(go.Bar(x=ysp["FY_str"], y=ysp["TotalAmount"]/1e6,
                text=ysp["Label"], textposition="outside", textfont_size=11,
                marker_color=colors_fy))
            apply_layout(fig, height=300, xaxis=dict(gridcolor="#eeeeee"),
                         yaxis=dict(gridcolor="#eeeeee", title="Total Spend (PKR M)"))
            fig.update_layout(title="Promo Spend by FY (Orange = partial FY2025)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("Activity Type Breakdown"), unsafe_allow_html=True)
        if "ActivityHead" in df_af.columns:
            asp = df_af.groupby("ActivityHead")["TotalAmount"].sum().nlargest(8).reset_index()
            fig = px.pie(asp, values="TotalAmount", names="ActivityHead",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textinfo="percent+label", textfont_size=10)
            apply_layout(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)

    # Explorer
    st.markdown("---")
    st.markdown(sec("🔍 Promo Explorer"), unsafe_allow_html=True)
    col_pf1, col_pf2, col_pf3 = st.columns(3)
    with col_pf1:
        n_promo = st.slider("Items", 5, 50, 10, key="promo_n")
    with col_pf2:
        sort_promo = st.selectbox("Sort", ["Top","Bottom"], key="promo_sort")
    with col_pf3:
        promo_view = st.selectbox("View by", ["Teams","Products"], key="promo_view")

    asc_promo = (sort_promo == "Bottom")
    if "RequestorTeams" in df_af.columns and promo_view == "Teams":
        pdata = df_af.groupby("RequestorTeams")["TotalAmount"].sum().reset_index()
        pdata.columns = ["Name","TotalAmount"]
    elif "Product" in df_af.columns:
        pdata = df_af.groupby("Product")["TotalAmount"].sum().reset_index()
        pdata.columns = ["Name","TotalAmount"]
    else:
        pdata = pd.DataFrame(columns=["Name","TotalAmount"])

    if len(pdata) > 0:
        pdata = pdata.sort_values("TotalAmount", ascending=asc_promo).head(n_promo)
        pdata["Label"] = pdata["TotalAmount"].apply(fmt)
        cs_p = "Reds_r" if asc_promo else "Blues"
        fig = px.bar(pdata, x="TotalAmount", y="Name", orientation="h", text="Label",
                     color="TotalAmount", color_continuous_scale=cs_p,
                     title=f"{'Bottom' if asc_promo else 'Top'} {n_promo} {promo_view}")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=max(350, n_promo*28), yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee"), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# PAGE 4: TRAVEL ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "✈️ Travel Analysis":
    st.markdown("<h2 style='color:#2c5f8a'>✈️ Travel & Field Activity — Fiscal Year View</h2>", unsafe_allow_html=True)
    st.markdown(note("📅 FY2022 = Jul22–Jun23 | FY2023 = Jul23–Jun24 | FY2024 = Jul24–Jun25 | FY2025 = Jul25–Apr26 (partial)"), unsafe_allow_html=True)

    t_all = df_t["TravelCount"].sum() if "TravelCount" in df_t.columns else 0
    n_all = df_t["NoofNights"].sum() if "NoofNights" in df_t.columns else 0
    p_all = df_t["Traveller"].nunique() if "Traveller" in df_t.columns else 0
    l_all = df_t["VisitLocation"].nunique() if "VisitLocation" in df_t.columns else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Trips (all FYs)", fmt_num(t_all))
    c2.metric("Total Nights", fmt_num(n_all))
    c3.metric("Unique Travellers", str(p_all))
    c4.metric("Cities Covered", str(l_all))
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Travel Trips by Fiscal Year"), unsafe_allow_html=True)
        if "FY" in df_t.columns and "TravelCount" in df_t.columns:
            yt = df_t.groupby("FY")["TravelCount"].sum().reset_index()
            yt["FY_str"] = yt["FY"].apply(lambda x: f"FY{x}")
            yt["Label"] = yt["TravelCount"].apply(fmt_num)
            yt["Partial"] = yt["FY"].apply(lambda x: x==2025)
            colors_t = ["#e65100" if p else "#2c5f8a" for p in yt["Partial"]]
            fig = go.Figure(go.Bar(x=yt["FY_str"], y=yt["TravelCount"],
                text=yt["Label"], textposition="outside", textfont_size=12,
                marker_color=colors_t))
            apply_layout(fig, height=290, xaxis=dict(gridcolor="#eeeeee"),
                         yaxis=dict(gridcolor="#eeeeee", title="Total Trips"))
            fig.update_layout(title="Field Trips by Fiscal Year (Orange = partial)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("Top 15 Most Visited Cities"), unsafe_allow_html=True)
        if "VisitLocation" in df_t.columns:
            lc = df_t.groupby("VisitLocation")["TravelCount"].sum().nlargest(15).reset_index()
            lc["Label"] = lc["TravelCount"].apply(fmt_num)
            fig = px.bar(lc, x="TravelCount", y="VisitLocation", orientation="h", text="Label",
                         color="TravelCount", color_continuous_scale="Blues")
            fig.update_traces(textposition="outside", textfont_size=10)
            apply_layout(fig, height=450, yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee"), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Division Activity — Trips per Person"), unsafe_allow_html=True)
        if "TravellerDivision" in df_t.columns:
            dv = df_t.groupby("TravellerDivision").agg(
                Trips=("TravelCount","sum"), People=("Traveller","nunique")).reset_index()
            dv["TpP"] = (dv["Trips"]/dv["People"]).round(1)
            dv = dv.sort_values("TpP", ascending=False)
            colors_dv = ["#c62828" if t<30 else "#e65100" if t<50 else "#2c5f8a" for t in dv["TpP"]]
            fig = go.Figure(go.Bar(x=dv["TpP"], y=dv["TravellerDivision"], orientation="h",
                text=dv["TpP"].apply(lambda x: f"{x:.0f} trips/person"),
                textposition="outside", textfont_size=10, marker_color=colors_dv))
            apply_layout(fig, height=320, yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee", title="Trips per Person"))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("Travel Seasonality (Month within FY)"), unsafe_allow_html=True)
        if "Mo" in df_t.columns and "TravelCount" in df_t.columns:
            mt = df_t.groupby("Mo")["TravelCount"].sum().reset_index()
            mt["Month"] = mt["Mo"].map(months_map)
            mt["Label"] = mt["TravelCount"].apply(fmt_num)
            # Order Jul→Jun
            mo_order_fy = [7,8,9,10,11,12,1,2,3,4,5,6]
            mt = mt.set_index("Mo").reindex(mo_order_fy).reset_index()
            mt["Month"] = mt["Mo"].map(months_map)
            fig = px.bar(mt, x="Month", y="TravelCount", text="Label",
                         color="TravelCount", color_continuous_scale="Blues")
            fig.update_traces(textposition="outside", textfont_size=10)
            apply_layout(fig, height=280, xaxis=dict(gridcolor="#eeeeee"),
                         yaxis=dict(gridcolor="#eeeeee", title="Total Trips"), coloraxis_showscale=False)
            fig.update_layout(title="Monthly Travel (Jul→Jun fiscal order)")
            st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# PAGE 5: DISTRIBUTION ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "📦 Distribution Analysis":
    st.markdown("<h2 style='color:#2c5f8a'>📦 Distribution Analysis — ZSDCY (Primary Sales)</h2>", unsafe_allow_html=True)
    st.markdown(note("📅 FY2022 = Jul22–Jun23 | FY2023 = Jul23–Jun24 | FY2024 = Jul24–Jun25 | FY2025 = Jul25–present (partial). ZSDCY = factory → Premier Sales distributor."), unsafe_allow_html=True)

    if len(df_z) > 0 and "Revenue" in df_z.columns:
        total_rev_z = df_z["Revenue"].sum()
        total_qty_z = df_z["Qty"].sum() if "Qty" in df_z.columns else 0
        total_cities = df_z["City"].nunique() if "City" in df_z.columns else 0
        total_sdps = df_z["SDP Name"].nunique() if "SDP Name" in df_z.columns else 0

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.markdown(kpi("Total Revenue", fmt(total_rev_z), "All FYs ZSDCY"), unsafe_allow_html=True)
        c2.markdown(kpi("Total Units", fmt_num(total_qty_z), "Delivered units"), unsafe_allow_html=True)
        c3.markdown(kpi("Cities Covered", str(total_cities), "Unique cities"), unsafe_allow_html=True)
        c4.markdown(kpi("Distributors (SDPs)", str(total_sdps), "Premier Sales branches"), unsafe_allow_html=True)
        c5.markdown(kpi("FY2024 Revenue", fmt(zr24), "Jul 2024 – Jun 2025"), unsafe_allow_html=True)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(sec("Primary Revenue by Fiscal Year"), unsafe_allow_html=True)
            if "FY" in df_z.columns:
                zy = df_z.groupby("FY")["Revenue"].sum().reset_index()
                zy["FY_str"] = zy["FY"].apply(lambda x: f"FY{x}")
                zy["Label"] = zy["Revenue"].apply(fmt)
                zy["Partial"] = zy["FY"].apply(lambda x: x==2025)
                colors_z = ["#e65100" if p else "#7b1fa2" for p in zy["Partial"]]
                fig = go.Figure(go.Bar(x=zy["FY_str"], y=zy["Revenue"]/1e9,
                    text=zy["Label"], textposition="outside", textfont_size=11,
                    marker_color=colors_z))
                apply_layout(fig, height=300, xaxis=dict(gridcolor="#eeeeee"),
                             yaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR Billions)"))
                fig.update_layout(title="ZSDCY Primary Sales by FY (Orange = partial)", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(sec("Category Breakdown"), unsafe_allow_html=True)
            if "Category" in df_z.columns:
                cat_map_d = {"P":"Pharma","N":"Nutraceutical","M":"Medical Device","H":"Herbal","E":"Export","O":"Other"}
                cat_rev = df_z.groupby("Category")["Revenue"].sum().reset_index()
                cat_rev["CategoryName"] = cat_rev["Category"].map(cat_map_d).fillna(cat_rev["Category"])
                fig = px.pie(cat_rev, values="Revenue", names="CategoryName",
                             color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_traces(textinfo="percent+label", textfont_size=11)
                apply_layout(fig, height=300)
                st.plotly_chart(fig, use_container_width=True)

        # Top products
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(sec("Top 20 Products by Revenue"), unsafe_allow_html=True)
            if "Material Name" in df_z.columns:
                top20 = df_z.groupby("Material Name")["Revenue"].sum().nlargest(20).reset_index()
                top20["Label"] = top20["Revenue"].apply(fmt)
                top20["Short"] = top20["Material Name"].str[:35]
                fig = px.bar(top20, x="Revenue", y="Short", orientation="h", text="Label",
                             color="Revenue", color_continuous_scale="Blues")
                fig.update_traces(textposition="outside", textfont_size=9)
                apply_layout(fig, height=580, yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                             xaxis=dict(gridcolor="#eeeeee"), coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(sec("Top Cities by Revenue"), unsafe_allow_html=True)
            if "City" in df_z.columns:
                city_rev = df_z.groupby("City")["Revenue"].sum().nlargest(20).reset_index()
                city_rev["Label"] = city_rev["Revenue"].apply(fmt)
                fig = px.bar(city_rev, x="Revenue", y="City", orientation="h", text="Label",
                             color="Revenue", color_continuous_scale="Greens")
                fig.update_traces(textposition="outside", textfont_size=9)
                apply_layout(fig, height=580, yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                             xaxis=dict(gridcolor="#eeeeee"), coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

        # FY growth comparison
        st.markdown(sec("FY2023 vs FY2024 City Growth (Complete Years)"), unsafe_allow_html=True)
        if "FY" in df_z.columns and "City" in df_z.columns:
            c23 = df_z[df_z["FY"]==2023].groupby("City")["Revenue"].sum()
            c24 = df_z[df_z["FY"]==2024].groupby("City")["Revenue"].sum()
            cg = pd.DataFrame({"fy23":c23,"fy24":c24}).dropna()
            cg = cg[cg["fy23"]>10e6]
            cg["Growth"] = (cg["fy24"]-cg["fy23"])/cg["fy23"]*100
            cg = cg.sort_values("Growth",ascending=False).head(15).reset_index()
            cg["Label"] = cg["Growth"].apply(lambda x: f"+{x:.0f}%" if x>=0 else f"{x:.0f}%")
            colors_cg = ["#2e7d32" if g>30 else "#2c5f8a" if g>0 else "#c62828" for g in cg["Growth"]]
            fig = go.Figure(go.Bar(x=cg["Growth"], y=cg["City"], orientation="h",
                text=cg["Label"], textposition="outside", textfont_size=9, marker_color=colors_cg))
            apply_layout(fig, height=450, yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee", title="Revenue Growth % FY2023→FY2024"))
            fig.update_layout(title="City Revenue Growth: FY2023 → FY2024 (Complete Fiscal Years)")
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("⚠️ ZSDCY data not loaded. Please upload zsdcy_agg.csv to GitHub.")


# ════════════════════════════════════════════════════════════
# PAGE 6: STRATEGIC INTELLIGENCE HUB
# ════════════════════════════════════════════════════════════
elif page == "🔬 Strategic Intelligence Hub":
    st.markdown("<h1 style='color:#2c5f8a'>🔬 Strategic Intelligence Hub</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#666'>Fiscal Year Analysis | FY2022–FY2025 | Updated {CURRENT_DATE}</p>", unsafe_allow_html=True)
    st.markdown(note("📅 All analysis uses fiscal years (Jul–Jun). FY2025 = partial (Jul 2025–Apr 2026). Compare FY2023 vs FY2024 for latest complete year-over-year analysis."), unsafe_allow_html=True)
    st.markdown("---")

    hub_tab1, hub_tab2, hub_tab3 = st.tabs([
        "🔗 ROI Analysis",
        "🚨 Alerts & Opportunities",
        "📊 BCG Matrix"
    ])

    with hub_tab1:
        st.markdown("<h2 style='color:#2c5f8a'>🔗 ROI Analysis — Fiscal Year</h2>", unsafe_allow_html=True)

        # ROI by FY
        c1,c2,c3,c4 = st.columns(4)
        roi22 = rv22/sp22 if sp22>0 else 0
        roi23 = rv23/sp23 if sp23>0 else 0
        c1.markdown(kpi("ROI FY2022", f"{roi22:.1f}x" if roi22>0 else "N/A", "Jul22–Jun23"), unsafe_allow_html=True)
        c2.markdown(kpi("ROI FY2023", f"{roi23:.1f}x" if roi23>0 else "N/A", "Jul23–Jun24"), unsafe_allow_html=True)
        c3.markdown(kpi("ROI FY2024", f"{roi24:.1f}x" if roi24>0 else "N/A", "Jul24–Jun25"), unsafe_allow_html=True)
        c4.markdown(kpi("ROI FY2025", f"{roi25:.1f}x" if roi25>0 else "N/A", "Partial — Jul25–Apr26", red=True), unsafe_allow_html=True)

        # ROI trend chart
        roi_fys = [(2022,roi22),(2023,roi23),(2024,roi24),(2025,roi25)]
        roi_df_plot = pd.DataFrame(roi_fys, columns=["FY","ROI"])
        roi_df_plot = roi_df_plot[roi_df_plot["ROI"]>0]
        roi_df_plot["FY_str"] = roi_df_plot["FY"].apply(lambda x: f"FY{x}")
        roi_df_plot["Partial"] = roi_df_plot["FY"].apply(lambda x: x==2025)
        colors_roi = ["#e65100" if p else "#2c5f8a" for p in roi_df_plot["Partial"]]
        fig = go.Figure(go.Bar(x=roi_df_plot["FY_str"], y=roi_df_plot["ROI"],
            text=roi_df_plot["ROI"].apply(lambda x: f"{x:.1f}x"),
            textposition="outside", textfont_size=13, marker_color=colors_roi))
        apply_layout(fig, height=300, xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee", title="ROI"))
        fig.update_layout(title="ROI by Fiscal Year — Orange = partial FY2025", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Top ROI products
        st.markdown(sec("Top Products by ROI"), unsafe_allow_html=True)
        if "ProductName" in df_sales.columns and "Product" in df_act.columns:
            rv_p = df_sales[df_sales["FY"].isin([2023,2024])].groupby("ProductName")["TotalRevenue"].sum()
            sp_p = df_act[df_act["FY"].isin([2023,2024])].groupby("Product")["TotalAmount"].sum()
            rc = pd.DataFrame({"Rev":rv_p,"Spend":sp_p}).dropna().reset_index()
            rc.columns = ["ProductName","Rev","Spend"]
            rc = rc[rc["Spend"]>500000]
            rc["ROI"] = rc["Rev"]/rc["Spend"]
            tr = rc.nlargest(15,"ROI")
            colors_r = ["#FFD700" if "XCEPT" in p.upper() else "#2e7d32" if r>30 else "#2c5f8a"
                        for p,r in zip(tr["ProductName"],tr["ROI"])]
            fig = go.Figure(go.Bar(x=tr["ROI"], y=tr["ProductName"], orientation="h",
                text=[f"{r:.1f}x" for r in tr["ROI"]], textposition="outside", textfont_size=10,
                marker_color=colors_r))
            apply_layout(fig, height=480, yaxis=dict(autorange="reversed",gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee",title="ROI"))
            fig.update_layout(title="Top 15 ROI Products — FY2023+FY2024 (Complete Years)")
            st.plotly_chart(fig, use_container_width=True)

    with hub_tab2:
        st.markdown("<h2 style='color:#2c5f8a'>🚨 Alerts & Opportunities</h2>", unsafe_allow_html=True)

        # FY-based alerts
        if rv24 > 0 and rv23 > 0:
            rev_growth_fy = (rv24-rv23)/rv23*100
            st.markdown(sec(f"📈 Revenue Growth FY2023→FY2024: +{rev_growth_fy:.1f}%"), unsafe_allow_html=True)
            if rev_growth_fy > 10:
                st.markdown(good(f"Revenue grew +{rev_growth_fy:.1f}% from FY2023 ({fmt(rv23)}) to FY2024 ({fmt(rv24)}). Strong performance on complete fiscal years."), unsafe_allow_html=True)
            else:
                st.markdown(warn(f"Revenue growth slowed to +{rev_growth_fy:.1f}%. Investigate product mix and promo effectiveness."), unsafe_allow_html=True)

        if roi24 > 0 and roi23 > 0:
            st.markdown(sec("💹 ROI Trend Analysis"), unsafe_allow_html=True)
            if roi24 < roi23:
                st.markdown(danger(f"ROI declined FY2023→FY2024: {roi23:.1f}x → {roi24:.1f}x. Promo spend is growing faster than revenue. Fix timing and product mix."), unsafe_allow_html=True)
            else:
                st.markdown(good(f"ROI improved: {roi23:.1f}x (FY2023) → {roi24:.1f}x (FY2024). Promotional efficiency is improving!"), unsafe_allow_html=True)

        # Hidden opportunities (high ROI, low spend)
        if "ProductName" in df_sales.columns and "Product" in df_act.columns:
            rv_a = df_sales[df_sales["FY"].isin([2023,2024])].groupby("ProductName")["TotalRevenue"].sum()
            sp_a = df_act[df_act["FY"].isin([2023,2024])].groupby("Product")["TotalAmount"].sum()
            roi_a = pd.DataFrame({"Revenue":rv_a,"Spend":sp_a}).dropna().reset_index()
            roi_a.columns = ["ProductName","TotalRevenue","TotalPromoSpend"]
            roi_a = roi_a[roi_a["TotalPromoSpend"]>0]
            roi_a["ROI"] = roi_a["TotalRevenue"]/roi_a["TotalPromoSpend"]

            st.markdown(sec("🌟 Hidden Opportunities — High ROI, Low Budget (FY2023+FY2024)"), unsafe_allow_html=True)
            opp = roi_a[(roi_a["ROI"]>20)&(roi_a["TotalPromoSpend"]<roi_a["TotalPromoSpend"].median())].sort_values("ROI",ascending=False).head(8)
            for _, row in opp.iterrows():
                st.markdown(good(f"<b>{row['ProductName']}</b> — ROI: <b>{row['ROI']:.1f}x</b> | Spend: {fmt(row['TotalPromoSpend'])} | Revenue: {fmt(row['TotalRevenue'])}<br><i>Action: Increase budget → expected revenue growth</i>"), unsafe_allow_html=True)

        # Q4 (Oct-Dec) peak within FY
        if "Mo" in df_s.columns and "TotalRevenue" in df_s.columns:
            st.markdown(sec("📅 Peak Sales Months within Fiscal Year"), unsafe_allow_html=True)
            mo_rev = df_s[df_s["FY"].isin([2022,2023,2024])].groupby("Mo")["TotalRevenue"].sum().reset_index()
            mo_rev["Month"] = mo_rev["Mo"].map(months_map)
            mo_rev["FYPosition"] = mo_rev["Mo"].apply(lambda m: (m-7)%12)  # Jul=0, Aug=1...Jun=11
            mo_rev = mo_rev.sort_values("FYPosition")
            q4_months = [10,11,12]
            q4_rev = mo_rev[mo_rev["Mo"].isin(q4_months)]["TotalRevenue"].sum()
            total_rev_mo = mo_rev["TotalRevenue"].sum()
            st.markdown(good(f"Oct/Nov/Dec (calendar Q4) = {q4_rev/total_rev_mo*100:.1f}% of revenue across FY2022–FY2024. These months consistently peak — start campaigns in September."), unsafe_allow_html=True)

    with hub_tab3:
        st.markdown("<h2 style='color:#2c5f8a'>📊 BCG Matrix — FY2023 vs FY2024</h2>", unsafe_allow_html=True)
        st.markdown(note("Based on complete fiscal years. Growth = FY2023→FY2024 change. Size = total revenue FY2022+FY2023+FY2024."), unsafe_allow_html=True)

        if "FY" in df_s.columns and "ProductName" in df_s.columns:
            r23_b = df_s[df_s["FY"]==2023].groupby("ProductName")["TotalRevenue"].sum()
            r24_b = df_s[df_s["FY"]==2024].groupby("ProductName")["TotalRevenue"].sum()
            bcg = pd.DataFrame({"Rev23":r23_b,"Rev24":r24_b}).dropna()
            bcg = bcg[bcg["Rev23"]>5e6].reset_index()
            bcg["Growth"] = (bcg["Rev24"]-bcg["Rev23"])/bcg["Rev23"]*100
            bcg["TotalRev"] = bcg["Rev23"]+bcg["Rev24"]
            med_r = bcg["TotalRev"].median(); med_g = bcg["Growth"].median()

            def classify_bcg(row):
                if row["TotalRev"]>=med_r and row["Growth"]>=med_g: return "⭐ Stars"
                elif row["TotalRev"]>=med_r: return "🐄 Cash Cows"
                elif row["Growth"]>=med_g:  return "❓ Question Marks"
                else: return "🐕 Dogs"
            bcg["Category"] = bcg.apply(classify_bcg, axis=1)

            c1,c2,c3,c4 = st.columns(4)
            for cat, col in zip(["⭐ Stars","🐄 Cash Cows","❓ Question Marks","🐕 Dogs"],[c1,c2,c3,c4]):
                n = len(bcg[bcg["Category"]==cat])
                desc = {"⭐ Stars":"Invest More","🐄 Cash Cows":"Maintain","❓ Question Marks":"Watch","🐕 Dogs":"Cut Budget"}
                col.markdown(kpi(cat, str(n), desc[cat], red=cat=="🐕 Dogs"), unsafe_allow_html=True)

            fig = px.scatter(bcg, x="TotalRev", y="Growth", color="Category", size="TotalRev",
                hover_name="ProductName", size_max=40,
                color_discrete_map={"⭐ Stars":"#2e7d32","🐄 Cash Cows":"#2c5f8a",
                                     "❓ Question Marks":"#e65100","🐕 Dogs":"#c62828"},
                labels={"TotalRev":"Total Revenue (FY23+FY24)","Growth":"Growth % FY2023→FY2024"},
                title="BCG Matrix — FY2023 vs FY2024 (Complete Fiscal Years)")
            fig.add_vline(x=med_r, line_dash="dash", line_color="gray")
            fig.add_hline(y=med_g, line_dash="dash", line_color="gray")
            apply_layout(fig, height=450)
            st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# PAGE 7: ML INTELLIGENCE
# ════════════════════════════════════════════════════════════
elif page == "🤖 ML Intelligence":
    from sklearn.ensemble import GradientBoostingRegressor
    import warnings; warnings.filterwarnings("ignore")

    st.markdown("<h1 style='color:#2c5f8a'>🤖 ML Intelligence Center</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#555'>6-Month Forecasts | Fiscal Year Training Data FY2022–FY2025 | {CURRENT_DATE}</p>", unsafe_allow_html=True)
    st.markdown(note("📅 Forecasts trained on FY2022–FY2025 data. FY2025 is partial (10 months). Prediction horizon: next 6 months from Apr 2026."), unsafe_allow_html=True)

    try:
        hist_roi = pd.read_csv("ml_roi_products.csv")
        models_ok = True
    except:
        # Build ROI from loaded data
        if "ProductName" in df_sales.columns and "Product" in df_act.columns:
            rv_p = df_sales.groupby("ProductName")["TotalRevenue"].sum()
            sp_p = df_act.groupby("Product")["TotalAmount"].sum()
            hist_roi = pd.DataFrame({"TotalRevenue":rv_p,"TotalPromoSpend":sp_p}).dropna().reset_index()
            hist_roi.columns = ["ProductName","TotalRevenue","TotalPromoSpend"]
            hist_roi = hist_roi[hist_roi["TotalPromoSpend"]>500000]
            hist_roi["ROI"] = hist_roi["TotalRevenue"]/hist_roi["TotalPromoSpend"]
            hist_roi = hist_roi.sort_values("ROI",ascending=False)
            models_ok = True
        else:
            models_ok = False
            st.error("Data not available for ML.")

    if models_ok:
        def build_forecast(series_df, value_col, yoy_growth=1.10, n_months=6):
            df_f = series_df.copy().sort_values(["Yr","Mo"]).reset_index(drop=True)
            df_f["Date"] = pd.to_datetime(df_f["Yr"].astype(int).astype(str)+"-"+df_f["Mo"].astype(int).astype(str)+"-01")
            df_f["lag1"] = df_f[value_col].shift(1)
            df_f["lag2"] = df_f[value_col].shift(2)
            df_f["lag3"] = df_f[value_col].shift(3)
            df_f["roll3"] = df_f[value_col].rolling(3).mean()
            df_f["roll6"] = df_f[value_col].rolling(6).mean()
            df_f["sin_m"] = np.sin(2*np.pi*df_f["Mo"]/12)
            df_f["cos_m"] = np.cos(2*np.pi*df_f["Mo"]/12)
            df_f["trend"] = np.arange(len(df_f))
            feats = ["Yr","Mo","lag1","lag2","lag3","roll3","roll6","sin_m","cos_m","trend"]
            train = df_f.dropna().copy()
            if len(train) < 6:
                return df_f, pd.DataFrame()
            gbr = GradientBoostingRegressor(n_estimators=300, learning_rate=0.05, max_depth=4, random_state=42)
            gbr.fit(train[feats], train[value_col])
            last = df_f.iloc[-1]
            last_yr = int(last["Yr"]); last_mo = int(last["Mo"]); last_tr = int(last["trend"])
            history = list(df_f[value_col].values)
            forecasts = []
            for i in range(1, n_months+1):
                mo = last_mo + i; yr = last_yr
                if mo > 12: mo -= 12; yr += 1
                same = df_f[(df_f["Yr"]==yr-1)&(df_f["Mo"]==mo)][value_col].values
                base = same[0]*yoy_growth if len(same)>0 else history[-1]
                row = pd.DataFrame([[yr,mo,history[-1],history[-2],history[-3],
                    np.mean(history[-3:]),np.mean(history[-6:]),
                    np.sin(2*np.pi*mo/12),np.cos(2*np.pi*mo/12),last_tr+i]], columns=feats)
                pred = max(gbr.predict(row)[0]*0.4 + base*0.6, base*0.95)
                mo_n = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][mo-1]
                forecasts.append({"Month":f"{mo_n} {yr}","Date":pd.Timestamp(f"{yr}-{mo:02d}-01"),
                    "Forecast":pred,"Upper":pred*1.10,"Lower":pred*0.90})
                history.append(pred)
            return df_f, pd.DataFrame(forecasts)

        # Build monthly series
        if "TotalRevenue" in df_sales.columns and "Yr" in df_sales.columns:
            dsr_rev = df_sales.groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
            dsr_units = df_sales.groupby(["Yr","Mo"])["TotalUnits"].sum().reset_index() if "TotalUnits" in df_sales.columns else pd.DataFrame()

            # Revenue forecast
            st.markdown(sec("📈 Secondary Revenue Forecast — Next 6 Months"), unsafe_allow_html=True)
            st.markdown(note("Trained on FY2022–FY2025 (3 complete + 1 partial fiscal year). Orange dashed = forecast May–Oct 2026."), unsafe_allow_html=True)
            try:
                hist_r, fc_r = build_forecast(dsr_rev, "TotalRevenue", yoy_growth=1.10)
                hist_r_plot = hist_r[hist_r["Yr"]>=2023]
                col1, col2 = st.columns([3,1])
                with col1:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=hist_r_plot["Date"], y=hist_r_plot["TotalRevenue"]/1e9,
                        name="Actual Revenue", mode="lines+markers",
                        line=dict(color="#2c5f8a",width=3), marker=dict(size=5)))
                    if len(fc_r) > 0:
                        fig.add_trace(go.Scatter(x=fc_r["Date"], y=fc_r["Forecast"]/1e9,
                            name="Forecast", mode="lines+markers",
                            line=dict(color="#e65100",width=3,dash="dash"),
                            marker=dict(size=9,symbol="diamond")))
                        db = pd.concat([fc_r["Date"],fc_r["Date"][::-1]])
                        vb = pd.concat([fc_r["Upper"]/1e9,fc_r["Lower"][::-1]/1e9])
                        fig.add_trace(go.Scatter(x=db,y=vb,fill="toself",
                            fillcolor="rgba(230,81,0,0.10)",line=dict(color="rgba(0,0,0,0)"),
                            name="±10% Band",hoverinfo="skip"))
                    apply_layout(fig, height=380, yaxis=dict(gridcolor="#eee",title="Revenue (PKR Billions)"),
                                 hovermode="x unified")
                    fig.update_layout(title="Revenue Forecast: May–Oct 2026")
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    if len(fc_r) > 0:
                        lines = "\n".join([f"{r['Month']}: PKR {r['Forecast']/1e9:.2f}B" for _,r in fc_r.iterrows()])
                        total_fc = fc_r["Forecast"].sum()/1e9
                        st.markdown(f"""<div class="manual-working">6-MONTH FORECAST
══════════════════════
{lines}

TOTAL: PKR {total_fc:.2f}B
Training: FY2022-FY2025
Growth rate: ~10% YoY
══════════════════════</div>""", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Forecast error: {e}")

        # ROI simulator
        st.markdown("---")
        st.markdown(sec("💹 Budget ROI Simulator"), unsafe_allow_html=True)
        if len(hist_roi) > 0:
            col1, col2 = st.columns(2)
            with col1:
                top_roi = hist_roi.head(15)
                colors_roi = ["#FFD700" if "XCEPT" in str(p).upper() else "#2e7d32" if r>30 else "#2c5f8a"
                              for p,r in zip(top_roi["ProductName"],top_roi["ROI"])]
                fig = go.Figure(go.Bar(x=top_roi["ROI"], y=top_roi["ProductName"], orientation="h",
                    text=top_roi["ROI"].apply(lambda x: f"{x:.1f}x"),
                    textposition="outside", textfont_size=10, marker_color=colors_roi))
                apply_layout(fig, height=480, yaxis=dict(autorange="reversed",gridcolor="#eee"),
                    xaxis=dict(gridcolor="#eee",title="ROI"))
                fig.update_layout(title="Top 15 Products by ROI")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown("### 🎯 Budget Simulator")
                budget_input = st.number_input("Budget (PKR)", min_value=100000, max_value=50000000,
                    value=5000000, step=500000, key="ml_budget")
                prod_list = sorted(hist_roi["ProductName"].unique())
                default_idx = prod_list.index("Xcept") if "Xcept" in prod_list else 0
                prod_sel = st.selectbox("Select Product", prod_list, index=default_idx, key="ml_prod")
                prod_row = hist_roi[hist_roi["ProductName"]==prod_sel]
                if len(prod_row) > 0:
                    h_roi = prod_row.iloc[0]["ROI"]
                    expected_rev = budget_input * h_roi
                    st.markdown(f"""<div class="manual-working">PREDICTION
══════════════════════
Product : {prod_sel}
Budget  : {fmt(budget_input)}
ROI     : {h_roi:.1f}x
Expected: {fmt(expected_rev)}
Upper   : {fmt(expected_rev*1.2)}
Lower   : {fmt(expected_rev*0.8)}
══════════════════════</div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 8: PERSONAL DASHBOARD
# ════════════════════════════════════════════════════════════
elif page == "📌 Personal Dashboard":
    st.markdown("<h1 style='color:#2c5f8a'>📌 Personal Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666'>Build your own view. Fiscal Year system applied throughout.</p>", unsafe_allow_html=True)
    st.markdown("---")

    all_charts = {
        "📊 KPI — Revenue by FY": "kpi_fy",
        "📊 KPI — Promo Spend & ROI": "kpi_promo",
        "📊 KPI — Field Trips by FY": "kpi_travel",
        "📊 KPI — Primary Sales (ZSDCY)": "kpi_zsdcy",
        "📈 Revenue Trend (Monthly)": "rev_trend",
        "📊 Revenue by Fiscal Year": "rev_fy",
        "🏆 Top Products by Revenue": "top_products",
        "⚠️ Bottom Products by Revenue": "bot_products",
        "👥 Teams by Revenue": "top_teams",
        "🚀 Fastest Growing Products (FY23→FY24)": "fast_grow",
        "📅 Sales Seasonality Heatmap (FY)": "seasonality",
        "💰 Promo Spend by FY": "promo_fy",
        "💰 Promo Spend by Team": "promo_team",
        "💰 Promo Spend by Product": "promo_prod",
        "📊 ROI by Product": "roi_products",
        "📊 ROI by FY": "roi_fy",
        "✈️ Travel by FY": "travel_fy",
        "✈️ Top Cities": "travel_cities",
        "📦 ZSDCY Revenue by FY": "zsdcy_fy",
        "🌿 Category Breakdown (ZSDCY)": "zsdcy_cat",
        "⚡ Quick Wins Table": "quick_wins",
    }

    if "personal_charts" not in st.session_state:
        st.session_state.personal_charts = []

    col1, col2 = st.columns([3,1])
    with col1:
        selected_charts = st.multiselect("Choose items:", options=list(all_charts.keys()),
            default=st.session_state.personal_charts if st.session_state.personal_charts else [])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Save", type="primary", use_container_width=True):
            st.session_state.personal_charts = selected_charts
            st.success(f"✅ Saved {len(selected_charts)} items!")
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.personal_charts = []
            st.rerun()

    active = st.session_state.personal_charts if st.session_state.personal_charts else selected_charts
    if not active:
        st.info("Select items above to build your view.")
    else:
        st.markdown("---")
        for i in range(0, len(active), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i+j < len(active):
                    chart_name = active[i+j]
                    chart_key = all_charts[chart_name]
                    with col:
                        st.markdown(f"**{chart_name}**")
                        try:
                            if chart_key == "kpi_fy":
                                c1,c2,c3,c4 = st.columns(4)
                                c1.markdown(kpi("FY2022",fmt(rv22),"Jul22–Jun23"), unsafe_allow_html=True)
                                c2.markdown(kpi("FY2023",fmt(rv23),"Jul23–Jun24"), unsafe_allow_html=True)
                                c3.markdown(kpi("FY2024",fmt(rv24),"Jul24–Jun25"), unsafe_allow_html=True)
                                c4.markdown(kpi("FY2025",fmt(rv25),"Partial",red=True), unsafe_allow_html=True)
                            elif chart_key == "kpi_promo":
                                c1,c2,c3 = st.columns(3)
                                c1.markdown(kpi("FY2024 Spend",fmt(sp24),"Jul24–Jun25"), unsafe_allow_html=True)
                                c2.markdown(kpi("ROI FY2024",f"{roi24:.1f}x","Complete year"), unsafe_allow_html=True)
                                c3.markdown(kpi("ROI FY2025",f"{roi25:.1f}x","Partial",red=True), unsafe_allow_html=True)
                            elif chart_key == "rev_trend":
                                if "Date" in df_s.columns:
                                    m = df_s.groupby("Date")["TotalRevenue"].sum().reset_index()
                                    fig = px.line(m, x="Date", y="TotalRevenue", color_discrete_sequence=["#2c5f8a"])
                                    fig.update_traces(mode="lines+markers")
                                    apply_layout(fig, height=280)
                                    st.plotly_chart(fig, use_container_width=True)
                            elif chart_key == "rev_fy":
                                fy_d = pd.DataFrame({"FY":["FY2022","FY2023","FY2024","FY2025"],
                                    "Rev":[rv22,rv23,rv24,rv25]})
                                fy_d = fy_d[fy_d["Rev"]>0]
                                fig = px.bar(fy_d, x="FY", y="Rev", text=fy_d["Rev"].apply(fmt),
                                    color_discrete_sequence=["#2c5f8a"])
                                fig.update_traces(textposition="outside")
                                apply_layout(fig, height=280)
                                st.plotly_chart(fig, use_container_width=True)
                            elif chart_key == "top_products":
                                if "ProductName" in df_s.columns:
                                    tp = df_s.groupby("ProductName")["TotalRevenue"].sum().nlargest(10).reset_index()
                                    fig = px.bar(tp, x="TotalRevenue", y="ProductName", orientation="h",
                                        text=tp["TotalRevenue"].apply(fmt), color_discrete_sequence=["#2c5f8a"])
                                    fig.update_traces(textposition="outside",textfont_size=9)
                                    apply_layout(fig, height=320, yaxis=dict(autorange="reversed"))
                                    st.plotly_chart(fig, use_container_width=True)
                            elif chart_key == "roi_fy":
                                rfys = [(2022,roi22),(2023,roi23),(2024,roi24),(2025,roi25)]
                                rfys_df = pd.DataFrame(rfys,columns=["FY","ROI"])
                                rfys_df = rfys_df[rfys_df["ROI"]>0]
                                rfys_df["FY_str"] = rfys_df["FY"].apply(lambda x: f"FY{x}")
                                fig = px.bar(rfys_df, x="FY_str", y="ROI",
                                    text=rfys_df["ROI"].apply(lambda x: f"{x:.1f}x"),
                                    color_discrete_sequence=["#2c5f8a"])
                                fig.update_traces(textposition="outside")
                                apply_layout(fig, height=280, yaxis=dict(title="ROI"))
                                st.plotly_chart(fig, use_container_width=True)
                            elif chart_key == "zsdcy_fy":
                                if len(df_z)>0 and "FY" in df_z.columns:
                                    zy = df_z.groupby("FY")["Revenue"].sum().reset_index()
                                    zy["FY_str"] = zy["FY"].apply(lambda x: f"FY{x}")
                                    fig = px.bar(zy, x="FY_str", y="Revenue",
                                        text=zy["Revenue"].apply(fmt), color_discrete_sequence=["#7b1fa2"])
                                    fig.update_traces(textposition="outside")
                                    apply_layout(fig, height=280)
                                    st.plotly_chart(fig, use_container_width=True)
                            elif chart_key == "quick_wins":
                                qw = pd.DataFrame({
                                    "Action":["Invest in top-ROI product","Fix promo timing","Q4 campaigns (Oct-Dec)",
                                              "Nutraceutical team","City depot expansion"],
                                    "Expected Impact":["+PKR 300M","+PKR 200M","+PKR 300M","+PKR 200M","+PKR 150M"],
                                    "FY":["FY2025","FY2025","FY2025","FY2025–FY2026","FY2025–FY2026"]})
                                st.dataframe(qw, use_container_width=True, hide_index=True)
                            else:
                                st.info(f"Chart '{chart_name}' — select on main pages for detailed view.")
                        except Exception as e:
                            st.error(f"Error: {e}")


# ════════════════════════════════════════════════════════════
# PAGE 9: MANAGEMENT VIEW
# ════════════════════════════════════════════════════════════
elif page == "👔 Management View":
    st.markdown("<h1 style='color:#2c5f8a'>👔 Management Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#666'>Fiscal Year Summary for Management | {CURRENT_DATE}</p>", unsafe_allow_html=True)
    st.markdown(note("📅 All numbers use fiscal year (Jul–Jun). FY2025 is partial (Jul 2025–Apr 2026 = 10 months)."), unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 Sales Management", "📣 Marketing Leadership", "🏆 Elite Management"])

    with tab1:
        st.markdown("### 📊 Sales Management — Fiscal Year Overview")

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.markdown(kpi("FY2022 Revenue", fmt(rv22), "Jul 2022 – Jun 2023"), unsafe_allow_html=True)
        c2.markdown(kpi("FY2023 Revenue", fmt(rv23), f"+{(rv23-rv22)/rv22*100:.1f}% vs FY2022" if rv22>0 else "Jul 2023 – Jun 2024"), unsafe_allow_html=True)
        c3.markdown(kpi("FY2024 Revenue", fmt(rv24), f"+{(rv24-rv23)/rv23*100:.1f}% vs FY2023" if rv23>0 else "Jul 2024 – Jun 2025"), unsafe_allow_html=True)
        c4.markdown(kpi("FY2025 (partial)", fmt(rv25), "Jul 2025 – Apr 2026 only", red=True), unsafe_allow_html=True)
        c5.markdown(kpi("Growth FY23→FY24", f"+{(rv24-rv23)/rv23*100:.1f}%" if rv23>0 else "N/A", "Latest complete pair"), unsafe_allow_html=True)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(sec("Revenue by Fiscal Year — Management View"), unsafe_allow_html=True)
            fy_df = pd.DataFrame({
                "Fiscal Year": ["FY2022\n(Jul22–Jun23)","FY2023\n(Jul23–Jun24)","FY2024\n(Jul24–Jun25)","FY2025*\n(Jul25–Apr26)"],
                "Revenue": [rv22, rv23, rv24, rv25],
                "Complete": [True, True, True, False]
            })
            fy_df = fy_df[fy_df["Revenue"] > 0]
            colors_mgmt = ["#e65100" if not c else "#2c5f8a" for c in fy_df["Complete"]]
            fig = go.Figure(go.Bar(
                x=fy_df["Fiscal Year"], y=fy_df["Revenue"]/1e9,
                text=fy_df["Revenue"].apply(fmt), textposition="outside", textfont_size=12,
                marker_color=colors_mgmt))
            apply_layout(fig, height=350, xaxis=dict(gridcolor="#eeeeee"),
                         yaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR Billions)"))
            fig.update_layout(title="Revenue by Fiscal Year (* = partial)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(warn("FY2025 marked * is 10 months only (Jul2025–Apr2026). Not directly comparable to complete years."), unsafe_allow_html=True)

        with col2:
            st.markdown(sec("YoY Growth Rate (Fiscal Year)"), unsafe_allow_html=True)
            growth_pairs = []
            if rv22>0 and rv23>0: growth_pairs.append(("FY22→FY23",(rv23-rv22)/rv22*100))
            if rv23>0 and rv24>0: growth_pairs.append(("FY23→FY24",(rv24-rv23)/rv23*100))
            if growth_pairs:
                gp_df = pd.DataFrame(growth_pairs, columns=["Period","Growth"])
                colors_gp = ["#2e7d32" if g>10 else "#e65100" for g in gp_df["Growth"]]
                fig = go.Figure(go.Bar(
                    x=gp_df["Period"], y=gp_df["Growth"],
                    text=gp_df["Growth"].apply(lambda x: f"+{x:.1f}%"),
                    textposition="outside", textfont_size=13, marker_color=colors_gp))
                apply_layout(fig, height=300, xaxis=dict(gridcolor="#eeeeee"),
                             yaxis=dict(gridcolor="#eeeeee",title="Growth %"))
                fig.update_layout(title="Revenue Growth Rate (Complete FY pairs)", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # Team performance
        if "TeamName" in df_s.columns and "FY" in df_s.columns:
            st.markdown(sec("Team Revenue — FY2024 (Latest Complete Year)"), unsafe_allow_html=True)
            team_fy24 = df_s[df_s["FY"]==2024].groupby("TeamName")["TotalRevenue"].sum().nlargest(15).reset_index()
            team_fy24["Label"] = team_fy24["TotalRevenue"].apply(fmt)
            fig = go.Figure(go.Bar(
                x=team_fy24["TotalRevenue"], y=team_fy24["TeamName"], orientation="h",
                text=team_fy24["Label"], textposition="outside", textfont_size=9,
                marker_color="#2c5f8a"))
            apply_layout(fig, height=480, yaxis=dict(autorange="reversed",gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee",title="Revenue (PKR)"))
            fig.update_layout(title="Top 15 Teams by Revenue — FY2024 (Jul 2024 – Jun 2025)")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### 📣 Marketing Leadership — Fiscal Year ROI")

        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(kpi("Promo Spend FY2023", fmt(sp23), "Jul 2023 – Jun 2024"), unsafe_allow_html=True)
        c2.markdown(kpi("Promo Spend FY2024", fmt(sp24), f"+{(sp24-sp23)/sp23*100:.1f}% vs FY2023" if sp23>0 else "—"), unsafe_allow_html=True)
        c3.markdown(kpi("ROI FY2023", f"{roi23:.1f}x", "Complete year"), unsafe_allow_html=True)
        c4.markdown(kpi("ROI FY2024", f"{roi24:.1f}x", "Complete year"), unsafe_allow_html=True)

        st.markdown("---")

        if "ProductName" in df_sales.columns and "Product" in df_act.columns:
            # ROI products using FY2023+FY2024
            st.markdown(sec("Top ROI Products — FY2023 + FY2024 Combined"), unsafe_allow_html=True)
            rv_m = df_sales[df_sales["FY"].isin([2023,2024])].groupby("ProductName")["TotalRevenue"].sum()
            sp_m = df_act[df_act["FY"].isin([2023,2024])].groupby("Product")["TotalAmount"].sum()
            rc_m = pd.DataFrame({"Rev":rv_m,"Spend":sp_m}).dropna().reset_index()
            rc_m.columns = ["ProductName","Rev","Spend"]
            rc_m = rc_m[rc_m["Spend"]>1e6]
            rc_m["ROI"] = rc_m["Rev"]/rc_m["Spend"]
            top_r = rc_m.nlargest(12,"ROI")
            colors_rm = ["#FFD700" if "XCEPT" in p.upper() else "#2e7d32" if r>25 else "#2c5f8a"
                         for p,r in zip(top_r["ProductName"],top_r["ROI"])]
            fig = go.Figure(go.Bar(
                x=top_r["ROI"], y=top_r["ProductName"], orientation="h",
                text=[f"{r:.1f}x" for r in top_r["ROI"]],
                textposition="outside", textfont_size=10, marker_color=colors_rm))
            apply_layout(fig, height=420, yaxis=dict(autorange="reversed",gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee",title="ROI"))
            fig.update_layout(title="Top 12 ROI Products — FY2023+FY2024 Combined")
            st.plotly_chart(fig, use_container_width=True)

            # Growing products
            st.markdown(sec("Fastest Growing Products FY2023 → FY2024"), unsafe_allow_html=True)
            r23_g = df_sales[df_sales["FY"]==2023].groupby("ProductName")["TotalRevenue"].sum()
            r24_g = df_sales[df_sales["FY"]==2024].groupby("ProductName")["TotalRevenue"].sum()
            gdf = pd.DataFrame({"r23":r23_g,"r24":r24_g}).dropna()
            gdf = gdf[gdf["r23"]>5e6]
            gdf["Growth"] = (gdf["r24"]-gdf["r23"])/gdf["r23"]*100
            top_g = gdf.nlargest(12,"Growth").reset_index()
            fig = go.Figure(go.Bar(
                x=top_g["Growth"], y=top_g["ProductName"], orientation="h",
                text=[f"+{g:.0f}%" for g in top_g["Growth"]],
                textposition="outside", textfont_size=9,
                marker_color=["#e65100" if g>100 else "#2c5f8a" for g in top_g["Growth"]]))
            apply_layout(fig, height=420, yaxis=dict(autorange="reversed",gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee",title="Growth %"))
            fig.update_layout(title="Fastest Growing Products: FY2023 → FY2024")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### 🏆 Elite Management — Complete Fiscal Year Summary")
        st.markdown(note("All numbers based on Jul–Jun fiscal years. For year-over-year comparisons, FY2023→FY2024 is the most reliable (both complete years)."), unsafe_allow_html=True)

        # Full scorecard
        st.markdown(f"""<div class="manual-working">PHARMEVO FISCAL YEAR SCORECARD — {CURRENT_DATE}
═══════════════════════════════════════════════════════════
SECONDARY SALES (DSR Database)
  FY2022 (Jul 2022 – Jun 2023) : {fmt(rv22)} secondary revenue
  FY2023 (Jul 2023 – Jun 2024) : {fmt(rv23)} secondary revenue  ({'+' if rv23>rv22 else ''}{(rv23-rv22)/rv22*100:.1f}% vs FY2022)
  FY2024 (Jul 2024 – Jun 2025) : {fmt(rv24)} secondary revenue  ({'+' if rv24>rv23 else ''}{(rv24-rv23)/rv23*100:.1f}% vs FY2023)
  FY2025 (Jul 2025 – Apr 2026) : {fmt(rv25)} secondary revenue  [PARTIAL - 10 months only]

PRIMARY SALES (ZSDCY Database — Factory → Distributor)
  FY2022 : {fmt(zr22)}
  FY2023 : {fmt(zr23)}
  FY2024 : {fmt(zr24)}
  FY2025 : {fmt(zr25)} [PARTIAL]

PROMOTIONAL INVESTMENT (FTTS Activities)
  FY2022 : {fmt(sp22)}
  FY2023 : {fmt(sp23)}
  FY2024 : {fmt(sp24)}  ROI = {roi24:.1f}x
  FY2025 : {fmt(sp25)}  ROI = {roi25:.1f}x [PARTIAL]

FIELD TRAVEL (FTTS Travel)
  FY2022 : {fmt_num(tr22)} trips
  FY2023 : {fmt_num(tr23)} trips
  FY2024 : {fmt_num(tr24)} trips
  FY2025 : {fmt_num(tr25)} trips [PARTIAL]

KEY INSIGHT: FY2023→FY2024 is latest complete comparison
  Revenue growth : +{(rv24-rv23)/rv23*100:.1f}%
  Promo growth   : +{(sp24-sp23)/sp23*100:.1f}%
  ROI change     : {roi23:.1f}x → {roi24:.1f}x
═══════════════════════════════════════════════════════════</div>""", unsafe_allow_html=True)

        # Action items
        st.markdown(sec("Strategic Priorities — Fiscal Year Aligned"), unsafe_allow_html=True)
        priorities = pd.DataFrame({
            "Priority":["🔴 Immediate","🔴 Immediate","🟡 FY2025","🟡 FY2025","🟢 FY2026"],
            "Action":["Invest in top-ROI products (complete FY2023+FY2024 verified)",
                      "Fix promo timing — align spend months with peak sales months",
                      "Build complete FY2025 data (Jun 2026) for full-year analysis",
                      "Q4 Oct-Dec campaigns — highest revenue months every FY",
                      "Nutraceutical dedicated team — growing faster than Pharma"],
            "Expected Impact":["+PKR 300M+","+PKR 200M","Data completeness","+PKR 300M","+PKR 300M by FY2026"]
        })
        st.dataframe(priorities, use_container_width=True, hide_index=True)

        # FY comparison chart
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(sec("All Databases — Revenue by Fiscal Year"), unsafe_allow_html=True)
            db_rev = pd.DataFrame({
                "FY": ["FY2022","FY2023","FY2024","FY2025*"],
                "Secondary (DSR)": [rv22/1e9, rv23/1e9, rv24/1e9, rv25/1e9],
                "Primary (ZSDCY)": [zr22/1e9, zr23/1e9, zr24/1e9, zr25/1e9],
            })
            db_rev = db_rev[(db_rev["Secondary (DSR)"]>0) | (db_rev["Primary (ZSDCY)"]>0)]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=db_rev["FY"], y=db_rev["Secondary (DSR)"],
                name="Secondary (DSR)", marker_color="#2c5f8a",
                text=[f"{v:.2f}B" for v in db_rev["Secondary (DSR)"]],textposition="outside"))
            fig.add_trace(go.Bar(x=db_rev["FY"], y=db_rev["Primary (ZSDCY)"],
                name="Primary (ZSDCY)", marker_color="#7b1fa2",
                text=[f"{v:.2f}B" for v in db_rev["Primary (ZSDCY)"]],textposition="outside"))
            apply_layout(fig, height=350, barmode="group",
                xaxis=dict(gridcolor="#eeeeee"),
                yaxis=dict(gridcolor="#eeeeee",title="Revenue (PKR Billions)"))
            fig.update_layout(title="Primary vs Secondary Revenue by Fiscal Year")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(sec("ROI Trend by Fiscal Year"), unsafe_allow_html=True)
            roi_pairs = [(2022,roi22,"FY2022"),(2023,roi23,"FY2023"),
                         (2024,roi24,"FY2024"),(2025,roi25,"FY2025*")]
            roi_df_m = pd.DataFrame(roi_pairs, columns=["FY","ROI","Label"])
            roi_df_m = roi_df_m[roi_df_m["ROI"]>0]
            colors_roi_m = ["#e65100" if fy==2025 else "#2c5f8a" if roi>10 else "#c62828"
                            for fy,roi in zip(roi_df_m["FY"],roi_df_m["ROI"])]
            fig = go.Figure(go.Bar(
                x=roi_df_m["Label"], y=roi_df_m["ROI"],
                text=roi_df_m["ROI"].apply(lambda x: f"{x:.1f}x"),
                textposition="outside", textfont_size=13, marker_color=colors_roi_m))
            apply_layout(fig, height=350, xaxis=dict(gridcolor="#eeeeee"),
                         yaxis=dict(gridcolor="#eeeeee",title="ROI"))
            fig.update_layout(title="ROI by Fiscal Year (* = partial)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
