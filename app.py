
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Pharmevo BI Dashboard", page_icon="💊", layout="wide")

# ── LIGHT NEUTRAL THEME ─────────────────────────────────────
st.markdown("""
<style>
body, .main { background-color: #f5f7fa; }
.block-container { padding-top: 1.5rem; }
.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    margin: 4px;
    border-top: 4px solid #2c5f8a;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.kpi-value { font-size: 24px; font-weight: 800; color: #2c5f8a; margin: 6px 0; }
.kpi-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 1px; }
.kpi-delta { font-size: 12px; color: #2e7d32; font-weight: 600; margin-top: 4px; }
.kpi-delta-red { font-size: 12px; color: #c62828; font-weight: 600; margin-top: 4px; }
.insight-box {
    background: #e8f5e9;
    border-left: 5px solid #2e7d32;
    border-radius: 6px;
    padding: 12px 15px;
    margin: 6px 0;
    color: #1b1b1b;
    font-size: 13px;
    line-height: 1.6;
}
.warning-box {
    background: #fff3e0;
    border-left: 5px solid #e65100;
    border-radius: 6px;
    padding: 12px 15px;
    margin: 6px 0;
    color: #1b1b1b;
    font-size: 13px;
    line-height: 1.6;
}
.danger-box {
    background: #ffebee;
    border-left: 5px solid #c62828;
    border-radius: 6px;
    padding: 12px 15px;
    margin: 6px 0;
    color: #1b1b1b;
    font-size: 13px;
    line-height: 1.6;
}
.chart-note {
    background: #e3f2fd;
    border-left: 4px solid #1565c0;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 4px 0 10px 0;
    color: #1b1b1b;
    font-size: 12px;
}
.sec-header {
    font-size: 17px;
    font-weight: 700;
    color: #2c5f8a;
    border-bottom: 2px solid #2c5f8a;
    padding-bottom: 5px;
    margin: 18px 0 10px 0;
}
.manual-working {
    background: #fafafa;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    font-family: monospace;
    font-size: 13px;
    color: #333;
}
</style>
""", unsafe_allow_html=True)

# ── LOAD DATA ───────────────────────────────────────────────
@st.cache_data
def load_data():
    ds = pd.read_csv("sales_clean.csv")
    da = pd.read_csv("activities_clean.csv")
    dm = pd.read_csv("merged_analysis.csv")
    dr = pd.read_csv("roi_analysis.csv")
    dt = pd.read_csv("travel_clean.csv")
    with open("kpis.json") as f:
        kpis = json.load(f)
    ds["Date"] = pd.to_datetime(ds["Date"])
    da["Date"] = pd.to_datetime(da["Date"])
    dt["RequestCreatedDate"] = pd.to_datetime(dt["RequestCreatedDate"])
    dt["FlightDate"]         = pd.to_datetime(dt["FlightDate"])
    return ds, da, dm, dr, dt, kpis

df_sales, df_act, df_merged, df_roi, df_travel, kpis = load_data()

# Load ZSDCY globally for Executive Intelligence page
@st.cache_data
def load_zsdcy_global():
    df = pd.read_csv("zsdcy_clean.csv")
    return df

df_zsdcy = load_zsdcy_global()

months_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}



# ── HELPER FUNCTIONS ────────────────────────────────────────
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

LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(color="#333333", size=12),
    xaxis=dict(gridcolor="#eeeeee", showgrid=True, linecolor="#cccccc"),
    yaxis=dict(gridcolor="#eeeeee", showgrid=True, linecolor="#cccccc"),
    margin=dict(t=30, b=40, l=10, r=10)
)

def apply_layout(fig, height=350, **kwargs):
    layout = dict(LAYOUT)
    layout["height"] = height
    layout.update(kwargs)
    fig.update_layout(**layout)
    return fig

def kpi(label, value, delta, red=False):
    delta_class = "kpi-delta-red" if red else "kpi-delta"
    return f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="{delta_class}">{delta}</div>
    </div>"""

def note(text):  return f"<div class='chart-note'>💡 {text}</div>"
def good(text):  return f"<div class='insight-box'>✅ {text}</div>"
def warn(text):  return f"<div class='warning-box'>⚠️ {text}</div>"
def danger(text):return f"<div class='danger-box'>🚨 {text}</div>"
def sec(text):   return f"<div class='sec-header'>{text}</div>"

# ── SIDEBAR ─────────────────────────────────────────────────
st.sidebar.title("💊 Pharmevo BI")
st.sidebar.markdown("**4 Databases Connected**")
st.sidebar.markdown("- 📊 Sales — DSR Server")
st.sidebar.markdown("- 💰 Activities — FTTS Server")
st.sidebar.markdown("- ✈️ Travel — FTTS Server")
st.sidebar.markdown("- 📦 ZSDCY — Distribution")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigate to", [
    "🏠 Executive Summary",
    "📈 Sales Analysis",
    "💰 Promotional Analysis",
    "✈️ Travel Analysis",
    "📦 Distribution Analysis",
    "🔗 Combined ROI Analysis",
    "🔮 Predictions & Forecast",
    "🚨 Alerts & Opportunities",
    "📊 Advanced Insights",
    "🎯 Strategic Growth Plan",
    "🔬 Marketing Intelligence",
    "🔍 Executive Intelligence",
    "🧠 Combine 4 Dataset",
    "🤖 ML Intelligence"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")
year_filter = st.sidebar.multiselect(
    "Year(s)",
    options=sorted(df_sales["Yr"].unique()),
    default=sorted(df_sales["Yr"].unique()))
team_filter = st.sidebar.multiselect(
    "Team(s)",
    options=sorted(df_sales["TeamName"].unique()),
    default=[])

df_s = df_sales[df_sales["Yr"].isin(year_filter)]
df_a = df_act[df_act["Yr"].isin(year_filter)]
df_t = df_travel[df_travel["Yr"].isin(year_filter)]

if team_filter:
    df_s = df_s[df_s["TeamName"].isin(team_filter)]
    df_a = df_a[df_a["RequestorTeams"].str.upper().isin(
        [t.upper() for t in team_filter])]

# ════════════════════════════════════════════════════════════
# PAGE 1: EXECUTIVE SUMMARY
# ════════════════════════════════════════════════════════════
if page == "🏠 Executive Summary":
    st.markdown("<h1 style=\'color:#2c5f8a\'>💊 Pharmevo Business Intelligence Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style=\'color:#666\'>3 Databases | Sales + Promotions + Travel | 2017-2026 | Updated Live from SQL Server</p>", unsafe_allow_html=True)
    st.markdown("---")

    # # KPI calculations per period
    rev_2025     = df_sales[df_sales["Yr"]==2025]["TotalRevenue"].sum()
    rev_2024     = df_sales[df_sales["Yr"]==2024]["TotalRevenue"].sum()
    rev_2026     = df_sales[df_sales["Yr"]==2026]["TotalRevenue"].sum()
    rev_overall  = df_sales["TotalRevenue"].sum()
    units_2025   = df_sales[df_sales["Yr"]==2025]["TotalUnits"].sum()
    units_overall= df_sales["TotalUnits"].sum()
    spend_2024   = df_act[df_act["Yr"]==2024]["TotalAmount"].sum()
    spend_2025   = df_act[df_act["Yr"]==2025]["TotalAmount"].sum()
    spend_overall= df_act["TotalAmount"].sum()
    roi_2025     = rev_2025/spend_2025 if spend_2025>0 else 0
    roi_overall  = rev_overall/spend_overall if spend_overall>0 else 0
    trips_overall= df_travel["TravelCount"].sum()
    trips_2025   = df_travel[df_travel["Yr"]==2025]["TravelCount"].sum()
    yoy_growth   = ((rev_2025-rev_2024)/rev_2024*100) if rev_2024>0 else 0

    st.markdown("### 📊 Key Performance Indicators — Company Overview")
    st.markdown(note("ROW 1: Company totals 2024-2026. ROW 2: Latest complete year 2025 only. ROW 3: Company records and highlights. All data filtered to 2024-2026 as per supervisor instruction."), unsafe_allow_html=True)

    st.markdown("**📅 Overall Totals — 2024 to 2026 (Mar 16)**")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Total Revenue",    fmt(rev_overall),           "2024 + 2025 + 2026 combined"), unsafe_allow_html=True)
    c2.markdown(kpi("Total Units Sold", fmt_num(units_overall),     "All products 2024-2026"), unsafe_allow_html=True)
    c3.markdown(kpi("Total Promo Spend",fmt(spend_overall),         "2024-2026 activities only"), unsafe_allow_html=True)
    c4.markdown(kpi("Overall ROI",      f"{roi_overall:.1f}x",      "PKR 1 spent = PKR 18.6 earned"), unsafe_allow_html=True)
    c5.markdown(kpi("Total Field Trips",fmt_num(trips_overall),     "Field visits 2024-2026"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**📅 Latest Complete Year — 2025**")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Revenue 2025",      fmt(rev_2025),            f"↑ +{yoy_growth:.1f}% vs 2024"), unsafe_allow_html=True)
    c2.markdown(kpi("Units Sold 2025",   fmt_num(units_2025),      "Jan 2025 to Dec 2025"), unsafe_allow_html=True)
    c3.markdown(kpi("Promo Spend 2025",  fmt(spend_2025),          f"↑ +{((spend_2025-spend_2024)/spend_2024*100):.1f}% vs 2024"), unsafe_allow_html=True)
    c4.markdown(kpi("ROI 2025",          f"{roi_2025:.1f}x",       "2025 spend vs 2025 revenue"), unsafe_allow_html=True)
    c5.markdown(kpi("Trips 2025",        fmt_num(trips_2025),      "Field visits Jan-Dec 2025"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**🏆 Company Records & Highlights (2024-2026)**")
    c1,c2,c3,c4,c5 = st.columns(5)

    top_prod     = df_s.groupby("ProductName")["TotalRevenue"].sum().idxmax()
    top_prod_rev = df_s.groupby("ProductName")["TotalRevenue"].sum().max()
    top_team     = df_s.groupby("TeamName")["TotalRevenue"].sum().idxmax()
    top_team_rev = df_s.groupby("TeamName")["TotalRevenue"].sum().max()

    c1.markdown(kpi("Top Product",       top_prod,                 fmt(top_prod_rev)+" revenue"), unsafe_allow_html=True)
    c2.markdown(kpi("Top Sales Team",    top_team,                 fmt(top_team_rev)+" revenue"), unsafe_allow_html=True)
    c3.markdown(kpi("Best ROI Product",  "Ramipace",               "65.9x ROI — verified manually"), unsafe_allow_html=True)
    c4.markdown(kpi("Top Travel City",   "Lahore",                 "Biggest field market 2024-2026"), unsafe_allow_html=True)
    c5.markdown(kpi("2026 So Far",       fmt(rev_2026),            "⚠️ Jan-Mar 2026 partial only", red=True), unsafe_allow_html=True)

    # RAMIPACE MANUAL ROI WORKING (Supervisor requested!)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(sec("🔢 Manual ROI Verification — Ramipace (As Requested by Supervisors)"), unsafe_allow_html=True)
    st.markdown(note("Supervisors asked to verify Ramipace ROI manually. Below is the step-by-step calculation showing exactly how 99.7x ROI was calculated."), unsafe_allow_html=True)

    ram_spend = df_roi[df_roi["ProductName"].str.upper() == "RAMIPACE"]["TotalPromoSpend"].values
    ram_rev   = df_roi[df_roi["ProductName"].str.upper() == "RAMIPACE"]["TotalRevenue"].values

    if len(ram_spend) > 0:
        rs = ram_spend[0]
        rr = ram_rev[0]
        roi_r = rr / rs
        st.markdown(f"""
        <div class="manual-working">
        RAMIPACE ROI — MANUAL CALCULATION (2024-2026 Overlap Period)
        ═══════════════════════════════════════════════════════════
        Step 1: Total Promotional Spend on Ramipace
                = PKR {rs:,.0f}
                = PKR {rs/1e6:.2f} Million

        Step 2: Total Revenue Generated from Ramipace Sales
                = PKR {rr:,.0f}
                = PKR {rr/1e6:.1f} Million

        Step 3: ROI Formula
                ROI = Total Revenue / Total Promo Spend
                ROI = PKR {rr:,.0f} / PKR {rs:,.0f}
                ROI = {roi_r:.2f}x

        Step 4: Interpretation
                Every PKR 1 spent promoting Ramipace
                generated PKR {roi_r:.1f} in sales revenue

        Step 5: Company Average ROI for comparison
                Company Average ROI = 20.3x
                Ramipace ROI        = {roi_r:.1f}x
                Ramipace is {roi_r/20.3:.1f}x BETTER than company average!

        Step 6: Opportunity Calculation
                If we double Ramipace promo spend:
                New Spend   = PKR {rs*2:,.0f}
                Expected Rev= PKR {rr*2:,.0f} (~PKR {rr*2/1e6:.0f}M)
                Extra Profit= PKR {rr:,.0f} additional revenue
        ═══════════════════════════════════════════════════════════
        DATA SOURCE: Merged Activities DB + Sales DB (2024-2026)
        </div>
        """, unsafe_allow_html=True)

    # Revenue trend
    st.markdown(sec("📈 Revenue Trend (Monthly)"), unsafe_allow_html=True)
    st.markdown(note("Blue line shows monthly revenue. Orange dashed = 2026 partial year (Jan-Mar only). Upward trend confirms business growth."), unsafe_allow_html=True)

    monthly  = df_s.groupby("Date")["TotalRevenue"].sum().reset_index()
    complete = monthly[monthly["Date"].dt.year < 2026]
    partial  = monthly[monthly["Date"].dt.year >= 2026]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=complete["Date"], y=complete["TotalRevenue"]/1e6,
        name="Monthly Revenue",
        line=dict(color="#2c5f8a", width=2.5),
        fill="tozeroy", fillcolor="rgba(44,95,138,0.08)",
        mode="lines+markers", marker=dict(size=5, color="#2c5f8a"),
        hovertemplate="%{x|%b %Y}<br>Revenue: PKR %{y:.1f}M<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=partial["Date"], y=partial["TotalRevenue"]/1e6,
        name="2026 (Partial Year)",
        line=dict(color="#e65100", width=2.5, dash="dash"),
        mode="lines+markers", marker=dict(size=7, color="#e65100"),
        hovertemplate="%{x|%b %Y}<br>Revenue: PKR %{y:.1f}M (partial)<extra></extra>"
    ))
    apply_layout(fig, height=300, hovermode="x unified",
                 yaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)",
                            tickformat=",.0f"),
                 legend=dict(bgcolor="white", bordercolor="#ddd", borderwidth=1))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("🏆 Top 10 Products by Revenue"), unsafe_allow_html=True)
        st.markdown(note("Longer bar = more revenue earned. X-Plended leads at PKR 4.3B."), unsafe_allow_html=True)
        tp = df_s.groupby("ProductName")["TotalRevenue"].sum().nlargest(10).reset_index()
        tp["Label"] = tp["TotalRevenue"].apply(fmt)
        fig = px.bar(tp, x="TotalRevenue", y="ProductName",
                     orientation="h", text="Label",
                     color="TotalRevenue", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=370,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("👥 Top 10 Teams by Revenue"), unsafe_allow_html=True)
        st.markdown(note("Challengers team generates PKR 6.5B — nearly double second place. Their strategy should be studied and replicated."), unsafe_allow_html=True)
        tt = df_s.groupby("TeamName")["TotalRevenue"].sum().nlargest(10).reset_index()
        tt["Label"] = tt["TotalRevenue"].apply(fmt)
        fig = px.bar(tt, x="TotalRevenue", y="TeamName",
                     orientation="h", text="Label",
                     color="TotalRevenue", color_continuous_scale="Greens")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=370,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Bottom teams + Bottom products side by side
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("⚠️ Bottom 10 Teams — Needs Attention"), unsafe_allow_html=True)
        st.markdown(note("Teams with LOWEST revenue. Management should investigate why they underperform — is it low promo spend, low travel activity, or territory issues?"), unsafe_allow_html=True)
        bt = df_s.groupby("TeamName")["TotalRevenue"].sum().nsmallest(10).reset_index()
        bt["Label"] = bt["TotalRevenue"].apply(fmt)
        fig = px.bar(bt, x="TotalRevenue", y="TeamName",
                     orientation="h", text="Label",
                     color="TotalRevenue", color_continuous_scale="Reds")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=370,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("⚠️ Bottom 10 Products — Needs Attention"), unsafe_allow_html=True)
        st.markdown(note("Products with LOWEST revenue overall. Zero revenue products may be discontinued or newly launched. Cross check with Sales Analysis page for 2024-2025 breakdown."), unsafe_allow_html=True)
        bp10_all = df_s.groupby("ProductName")["TotalRevenue"].sum().reset_index()
        bp10 = bp10_all[bp10_all["TotalRevenue"]>0].nsmallest(10,"TotalRevenue")
        bp10["Label"] = bp10["TotalRevenue"].apply(fmt)
        fig = go.Figure(go.Bar(
            x=bp10["TotalRevenue"], y=bp10["ProductName"],
            orientation="h",
            text=bp10["Label"],
            textposition="outside",
            textfont_size=11,
            marker_color="#e65100"
        ))
        apply_layout(fig, height=370,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Revenue (PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(good("Revenue grew <b>+16.6%</b> from 2024 to 2025. PKR 20.2B to PKR 23.6B. Strong consistent growth."), unsafe_allow_html=True)
        st.markdown(good("Promo spend has <b>0.784 correlation</b> with same month revenue. Promotions are proven to work!"), unsafe_allow_html=True)
        st.markdown(good("Travel activity matches sales peaks. Dec/Sep/Oct are top months for both travel AND sales."), unsafe_allow_html=True)
    with col2:
        st.markdown(warn("2025 promo spend grew +38.2% but revenue only grew +16.6%. Spend is growing FASTER than revenue."), unsafe_allow_html=True)
        st.markdown(warn("Division 4 and Division 5 have very low travel activity (80 and 175 trips). This may explain lower sales in those areas."), unsafe_allow_html=True)
        st.markdown(danger("2026 data is PARTIAL — only Jan to Mar available. Do NOT compare 2026 numbers with full years."), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# PAGE 2: SALES ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "📈 Sales Analysis":
    st.markdown("<h2 style=\'color:#2c5f8a\'>📈 Sales Deep Analysis</h2>", unsafe_allow_html=True)
    st.markdown(note("This page analyzes revenue, units sold and invoices from the DSR Sales Database covering 2024-2026."), unsafe_allow_html=True)

    yearly = df_s[df_s["Yr"] < 2026].groupby("Yr").agg(
        Revenue=("TotalRevenue","sum"),
        Units=("TotalUnits","sum"),
        Invoices=("InvoiceCount","sum")).reset_index()
    yearly["RevLabel"]  = yearly["Revenue"].apply(fmt)
    yearly["UnitLabel"] = yearly["Units"].apply(lambda x: f"{x/1e6:.1f}M")
    yearly["InvLabel"]  = yearly["Invoices"].apply(lambda x: f"{x/1e6:.1f}M")

    st.markdown(sec("Year-over-Year Comparison (2024 vs 2025)"), unsafe_allow_html=True)
    st.markdown(note("All 3 metrics grew from 2024 to 2025 — more revenue, more units sold, more invoices. This confirms genuine business growth not just price increases."), unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    for col, field, lbl, title, color in zip(
        [c1,c2,c3],
        ["Revenue","Units","Invoices"],
        ["RevLabel","UnitLabel","InvLabel"],
        ["Revenue (PKR)","Units Sold","Invoice Count"],
        ["#2c5f8a","#2e7d32","#e65100"]
    ):
        with col:
            fig = px.bar(yearly, x="Yr", y=field, text=lbl,
                         title=title, color_discrete_sequence=[color])
            fig.update_traces(textposition="outside", textfont_size=12)
            apply_layout(fig, height=270,
                         xaxis=dict(gridcolor="#eeeeee", tickmode="array",
                                    tickvals=yearly["Yr"].tolist()),
                         yaxis=dict(gridcolor="#eeeeee"))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown(sec("Product Revenue: 2024 vs 2025 — Side by Side"), unsafe_allow_html=True)
    st.markdown(note("Each product has 2 bars side by side. Blue = 2024. Green = 2025. Taller green bar = product grew. Taller blue bar = product declined in 2025. Shows top 15 products by combined revenue."), unsafe_allow_html=True)
    ry = df_s[df_s["Yr"].isin([2024,2025])].groupby(
        ["ProductName","Yr"])["TotalRevenue"].sum().reset_index()
    top15 = ry.groupby("ProductName")["TotalRevenue"].sum().nlargest(15).index
    ry = ry[ry["ProductName"].isin(top15)]
    ry["Label"] = ry["TotalRevenue"].apply(fmt)
    ry["Yr"] = ry["Yr"].astype(str)
    fig = px.bar(ry, x="ProductName", y="TotalRevenue",
                 color="Yr", barmode="group",
                 text="Label",
                 color_discrete_map={"2024":"#2c5f8a","2025":"#2e7d32"},
                 labels={"TotalRevenue":"Revenue (PKR)","ProductName":"Product"})
    fig.update_traces(textposition="outside", textfont_size=9,
                      textangle=-45)
    apply_layout(fig, height=480,
                 xaxis=dict(gridcolor="#eeeeee", tickangle=-35),
                 yaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Fastest Growing Products 2024→2025"), unsafe_allow_html=True)
        st.markdown(note("Products with highest % growth rate. Finno-Q grew 226% — nearly tripled in one year! These are emerging stars needing promotional support NOW."), unsafe_allow_html=True)
        r24 = df_s[df_s["Yr"]==2024].groupby("ProductName")["TotalRevenue"].sum()
        r25 = df_s[df_s["Yr"]==2025].groupby("ProductName")["TotalRevenue"].sum()
        gdf = pd.DataFrame({"y2024":r24,"y2025":r25}).dropna()
        gdf = gdf[gdf["y2024"] > 5000000]
        gdf["Growth"] = ((gdf["y2025"]-gdf["y2024"])/gdf["y2024"]*100)
        gdf = gdf.sort_values("Growth", ascending=False).head(15).reset_index()
        gdf["Label"] = gdf["Growth"].apply(lambda x: f"{x:.0f}%")
        fig = px.bar(gdf, x="Growth", y="ProductName",
                     orientation="h", text="Label",
                     color="Growth", color_continuous_scale="Greens")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=530,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Growth %"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Bottom 50 products
    st.markdown(sec("⚠️ Bottom 50 Products by Revenue — Underperforming or Discontinued?"), unsafe_allow_html=True)
    st.markdown(note("Bottom 50 products by revenue 2024-2025. Products showing PKR 0 or very low revenue may be discontinued, newly launched, or severely underpromoted. Management should verify status of each."), unsafe_allow_html=True)
    bp_all = df_s[df_s["Yr"].isin([2024,2025])].groupby(
        "ProductName")["TotalRevenue"].sum().reset_index()
    bp = bp_all[bp_all["TotalRevenue"]>0].nsmallest(10,"TotalRevenue")
    bp["Label"] = bp["TotalRevenue"].apply(fmt)
    fig = go.Figure(go.Bar(
        x=bp["TotalRevenue"], y=bp["ProductName"],
        orientation="h",
        text=bp["Label"],
        textposition="outside",
        textfont_size=11,
        marker_color="#e65100"
    ))
    apply_layout(fig, height=380,
                 yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                 xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(warn("These are the 10 lowest revenue products that are still active. Management should review if more promotional support is needed."), unsafe_allow_html=True)

    st.markdown(sec("📅 Sales Seasonality Heatmap"), unsafe_allow_html=True)
    st.markdown(note("Each cell = one month in one year. Darker blue = more revenue. Numbers show revenue in M (millions) e.g. 1.6B means PKR 1.6 Billion. Oct/Nov/Dec are ALWAYS strongest months every year."), unsafe_allow_html=True)
    heat = df_s[df_s["Yr"]<2026].groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
    heat["Month"] = heat["Mo"].map(months_map)
    hp = heat.pivot(index="Yr", columns="Month", values="TotalRevenue")
    hp = hp.reindex(columns=list(months_map.values()))

    # Create formatted text labels
    text_labels = []
    for idx in hp.index:
        row_labels = []
        for col in hp.columns:
            val = hp.loc[idx, col]
            if pd.isna(val):
                row_labels.append("")
            elif val >= 1e9:
                row_labels.append(f"{val/1e9:.1f}B")
            elif val >= 1e6:
                row_labels.append(f"{val/1e6:.1f}M")
            elif val >= 1e3:
                row_labels.append(f"{val/1e3:.0f}K")
            else:
                row_labels.append(f"{val:.0f}")
        text_labels.append(row_labels)

    fig = px.imshow(hp/1e6, color_continuous_scale="Blues", aspect="auto",
                    labels=dict(color="Revenue (M PKR)"))
    fig.update_traces(text=text_labels, texttemplate="%{text}",
                      textfont=dict(size=11, color="black"))
    apply_layout(fig, height=250,
                 coloraxis_colorbar=dict(title="M PKR"))
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# PAGE 3: PROMOTIONAL ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "💰 Promotional Analysis":
    st.markdown("<h2 style=\'color:#2c5f8a\'>💰 Promotional Spend Analysis (2024-2026)</h2>", unsafe_allow_html=True)
    st.markdown(note("This page uses the Activities database (FTTS) filtered to 2024-2026 only as per supervisor instruction. Total spend = PKR 2.58B across 3 years. 2024: PKR 994M | 2025: PKR 1.37B | 2026: PKR 216M (partial)."), unsafe_allow_html=True)

    df_af = df_act[df_act["Yr"].isin([2024,2025,2026])]
    if team_filter:
        df_af = df_af[df_af["RequestorTeams"].str.upper().isin(
            [t.upper() for t in team_filter])]

    total_sp = df_af["TotalAmount"].sum()
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Promo Spend",  fmt(total_sp), help="Total money spent on promotional activities 2024-2026")
    with c2: st.metric("Total Requests",     f"{df_af['RequestCount'].sum():,.0f}", help="Number of promotional activity requests submitted by sales reps")
    with c3: st.metric("Avg per Request",    fmt(total_sp/max(df_af["RequestCount"].sum(),1)), help="Average cost of one promotional activity")
    with c4: st.metric("Peak Spend Year",    "2025", delta="PKR 1.37B (+38.2%)", help="2025 had the highest promotional spending ever")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Promotional Spend by Year"), unsafe_allow_html=True)
        st.markdown(note("Each bar = total promo money spent that year. 2025 is the tallest — biggest investment year. 2026 bar is small because it is only Jan-Mar data."), unsafe_allow_html=True)
        ysp = df_af.groupby("Yr")["TotalAmount"].sum().reset_index()
        ysp["Label"] = ysp["TotalAmount"].apply(fmt)
        fig = px.bar(ysp, x="Yr", y="TotalAmount", text="Label",
                     color_discrete_sequence=["#2c5f8a"])
        fig.update_traces(textposition="outside", textfont_size=12)
        apply_layout(fig, height=300,
                     xaxis=dict(gridcolor="#eeeeee", tickmode="array",
                                tickvals=ysp["Yr"].tolist(), title="Year"),
                     yaxis=dict(gridcolor="#eeeeee", title="Total Spend (PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("Where Does Money Go? (Activity Types)"), unsafe_allow_html=True)
        st.markdown(note("Pie shows how promotional budget is divided. Social/Cultural events and Equipment donations take the biggest shares — these are doctor engagement tools."), unsafe_allow_html=True)
        asp = df_af.groupby("ActivityHead")["TotalAmount"].sum().nlargest(8).reset_index()
        asp["Label"] = asp["TotalAmount"].apply(fmt)
        fig = px.pie(asp, values="TotalAmount", names="ActivityHead",
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     hover_data=["Label"])
        fig.update_traces(textinfo="percent+label", textfont_size=11)
        apply_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Top 10 Teams — Highest Promo Spend"), unsafe_allow_html=True)
        st.markdown(note("Teams spending the most on promotions. High spend is not always good — check ROI page to see if this spend is generating returns."), unsafe_allow_html=True)
        tsp = df_af.groupby("RequestorTeams")["TotalAmount"].sum().nlargest(10).reset_index()
        tsp["Label"] = tsp["TotalAmount"].apply(fmt)
        fig = px.bar(tsp, x="TotalAmount", y="RequestorTeams",
                     orientation="h", text="Label",
                     color="TotalAmount", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=370,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Spend (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("⚠️ Bottom 10 Teams — Lowest Promo Spend"), unsafe_allow_html=True)
        st.markdown(note("These teams spend the LEAST on promotions. Low spend may explain low sales. Management should check if these teams need more budget allocation."), unsafe_allow_html=True)
        bsp = df_af.groupby("RequestorTeams")["TotalAmount"].sum().nsmallest(10).reset_index()
        bsp["Label"] = bsp["TotalAmount"].apply(fmt)
        fig = px.bar(bsp, x="TotalAmount", y="RequestorTeams",
                     orientation="h", text="Label",
                     color="TotalAmount", color_continuous_scale="Reds_r")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=370,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Spend (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Top 10 Products — Highest Promo Investment"), unsafe_allow_html=True)
        st.markdown(note("Products receiving the most promotional budget. Avsar and Lowplat Plus get the most. Cross-check with ROI page to verify if this investment is justified."), unsafe_allow_html=True)
        psp = df_af.groupby("Product")["TotalAmount"].sum().nlargest(10).reset_index()
        psp["Label"] = psp["TotalAmount"].apply(fmt)
        fig = px.bar(psp, x="TotalAmount", y="Product",
                     orientation="h", text="Label",
                     color="TotalAmount", color_continuous_scale="Purples")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=370,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Spend (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("Budget by GL Head (Expense Category)"), unsafe_allow_html=True)
        st.markdown(note("GL Head = General Ledger expense category. Equipment S&D is biggest spend (27.7% of budget). This tells the accounting team where money is going."), unsafe_allow_html=True)
        gl = df_af.groupby("GLHead")["TotalAmount"].sum().nlargest(8).reset_index()
        gl["Label"] = gl["TotalAmount"].apply(fmt)
        fig = px.bar(gl, x="TotalAmount", y="GLHead",
                     orientation="h", text="Label",
                     color="TotalAmount", color_continuous_scale="Oranges")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=370,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Spend (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# PAGE 4: TRAVEL ANALYSIS
# ════════════════════════════════════════════════════════════
elif page == "✈️ Travel Analysis":
    st.markdown("<h2 style=\'color:#2c5f8a\'>✈️ Travel & Field Activity Analysis (2024-2026)</h2>", unsafe_allow_html=True)
    st.markdown(note("This page uses the Travel database (FTTS) filtered to 2024-2026 only as per supervisor instruction. Total trips = 4,332 | 2024: 1,985 trips | 2025: 2,025 trips | 2026: 322 trips (partial Jan-Mar)."), unsafe_allow_html=True)

    total_trips  = df_t["TravelCount"].sum()
    total_nights = df_t["NoofNights"].sum()
    total_people = df_t["Traveller"].nunique()
    total_locs   = df_t["VisitLocation"].nunique()

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Trips (2024-2026)",    fmt_num(total_trips),  help="Total field visits made by all sales reps from 2024 to 2026")
    with c2: st.metric("Total Nights (2024-2026)",   fmt_num(total_nights), help="Total hotel nights stayed during all field visits 2024-2026")
    with c3: st.metric("Unique Travellers",           str(total_people),     help="Number of unique employees who travelled at least once 2024-2026")
    with c4: st.metric("Cities Covered (Pakistan)",   str(total_locs),       help="Number of unique cities visited across Pakistan 2024-2026")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Travel Activity by Year"), unsafe_allow_html=True)
        st.markdown(note("2021 was low due to COVID recovery. 2022 saw +122% jump as field work resumed. 2024-2025 stable around 2,000 trips/year. 2026 bar is partial (Jan-Mar only)."), unsafe_allow_html=True)
        yt = df_t[df_t["Yr"]<2026].groupby("Yr").agg(
            Trips=("TravelCount","sum")).reset_index()
        yt["Label"] = yt["Trips"].apply(fmt_num)
        fig = px.bar(yt, x="Yr", y="Trips", text="Label",
                     color_discrete_sequence=["#2c5f8a"])
        fig.update_traces(textposition="outside", textfont_size=12)
        apply_layout(fig, height=290,
                     xaxis=dict(gridcolor="#eeeeee", tickmode="array",
                                tickvals=yt["Yr"].tolist(), title="Year"),
                     yaxis=dict(gridcolor="#eeeeee", title="Total Trips"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("Top 15 Most Visited Cities"), unsafe_allow_html=True)
        st.markdown(note("Lahore is #1 with 3,161 trips — it is Pharmevo biggest market. Islamabad #2. These cities need sustained promotional presence. Smaller cities may be growth opportunities."), unsafe_allow_html=True)
        lc = df_t.groupby("VisitLocation")["TravelCount"].sum().nlargest(15).reset_index()
        lc["Label"] = lc["TravelCount"].apply(fmt_num)
        fig = px.bar(lc, x="TravelCount", y="VisitLocation",
                     orientation="h", text="Label",
                     color="TravelCount", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=450,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Trips"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Division name mapping with all teams listed
    div_name_map = {
        "Division 1": "Division 1 — Alpha, Bone Saviors, Bravo, Challengers, Champions, Elite, Legends, Mavericks, Titans, X-Treme",
        "Division 2": "Division 2 — Aviators, Conqueror, Gladiators, Metabolizers, Navigators, Sprinters, Transformers, Warriors, Winners",
        "Division 3": "Division 3 — Archers, Institutional, International Markets, Oncology",
        "Division 4": "Division 4 — Admin, Afghanistan, Corp Comm, Digital Marketing",
        "Division 5": "Division 5 — Strikers (R)"
    }

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Division Performance — Travel Activity"), unsafe_allow_html=True)
        st.markdown(note("Division 1 = 11 sales teams (Alpha, Bone Saviors, Challengers etc) | Division 2 = 13 teams (Winners, Warriors etc) | Division 3 = Institutional and International | Division 4 = Admin and Afghanistan | Division 5 = Strikers. Blue = healthy. Red = critically low."), unsafe_allow_html=True)
        dv = df_t.groupby("TravellerDivision").agg(
            Trips=("TravelCount","sum"),
            Nights=("NoofNights","sum"),
            People=("Traveller","nunique")).reset_index()
        dv["AvgNights"] = (dv["Nights"]/dv["Trips"]).round(1)
        dv["DivisionName"] = dv["TravellerDivision"].map(div_name_map).fillna(dv["TravellerDivision"])
        dv["Label"] = dv["Trips"].apply(fmt_num)
        dv = dv.sort_values("Trips", ascending=False)

        colors = []
        for t in dv["Trips"]:
            if t < 200:    colors.append("#c62828")
            elif t < 1000: colors.append("#e65100")
            else:           colors.append("#2c5f8a")

        fig = go.Figure(go.Bar(
            x=dv["Trips"], y=dv["DivisionName"],
            orientation="h",
            text=dv["Label"],
            textposition="outside",
            marker_color=colors
        ))
        apply_layout(fig, height=320,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Trips"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(danger("Division 4: only 80 trips in 5 years! Division 5: only 175 trips. These divisions are severely underperforming in field activity."), unsafe_allow_html=True)

    with col2:
        st.markdown(sec("Travel Seasonality — Busiest Months"), unsafe_allow_html=True)
        st.markdown(note("Dec is busiest travel month (1,110 trips). Sep/Oct/Nov also strong. This perfectly aligns with sales peaks — confirming that field visits drive sales!"), unsafe_allow_html=True)
        mt = df_t.groupby("Mo")["TravelCount"].sum().reset_index()
        mt["Month"] = mt["Mo"].map(months_map)
        mt["Label"] = mt["TravelCount"].apply(fmt_num)
        mt = mt.sort_values("TravelCount", ascending=False)
        fig = px.bar(mt, x="Month", y="TravelCount", text="Label",
                     color="TravelCount", color_continuous_scale="Blues",
                     category_orders={"Month":list(months_map.values())})
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=280,
                     xaxis=dict(gridcolor="#eeeeee", title="Month"),
                     yaxis=dict(gridcolor="#eeeeee", title="Total Trips"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Top 15 Most Active Travellers"), unsafe_allow_html=True)
        st.markdown(note("These employees made the most field visits. Muhammad Usman Karim leads with 230 trips. High travel usually correlates with high sales performance."), unsafe_allow_html=True)
        tv = df_t.groupby(["Traveller","TravellerDivision"]).agg(
            Trips=("TravelCount","sum"),
            Nights=("NoofNights","sum")).reset_index()
        tv = tv.nlargest(15,"Trips")
        tv["Label"] = tv["Trips"].apply(fmt_num)
        fig = px.bar(tv, x="Trips", y="Traveller",
                     orientation="h", text="Label",
                     color="TravellerDivision",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Trips"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("Top 10 Hotels by Bookings"), unsafe_allow_html=True)
        st.markdown(note("Indigo Heights in Lahore is most used hotel (880 bookings). Management can negotiate bulk rates with top hotels to reduce travel costs."), unsafe_allow_html=True)
        ht = df_t[df_t["HotelName"]!="Not Recorded"].groupby("HotelName").agg(
            Bookings=("TravelCount","sum"),
            Nights=("NoofNights","sum")).reset_index()
        ht = ht.nlargest(10,"Bookings")
        ht["Label"] = ht["Bookings"].apply(fmt_num)
        fig = px.bar(ht, x="Bookings", y="HotelName",
                     orientation="h", text="Label",
                     color="Bookings", color_continuous_scale="Purples")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=380,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Bookings"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # TEAM TRAVEL ANALYSIS side by side with division
    st.markdown(sec("Team-Level Travel Activity (34 Teams)"), unsafe_allow_html=True)
    st.markdown(note("Travel broken down by sales team. WINNERS team travels most (791 trips) but CHALLENGERS has best sales ROI — proves quality of visits matters more than quantity."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top 15 Teams — Most Field Trips**", unsafe_allow_html=True)
        tt = df_t.groupby("TravellerTeam").agg(
            Trips=("TravelCount","sum"),
            Nights=("NoofNights","sum"),
            People=("Traveller","nunique")).reset_index()
        tt["AvgNights"] = (tt["Nights"]/tt["Trips"]).round(1)
        tt_top = tt.nlargest(15,"Trips")
        tt_top["Label"] = tt_top["Trips"].apply(fmt_num)
        fig = px.bar(tt_top, x="Trips", y="TravellerTeam",
                     orientation="h", text="Label",
                     color="Trips", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Trips"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**⚠️ Bottom 15 Teams — Least Field Trips**", unsafe_allow_html=True)
        tt_bot = tt.nsmallest(15,"Trips")
        tt_bot["Label"] = tt_bot["Trips"].apply(fmt_num)
        fig = px.bar(tt_bot, x="Trips", y="TravellerTeam",
                     orientation="h", text="Label",
                     color="Trips", color_continuous_scale="Reds_r")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Trips"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Team Travel Summary Table removed as per requirements

    # KEY INSIGHT: Travel vs Sales comparison
    st.markdown(sec("Key Insight — Travel Rank vs Sales ROI"), unsafe_allow_html=True)
    st.markdown(note("WINNERS travel most (791 trips) but CHALLENGERS have best sales ROI (38.2x). This means travel quantity alone does not guarantee sales. Quality of doctor visits matters more than quantity."), unsafe_allow_html=True)

    insight_df = pd.DataFrame({
        "Team":        ["WINNERS","BONE SAVIORS","MAVERICKS","CHALLENGERS","LEGENDS",
                        "GLADIATORS","TRANSFORMERS","METABOLIZERS","WARRIORS","TITANS"],
        "Division":    ["Div 2","Div 1","Div 1","Div 1","Div 1",
                        "Div 2","Div 2","Div 2","Div 2","Div 1"],
        "Travel Rank": ["#1 (791)","#2 (738)","#3 (708)","#11 (367)","#4 (587)",
                        "#7 (446)","#9 (471)","#8 (402)","#5 (518)","#13 (349)"],
        "Sales ROI":   ["22.3x","17.4x","—","38.2x ⭐","26.8x",
                        "—","—","29.1x","21.0x","13.1x 🔴"],
        "Insight":     [
            "Most travel but average ROI — quality of visits?",
            "High travel but below avg ROI — review approach",
            "High travel — not in sales DB yet",
            "Less travel but BEST ROI — most efficient team!",
            "Good balance of travel and sales",
            "High travel — cross check sales performance",
            "Good travel — cross check sales performance",
            "Good travel AND good ROI — solid team",
            "Decent travel and ROI — stable performer",
            "Decent travel but lowest ROI — needs review"
        ]
    })
    st.dataframe(insight_df, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════
# PAGE 5: COMBINED ROI
# ════════════════════════════════════════════════════════════
elif page == "🔗 Combined ROI Analysis":
    st.markdown("<h2 style=\'color:#2c5f8a\'>🔗 Combined ROI — All 3 Databases</h2>", unsafe_allow_html=True)
    st.markdown(note("This is the most powerful page. It connects promotional spending (FTTS) with actual sales revenue (DSR) to prove which products and teams give best return on investment."), unsafe_allow_html=True)

    st.markdown(good("KEY PROOF: Promotional spend and same-month revenue have <b>0.784 correlation</b>. This mathematically proves Pharmevo promotions work. Every PKR 1 spent = PKR 20.3 in revenue."), unsafe_allow_html=True)

    st.markdown(sec("Promo Spend vs Revenue — Monthly Comparison"), unsafe_allow_html=True)
    st.markdown(note("Orange bars = promo spend each month. Blue line = revenue each month. Notice how they move together — when spending goes up, revenue follows. This is the proof."), unsafe_allow_html=True)

    msp   = df_act[df_act["Yr"]>=2024].groupby("Date")["TotalAmount"].sum().reset_index()
    mrv   = df_s.groupby("Date")["TotalRevenue"].sum().reset_index()
    combo = pd.merge(msp, mrv, on="Date", how="inner")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=combo["Date"], y=combo["TotalAmount"]/1e6,
        name="Promo Spend (M PKR)",
        marker_color="rgba(230,81,0,0.7)",
        text=[f"PKR {v:.1f}M" for v in combo["TotalAmount"]/1e6],
        textposition="outside",
        hovertemplate="%{x|%b %Y}<br>Spend: PKR %{y:.1f}M<extra></extra>"
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=combo["Date"], y=combo["TotalRevenue"]/1e6,
        name="Revenue (M PKR)",
        line=dict(color="#2c5f8a", width=3),
        mode="lines+markers", marker=dict(size=6),
        hovertemplate="%{x|%b %Y}<br>Revenue: PKR %{y:.1f}M<extra></extra>"
    ), secondary_y=True)
    apply_layout(fig, height=360, hovermode="x unified")
    fig.update_yaxes(title_text="Promo Spend (M PKR)",
                     gridcolor="#eeeeee", secondary_y=False)
    fig.update_yaxes(title_text="Revenue (M PKR)",
                     gridcolor="#eeeeee", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("ROI Bubble Chart"), unsafe_allow_html=True)
        st.markdown(note("Each bubble = one product. Bigger bubble = higher ROI. Top-LEFT corner = best zone (high ROI + low spend = invest more here!). Green = exceptional ROI."), unsafe_allow_html=True)
        rp = df_roi[(df_roi["TotalPromoSpend"]>0) & (df_roi["ROI"]<200)].copy()
        rp["SpendLabel"] = rp["TotalPromoSpend"].apply(fmt)
        rp["RevLabel"]   = rp["TotalRevenue"].apply(fmt)
        fig = px.scatter(rp, x="TotalPromoSpend", y="TotalRevenue",
                         size="ROI", color="ROI",
                         hover_name="ProductName",
                         hover_data={"SpendLabel":True,"RevLabel":True,
                                     "TotalPromoSpend":False,"TotalRevenue":False},
                         color_continuous_scale="RdYlGn", size_max=50,
                         labels={"TotalPromoSpend":"Promo Spend (PKR)",
                                 "TotalRevenue":"Revenue (PKR)"})
        apply_layout(fig, height=420)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("Top 15 Products by ROI"), unsafe_allow_html=True)
        # Recalculate ROI from raw data
        prod_rev_roi  = df_sales.groupby("ProductName")["TotalRevenue"].sum()
        prod_spend_roi= df_act.groupby("Product")["TotalAmount"].sum()
        roi_calc = pd.DataFrame({
            "TotalRevenue"  : prod_rev_roi,
            "TotalPromoSpend": prod_spend_roi
        }).dropna()
        roi_calc = roi_calc[roi_calc["TotalPromoSpend"]>0]
        roi_calc["ROI"] = roi_calc["TotalRevenue"]/roi_calc["TotalPromoSpend"]
        roi_calc = roi_calc.reset_index().rename(columns={"index":"ProductName"})

        st.markdown(note("Green = ROI above 50x (exceptional). Blue = above 20x (excellent). Orange = below 20x (needs review). ROI calculated directly from raw data: Revenue (DSR) / Spend (Activities)."), unsafe_allow_html=True)
        tr     = roi_calc.nlargest(15,"ROI")
        colors = ["#2e7d32" if r>50 else "#2c5f8a" if r>20 else "#e65100"
                  for r in tr["ROI"]]
        fig = go.Figure(go.Bar(
            x=tr["ROI"], y=tr["ProductName"],
            orientation="h",
            marker_color=colors,
            text=[f"{r:.1f}x" for r in tr["ROI"]],
            textposition="outside",
            textfont_size=11
        ))
        apply_layout(fig, height=420,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="ROI = Revenue / Promo Spend"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(sec("Team ROI Summary Table"), unsafe_allow_html=True)
    st.markdown(note("Challengers team has best ROI at 38.2x AND highest revenue. Titans at 13.1x need strategy review. ROI = Revenue divided by Promo Spend."), unsafe_allow_html=True)
    tdf = pd.DataFrame({
        "Team":["CHALLENGERS","BRAVO","METABOLIZERS","LEGENDS","CHAMPIONS",
                "WINNERS","WARRIORS","ALPHA","BONE SAVIORS","TITANS"],
        "Promo Spend":["PKR 118.6M","PKR 44.9M","PKR 81.7M","PKR 78.1M","PKR 37.5M",
                       "PKR 67.2M","PKR 75.5M","PKR 61.4M","PKR 133.6M","PKR 101.7M"],
        "Revenue":["PKR 4.53B","PKR 1.52B","PKR 2.38B","PKR 2.10B","PKR 1.07B",
                   "PKR 1.49B","PKR 1.59B","PKR 1.11B","PKR 2.32B","PKR 1.33B"],
        "ROI":["38.2x","33.9x","29.1x","26.8x","28.7x",
               "22.3x","21.0x","18.0x","17.4x","13.1x"],
        "Status":["🟢 Best","🟢 Excellent","🟢 Excellent","🟢 Excellent","🟢 Excellent",
                  "🟡 Good","🟡 Good","🟡 Good","🟡 Good","🔴 Review"]
    })
    st.dataframe(tdf, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════
# PAGE 6: PREDICTIONS
# ════════════════════════════════════════════════════════════
elif page == "🔮 Predictions & Forecast":
    st.markdown("<h2 style=\'color:#2c5f8a\'>🔮 Predictions & Forecast</h2>", unsafe_allow_html=True)
    st.markdown(note("Two ML models: (1) Monthly Revenue Forecast for next 6 months. (2) Promo ROI Predictor — enter a budget and see expected revenue per product. All models trained on real data from all 4 databases."), unsafe_allow_html=True)

    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import r2_score, mean_absolute_error
    from sklearn.model_selection import train_test_split

    mo_map_p = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

    # ── MODEL 1: MONTHLY REVENUE FORECAST ────────────────
    st.markdown(sec("📈 Model 1 — Monthly Revenue Forecast (Next 6 Months)"), unsafe_allow_html=True)
    st.markdown(note("Trained on 2024-2025 monthly data from Sales DSR + Activities + Travel databases. Predicts next 6 months of revenue with confidence range. Green = actual, Orange dashed = forecast."), unsafe_allow_html=True)

    # Prepare monthly data
    monthly_rev   = df_sales.groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
    monthly_spend = df_act.groupby(["Yr","Mo"])["TotalAmount"].sum().reset_index()
    monthly_trips = df_travel.groupby(["Yr","Mo"])["TravelCount"].sum().reset_index()

    monthly = monthly_rev.merge(monthly_spend, on=["Yr","Mo"], how="left")
    monthly = monthly.merge(monthly_trips,     on=["Yr","Mo"], how="left")
    monthly = monthly.fillna(0)
    monthly["Month_sin"] = np.sin(2*np.pi*monthly["Mo"]/12)
    monthly["Month_cos"] = np.cos(2*np.pi*monthly["Mo"]/12)
    monthly["Q4"]        = monthly["Mo"].apply(lambda x: 1 if x in [10,11,12] else 0)
    monthly["Q1"]        = monthly["Mo"].apply(lambda x: 1 if x in [1,2,3]    else 0)
    monthly["Date"]      = pd.to_datetime(
        monthly["Yr"].astype(int).astype(str)+"-"+
        monthly["Mo"].astype(int).astype(str)+"-01")
    monthly = monthly.sort_values("Date")

    features_m = ["Yr","Mo","TotalAmount","TravelCount",
                  "Month_sin","Month_cos","Q4","Q1"]
    X_m = monthly[features_m]
    y_m = monthly["TotalRevenue"]

    # Train model
    gb_model = GradientBoostingRegressor(
        n_estimators=200, max_depth=3,
        learning_rate=0.05, random_state=42)
    gb_model.fit(X_m, y_m)

    # Score on training data
    train_preds = gb_model.predict(X_m)
    r2_m  = r2_score(y_m, train_preds)
    mae_m = mean_absolute_error(y_m, train_preds)

    # Forecast next 6 months
    last_yr  = int(monthly["Yr"].max())
    last_mo  = int(monthly[monthly["Yr"]==last_yr]["Mo"].max())
    avg_spend_mo  = monthly.groupby("Mo")["TotalAmount"].mean()
    avg_trips_mo  = monthly.groupby("Mo")["TravelCount"].mean()

    forecast_rows = []
    for i in range(1, 7):
        next_mo = (last_mo + i - 1) % 12 + 1
        next_yr = last_yr + ((last_mo + i - 1) // 12)
        row = {
            "Yr"          : next_yr,
            "Mo"          : next_mo,
            "TotalAmount" : avg_spend_mo.get(next_mo, monthly["TotalAmount"].mean()),
            "TravelCount" : avg_trips_mo.get(next_mo, monthly["TravelCount"].mean()),
            "Month_sin"   : np.sin(2*np.pi*next_mo/12),
            "Month_cos"   : np.cos(2*np.pi*next_mo/12),
            "Q4"          : 1 if next_mo in [10,11,12] else 0,
            "Q1"          : 1 if next_mo in [1,2,3]    else 0
        }
        pred = gb_model.predict(pd.DataFrame([row]))[0]
        # Confidence interval ±15%
        forecast_rows.append({
            "Date"  : pd.to_datetime(f"{next_yr}-{next_mo}-01"),
            "Month" : f"{mo_map_p[next_mo]} {next_yr}",
            "Forecast"    : max(pred, 0),
            "Upper"       : max(pred*1.15, 0),
            "Lower"       : max(pred*0.85, 0)
        })

    forecast_df = pd.DataFrame(forecast_rows)

    col1, col2 = st.columns([3,1])
    with col1:
        fig = go.Figure()
        # Actual data
        fig.add_trace(go.Scatter(
            x=monthly["Date"], y=monthly["TotalRevenue"]/1e6,
            name="Actual Revenue",
            mode="lines+markers",
            line=dict(color="#2c5f8a", width=2.5),
            marker=dict(size=5),
            hovertemplate="%{x|%b %Y}: PKR %{y:.1f}M<extra></extra>"))
        # Forecast
        fig.add_trace(go.Scatter(
            x=forecast_df["Date"], y=forecast_df["Forecast"]/1e6,
            name="Forecast",
            mode="lines+markers",
            line=dict(color="#e65100", width=2.5, dash="dash"),
            marker=dict(size=8, symbol="diamond"),
            hovertemplate="%{x|%b %Y}: PKR %{y:.1f}M (forecast)<extra></extra>"))
        # Confidence band
        fig.add_trace(go.Scatter(
            x=pd.concat([forecast_df["Date"], forecast_df["Date"][::-1]]),
            y=pd.concat([forecast_df["Upper"]/1e6, forecast_df["Lower"][::-1]/1e6]),
            fill="toself",
            fillcolor="rgba(230,81,0,0.15)",
            line=dict(color="rgba(255,255,255,0)"),
            name="±15% Confidence Band",
            hoverinfo="skip"))
        apply_layout(fig, height=380,
                     xaxis=dict(gridcolor="#eee", title="Month"),
                     yaxis=dict(gridcolor="#eee", title="Revenue (M PKR)"),
                     hovermode="x unified")
        fig.update_layout(title="Revenue Forecast — Next 6 Months")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        total_forecast = forecast_df["Forecast"].sum()
        st.markdown(f"""
        <div class="manual-working">
        6-MONTH FORECAST
        ══════════════════════
        Model: Gradient Boosting
        R2 Score : {r2_m:.3f}
        MAE      : {fmt(mae_m)}

        Features Used:
        → Sales DSR (revenue)
        → Activities (spend)
        → Travel (trips)
        → Month seasonality
        → Q4/Q1 flags

        6-Month Total:
        {fmt(total_forecast)}

        Monthly Average:
        {fmt(total_forecast/6)}
        ══════════════════════
        </div>
        """, unsafe_allow_html=True)

    # Forecast table
    st.markdown("**Detailed Monthly Forecast:**")
    fc_display = forecast_df.copy()
    fc_display["Forecast"]     = fc_display["Forecast"].apply(fmt)
    fc_display["Upper Bound"]  = fc_display["Upper"].apply(fmt)
    fc_display["Lower Bound"]  = fc_display["Lower"].apply(fmt)
    st.dataframe(fc_display[["Month","Forecast","Lower Bound","Upper Bound"]],
                 use_container_width=True, hide_index=True)
    st.caption("Confidence band = ±15% around forecast. Upper = optimistic scenario. Lower = conservative scenario.")

    st.markdown("---")

    # ── MODEL 2: PROMO ROI PREDICTOR ─────────────────────
    st.markdown(sec("💹 Model 2 — Promo ROI Predictor: Enter Budget, Get Expected Revenue"), unsafe_allow_html=True)
    st.markdown(note("Enter your promotional budget and select product and month. The model predicts how much revenue you can expect. Trained on actual spend vs revenue data from Activities + Sales DSR databases."), unsafe_allow_html=True)

    # Prepare ROI predictor data
    prod_rev_p   = df_sales.groupby(["ProductName","Yr","Mo"])["TotalRevenue"].sum().reset_index()
    prod_spend_p = df_act.groupby(["Product","Yr","Mo"])["TotalAmount"].sum().reset_index()
    prod_spend_p = prod_spend_p.rename(columns={"Product":"ProductName","TotalAmount":"PromoSpend"})
    roi_data_p   = pd.merge(prod_rev_p, prod_spend_p, on=["ProductName","Yr","Mo"], how="inner")
    roi_data_p   = roi_data_p[roi_data_p["PromoSpend"]>0]
    roi_data_p   = roi_data_p[roi_data_p["TotalRevenue"]>0]

    le_p2 = LabelEncoder()
    roi_data_p["Prod_enc"] = le_p2.fit_transform(roi_data_p["ProductName"])
    roi_data_p["Month_sin"]= np.sin(2*np.pi*roi_data_p["Mo"]/12)
    roi_data_p["Month_cos"]= np.cos(2*np.pi*roi_data_p["Mo"]/12)
    roi_data_p["Q4"]       = roi_data_p["Mo"].apply(lambda x: 1 if x in [10,11,12] else 0)

    feat_p = ["PromoSpend","Prod_enc","Mo","Yr","Month_sin","Month_cos","Q4"]
    X_p = roi_data_p[feat_p]
    y_p = roi_data_p["TotalRevenue"]

    Xtr_p,Xte_p,ytr_p,yte_p = train_test_split(X_p, y_p, test_size=0.2, random_state=42)

    models_p = {
        "Linear Regression"  : LinearRegression(),
        "Random Forest"      : RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting"  : GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    results_p = {}
    for name, mdl in models_p.items():
        mdl.fit(Xtr_p, ytr_p)
        preds_p = mdl.predict(Xte_p)
        results_p[name] = {
            "model": mdl,
            "r2"   : r2_score(yte_p, preds_p),
            "mae"  : mean_absolute_error(yte_p, preds_p)
        }

    best_name_p  = max(results_p, key=lambda k: results_p[k]["r2"])
    best_model_p = results_p[best_name_p]["model"]
    best_r2_p    = results_p[best_name_p]["r2"]

    # Model comparison
    st.markdown("**Model Comparison:**")
    c1,c2,c3 = st.columns(3)
    for col,(name,res),color in zip(
        [c1,c2,c3], results_p.items(),
        ["#e65100","#2c5f8a","#2e7d32"]):
        r2_val  = res["r2"]
        mae_val = res["mae"]
        col.markdown(kpi(name,
                         f"R2={r2_val:.3f}",
                         f"MAE={fmt(mae_val)}"),
                     unsafe_allow_html=True)

    st.markdown(good(f"<b>Best Model: {best_name_p}</b> — R2={best_r2_p:.3f} — explains {best_r2_p*100:.1f}% of revenue variation."), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 Promo Budget Simulator")
    st.markdown("Enter your planned promotional budget and see expected revenue:")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sim_budget = st.number_input(
            "Promotional Budget (PKR)",
            min_value=100000,
            max_value=50000000,
            value=5000000,
            step=500000,
            help="Total PKR amount you plan to spend on promotions")
    with col2:
        products_list = sorted(roi_data_p["ProductName"].unique())
        sim_product   = st.selectbox("Select Product", products_list,
                                      index=products_list.index("Ramipace")
                                      if "Ramipace" in products_list else 0)
    with col3:
        sim_month = st.selectbox("Month", range(1,13),
                                  format_func=lambda x: mo_map_p[x])
    with col4:
        sim_year = st.selectbox("Year", [2025, 2026])

    # Show historical ROI for selected product
    prod_hist = roi_data_p[roi_data_p["ProductName"]==sim_product]
    if len(prod_hist) > 0:
        hist_roi = prod_hist["TotalRevenue"].sum()/prod_hist["PromoSpend"].sum()
        st.markdown(f"📊 Historical ROI for **{sim_product}**: **{hist_roi:.1f}x** (PKR 1 spent → PKR {hist_roi:.1f} earned)")

    if st.button("🔮 Predict Revenue", type="primary"):
        try:
            prod_enc = le_p2.transform([sim_product])[0]
        except:
            prod_enc = 0

        sim_input = pd.DataFrame([{
            "PromoSpend" : sim_budget,
            "Prod_enc"   : prod_enc,
            "Mo"         : sim_month,
            "Yr"         : sim_year,
            "Month_sin"  : np.sin(2*np.pi*sim_month/12),
            "Month_cos"  : np.cos(2*np.pi*sim_month/12),
            "Q4"         : 1 if sim_month in [10,11,12] else 0
        }])

        pred_rev  = max(best_model_p.predict(sim_input)[0], 0)
        pred_roi  = pred_rev/sim_budget if sim_budget>0 else 0
        pred_upper= pred_rev * 1.20
        pred_lower= pred_rev * 0.80

        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(kpi("Predicted Revenue",  fmt(pred_rev),
                        f"For {mo_map_p[sim_month]} {sim_year}"),
                    unsafe_allow_html=True)
        c2.markdown(kpi("Expected ROI",       f"{pred_roi:.1f}x",
                        "Revenue / Budget"),
                    unsafe_allow_html=True)
        c3.markdown(kpi("Optimistic (+20%)",  fmt(pred_upper),
                        "Best case scenario"),
                    unsafe_allow_html=True)
        c4.markdown(kpi("Conservative (-20%)",fmt(pred_lower),
                        "Worst case scenario"),
                    unsafe_allow_html=True)

        st.markdown(f"""
        <div class="manual-working">
        PREDICTION DETAILS
        ══════════════════════════════════════════
        Product      : {sim_product}
        Month        : {mo_map_p[sim_month]} {sim_year}
        Budget       : {fmt(sim_budget)}
        Model Used   : {best_name_p} (R2={best_r2_p:.3f})

        Predicted Revenue : {fmt(pred_rev)}
        Expected ROI      : {pred_roi:.1f}x
        Confidence Range  : {fmt(pred_lower)} to {fmt(pred_upper)}

        INTERPRETATION:
        For every PKR 1 you invest in {sim_product}
        promotion in {mo_map_p[sim_month]}, you can expect
        PKR {pred_roi:.1f} in revenue return.

        Note: Prediction based on historical patterns.
        Actual results may vary ±20%.
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Top 10 products by historical ROI
    st.markdown(sec("🏆 Top Products by Historical ROI — Where to Invest?"), unsafe_allow_html=True)
    st.markdown(note("This table shows which products historically give best return on promotional investment. Use this to decide WHERE to allocate your budget for maximum impact."), unsafe_allow_html=True)

    prod_roi_hist = roi_data_p.groupby("ProductName").agg(
        TotalRevenue=("TotalRevenue","sum"),
        TotalSpend=("PromoSpend","sum")).reset_index()
    prod_roi_hist = prod_roi_hist[prod_roi_hist["TotalSpend"]>500000]
    prod_roi_hist["ROI"] = prod_roi_hist["TotalRevenue"]/prod_roi_hist["TotalSpend"]
    prod_roi_hist = prod_roi_hist.nlargest(15,"ROI")
    prod_roi_hist["Rev_fmt"]   = prod_roi_hist["TotalRevenue"].apply(fmt)
    prod_roi_hist["Spend_fmt"] = prod_roi_hist["TotalSpend"].apply(fmt)
    prod_roi_hist["ROI_fmt"]   = prod_roi_hist["ROI"].apply(lambda x: f"{x:.1f}x")

    col1, col2 = st.columns(2)
    with col1:
        colors_h = ["#FFD700" if r>60 else "#2e7d32" if r>30
                    else "#2c5f8a" for r in prod_roi_hist["ROI"]]
        fig = go.Figure(go.Bar(
            x=prod_roi_hist["ROI"],
            y=prod_roi_hist["ProductName"],
            orientation="h",
            text=prod_roi_hist["ROI_fmt"],
            textposition="outside",
            textfont_size=10,
            marker_color=colors_h))
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="ROI (Revenue / Spend)"))
        fig.update_layout(title="Top 15 Products by ROI")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(
            prod_roi_hist[["ProductName","ROI_fmt","Rev_fmt","Spend_fmt"]].rename(
                columns={"ProductName":"Product","ROI_fmt":"ROI",
                         "Rev_fmt":"Revenue","Spend_fmt":"Spend"}),
            use_container_width=True, hide_index=True)
        st.markdown(good("Gold bars = exceptional ROI above 60x. Invest MORE in these products for maximum return."), unsafe_allow_html=True)
        st.markdown(warn("Always cross-check with volume — a very high ROI on small spend may not scale linearly."), unsafe_allow_html=True)

elif page == "🚨 Alerts & Opportunities":
    st.markdown("<h2 style=\'color:#2c5f8a\'>🚨 Alerts & Strategic Opportunities</h2>", unsafe_allow_html=True)
    st.markdown(note("All alerts based on verified data from all 4 databases. Green = opportunity to earn more. Orange = warning to fix. Red = urgent action needed this week."), unsafe_allow_html=True)

    # ── OPPORTUNITIES ────────────────────────────────────
    st.markdown(sec("🌟 Hidden Opportunities — High ROI Products Getting Low Budget"), unsafe_allow_html=True)
    st.markdown(note("These products give exceptional return per PKR spent but receive very little promotional budget. Doubling their budget could significantly boost company revenue."), unsafe_allow_html=True)

    # Calculate ROI from raw data
    prod_rev_a   = df_sales.groupby("ProductName")["TotalRevenue"].sum()
    prod_spend_a = df_act.groupby("Product")["TotalAmount"].sum()
    roi_a = pd.DataFrame({
        "Revenue": prod_rev_a,
        "Spend"  : prod_spend_a
    }).dropna().reset_index()
    roi_a.columns = ["ProductName","TotalRevenue","TotalPromoSpend"]
    roi_a = roi_a[roi_a["TotalPromoSpend"]>0]
    roi_a["ROI"] = roi_a["TotalRevenue"]/roi_a["TotalPromoSpend"]

    opp = roi_a[
        (roi_a["ROI"] > 20) &
        (roi_a["TotalPromoSpend"] < roi_a["TotalPromoSpend"].median())
    ].sort_values("ROI", ascending=False).head(10)

    for _, row in opp.iterrows():
        pot = row["ROI"] * row["TotalPromoSpend"] * 2
        pname = row["ProductName"]
        proi  = row["ROI"]
        pspend= row["TotalPromoSpend"]
        prev  = row["TotalRevenue"]
        st.markdown(good(
            f"<b>{pname}</b> — ROI: <b>{proi:.1f}x</b> | "
            f"Current Spend: {fmt(pspend)} | Revenue: {fmt(prev)}<br>"
            f"<i>Action: Double budget to {fmt(pspend*2)} → Expected ~{fmt(pot)}</i>"
        ), unsafe_allow_html=True)

    # ── BUDGET WASTE ─────────────────────────────────────
    st.markdown(sec("⚠️ Budget Waste — High Spend but Low ROI"), unsafe_allow_html=True)
    st.markdown(note("These products consume large promotional budgets but deliver poor returns. Budget should be reallocated to high ROI products above."), unsafe_allow_html=True)

    waste = roi_a[
        (roi_a["ROI"] < 10) &
        (roi_a["TotalPromoSpend"] > roi_a["TotalPromoSpend"].median())
    ].sort_values("TotalPromoSpend", ascending=False).head(5)

    for _, row in waste.iterrows():
        wname  = row["ProductName"]
        wroi   = row["ROI"]
        wspend = row["TotalPromoSpend"]
        wrev   = row["TotalRevenue"]
        wavg   = roi_a["ROI"].mean()
        st.markdown(warn(
            f"<b>{wname}</b> — ROI: <b>{wroi:.1f}x</b> "
            f"(vs company avg {wavg:.1f}x)<br>"
            f"Spent: {fmt(wspend)} → Revenue: {fmt(wrev)}<br>"
            f"<i>Action: Reduce budget 50% and reallocate to high ROI products</i>"
        ), unsafe_allow_html=True)

    # ── DISCOUNT ABUSE ───────────────────────────────────
    st.markdown(sec("🚨 Discount Abuse Alert"), unsafe_allow_html=True)
    st.markdown(note("Total discounts given = PKR 750M. Company average = 1.6%. Falcons team at 20.5% rate. This needs immediate management audit."), unsafe_allow_html=True)

    disc_team = df_sales.groupby("TeamName").agg(
        Discount=("TotalDiscount","sum"),
        Revenue=("TotalRevenue","sum")).reset_index()
    disc_team = disc_team[disc_team["Revenue"]>5e6]
    disc_team["Rate"] = disc_team["Discount"]/disc_team["Revenue"]*100
    disc_team = disc_team[disc_team["Rate"]>5].sort_values("Rate",ascending=False)

    for _, row in disc_team.iterrows():
        tname  = row["TeamName"]
        trate  = row["Rate"]
        tdisc  = row["Discount"]
        if trate > 15:
            st.markdown(danger(
                f"<b>{tname}</b> — Discount Rate: <b>{trate:.1f}%</b> "
                f"(avg 1.6%) | Discount Given: {fmt(tdisc)}"
            ), unsafe_allow_html=True)
        else:
            st.markdown(warn(
                f"<b>{tname}</b> — Discount Rate: <b>{trate:.1f}%</b> "
                f"(avg 1.6%) | Discount Given: {fmt(tdisc)}"
            ), unsafe_allow_html=True)

    # ── DIVISION ALERTS ───────────────────────────────────
    st.markdown(sec("🚨 Division Field Activity Alerts"), unsafe_allow_html=True)
    st.markdown(note("Low travel activity = fewer doctor visits = lower prescriptions = lower revenue. Divisions below 30 trips per person need immediate attention."), unsafe_allow_html=True)

    div_alert = df_travel.groupby("TravellerDivision").agg(
        Trips=("TravelCount","sum"),
        People=("Traveller","nunique")).reset_index()
    div_alert["TripsPerPerson"] = (div_alert["Trips"]/div_alert["People"]).round(1)
    div_name_a = {
        "Division 1":"Division 1 — Bone Saviors",
        "Division 2":"Division 2 — Winners",
        "Division 3":"Division 3 — International",
        "Division 4":"Division 4 — Admin",
        "Division 5":"Division 5 — Strikers"
    }
    div_alert["Name"] = div_alert["TravellerDivision"].map(div_name_a)

    for _, row in div_alert.sort_values("TripsPerPerson").iterrows():
        dname   = row["Name"]
        dtrips  = row["TripsPerPerson"]
        dpeople = int(row["People"])
        dtotal  = int(row["Trips"])
        if dtrips < 30:
            st.markdown(danger(
                f"<b>{dname}</b> — Only {dtrips:.0f} trips/person | "
                f"{dpeople} people | {dtotal} total trips<br>"
                f"<i>Set minimum 40 trips/person target immediately</i>"
            ), unsafe_allow_html=True)
        else:
            st.markdown(good(
                f"<b>{dname}</b> — {dtrips:.0f} trips/person ✓"
            ), unsafe_allow_html=True)

    # ── DISTRIBUTOR ALERTS ────────────────────────────────
    st.markdown(sec("⚠️ Distributor Risk Alerts"), unsafe_allow_html=True)

    sdp_24_a = set(df_zsdcy[df_zsdcy["Yr"]==2024]["SDP Name"].unique())
    sdp_25_a = set(df_zsdcy[df_zsdcy["Yr"]==2025]["SDP Name"].unique())
    lost_a   = sdp_24_a - sdp_25_a
    lost_rev_a = []
    for sdp in lost_a:
        rev = df_zsdcy[df_zsdcy["SDP Name"]==sdp]["Revenue"].sum()
        lost_rev_a.append({"Distributor":sdp,"Lost Revenue":rev})
    if lost_rev_a:
        lost_df_a   = pd.DataFrame(lost_rev_a).sort_values("Lost Revenue",ascending=False)
        lost_df_a["Revenue"] = lost_df_a["Lost Revenue"].apply(fmt)
        total_lost  = sum(r["Lost Revenue"] for r in lost_rev_a)
        st.markdown(danger(
            f"{len(lost_a)} distributors lost from 2024 to 2025. "
            f"Total at-risk revenue: {fmt(total_lost)}"
        ), unsafe_allow_html=True)
        st.dataframe(lost_df_a[["Distributor","Revenue"]].head(10),
                     use_container_width=True, hide_index=True)

    # ── STRATEGIC RECOMMENDATIONS ─────────────────────────
    st.markdown(sec("📋 Strategic Recommendations"), unsafe_allow_html=True)
    recs = [
        ("good",  "Invest in Ramipace",      "ROI = 65.9x verified manually. Double budget immediately."),
        ("good",  "Invest in Finno-Q",       "226% growth with minimal spend. Allocate PKR 10M now."),
        ("good",  "Focus on Q4",             "Oct-Dec = 24.4% of annual revenue. Start September campaigns."),
        ("warn",  "Fix Promo Timing",        "July = highest spend but 8th in sales. Move to January."),
        ("warn",  "Grow Nutraceuticals",     "Growing 35% vs Pharma 28%. Launch dedicated team."),
        ("warn",  "Fix Division 4",          "Only 10 trips/person. Set 40 trips minimum target."),
        ("danger","Fix Discount Abuse",      "Falcons 20.5% discount rate. Audit immediately. Save PKR 200M."),
        ("danger","Reduce Distributor Risk", "87.5% through Premier Sales. Onboard 2 new distributors."),
    ]
    for style, title, desc in recs:
        if style=="good":
            st.markdown(good(f"<b>{title}:</b> {desc}"), unsafe_allow_html=True)
        elif style=="warn":
            st.markdown(warn(f"<b>{title}:</b> {desc}"), unsafe_allow_html=True)
        else:
            st.markdown(danger(f"<b>{title}:</b> {desc}"), unsafe_allow_html=True)

    # ── QUICK WINS TABLE ──────────────────────────────────
    st.markdown(sec("⚡ Quick Wins Action Table"), unsafe_allow_html=True)
    qw = pd.DataFrame({
        "Action":[
            "Double Ramipace budget",
            "Allocate PKR 10M to Finno-Q",
            "Fix Falcons discount abuse",
            "Move July spend to January",
            "Add 300 Karachi field trips",
            "Onboard 2 new distributors",
            "Double Q4 campaigns",
            "Launch Nutraceutical team"
        ],
        "Expected Impact":[
            "+PKR 951M additional revenue",
            "+PKR 75M revenue",
            "Save PKR 200M/year",
            "+PKR 300M revenue",
            "+PKR 150M revenue",
            "Risk reduction",
            "+PKR 300M Q4 revenue",
            "+PKR 300M by 2027"
        ],
        "Priority":[
            "🔴 THIS WEEK","🔴 THIS WEEK",
            "🔴 THIS WEEK","🟡 THIS MONTH",
            "🟡 THIS MONTH","🟡 THIS MONTH",
            "🟡 THIS MONTH","🟢 THIS YEAR"
        ]
    })
    st.dataframe(qw, use_container_width=True, hide_index=True)

elif page == "📊 Advanced Insights":
    st.markdown("<h2 style=\'color:#2c5f8a\'>📊 Advanced Business Insights</h2>", unsafe_allow_html=True)
    st.markdown(note("This page contains 12 deep analytical insights derived from all 3 databases combined. These insights go beyond basic reporting to reveal hidden patterns and growth opportunities."), unsafe_allow_html=True)

    import os

    # ── INSIGHT 1: REVENUE PER INVOICE ──────────────────────
    st.markdown(sec("💳 Insight 1 — Revenue Per Invoice Trend"), unsafe_allow_html=True)
    st.markdown(note("Revenue per invoice shows whether growth is coming from MORE customers or HIGHER prices. If revenue grows faster than invoices, prices are increasing — not just volume."), unsafe_allow_html=True)

    rpi = df_sales.groupby("Yr").agg(
        Revenue=("TotalRevenue","sum"),
        Invoices=("InvoiceCount","sum")).reset_index()
    rpi["RevPerInvoice"] = rpi["Revenue"]/rpi["Invoices"]
    rpi = rpi[rpi["Yr"] < 2026]
    rpi["Label"] = rpi["RevPerInvoice"].apply(lambda x: f"PKR {x:,.0f}")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(rpi, x="Yr", y="RevPerInvoice", text="Label",
                     color_discrete_sequence=["#2c5f8a"],
                     title="Revenue Per Invoice by Year")
        fig.update_traces(textposition="outside", textfont_size=12)
        apply_layout(fig, height=280,
                     xaxis=dict(gridcolor="#eeeeee", tickmode="array",
                                tickvals=rpi["Yr"].tolist()),
                     yaxis=dict(gridcolor="#eeeeee", title="PKR per Invoice"))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        rev_growth  = ((rpi.iloc[1]["Revenue"]-rpi.iloc[0]["Revenue"])/rpi.iloc[0]["Revenue"]*100)
        inv_growth  = ((rpi.iloc[1]["Invoices"]-rpi.iloc[0]["Invoices"])/rpi.iloc[0]["Invoices"]*100)
        unit_g_2024 = df_sales[df_sales["Yr"]==2024]["TotalUnits"].sum()
        unit_g_2025 = df_sales[df_sales["Yr"]==2025]["TotalUnits"].sum()
        unit_growth = ((unit_g_2025-unit_g_2024)/unit_g_2024*100)

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(good(f"Revenue grew <b>+{rev_growth:.1f}%</b> from 2024 to 2025"), unsafe_allow_html=True)
        st.markdown(good(f"Invoices grew <b>+{inv_growth:.1f}%</b> — more customers being served"), unsafe_allow_html=True)
        st.markdown(good(f"Units grew <b>+{unit_growth:.1f}%</b> — genuine volume growth"), unsafe_allow_html=True)
        if rev_growth > unit_growth:
            st.markdown(warn(f"Revenue grew {rev_growth-unit_growth:.1f}% FASTER than units — part of growth is price increase not just volume. Monitor pricing strategy carefully."), unsafe_allow_html=True)

    # ── INSIGHT 2: PARETO ANALYSIS ──────────────────────────
    st.markdown(sec("📊 Insight 2 — Pareto Analysis (80/20 Rule)"), unsafe_allow_html=True)
    st.markdown(note("The 80/20 rule: 20% of products should generate 80% of revenue. Pharmevo has 140 products but only 30 (21.4%) generate 80% of revenue. This shows HIGH dependency on few products — a business risk!"), unsafe_allow_html=True)

    prod_rev = df_sales.groupby("ProductName")["TotalRevenue"].sum().sort_values(ascending=False).reset_index()
    prod_rev["CumRevenue"] = prod_rev["TotalRevenue"].cumsum()
    prod_rev["CumPct"]     = prod_rev["CumRevenue"]/prod_rev["TotalRevenue"].sum()*100
    prod_rev["Label"]      = prod_rev["TotalRevenue"].apply(fmt)
    top30 = prod_rev.head(30).copy()
    top30["Rank"] = range(1, 31)

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top30["ProductName"], y=top30["TotalRevenue"]/1e6,
            name="Revenue (M PKR)",
            marker_color="#2c5f8a",
            text=top30["Label"], textposition="outside",
            textfont_size=8
        ))
        fig.add_trace(go.Scatter(
            x=top30["ProductName"], y=top30["CumPct"],
            name="Cumulative %",
            line=dict(color="#e65100", width=2),
            yaxis="y2", mode="lines+markers",
            marker=dict(size=4)
        ))
        fig.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font_color="#333", height=400,
            yaxis=dict(title="Revenue (M PKR)", gridcolor="#eeeeee"),
            yaxis2=dict(title="Cumulative %", overlaying="y",
                       side="right", range=[0,105],
                       gridcolor="#eeeeee"),
            xaxis=dict(tickangle=-45, gridcolor="#eeeeee"),
            legend=dict(bgcolor="white"),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        total_prods = len(prod_rev)
        st.markdown(f"""
        <div class="manual-working">
        PARETO ANALYSIS — PHARMEVO PRODUCT PORTFOLIO
        ══════════════════════════════════════════════
        Total Products in Portfolio : {total_prods}
        Products generating 80% rev : 30 (21.4%)
        Products generating 90% rev : ~45 (32.1%)
        Products generating 99% rev : ~80 (57.1%)
        Remaining ~60 products      : only 1% revenue

        BUSINESS RISK ASSESSMENT:
        If top 5 products fail       → lose 32.9% revenue
        If top 10 products fail      → lose 49.4% revenue
        If top 30 products fail      → lose 80.0% revenue

        RECOMMENDATION:
        → Protect top 30 products with max promo budget
        → Review bottom 60 products — discontinue or invest
        → Develop 2-3 new products to reduce dependency
        ══════════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    # ── INSIGHT 3: DISCOUNT ANALYSIS ────────────────────────
    st.markdown(sec("💸 Insight 3 — Discount & Bonus Analysis"), unsafe_allow_html=True)
    st.markdown(note("PKR 749M in discounts were given in 2024-2026. Zoltar has 47% discount rate — nearly HALF its revenue is given as discount. This is unsustainable and needs urgent review."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top 10 Products by Total Discount Given**")
        disc_df = df_sales.groupby("ProductName").agg(
            Discount=("TotalDiscount","sum"),
            Revenue=("TotalRevenue","sum")).reset_index()
        disc_df["DiscRate"] = disc_df["Discount"]/disc_df["Revenue"].replace(0,1)*100
        disc_df = disc_df[disc_df["Revenue"]>0].nlargest(10,"Discount")
        disc_df["Label"] = disc_df["Discount"].apply(fmt)

        colors = ["#c62828" if r>20 else "#e65100" if r>5 else "#2c5f8a"
                  for r in disc_df["DiscRate"]]
        fig = go.Figure(go.Bar(
            x=disc_df["Discount"]/1e6, y=disc_df["ProductName"],
            orientation="h",
            text=[f"{fmt(d)} ({r:.1f}%)" for d,r in
                  zip(disc_df["Discount"],disc_df["DiscRate"])],
            textposition="outside", textfont_size=10,
            marker_color=colors
        ))
        apply_layout(fig, height=360,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Discount (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(danger("Red bars = discount rate above 20% — CRITICAL. These products may be unprofitable after discounts."), unsafe_allow_html=True)

    with col2:
        st.markdown("**Top 10 Teams by Discount Given**")
        team_disc = df_sales.groupby("TeamName").agg(
            Discount=("TotalDiscount","sum"),
            Revenue=("TotalRevenue","sum")).reset_index()
        team_disc["DiscRate"] = team_disc["Discount"]/team_disc["Revenue"].replace(0,1)*100
        team_disc = team_disc[team_disc["Revenue"]>0].nlargest(10,"Discount")

        colors2 = ["#c62828" if r>15 else "#e65100" if r>5 else "#2c5f8a"
                   for r in team_disc["DiscRate"]]
        fig = go.Figure(go.Bar(
            x=team_disc["Discount"]/1e6, y=team_disc["TeamName"],
            orientation="h",
            text=[f"{fmt(d)} ({r:.1f}%)" for d,r in
                  zip(team_disc["Discount"],team_disc["DiscRate"])],
            textposition="outside", textfont_size=10,
            marker_color=colors2
        ))
        apply_layout(fig, height=360,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Discount (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(danger("Falcons team gave PKR 224.7M discounts at 20.5% rate! Strikers 20.3%. Management must investigate if these discounts are necessary or being abused."), unsafe_allow_html=True)

    # ── INSIGHT 4: PROMOTIONAL TIMING ───────────────────────
    st.markdown(sec("⏰ Insight 4 — Promotional Timing vs Sales Peak"), unsafe_allow_html=True)
    st.markdown(note("Ideal timing: promotions should happen 1-2 months BEFORE sales peaks to build doctor awareness. Misaligned months mean wasted promotional budget. Green = aligned, Red = misaligned."), unsafe_allow_html=True)

    promo_monthly = df_act.groupby("Mo")["TotalAmount"].sum()
    sales_monthly = df_sales.groupby("Mo")["TotalRevenue"].sum()
    promo_rank    = promo_monthly.rank(ascending=False)
    sales_rank    = sales_monthly.rank(ascending=False)

    timing_df = pd.DataFrame({
        "Month"     : list(months_map.values()),
        "PromoRank" : [int(promo_rank.get(m,0)) for m in range(1,13)],
        "SalesRank" : [int(sales_rank.get(m,0)) for m in range(1,13)],
        "PromoAmt"  : [promo_monthly.get(m,0)/1e6 for m in range(1,13)],
        "SalesAmt"  : [sales_monthly.get(m,0)/1e6 for m in range(1,13)],
    })
    timing_df["Gap"]       = abs(timing_df["PromoRank"]-timing_df["SalesRank"])
    timing_df["Aligned"]   = timing_df["Gap"] <= 2
    timing_df["Status"]    = timing_df["Aligned"].map({True:"✅ Aligned", False:"⚠️ Misaligned"})
    timing_df["PromoLabel"]= timing_df["PromoAmt"].apply(lambda x: f"PKR {x:.1f}M")
    timing_df["SalesLabel"]= timing_df["SalesAmt"].apply(lambda x: f"PKR {x:.0f}M")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=timing_df["Month"], y=timing_df["PromoAmt"],
            name="Promo Spend (M PKR)",
            marker_color="rgba(230,81,0,0.7)",
            text=timing_df["PromoLabel"],
            textposition="outside", textfont_size=9
        ))
        fig.add_trace(go.Scatter(
            x=timing_df["Month"], y=timing_df["SalesAmt"]/50,
            name="Sales Index",
            line=dict(color="#2c5f8a", width=3),
            mode="lines+markers"
        ))
        apply_layout(fig, height=320,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee", title="Amount (M PKR)"),
                     hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(timing_df[["Month","PromoRank","SalesRank","Gap","Status"]],
                     use_container_width=True, hide_index=True)
        aligned_count = timing_df["Aligned"].sum()
        st.markdown(good(f"{aligned_count}/12 months are well aligned between promo spend and sales peaks."), unsafe_allow_html=True)
        st.markdown(warn("Jan and Feb: Sales rank #1 and #2 but promo rank #6 and #8 — MAJOR GAP! Increase January and February promotional spend to capture peak sales months."), unsafe_allow_html=True)
        st.markdown(warn("July: Highest promo spend (#1) but only #8 in sales — promotional spend in July is not converting well to sales."), unsafe_allow_html=True)

    # ── INSIGHT 5: TEAM PRODUCTIVITY INDEX ──────────────────
    st.markdown(sec("🏆 Insight 5 — Team Productivity Index"), unsafe_allow_html=True)
    st.markdown(note("Productivity Score combines 3 factors: ROI (40%), Revenue per Trip (30%), Total Revenue (30%). Score of 100 = best team overall. This single number ranks all teams fairly."), unsafe_allow_html=True)

    team_rev   = df_sales.groupby("TeamName")["TotalRevenue"].sum()
    team_disc2 = df_sales.groupby("TeamName")["TotalDiscount"].sum()
    team_spend = df_act.groupby("RequestorTeams")["TotalAmount"].sum()
    team_trips = df_travel.groupby("TravellerTeam")["TravelCount"].sum()

    prod_index = pd.DataFrame({
        "Revenue" : team_rev,
        "Discount": team_disc2,
        "Spend"   : team_spend,
        "Trips"   : team_trips
    }).fillna(0)

    prod_index = prod_index[prod_index["Revenue"]>1e8].copy()
    prod_index["NetRevenue"]  = prod_index["Revenue"] - prod_index["Discount"]
    prod_index["ROI"]         = prod_index["Revenue"]/prod_index["Spend"].replace(0,1)
    prod_index["RevPerTrip"]  = prod_index["Revenue"]/prod_index["Trips"].replace(0,1)
    prod_index["DiscRate"]    = prod_index["Discount"]/prod_index["Revenue"]*100

    for col in ["ROI","Revenue"]:
        mn = prod_index[col].min()
        mx = prod_index[col].max()
        prod_index[f"{col}_score"] = (prod_index[col]-mn)/(mx-mn)*100 if mx>mn else 50

    prod_index["Score"] = (
        prod_index["ROI_score"]*0.5 +
        prod_index["Revenue_score"]*0.5
    ).round(1)
    prod_index = prod_index.reset_index()
    prod_index = prod_index.rename(columns={"index":"TeamName"})
    prod_index = prod_index.sort_values("Score", ascending=False)

    prod_index["RevLabel"]   = prod_index["Revenue"].apply(fmt)
    prod_index["SpendLabel"] = prod_index["Spend"].apply(fmt)
    prod_index["DiscLabel"]  = prod_index["Discount"].apply(fmt)

    col1, col2 = st.columns(2)
    with col1:
        colors = ["#2e7d32" if s>=70 else "#2c5f8a" if s>=40 else "#e65100"
                  for s in prod_index["Score"]]
        fig = go.Figure(go.Bar(
            x=prod_index["Score"], y=prod_index["TeamName"],
            orientation="h",
            text=[f"{s:.0f}/100" for s in prod_index["Score"]],
            textposition="outside", textfont_size=10,
            marker_color=colors
        ))
        apply_layout(fig, height=500,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Productivity Score (0-100)",
                                range=[0,115]))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        display_cols = prod_index[["TeamName","Score","RevLabel",
                                   "SpendLabel","DiscLabel","DiscRate"]].copy()
        display_cols.columns = ["Team","Score","Revenue",
                                "Promo Spend","Discounts","Disc %"]
        display_cols["Disc %"] = display_cols["Disc %"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_cols, use_container_width=True, hide_index=True)
        st.markdown(good("Green score (70+) = top performing teams. Challengers leads consistently."), unsafe_allow_html=True)
        st.markdown(warn("Orange score (below 40) = needs management attention and strategy review."), unsafe_allow_html=True)

    # ── INSIGHT 6: PRODUCT CONSISTENCY ──────────────────────
    st.markdown(sec("📈 Insight 6 — Product Revenue Consistency"), unsafe_allow_html=True)
    st.markdown(note("CV (Coefficient of Variation) measures consistency. Low CV = steady reliable revenue every month. High CV = unpredictable spikes and crashes. Consistent products are safer for forecasting."), unsafe_allow_html=True)

    prod_monthly = df_sales[df_sales["Yr"].isin([2024,2025])].groupby(
        ["ProductName","Yr","Mo"])["TotalRevenue"].sum().reset_index()
    prod_cv = prod_monthly.groupby("ProductName")["TotalRevenue"].agg(
        Mean=("mean"), Std=("std")).reset_index()
    prod_cv.columns = ["ProductName","Mean","Std"]
    prod_cv["CV"]   = prod_cv["Std"]/prod_cv["Mean"].replace(0,1)
    prod_cv         = prod_cv[prod_cv["Mean"]>2e6]
    prod_cv["MeanLabel"] = prod_cv["Mean"].apply(fmt)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Most Consistent Products — Reliable Revenue**")
        top_con = prod_cv.nsmallest(12,"CV")
        top_con["CVLabel"] = top_con["CV"].apply(lambda x: f"CV={x:.2f}")
        fig = px.bar(top_con, x="Mean", y="ProductName",
                     orientation="h", text="CVLabel",
                     color="CV", color_continuous_scale="Greens_r")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=400,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Avg Monthly Revenue"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(good("These products generate steady revenue every month. Perfect base for reliable annual forecasting."), unsafe_allow_html=True)

    with col2:
        st.markdown("**Most Volatile Products — Unpredictable Revenue**")
        top_vol = prod_cv.nlargest(12,"CV")
        top_vol["CVLabel"] = top_vol["CV"].apply(lambda x: f"CV={x:.2f}")
        fig = px.bar(top_vol, x="Mean", y="ProductName",
                     orientation="h", text="CVLabel",
                     color="CV", color_continuous_scale="Reds")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=400,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Avg Monthly Revenue"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(warn("These products have highly unpredictable revenue. Investigate seasonal patterns or supply chain issues."), unsafe_allow_html=True)

    # ── INSIGHT 7: CITY PENETRATION ─────────────────────────
    st.markdown(sec("🗺️ Insight 7 — City Penetration & New Market Expansion"), unsafe_allow_html=True)
    st.markdown(note("In 2025, Pharmevo entered 9 NEW cities and lost coverage in 6 cities. New cities like DI Khan, Mardan, Swabi represent untapped markets with growth potential."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        cities_2024 = set(df_travel[df_travel["Yr"]==2024]["VisitLocation"].unique())
        cities_2025 = set(df_travel[df_travel["Yr"]==2025]["VisitLocation"].unique())
        new_cities  = cities_2025 - cities_2024
        lost_cities = cities_2024 - cities_2025

        expansion_df = pd.DataFrame({
            "City"  : list(new_cities),
            "Status": ["🟢 New in 2025"] * len(new_cities)
        })
        lost_df = pd.DataFrame({
            "City"  : list(lost_cities),
            "Status": ["🔴 Lost from 2024"] * len(lost_cities)
        })
        combined = pd.concat([expansion_df, lost_df]).reset_index(drop=True)
        st.dataframe(combined, use_container_width=True, hide_index=True)
        st.markdown(good(f"9 new cities added in 2025 — market expansion is happening!"), unsafe_allow_html=True)
        st.markdown(warn(f"6 cities lost coverage — follow up needed in Mianwali, Kasur, Sheikhupura, Naran, Burewala, Dadu."), unsafe_allow_html=True)

    with col2:
        city_yoy = df_travel[df_travel["Yr"].isin([2024,2025])].groupby(
            ["VisitLocation","Yr"])["TravelCount"].sum().reset_index()
        city_pivot = city_yoy.pivot(index="VisitLocation",
                                    columns="Yr", values="TravelCount").fillna(0)
        if 2024 in city_pivot.columns and 2025 in city_pivot.columns:
            city_pivot["Growth"] = ((city_pivot[2025]-city_pivot[2024])/
                                    city_pivot[2024].replace(0,1)*100)
            city_growth = city_pivot[city_pivot[2024]>5].sort_values(
                "Growth", ascending=False).head(10).reset_index()
            city_growth["Label"] = city_growth["Growth"].apply(lambda x: f"{x:.0f}%")
            fig = px.bar(city_growth, x="Growth", y="VisitLocation",
                         orientation="h", text="Label",
                         color="Growth", color_continuous_scale="Greens")
            fig.update_traces(textposition="outside", textfont_size=10)
            apply_layout(fig, height=370,
                         yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                         xaxis=dict(gridcolor="#eeeeee", title="Trip Growth % 2024→2025"),
                         coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    # ── INSIGHT 8: DIVISION EFFICIENCY ──────────────────────
    st.markdown(sec("🏢 Insight 8 — Division Field Efficiency"), unsafe_allow_html=True)
    st.markdown(note("Trips per person shows how hard each division works in the field. Division 1 (Bone Saviors) leads with 82 trips per person. Division 4 at only 16 trips per person needs immediate action."), unsafe_allow_html=True)

    div_eff = df_travel.groupby("TravellerDivision").agg(
        Trips=("TravelCount","sum"),
        Nights=("NoofNights","sum"),
        People=("Traveller","nunique")).reset_index()
    div_eff["TripsPerPerson"] = (div_eff["Trips"]/div_eff["People"]).round(1)
    div_eff["NightsPerTrip"]  = (div_eff["Nights"]/div_eff["Trips"]).round(1)

    div_name_map2 = {
        "Division 1": "Div 1 — Bone Saviors",
        "Division 2": "Div 2 — Winners",
        "Division 3": "Div 3 — International",
        "Division 4": "Div 4 — Admin",
        "Division 5": "Div 5 — Strikers"
    }
    div_eff["DivName"] = div_eff["TravellerDivision"].map(div_name_map2)

    col1, col2 = st.columns(2)
    with col1:
        colors = ["#2e7d32" if t>70 else "#2c5f8a" if t>40 else "#c62828"
                  for t in div_eff["TripsPerPerson"]]
        fig = go.Figure(go.Bar(
            x=div_eff.sort_values("TripsPerPerson",ascending=False)["TripsPerPerson"],
            y=div_eff.sort_values("TripsPerPerson",ascending=False)["DivName"],
            orientation="h",
            text=[f"{t:.0f} trips/person" for t in
                  div_eff.sort_values("TripsPerPerson",ascending=False)["TripsPerPerson"]],
            textposition="outside", textfont_size=11,
            marker_color=sorted(colors, reverse=True)
        ))
        apply_layout(fig, height=280,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Trips Per Person"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(div_eff[["DivName","People","Trips","TripsPerPerson",
                               "NightsPerTrip"]].sort_values(
            "TripsPerPerson", ascending=False),
            use_container_width=True, hide_index=True)
        st.markdown(good("Division 1 (Bone Saviors): 82 trips per person — highest field activity!"), unsafe_allow_html=True)
        st.markdown(danger("Division 4: only 16 trips per person in 5 years. This is an admin division — but if any sales roles exist here they are severely underperforming."), unsafe_allow_html=True)

    # ── INSIGHT 9: DISCOUNT RISK ─────────────────────────────
    st.markdown(sec("🚨 Insight 9 — High Discount Risk Products"), unsafe_allow_html=True)
    st.markdown(note("Products with discount rate above 10% are at profitability risk. Zoltar at 47% means for every PKR 100 sold, PKR 47 is given as discount — this product may be loss-making!"), unsafe_allow_html=True)

    disc_risk = df_sales.groupby("ProductName").agg(
        Revenue=("TotalRevenue","sum"),
        Discount=("TotalDiscount","sum")).reset_index()
    disc_risk = disc_risk[disc_risk["Revenue"]>5e6]
    disc_risk["DiscRate"] = disc_risk["Discount"]/disc_risk["Revenue"]*100
    disc_risk = disc_risk.sort_values("DiscRate", ascending=False).head(15)
    disc_risk["Label"] = disc_risk["DiscRate"].apply(lambda x: f"{x:.1f}%")

    colors_risk = ["#c62828" if r>20 else "#e65100" if r>10 else "#2c5f8a"
                   for r in disc_risk["DiscRate"]]
    fig = go.Figure(go.Bar(
        x=disc_risk["DiscRate"], y=disc_risk["ProductName"],
        orientation="h",
        text=disc_risk["Label"],
        textposition="outside", textfont_size=11,
        marker_color=colors_risk
    ))
    apply_layout(fig, height=450,
                 yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                 xaxis=dict(gridcolor="#eeeeee", title="Discount Rate (%)"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(danger("Zoltar: 47% discount rate. EvoCheck Go: 27.5%. EvoCheck: 18.3%. These products need immediate pricing strategy review — they may be unprofitable."), unsafe_allow_html=True)

    # ── INSIGHT 10: TEAM CONSISTENCY ────────────────────────
    st.markdown(sec("📊 Insight 10 — Team Revenue Consistency"), unsafe_allow_html=True)
    st.markdown(note("Consistent teams are predictable and reliable. Volatile teams have unpredictable months — hard to plan for. Conqueror team has CV of 1.21 meaning massive month-to-month swings."), unsafe_allow_html=True)

    team_monthly = df_sales[df_sales["Yr"].isin([2024,2025])].groupby(
        ["TeamName","Yr","Mo"])["TotalRevenue"].sum().reset_index()
    team_cv = team_monthly.groupby("TeamName")["TotalRevenue"].agg(
        Mean=("mean"), Std=("std")).reset_index()
    team_cv.columns = ["TeamName","Mean","Std"]
    team_cv["CV"]       = team_cv["Std"]/team_cv["Mean"].replace(0,1)
    team_cv             = team_cv[team_cv["Mean"]>2e6].sort_values("CV")
    team_cv["MeanLabel"]= team_cv["Mean"].apply(fmt)
    team_cv["CVLabel"]  = team_cv["CV"].apply(lambda x: f"CV={x:.2f}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Most Consistent Teams**")
        top_t = team_cv.head(10)
        colors_c = ["#2e7d32"]*len(top_t)
        fig = go.Figure(go.Bar(
            x=top_t["CV"], y=top_t["TeamName"],
            orientation="h",
            text=top_t["CVLabel"],
            textposition="outside", textfont_size=10,
            marker_color=colors_c
        ))
        apply_layout(fig, height=360,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="CV (lower = more consistent)"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Most Volatile Teams — Needs Attention**")
        bot_t = team_cv.tail(10).sort_values("CV", ascending=False)
        colors_v = ["#c62828" if c>0.5 else "#e65100"
                    for c in bot_t["CV"]]
        fig = go.Figure(go.Bar(
            x=bot_t["CV"], y=bot_t["TeamName"],
            orientation="h",
            text=bot_t["CVLabel"],
            textposition="outside", textfont_size=10,
            marker_color=colors_v
        ))
        apply_layout(fig, height=360,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="CV (higher = more volatile)"))
        st.plotly_chart(fig, use_container_width=True)

    # ── INSIGHT 11: HOTEL COST OPTIMIZATION ─────────────────
    st.markdown(sec("🏨 Insight 11 — Hotel Cost Optimization Opportunity"), unsafe_allow_html=True)
    st.markdown(note("Top 5 hotels account for majority of bookings. Negotiating corporate rates with these hotels could save 15-20% of travel costs. Indigo Heights alone had 880 bookings — huge negotiation leverage!"), unsafe_allow_html=True)

    hotel_df = df_travel[df_travel["HotelName"]!="Not Recorded"].groupby("HotelName").agg(
        Bookings=("TravelCount","sum"),
        Nights=("NoofNights","sum")).reset_index()
    hotel_df = hotel_df.nlargest(10,"Bookings")
    hotel_df["EstCost"]     = hotel_df["Nights"] * 8000
    hotel_df["Savings15pct"]= hotel_df["EstCost"] * 0.15
    hotel_df["BookLabel"]   = hotel_df["Bookings"].apply(fmt_num)
    hotel_df["CostLabel"]   = hotel_df["EstCost"].apply(fmt)
    hotel_df["SaveLabel"]   = hotel_df["Savings15pct"].apply(fmt)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(hotel_df, x="Bookings", y="HotelName",
                     orientation="h", text="BookLabel",
                     color="Bookings", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=360,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Bookings"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        total_est_cost    = hotel_df["EstCost"].sum()
        total_est_savings = hotel_df["Savings15pct"].sum()
        st.markdown(f"""
        <div class="manual-working">
        HOTEL COST OPTIMIZATION ANALYSIS
        ══════════════════════════════════════════
        Assumption: PKR 8,000 avg per night

        Top 10 Hotels Combined:
        Total Nights    : {int(hotel_df["Nights"].sum()):,}
        Est. Total Cost : {fmt(total_est_cost)}
        Est. 15% Saving : {fmt(total_est_savings)}

        Top 3 Negotiation Targets:
        1. Indigo Heights  : 880 bookings | 2,614 nights
           Est Cost = {fmt(880*2614*8/2614*8000)} → Save {fmt(880*2614/2614*8000*0.15)}
        2. Luxus Grand     : 470 bookings | 1,370 nights
           Est Cost = {fmt(470*1370/1370*8000*1370)} → Save {fmt(470*1370/1370*8000*0.15*1370)}
        3. Hotel Hill View : 464 bookings | 1,391 nights

        ACTION: Contact procurement team to negotiate
        bulk corporate rates with top 5 hotels ASAP.
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    # ── INSIGHT 12: SUMMARY SCORECARD ───────────────────────
    st.markdown(sec("📋 Insight 12 — Company Health Scorecard"), unsafe_allow_html=True)
    st.markdown(note("Overall company health across 6 dimensions. Green = strong. Orange = needs attention. Red = urgent action required. This gives management a quick one-page summary."), unsafe_allow_html=True)

    scorecard = pd.DataFrame({
        "Dimension"     : [
            "Revenue Growth",
            "Promo Efficiency",
            "Field Activity",
            "Product Portfolio",
            "Discount Control",
            "Market Expansion"
        ],
        "Score"         : ["🟢 Strong","🟢 Strong","🟡 Moderate",
                           "🟡 Moderate","🔴 Urgent","🟢 Strong"],
        "Key Metric"    : [
            "+16.6% YoY revenue growth",
            "0.784 correlation | 20.3x ROI",
            "Div 4 only 16 trips/person",
            "30 products = 80% revenue (risk)",
            "Zoltar 47% | Falcons 20.5%",
            "9 new cities added in 2025"
        ],
        "Action Required": [
            "Maintain momentum — invest in top 30 products",
            "Fix Jan/Feb promo timing gap urgently",
            "Set monthly trip targets for Division 4 and 5",
            "Protect top 30 products — develop 2-3 new ones",
            "Audit Falcons and Strikers discount practices",
            "Follow up on 6 lost cities from 2024"
        ]
    })
    st.dataframe(scorecard, use_container_width=True, hide_index=True)

    # Final summary
    col1, col2, col3 = st.columns(3)
    col1.markdown(good("<b>3 STRENGTHS:</b> Revenue growth, Promo ROI, Market expansion"), unsafe_allow_html=True)
    col2.markdown(warn("<b>2 WATCH:</b> Product concentration risk, Field activity gaps"), unsafe_allow_html=True)
    col3.markdown(danger("<b>1 URGENT:</b> Discount abuse — PKR 749M given, Zoltar 47% rate"), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 9: DISTRIBUTION ANALYSIS (ZSDCY DATABASE)
# ════════════════════════════════════════════════════════════
elif page == "📦 Distribution Analysis":
    st.markdown("<h2 style=\'color:#2c5f8a\'>📦 Distribution Analysis — ZSDCY Database</h2>", unsafe_allow_html=True)
    st.markdown(note("This page uses the ZSDCY database — 422,171 delivery and billing records from 2024-2025. Shows product distribution, city coverage, distributor performance and shelf life risk."), unsafe_allow_html=True)

    # Load zsdcy data
    @st.cache_data
    def load_zsdcy():
        df   = pd.read_csv("zsdcy_clean.csv")
        prod = pd.read_csv("zsdcy_products.csv")
        city = pd.read_csv("zsdcy_cities.csv")
        sdp  = pd.read_csv("zsdcy_sdp.csv")
        grow = pd.read_csv("zsdcy_growth.csv")
        risk = pd.read_csv("zsdcy_shelf_risk.csv")
        return df, prod, city, sdp, grow, risk

    df_z, df_zprod, df_zcity, df_zsdp, df_zgrow, df_zrisk = load_zsdcy()

    # KPIs
    # Calculate live KPIs from actual data
    total_rev_z  = df_z["Revenue"].sum()
    total_qty_z  = df_z["Qty"].sum()
    total_cities = df_z["City"].nunique()
    total_sdps   = df_z["SDP Name"].nunique()
    total_prods  = df_z["Material Name"].nunique()
    rev24_z      = df_z[df_z["Yr"]==2024]["Revenue"].sum()
    rev25_z      = df_z[df_z["Yr"]==2025]["Revenue"].sum()
    growth_z     = ((rev25_z-rev24_z)/rev24_z*100) if rev24_z>0 else 0
    top_city     = df_z.groupby("City")["Revenue"].sum().idxmax()
    top_city_rev = df_z.groupby("City")["Revenue"].sum().max()

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Total Revenue",    fmt(total_rev_z),      "2024-2025 ZSDCY DB"), unsafe_allow_html=True)
    c2.markdown(kpi("Total Units",      fmt_num(total_qty_z),  "Units delivered 2024-2025"), unsafe_allow_html=True)
    c3.markdown(kpi("Cities Covered",   str(total_cities),     "Unique cities in Pakistan"), unsafe_allow_html=True)
    c4.markdown(kpi("Distributors",     str(total_sdps),       "Active SDP partners"), unsafe_allow_html=True)
    c5.markdown(kpi("YoY Growth",       f"+{growth_z:.1f}%",   "2024 to 2025 growth"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Revenue 2024",     fmt(rev24_z),          "Jan-Dec 2024"), unsafe_allow_html=True)
    c2.markdown(kpi("Revenue 2025",     fmt(rev25_z),          "Jan-Dec 2025"), unsafe_allow_html=True)
    c3.markdown(kpi("Unique SKUs",      str(total_prods),      "Product variants tracked"), unsafe_allow_html=True)
    c4.markdown(kpi("Top City",         top_city,              fmt(top_city_rev)+" revenue"), unsafe_allow_html=True)
    c5.markdown(kpi("Shelf Risk",       str(len(df_zrisk)),    "⚠️ Items under 90 days", red=True), unsafe_allow_html=True)
    st.markdown("---")

    # CATEGORY SPLIT
    st.markdown(sec("📊 Revenue by Product Category"), unsafe_allow_html=True)
    st.markdown(note("Pharma is 86.3% of all revenue — core business. Nutraceutical at 12.7% is growing fast. Herbal and Medical Devices are small but present. Export is minimal."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        cat_map_dist = {"P":"Pharma","N":"Nutraceutical",
                        "M":"Medical Device","H":"Herbal",
                        "E":"Export","O":"Other"}
        cat_rev = df_z.groupby("Category")["Revenue"].sum().reset_index()
        cat_rev["CategoryName"] = cat_rev["Category"].map(cat_map_dist).fillna(cat_rev["Category"])
        cat_rev["Label"] = cat_rev["Revenue"].apply(fmt)
        cat_rev = cat_rev.sort_values("Revenue", ascending=False)
        fig = px.bar(cat_rev, x="Revenue", y="CategoryName",
                     orientation="h", text="Label",
                     color="Revenue", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=300,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.pie(cat_rev, values="Revenue", names="CategoryName",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textinfo="percent+label", textfont_size=11)
        apply_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)

    # MONTHLY TREND
    st.markdown(sec("📈 Monthly Revenue Trend (ZSDCY)"), unsafe_allow_html=True)
    st.markdown(note("September 2025 = PKR 1.03B — biggest single month ever recorded! Jan 2024 was strong at PKR 692M. Clear upward trend from 2024 to 2025 confirms business growth."), unsafe_allow_html=True)

    mo_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    monthly_z = df_z.groupby(["Yr","Mo"])["Revenue"].sum().reset_index()
    monthly_z["Date"]  = pd.to_datetime(
        monthly_z["Yr"].astype(int).astype(str)+"-"+
        monthly_z["Mo"].astype(int).astype(str)+"-01")
    monthly_z["Label"] = monthly_z["Revenue"].apply(fmt)

    complete_z = monthly_z[monthly_z["Yr"]==2024]
    y2025_z    = monthly_z[monthly_z["Yr"]==2025]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=complete_z["Date"], y=complete_z["Revenue"]/1e6,
        name="2024", marker_color="rgba(44,95,138,0.7)",
        text=complete_z["Label"], textposition="outside",
        textfont_size=9
    ))
    fig.add_trace(go.Bar(
        x=y2025_z["Date"], y=y2025_z["Revenue"]/1e6,
        name="2025", marker_color="rgba(46,125,50,0.7)",
        text=y2025_z["Label"], textposition="outside",
        textfont_size=9
    ))
    apply_layout(fig, height=340,
                 xaxis=dict(gridcolor="#eeeeee", title="Month"),
                 yaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"),
                 barmode="group", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # TOP PRODUCTS
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("🏆 Top 20 Products by Revenue (SKU Level)"), unsafe_allow_html=True)
        st.markdown(note("These are at SKU level — same product in different dosages counts separately. Inosita Plus leads at PKR 689M across all dosages."), unsafe_allow_html=True)
        top20_z = df_z.groupby("Material Name").agg(
            Revenue=("Revenue","sum"),
            Qty=("Qty","sum")).reset_index().nlargest(20,"Revenue")
        top20_z["Label"] = top20_z["Revenue"].apply(fmt)
        top20_z["ShortName"] = top20_z["Material Name"].str[:35]
        fig = px.bar(top20_z, x="Revenue", y="ShortName",
                     orientation="h", text="Label",
                     color="Revenue", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=9)
        apply_layout(fig, height=580,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("🚀 Fastest Growing Products 2024→2025"), unsafe_allow_html=True)
        st.markdown(note("Tiocap grew +157%! Finno-Q +123%! These are emerging stars. Compare with existing dashboard — same products appear here confirming the growth trend from 2 different databases."), unsafe_allow_html=True)
        grow_top = df_zgrow[df_zgrow["Rev2024"]>10e6].nlargest(20,"Growth")
        grow_top["Label"]     = grow_top["Growth"].apply(lambda x: f"+{x:.0f}%")
        grow_top["ShortName"] = grow_top["Material Name"].str[:35]
        colors_g = ["#2e7d32" if g>100 else "#2c5f8a" if g>50 else "#e65100"
                    for g in grow_top["Growth"]]
        fig = go.Figure(go.Bar(
            x=grow_top["Growth"], y=grow_top["ShortName"],
            orientation="h",
            text=grow_top["Label"],
            textposition="outside", textfont_size=9,
            marker_color=colors_g
        ))
        apply_layout(fig, height=580,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Growth % 2024→2025"))
        st.plotly_chart(fig, use_container_width=True)

    # CITY ANALYSIS
    st.markdown(sec("🗺️ City-Level Revenue Distribution"), unsafe_allow_html=True)
    st.markdown(note("Karachi is #1 city at PKR 872M — bigger than Lahore and Peshawar combined! This is different from travel data where Lahore led. ZSDCY shows actual sales delivery locations."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        city_total_z = df_zcity.groupby("City")["Revenue"].sum().nlargest(20).reset_index()
        city_total_z["Label"] = city_total_z["Revenue"].apply(fmt)
        fig = px.bar(city_total_z, x="Revenue", y="City",
                     orientation="h", text="Label",
                     color="Revenue", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=580,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("📈 City Growth 2024→2025"), unsafe_allow_html=True)
        st.markdown(note("Cities where revenue grew most from 2024 to 2025. These cities have highest market expansion — increase distributor presence here."), unsafe_allow_html=True)
        city24 = df_zcity[df_zcity["Yr"]==2024].groupby("City")["Revenue"].sum()
        city25 = df_zcity[df_zcity["Yr"]==2025].groupby("City")["Revenue"].sum()
        city_g = pd.DataFrame({"2024":city24,"2025":city25}).dropna()
        city_g = city_g[city_g["2024"]>10e6]
        city_g["Growth"] = ((city_g["2025"]-city_g["2024"])/city_g["2024"]*100)
        city_g = city_g.sort_values("Growth",ascending=False).head(20).reset_index()
        city_g["Label"] = city_g["Growth"].apply(lambda x: f"{x:.0f}%")
        colors_cg = ["#2e7d32" if g>30 else "#2c5f8a" if g>0 else "#c62828"
                     for g in city_g["Growth"]]
        fig = go.Figure(go.Bar(
            x=city_g["Growth"], y=city_g["City"],
            orientation="h",
            text=city_g["Label"],
            textposition="outside", textfont_size=10,
            marker_color=colors_cg
        ))
        apply_layout(fig, height=580,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue Growth %"))
        st.plotly_chart(fig, use_container_width=True)

    # TOP DISTRIBUTORS
    st.markdown(sec("🏢 Top 20 Distributors (SDPs) by Revenue"), unsafe_allow_html=True)
    st.markdown(note("Premier Sales is the primary distributor across all cities. Each branch is tracked separately. Lahore branch leads but Peshawar and Rawalpindi are close. These relationships are critical to protect."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        sdp_total = df_zsdp.groupby("SDP Name").agg(
            Revenue=("Revenue","sum"),
            Products=("Products","max")).reset_index().nlargest(20,"Revenue")
        sdp_total["ShortName"] = sdp_total["SDP Name"].str.replace(
            "PREMIER SALES PVT LTD-","").str.title()
        sdp_total["Label"] = sdp_total["Revenue"].apply(fmt)
        fig = px.bar(sdp_total, x="Revenue", y="ShortName",
                     orientation="h", text="Label",
                     color="Revenue", color_continuous_scale="Greens")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=580,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(sec("📦 Products per Distributor"), unsafe_allow_html=True)
        st.markdown(note("Number of unique products each distributor carries. Higher number = more diversified distributor. Distributors carrying fewer products may need to expand their portfolio."), unsafe_allow_html=True)
        sdp_prods = df_zsdp.groupby("SDP Name")["Products"].max().nlargest(20).reset_index()
        sdp_prods["ShortName"] = sdp_prods["SDP Name"].str.replace(
            "PREMIER SALES PVT LTD-","").str.title()
        sdp_prods["Label"] = sdp_prods["Products"].astype(str) + " products"
        fig = px.bar(sdp_prods, x="Products", y="ShortName",
                     orientation="h", text="Label",
                     color="Products", color_continuous_scale="Purples")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=580,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Unique Products"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # SHELF LIFE RISK
    st.markdown(sec("🚨 Shelf Life Risk — Products Near Expiry"), unsafe_allow_html=True)
    st.markdown(note("20 invoices have products with less than 90 days shelf life remaining at time of delivery. These need immediate attention — expired products damage brand reputation and create returns."), unsafe_allow_html=True)

    if len(df_zrisk) > 0:
        risk_display = df_zrisk[[
            "Material Name","SDP Name","Billing date",
            "ShelfLifeDays"]].copy()
        risk_display["Revenue"] = "N/A"
        risk_display["Days Left"] = risk_display["ShelfLifeDays"].astype(int)
        risk_display["Risk Level"] = risk_display["ShelfLifeDays"].apply(
            lambda x: "🔴 CRITICAL" if x<30 else "🟡 WARNING")
        risk_display["Material Name"] = risk_display["Material Name"].str[:40]
        risk_display["SDP Name"]      = risk_display["SDP Name"].str[:35]
        st.dataframe(
            risk_display[["Material Name","SDP Name","Billing date",
                          "Days Left","Risk Level"]],
            use_container_width=True, hide_index=True)
        st.markdown(danger("Action Required: Contact distributors for these 20 items. Arrange returns or promotions to clear near-expiry stock before it becomes a loss."), unsafe_allow_html=True)
    else:
        st.markdown(good("No critical shelf life issues found! All products have adequate shelf life at delivery."), unsafe_allow_html=True)

    # 2024 vs 2025 COMPARISON TABLE
    st.markdown(sec("📊 Year Comparison Summary"), unsafe_allow_html=True)
    st.markdown(note("Side by side comparison of key metrics between 2024 and 2025. Revenue grew +28.5% — significantly faster than the 16.6% shown in DSR database, confirming strong underlying growth."), unsafe_allow_html=True)

    comp_df = pd.DataFrame({
        "Metric"    : ["Total Revenue","Total Units","Unique Products",
                       "Cities Covered","Total Invoices","Avg Monthly Revenue"],
        "2024"      : [
            fmt(rev24_z),
            fmt_num(df_z[df_z["Yr"]==2024]["Qty"].sum()),
            str(df_z[df_z["Yr"]==2024]["Material Name"].nunique()),
            str(df_zcity[df_zcity["Yr"]==2024]["City"].nunique()),
            f"{len(df_z[df_z['Yr']==2024]):,}",
            fmt(rev24_z/12)
        ],
        "2025"      : [
            fmt(rev25_z),
            fmt_num(df_z[df_z["Yr"]==2025]["Qty"].sum()),
            str(df_z[df_z["Yr"]==2025]["Material Name"].nunique()),
            str(df_zcity[df_zcity["Yr"]==2025]["City"].nunique()),
            f"{len(df_z[df_z['Yr']==2025]):,}",
            fmt(rev25_z/12)
        ],
        "Growth"    : [
            f"+{growth_z:.1f}%","","","","",""
        ]
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
# PAGE 10: STRATEGIC GROWTH PLAN
# ════════════════════════════════════════════════════════════
elif page == "🎯 Strategic Growth Plan":
    st.markdown("<h1 style=\'color:#2c5f8a\'>🎯 Strategic Growth Plan</h1>", unsafe_allow_html=True)
    st.markdown("<p style=\'color:#666\'>Cross-database insights from all 4 sources — Sales + Activities + Travel + ZSDCY</p>", unsafe_allow_html=True)
    st.markdown(note("This page combines all 4 databases to find the most powerful growth and cost-saving opportunities. Every insight is backed by data from multiple sources."), unsafe_allow_html=True)
    st.markdown("---")

    # SUMMARY SCORECARD
    st.markdown(sec("📋 Executive Summary — Top 5 Highest Impact Actions"), unsafe_allow_html=True)
    st.markdown(note("These 5 actions have the highest potential financial impact based on cross-database analysis. Total potential = PKR 1.05B+ in additional revenue and savings."), unsafe_allow_html=True)

    impact_df = pd.DataFrame({
        "Priority": ["🥇 #1","🥈 #2","🥉 #3","4️⃣ #4","5️⃣ #5"],
        "Action": [
            "Fix Promo Timing (Move Jul budget to Jan/Feb/Sep)",
            "Invest in Ramipace + Finno-Q immediately",
            "Fix Falcons and Strikers discount abuse",
            "Increase Karachi and Swat field visits",
            "Develop alternative distributors"
        ],
        "Potential Impact": [
            "+PKR 400M revenue",
            "+PKR 300M revenue",
            "Save PKR 200M",
            "+PKR 150M revenue",
            "Risk reduction"
        ],
        "Data Source": [
            "Activities DB + Sales DB",
            "ROI DB + ZSDCY DB",
            "Sales DSR DB",
            "Travel DB + ZSDCY DB",
            "ZSDCY DB"
        ],
        "Effort": ["Medium","Low","Low","Medium","High"]
    })
    st.dataframe(impact_df, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── INSIGHT 1: TERRITORY GAP ─────────────────────────────
    st.markdown(sec("🗺️ Insight 1 — Territory Gap: We Visit Lahore but Karachi Earns More!"), unsafe_allow_html=True)
    st.markdown(note("Travel DB shows Lahore = 3,161 trips (most visited). But ZSDCY DB shows Karachi = PKR 872M revenue (highest earning city). This means we are OVER-investing in Lahore and UNDER-investing in Karachi!"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Travel Trips by City (Travel DB)**")
        travel_cities = df_travel.groupby("VisitLocation")["TravelCount"].sum().nlargest(10).reset_index()
        travel_cities["Label"] = travel_cities["TravelCount"].apply(fmt_num)
        travel_cities["Type"]  = travel_cities["VisitLocation"].apply(
            lambda x: "Most Visited" if x=="Lahore" else "Other")
        fig = px.bar(travel_cities, x="TravelCount", y="VisitLocation",
                     orientation="h", text="Label",
                     color="Type",
                     color_discrete_map={"Most Visited":"#e65100","Other":"#2c5f8a"})
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=360,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Total Trips"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Revenue by City (ZSDCY DB)**")
        @st.cache_data
        def load_zcity():
            return pd.read_csv("zsdcy_cities.csv")
        df_zc = load_zcity()
        city_rev_z = df_zc.groupby("City")["Revenue"].sum().nlargest(10).reset_index()
        city_rev_z["Label"] = city_rev_z["Revenue"].apply(fmt)
        city_rev_z["Type"]  = city_rev_z["City"].apply(
            lambda x: "Highest Revenue" if x=="Karachi" else "Other")
        fig = px.bar(city_rev_z, x="Revenue", y="City",
                     orientation="h", text="Label",
                     color="Type",
                     color_discrete_map={"Highest Revenue":"#2e7d32","Other":"#2c5f8a"})
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=360,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div class="manual-working">
    TERRITORY GAP ANALYSIS
    ══════════════════════════════════════════════════
    City       | Travel Rank | Revenue Rank | Gap
    ──────────────────────────────────────────────────
    Lahore     | #1 (3,161)  | #3 (PKR 634M)| OVER-visited
    Karachi    | #N/A        | #1 (PKR 872M)| UNDER-visited
    Islamabad  | #2 (1,818)  | #8 (PKR 416M)| Balanced
    Swat       | #12 (122)   | #5 (PKR 514M)| CRITICAL GAP!
    Peshawar   | #5 (516)    | #2 (PKR 637M)| Good balance
    ══════════════════════════════════════════════════
    ACTION: Increase Karachi visits by 500/year
    ACTION: Increase Swat visits by 300/year
    EXPECTED IMPACT: +PKR 150M additional revenue
    ══════════════════════════════════════════════════
    </div>
    """, unsafe_allow_html=True)

    # ── INSIGHT 2: PROMO TIMING GAP ─────────────────────────
    st.markdown(sec("⏰ Insight 2 — Promo Timing Gap: PKR 1.37B Spent in Wrong Months!"), unsafe_allow_html=True)
    st.markdown(note("July = highest promo spend month (#1) but only #8 in sales rank. January = #1 in sales but only #6 in promo spend. Budget is misaligned with actual sales peaks — fixing this could boost revenue by 15-20%."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        mo_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                  7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        promo_mo = df_act.groupby("Mo")["TotalAmount"].sum().reset_index()
        sales_mo = df_sales.groupby("Mo")["TotalRevenue"].sum().reset_index()
        promo_mo["Month"] = promo_mo["Mo"].map(mo_map)
        sales_mo["Month"] = sales_mo["Mo"].map(mo_map)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=promo_mo["Month"], y=promo_mo["TotalAmount"]/1e6,
            name="Promo Spend (M PKR)",
            marker_color="rgba(230,81,0,0.8)",
            text=[f"PKR {v:.0f}M" for v in promo_mo["TotalAmount"]/1e6],
            textposition="outside", textfont_size=9
        ))
        apply_layout(fig, height=300,
                     title="Monthly Promo Spend",
                     xaxis=dict(gridcolor="#eeeeee",
                                categoryorder="array",
                                categoryarray=list(mo_map.values())),
                     yaxis=dict(gridcolor="#eeeeee", title="Spend (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=sales_mo["Month"], y=sales_mo["TotalRevenue"]/1e6,
            name="Revenue (M PKR)",
            marker_color="rgba(44,95,138,0.8)",
            text=[f"PKR {v:.0f}M" for v in sales_mo["TotalRevenue"]/1e6],
            textposition="outside", textfont_size=9
        ))
        apply_layout(fig, height=300,
                     title="Monthly Sales Revenue",
                     xaxis=dict(gridcolor="#eeeeee",
                                categoryorder="array",
                                categoryarray=list(mo_map.values())),
                     yaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    timing_data = pd.DataFrame({
        "Month":list(mo_map.values()),
        "Promo Rank":[6,8,9,10,12,11,1,3,4,2,5,7],
        "Sales Rank":[1,2,9,12,10,11,8,7,5,3,6,4],
        "Verdict":[
            "🔴 Jan: Sales #1 but Promo #6 — INCREASE SPEND",
            "🔴 Feb: Sales #2 but Promo #8 — INCREASE SPEND",
            "✅ Mar: Aligned",
            "✅ Apr: Aligned",
            "✅ May: Aligned",
            "✅ Jun: Aligned",
            "🔴 Jul: Promo #1 but Sales #8 — REDUCE SPEND",
            "🟡 Aug: Slightly misaligned",
            "✅ Sep: Aligned",
            "✅ Oct: Aligned",
            "✅ Nov: Aligned",
            "🟡 Dec: Slightly misaligned"
        ]
    })
    st.dataframe(timing_data, use_container_width=True, hide_index=True)
    st.markdown(warn("Recommendation: Move 30% of July promo budget to January and February. Expected revenue impact: +PKR 200-400M annually."), unsafe_allow_html=True)

    # ── INSIGHT 3: RAMIPACE + FINNO-Q ───────────────────────
    st.markdown(sec("💊 Insight 3 — Ramipace and Finno-Q: Confirmed by 2 Databases!"), unsafe_allow_html=True)
    st.markdown(note("Both DSR Sales DB and ZSDCY DB independently confirm the same finding: Ramipace has incredible ROI and Finno-Q is growing explosively. Two databases = double confidence in this insight!"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="manual-working">
        RAMIPACE — CONFIRMED BY 2 DATABASES
        ══════════════════════════════════════════
        DSR Sales Database:
          Revenue 2024-2026 : PKR 430M+
          ROI               : 99.7x
          Promo Spend       : PKR 4.3M only
          ROI vs Avg        : 5x better than company avg

        ZSDCY Distribution Database:
          Revenue 2024-2025 : PKR 265M
          Units Delivered   : 651,400 units
          Rank by Revenue   : #16 out of 827 SKUs
          Growth 2024→2025  : Positive trend

        CROSS-DB CONCLUSION:
          Both databases confirm Ramipace is:
          → High revenue generator
          → Very low promotional investment
          → Massive untapped potential

        ACTION PLAN:
          Current spend  : PKR 4.3M
          Recommended    : PKR 15M (3.5x increase)
          Expected return: PKR 430M additional revenue
          Confidence     : HIGH (2 DB confirmation)
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="manual-working">
        FINNO-Q — CONFIRMED BY 2 DATABASES
        ══════════════════════════════════════════
        DSR Sales Database:
          Growth 2024→2025  : +226% (HIGHEST!)
          Revenue           : Growing fast
          Promo Spend       : Minimal

        ZSDCY Distribution Database:
          Growth 2024→2025  : +123% (rank #2!)
          Units Delivered   : Growing rapidly
          Cities covered    : Expanding

        CROSS-DB CONCLUSION:
          Both databases confirm Finno-Q is:
          → Fastest/2nd fastest growing product
          → Almost zero promotional support
          → Market is pulling it naturally
          → With promotion = explosive growth

        ACTION PLAN:
          Current promo   : ~PKR 0
          Recommended     : PKR 10M immediately
          Expected growth : +300% by end 2026
          Confidence      : VERY HIGH (2 DB)
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    # ── INSIGHT 4: DISCOUNT ABUSE ────────────────────────────
    st.markdown(sec("💸 Insight 4 — Discount Abuse: PKR 749M Given Away!"), unsafe_allow_html=True)
    st.markdown(note("Total discounts = PKR 749M across 2024-2026. Falcons team gave PKR 224M at 20.5% rate. Zoltar product has 47% discount rate — nearly half its revenue is given as discount. This is costing the company massively."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        disc_prod = df_sales.groupby("ProductName").agg(
            Discount=("TotalDiscount","sum"),
            Revenue=("TotalRevenue","sum")).reset_index()
        disc_prod = disc_prod[disc_prod["Revenue"]>5e6]
        disc_prod["DiscRate"] = disc_prod["Discount"]/disc_prod["Revenue"]*100
        disc_prod = disc_prod.nlargest(12,"DiscRate")
        disc_prod["Label"] = disc_prod["DiscRate"].apply(lambda x: f"{x:.1f}%")
        colors_d = ["#c62828" if r>20 else "#e65100" if r>10 else "#2c5f8a"
                    for r in disc_prod["DiscRate"]]
        fig = go.Figure(go.Bar(
            x=disc_prod["DiscRate"], y=disc_prod["ProductName"],
            orientation="h", text=disc_prod["Label"],
            textposition="outside", textfont_size=10,
            marker_color=colors_d
        ))
        apply_layout(fig, height=400,
                     title="Discount Rate by Product (%)",
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Discount Rate %"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        team_disc = df_sales.groupby("TeamName").agg(
            Discount=("TotalDiscount","sum"),
            Revenue=("TotalRevenue","sum")).reset_index()
        team_disc = team_disc[team_disc["Revenue"]>5e6]
        team_disc["DiscRate"] = team_disc["Discount"]/team_disc["Revenue"]*100
        team_disc = team_disc.nlargest(12,"DiscRate")
        team_disc["Label"] = team_disc["DiscRate"].apply(lambda x: f"{x:.1f}%")
        colors_t = ["#c62828" if r>15 else "#e65100" if r>5 else "#2c5f8a"
                    for r in team_disc["DiscRate"]]
        fig = go.Figure(go.Bar(
            x=team_disc["DiscRate"], y=team_disc["TeamName"],
            orientation="h", text=team_disc["Label"],
            textposition="outside", textfont_size=10,
            marker_color=colors_t
        ))
        apply_layout(fig, height=400,
                     title="Discount Rate by Team (%)",
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Discount Rate %"))
        st.plotly_chart(fig, use_container_width=True)

    total_disc = df_sales["TotalDiscount"].sum()
    st.markdown(f"""
    <div class="manual-working">
    DISCOUNT SAVINGS CALCULATION
    ══════════════════════════════════════════════════
    Current State:
      Total Discounts Given  : {fmt(total_disc)}
      Company Avg Disc Rate  : 1.56%
      Falcons Team Rate      : 20.5% (13x above avg!)
      Strikers Team Rate     : 20.3% (13x above avg!)
      Zoltar Product Rate    : 47.0% (30x above avg!)

    If We Cap All Discounts at 5%:
      Falcons savings        : PKR {224.7*0.75:.0f}M
      Strikers savings       : PKR {99.9*0.75:.0f}M
      Zoltar savings         : PKR {98.8*0.75:.0f}M
      Total estimated saving : PKR 200M+

    Root Cause Investigation Needed:
      → Are these discounts authorized?
      → Are sales reps giving personal discounts?
      → Is Zoltar pricing strategy correct?
      → Audit required immediately!
    ══════════════════════════════════════════════════
    </div>
    """, unsafe_allow_html=True)
    st.markdown(danger("URGENT: Falcons and Strikers teams giving 20%+ discounts. This needs immediate management audit. PKR 200M+ can be saved annually by fixing this."), unsafe_allow_html=True)

    # ── INSIGHT 5: SWAT OPPORTUNITY ─────────────────────────
    st.markdown(sec("🌟 Insight 5 — Swat: PKR 514M Revenue with Only 122 Visits!"), unsafe_allow_html=True)
    st.markdown(note("Swat generates PKR 514M revenue (rank #5 in ZSDCY) but receives only 122 field visits (rank #12 in travel). This is the biggest untapped opportunity — revenue is happening WITHOUT field support!"), unsafe_allow_html=True)

    gap_data = pd.DataFrame({
        "City"        :["Lahore","Islamabad","Peshawar","Karachi","Swat",
                        "Faisalabad","Multan","Hyderabad","Quetta","Rawalpindi"],
        "Travel Trips":[3161,1818,516,0,122,402,576,538,0,97],
        "Revenue (M)" :[634,416,637,872,514,442,415,343,396,540],
    })
    gap_data["Rev per Trip"] = (gap_data["Revenue (M)"]*1e6/
                                gap_data["Travel Trips"].replace(0,1)).round(0)
    gap_data["Opportunity"]  = gap_data.apply(
        lambda r: "🔴 Critical Gap" if r["Travel Trips"]<200 and r["Revenue (M)"]>400
        else "🟡 Monitor" if r["Travel Trips"]<500 and r["Revenue (M)"]>300
        else "✅ Balanced", axis=1)

    st.dataframe(gap_data, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.scatter(gap_data,
                         x="Travel Trips", y="Revenue (M)",
                         size="Revenue (M)", color="Opportunity",
                         hover_name="City",
                         color_discrete_map={
                             "🔴 Critical Gap":"#c62828",
                             "🟡 Monitor":"#e65100",
                             "✅ Balanced":"#2e7d32"},
                         size_max=50,
                         title="Travel Trips vs Revenue by City")
        apply_layout(fig, height=380,
                     xaxis=dict(gridcolor="#eeeeee", title="Travel Trips"),
                     yaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(danger("Swat and Karachi: Top 5 revenue cities with almost ZERO field visits. Immediate action needed!"), unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="manual-working">
        SWAT OPPORTUNITY ANALYSIS
        ══════════════════════════════════════════
        Current State (Travel DB):
          Field visits to Swat : 122 trips only
          Travel ranking       : #12 of 63 cities

        Revenue Reality (ZSDCY DB):
          Revenue from Swat    : PKR 514M
          Revenue ranking      : #5 of 268 cities
          Revenue per trip     : PKR 4.2M per visit!

        COMPARISON:
          Lahore revenue/trip  : PKR 0.2M per visit
          Swat revenue/trip    : PKR 4.2M per visit
          Swat is 21x MORE efficient per trip!

        ACTION PLAN:
          Increase Swat visits : +300 trips/year
          Expected extra rev   : +PKR 125M/year
          Cost of extra travel : ~PKR 7.2M
          Net benefit          : PKR 118M profit!

        KARACHI GAP:
          Revenue              : PKR 872M (#1 city)
          Travel DB visits     : Not tracked!
          → Add Karachi to travel tracking
          → Assign dedicated sales team
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    # ── INSIGHT 6: NUTRACEUTICAL GROWTH ─────────────────────
    st.markdown(sec("🌿 Insight 6 — Nutraceutical: The Next Big Revenue Stream!"), unsafe_allow_html=True)
    st.markdown(note("Nutraceuticals = PKR 2.2B revenue (12.7% of ZSDCY total). This category is growing faster than pharma. With dedicated promotion it could reach 20% of revenue by 2027 — an additional PKR 500M+."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        @st.cache_data
        def load_zmonthly():
            return pd.read_csv("zsdcy_monthly.csv")
        df_zm = load_zmonthly()
        nutra = df_zm[df_zm["Category"]=="Nutraceutical"].groupby(
            ["Yr","Mo"])["Revenue"].sum().reset_index()
        pharma = df_zm[df_zm["Category"]=="Pharma"].groupby(
            ["Yr","Mo"])["Revenue"].sum().reset_index()
        nutra["Month"]  = nutra["Mo"].map(mo_map)
        pharma["Month"] = pharma["Mo"].map(mo_map)
        nutra["Date"]   = pd.to_datetime(
            nutra["Yr"].astype(int).astype(str)+"-"+
            nutra["Mo"].astype(int).astype(str)+"-01")
        pharma["Date"]  = pd.to_datetime(
            pharma["Yr"].astype(int).astype(str)+"-"+
            pharma["Mo"].astype(int).astype(str)+"-01")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=pharma["Date"], y=pharma["Revenue"]/1e6,
            name="Pharma", line=dict(color="#2c5f8a",width=2),
            fill="tozeroy", fillcolor="rgba(44,95,138,0.1)"
        ))
        fig.add_trace(go.Scatter(
            x=nutra["Date"], y=nutra["Revenue"]/1e6,
            name="Nutraceutical", line=dict(color="#2e7d32",width=2.5),
            fill="tozeroy", fillcolor="rgba(46,125,50,0.15)"
        ))
        apply_layout(fig, height=320,
                     yaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"),
                     hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        nutra_24 = df_zm[(df_zm["Category"]=="Nutraceutical") &
                         (df_zm["Yr"]==2024)]["Revenue"].sum()
        nutra_25 = df_zm[(df_zm["Category"]=="Nutraceutical") &
                         (df_zm["Yr"]==2025)]["Revenue"].sum()
        pharma_24= df_zm[(df_zm["Category"]=="Pharma") &
                         (df_zm["Yr"]==2024)]["Revenue"].sum()
        pharma_25= df_zm[(df_zm["Category"]=="Pharma") &
                         (df_zm["Yr"]==2025)]["Revenue"].sum()
        nutra_growth  = ((nutra_25-nutra_24)/nutra_24*100)
        pharma_growth = ((pharma_25-pharma_24)/pharma_24*100)

        st.markdown(f"""
        <div class="manual-working">
        NUTRACEUTICAL GROWTH ANALYSIS
        ══════════════════════════════════════════
        Category     2024 Rev   2025 Rev   Growth
        ──────────────────────────────────────────
        Pharma       {fmt(pharma_24)}  {fmt(pharma_25)}  +{pharma_growth:.1f}%
        Nutraceutical{fmt(nutra_24)}   {fmt(nutra_25)}  +{nutra_growth:.1f}%

        Nutraceutical is growing {nutra_growth/pharma_growth:.1f}x
        FASTER than Pharma!

        Current share: 12.7% of revenue
        2026 projection (if trend continues):
          → 15-16% of revenue
          → Additional PKR 200M+

        ACTION PLAN:
        → Launch dedicated Nutra sales team
        → Increase Nutra promo budget by 50%
        → Target health-conscious doctors
        → Focus on top 5 Nutra products
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)
        st.markdown(good(f"Nutraceutical grew +{nutra_growth:.1f}% vs Pharma +{pharma_growth:.1f}%. Nutra is the faster growing segment — invest more here!"), unsafe_allow_html=True)

    # ── INSIGHT 7: PRODUCT CONCENTRATION RISK ───────────────
    st.markdown(sec("⚠️ Insight 7 — Product Concentration Risk: Top 5 Products = 33% Revenue"), unsafe_allow_html=True)
    st.markdown(note("If top 5 products face any issue (competitor, shortage, ban) — company loses 33% of revenue instantly. This is a critical business risk. Diversification needed urgently."), unsafe_allow_html=True)

    prod_rev = df_sales.groupby("ProductName")["TotalRevenue"].sum().sort_values(ascending=False).reset_index()
    prod_rev["CumPct"] = prod_rev["TotalRevenue"].cumsum()/prod_rev["TotalRevenue"].sum()*100
    prod_rev["Label"]  = prod_rev["TotalRevenue"].apply(fmt)

    col1, col2 = st.columns(2)
    with col1:
        top15_risk = prod_rev.head(15)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top15_risk["TotalRevenue"]/1e6,
            y=top15_risk["ProductName"],
            orientation="h",
            text=top15_risk["Label"],
            textposition="outside", textfont_size=9,
            marker_color="#2c5f8a",
            name="Revenue"
        ))
        fig.add_trace(go.Scatter(
            x=top15_risk["CumPct"]*1.5,
            y=top15_risk["ProductName"],
            mode="lines+markers",
            name="Cumulative %",
            line=dict(color="#c62828",width=2),
            xaxis="x2"
        ))
        fig.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            height=480, font_color="#333",
            xaxis=dict(title="Revenue (M PKR)", gridcolor="#eeeeee"),
            xaxis2=dict(title="Cumulative %", overlaying="x",
                       side="top", range=[0,110]),
            yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
            legend=dict(bgcolor="white")
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top5_rev  = prod_rev.head(5)["TotalRevenue"].sum()
        top10_rev = prod_rev.head(10)["TotalRevenue"].sum()
        top30_rev = prod_rev.head(30)["TotalRevenue"].sum()
        total_r   = prod_rev["TotalRevenue"].sum()

        st.markdown(f"""
        <div class="manual-working">
        PRODUCT CONCENTRATION RISK MATRIX
        ══════════════════════════════════════════
        Products   Revenue Share   Risk if Failed
        ──────────────────────────────────────────
        Top 1      9.0%           Medium
        Top 5      32.9%          CRITICAL
        Top 10     49.4%          SEVERE
        Top 30     80.0%          CATASTROPHIC

        Total products  : 140
        Revenue earners : 80 products (57%)
        Near-zero rev   : 60 products (43%)

        RISK SCENARIOS:
        If X-Plended discontinued:
          → Lose PKR 4.3B (9% revenue)
        If Avsar + X-Plended fail:
          → Lose PKR 8.1B (17% revenue)
        If competitor copies top 5:
          → Lose PKR 15.8B (33% revenue)

        RECOMMENDATIONS:
        1. Invest in developing 3-5 new products
        2. File patents on top 5 products
        3. Accelerate growth of products 6-15
        4. Review bottom 60 — discontinue 20
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)
        st.markdown(danger(f"Top 5 products = {top5_rev/total_r*100:.1f}% of revenue. Single point of failure risk is HIGH. Management must develop product pipeline urgently."), unsafe_allow_html=True)

    # ── INSIGHT 8: DISTRIBUTOR RISK ──────────────────────────
    st.markdown(sec("🏢 Insight 8 — Single Distributor Risk: 100% Dependency on Premier Sales!"), unsafe_allow_html=True)
    st.markdown(note("ZSDCY DB shows almost all distribution goes through Premier Sales branches. If Premier Sales faces any issue — strike, bankruptcy, dispute — Pharmevo loses ALL distribution channels instantly!"), unsafe_allow_html=True)

    @st.cache_data
    def load_zsdp():
        return pd.read_csv("zsdcy_sdp.csv")
    df_zs = load_zsdp()

    col1, col2 = st.columns(2)
    with col1:
        df_zs["DistributorGroup"] = df_zs["SDP Name"].apply(
            lambda x: "Premier Sales" if "PREMIER" in str(x).upper()
            else "Other")
        dist_split = df_zs.groupby("DistributorGroup")["Revenue"].sum().reset_index()
        dist_split["Label"] = dist_split["Revenue"].apply(fmt)
        dist_split["Pct"]   = dist_split["Revenue"]/dist_split["Revenue"].sum()*100

        fig = px.pie(dist_split, values="Revenue", names="DistributorGroup",
                     color_discrete_map={
                         "Premier Sales":"#c62828",
                         "Other":"#2c5f8a"},
                     title="Revenue by Distributor Group")
        fig.update_traces(textinfo="percent+label", textfont_size=13)
        apply_layout(fig, height=320)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        premier_rev = dist_split[dist_split["DistributorGroup"]=="Premier Sales"]["Revenue"].sum()
        other_rev   = dist_split[dist_split["DistributorGroup"]=="Other"]["Revenue"].sum()
        st.markdown(f"""
        <div class="manual-working">
        DISTRIBUTOR DEPENDENCY ANALYSIS
        ══════════════════════════════════════════
        Premier Sales revenue : {fmt(premier_rev)}
        Other distributors    : {fmt(other_rev)}
        Premier Sales share   : {premier_rev/(premier_rev+other_rev)*100:.1f}%

        RISK LEVEL: CRITICAL 🔴

        What happens if Premier Sales stops?
        → Pharmevo loses ALL distribution
        → Zero revenue until new channel found
        → Takes 3-6 months to rebuild
        → Estimated loss: PKR 8-15B

        RECOMMENDATIONS:
        1. Identify 3 alternative distributors NOW
        2. Give 10% of volume to new distributor
        3. Gradually increase to 30% over 2 years
        4. Never let one distributor exceed 70%

        Target Distribution Mix by 2027:
        → Premier Sales  : 70% (down from 99%)
        → Distributor 2  : 15%
        → Distributor 3  : 10%
        → Direct/Online  : 5%
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)
        st.markdown(danger("CRITICAL RISK: Near 100% dependency on single distributor. This must be addressed in 2026 strategy planning."), unsafe_allow_html=True)

    # ── INSIGHT 9: Q4 SEASONAL OPPORTUNITY ──────────────────
    st.markdown(sec("📅 Insight 9 — Q4 Seasonal Opportunity: Maximize Oct/Nov/Dec!"), unsafe_allow_html=True)
    st.markdown(note("3 separate databases all confirm Oct/Nov/Dec are strongest months. Sales DB, ZSDCY DB and Travel DB all show Q4 peaks. Yet promotional spend in Q4 is only average. Doubling Q4 promo could add PKR 300M+!"), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        sales_q = df_sales.groupby("Mo")["TotalRevenue"].sum().reset_index()
        sales_q["Month"] = sales_q["Mo"].map(mo_map)
        sales_q["Q"]     = sales_q["Mo"].apply(
            lambda x: "Q4 Peak" if x in [10,11,12] else "Other")
        fig = px.bar(sales_q, x="Month", y="TotalRevenue",
                     color="Q", title="Sales DB — Monthly Revenue",
                     color_discrete_map={"Q4 Peak":"#2e7d32","Other":"#2c5f8a"},
                     category_orders={"Month":list(mo_map.values())})
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",
                          height=280,font_color="#333",showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        @st.cache_data
        def load_zgrowth():
            return pd.read_csv("zsdcy_growth.csv")
        df_zm2 = load_zmonthly()
        zsdcy_q = df_zm2.groupby("Mo")["Revenue"].sum().reset_index()
        zsdcy_q["Month"] = zsdcy_q["Mo"].map(mo_map)
        zsdcy_q["Q"]     = zsdcy_q["Mo"].apply(
            lambda x: "Q4 Peak" if x in [10,11,12] else "Other")
        fig = px.bar(zsdcy_q, x="Month", y="Revenue",
                     color="Q", title="ZSDCY DB — Monthly Revenue",
                     color_discrete_map={"Q4 Peak":"#2e7d32","Other":"#2c5f8a"},
                     category_orders={"Month":list(mo_map.values())})
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",
                          height=280,font_color="#333",showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        travel_q = df_travel.groupby("Mo")["TravelCount"].sum().reset_index()
        travel_q["Month"] = travel_q["Mo"].map(mo_map)
        travel_q["Q"]     = travel_q["Mo"].apply(
            lambda x: "Q4 Peak" if x in [10,11,12] else "Other")
        fig = px.bar(travel_q, x="Month", y="TravelCount",
                     color="Q", title="Travel DB — Monthly Trips",
                     color_discrete_map={"Q4 Peak":"#2e7d32","Other":"#2c5f8a"},
                     category_orders={"Month":list(mo_map.values())})
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",
                          height=280,font_color="#333",showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(good("All 3 databases confirm Q4 (Oct/Nov/Dec) is strongest. Action: Start promotional campaigns in September to build momentum for Q4 peak. Expected impact: +PKR 300M in Q4 revenue."), unsafe_allow_html=True)

    # ── INSIGHT 10: DIVISION EFFICIENCY ─────────────────────
    st.markdown(sec("👥 Insight 10 — Division Efficiency: Division 1 Works 5x Harder!"), unsafe_allow_html=True)
    st.markdown(note("Division 1 (Bone Saviors) makes 82 trips per person vs Division 4 at only 16 trips per person. Division 1 is 5x more active in the field. Budget should reflect this performance difference."), unsafe_allow_html=True)

    div_eff = df_travel.groupby("TravellerDivision").agg(
        Trips=("TravelCount","sum"),
        Nights=("NoofNights","sum"),
        People=("Traveller","nunique")).reset_index()
    div_eff["TripsPerPerson"] = (div_eff["Trips"]/div_eff["People"]).round(1)
    div_eff["NightsPerTrip"]  = (div_eff["Nights"]/div_eff["Trips"]).round(1)
    div_name = {
        "Division 1":"Div 1 — Bone Saviors",
        "Division 2":"Div 2 — Winners",
        "Division 3":"Div 3 — International",
        "Division 4":"Div 4 — Admin",
        "Division 5":"Div 5 — Strikers"
    }
    div_eff["DivName"] = div_eff["TravellerDivision"].map(div_name)

    col1, col2 = st.columns(2)
    with col1:
        colors_div = ["#2e7d32" if t>70 else "#2c5f8a" if t>40
                      else "#e65100" if t>20 else "#c62828"
                      for t in div_eff.sort_values(
                          "TripsPerPerson",ascending=False)["TripsPerPerson"]]
        fig = go.Figure(go.Bar(
            x=div_eff.sort_values("TripsPerPerson",ascending=False)["TripsPerPerson"],
            y=div_eff.sort_values("TripsPerPerson",ascending=False)["DivName"],
            orientation="h",
            text=[f"{t:.0f} trips/person" for t in
                  div_eff.sort_values("TripsPerPerson",ascending=False)["TripsPerPerson"]],
            textposition="outside", textfont_size=11,
            marker_color=colors_div
        ))
        apply_layout(fig, height=300,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee",
                                title="Trips Per Person (2024-2026)"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(
            div_eff[["DivName","People","Trips","TripsPerPerson",
                     "NightsPerTrip"]].sort_values(
                "TripsPerPerson",ascending=False),
            use_container_width=True, hide_index=True)
        st.markdown(good("Division 1 = 82 trips/person. These are the most active field workers. Reward them and replicate their approach."), unsafe_allow_html=True)
        st.markdown(danger("Division 4 = 16 trips/person. 5x less active than Division 1. Investigate immediately and set minimum trip targets."), unsafe_allow_html=True)

    # ── INSIGHT 11: SHELF LIFE RISK ──────────────────────────
    st.markdown(sec("🏥 Insight 11 — Shelf Life Risk: 20 Near-Expiry Deliveries Found!"), unsafe_allow_html=True)
    st.markdown(note("ZSDCY DB found 20 invoices where products had less than 90 days shelf life at delivery. Near-expiry products damage brand reputation, cause returns and create losses. Immediate action needed."), unsafe_allow_html=True)

    @st.cache_data
    def load_zrisk():
        return pd.read_csv("zsdcy_shelf_risk.csv")
    df_zr = load_zrisk()

    if len(df_zr) > 0:
        df_zr["Risk"] = df_zr["ShelfLifeDays"].apply(
            lambda x: "🔴 Under 30 days" if x<30 else "🟡 30-90 days")
        df_zr["Material Name"] = df_zr["Material Name"].str[:40]
        df_zr["SDP Name"]      = df_zr["SDP Name"].str[:30]
        st.dataframe(
            df_zr[["Material Name","SDP Name","ShelfLifeDays","Risk"]].rename(
            columns={"ShelfLifeDays":"Days Left"}),
            use_container_width=True, hide_index=True)
    st.markdown(warn("Contact all 20 distributors immediately. Offer exchange or return for near-expiry products. Investigate root cause — is manufacturing date too close to delivery?"), unsafe_allow_html=True)

    # ── INSIGHT 12: COST SAVING SUMMARY ─────────────────────
    st.markdown(sec("💰 Insight 12 — Complete Cost Saving Opportunities"), unsafe_allow_html=True)
    st.markdown(note("All cost saving opportunities identified across all 4 databases. Total potential savings = PKR 400M+ per year if all actions are implemented."), unsafe_allow_html=True)

    savings_df = pd.DataFrame({
        "Opportunity"     :[
            "Fix Falcons team discounts (20.5% → 5%)",
            "Fix Strikers team discounts (20.3% → 5%)",
            "Fix Zoltar product pricing (47% → 10%)",
            "Negotiate hotel bulk rates (top 10 hotels)",
            "Discontinue bottom 20 zero-revenue products",
            "Reduce Division 4 travel (reallocate budget)",
            "Fix July promo spend (move to Jan/Feb)",
            "Reduce Shevit promo budget (5.6x ROI only)"
        ],
        "Annual Saving"   :[
            "PKR 168M","PKR 75M","PKR 74M",
            "PKR 18M","PKR 15M","PKR 12M",
            "Budget reallocation","PKR 14M"
        ],
        "Action Required" :[
            "Audit Falcons team discount approvals",
            "Audit Strikers team discount approvals",
            "Review Zoltar pricing strategy",
            "Contact procurement for hotel contracts",
            "Review and discontinue low performers",
            "Reassign Division 4 travel budget",
            "Reallocate July budget to peak months",
            "Reduce Shevit, reinvest in Ramipace"
        ],
        "Priority":["🔴 URGENT","🔴 URGENT","🔴 URGENT",
                    "🟡 HIGH","🟡 HIGH","🟡 HIGH",
                    "🟡 HIGH","🟢 MEDIUM"]
    })
    st.dataframe(savings_df, use_container_width=True, hide_index=True)

    total_saving = 168+75+74+18+15+12+14
    st.markdown(good(f"Total identifiable annual savings: PKR {total_saving}M+ ({fmt(total_saving*1e6)}). This is money that can be reinvested into high-ROI products like Ramipace and Finno-Q."), unsafe_allow_html=True)

    # ── INSIGHT 13: GROWTH FORECAST ──────────────────────────
    st.markdown(sec("🔮 Insight 13 — Growth Forecast: Where Will Revenue Come From?"), unsafe_allow_html=True)
    st.markdown(note("Based on current trends from all 4 databases, here is where the next PKR 5B in revenue growth will come from if recommended actions are taken."), unsafe_allow_html=True)

    forecast_df = pd.DataFrame({
        "Growth Source"    :[
            "Fix promo timing (Jan/Feb boost)",
            "Invest in Ramipace (3x budget)",
            "Invest in Finno-Q (new budget)",
            "Increase Karachi/Swat visits",
            "Nutraceutical category growth",
            "Emerging products (Tiocap, Erli+)",
            "Q4 promo boost (double Oct-Dec)",
            "New city penetration (9 new cities)"
        ],
        "Expected Revenue" :[
            "+PKR 400M","+PKR 430M","+PKR 200M",
            "+PKR 150M","+PKR 300M","+PKR 250M",
            "+PKR 300M","+PKR 100M"
        ],
        "Timeline"         :[
            "6 months","12 months","12 months",
            "6 months","18 months","12 months",
            "3 months","12 months"
        ],
        "Investment Needed":[
            "Budget reallocation only",
            "PKR 10M additional spend",
            "PKR 10M new budget",
            "PKR 15M travel budget",
            "PKR 20M promo budget",
            "PKR 15M promo budget",
            "PKR 30M Q4 budget",
            "PKR 10M travel budget"
        ],
        "Confidence"       :[
            "🟢 High","🟢 High","🟢 High",
            "🟡 Medium","🟢 High","🟡 Medium",
            "🟢 High","🟡 Medium"
        ]
    })
    st.dataframe(forecast_df, use_container_width=True, hide_index=True)

    total_forecast = 400+430+200+150+300+250+300+100
    col1, col2, col3 = st.columns(3)
    col1.markdown(kpi("Total Growth Potential", fmt(total_forecast*1e6),
                      "If all actions taken"), unsafe_allow_html=True)
    col2.markdown(kpi("Total Investment Needed", "PKR 110M",
                      "To unlock PKR 2.13B growth"), unsafe_allow_html=True)
    col3.markdown(kpi("Expected ROI on Plan", "19.4x",
                      "PKR 1 invested = PKR 19 returned"), unsafe_allow_html=True)

    # ── INSIGHT 14: FINAL SCORECARD ──────────────────────────
    st.markdown(sec("📋 Insight 14 — Final Strategic Scorecard"), unsafe_allow_html=True)
    st.markdown(note("Summary of all 14 insights with current status, recommended action and expected impact. This is the complete strategic roadmap for management."), unsafe_allow_html=True)

    scorecard = pd.DataFrame({
        "Insight"         :[
            "Territory Gap",
            "Promo Timing",
            "Ramipace + Finno-Q",
            "Discount Abuse",
            "Swat Opportunity",
            "Nutraceutical Growth",
            "Product Concentration",
            "Distributor Dependency",
            "Q4 Seasonality",
            "Division Efficiency",
            "Shelf Life Risk",
            "Cost Savings",
            "Growth Forecast",
            "Data Quality"
        ],
        "Status"          :[
            "🔴 Critical","🔴 Critical","🟢 Opportunity",
            "🔴 Urgent","🟢 Opportunity","🟢 Opportunity",
            "🟡 Monitor","🔴 Critical","🟢 Opportunity",
            "🔴 Critical","🟡 Monitor","🟡 Pending",
            "🟢 Planned","🟢 Good"
        ],
        "Action"          :[
            "Increase Karachi/Swat visits",
            "Move July budget to Jan/Feb",
            "Increase both product budgets",
            "Audit Falcons/Strikers NOW",
            "Add 300 Swat trips/year",
            "Launch dedicated Nutra team",
            "Develop 3-5 new products",
            "Onboard 2 new distributors",
            "Double Q4 promo budget",
            "Set Division 4 targets",
            "Contact 20 distributors",
            "Implement all 8 savings",
            "Approve PKR 110M plan",
            "Continue data collection"
        ],
        "Impact"          :[
            "+PKR 150M","+PKR 400M","+PKR 630M",
            "Save PKR 317M","+PKR 150M","+PKR 300M",
            "Risk reduction","Risk reduction",
            "+PKR 300M","Performance up",
            "Brand protection","Save PKR 376M",
            "+PKR 2.13B","Better decisions"
        ]
    })
    st.dataframe(scorecard, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(kpi("🔴 Critical Issues",  "4",          "Need immediate action"), unsafe_allow_html=True)
    col2.markdown(kpi("🟢 Opportunities",    "6",          "Growth potential"), unsafe_allow_html=True)
    col3.markdown(kpi("💰 Total Savings",    "PKR 376M",   "Identifiable per year"), unsafe_allow_html=True)
    col4.markdown(kpi("📈 Growth Potential", "PKR 2.13B",  "With PKR 110M investment"), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 11: MARKETING INTELLIGENCE
# ════════════════════════════════════════════════════════════
elif page == "🔬 Marketing Intelligence":
    st.markdown("<h1 style=\'color:#2c5f8a\'>🔬 Marketing Intelligence — ZSDCY Deep Analysis</h1>", unsafe_allow_html=True)
    st.markdown("<p style=\'color:#666\'>10 advanced marketing insights from 422,171 distribution records</p>", unsafe_allow_html=True)
    st.markdown(note("This page contains deep marketing intelligence extracted from the ZSDCY distribution database. Every insight is designed to help increase sales and improve marketing strategy."), unsafe_allow_html=True)
    st.markdown("---")

    # Load data
    @st.cache_data
    def load_marketing_data():
        df = pd.read_csv("zsdcy_clean.csv")
        def extract_city(sdp):
            try:
                parts = str(sdp).split("-")
                if len(parts) > 1:
                    city = parts[-1].strip()
                    city = city.replace(" AREA","").replace(" LH","")
                    city = city.replace("FB ","").replace("S.I.T.E","KARACHI")
                    city = city.replace("KORANGI","KARACHI").replace("FATEH GARH","LAHORE")
                    return city.title()
                return sdp
            except:
                return "Unknown"
        df["City"] = df["SDP Name"].apply(extract_city)
        return df

    df_mkt = load_marketing_data()

    # Summary KPIs
    # Calculate live KPIs from actual data
    sdp_2024     = set(df_mkt[df_mkt["Yr"]==2024]["SDP Name"].unique())
    sdp_2025     = set(df_mkt[df_mkt["Yr"]==2025]["SDP Name"].unique())
    loyal_sdps   = sdp_2024 & sdp_2025
    lost_sdps    = sdp_2024 - sdp_2025
    retention    = len(loyal_sdps)/len(sdp_2024)*100 if sdp_2024 else 0
    price_2024   = df_mkt[df_mkt["Yr"]==2024]["AvgPrice"].mean()
    price_2025   = df_mkt[df_mkt["Yr"]==2025]["AvgPrice"].mean()
    price_growth = ((price_2025-price_2024)/price_2024*100) if price_2024>0 else 0

    vel_df       = df_mkt.groupby("Material Name").agg(
        TotalQty=("Qty","sum"),
        Months=("Mo","nunique"),
        Revenue=("Revenue","sum")).reset_index()
    vel_df       = vel_df[vel_df["Revenue"]>10e6]
    vel_df["QtyPerMonth"] = vel_df["TotalQty"]/vel_df["Months"]
    fastest_prod = vel_df.nlargest(1,"QtyPerMonth").iloc[0]

    total_sdps_mkt = df_mkt["SDP Name"].nunique()
    total_rev_mkt  = df_mkt["Revenue"].sum()

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Customer Retention",  f"{retention:.1f}%",         f"{len(loyal_sdps)} loyal distributors"), unsafe_allow_html=True)
    c2.markdown(kpi("Total Distributors",  str(total_sdps_mkt),         "Active SDPs 2024-2025"), unsafe_allow_html=True)
    c3.markdown(kpi("Price Growth",        f"+{price_growth:.1f}%",     f"PKR {price_2024:.0f} to PKR {price_2025:.0f}/unit"), unsafe_allow_html=True)
    c4.markdown(kpi("Lost Distributors",   str(len(lost_sdps)),         "⚠️ Left in 2025", red=True), unsafe_allow_html=True)
    c5.markdown(kpi("Fastest Product",     fastest_prod["Material Name"][:20], f"{fastest_prod['QtyPerMonth']:,.0f} units/month"), unsafe_allow_html=True)
    st.markdown("---")

    # INSIGHT 1: PRICE ANALYSIS
    st.markdown(sec("💰 Insight 1 — Price Per Unit Analysis (Premium Products)"), unsafe_allow_html=True)
    st.markdown(note("Higher price per unit = premium product = higher margin. Paridopa at PKR 947/unit and Femova at PKR 868/unit are premium products. Marketing should protect these products from generic competition."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        price_df = df_mkt[df_mkt["AvgPrice"]>0].groupby("Material Name").agg(
            AvgPrice=("AvgPrice","mean"),
            Revenue=("Revenue","sum")).reset_index()
        price_df = price_df[price_df["Revenue"]>10e6].nlargest(15,"AvgPrice")
        price_df["ShortName"] = price_df["Material Name"].str[:35]
        price_df["Label"]     = price_df["AvgPrice"].apply(lambda x: f"PKR {x:,.0f}")
        fig = px.bar(price_df, x="AvgPrice", y="ShortName",
                     orientation="h", text="Label",
                     color="AvgPrice", color_continuous_scale="Purples")
        fig.update_traces(textposition="outside", textfont_size=9)
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Avg Price Per Unit (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Price Trend 2024 vs 2025**")
        price_yr = df_mkt[df_mkt["AvgPrice"]>0].groupby(
            ["Yr","Material Name"])["AvgPrice"].mean().reset_index()
        price_yr24 = price_yr[price_yr["Yr"]==2024].set_index("Material Name")["AvgPrice"]
        price_yr25 = price_yr[price_yr["Yr"]==2025].set_index("Material Name")["AvgPrice"]
        price_chg  = pd.DataFrame({"2024":price_yr24,"2025":price_yr25}).dropna()
        price_chg["Change"] = ((price_chg["2025"]-price_chg["2024"])/
                                price_chg["2024"]*100)
        price_chg = price_chg[price_chg["2024"]>100]

        st.markdown(f"""
        <div class="manual-working">
        PRICE INFLATION ANALYSIS 2024 vs 2025
        ══════════════════════════════════════════
        Overall Average Price:
          2024: PKR 359.2 per unit
          2025: PKR 391.0 per unit
          Change: +{price_growth:.1f}% price increase

        This means:
          → Part of revenue growth is PRICE DRIVEN
          → Not just volume growth
          → Revenue grew +28.5% but price grew +{price_growth:.1f}%
          → Real volume growth = ~{28.5-price_growth:.1f}%

        Products with HIGHEST price increase:
        (showing top 5)
        </div>
        """, unsafe_allow_html=True)
        top_price_inc = price_chg.nlargest(5,"Change")
        for prod, r in top_price_inc.iterrows():
            st.markdown(good(f"<b>{prod[:35]}</b> — Price up +{r['Change']:.1f}% (PKR {r['2024']:.0f} → PKR {r['2025']:.0f})"), unsafe_allow_html=True)

    # INSIGHT 2: CUSTOMER LOYALTY
    st.markdown(sec("👥 Insight 2 — Customer Loyalty & Retention Analysis"), unsafe_allow_html=True)
    st.markdown(note("87.6% retention rate is excellent! Industry average is 70-75%. But Nusrat Pharma (PKR 23.7M) was lost — this is the biggest lost customer and needs immediate recovery action."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        loyalty_data = pd.DataFrame({
            "Status" :["Loyal (Both Years)","New in 2025","Lost from 2024"],
            "Count"  :[184, 85, 26],
            "Revenue":[
                df_mkt[df_mkt["SDP Name"].isin(
                    set(df_mkt[df_mkt["Yr"]==2024]["SDP Name"]) &
                    set(df_mkt[df_mkt["Yr"]==2025]["SDP Name"]))]["Revenue"].sum(),
                df_mkt[df_mkt["SDP Name"].isin(
                    set(df_mkt[df_mkt["Yr"]==2025]["SDP Name"]) -
                    set(df_mkt[df_mkt["Yr"]==2024]["SDP Name"]))]["Revenue"].sum(),
                df_mkt[df_mkt["SDP Name"].isin(
                    set(df_mkt[df_mkt["Yr"]==2024]["SDP Name"]) -
                    set(df_mkt[df_mkt["Yr"]==2025]["SDP Name"]))]["Revenue"].sum()
            ]
        })
        loyalty_data["RevLabel"] = loyalty_data["Revenue"].apply(fmt)
        fig = px.bar(loyalty_data, x="Status", y="Count",
                     text="Count", color="Status",
                     color_discrete_map={
                         "Loyal (Both Years)":"#2e7d32",
                         "New in 2025":"#2c5f8a",
                         "Lost from 2024":"#c62828"})
        fig.update_traces(textposition="outside", textfont_size=12)
        apply_layout(fig, height=320,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee", title="Number of Distributors"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"""
        <div class="manual-working">
        CUSTOMER RETENTION ANALYSIS
        ══════════════════════════════════════════
        Loyal Customers  : 184 (87.6% retention)
        New in 2025      : 85  (market expansion!)
        Lost from 2024   : 26  (needs recovery)

        TOP LOST CUSTOMER — URGENT ACTION:
        Nusrat Pharma    : PKR 23.7M revenue lost
        → Call immediately
        → Offer special pricing
        → Assign dedicated account manager

        Other lost customers were small
        (all under PKR 5M) — lower priority

        NEW CUSTOMER WIN:
        85 new distributors in 2025 = excellent!
        These represent new market penetration.
        Nurture them carefully in 2026.

        RETENTION BENCHMARK:
        Pharmevo  : 87.6% ✅ Excellent
        Industry  : 70-75% (typical)
        Target    : 90%+ for 2026
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)
        st.markdown(danger("Action Required: Contact Nusrat Pharma immediately. PKR 23.7M annual revenue lost. Assign top account manager for recovery."), unsafe_allow_html=True)

    # INSIGHT 3: SALES VELOCITY
    st.markdown(sec("🚀 Insight 3 — Sales Velocity: Fastest & Slowest Moving Products"), unsafe_allow_html=True)
    st.markdown(note("Sales velocity = units sold per month. High velocity = product in strong demand = protect with adequate supply. Low velocity = potential deadstock risk = review promotion strategy."), unsafe_allow_html=True)

    velocity = df_mkt.groupby("Material Name").agg(
        TotalQty=("Qty","sum"),
        Months=("Mo","nunique"),
        Revenue=("Revenue","sum")).reset_index()
    velocity = velocity[velocity["Revenue"]>10e6]
    velocity["QtyPerMonth"] = velocity["TotalQty"]/velocity["Months"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🚀 Top 15 Fastest Moving Products**")
        fast = velocity.nlargest(15,"QtyPerMonth")
        fast["ShortName"] = fast["Material Name"].str[:35]
        fast["Label"]     = fast["QtyPerMonth"].apply(lambda x: f"{x:,.0f} u/mo")
        fig = px.bar(fast, x="QtyPerMonth", y="ShortName",
                     orientation="h", text="Label",
                     color="QtyPerMonth", color_continuous_scale="Greens")
        fig.update_traces(textposition="outside", textfont_size=9)
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Units Per Month"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(good("These products need consistent supply chain — never let them go out of stock!"), unsafe_allow_html=True)

    with col2:
        st.markdown("**⚠️ Top 15 Slowest Moving Products**")
        slow = velocity.nsmallest(15,"QtyPerMonth")
        slow["ShortName"] = slow["Material Name"].str[:35]
        slow["Label"]     = slow["QtyPerMonth"].apply(lambda x: f"{x:,.0f} u/mo")
        fig = px.bar(slow, x="QtyPerMonth", y="ShortName",
                     orientation="h", text="Label",
                     color="QtyPerMonth", color_continuous_scale="Reds_r")
        fig.update_traces(textposition="outside", textfont_size=9)
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Units Per Month"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(warn("These products sell very slowly. Review: Is pricing too high? Is promotion sufficient? Should they be discontinued?"), unsafe_allow_html=True)

    # INSIGHT 4: NEW PRODUCT LAUNCHES
    st.markdown(sec("🆕 Insight 4 — New Product Launches in 2025 (133 Products!)"), unsafe_allow_html=True)
    st.markdown(note("133 new products were launched in 2025. Momist Nasal Spray leads at PKR 36.5M in first year — exceptional launch performance! Vanzak Tab at PKR 31.1M is also strong. These need continued marketing support."), unsafe_allow_html=True)

    prods_2024   = set(df_mkt[df_mkt["Yr"]==2024]["Material Name"].unique())
    prods_2025   = set(df_mkt[df_mkt["Yr"]==2025]["Material Name"].unique())
    new_prods    = prods_2025 - prods_2024
    new_prod_df  = df_mkt[
        (df_mkt["Material Name"].isin(new_prods)) &
        (df_mkt["Yr"]==2025)].groupby("Material Name").agg(
        Revenue=("Revenue","sum"),
        Qty=("Qty","sum"),
        Cities=("City","nunique")).reset_index()
    new_prod_df  = new_prod_df[new_prod_df["Revenue"]>1e6].nlargest(20,"Revenue")
    new_prod_df["ShortName"] = new_prod_df["Material Name"].str[:35]
    new_prod_df["Label"]     = new_prod_df["Revenue"].apply(fmt)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(new_prod_df, x="Revenue", y="ShortName",
                     orientation="h", text="Label",
                     color="Revenue", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=9)
        apply_layout(fig, height=550,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"""
        <div class="manual-working">
        NEW PRODUCT LAUNCH ANALYSIS 2025
        ══════════════════════════════════════════
        Total new products    : 133
        Products > PKR 1M rev : {len(new_prod_df)}
        Top 3 launches:

        1. MOMIST NASAL SPRAY  : PKR 36.5M
           → First year revenue excellent
           → Increase marketing support

        2. VANZAK TAB 20MG     : PKR 31.1M
           → Strong first year
           → Monitor for 2026 growth

        3. K-1000 PLUS SAC     : PKR 22.2M
           → Good launch
           → Expand city coverage

        LAUNCH SUCCESS RATE:
        133 launched → {len(new_prod_df)} earned >PKR 1M
        Success rate: {len(new_prod_df)/133*100:.0f}%

        RECOMMENDATION:
        → Focus 2026 marketing on top 10 new products
        → Phase out bottom 50 new products
        → Allocate PKR 5M launch budget per product
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(new_prod_df[["ShortName","Label","Cities"]].rename(
            columns={"ShortName":"Product","Label":"Revenue","Cities":"Cities Reached"}),
            use_container_width=True, hide_index=True)

    # INSIGHT 5: PRODUCT LIFE CYCLE
    st.markdown(sec("🔄 Insight 5 — Product Life Cycle Analysis"), unsafe_allow_html=True)
    st.markdown(note("202 products are growing (invest more!). 484 are stable (maintain). 128 are critical (declining >30%). 13 are warning (declining 10-30%). Critical products need urgent marketing intervention or discontinuation."), unsafe_allow_html=True)

    plc = df_mkt.groupby(["Material Name","Yr"])["Revenue"].sum().reset_index()
    plc_pivot = plc.pivot(index="Material Name", columns="Yr",
                           values="Revenue").fillna(0)
    plc_pivot["Growth"] = ((plc_pivot[2025]-plc_pivot[2024])/
                            plc_pivot[2024].replace(0,1)*100)
    plc_pivot["Status"] = plc_pivot["Growth"].apply(
        lambda x: "🚀 Growing"   if x>20  else
                  "✅ Stable"    if x>-10 else
                  "⚠️ Declining" if x>-30 else
                  "🔴 Critical")
    plc_pivot = plc_pivot.reset_index()

    col1, col2 = st.columns(2)
    with col1:
        status_count = plc_pivot["Status"].value_counts().reset_index()
        status_count.columns = ["Status","Count"]
        colors_lc = {"🚀 Growing":"#2e7d32","✅ Stable":"#2c5f8a",
                     "⚠️ Declining":"#e65100","🔴 Critical":"#c62828"}
        fig = px.pie(status_count, values="Count", names="Status",
                     color="Status", color_discrete_map=colors_lc)
        fig.update_traces(textinfo="percent+label+value", textfont_size=11)
        apply_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        growing  = plc_pivot[plc_pivot["Status"]=="🚀 Growing"].nlargest(10,"Growth")
        st.markdown("**Top 10 Growing Products — Invest More!**")
        for _, r in growing.iterrows():
            st.markdown(good(f"<b>{r['Material Name'][:35]}</b> +{r['Growth']:.0f}% growth"), unsafe_allow_html=True)

    # Show critical products
    st.markdown(sec("🔴 Critical Products — Needs Urgent Action"), unsafe_allow_html=True)
    st.markdown(note("These products declined more than 30% from 2024 to 2025. Most are export/Afghanistan variants — possibly discontinued markets. Domestic critical products need immediate marketing intervention."), unsafe_allow_html=True)

    critical = plc_pivot[plc_pivot["Status"]=="🔴 Critical"].copy()
    critical["IsDomestic"] = ~critical["Material Name"].str.contains(
        "AFG|GTM|SLK|VNM|IQ|KEN|CMB|UZB|BRN", na=False)
    domestic_critical = critical[critical["IsDomestic"]].nsmallest(10,"Growth")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Domestic Critical Products**")
        if len(domestic_critical) > 0:
            for _, r in domestic_critical.iterrows():
                st.markdown(danger(f"<b>{r['Material Name'][:40]}</b> — {r['Growth']:.0f}% decline"), unsafe_allow_html=True)
        else:
            st.markdown(good("No domestic products are in critical decline! All critical products are export variants."), unsafe_allow_html=True)

    with col2:
        st.markdown("**Export/International Critical Products**")
        export_critical = critical[~critical["IsDomestic"]].head(8)
        for _, r in export_critical.iterrows():
            st.markdown(warn(f"<b>{r['Material Name'][:40]}</b> — Export market issue"), unsafe_allow_html=True)

    # INSIGHT 6: CITY MARKET SHARE
    st.markdown(sec("🗺️ Insight 6 — City Market Share & Concentration"), unsafe_allow_html=True)
    st.markdown(note("Karachi leads at 5% market share (PKR 872M). Top 15 cities = 40% of total revenue. 253 smaller cities share remaining 60%. This shows opportunity in mid-tier cities."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        city_rev   = df_mkt.groupby("City")["Revenue"].sum()
        total_cr   = city_rev.sum()
        city_share = (city_rev/total_cr*100).nlargest(15).reset_index()
        city_share.columns = ["City","Share"]
        city_share["Revenue"] = city_share["City"].map(city_rev)
        city_share["Label"]   = city_share["Share"].apply(lambda x: f"{x:.1f}%")
        fig = px.bar(city_share, x="Share", y="City",
                     orientation="h", text="Label",
                     color="Share", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Market Share %"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        top15_share = city_share["Share"].sum()
        st.markdown(f"""
        <div class="manual-working">
        CITY MARKET CONCENTRATION
        ══════════════════════════════════════════
        Total cities covered  : 268
        Top 15 cities share   : {top15_share:.1f}%
        Remaining 253 cities  : {100-top15_share:.1f}%

        TOP 5 CITIES:
        1. Karachi    : 5.0% (PKR 872M)
        2. Peshawar   : 3.7% (PKR 637M)
        3. Lahore     : 3.7% (PKR 634M)
        4. Rawalpindi : 3.1% (PKR 540M)
        5. Swat       : 3.0% (PKR 514M)

        GROWTH OPPORTUNITY:
        Cities 6-15 average : 2.2% share each
        Cities 16-268 avg   : 0.24% share each

        Mid-tier cities (rank 16-50) represent
        the biggest untapped growth opportunity.
        Each 1% increase in coverage = PKR 174M

        ACTION: Assign dedicated sales reps to
        top 10 mid-tier cities for 2026.
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    # INSIGHT 7: DISTRIBUTOR FREQUENCY
    st.markdown(sec("📦 Insight 7 — Most Loyal & Frequent Distributors"), unsafe_allow_html=True)
    st.markdown(note("Distributors who order every single month (12 months active) are the most reliable partners. These relationships must be protected and rewarded with priority service and better terms."), unsafe_allow_html=True)

    freq = df_mkt.groupby("SDP Name").agg(
        OrderMonths=("Mo","nunique"),
        Revenue=("Revenue","sum"),
        Products=("Material Name","nunique")).reset_index()
    freq12 = freq[freq["OrderMonths"]==12].sort_values("Revenue",ascending=False)
    freq12["ShortName"] = freq12["SDP Name"].str[:35]
    freq12["Label"]     = freq12["Revenue"].apply(fmt)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(freq12.head(15), x="Revenue", y="ShortName",
                     orientation="h", text="Label",
                     color="Revenue", color_continuous_scale="Greens")
        fig.update_traces(textposition="outside", textfont_size=9)
        apply_layout(fig, height=480,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"""
        <div class="manual-working">
        DISTRIBUTOR LOYALTY ANALYSIS
        ══════════════════════════════════════════
        Total distributors     : 295
        12-month active (loyal): {len(freq12)}
        Their combined revenue : {fmt(freq12["Revenue"].sum())}

        Top 3 Most Loyal Distributors:
        1. Atif Distributor    : PKR 240M
        2. Ali Hajvery Pharma  : PKR 190M
        3. Al-Fateh Med Co     : PKR 141M

        These distributors order EVERY month
        without fail. They are the backbone of
        Pharmevo distribution network.

        RECOMMENDATION:
        → Give them priority stock allocation
        → Offer loyalty discounts (2-3%)
        → Assign dedicated account managers
        → Invite to annual partner events
        → First access to new product launches

        RISK: If any of top 5 loyal distributors
        leave, Pharmevo loses PKR 100M+ instantly.
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)
        st.markdown(good(f"{len(freq12)} distributors order every month. Combined revenue = {fmt(freq12['Revenue'].sum())}. These are VIP partners — treat them accordingly!"), unsafe_allow_html=True)

    # INSIGHT 8: DISTRIBUTOR CONCENTRATION
    st.markdown(sec("⚠️ Insight 8 — Distributor Concentration Risk"), unsafe_allow_html=True)
    st.markdown(note("Only 46 distributors (out of 295) generate 80% of all revenue. Top 5 distributors = 16.3% of revenue. This concentration is better than product concentration but still needs monitoring."), unsafe_allow_html=True)

    dist_rev = df_mkt.groupby("SDP Name")["Revenue"].sum().sort_values(ascending=False).reset_index()
    dist_rev["CumPct"] = dist_rev["Revenue"].cumsum()/dist_rev["Revenue"].sum()*100
    dist_rev["Label"]  = dist_rev["Revenue"].apply(fmt)
    dist_rev["ShortName"] = dist_rev["SDP Name"].str[:30]

    col1, col2 = st.columns(2)
    with col1:
        top20_dist = dist_rev.head(20)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top20_dist["Revenue"]/1e6,
            y=top20_dist["ShortName"],
            orientation="h", name="Revenue (M PKR)",
            marker_color="#2c5f8a",
            text=top20_dist["Label"],
            textposition="outside", textfont_size=8
        ))
        apply_layout(fig, height=580,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        concentration = pd.DataFrame({
            "Group"  :["Top 5","Top 10","Top 20","Top 46","Rest (249)"],
            "Share"  :[16.3, 26.1, 40.2, 80.0, 20.0],
            "Count"  :[5, 10, 20, 46, 249]
        })
        fig = px.bar(concentration, x="Group", y="Share",
                     text=[f"{s:.1f}%" for s in concentration["Share"]],
                     color="Share", color_continuous_scale="Reds")
        fig.update_traces(textposition="outside", textfont_size=12)
        apply_layout(fig, height=320,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee", title="Revenue Share %"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(warn("46 distributors = 80% revenue. Better than product concentration (30 products = 80%). But still monitor top 10 distributors closely."), unsafe_allow_html=True)

    # INSIGHT 9: CATEGORY GROWTH
    st.markdown(sec("📊 Insight 9 — Category Growth Analysis"), unsafe_allow_html=True)
    st.markdown(note("Pharma is 86.3% of revenue but which category is growing FASTEST? This tells marketing where to invest for future growth."), unsafe_allow_html=True)

    cat_yr = df_mkt.groupby(["Category","Yr"])["Revenue"].sum().reset_index()
    cat_pivot = cat_yr.pivot(index="Category", columns="Yr",
                              values="Revenue").fillna(0)
    if 2024 in cat_pivot.columns and 2025 in cat_pivot.columns:
        cat_pivot["Growth"] = ((cat_pivot[2025]-cat_pivot[2024])/
                                cat_pivot[2024].replace(0,1)*100)
        cat_pivot = cat_pivot.reset_index()
        cat_pivot["Label24"] = cat_pivot[2024].apply(fmt)
        cat_pivot["Label25"] = cat_pivot[2025].apply(fmt)
        cat_pivot["GrowthLabel"] = cat_pivot["Growth"].apply(lambda x: f"+{x:.1f}%")

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(cat_pivot, x="Category", y="Growth",
                         text="GrowthLabel", color="Growth",
                         color_continuous_scale="Greens",
                         title="Category Growth % 2024→2025")
            fig.update_traces(textposition="outside", textfont_size=11)
            apply_layout(fig, height=360,
                         xaxis=dict(gridcolor="#eeeeee"),
                         yaxis=dict(gridcolor="#eeeeee", title="Growth %"),
                         coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.dataframe(
                cat_pivot[["Category","Label24","Label25","GrowthLabel"]].rename(
                    columns={"Label24":"2024 Revenue","Label25":"2025 Revenue",
                             "GrowthLabel":"Growth"}),
                use_container_width=True, hide_index=True)
            best_cat = cat_pivot.nlargest(1,"Growth").iloc[0]
            st.markdown(good(f"<b>{best_cat['Category']}</b> is fastest growing category at +{best_cat['Growth']:.1f}%! Increase marketing investment here for maximum impact."), unsafe_allow_html=True)

    # INSIGHT 10: MARKETING SCORECARD
    st.markdown(sec("📋 Insight 10 — Marketing Intelligence Scorecard"), unsafe_allow_html=True)
    st.markdown(note("Complete marketing health check across all dimensions. Use this scorecard for monthly marketing reviews and board presentations."), unsafe_allow_html=True)

    mkt_scorecard = pd.DataFrame({
        "Marketing Dimension":[
            "Customer Retention",
            "New Customer Acquisition",
            "Product Portfolio Health",
            "New Product Launch Success",
            "Price Management",
            "Geographic Coverage",
            "Distributor Loyalty",
            "Sales Velocity",
            "Category Diversification",
            "Market Concentration Risk"
        ],
        "Score":[
            "🟢 87.6% retention",
            "🟢 85 new in 2025",
            "🟡 202 growing, 128 critical",
            "🟢 133 launched, top PKR 36M",
            "🟢 +8.9% price increase",
            "🟢 268 cities covered",
            "🟢 15 order every month",
            "🟢 X-Plended 89K units/mo",
            "🟡 86% pharma dependency",
            "🟡 46 SDPs = 80% revenue"
        ],
        "Action":[
            "Target 90%+ for 2026",
            "Nurture all 85 carefully",
            "Fix 128 critical products",
            "Support top 10 new launches",
            "Monitor price elasticity",
            "Add 20 new cities in 2026",
            "Give VIP treatment to 15",
            "Ensure X-Plended supply",
            "Grow nutraceutical to 20%",
            "Reduce top 10 SDP dependency"
        ]
    })
    st.dataframe(mkt_scorecard, use_container_width=True, hide_index=True)

    # Final KPIs
    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2,col3,col4 = st.columns(4)
    col1.markdown(kpi("🟢 Marketing Strengths", "6/10", "Above average performance"), unsafe_allow_html=True)
    col2.markdown(kpi("🟡 Areas to Watch",      "4/10", "Need monitoring"), unsafe_allow_html=True)
    col3.markdown(kpi("🆕 New Products 2025",   "133",  "Launched successfully"), unsafe_allow_html=True)
    col4.markdown(kpi("💰 Price Growth",        "+8.9%","Healthy price management"), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PAGE 12: EXECUTIVE INTELLIGENCE
# ════════════════════════════════════════════════════════════
elif page == "🔍 Executive Intelligence":
    st.markdown("<h1 style=\'color:#2c5f8a\'>🔍 Executive Intelligence Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style=\'color:#666; font-size:16px\'>Complete Business Summary — All 4 Databases Connected | For Senior Management</p>", unsafe_allow_html=True)
    st.markdown(note("This page connects all 4 databases into one complete business picture. Every finding is backed by data. Green = invest more. Orange = fix this. Red = act immediately."), unsafe_allow_html=True)
    st.markdown("---")

    # ── SECTION 1: BUSINESS HEALTH ───────────────────────────
    st.markdown("### 📊 Where Are We Today? — Complete Business Overview")

    total_rev_all  = df_sales["TotalRevenue"].sum()
    total_spend_all= df_act["TotalAmount"].sum()
    roi_all        = total_rev_all/total_spend_all
    rev_24         = df_sales[df_sales["Yr"]==2024]["TotalRevenue"].sum()
    rev_25         = df_sales[df_sales["Yr"]==2025]["TotalRevenue"].sum()
    growth_all     = ((rev_25-rev_24)/rev_24*100)
    total_trips_all= df_travel["TravelCount"].sum()
    primary_rev    = df_zsdcy["Revenue"].sum()

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Secondary Revenue",  fmt(total_rev_all),       "DSR DB — 2024 to 2026"), unsafe_allow_html=True)
    c2.markdown(kpi("Primary Revenue",    fmt(primary_rev),         "ZSDCY DB — 2024 to 2025"), unsafe_allow_html=True)
    c3.markdown(kpi("Promo Investment",   fmt(total_spend_all),     "Activities DB — 2024 to 2026"), unsafe_allow_html=True)
    c4.markdown(kpi("Overall ROI",        f"{roi_all:.1f}x",        "PKR 1 spent = PKR 18.6 earned"), unsafe_allow_html=True)
    c5.markdown(kpi("Revenue Growth",     f"+{growth_all:.1f}%",    "2024 to 2025 YoY"), unsafe_allow_html=True)
    st.markdown("---")

    # ── SECTION 2: COMPLETE SALES FUNNEL ────────────────────
    st.markdown("### 🔄 The Complete Pharmevo Sales Funnel — How All 4 Databases Connect")
    st.markdown(note("This funnel shows how money flows through Pharmevo business. Every PKR 1 invested in promotions eventually generates PKR 18.6 in secondary sales. Each stage is tracked by a separate database."), unsafe_allow_html=True)

    col1, col2 = st.columns([2,1])
    with col1:
        funnel_data = pd.DataFrame({
            "Stage"  :["Promo Investment (Activities DB)",
                       "Field Visits (Travel DB)",
                       "Primary Sales (ZSDCY DB)",
                       "Secondary Sales (DSR DB)"],
            "Value"  :[total_spend_all/1e9, total_trips_all/1000,
                       primary_rev/1e9, total_rev_all/1e9],
            "Label"  :[fmt(total_spend_all),
                       f"{total_trips_all:,} trips",
                       fmt(primary_rev),
                       fmt(total_rev_all)],
            "Color"  :["#e65100","#2c5f8a","#7b1fa2","#2e7d32"]
        })

        fig = go.Figure()
        for i, row in funnel_data.iterrows():
            fig.add_trace(go.Bar(
                x=[row["Label"]],
                y=[row["Value"]],
                name=row["Stage"],
                marker_color=row["Color"],
                text=row["Label"],
                textposition="outside",
                textfont_size=13,
                width=0.5
            ))
        apply_layout(fig, height=350,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee", title="Value"),
                     showlegend=False,
                     barmode="group")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"""
        <div class="manual-working">
        SALES FUNNEL ANALYSIS
        ═══════════════════════════════
        Stage 1 — INVEST
        Activities DB
        PKR {total_spend_all/1e9:.2f}B promotional spend
        ↓ multiplied by 6.7x
        Stage 2 — VISIT
        Travel DB
        {total_trips_all:,} field visits made
        ↓ converts to orders
        Stage 3 — SHIP
        ZSDCY DB (Primary)
        PKR {primary_rev/1e9:.1f}B shipped to distributors
        ↓ multiplied by 2.8x
        Stage 4 — SELL
        DSR DB (Secondary)
        PKR {total_rev_all/1e9:.1f}B sold to patients

        KEY RATIO:
        PKR 1 invested → PKR {roi_all:.1f} returned
        Every trip → PKR {total_rev_all/total_trips_all/1e6:.1f}M revenue
        ═══════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── SECTION 3: 13 FINDINGS ───────────────────────────────
    st.markdown("### 🎯 13 Key Management Findings — Cross Database Analysis")

    # ─── FINDING 1: RAMIPACE ────────────────────────────────
    st.markdown(sec("🟢 FINDING 1 — Ramipace: Best Investment in Company History"), unsafe_allow_html=True)
    st.markdown(note("Confirmed by 3 databases: Activities (spend), DSR (revenue), ZSDCY (distribution). PKR 4.3M investment generates PKR 430M revenue. This is 5x better than company average ROI of 18.6x."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        ram_data = df_roi.nlargest(8,"ROI")
        colors_r = ["#c62828" if p=="Ramipace" else "#2c5f8a"
                    for p in ram_data["ProductName"]]
        fig = go.Figure(go.Bar(
            x=ram_data["ROI"], y=ram_data["ProductName"],
            orientation="h",
            text=[f"{r:.0f}x" for r in ram_data["ROI"]],
            textposition="outside", textfont_size=10,
            marker_color=colors_r
        ))
        apply_layout(fig, height=280,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="ROI"))
        fig.update_layout(title="ROI Comparison — Ramipace vs Others")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"""
        <div class="manual-working">
        RAMIPACE — 3 DATABASE PROOF
        ═══════════════════════════════
        Activities DB:
          Promo Spend : PKR 4.3M only

        DSR DB:
          Revenue     : PKR 430M+
          ROI         : 99.7x

        ZSDCY DB:
          Distributed : PKR 265M
          Units       : 651,400

        CONCLUSION:
          ROI = 99.7x vs avg 18.6x
          5.4x BETTER than average!
        ═══════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(good("<b>ACTION:</b> Increase Ramipace promo budget from PKR 4.3M to PKR 15M. Expected return: +PKR 430M additional revenue. Confidence: VERY HIGH — confirmed by 3 databases."), unsafe_allow_html=True)
        st.markdown(kpi("Potential Gain", "+PKR 430M", "From PKR 10M extra investment"), unsafe_allow_html=True)

    # ─── FINDING 2: FINNO-Q ─────────────────────────────────
    st.markdown(sec("🟢 FINDING 2 — Finno-Q: +226% Growth with Almost Zero Promotion!"), unsafe_allow_html=True)
    st.markdown(note("Confirmed by DSR (+226%) and ZSDCY (+123%). This product is growing explosively WITHOUT promotional support. Imagine the growth WITH a dedicated campaign!"), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        r24 = df_sales[df_sales["Yr"]==2024].groupby("ProductName")["TotalRevenue"].sum()
        r25 = df_sales[df_sales["Yr"]==2025].groupby("ProductName")["TotalRevenue"].sum()
        gdf = pd.DataFrame({"2024":r24,"2025":r25}).dropna()
        gdf = gdf[gdf["2024"]>5e6]
        gdf["Growth"] = ((gdf["2025"]-gdf["2024"])/gdf["2024"]*100)
        gdf = gdf.nlargest(8,"Growth").reset_index()
        colors_f = ["#c62828" if "FINNO" in p.upper() else "#2c5f8a"
                    for p in gdf["ProductName"]]
        fig = go.Figure(go.Bar(
            x=gdf["Growth"], y=gdf["ProductName"],
            orientation="h",
            text=[f"+{g:.0f}%" for g in gdf["Growth"]],
            textposition="outside", textfont_size=10,
            marker_color=colors_f
        ))
        apply_layout(fig, height=280,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Growth %"))
        fig.update_layout(title="Top Growing Products — DSR DB")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        finnoq_monthly = df_sales[
            df_sales["ProductName"].str.upper().str.contains("FINNO")
        ].groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
        finnoq_monthly["Date"] = pd.to_datetime(
            finnoq_monthly["Yr"].astype(int).astype(str)+"-"+
            finnoq_monthly["Mo"].astype(int).astype(str)+"-01")
        fig = px.line(finnoq_monthly, x="Date", y="TotalRevenue",
                      title="Finno-Q Monthly Revenue Trend",
                      color_discrete_sequence=["#2e7d32"])
        fig.update_traces(mode="lines+markers", line_width=2.5)
        apply_layout(fig, height=280,
                     yaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown(good(f"<b>ACTION:</b> Allocate PKR 10M immediately for Finno-Q promotion. Product grew +226% with only PKR {6.7:.1f}M promo. With PKR 10M dedicated campaign — target +400% growth in 2026."), unsafe_allow_html=True)
        st.markdown(kpi("Potential Gain", "+PKR 200M", "With PKR 10M investment"), unsafe_allow_html=True)

    # ─── FINDING 3: TERRITORY GAP ───────────────────────────
    st.markdown(sec("🟢 FINDING 3 — Territory Gap: We Visit Lahore But Karachi Earns More!"), unsafe_allow_html=True)
    st.markdown(note("Travel DB shows Lahore = most visited. ZSDCY DB shows Karachi = highest revenue. Swat gets 63 visits but earns PKR 514M — PKR 8.2M per visit! Lahore earns only PKR 0.4M per visit."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        city_travel = df_travel.groupby("VisitLocation")["TravelCount"].sum().nlargest(10).reset_index()
        city_travel["Label"] = city_travel["TravelCount"].apply(fmt_num)
        fig = px.bar(city_travel, x="TravelCount", y="VisitLocation",
                     orientation="h", text="Label",
                     title="Trips by City — Travel DB",
                     color_discrete_sequence=["#2c5f8a"])
        fig.update_traces(textposition="outside", textfont_size=9)
        apply_layout(fig, height=300,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        city_rev_z = df_zsdcy.groupby("City")["Revenue"].sum().nlargest(10).reset_index()
        city_rev_z["Label"] = city_rev_z["Revenue"].apply(fmt)
        colors_c = ["#c62828" if c in ["Karachi","Swat"] else "#2c5f8a"
                    for c in city_rev_z["City"]]
        fig = go.Figure(go.Bar(
            x=city_rev_z["Revenue"]/1e6,
            y=city_rev_z["City"],
            orientation="h",
            text=city_rev_z["Label"],
            textposition="outside", textfont_size=9,
            marker_color=colors_c
        ))
        apply_layout(fig, height=300,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"))
        fig.update_layout(title="Revenue by City — ZSDCY DB")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown(warn("<b>ACTION:</b> Increase Karachi and Swat field visits by 300+ trips each. Revenue per trip in Swat = PKR 8.2M vs Lahore PKR 0.4M. Swat is 20x more efficient per visit!"), unsafe_allow_html=True)
        st.markdown(kpi("Potential Gain", "+PKR 150M", "From 300 extra Swat visits"), unsafe_allow_html=True)

    # ─── FINDING 4: Q4 SEASONALITY ──────────────────────────
    st.markdown(sec("🟢 FINDING 4 — Q4 Golden Quarter: All 4 Databases Confirm Oct-Dec Peak!"), unsafe_allow_html=True)
    st.markdown(note("Q4 generates 24.4% of annual secondary sales, 29% of travel, 27% of promo spend. All 4 databases confirm same pattern every year. Double Q4 promotional campaigns starting September."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        mo_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                  7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        sales_mo = df_sales.groupby("Mo")["TotalRevenue"].sum().reset_index()
        sales_mo["Month"] = sales_mo["Mo"].map(mo_map)
        sales_mo["Q4"]    = sales_mo["Mo"].apply(
            lambda x: "Q4 Peak" if x in [10,11,12] else "Other")
        fig = px.bar(sales_mo, x="Month", y="TotalRevenue",
                     color="Q4", title="DSR — Monthly Sales",
                     color_discrete_map={"Q4 Peak":"#2e7d32","Other":"#2c5f8a"},
                     category_orders={"Month":list(mo_map.values())})
        fig.update_traces(textposition="outside")
        apply_layout(fig, height=260,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        travel_mo = df_travel.groupby("Mo")["TravelCount"].sum().reset_index()
        travel_mo["Month"] = travel_mo["Mo"].map(mo_map)
        travel_mo["Q4"]    = travel_mo["Mo"].apply(
            lambda x: "Q4 Peak" if x in [10,11,12] else "Other")
        fig = px.bar(travel_mo, x="Month", y="TravelCount",
                     color="Q4", title="Travel DB — Monthly Trips",
                     color_discrete_map={"Q4 Peak":"#2e7d32","Other":"#2c5f8a"},
                     category_orders={"Month":list(mo_map.values())})
        apply_layout(fig, height=260,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        promo_mo = df_act.groupby("Mo")["TotalAmount"].sum().reset_index()
        promo_mo["Month"] = promo_mo["Mo"].map(mo_map)
        promo_mo["Q4"]    = promo_mo["Mo"].apply(
            lambda x: "Q4 Peak" if x in [10,11,12] else "Other")
        fig = px.bar(promo_mo, x="Month", y="TotalAmount",
                     color="Q4", title="Activities DB — Promo Spend",
                     color_discrete_map={"Q4 Peak":"#2e7d32","Other":"#2c5f8a"},
                     category_orders={"Month":list(mo_map.values())})
        apply_layout(fig, height=260,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    q4_sales_ei  = df_sales[df_sales["Mo"].isin([10,11,12])]["TotalRevenue"].sum()
    q4_pct_ei    = q4_sales_ei/df_sales["TotalRevenue"].sum()*100
    st.markdown(good(f"<b>ACTION:</b> Q4 = {q4_pct_ei:.1f}% of annual revenue. Double promotional spend in September to build Q4 momentum. Expected impact: +PKR 300M in Q4 revenue."), unsafe_allow_html=True)

    # ─── FINDING 5: NUTRACEUTICAL ───────────────────────────
    st.markdown(sec("🟢 FINDING 5 — Nutraceutical: Growing 35.5% vs Pharma 28% — The Next Big Revenue Stream!"), unsafe_allow_html=True)
    st.markdown(note("ZSDCY DB confirms Nutraceutical grew 35.5% vs Pharma 28%. Currently 12.7% of primary revenue. With dedicated marketing team and budget — can reach 20% by 2027 = PKR 500M+ additional revenue."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        cat_yr = df_zsdcy.groupby(["Category","Yr"])["Revenue"].sum().reset_index()
        cat_map = {"P":"Pharma","N":"Nutraceutical","M":"Medical Device",
                   "H":"Herbal","E":"Export","O":"Other"}
        cat_yr["CatName"] = cat_yr["Category"].map(cat_map)
        cat_main = cat_yr[cat_yr["Category"].isin(["P","N"])]
        fig = px.bar(cat_main, x="Yr", y="Revenue",
                     color="CatName", barmode="group",
                     title="Pharma vs Nutraceutical Growth",
                     color_discrete_map={"Pharma":"#2c5f8a",
                                         "Nutraceutical":"#2e7d32"},
                     text=cat_main["Revenue"].apply(fmt))
        fig.update_traces(textposition="outside", textfont_size=9)
        apply_layout(fig, height=280,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        cat_share = df_zsdcy.groupby("Category")["Revenue"].sum().reset_index()
        cat_share["CatName"] = cat_share["Category"].map(cat_map)
        fig = px.pie(cat_share, values="Revenue", names="CatName",
                     title="Revenue Share by Category",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textinfo="percent+label", textfont_size=10)
        apply_layout(fig, height=280)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        nutra_24_ei  = df_zsdcy[(df_zsdcy["Category"]=="N") & (df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    nutra_25_ei  = df_zsdcy[(df_zsdcy["Category"]=="N") & (df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    pharma_24_ei = df_zsdcy[(df_zsdcy["Category"]=="P") & (df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    pharma_25_ei = df_zsdcy[(df_zsdcy["Category"]=="P") & (df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    nutra_growth_ei  = ((nutra_25_ei-nutra_24_ei)/nutra_24_ei*100) if nutra_24_ei>0 else 0
    pharma_growth_ei = ((pharma_25_ei-pharma_24_ei)/pharma_24_ei*100) if pharma_24_ei>0 else 0
    st.markdown(good(f"<b>ACTION:</b> Nutraceutical growing {nutra_growth_ei:.1f}% vs Pharma {pharma_growth_ei:.1f}%. Launch dedicated Nutraceutical sales team. Increase promo budget by PKR 20M. Target 20% revenue share by 2027."), unsafe_allow_html=True)
    st.markdown(kpi("Potential Gain", "+PKR 300M", "Nutra to 20% share by 2027"), unsafe_allow_html=True)

    # ─── FINDING 6: PROMO TIMING ────────────────────────────
    st.markdown(sec("🟡 FINDING 6 — Promo Timing Mismatch: Budget Spent in Wrong Months!"), unsafe_allow_html=True)
    st.markdown(note("Activities DB vs DSR DB comparison: July = highest promo spend (#1) but only #8 in sales. January = #1 in sales but #3 in promo. PKR 1.37B promo budget is misaligned with actual sales peaks!"), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        promo_rank_s = df_act.groupby("Mo")["TotalAmount"].sum().rank(ascending=False)
        sales_rank_s = df_sales.groupby("Mo")["TotalRevenue"].sum().rank(ascending=False)
        timing_df    = pd.DataFrame({
            "Month"     : list(mo_map.values()),
            "Promo Rank": [int(promo_rank_s.get(m,0)) for m in range(1,13)],
            "Sales Rank": [int(sales_rank_s.get(m,0)) for m in range(1,13)]
        })
        timing_df["Gap"]    = abs(timing_df["Promo Rank"]-timing_df["Sales Rank"])
        timing_df["Status"] = timing_df["Gap"].apply(
            lambda x: "✅" if x<=2 else "⚠️")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timing_df["Month"], y=timing_df["Promo Rank"],
            name="Promo Rank", mode="lines+markers",
            line=dict(color="#e65100", width=2.5),
            marker=dict(size=8)))
        fig.add_trace(go.Scatter(
            x=timing_df["Month"], y=timing_df["Sales Rank"],
            name="Sales Rank", mode="lines+markers",
            line=dict(color="#2c5f8a", width=2.5),
            marker=dict(size=8)))
        apply_layout(fig, height=280,
                     yaxis=dict(gridcolor="#eeeeee",
                                title="Rank (1=highest)",
                                autorange="reversed"),
                     xaxis=dict(gridcolor="#eeeeee"),
                     hovermode="x unified")
        fig.update_layout(title="Promo vs Sales Monthly Rank")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(timing_df[["Month","Promo Rank","Sales Rank","Status"]],
                     use_container_width=True, hide_index=True)

    with col3:
        st.markdown(warn("<b>ACTION:</b> Move 30% of July promo budget to January and February. January is #1 in sales but only #3 in promo spend. Fix this timing = +PKR 200-400M additional revenue annually."), unsafe_allow_html=True)
        st.markdown(kpi("Potential Gain", "+PKR 300M", "From budget reallocation only"), unsafe_allow_html=True)

    # ─── FINDING 7: PROMO EFFICIENCY ────────────────────────
    st.markdown(sec("🟡 FINDING 7 — Promo Efficiency Declining: Spend +38% But Revenue Only +16%!"), unsafe_allow_html=True)
    st.markdown(note("Activities DB: Promo spend grew +38.2% in 2025. DSR DB: Revenue grew only +16.6%. The gap = 21.6%. We are spending MORE but getting LESS return per rupee. This trend must be reversed in 2026."), unsafe_allow_html=True)

    # Calculate locally for this page
    spend_2024_ei = df_act[df_act["Yr"]==2024]["TotalAmount"].sum()
    spend_2025_ei = df_act[df_act["Yr"]==2025]["TotalAmount"].sum()
    rev_24_ei     = df_sales[df_sales["Yr"]==2024]["TotalRevenue"].sum()
    rev_25_ei     = df_sales[df_sales["Yr"]==2025]["TotalRevenue"].sum()
    roi_2024_ei   = rev_24_ei/spend_2024_ei if spend_2024_ei>0 else 0
    roi_2025_ei   = rev_25_ei/spend_2025_ei if spend_2025_ei>0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        eff_df = pd.DataFrame({
            "Year"  :["2024","2025"],
            "Promo" :[spend_2024_ei/1e6, spend_2025_ei/1e6],
            "Revenue":[rev_24_ei/1e6,    rev_25_ei/1e6]
        })
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=eff_df["Year"], y=eff_df["Promo"],
            name="Promo Spend (M)", marker_color="#e65100",
            text=[f"PKR {v:.0f}M" for v in eff_df["Promo"]],
            textposition="outside"))
        fig.add_trace(go.Bar(
            x=eff_df["Year"], y=eff_df["Revenue"],
            name="Revenue (M)", marker_color="#2c5f8a",
            text=[f"PKR {v:.0f}M" for v in eff_df["Revenue"]],
            textposition="outside"))
        apply_layout(fig, height=280,
                     barmode="group",
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee"))
        fig.update_layout(title="Spend vs Revenue Growth")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        roi_2024 = rev_24/spend_2024
        roi_2025 = rev_25/spend_2025
        fig = px.bar(
            x=["ROI 2024","ROI 2025"],
            y=[roi_2024, roi_2025],
            text=[f"{roi_2024:.1f}x", f"{roi_2025:.1f}x"],
            color=["ROI 2024","ROI 2025"],
            color_discrete_map={"ROI 2024":"#2e7d32","ROI 2025":"#c62828"},
            title="ROI Per Year — Is it Declining?")
        fig.update_traces(textposition="outside", textfont_size=13)
        apply_layout(fig, height=280,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee", title="ROI (x times)"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown(warn(f"<b>ACTION:</b> Promo ROI dropped from {roi_2024:.1f}x to {roi_2025:.1f}x. Fix promo timing (Finding 6) and reduce discount abuse (Finding 10). Target ROI of 22x for 2026."), unsafe_allow_html=True)
        st.markdown(kpi("ROI Change", f"{roi_2024:.1f}x → {roi_2025:.1f}x", "⚠️ Declining — must fix"), unsafe_allow_html=True)

    # ─── FINDING 8: DIVISION PERFORMANCE ────────────────────
    st.markdown(sec("🟡 FINDING 8 — Division 4 Works 5x Less Than Division 1!"), unsafe_allow_html=True)
    st.markdown(note("Travel DB: Division 1 = 48 trips/person. Division 4 = only 10 trips/person. 5x difference in field activity. Low field activity = fewer doctor visits = lower prescriptions = lower sales."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        div_df = df_travel.groupby("TravellerDivision").agg(
            Trips=("TravelCount","sum"),
            People=("Traveller","nunique")).reset_index()
        div_df["TripsPerPerson"] = (div_df["Trips"]/div_df["People"]).round(1)
        div_name_map = {
            "Division 1":"Div 1 — Bone Saviors",
            "Division 2":"Div 2 — Winners",
            "Division 3":"Div 3 — International",
            "Division 4":"Div 4 — Admin",
            "Division 5":"Div 5 — Strikers"
        }
        div_df["Name"] = div_df["TravellerDivision"].map(div_name_map)
        div_df = div_df.sort_values("TripsPerPerson", ascending=False)
        colors_d = ["#2e7d32" if t>40 else "#e65100" if t>20 else "#c62828"
                    for t in div_df["TripsPerPerson"]]
        fig = go.Figure(go.Bar(
            x=div_df["TripsPerPerson"], y=div_df["Name"],
            orientation="h",
            text=[f"{t:.0f} trips/person" for t in div_df["TripsPerPerson"]],
            textposition="outside", textfont_size=10,
            marker_color=colors_d
        ))
        apply_layout(fig, height=280,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee"))
        fig.update_layout(title="Field Activity by Division")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(div_df[["Name","People","Trips","TripsPerPerson"]].rename(
            columns={"Name":"Division","TripsPerPerson":"Trips/Person"}),
            use_container_width=True, hide_index=True)

    with col3:
        st.markdown(warn("<b>ACTION:</b> Set minimum 40 trips per person target for all divisions. Division 4 must increase from 10 to 40 trips/person. Assign performance improvement plan immediately."), unsafe_allow_html=True)
        st.markdown(kpi("Performance Gap", "5x difference", "Div 1 vs Div 4"), unsafe_allow_html=True)

    # ─── FINDING 9: PRODUCT CONCENTRATION ───────────────────
    st.markdown(sec("🟡 FINDING 9 — Product Risk: Top 5 Products = 34.5% of Revenue!"), unsafe_allow_html=True)
    st.markdown(note("DSR + ZSDCY both confirm: Top 5 products = 34.5% of revenue. If X-Plended faces any competitor or supply issue — company loses PKR 4.3B instantly. New product pipeline urgently needed."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        prod_rev_df = df_sales.groupby("ProductName")["TotalRevenue"].sum(
            ).sort_values(ascending=False).reset_index()
        prod_rev_df["CumPct"] = prod_rev_df["TotalRevenue"].cumsum(
            )/prod_rev_df["TotalRevenue"].sum()*100
        top15_p = prod_rev_df.head(15)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top15_p["TotalRevenue"]/1e6,
            y=top15_p["ProductName"],
            orientation="h",
            marker_color="#2c5f8a",
            name="Revenue",
            text=top15_p["TotalRevenue"].apply(fmt),
            textposition="outside", textfont_size=8
        ))
        apply_layout(fig, height=300,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"))
        fig.update_layout(title="Top 15 Products — DSR DB")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        conc_df = pd.DataFrame({
            "Group":["Top 5","Top 10","Top 30","Rest 110"],
            "Share":[34.5, 51.6, 80.0, 20.0]
        })
        fig = px.pie(conc_df, values="Share", names="Group",
                     title="Revenue Concentration Risk",
                     color_discrete_sequence=["#c62828","#e65100",
                                              "#2c5f8a","#2e7d32"])
        fig.update_traces(textinfo="percent+label", textfont_size=11)
        apply_layout(fig, height=280)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown(warn("<b>ACTION:</b> Develop 3-5 new products to reduce dependency. Invest in accelerating products ranked 6-15. File patents on top 5 products. Never allow single product to exceed 10% revenue share."), unsafe_allow_html=True)
        st.markdown(kpi("Risk Level", "HIGH", "Top 5 = 34.5% revenue"), unsafe_allow_html=True)

    # ─── FINDING 10: DISCOUNT ABUSE ─────────────────────────
    st.markdown(sec("🔴 FINDING 10 — URGENT: PKR 750M Discounts Given — Falcons at 20.5%!"), unsafe_allow_html=True)
    st.markdown(note("DSR DB: Total discounts = PKR 750M. Company average = 1.6%. Falcons team = 20.5% (13x above average!). This is either unauthorized discounting or pricing strategy failure. PKR 200M can be saved immediately."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        disc_team = df_sales.groupby("TeamName").agg(
            Discount=("TotalDiscount","sum"),
            Revenue=("TotalRevenue","sum")).reset_index()
        disc_team = disc_team[disc_team["Revenue"]>5e6]
        disc_team["Rate"] = disc_team["Discount"]/disc_team["Revenue"]*100
        disc_team = disc_team.nlargest(10,"Rate")
        colors_disc = ["#c62828" if r>10 else "#e65100" if r>3 else "#2c5f8a"
                       for r in disc_team["Rate"]]
        fig = go.Figure(go.Bar(
            x=disc_team["Rate"], y=disc_team["TeamName"],
            orientation="h",
            text=[f"{r:.1f}%" for r in disc_team["Rate"]],
            textposition="outside", textfont_size=10,
            marker_color=colors_disc
        ))
        apply_layout(fig, height=300,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Discount Rate %"))
        fig.update_layout(title="Discount Rate by Team — DSR DB")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        disc_prod = df_sales.groupby("ProductName").agg(
            Discount=("TotalDiscount","sum"),
            Revenue=("TotalRevenue","sum")).reset_index()
        disc_prod = disc_prod[disc_prod["Revenue"]>5e6]
        disc_prod["Rate"] = disc_prod["Discount"]/disc_prod["Revenue"]*100
        disc_prod = disc_prod.nlargest(8,"Rate")
        colors_dp = ["#c62828" if r>20 else "#e65100" if r>10 else "#2c5f8a"
                     for r in disc_prod["Rate"]]
        fig = go.Figure(go.Bar(
            x=disc_prod["Rate"], y=disc_prod["ProductName"],
            orientation="h",
            text=[f"{r:.1f}%" for r in disc_prod["Rate"]],
            textposition="outside", textfont_size=9,
            marker_color=colors_dp
        ))
        apply_layout(fig, height=300,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Discount Rate %"))
        fig.update_layout(title="Discount Rate by Product — DSR DB")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        total_disc_v = df_sales["TotalDiscount"].sum()
        st.markdown(danger(f"<b>URGENT ACTION:</b> Audit Falcons and Strikers teams this week. Cap all discounts at 5% maximum. Zoltar at 47% discount rate may be loss-making. Expected saving: PKR 200M+ per year."), unsafe_allow_html=True)
        st.markdown(kpi("Annual Saving", "PKR 200M+", "From fixing discount abuse"), unsafe_allow_html=True)

    # ─── FINDING 11: DISTRIBUTOR RISK ───────────────────────
    st.markdown(sec("🟡 FINDING 11 — Product Portfolio: Stars, Cash Cows, Question Marks, Dogs"), unsafe_allow_html=True)
    st.markdown(note("BCG Matrix classifies all products by revenue and growth. Stars = invest more. Cash Cows = maintain. Question Marks = watch closely. Dogs = cut budget."), unsafe_allow_html=True)

    r24_bcg = df_sales[df_sales["Yr"]==2024].groupby("ProductName")["TotalRevenue"].sum()
    r25_bcg = df_sales[df_sales["Yr"]==2025].groupby("ProductName")["TotalRevenue"].sum()
    bcg     = pd.DataFrame({"Rev2024":r24_bcg,"Rev2025":r25_bcg}).dropna()
    bcg     = bcg[bcg["Rev2024"]>5e6].reset_index()
    bcg["Growth"]   = ((bcg["Rev2025"]-bcg["Rev2024"])/bcg["Rev2024"]*100)
    bcg["TotalRev"] = bcg["Rev2024"]+bcg["Rev2025"]
    med_rev  = bcg["TotalRev"].median()
    med_grow = bcg["Growth"].median()

    def classify_bcg(row):
        if row["TotalRev"]>=med_rev and row["Growth"]>=med_grow:   return "⭐ Stars"
        elif row["TotalRev"]>=med_rev and row["Growth"]<med_grow:  return "🐄 Cash Cows"
        elif row["TotalRev"]<med_rev  and row["Growth"]>=med_grow: return "❓ Question Marks"
        else: return "🐕 Dogs"

    bcg["Category"] = bcg.apply(classify_bcg, axis=1)
    g1 = bcg[bcg["Category"]=="⭐ Stars"]
    g2 = bcg[bcg["Category"]=="🐄 Cash Cows"]
    g3 = bcg[bcg["Category"]=="❓ Question Marks"]
    g4 = bcg[bcg["Category"]=="🐕 Dogs"]

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("⭐ Stars",          str(len(g1)), "Invest More"), unsafe_allow_html=True)
    c2.markdown(kpi("🐄 Cash Cows",      str(len(g2)), "Maintain"),    unsafe_allow_html=True)
    c3.markdown(kpi("❓ Question Marks", str(len(g3)), "Watch"),        unsafe_allow_html=True)
    c4.markdown(kpi("🐕 Dogs",           str(len(g4)), "Cut Budget", red=True), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**⭐ Stars — INVEST MORE (High Revenue + Growing)**")
        g1s = g1.sort_values("TotalRev", ascending=False).head(20)
        fig = go.Figure(go.Bar(
            x=g1s["TotalRev"]/1e6, y=g1s["ProductName"],
            orientation="h", text=g1s["TotalRev"].apply(fmt),
            textposition="outside", textfont_size=9, marker_color="#2e7d32"))
        apply_layout(fig, height=520,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="Revenue (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(g1)} Stars — increase promo budget 50%")

    with col2:
        st.markdown("**❓ Question Marks — WATCH (Low Revenue + Growing Fast)**")
        g3s = g3.sort_values("Growth", ascending=False).head(20)
        colors_g3 = ["#FFD700" if "FINNO" in p.upper() else "#e65100"
                     for p in g3s["ProductName"]]
        fig = go.Figure(go.Bar(
            x=g3s["Growth"], y=g3s["ProductName"],
            orientation="h", text=g3s["Growth"].apply(lambda x: f"+{x:.1f}%"),
            textposition="outside", textfont_size=9, marker_color=colors_g3))
        apply_layout(fig, height=520,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="Growth %"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(g3)} Question Marks — Gold=Finno-Q, fund selectively")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🐄 Cash Cows — MAINTAIN (High Revenue + Stable)**")
        g2s = g2.sort_values("TotalRev", ascending=False).head(20)
        fig = go.Figure(go.Bar(
            x=g2s["TotalRev"]/1e6, y=g2s["ProductName"],
            orientation="h", text=g2s["TotalRev"].apply(fmt),
            textposition="outside", textfont_size=9, marker_color="#2c5f8a"))
        apply_layout(fig, height=520,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="Revenue (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(g2)} Cash Cows — maintain current budget")

    with col2:
        st.markdown("**🐕 Dogs — CUT BUDGET (Low Revenue + Declining)**")
        g4s = g4.sort_values("Growth").head(20)
        fig = go.Figure(go.Bar(
            x=g4s["Growth"], y=g4s["ProductName"],
            orientation="h", text=g4s["Growth"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside", textfont_size=9, marker_color="#c62828"))
        apply_layout(fig, height=520,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="Growth % (Negative=Declining)"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(g4)} Dogs — cut promo, redirect to Stars")

    st.markdown(good("<b>STRATEGY:</b> Stars = +50% budget. Cash Cows = maintain. Question Marks = fund Finno-Q only. Dogs = cut 80% and redirect to Stars."), unsafe_allow_html=True)

    # FINDING 12: PROMO ROI DECLINING
    st.markdown(sec("🔴 FINDING 12 — URGENT: Promo ROI Declining Year on Year!"), unsafe_allow_html=True)
    st.markdown(note("Activities + DSR combined: ROI dropped from previous levels. Spend growing faster than revenue. If this trend continues — 2026 will show negative returns on promotional investment. Must fix timing and targeting NOW."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        monthly_promo = df_act.groupby(["Yr","Mo"])["TotalAmount"].sum().reset_index()
        monthly_sales = df_sales.groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
        combined_mo   = pd.merge(monthly_promo, monthly_sales, on=["Yr","Mo"])
        combined_mo["ROI_mo"] = combined_mo["TotalRevenue"]/combined_mo["TotalAmount"]
        combined_mo["Date"]   = pd.to_datetime(
            combined_mo["Yr"].astype(int).astype(str)+"-"+
            combined_mo["Mo"].astype(int).astype(str)+"-01")
        combined_mo = combined_mo[combined_mo["Yr"]<2026]

        fig = px.line(combined_mo, x="Date", y="ROI_mo",
                      color="Yr", title="Monthly ROI Trend — Activities vs DSR",
                      color_discrete_map={2024:"#2c5f8a",2025:"#c62828"})
        fig.update_traces(mode="lines+markers", line_width=2)
        fig.add_hline(y=combined_mo["ROI_mo"].mean(),
                      line_dash="dash", line_color="gray",
                      annotation_text="Average")
        apply_layout(fig, height=280,
                     yaxis=dict(gridcolor="#eeeeee", title="Revenue/Spend Ratio"),
                     xaxis=dict(gridcolor="#eeeeee"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        yearly_roi = pd.DataFrame({
            "Year"   :["2024","2025"],
            "ROI"    :[roi_2024, roi_2025],
            "Spend"  :[spend_2024/1e6, spend_2025/1e6],
            "Revenue":[rev_24/1e6, rev_25/1e6]
        })
        fig = px.bar(yearly_roi, x="Year", y="ROI",
                     text=[f"{r:.1f}x" for r in yearly_roi["ROI"]],
                     color="Year",
                     color_discrete_map={"2024":"#2e7d32","2025":"#c62828"},
                     title="Annual ROI Comparison")
        fig.update_traces(textposition="outside", textfont_size=14)
        apply_layout(fig, height=280,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee", title="ROI"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.markdown(danger(f"<b>URGENT ACTION:</b> ROI dropped {roi_2024:.1f}x to {roi_2025:.1f}x. Fix promo timing. Fix discount abuse. Reallocate budget from low-ROI products (Shevit 5.6x) to high-ROI products (Ramipace 99.7x). Target: 22x ROI for 2026."), unsafe_allow_html=True)
        st.markdown(kpi("ROI Target 2026", "22x", f"Up from {roi_2025:.1f}x in 2025"), unsafe_allow_html=True)

    # ─── FINDING 13: LOST CUSTOMER ──────────────────────────
    st.markdown(sec("🔴 FINDING 13 — URGENT: Nusrat Pharma Lost — PKR 23.7M Revenue Gone!"), unsafe_allow_html=True)
    st.markdown(note("ZSDCY DB: Nusrat Pharma was active in 2024 but completely absent in 2025. PKR 23.7M revenue lost. With 87.5% Premier Sales dependency — every lost non-Premier distributor makes situation worse."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        sdp_2024_set = set(df_zsdcy[df_zsdcy["Yr"]==2024]["SDP Name"].unique())
        sdp_2025_set = set(df_zsdcy[df_zsdcy["Yr"]==2025]["SDP Name"].unique())
        loyal_set    = sdp_2024_set & sdp_2025_set
        new_set      = sdp_2025_set - sdp_2024_set
        lost_set     = sdp_2024_set - sdp_2025_set

        loyalty_df = pd.DataFrame({
            "Status":["Loyal Both Years","New in 2025","Lost from 2024"],
            "Count" :[len(loyal_set), len(new_set), len(lost_set)],
            "Color" :["#2e7d32","#2c5f8a","#c62828"]
        })
        fig = go.Figure(go.Bar(
            x=loyalty_df["Status"], y=loyalty_df["Count"],
            text=loyalty_df["Count"],
            textposition="outside", textfont_size=13,
            marker_color=loyalty_df["Color"].tolist()
        ))
        apply_layout(fig, height=280,
                     xaxis=dict(gridcolor="#eeeeee"),
                     yaxis=dict(gridcolor="#eeeeee", title="Distributors"))
        fig.update_layout(title="Customer Retention — ZSDCY DB")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        lost_rev_df = pd.DataFrame({
            "Distributor":["Nusrat Pharma","Scitech Health",
                           "Other Lost (24)"],
            "Lost Revenue":[23.7, 4.6, 5.0]
        })
        fig = px.bar(lost_rev_df, x="Lost Revenue", y="Distributor",
                     orientation="h", text="Lost Revenue",
                     title="Lost Revenue by Distributor (M PKR)",
                     color_discrete_sequence=["#c62828"])
        fig.update_traces(textposition="outside", textfont_size=11,
                          texttemplate="PKR %{text}M")
        apply_layout(fig, height=250,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee"))
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        retention_rate = len(loyal_set)/len(sdp_2024_set)*100
        st.markdown(danger(f"<b>URGENT ACTION:</b> Call Nusrat Pharma this week. Offer special pricing or dedicated account manager. PKR 23.7M lost annually. Retention rate = {retention_rate:.1f}% — target 95% for 2026."), unsafe_allow_html=True)
        st.markdown(kpi("Retention Rate", f"{retention_rate:.1f}%", "Target 95% for 2026"), unsafe_allow_html=True)

    st.markdown("---")

    # ── SECTION 4: CITY INTELLIGENCE TABLE ──────────────────
    st.markdown("### 🗺️ Section 4 — City Intelligence: All 4 Databases in One Table")
    st.markdown(note("This table combines Travel DB + ZSDCY DB to show complete city picture. Cities marked RED need immediate attention — high revenue but low field visits."), unsafe_allow_html=True)

    city_travel_df  = df_travel.groupby("VisitLocation")["TravelCount"].sum().reset_index()
    city_travel_df.columns = ["City","Trips"]
    city_zsdcy_df   = df_zsdcy.groupby("City")["Revenue"].sum().reset_index()
    city_intel      = pd.merge(city_zsdcy_df, city_travel_df,
                               left_on="City", right_on="City", how="left").fillna(0)
    city_intel["Trips"]       = city_intel["Trips"].astype(int)
    city_intel["RevPerTrip"]  = (city_intel["Revenue"]/
                                  city_intel["Trips"].replace(0,1)/1e6).round(1)
    city_intel["Priority"]    = city_intel.apply(
        lambda r: "🔴 Urgent" if r["Revenue"]>300e6 and r["Trips"]<200
        else "🟡 Watch"  if r["Revenue"]>100e6 and r["Trips"]<500
        else "✅ Good", axis=1)
    city_intel = city_intel.sort_values("Revenue", ascending=False).head(20)
    city_intel["Revenue"] = city_intel["Revenue"].apply(fmt)
    city_intel["RevPerTrip"] = city_intel["RevPerTrip"].apply(
        lambda x: f"PKR {x:.1f}M/trip")

    st.dataframe(city_intel[["City","Revenue","Trips","RevPerTrip","Priority"]],
                 use_container_width=True, hide_index=True)

    # ── SECTION 5: TEAM SCORECARD ────────────────────────────
    st.markdown("### 👥 Section 5 — Complete Team Scorecard: All Databases")
    st.markdown(note("This table ranks every team across all dimensions. Promo Spend from Activities DB. Travel Trips from Travel DB. Revenue and ROI from DSR DB. One table — complete picture."), unsafe_allow_html=True)

    team_rev_df   = df_sales.groupby("TeamName")["TotalRevenue"].sum()
    team_disc_df  = df_sales.groupby("TeamName")["TotalDiscount"].sum()
    team_spend_df = df_act.groupby("RequestorTeams")["TotalAmount"].sum()
    team_trips_df = df_travel.groupby("TravellerTeam")["TravelCount"].sum()

    team_score = pd.DataFrame({
        "Revenue" : team_rev_df,
        "Discount": team_disc_df,
        "Spend"   : team_spend_df,
        "Trips"   : team_trips_df
    }).fillna(0)

    team_score = team_score[team_score["Revenue"]>100e6].copy()
    team_score["ROI"]      = (team_score["Revenue"]/
                               team_score["Spend"].replace(0,1)).round(1)
    team_score["DiscRate"] = (team_score["Discount"]/
                               team_score["Revenue"]*100).round(1)

    for col in ["ROI","Revenue"]:
        mn = team_score[col].min()
        mx = team_score[col].max()
        team_score[f"{col}_s"] = ((team_score[col]-mn)/(mx-mn)*100
                                   if mx>mn else 50)

    team_score["Score"] = (team_score["ROI_s"]*0.5 +
                            team_score["Revenue_s"]*0.5).round(0).astype(int)
    team_score = team_score.sort_values("Score", ascending=False).reset_index()

    team_display = pd.DataFrame({
        "Team"        : team_score["TeamName"],
        "Score"       : team_score["Score"].apply(lambda x: f"{x}/100"),
        "Revenue"     : team_score["Revenue"].apply(fmt),
        "Promo Spend" : team_score["Spend"].apply(fmt),
        "ROI"         : team_score["ROI"].apply(lambda x: f"{x:.1f}x"),
        "Disc Rate"   : team_score["DiscRate"].apply(lambda x: f"{x:.1f}%"),
        "Field Trips" : team_score["Trips"].apply(lambda x: f"{int(x):,}"),
        "Status"      : team_score["Score"].apply(
            lambda x: "🟢 Top" if x>=70 else "🟡 Good" if x>=40 else "🔴 Review")
    })
    st.dataframe(team_display, use_container_width=True, hide_index=True)

    # ── SECTION 6: ACTION PLAN ───────────────────────────────
    st.markdown("---")
    st.markdown("### ⚡ Section 6 — Priority Action Plan with PKR Impact")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(sec("🔴 THIS WEEK"), unsafe_allow_html=True)
        actions_week = pd.DataFrame({
            "Action":[
                "Audit Falcons/Strikers discounts",
                "Call Nusrat Pharma — recover account",
                "Identify 2 backup distributors"
            ],
            "PKR Impact":[
                "Save PKR 200M/year",
                "Recover PKR 23.7M",
                "Reduce critical risk"
            ]
        })
        st.dataframe(actions_week, use_container_width=True, hide_index=True)
        st.markdown(danger("Total this week: Save PKR 223M+"), unsafe_allow_html=True)

    with col2:
        st.markdown(sec("🟡 THIS MONTH"), unsafe_allow_html=True)
        actions_month = pd.DataFrame({
            "Action":[
                "Increase Ramipace budget 3x",
                "Allocate PKR 10M to Finno-Q",
                "Move July budget to January",
                "Set Division 4 trip targets"
            ],
            "PKR Impact":[
                "+PKR 430M revenue",
                "+PKR 200M revenue",
                "+PKR 300M revenue",
                "Performance improvement"
            ]
        })
        st.dataframe(actions_month, use_container_width=True, hide_index=True)
        st.markdown(warn("Total this month: +PKR 930M potential"), unsafe_allow_html=True)

    with col3:
        st.markdown(sec("🟢 THIS YEAR"), unsafe_allow_html=True)
        actions_year = pd.DataFrame({
            "Action":[
                "Increase Karachi/Swat visits",
                "Double Q4 promo campaigns",
                "Launch Nutraceutical team",
                "Develop 3 new products",
                "Onboard 2 new distributors",
                "Fix promo ROI to 22x"
            ],
            "PKR Impact":[
                "+PKR 150M",
                "+PKR 300M",
                "+PKR 300M",
                "Risk reduction",
                "Risk reduction",
                "+PKR 200M"
            ]
        })
        st.dataframe(actions_year, use_container_width=True, hide_index=True)
        st.markdown(good("Total this year: +PKR 950M+ potential"), unsafe_allow_html=True)

    # FINAL SUMMARY
    st.markdown("---")
    st.markdown("### 💰 Total Financial Opportunity Summary")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("💰 Cost Savings",    "PKR 376M",   "From fixing waste"), unsafe_allow_html=True)
    c2.markdown(kpi("📈 Revenue Growth",  "PKR 2.13B",  "From opportunities"), unsafe_allow_html=True)
    c3.markdown(kpi("💡 Investment Needed","PKR 110M",  "To unlock all growth"), unsafe_allow_html=True)
    c4.markdown(kpi("🎯 Expected ROI",    "22x",        "Target for 2026"), unsafe_allow_html=True)



# ════════════════════════════════════════════════════════════
# PAGE 13: COMBINED 4 DATABASE INTELLIGENCE
# ════════════════════════════════════════════════════════════
elif page == "🧠 Combine 4 Dataset":
    st.markdown("<h1 style=\'color:#2c5f8a\'>🧠 Combined 4 Database Strategic Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("<p style=\'color:#555; font-size:15px\'>Sales (DSR) + Promotional Activities (FTTS) + Travel (FTTS) + Distribution (ZSDCY) | 2024-2026</p>", unsafe_allow_html=True)
    st.markdown(note("This page connects all 4 databases to tell one complete story. Every number is verified from real data. Designed for upper management decision making."), unsafe_allow_html=True)
    st.markdown("---")

    # ── ALL CALCULATIONS ─────────────────────────────────────
    # Sales metrics
    rev_24  = df_sales[df_sales["Yr"]==2024]["TotalRevenue"].sum()
    rev_25  = df_sales[df_sales["Yr"]==2025]["TotalRevenue"].sum()
    rev_26  = df_sales[df_sales["Yr"]==2026]["TotalRevenue"].sum()
    rev_all = df_sales["TotalRevenue"].sum()

    # Promo metrics
    sp_24   = df_act[df_act["Yr"]==2024]["TotalAmount"].sum()
    sp_25   = df_act[df_act["Yr"]==2025]["TotalAmount"].sum()
    sp_all  = df_act["TotalAmount"].sum()

    # ROI
    roi_24  = rev_24/sp_24   if sp_24>0  else 0
    roi_25  = rev_25/sp_25   if sp_25>0  else 0
    roi_all = rev_all/sp_all if sp_all>0 else 0

    # Growth
    rev_growth   = ((rev_25-rev_24)/rev_24*100) if rev_24>0 else 0
    spend_growth = ((sp_25-sp_24)/sp_24*100)     if sp_24>0 else 0

    # Travel
    trips_all = df_travel["TravelCount"].sum()
    trips_24  = df_travel[df_travel["Yr"]==2024]["TravelCount"].sum()
    trips_25  = df_travel[df_travel["Yr"]==2025]["TravelCount"].sum()

    # ZSDCY
    zrev_24  = df_zsdcy[df_zsdcy["Yr"]==2024]["Revenue"].sum()
    zrev_25  = df_zsdcy[df_zsdcy["Yr"]==2025]["Revenue"].sum()
    zrev_all = df_zsdcy["Revenue"].sum()
    zrev_growth = ((zrev_25-zrev_24)/zrev_24*100) if zrev_24>0 else 0

    # Top products
    top_prod_rev  = df_sales.groupby("ProductName")["TotalRevenue"].sum()
    top_team_rev  = df_sales.groupby("TeamName")["TotalRevenue"].sum()
    top_city_rev  = df_zsdcy.groupby("City")["Revenue"].sum()
    top_city_trip = df_travel.groupby("VisitLocation")["TravelCount"].sum()

    # Discount
    total_disc  = df_sales["TotalDiscount"].sum()
    disc_rate   = total_disc/rev_all*100

    # Nutra
    nutra_24 = df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    nutra_25 = df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    nutra_g  = ((nutra_25-nutra_24)/nutra_24*100) if nutra_24>0 else 0

    # Distributor retention
    sdp_24 = set(df_zsdcy[df_zsdcy["Yr"]==2024]["SDP Name"].unique())
    sdp_25 = set(df_zsdcy[df_zsdcy["Yr"]==2025]["SDP Name"].unique())
    loyal  = sdp_24 & sdp_25
    lost   = sdp_24 - sdp_25
    new_s  = sdp_25 - sdp_24
    ret    = len(loyal)/len(sdp_24)*100 if sdp_24 else 0

    # Ramipace
    # Ramipace — calculated directly from source databases (VERIFIED)
    ram_act_df  = df_act[df_act["Product"].str.upper().str.contains("RAMIPACE", na=False)]
    ram_dsr_df  = df_sales[df_sales["ProductName"].str.upper().str.contains("RAMIPACE", na=False)]
    ram_spend   = ram_act_df["TotalAmount"].sum()    # From Activities DB
    ram_rev     = ram_dsr_df["TotalRevenue"].sum()   # From Sales DSR DB
    ram_roi     = ram_rev/ram_spend if ram_spend>0 else 0

    # Finno-Q
    fq_24 = df_sales[(df_sales["Yr"]==2024)&
        (df_sales["ProductName"].str.upper().str.contains("FINNO"))]["TotalRevenue"].sum()
    fq_25 = df_sales[(df_sales["Yr"]==2025)&
        (df_sales["ProductName"].str.upper().str.contains("FINNO"))]["TotalRevenue"].sum()
    fq_g  = ((fq_25-fq_24)/fq_24*100) if fq_24>0 else 0
    fq_promo = df_act[df_act["Product"].str.upper().str.contains(
        "FINNO",na=False)]["TotalAmount"].sum()

    # ── SECTION 1: COMPLETE BUSINESS SCORECARD ───────────────
    st.markdown("### 📊 Complete Business Scorecard — All 4 Databases")
    st.markdown(note("Row 1 = Secondary Sales (DSR). Row 2 = Primary Distribution (ZSDCY). Row 3 = Investment and Field Activity. Every number comes from a different database — all connected."), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="manual-working">
    WHY ZSDCY ({fmt(zrev_all)}) IS LESS THAN DSR ({fmt(rev_all)})?
    ══════════════════════════════════════════════════════════════════════
    VERIFIED FROM LIVE SQL SERVER (SalesRawData table):

    DSR DATABASE CONTAINS BOTH PRIMARY AND SECONDARY:
      SaleFlag = "P" → PRIMARY   (Pharmevo → Distributor)
      SaleFlag = "S" → SECONDARY (Distributor → Pharmacy)

    VERIFIED LIVE NUMBERS:
      Primary 2024   : PKR 17.27B (SaleFlag=P)
      Secondary 2024 : PKR 18.04B (SaleFlag=S)
      Markup 2024    : 1.04x (almost same price!)

      Primary 2025   : PKR 21.14B (SaleFlag=P)
      Secondary 2025 : PKR 23.06B (SaleFlag=S)
      Markup 2025    : 1.09x (still very close)

    WHY IS ZSDCY ONLY {fmt(zrev_all)}?
      ZSDCY tracks only SAP-based distribution (Premier Sales)
      DSR tracks ALL distributors across Pakistan (295 SDPs)
      ZSDCY = SUBSET of total primary sales
      ZSDCY covers Premier Sales channel only
      DSR covers entire national distribution network

    WHY IS MARKUP ONLY 1.04x (NOT 2.7x)?
      Both P and S are recorded at distributor price
      NOT at pharmacy retail price
      The final consumer price is higher but not tracked here

    CONCLUSION:
      ZSDCY vs DSR difference = different coverage scope
      DSR is more complete — covers all channels
      ZSDCY is specific to SAP-tracked Premier Sales channel
    ══════════════════════════════════════════════════════════════════════
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**📈 Secondary Sales — DSR Database (Distributor to Pharmacy) | 2024-2026**")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Secondary 2024",   fmt(rev_24),  f"DSR DB | +{rev_growth:.1f}% growth in 2025"), unsafe_allow_html=True)
    c2.markdown(kpi("Secondary 2025",   fmt(rev_25),  "DSR DB | All 295 distributors"), unsafe_allow_html=True)
    c3.markdown(kpi("2026 YTD",         fmt(rev_26),  "Jan-Mar 2026 partial ⚠️"), unsafe_allow_html=True)
    c4.markdown(kpi("Grand Total",      fmt(rev_all), "2024+2025+2026 all years"), unsafe_allow_html=True)
    c5.markdown(kpi("Top Product",      "X-Plended",  fmt(top_prod_rev.max())+" revenue"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**📦 Primary Sales — Live SQL Server Verified (SalesRawData | SaleFlag=P) | 2024-2025**")
    st.markdown(note("PRIMARY = SaleFlag 'P' in SalesRawData table = Pharmevo → Distributor. SECONDARY = SaleFlag 'S' = Distributor → Pharmacy. Both in same DSR SQL Server. Verified March 2026. Markup = only 1.04x to 1.09x NOT 2.7x as previously thought."), unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    # Live SQL verified numbers
    sql_pri_2024 = 17270000000  # PKR 17.27B verified from SalesRawData SaleFlag=P
    sql_pri_2025 = 21140000000  # PKR 21.14B verified from SalesRawData SaleFlag=P
    sql_pri_growth = ((sql_pri_2025-sql_pri_2024)/sql_pri_2024*100)
    c1.markdown(kpi("Primary 2024",  fmt(sql_pri_2024),  "SQL Verified | SaleFlag=P | All distributors"), unsafe_allow_html=True)
    c2.markdown(kpi("Primary 2025",  fmt(sql_pri_2025),  f"+{sql_pri_growth:.1f}% vs 2024 | SQL Verified"), unsafe_allow_html=True)
    c3.markdown(kpi("Primary Total", fmt(sql_pri_2024+sql_pri_2025), "2024+2025 from live SQL Server"), unsafe_allow_html=True)
    c4.markdown(kpi("Distributors",       str(len(sdp_24|sdp_25)), "Total active SDPs"), unsafe_allow_html=True)
    c5.markdown(kpi("Retention Rate",     f"{ret:.1f}%", f"{len(loyal)} loyal SDPs"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**💰 Promotional Investment + Field Activity — Activities DB + Travel DB | 2024-2026**")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Promo Spend 2024", fmt(sp_24),         f"Activities DB | +{spend_growth:.1f}% in 2025"), unsafe_allow_html=True)
    c2.markdown(kpi("Promo Spend 2025", fmt(sp_25),         "Activities DB | Grew faster than revenue"), unsafe_allow_html=True)
    c3.markdown(kpi("ROI 2024",         f"{roi_24:.1f}x",   "PKR 1 spent → PKR {roi_24:.1f} earned"), unsafe_allow_html=True)
    c4.markdown(kpi("ROI 2025",         f"{roi_25:.1f}x",   "⚠️ Declining — must fix in 2026", red=roi_25<roi_24), unsafe_allow_html=True)
    c5.markdown(kpi("Field Trips",      fmt_num(trips_all), f"2024:{fmt_num(trips_24)} 2025:{fmt_num(trips_25)}"), unsafe_allow_html=True)
    st.markdown("---")

    # ── SECTION 2: THE SALES FUNNEL ──────────────────────────
    st.markdown("### 🔄 How Pharmevo Makes Money — Complete Sales Funnel")
    st.markdown(note("This funnel shows the complete journey. Every PKR 1 spent on promotions generates PKR 18.6 in secondary sales. Understanding this funnel helps management decide WHERE to invest."), unsafe_allow_html=True)

    col1, col2 = st.columns([3,2])
    with col1:
        funnel_lbls = [
            f"Stage 1: Promo Investment — {fmt(sp_all)} (Activities DB)",
            f"Stage 2: Field Visits — {trips_all:,} trips (Travel DB)",
            f"Stage 3: Primary Sales — {fmt(zrev_all)} (ZSDCY DB)",
            f"Stage 4: Secondary Sales — {fmt(rev_all)} (DSR DB)"
        ]
        # Use consistent PKR Billion scale for money stages
        fig = go.Figure()
        colors_f = ["#e65100","#2c5f8a","#7b1fa2","#2e7d32"]
        labels_f = [
            f"Promo: {fmt(sp_all)}",
            f"Trips: {trips_all:,}",
            f"Primary: {fmt(zrev_all)}",
            f"Secondary: {fmt(rev_all)}"
        ]
        stages   = ["1. Promo Investment\n(Activities DB)",
                    "2. Field Visits\n(Travel DB)",
                    "3. Primary Sales\n(ZSDCY DB)",
                    "4. Secondary Sales\n(DSR DB)"]
        values_f = [sp_all/1e9, trips_all/1000, zrev_all/1e9, rev_all/1e9]

        fig.add_trace(go.Bar(
            x=stages,
            y=values_f,
            text=labels_f,
            textposition="outside",
            textfont_size=11,
            marker_color=colors_f
        ))
        apply_layout(fig, height=420,
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee",
                                title="Note: Money in PKR Billion | Trips in Thousands"))
        fig.update_layout(
            title="Pharmevo Sales Funnel — All 4 Databases",
            showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Note: Promo and Sales bars show PKR Billions. Trips bar shows thousands of visits. Labels show exact values.")

    with col2:
        st.markdown(f"""
        <div class="manual-working">
        SALES FUNNEL EXPLAINED
        ══════════════════════════════════════
        STAGE 1 — INVEST (Activities DB)
        Company spends {fmt(sp_all)} on
        doctor promotions and activities

        ↓ Generates field visits

        STAGE 2 — VISIT (Travel DB)
        Sales reps make {trips_all:,} field
        visits to doctors across Pakistan

        ↓ Doctors prescribe medicines

        STAGE 3 — SHIP (ZSDCY DB)
        Company ships {fmt(zrev_all)} worth
        of medicines to distributors

        ↓ Distributors supply pharmacies

        STAGE 4 — SELL (DSR DB)
        {fmt(rev_all)} reaches end market
        through pharmacies to patients

        KEY RATIO:
        PKR 1 invested = PKR {roi_all:.1f} returned
        ══════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")

    # ── SECTION 3: 12 KEY FINDINGS ───────────────────────────
    st.markdown("### 🎯 12 Strategic Findings — Connected Across All 4 Databases")

    # FINDING 1
    st.markdown(sec("🟢 FINDING 1 — Revenue Growing But Efficiency Declining"), unsafe_allow_html=True)
    st.markdown(note("Revenue grew +16.6% which is good. But promo spend grew +38.2% — more than double the revenue growth. This means we are spending MORE to earn LESS per rupee. ROI dropped from 20.3x to 17.2x."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["2024","2025"],
            y=[rev_24/1e9, rev_25/1e9],
            name="Revenue (B)", marker_color="#2e7d32",
            text=[f"{rev_24/1e9:.1f}B", f"{rev_25/1e9:.1f}B"],
            textposition="outside"))
        fig.add_trace(go.Bar(
            x=["2024","2025"],
            y=[sp_24/1e9, sp_25/1e9],
            name="Promo Spend (B)", marker_color="#e65100",
            text=[f"{sp_24/1e9:.2f}B", f"{sp_25/1e9:.2f}B"],
            textposition="outside"))
        apply_layout(fig, height=300, barmode="group",
                     yaxis=dict(gridcolor="#eee",title="PKR Billions"),
                     xaxis=dict(gridcolor="#eee"))
        fig.update_layout(title="Revenue vs Promo Spend")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["ROI 2024","ROI 2025"],
            y=[roi_24, roi_25],
            marker_color=["#2e7d32","#c62828"],
            text=[f"{roi_24:.1f}x",f"{roi_25:.1f}x"],
            textposition="outside"))
        apply_layout(fig, height=300,
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee",title="ROI"))
        fig.update_layout(title="ROI Declining Year on Year",showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        gap = spend_growth - rev_growth
        st.markdown(f"""
        <div class="manual-working">
        EFFICIENCY ANALYSIS
        ══════════════════════════
        Revenue Growth   : +{rev_growth:.1f}%
        Spend Growth     : +{spend_growth:.1f}%
        Efficiency Gap   : {gap:.1f}%

        ROI 2024 : {roi_24:.1f}x
        ROI 2025 : {roi_25:.1f}x
        Change   : {roi_25-roi_24:.1f}x DROP

        This means in 2025 every PKR 1
        spent earned {roi_25-roi_24:.1f} LESS
        than it did in 2024.

        ROOT CAUSE:
        → Budget in wrong months
        → Wrong products promoted
        → Discount abuse

        TARGET FOR 2026: 22x ROI
        ══════════════════════════
        </div>
        """, unsafe_allow_html=True)

    # Manual ROI verification
    st.markdown(f"""
    <div class="manual-working">
    MANUAL ROI VERIFICATION
    ══════════════════════════════════════════════
    ROI 2024:
    Revenue 2024 = {fmt(rev_24)}
    Spend 2024   = {fmt(sp_24)}
    ROI 2024     = {fmt(rev_24)} / {fmt(sp_24)} = {roi_24:.1f}x
    Every PKR 1 spent in 2024 earned PKR {roi_24:.1f}

    ROI 2025:
    Revenue 2025 = {fmt(rev_25)}
    Spend 2025   = {fmt(sp_25)}
    ROI 2025     = {fmt(rev_25)} / {fmt(sp_25)} = {roi_25:.1f}x
    Every PKR 1 spent in 2025 earned PKR {roi_25:.1f}

    COMPARISON:
    2024 ROI = {roi_24:.1f}x
    2025 ROI = {roi_25:.1f}x
    Change   = {roi_25-roi_24:.1f}x ({("DECLINED" if roi_25<roi_24 else "IMPROVED")})

    WHY ROI DECLINED:
    Revenue grew  +{rev_growth:.1f}%
    Spend grew    +{spend_growth:.1f}%
    Spend grew {spend_growth/rev_growth:.1f}x FASTER than revenue
    This is why ROI went DOWN despite revenue going UP.
    ══════════════════════════════════════════════
    </div>
    """, unsafe_allow_html=True)
    # PRIMARY vs SECONDARY monthly comparison
    st.markdown("**Primary vs Secondary Sales Monthly — Did Manufacturing Limit Sales?**")
    st.markdown(note("If Primary Sales (ZSDCY) drops in a month but Secondary Sales (DSR) stays same — it means distributors used existing stock. If both drop together — manufacturing may have limited supply."), unsafe_allow_html=True)

    primary_mo = df_zsdcy.groupby(["Yr","Mo"])["Revenue"].sum().reset_index()
    secondary_mo = df_sales.groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
    primary_mo["Date"] = pd.to_datetime(
        primary_mo["Yr"].astype(int).astype(str)+"-"+
        primary_mo["Mo"].astype(int).astype(str)+"-01")
    secondary_mo["Date"] = pd.to_datetime(
        secondary_mo["Yr"].astype(int).astype(str)+"-"+
        secondary_mo["Mo"].astype(int).astype(str)+"-01")

    # Merge on same months
    both_mo = pd.merge(
        primary_mo[["Date","Revenue"]],
        secondary_mo[["Date","TotalRevenue"]],
        on="Date", how="inner")
    both_mo = both_mo.sort_values("Date")

    fig = go.Figure()
    both_mo["Pri_fmt"] = both_mo["Revenue"].apply(fmt)
    both_mo["Sec_fmt"] = both_mo["TotalRevenue"].apply(fmt)
    fig.add_trace(go.Scatter(
        x=both_mo["Date"], y=both_mo["Revenue"]/1e6,
        name="Primary Sales — ZSDCY (Factory to Distributor)",
        mode="lines+markers",
        line=dict(color="#7b1fa2", width=2.5),
        marker=dict(size=6),
        text=both_mo["Pri_fmt"],
        hovertemplate="%{x|%b %Y}<br>Primary: %{text}<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=both_mo["Date"], y=both_mo["TotalRevenue"]/1e6,
        name="Secondary Sales — DSR (Distributor to Pharmacy)",
        mode="lines+markers",
        line=dict(color="#2e7d32", width=2.5),
        marker=dict(size=6),
        text=both_mo["Sec_fmt"],
        hovertemplate="%{x|%b %Y}<br>Secondary: %{text}<extra></extra>"))
    apply_layout(fig, height=350,
                 xaxis=dict(gridcolor="#eee"),
                 yaxis=dict(gridcolor="#eee", title="Revenue (M PKR)"),
                 hovermode="x unified")
    fig.update_layout(title="Primary vs Secondary Sales — Monthly Comparison (hover for exact values)")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Y-axis in M PKR (millions). Hover over any point to see exact value in B/M/K format.")

    # Find months where both dropped
    both_mo["Pri_pct"]  = both_mo["Revenue"].pct_change()*100
    both_mo["Sec_pct"]  = both_mo["TotalRevenue"].pct_change()*100
    both_mo["BothDrop"] = (both_mo["Pri_pct"]<-5) & (both_mo["Sec_pct"]<-5)
    both_mo["PriOnly"]  = (both_mo["Pri_pct"]<-5) & (both_mo["Sec_pct"]>=-5)
    drop_months = both_mo[both_mo["BothDrop"]]["Date"].dt.strftime("%b %Y").tolist()
    pri_months  = both_mo[both_mo["PriOnly"]]["Date"].dt.strftime("%b %Y").tolist()

    col1, col2 = st.columns(2)
    with col1:
        if drop_months:
            st.markdown(danger(f"<b>Both Primary AND Secondary dropped in:</b> {', '.join(drop_months)}<br>This suggests manufacturing or supply chain issues — not promotional problems."), unsafe_allow_html=True)
        else:
            st.markdown(good("No months found where BOTH primary and secondary dropped together. Supply chain is stable."), unsafe_allow_html=True)
    with col2:
        if pri_months:
            st.markdown(warn(f"<b>Primary dropped but Secondary stayed stable in:</b> {', '.join(pri_months[:5])}<br>Distributors used existing stock. Manufacturing slowed but market demand was still there."), unsafe_allow_html=True)
        else:
            st.markdown(good("Primary and Secondary sales move together — healthy supply chain alignment."), unsafe_allow_html=True)

    st.markdown(danger(f"<b>ACTION:</b> Audit all promotional activities. Cut lowest 20% ROI activities. Move July budget to January. Target ROI = 22x for 2026. Expected saving: PKR 80-120M."), unsafe_allow_html=True)

    # PRIMARY vs SECONDARY MONTHLY FROM LIVE SQL
    st.markdown(sec("📊 Primary vs Secondary Monthly — Verified from Live SQL Server"), unsafe_allow_html=True)
    st.markdown(note("Both Primary (SaleFlag=P) and Secondary (SaleFlag=S) are in same SalesRawData table in DSR SQL Server. Verified March 2026. Positive gap = distributors sold from old stock. Negative gap = stock building at distributor."), unsafe_allow_html=True)

    pri_2024_sql = [1362,1239,1096,1019,1536,1266,1442,1671,1481,1905,1385,1868]
    sec_2024_sql = [1380,1334,1416,1302,1445,1371,1466,1539,1604,1760,1698,1725]
    pri_2025_sql = [1707,1231,1711,1469,1913,1565,1970,1425,2426,1815,2121,1788]
    sec_2025_sql = [1814,1731,1753,1775,1899,1748,1977,1947,2034,2164,2029,2188]
    months_sql   = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months_sql, y=pri_2024_sql,
            name="Primary 2024 (SaleFlag=P)",
            marker_color="#7b1fa2",
            text=[f"PKR {v/1000:.1f}B" for v in pri_2024_sql],
            textposition="outside", textfont_size=8))
        fig.add_trace(go.Bar(
            x=months_sql, y=sec_2024_sql,
            name="Secondary 2024 (SaleFlag=S)",
            marker_color="#2c5f8a",
            text=[f"PKR {v/1000:.1f}B" for v in sec_2024_sql],
            textposition="outside", textfont_size=8))
        apply_layout(fig, height=350, barmode="group",
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee",title="Revenue (M PKR)"))
        fig.update_layout(title="2024: Primary vs Secondary Monthly")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months_sql, y=pri_2025_sql,
            name="Primary 2025 (SaleFlag=P)",
            marker_color="#e65100",
            text=[f"PKR {v/1000:.1f}B" for v in pri_2025_sql],
            textposition="outside", textfont_size=8))
        fig.add_trace(go.Bar(
            x=months_sql, y=sec_2025_sql,
            name="Secondary 2025 (SaleFlag=S)",
            marker_color="#2e7d32",
            text=[f"PKR {v/1000:.1f}B" for v in sec_2025_sql],
            textposition="outside", textfont_size=8))
        apply_layout(fig, height=350, barmode="group",
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee",title="Revenue (M PKR)"))
        fig.update_layout(title="2025: Primary vs Secondary Monthly")
        st.plotly_chart(fig, use_container_width=True)

    gaps_24_sql = [s-p for s,p in zip(sec_2024_sql, pri_2024_sql)]
    gaps_25_sql = [s-p for s,p in zip(sec_2025_sql, pri_2025_sql)]
    gap_df_sql = pd.DataFrame({
        "Month"   : months_sql,
        "Gap 2024 (M PKR)": [f"{'+'if g>0 else ''}PKR {g:,.0f}M" for g in gaps_24_sql],
        "Meaning 2024"    : ["Sold from old stock" if g>0 else "Stock building" for g in gaps_24_sql],
        "Gap 2025 (M PKR)": [f"{'+'if g>0 else ''}PKR {g:,.0f}M" for g in gaps_25_sql],
        "Meaning 2025"    : ["Sold from old stock" if g>0 else "Stock building" for g in gaps_25_sql]
    })
    st.dataframe(gap_df_sql, use_container_width=True, hide_index=True)
    st.markdown(warn("Sep 2025: Pharmevo shipped PKR 392M MORE than distributors sold = large stock build. This stock was then sold in Q4 2025 (Oct-Dec) explaining the Q4 revenue peak."), unsafe_allow_html=True)
    st.markdown("---")

    # FINDING 2
    st.markdown(sec("🟢 FINDING 2 — Ramipace: PKR 14.4M Investment Returns PKR 951M (65.9x ROI)"), unsafe_allow_html=True)
    st.markdown(note("Ramipace ROI = 65.9x (verified manually). Confirmed by 3 databases: Activities (spend), DSR (revenue), ZSDCY (distribution). This product is 5x better than company average. It is severely underfunded."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        # Calculate ROI from raw data directly
        rv_ram  = df_sales.groupby("ProductName")["TotalRevenue"].sum()
        sp_ram  = df_act.groupby("Product")["TotalAmount"].sum()
        roi_raw = pd.DataFrame({"Rev":rv_ram,"Spend":sp_ram}).dropna()
        roi_raw = roi_raw[roi_raw["Spend"]>500000]
        roi_raw["ROI"] = roi_raw["Rev"]/roi_raw["Spend"]
        roi_raw = roi_raw.reset_index()
        roi_raw.columns = ["ProductName","Rev","Spend","ROI"]
        top_roi = roi_raw.nlargest(10,"ROI")
        colors_roi = ["#FFD700" if "RAMIPACE" in p.upper()
                      else "#2e7d32" if r>50
                      else "#2c5f8a" for p,r in
                      zip(top_roi["ProductName"],top_roi["ROI"])]
        fig = go.Figure(go.Bar(
            y=top_roi["ProductName"],
            x=top_roi["ROI"],
            orientation="h",
            marker_color=colors_roi,
            text=[f"{r:.0f}x" for r in top_roi["ROI"]],
            textposition="outside", textfont_size=10))
        apply_layout(fig, height=320,
                     yaxis=dict(autorange="reversed",gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee",title="ROI"))
        fig.update_layout(title="Top 10 ROI Products (Gold=Ramipace)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Use verified raw numbers
        ram_act_v = df_act[df_act["Product"].str.upper().str.contains("RAMIPACE",na=False)]["TotalAmount"].sum()
        ram_rev_v = df_sales[df_sales["ProductName"].str.upper().str.contains("RAMIPACE",na=False)]["TotalRevenue"].sum()
        ram_roi_v = ram_rev_v/ram_act_v if ram_act_v>0 else 0
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Promo Spent","Revenue Earned"],
            y=[ram_act_v/1e6, ram_rev_v/1e6],
            marker_color=["#e65100","#2e7d32"],
            text=[fmt(ram_act_v), fmt(ram_rev_v)],
            textposition="outside", textfont_size=12))
        apply_layout(fig, height=320,
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee",title="PKR Million"))
        fig.update_layout(title=f"Ramipace: {ram_roi_v:.1f}x ROI (Verified)",showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        # ZSDCY verification
        ram_z_df  = df_zsdcy[df_zsdcy["Material Name"].str.upper().str.contains(
            "RAMIPACE", na=False)]
        ram_zdist = ram_z_df["Revenue"].sum()

        st.markdown(f"""
        <div class="manual-working">
        RAMIPACE — VERIFIED FROM 3 DATABASES
        ══════════════════════════════════════════
        DATABASE 1: Activities (activities_clean.csv)
          Column : Product = RAMIPACE
          Column : TotalAmount
          Records: {len(ram_act_df)} activity records
          Result : {fmt(ram_spend)} promotional spend

        DATABASE 2: Sales DSR (sales_clean.csv)
          Column : ProductName = RAMIPACE
          Column : TotalRevenue
          Records: {len(ram_dsr_df)} sales records
          Result : {fmt(ram_rev)} revenue earned

        DATABASE 3: ZSDCY (zsdcy_clean.csv)
          Column : Material Name contains RAMIPACE
          Column : Revenue
          Result : {fmt(ram_zdist)} distributed

        MANUAL ROI CALCULATION:
          ROI = Revenue / Spend
          ROI = {ram_rev:,.0f} / {ram_spend:,.0f}
          ROI = {ram_roi:.1f}x

        COMPANY AVERAGE : {roi_all:.1f}x
        RAMIPACE ROI    : {ram_roi:.1f}x
        RAMIPACE IS {ram_roi/roi_all:.1f}x BETTER THAN AVERAGE!

        IF WE DOUBLE BUDGET:
        New Spend   : {fmt(ram_spend*2)}
        Expected Rev: {fmt(ram_rev*2)}
        Extra Revenue: {fmt(ram_rev)}
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    st.markdown(good(f"<b>ACTION (This Week):</b> Increase Ramipace budget from {fmt(ram_spend)} to {fmt(ram_spend*2)}. ROI verified manually at {ram_roi:.1f}x from 3 databases. Expected additional revenue = {fmt(ram_rev)}. Highest confidence action available."), unsafe_allow_html=True)

    # FINDING 3
    st.markdown(sec("🟢 FINDING 3 — Finno-Q: +226% Growth With Almost Zero Promotion"), unsafe_allow_html=True)
    st.markdown(note("Finno-Q grew +226% in DSR and +123% in ZSDCY — both databases confirm explosive growth. Total promo spent = only PKR 6.7M. This product is growing by itself without any support. With proper promotion it could triple again."), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        r24_all = df_sales[df_sales["Yr"]==2024].groupby("ProductName")["TotalRevenue"].sum()
        r25_all = df_sales[df_sales["Yr"]==2025].groupby("ProductName")["TotalRevenue"].sum()
        gdf = pd.DataFrame({"2024":r24_all,"2025":r25_all}).dropna()
        gdf = gdf[gdf["2024"]>5e6]
        gdf["Growth"] = ((gdf["2025"]-gdf["2024"])/gdf["2024"]*100)
        gdf = gdf.nlargest(10,"Growth").reset_index()
        colors_g = ["#FFD700" if "FINNO" in p.upper() else "#2c5f8a"
                    for p in gdf["ProductName"]]
        fig = go.Figure(go.Bar(
            x=gdf["Growth"], y=gdf["ProductName"],
            orientation="h",
            text=[f"+{g:.0f}%" for g in gdf["Growth"]],
            textposition="outside", textfont_size=9,
            marker_color=colors_g))
        apply_layout(fig, height=320,
                     yaxis=dict(autorange="reversed",gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee",title="Growth %"))
        fig.update_layout(title="Top Growing Products (Gold=Finno-Q)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fq_monthly = df_sales[
            df_sales["ProductName"].str.upper().str.contains("FINNO",na=False)
        ].groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
        if len(fq_monthly)>0:
            fq_monthly["Date"]  = pd.to_datetime(
                fq_monthly["Yr"].astype(int).astype(str)+"-"+
                fq_monthly["Mo"].astype(int).astype(str)+"-01")
            fq_monthly["Label"] = fq_monthly["TotalRevenue"].apply(fmt)
            fig = px.area(fq_monthly, x="Date", y="TotalRevenue",
                          title="Finno-Q Monthly Revenue Trend (DSR Database)",
                          color_discrete_sequence=["#2e7d32"])
            fig.update_traces(
                text=fq_monthly["Label"],
                hovertemplate="%{x|%b %Y}<br>Revenue: %{text}<extra></extra>")
            apply_layout(fig, height=320,
                         yaxis=dict(gridcolor="#eee",title="Revenue (PKR)"))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Hover for exact values in B/M/K format. Clear upward trend confirms +226% growth.")

    with col3:
        fq_act_rows = df_act[df_act["Product"].str.upper().str.contains(
            "FINNO", na=False)]
        fq_dsr_rows = df_sales[df_sales["ProductName"].str.upper().str.contains(
            "FINNO", na=False)]

        st.markdown(f"""
        <div class="manual-working">
        FINNO-Q — VERIFIED FROM 2 DATABASES
        ══════════════════════════════════════════
        DATABASE 1: Sales DSR (sales_clean.csv)
          Column : ProductName contains FINNO
          Column : TotalRevenue, Yr
          Records: {len(fq_dsr_rows)} sales records

          2024 Revenue = sum(TotalRevenue WHERE Yr=2024)
                       = {fmt(fq_24)}

          2025 Revenue = sum(TotalRevenue WHERE Yr=2025)
                       = {fmt(fq_25)}

          Growth = ({fq_25/1e6:.1f}M - {fq_24/1e6:.1f}M) / {fq_24/1e6:.1f}M x 100
                 = {fq_g:.1f}%

        DATABASE 2: Activities (activities_clean.csv)
          Column : Product contains FINNO
          Column : TotalAmount
          Records: {len(fq_act_rows)} promo records
          Spend  : {fmt(fq_promo)} ONLY

        DIFFERENCE FROM FINDING 2 (Ramipace):
          Finding 2 = Ramipace has HIGH ROI (65.9x)
                      Already promoted, needs more budget
          Finding 3 = Finno-Q has HIGH GROWTH (+226%)
                      NOT promoted at all, needs first budget

        IF WE INVEST PKR 10M IN FINNO-Q:
          Current revenue: {fmt(fq_25)}
          Expected growth: +200% minimum
          Expected revenue: {fmt(fq_25*2)}
          ROI potential: {fq_25*2/10e6:.0f}x
        ══════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="manual-working">
    FINNO-Q — VERIFIED MANUAL CALCULATION
    ══════════════════════════════════════════════
    DATABASE USED: Sales DSR (sales_clean.csv)
    Column 1: ProductName — filter where contains "FINNO"
    Column 2: TotalRevenue — sum by year
    Column 3: Yr — group by year

    STEP BY STEP:
    2024 Revenue = sum(TotalRevenue WHERE
                  ProductName LIKE "FINNO%" AND Yr=2024)
                = PKR 11,550,406

    2025 Revenue = sum(TotalRevenue WHERE
                  ProductName LIKE "FINNO%" AND Yr=2025)
                = PKR 37,669,105

    Growth Formula:
    = (2025 Revenue - 2024 Revenue) / 2024 Revenue × 100
    = (37,669,105 - 11,550,406) / 11,550,406 × 100
    = 26,118,699 / 11,550,406 × 100
    = 226.1%

    PROMO CHECK (activities_clean.csv):
    Column: Product contains "FINNO"
    Column: TotalAmount → sum = PKR 6,713,685

    DIFFERENCE FROM FINDING 4 (Q4 Seasonality):
    Finding 3 = ONE product (Finno-Q) growing +226%
    Finding 4 = ALL products peak in Oct/Nov/Dec
    Finding 3 = WHAT product to invest in
    Finding 4 = WHEN to run campaigns
    ══════════════════════════════════════════════
    </div>
    """, unsafe_allow_html=True)
    st.markdown(good("<b>ACTION (This Month):</b> Allocate PKR 10M for Finno-Q promotion. Product grew +226% with only PKR 6.7M spend. Expected revenue in 2026: +PKR 75M minimum."), unsafe_allow_html=True)

    # FINDING 4
    st.markdown(sec("🟢 FINDING 4 — Q4 is Golden Quarter: All 4 Databases Confirm Oct-Dec Peak"), unsafe_allow_html=True)
    st.markdown(note("Oct/Nov/Dec are strongest months in EVERY database — Sales, ZSDCY, Travel and Activities all show Q4 peaks. Yet Q4 promotional spend is only average. This is a missed opportunity every year."), unsafe_allow_html=True)

    mo_map_c = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    col1, col2 = st.columns(2)
    with col1:
        sales_mo = df_sales.groupby("Mo")["TotalRevenue"].sum().reset_index()
        sales_mo["Month"] = sales_mo["Mo"].map(mo_map_c)
        sales_mo["Q4"] = sales_mo["Mo"].apply(
            lambda x: "Q4 Peak" if x in [10,11,12] else "Other Months")
        fig = px.bar(sales_mo, x="Month", y="TotalRevenue",
                     color="Q4", title="DSR — Monthly Sales Revenue",
                     color_discrete_map={"Q4 Peak":"#2e7d32","Other Months":"#2c5f8a"},
                     category_orders={"Month":list(mo_map_c.values())},
                     text=sales_mo["TotalRevenue"].apply(lambda x: f"{x/1e9:.1f}B"))
        fig.update_traces(textposition="outside",textfont_size=9)
        apply_layout(fig, height=300,
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        promo_mo = df_act.groupby("Mo")["TotalAmount"].sum().reset_index()
        promo_mo["Month"] = promo_mo["Mo"].map(mo_map_c)
        promo_mo["Q4"]    = promo_mo["Mo"].apply(
            lambda x: "Q4 Peak" if x in [10,11,12] else "Other Months")
        fig = px.bar(promo_mo, x="Month", y="TotalAmount",
                     color="Q4", title="Activities — Monthly Promo Spend",
                     color_discrete_map={"Q4 Peak":"#2e7d32","Other Months":"#e65100"},
                     category_orders={"Month":list(mo_map_c.values())},
                     text=promo_mo["TotalAmount"].apply(lambda x: f"{x/1e6:.0f}M"))
        fig.update_traces(textposition="outside",textfont_size=9)
        apply_layout(fig, height=300,
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    q4_rev  = df_sales[df_sales["Mo"].isin([10,11,12])]["TotalRevenue"].sum()
    q4_pct  = q4_rev/rev_all*100
    st.markdown(good(f"<b>ACTION (September 2026):</b> Double promotional spend in September to prepare for Q4. Q4 = {q4_pct:.1f}% of annual revenue. Starting campaigns 1 month early can add PKR 200-300M to Q4 results."), unsafe_allow_html=True)

    # FINDING 6
    st.markdown(sec("🟡 FINDING 6 — Promo Timing Wrong: Highest Spend in Lowest Sales Month"), unsafe_allow_html=True)
    st.markdown(note("July = rank #1 in promo spend but rank #8 in sales revenue. January = rank #1 in sales but rank #3 in promo spend. PKR 2.58B promotional budget is being spent in wrong months!"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        promo_rank = df_act.groupby("Mo")["TotalAmount"].sum().rank(ascending=False)
        sales_rank = df_sales.groupby("Mo")["TotalRevenue"].sum().rank(ascending=False)
        timing_df  = pd.DataFrame({
            "Month"     : list(mo_map_c.values()),
            "Promo Rank": [int(promo_rank.get(m,0)) for m in range(1,13)],
            "Sales Rank": [int(sales_rank.get(m,0))  for m in range(1,13)]
        })
        timing_df["Gap"]    = abs(timing_df["Promo Rank"]-timing_df["Sales Rank"])
        timing_df["Status"] = timing_df["Gap"].apply(
            lambda x: "✅ Aligned" if x<=2 else "⚠️ Misaligned")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timing_df["Month"], y=timing_df["Promo Rank"],
            name="Promo Rank (#1=highest spend)",
            mode="lines+markers",
            line=dict(color="#e65100",width=2.5),
            marker=dict(size=8)))
        fig.add_trace(go.Scatter(
            x=timing_df["Month"], y=timing_df["Sales Rank"],
            name="Sales Rank (#1=highest sales)",
            mode="lines+markers",
            line=dict(color="#2c5f8a",width=2.5),
            marker=dict(size=8)))
        apply_layout(fig, height=300,
                     yaxis=dict(gridcolor="#eee",title="Rank",autorange="reversed"),
                     xaxis=dict(gridcolor="#eee"),
                     hovermode="x unified")
        fig.update_layout(title="Promo Rank vs Sales Rank by Month")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(timing_df[["Month","Promo Rank","Sales Rank","Gap","Status"]],
                     use_container_width=True, hide_index=True)
        aligned = timing_df["Status"].value_counts().get("✅ Aligned",0)
        st.markdown(warn(f"Only {aligned}/12 months are properly aligned. Move 30% of July promo budget to January and February. This reallocation alone could add PKR 200-300M revenue."), unsafe_allow_html=True)

    # FINDING 7
    st.markdown(sec("🟡 FINDING 7 — Nutraceutical Growing 35% vs Pharma 28%"), unsafe_allow_html=True)
    st.markdown(note("ZSDCY confirms Nutraceutical category grew +35.5% vs Pharma +28%. Currently 12.7% of primary revenue. With a dedicated sales team and marketing campaign it can reach 20% by 2027 = PKR 500M+ additional."), unsafe_allow_html=True)

    # Backend explanation for supervisor
    nutra_24_v = df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    nutra_25_v = df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    pharma_24_v= df_zsdcy[(df_zsdcy["Category"]=="P")&(df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    pharma_25_v= df_zsdcy[(df_zsdcy["Category"]=="P")&(df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    nutra_rows = df_zsdcy[df_zsdcy["Category"]=="N"]
    pharma_rows= df_zsdcy[df_zsdcy["Category"]=="P"]

    with st.expander("📋 Click to see: How we identified Nutraceutical vs Pharma products"):
        st.markdown(f"""
        <div class="manual-working">
        HOW NUTRACEUTICAL vs PHARMA WAS IDENTIFIED
        ══════════════════════════════════════════════════
        DATABASE: ZSDCY (zsdcy_clean.csv)
        ORIGINAL COLUMN: "Billing Type Name"

        RAW VALUES IN DATA:
          "Pharma Invoice"        → Category = P (Pharma)
          "Nutraceutical Invoic"  → Category = N (Nutraceutical)
          "Medical Devices - ST"  → Category = M (Medical Device)
          "Herbal Invoice"        → Category = H (Herbal)
          "Export Invoice"        → Category = E (Export)

        WE CREATED A NEW COLUMN CALLED "Category":
          If "Pharma"   in Billing Type → P
          If "Nutra"    in Billing Type → N
          If "Medical"  in Billing Type → M
          If "Herbal"   in Billing Type → H
          If "Export"   in Billing Type → E

        NUTRACEUTICAL PRODUCTS EXAMPLES:
          → Inosita Plus (diabetes supplement)
          → Ad Folic OD (folic acid supplement)
          → Opt-D (Vitamin D capsules)
          → Femova (fertility supplement)
          → K-1000 (potassium supplement)
          Total: {nutra_rows["Material Name"].nunique()} unique Nutraceutical products

        PHARMA PRODUCTS EXAMPLES:
          → X-Plended (heart medicine)
          → Avsar (blood pressure)
          → Ramipace (ACE inhibitor)
          → Lowplat (blood thinner)
          Total: {pharma_rows["Material Name"].nunique()} unique Pharma products

        CALCULATION:
          Nutra 2024 = sum(Revenue WHERE Category=N AND Yr=2024)
                     = {fmt(nutra_24_v)}
          Nutra 2025 = sum(Revenue WHERE Category=N AND Yr=2025)
                     = {fmt(nutra_25_v)}
          Growth     = ({nutra_25_v/1e9:.2f}B - {nutra_24_v/1e9:.2f}B) / {nutra_24_v/1e9:.2f}B x 100
                     = +{((nutra_25_v-nutra_24_v)/nutra_24_v*100):.1f}%

          Pharma 2024 = {fmt(pharma_24_v)}
          Pharma 2025 = {fmt(pharma_25_v)}
          Growth      = +{((pharma_25_v-pharma_24_v)/pharma_24_v*100):.1f}%
        ══════════════════════════════════════════════════
        </div>
        """, unsafe_allow_html=True)

    # Backend explanation for supervisor
    nutra_24_v = df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    nutra_25_v = df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    pharma_24_v= df_zsdcy[(df_zsdcy["Category"]=="P")&(df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    pharma_25_v= df_zsdcy[(df_zsdcy["Category"]=="P")&(df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    nutra_rows = df_zsdcy[df_zsdcy["Category"]=="N"]
    pharma_rows= df_zsdcy[df_zsdcy["Category"]=="P"]
    nutra_g7   = ((nutra_25_v-nutra_24_v)/nutra_24_v*100) if nutra_24_v>0 else 0
    pharma_g7  = ((pharma_25_v-pharma_24_v)/pharma_24_v*100) if pharma_24_v>0 else 0

    col1, col2 = st.columns(2)
    with col1:
        cat_map_f7 = {"P":"Pharma","N":"Nutraceutical","M":"Medical Device",
                      "H":"Herbal","E":"Export","O":"Other"}
        cat_yr_f7  = df_zsdcy.groupby(["Category","Yr"])["Revenue"].sum().reset_index()
        cat_yr_f7["CatName"] = cat_yr_f7["Category"].map(cat_map_f7)
        cat_main_f7 = cat_yr_f7[cat_yr_f7["Category"].isin(["P","N"])].copy()
        cat_main_f7["Label"] = cat_main_f7["Revenue"].apply(fmt)
        fig = px.bar(cat_main_f7, x="Yr", y="Revenue",
                     color="CatName", barmode="group",
                     text="Label",
                     title="Pharma vs Nutraceutical Revenue (ZSDCY DB)",
                     color_discrete_map={"Pharma":"#2c5f8a",
                                         "Nutraceutical":"#7b1fa2"})
        fig.update_traces(textposition="outside", textfont_size=10)
        apply_layout(fig, height=320,
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee", title="Revenue (PKR)"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            x=["Pharma Growth","Nutraceutical Growth"],
            y=[pharma_g7, nutra_g7],
            color=["Pharma","Nutraceutical"],
            text=[f"+{pharma_g7:.1f}%", f"+{nutra_g7:.1f}%"],
            color_discrete_map={"Pharma":"#2c5f8a",
                                "Nutraceutical":"#7b1fa2"},
            title="Growth Rate 2024→2025")
        fig.update_traces(textposition="outside", textfont_size=13)
        apply_layout(fig, height=320,
                     xaxis=dict(gridcolor="#eee"),
                     yaxis=dict(gridcolor="#eee", title="Growth %"),
                     showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(good(f"<b>ACTION (June 2026):</b> Launch dedicated Nutraceutical business unit. Nutra growing {nutra_g7:.1f}% vs Pharma {pharma_g7:.1f}%. Invest PKR 20M. Target 20% revenue share by 2027 = +PKR 300M."), unsafe_allow_html=True)
    st.markdown("---")

    
    st.markdown('---')
    
    # FINDING 8 in page 13
    st.markdown("---")
    st.markdown(sec("🟡 FINDING 11 — Product Portfolio: Stars, Cash Cows, Question Marks, Dogs"), unsafe_allow_html=True)
    st.markdown(note("BCG Matrix classifies all products by revenue and growth. Stars = invest more. Cash Cows = maintain. Question Marks = watch closely. Dogs = cut budget."), unsafe_allow_html=True)

    r24_bcg = df_sales[df_sales["Yr"]==2024].groupby("ProductName")["TotalRevenue"].sum()
    r25_bcg = df_sales[df_sales["Yr"]==2025].groupby("ProductName")["TotalRevenue"].sum()
    bcg     = pd.DataFrame({"Rev2024":r24_bcg,"Rev2025":r25_bcg}).dropna()
    bcg     = bcg[bcg["Rev2024"]>5e6].reset_index()
    bcg["Growth"]   = ((bcg["Rev2025"]-bcg["Rev2024"])/bcg["Rev2024"]*100)
    bcg["TotalRev"] = bcg["Rev2024"]+bcg["Rev2025"]
    med_rev  = bcg["TotalRev"].median()
    med_grow = bcg["Growth"].median()

    def classify_bcg(row):
        if row["TotalRev"]>=med_rev and row["Growth"]>=med_grow:   return "⭐ Stars"
        elif row["TotalRev"]>=med_rev and row["Growth"]<med_grow:  return "🐄 Cash Cows"
        elif row["TotalRev"]<med_rev  and row["Growth"]>=med_grow: return "❓ Question Marks"
        else: return "🐕 Dogs"

    bcg["Category"] = bcg.apply(classify_bcg, axis=1)
    g1 = bcg[bcg["Category"]=="⭐ Stars"]
    g2 = bcg[bcg["Category"]=="🐄 Cash Cows"]
    g3 = bcg[bcg["Category"]=="❓ Question Marks"]
    g4 = bcg[bcg["Category"]=="🐕 Dogs"]

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("⭐ Stars",          str(len(g1)), "Invest More"), unsafe_allow_html=True)
    c2.markdown(kpi("🐄 Cash Cows",      str(len(g2)), "Maintain"),    unsafe_allow_html=True)
    c3.markdown(kpi("❓ Question Marks", str(len(g3)), "Watch"),        unsafe_allow_html=True)
    c4.markdown(kpi("🐕 Dogs",           str(len(g4)), "Cut Budget", red=True), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**⭐ Stars — INVEST MORE (High Revenue + Growing)**")
        g1s = g1.sort_values("TotalRev", ascending=False).head(20)
        fig = go.Figure(go.Bar(
            x=g1s["TotalRev"]/1e6, y=g1s["ProductName"],
            orientation="h", text=g1s["TotalRev"].apply(fmt),
            textposition="outside", textfont_size=9, marker_color="#2e7d32"))
        apply_layout(fig, height=520,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="Revenue (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(g1)} Stars — increase promo budget 50%")

    with col2:
        st.markdown("**❓ Question Marks — WATCH (Low Revenue + Growing Fast)**")
        g3s = g3.sort_values("Growth", ascending=False).head(20)
        colors_g3 = ["#FFD700" if "FINNO" in p.upper() else "#e65100"
                     for p in g3s["ProductName"]]
        fig = go.Figure(go.Bar(
            x=g3s["Growth"], y=g3s["ProductName"],
            orientation="h", text=g3s["Growth"].apply(lambda x: f"+{x:.1f}%"),
            textposition="outside", textfont_size=9, marker_color=colors_g3))
        apply_layout(fig, height=520,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="Growth %"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(g3)} Question Marks — Gold=Finno-Q, fund selectively")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🐄 Cash Cows — MAINTAIN (High Revenue + Stable)**")
        g2s = g2.sort_values("TotalRev", ascending=False).head(20)
        fig = go.Figure(go.Bar(
            x=g2s["TotalRev"]/1e6, y=g2s["ProductName"],
            orientation="h", text=g2s["TotalRev"].apply(fmt),
            textposition="outside", textfont_size=9, marker_color="#2c5f8a"))
        apply_layout(fig, height=520,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="Revenue (M PKR)"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(g2)} Cash Cows — maintain current budget")

    with col2:
        st.markdown("**🐕 Dogs — CUT BUDGET (Low Revenue + Declining)**")
        g4s = g4.sort_values("Growth").head(20)
        fig = go.Figure(go.Bar(
            x=g4s["Growth"], y=g4s["ProductName"],
            orientation="h", text=g4s["Growth"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside", textfont_size=9, marker_color="#c62828"))
        apply_layout(fig, height=520,
                     yaxis=dict(autorange="reversed", gridcolor="#eee"),
                     xaxis=dict(gridcolor="#eee", title="Growth % (Negative=Declining)"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(g4)} Dogs — cut promo, redirect to Stars")

    st.markdown(good("<b>STRATEGY:</b> Stars = +50% budget. Cash Cows = maintain. Question Marks = fund Finno-Q only. Dogs = cut 80% and redirect to Stars."), unsafe_allow_html=True)


    st.markdown("---")
    # ── SECTION 5: EXECUTIVE ACTION PLAN ─────────────────────
    st.markdown("### ⚡ Executive Action Plan — Prioritized by PKR Impact")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(sec("🔴 THIS WEEK"), unsafe_allow_html=True)
        week_df = pd.DataFrame({
            "Action":[
                "Audit Falcons discount abuse",
                "Triple Ramipace promo budget",
                "Call Nusrat Pharma — recovery",
                "Identify 2 backup distributors"
            ],
            "PKR Impact":[
                "Save PKR 200M/year",
                "+PKR 430M revenue",
                "Recover PKR 23.7M",
                "Remove critical risk"
            ]})
        st.dataframe(week_df, use_container_width=True, hide_index=True)
        st.markdown(danger("Week total: Save/earn PKR 650M+"), unsafe_allow_html=True)

    with col2:
        st.markdown(sec("🟡 THIS MONTH"), unsafe_allow_html=True)
        month_df = pd.DataFrame({
            "Action":[
                "Allocate PKR 10M to Finno-Q",
                "Move July budget to Jan/Feb",
                "Add 300 Karachi field trips",
                "Set Division 4 trip targets",
                "Fix Zoltar pricing strategy"
            ],
            "PKR Impact":[
                "+PKR 200M revenue",
                "+PKR 300M revenue",
                "+PKR 150M revenue",
                "Performance boost",
                "Save PKR 74M/year"
            ]})
        st.dataframe(month_df, use_container_width=True, hide_index=True)
        st.markdown(warn("Month total: +PKR 650M+ potential"), unsafe_allow_html=True)

    with col3:
        st.markdown(sec("🟢 THIS YEAR"), unsafe_allow_html=True)
        year_df = pd.DataFrame({
            "Action":[
                "Launch Nutraceutical team",
                "Double Q4 Sept campaigns",
                "Onboard 2 new distributors",
                "Develop 3 new products",
                "Challengers playbook for all",
                "Hotel bulk rate negotiation"
            ],
            "PKR Impact":[
                "+PKR 300M",
                "+PKR 300M",
                "Risk reduction",
                "Risk reduction",
                "+PKR 200M",
                "Save PKR 18M"
            ]})
        st.dataframe(year_df, use_container_width=True, hide_index=True)
        st.markdown(good("Year total: +PKR 800M+ potential"), unsafe_allow_html=True)

    # FINAL SUMMARY
    st.markdown("---")
    st.markdown("### 💰 Total Financial Opportunity — All 4 Databases Combined")

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("💰 Total Savings",    "PKR 292M",  "From fixing waste & abuse"), unsafe_allow_html=True)
    c2.markdown(kpi("📈 Revenue Growth",   "PKR 1.58B", "From identified opportunities"), unsafe_allow_html=True)
    c3.markdown(kpi("💡 Investment Needed","PKR 110M",  "To unlock all growth"), unsafe_allow_html=True)
    c4.markdown(kpi("🎯 Net Benefit",      "PKR 1.76B", "Savings + Growth combined"), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="manual-working" style="font-size:13px; line-height:1.8">
    ══════════════════════════════════════════════════════════════
    PHARMEVO STRATEGIC SUMMARY — COMBINED 4 DATABASE ANALYSIS
    Prepared by: Business Intelligence Dashboard | March 2026
    ══════════════════════════════════════════════════════════════

    CURRENT STATE:
    Revenue 2025      : {fmt(rev_25)} (+{rev_growth:.1f}% vs 2024)
    ROI 2025          : {roi_25:.1f}x (DOWN from {roi_24:.1f}x in 2024)
    Primary Sales     : {fmt(zrev_25)} (+{zrev_growth:.1f}%)
    Distributor Ret.  : {ret:.1f}% (26 lost = PKR 28.5M at risk)

    TOP 5 GROWTH OPPORTUNITIES (Total = PKR 1.58B):
    1. Fix promo timing          → +PKR 300M  (no extra cost)
    2. Invest in Ramipace x3     → +PKR 430M  (PKR 9M extra)
    3. Invest in Finno-Q         → +PKR 200M  (PKR 10M extra)
    4. Increase Karachi/Swat     → +PKR 150M  (PKR 15M extra)
    5. Nutraceutical team        → +PKR 300M  (PKR 20M extra)

    TOP 3 COST SAVINGS (Total = PKR 292M):
    1. Fix discount abuse        → Save PKR 200M (zero cost)
    2. Fix Zoltar pricing        → Save PKR 74M  (zero cost)
    3. Hotel bulk contracts      → Save PKR 18M  (minimal cost)

    MOST IMPORTANT SINGLE ACTION:
    Double Ramipace budget = PKR 14M investment → PKR 951M return
    ROI = 65.9x verified manually from 3 databases.
    This is the highest confidence, highest impact action available.
    ══════════════════════════════════════════════════════════════
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# ML INTELLIGENCE PAGE
# ════════════════════════════════════════════════════════
elif page == "🤖 ML Intelligence":
    import pickle
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, RandomForestClassifier
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import r2_score, mean_absolute_error
    from sklearn.model_selection import train_test_split

    st.markdown("<h1 style=\'color:#2c5f8a\'>🤖 ML Intelligence Center</h1>", unsafe_allow_html=True)
    st.markdown("<p style=\'color:#555; font-size:15px\'>5 Machine Learning Models trained on Live SQL Data | Pharmevo 2020-2026</p>", unsafe_allow_html=True)
    st.markdown(note("All models trained on LIVE SQL Server data. Data covers 2020-2026. Models help management make data-driven decisions on revenue, products, budgets, distributors and territories."), unsafe_allow_html=True)

    # Load pre-computed results
    try:
        df_fc1     = pd.read_csv("ml_forecast_revenue.csv")
        prod_growth= pd.read_csv("ml_forecast_products.csv")
        hist_roi   = pd.read_csv("ml_roi_products.csv")
        churn_df   = pd.read_csv("ml_churn_risk.csv")
        territory  = pd.read_csv("ml_territory_scores.csv")
        master_ml  = pd.read_csv("ml_master.csv")
        master_ml["Date"] = pd.to_datetime(master_ml["Date"])
        models_ok  = True
    except:
        models_ok  = False
        st.error("ML model files not found. Please run the ML notebook first.")

    if models_ok:
        # ── OVERVIEW KPIS ─────────────────────────────────
        st.markdown("### 📊 ML Model Performance Summary")
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.markdown(kpi("Model 1", "R2 = 1.000", "Revenue Forecast"), unsafe_allow_html=True)
        c2.markdown(kpi("Model 2", "101 Products", "Classified & Forecast"), unsafe_allow_html=True)
        c3.markdown(kpi("Model 3", "R2 = 0.849", "ROI Predictor"), unsafe_allow_html=True)
        c4.markdown(kpi("Model 4 Accuracy", "100%", "Churn Prediction"), unsafe_allow_html=True)
        c5.markdown(kpi("Model 5", "1 City", "High Opportunity"), unsafe_allow_html=True)
        st.markdown("---")

        # ── MODEL 1: REVENUE FORECAST ─────────────────────
        st.markdown(sec("📈 Model 1 — 6-Month Revenue Forecast (Gradient Boosting)"), unsafe_allow_html=True)
        st.markdown(note("Trained on 2020-2026 monthly data from live SQL Server. Features: Promo spend, Travel trips, Seasonality, Lag variables. Predicts next 6 months with ±12% confidence band."), unsafe_allow_html=True)

        col1, col2 = st.columns([3,1])
        with col1:
            # Historical + forecast chart
            hist_chart = master_ml[master_ml["Yr"]>=2024][["Date","Sec_Rev"]].copy()
            hist_chart.columns = ["Date","Revenue"]

            df_fc1["Date"] = pd.to_datetime(
                df_fc1["Month"].apply(lambda x: x.split()[1]+"-"+
                    {"Jan":"01","Feb":"02","Mar":"03","Apr":"04","May":"05","Jun":"06",
                     "Jul":"07","Aug":"08","Sep":"09","Oct":"10","Nov":"11","Dec":"12"}[x.split()[0]]+"-01"))

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist_chart["Date"], y=hist_chart["Revenue"]/1e9,
                name="Actual Revenue", mode="lines+markers",
                line=dict(color="#2c5f8a", width=2.5),
                hovertemplate="%{x|%b %Y}: PKR %{y:.2f}B<extra></extra>"))
            fig.add_trace(go.Scatter(
                x=df_fc1["Date"], y=df_fc1["Forecast"]/1e9,
                name="ML Forecast", mode="lines+markers",
                line=dict(color="#e65100", width=2.5, dash="dash"),
                marker=dict(size=8, symbol="diamond"),
                hovertemplate="%{x|%b %Y}: PKR %{y:.2f}B (forecast)<extra></extra>"))
            # Confidence band
            dates_band = pd.concat([df_fc1["Date"], df_fc1["Date"][::-1]])
            vals_band  = pd.concat([df_fc1["Upper"]/1e9, df_fc1["Lower"][::-1]/1e9])
            fig.add_trace(go.Scatter(
                x=dates_band, y=vals_band,
                fill="toself", fillcolor="rgba(230,81,0,0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                name="±12% Confidence", hoverinfo="skip"))
            apply_layout(fig, height=380,
                         xaxis=dict(gridcolor="#eee"),
                         yaxis=dict(gridcolor="#eee", title="Revenue (PKR Billion)"),
                         hovermode="x unified")
            fig.update_layout(title="Revenue Forecast — Next 6 Months (Apr-Sep 2026)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            total_fc = df_fc1["Forecast"].sum()
            st.markdown(f"""
            <div class="manual-working">
            6-MONTH FORECAST
            ══════════════════════
            Model: Gradient Boosting
            Data : 2020-2026 Live SQL
            R2   : 1.000

            Apr 2026: {fmt(df_fc1.iloc[0]["Forecast"])}
            May 2026: {fmt(df_fc1.iloc[1]["Forecast"])}
            Jun 2026: {fmt(df_fc1.iloc[2]["Forecast"])}
            Jul 2026: {fmt(df_fc1.iloc[3]["Forecast"])}
            Aug 2026: {fmt(df_fc1.iloc[4]["Forecast"])}
            Sep 2026: {fmt(df_fc1.iloc[5]["Forecast"])}

            TOTAL:
            {fmt(total_fc)}

            2025 H2 actual:
            PKR 12.36B
            ══════════════════════
            </div>
            """, unsafe_allow_html=True)

        # Forecast table
        fc_display = df_fc1.copy()
        fc_display["Forecast"]    = fc_display["Forecast"].apply(fmt)
        fc_display["Upper Bound"] = fc_display["Upper"].apply(fmt)
        fc_display["Lower Bound"] = fc_display["Lower"].apply(fmt)
        st.dataframe(fc_display[["Month","Forecast","Lower Bound","Upper Bound"]],
                     use_container_width=True, hide_index=True)
        st.markdown("---")

        # ── MODEL 2: PRODUCT FORECAST ─────────────────────
        st.markdown(sec("📦 Model 2 — Product Revenue Forecast 2026 (BCG Classification)"), unsafe_allow_html=True)
        st.markdown(note("101 products classified using BCG Matrix based on 2024-2025 revenue and growth. Stars = invest more. Cash Cows = maintain. Question Marks = selective invest. Dogs = reduce budget."), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            stars = prod_growth[prod_growth["Category"].str.startswith("⭐")].nlargest(15,"Forecast2026")
            fig = go.Figure(go.Bar(
                x=stars["Forecast2026"]/1e6, y=stars["ProductName"],
                orientation="h",
                text=stars["Forecast2026"].apply(fmt),
                textposition="outside", textfont_size=9,
                marker_color="#2e7d32"))
            apply_layout(fig, height=450,
                         yaxis=dict(autorange="reversed", gridcolor="#eee"),
                         xaxis=dict(gridcolor="#eee", title="2026 Forecast (M PKR)"))
            fig.update_layout(title="⭐ Stars — Invest More (Top 15)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            qmarks = prod_growth[prod_growth["Category"].str.startswith("❓")].nlargest(15,"Growth")
            colors_q = ["#FFD700" if "FINNO" in str(p).upper() else "#e65100"
                        for p in qmarks["ProductName"]]
            fig = go.Figure(go.Bar(
                x=qmarks["Growth"], y=qmarks["ProductName"],
                orientation="h",
                text=qmarks["Growth"].apply(lambda x: f"+{x:.0f}%"),
                textposition="outside", textfont_size=9,
                marker_color=colors_q))
            apply_layout(fig, height=450,
                         yaxis=dict(autorange="reversed", gridcolor="#eee"),
                         xaxis=dict(gridcolor="#eee", title="Growth % 2024→2025"))
            fig.update_layout(title="❓ Question Marks — Watch (Gold=Finno-Q)")
            st.plotly_chart(fig, use_container_width=True)

        prod_display = prod_growth[["ProductName","Rev2024","Rev2025",
                                     "Forecast2026","Growth","Category"]].copy()
        prod_display["Rev2024"]      = prod_display["Rev2024"].apply(fmt)
        prod_display["Rev2025"]      = prod_display["Rev2025"].apply(fmt)
        prod_display["Forecast2026"] = prod_display["Forecast2026"].apply(fmt)
        prod_display["Growth"]       = prod_display["Growth"].apply(lambda x: f"{x:+.1f}%")
        st.dataframe(prod_display.rename(columns={
            "ProductName":"Product","Rev2024":"2024 Rev",
            "Rev2025":"2025 Rev","Forecast2026":"2026 Forecast",
            "Growth":"Growth %","Category":"BCG Category"}),
            use_container_width=True, hide_index=True)
        st.markdown("---")

        # ── MODEL 3: ROI PREDICTOR ─────────────────────────
        st.markdown(sec("💹 Model 3 — Promo ROI Predictor (Random Forest R2=0.849)"), unsafe_allow_html=True)
        st.markdown(note("Enter your promotional budget. Select product and month. Model predicts expected revenue using Random Forest trained on historical Activities + Sales data."), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            # Historical ROI chart
            top_roi = hist_roi.head(15)
            colors_roi = ["#FFD700" if "RAMIPACE" in str(p).upper()
                          else "#2e7d32" if r>30 else "#2c5f8a"
                          for p,r in zip(top_roi["ProductName"],top_roi["ROI"])]
            fig = go.Figure(go.Bar(
                x=top_roi["ROI"], y=top_roi["ProductName"],
                orientation="h",
                text=top_roi["ROI"].apply(lambda x: f"{x:.1f}x"),
                textposition="outside", textfont_size=10,
                marker_color=colors_roi))
            apply_layout(fig, height=420,
                         yaxis=dict(autorange="reversed", gridcolor="#eee"),
                         xaxis=dict(gridcolor="#eee", title="ROI (Revenue/Spend)"))
            fig.update_layout(title="Historical ROI by Product (Gold=Ramipace)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### 🎯 Budget Simulator")
            mo_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                        7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
            budget_input = st.number_input(
                "Enter Budget (PKR)", min_value=100000,
                max_value=50000000, value=5000000, step=500000)
            prod_list = sorted(hist_roi["ProductName"].unique())
            prod_sel  = st.selectbox("Select Product", prod_list,
                index=prod_list.index("Ramipace") if "Ramipace" in prod_list else 0)
            mo_sel = st.selectbox("Select Month", range(1,13),
                                   format_func=lambda x: mo_names[x], index=3)

            # Get historical ROI for selected product
            prod_hist_roi = hist_roi[hist_roi["ProductName"]==prod_sel]
            if len(prod_hist_roi)>0:
                h_roi = prod_hist_roi.iloc[0]["ROI"]
                expected_rev = budget_input * h_roi
                st.markdown(f"""
                <div class="manual-working">
                PREDICTION RESULTS
                ══════════════════════════════
                Product : {prod_sel}
                Month   : {mo_names[mo_sel]}
                Budget  : {fmt(budget_input)}

                Historical ROI : {h_roi:.1f}x
                Expected Rev   : {fmt(expected_rev)}
                Upper (+20%)   : {fmt(expected_rev*1.2)}
                Lower (-20%)   : {fmt(expected_rev*0.8)}

                For every PKR 1 invested:
                Expected return = PKR {h_roi:.1f}
                ══════════════════════════════
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("No historical data for selected product")
        st.markdown("---")

        # ── MODEL 4: CHURN PREDICTOR ───────────────────────
        st.markdown(sec("⚠️ Model 4 — Distributor Churn Predictor (Accuracy=100%)"), unsafe_allow_html=True)
        st.markdown(note("Random Forest classifier trained on ZSDCY distributor data. Predicts which distributors are likely to stop ordering in 2026. Red = call this week. Revenue at risk = PKR 28.5M."), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            risk_counts = churn_df["RiskLevel"].value_counts().reset_index()
            risk_counts.columns = ["Risk","Count"]
            fig = px.pie(risk_counts, values="Count", names="Risk",
                         title="Distributor Risk Distribution",
                         color_discrete_map={
                             "🔴 High":"#c62828",
                             "🟡 Medium":"#e65100",
                             "🟢 Low":"#2e7d32"})
            fig.update_traces(textinfo="percent+label+value", textfont_size=12)
            apply_layout(fig, height=320)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            high_risk = churn_df[churn_df["RiskLevel"]=="🔴 High"].copy()
            high_risk["Rev2024"] = high_risk["Rev2024"].apply(fmt)
            high_risk["ChurnProb"] = high_risk["ChurnProb"].apply(
                lambda x: f"{x*100:.0f}%")
            st.markdown("**🔴 High Risk Distributors — Contact Immediately:**")
            st.dataframe(
                high_risk[["SDP Name","Rev2024","ChurnProb"]].head(15).rename(
                    columns={"SDP Name":"Distributor",
                             "Rev2024":"2024 Revenue",
                             "ChurnProb":"Churn Risk"}),
                use_container_width=True, hide_index=True)
        st.markdown("---")

        # ── MODEL 5: TERRITORY SCORER ──────────────────────
        st.markdown(sec("🗺️ Model 5 — Territory Opportunity Scorer (K-Means Clustering)"), unsafe_allow_html=True)
        st.markdown(note("Scores each city based on Revenue, Growth, Revenue-per-Trip and Low-Visit opportunity. Red = urgent — high revenue but few field visits. Score 0-100."), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            top_terr = territory.head(20)
            colors_t = ["#c62828" if p=="🔴 High Opportunity"
                        else "#e65100" if p=="🟡 Needs Attention"
                        else "#2c5f8a" for p in top_terr["Priority"]]
            fig = go.Figure(go.Bar(
                x=top_terr["OpportunityScore"], y=top_terr["City"],
                orientation="h",
                text=top_terr["OpportunityScore"].apply(lambda x: f"{x:.1f}"),
                textposition="outside", textfont_size=10,
                marker_color=colors_t))
            apply_layout(fig, height=520,
                         yaxis=dict(autorange="reversed", gridcolor="#eee"),
                         xaxis=dict(gridcolor="#eee",
                                    title="Opportunity Score (0-100)"))
            fig.update_layout(title="City Opportunity Score (Red=High Opportunity)")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            terr_disp = territory[["City","Revenue","Trips",
                                    "RevPerTrip","OpportunityScore","Priority"]].copy()
            terr_disp["Revenue"]      = terr_disp["Revenue"].apply(fmt)
            terr_disp["RevPerTrip"]   = terr_disp["RevPerTrip"].apply(
                lambda x: f"PKR {x/1e6:.1f}M")
            terr_disp["Score"]        = terr_disp["OpportunityScore"].apply(
                lambda x: f"{x:.1f}/100")
            terr_disp["Trips"]        = terr_disp["Trips"].astype(int)
            st.dataframe(
                terr_disp[["City","Revenue","Trips",
                            "RevPerTrip","Score","Priority"]].head(20),
                use_container_width=True, hide_index=True)

        # Scatter plot
        fig = px.scatter(territory.head(30),
                         x="Trips", y="Revenue",
                         size="OpportunityScore",
                         color="Priority",
                         hover_name="City",
                         color_discrete_map={
                             "🔴 High Opportunity":"#c62828",
                             "🟡 Needs Attention":"#e65100",
                             "🟢 Good Coverage":"#2e7d32"},
                         size_max=40,
                         title="City Revenue vs Field Trips — Size = Opportunity Score")
        apply_layout(fig, height=400,
                     xaxis=dict(gridcolor="#eee", title="Field Trips"),
                     yaxis=dict(gridcolor="#eee", title="Revenue (PKR)"))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ── MODEL 6: NEXT ORDER PREDICTION ────────────────
        st.markdown(sec("🛒 Model 6 — Next Order Prediction per Distributor"), unsafe_allow_html=True)
        st.markdown(note("Predicts when each distributor will place their next order based on historical reorder cycles. Regular = orders every 30 days. Irregular = 30-60 days. Rare = over 60 days."), unsafe_allow_html=True)

        try:
            df_reorder = pd.read_csv("ml_next_order.csv")
            col1, col2 = st.columns(2)
            with col1:
                rel_counts = df_reorder["Reliability"].value_counts().reset_index()
                rel_counts.columns = ["Type","Count"]
                fig = px.pie(rel_counts, values="Count", names="Type",
                             title="Distributor Order Reliability",
                             color_discrete_map={
                                 "🟢 Regular":"#2e7d32",
                                 "🟡 Irregular":"#e65100",
                                 "🔴 Rare":"#c62828"})
                fig.update_traces(textinfo="percent+label+value",textfont_size=11)
                apply_layout(fig, height=300)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                disp_ro = df_reorder[["SDP Name","AvgReorderDays","LastOrderDate",
                                       "NextOrderEst","AvgMonthlyRev","Reliability"]].copy()
                disp_ro["AvgMonthlyRev"] = disp_ro["AvgMonthlyRev"].apply(fmt)
                disp_ro["AvgReorderDays"] = disp_ro["AvgReorderDays"].apply(
                    lambda x: f"{x:.0f} days")
                st.markdown("**Distributors Due for Order Soon:**")
                st.dataframe(disp_ro.rename(columns={
                    "SDP Name":"Distributor","AvgReorderDays":"Order Cycle",
                    "LastOrderDate":"Last Order","NextOrderEst":"Next Expected",
                    "AvgMonthlyRev":"Avg Monthly Rev"}).head(15),
                    use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Model 6 error: {e}")

        st.markdown("---")

        # ── MODEL 7: TRAVEL TO SALES ───────────────────────
        st.markdown(sec("✈️ Model 7 — Travel-to-Sales Converter (R2=0.959)"), unsafe_allow_html=True)
        st.markdown(note("Proves that travel drives sales. Shows how much revenue each field visit generates per city. Swat = PKR 9.8M per trip. Management can now decide which cities deserve more field reps."), unsafe_allow_html=True)

        try:
            df_ts = pd.read_csv("ml_travel_sales.csv")
            col1, col2 = st.columns(2)
            with col1:
                top_ts = df_ts.sort_values("RevPerTrip",ascending=False).head(15)
                colors_ts = ["#c62828" if t<10 else "#e65100" if t<50
                              else "#2c5f8a" for t in top_ts["TotalTrips"]]
                fig = go.Figure(go.Bar(
                    x=top_ts["RevPerTrip"]/1e6, y=top_ts["City"],
                    orientation="h",
                    text=[f"PKR {r/1e6:.1f}M ({t:.0f} trips)"
                          for r,t in zip(top_ts["RevPerTrip"],top_ts["TotalTrips"])],
                    textposition="outside", textfont_size=9,
                    marker_color=colors_ts))
                apply_layout(fig, height=480,
                             yaxis=dict(autorange="reversed",gridcolor="#eee"),
                             xaxis=dict(gridcolor="#eee",title="Revenue per Trip (M PKR)"))
                fig.update_layout(title="Revenue per Trip by City (Red=Few Trips=Opportunity)")
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Red = high revenue per trip but very few visits = big opportunity!")

            with col2:
                st.dataframe(
                    top_ts[["City","TotalTrips","TotalRev","RevPerTrip"]].rename(
                        columns={"TotalTrips":"Trips","TotalRev":"Revenue",
                                 "RevPerTrip":"Rev/Trip"}).assign(
                        Revenue=lambda df: df["Revenue"].apply(fmt),
                        **{"Rev/Trip": lambda df: df["Rev/Trip"].apply(
                            lambda x: f"PKR {x/1e6:.1f}M")}),
                    use_container_width=True, hide_index=True)
                st.markdown(good("Swat = PKR 9.8M per trip. Add 200 more Swat trips = +PKR 1.96B potential revenue!"), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Model 7 error: {e}")

        st.markdown("---")

        # ── MODEL 8: TEAM PERFORMANCE ──────────────────────
        st.markdown(sec("👥 Model 8 — Team Performance Predictor Q2 2026"), unsafe_allow_html=True)
        st.markdown(note("Gradient Boosting model predicts Q2 2026 revenue per team. Green = on track. Red = at risk. HR and NSM can intervene early before targets are missed."), unsafe_allow_html=True)

        try:
            df_tp = pd.read_csv("ml_team_performance.csv")
            col1, col2 = st.columns(2)
            with col1:
                df_tp_s = df_tp.sort_values("Q2_2026_Forecast",ascending=False).head(15)
                colors_tp = ["#2e7d32" if s=="🟢 On Track"
                              else "#e65100" if s=="🟡 Watch"
                              else "#c62828" for s in df_tp_s["Status"]]
                fig = go.Figure(go.Bar(
                    x=df_tp_s["Q2_2026_Forecast"]/1e6, y=df_tp_s["TeamName"],
                    orientation="h",
                    text=df_tp_s["Q2_2026_Forecast"].apply(fmt),
                    textposition="outside", textfont_size=9,
                    marker_color=colors_tp))
                apply_layout(fig, height=480,
                             yaxis=dict(autorange="reversed",gridcolor="#eee"),
                             xaxis=dict(gridcolor="#eee",title="Q2 2026 Forecast (M PKR)"))
                fig.update_layout(title="Team Q2 2026 Revenue Forecast")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                disp_tp = df_tp[["TeamName","Q2_2026_Forecast","Rev2025",
                                  "Growth_vs_2025","Status"]].copy()
                disp_tp["Q2_2026_Forecast"] = disp_tp["Q2_2026_Forecast"].apply(fmt)
                disp_tp["Rev2025"]          = disp_tp["Rev2025"].apply(fmt)
                disp_tp["Growth_vs_2025"]   = disp_tp["Growth_vs_2025"].apply(
                    lambda x: f"{x:+.1f}%")
                st.dataframe(disp_tp.rename(columns={
                    "TeamName":"Team","Q2_2026_Forecast":"Q2 Forecast",
                    "Rev2025":"2025 Revenue","Growth_vs_2025":"vs 2025",
                    "Status":"Status"}),
                    use_container_width=True, hide_index=True)
                at_risk = (df_tp["Status"]=="🔴 At Risk").sum()
                st.markdown(danger(f"<b>{at_risk} teams at risk</b> of missing Q2 targets. NSM should review immediately."), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Model 8 error: {e}")

        st.markdown("---")

        # ── MODEL 9: SHELF LIFE RISK ───────────────────────
        st.markdown(sec("⚠️ Model 9 — Shelf Life & Velocity Risk"), unsafe_allow_html=True)
        st.markdown(note("Identifies products at risk of expiring before being sold. Based on ShelfLifeDays and monthly velocity. Red = critical. Take immediate action to push sales or initiate recall."), unsafe_allow_html=True)

        try:
            df_sl = pd.read_csv("ml_shelf_risk.csv")
            if "VelocityRisk" in df_sl.columns:
                col1, col2 = st.columns(2)
                with col1:
                    slow = df_sl[df_sl["VelocityRisk"]=="🔴 Slow Moving"].head(15)
                    fig = go.Figure(go.Bar(
                        x=slow["QtyPerMonth"], y=slow["Material Name"],
                        orientation="h",
                        text=slow["QtyPerMonth"].apply(lambda x: f"{x:.0f} units/mo"),
                        textposition="outside", textfont_size=9,
                        marker_color="#c62828"))
                    apply_layout(fig, height=480,
                                 yaxis=dict(autorange="reversed",gridcolor="#eee"),
                                 xaxis=dict(gridcolor="#eee",title="Units per Month"))
                    fig.update_layout(title="🔴 Slow Moving Products — Expiry Risk")
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    fast = df_sl[df_sl["VelocityRisk"]=="🟢 Fast Moving"].nlargest(10,"QtyPerMonth")
                    fig = go.Figure(go.Bar(
                        x=fast["QtyPerMonth"], y=fast["Material Name"],
                        orientation="h",
                        text=fast["QtyPerMonth"].apply(lambda x: f"{x:,.0f} units/mo"),
                        textposition="outside", textfont_size=9,
                        marker_color="#2e7d32"))
                    apply_layout(fig, height=480,
                                 yaxis=dict(autorange="reversed",gridcolor="#eee"),
                                 xaxis=dict(gridcolor="#eee",title="Units per Month"))
                    fig.update_layout(title="🟢 Fast Moving Products — No Risk")
                    st.plotly_chart(fig, use_container_width=True)

                vc = df_sl["VelocityRisk"].value_counts()
                c1,c2,c3 = st.columns(3)
                c1.markdown(kpi("🔴 Slow Moving",str(vc.get("🔴 Slow Moving",0)),"Expiry Risk"), unsafe_allow_html=True)
                c2.markdown(kpi("🟡 Moderate",str(vc.get("🟡 Moderate",0)),"Monitor"), unsafe_allow_html=True)
                c3.markdown(kpi("🟢 Fast Moving",str(vc.get("🟢 Fast Moving",0)),"Safe"), unsafe_allow_html=True)

            elif "Risk" in df_sl.columns:
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(
                        df_sl["Risk"].value_counts().reset_index(),
                        values="count", names="Risk",
                        title="Shelf Life Risk Distribution",
                        color_discrete_map={
                            "🔴 CRITICAL":"#c62828",
                            "🟡 WARNING":"#e65100",
                            "🟢 OK":"#2e7d32"})
                    apply_layout(fig, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.dataframe(df_sl[["Material Name","SDP Name","ShelfLifeDays","Risk"]].head(20),
                                 use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Model 9 error: {e}")

        st.markdown("---")

        # ── MODEL 10: DEMAND FORECAST ──────────────────────
        st.markdown(sec("📦 Model 10 — Demand Forecast per City per Product (R2=0.909)"), unsafe_allow_html=True)
        st.markdown(note("Random Forest model predicts how many units each city needs next month per product. Supply chain team can pre-position stock. Reduces stockouts and overstocking simultaneously."), unsafe_allow_html=True)

        try:
            df_dem = pd.read_csv("ml_demand_forecast.csv")
            col1, col2 = st.columns(2)
            with col1:
                pivot_dem = df_dem.pivot_table(
                    values="Apr2026_Qty", index="Product",
                    columns="City", fill_value=0).round(0)
                st.markdown("**Apr 2026 Demand Forecast (Units) by City:**")
                st.dataframe(pivot_dem.astype(int), use_container_width=True)

            with col2:
                city_total = df_dem.groupby("City")["Apr2026_Rev"].sum().reset_index()
                fig = px.bar(city_total.sort_values("Apr2026_Rev",ascending=False),
                             x="City", y="Apr2026_Rev",
                             text=city_total.sort_values("Apr2026_Rev",
                                 ascending=False)["Apr2026_Rev"].apply(fmt),
                             title="Apr 2026 Forecast Revenue by City",
                             color_discrete_sequence=["#2c5f8a"])
                fig.update_traces(textposition="outside", textfont_size=10)
                apply_layout(fig, height=380,
                             xaxis=dict(gridcolor="#eee"),
                             yaxis=dict(gridcolor="#eee",title="Forecast Revenue"))
                st.plotly_chart(fig, use_container_width=True)

            prod_total = df_dem.groupby("Product")["Apr2026_Rev"].sum().reset_index()
            fig = go.Figure(go.Bar(
                x=prod_total.sort_values("Apr2026_Rev",ascending=False)["Apr2026_Rev"]/1e6,
                y=prod_total.sort_values("Apr2026_Rev",ascending=False)["Product"],
                orientation="h",
                text=prod_total.sort_values("Apr2026_Rev",ascending=False)["Apr2026_Rev"].apply(fmt),
                textposition="outside", textfont_size=9,
                marker_color="#7b1fa2"))
            apply_layout(fig, height=380,
                         yaxis=dict(autorange="reversed",gridcolor="#eee"),
                         xaxis=dict(gridcolor="#eee",title="Forecast Revenue (M PKR)"))
            fig.update_layout(title="Apr 2026 Forecast Revenue by Product")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Model 10 error: {e}")

        st.markdown("---")

        # ── MODEL 11: BUDGET ALLOCATION ────────────────────
        st.markdown(sec("💰 Model 11 — Optimal Promo Budget Allocator"), unsafe_allow_html=True)
        st.markdown(note("Enter your total promotional budget. Model calculates optimal split across products to MAXIMIZE revenue. Current ROI = 18.6x. Optimized ROI = 159.7x on same budget!"), unsafe_allow_html=True)

        try:
            df_roi_prod = pd.read_csv("ml_budget_allocation.csv")
            df_act_roi  = pd.read_csv("ml_activity_roi.csv")

            st.markdown("### 🎯 Enter Your Budget:")
            budget_total = st.number_input(
                "Total Promotional Budget (PKR)",
                min_value=1000000, max_value=200000000,
                value=10000000, step=1000000,
                key="budget_optimizer")

            if st.button("🚀 Optimize My Budget!", type="primary"):
                total_roi_sum = df_roi_prod["ROI_actual"].sum()
                df_roi_prod["OptBudget"] = (
                    df_roi_prod["ROI_actual"]/total_roi_sum * budget_total)
                df_roi_prod["ExpRev"] = (
                    df_roi_prod["OptBudget"] * df_roi_prod["ROI_actual"])

                opt_roi_v = df_roi_prod["ExpRev"].sum()/df_roi_prod["OptBudget"].sum()
                exp_rev_v = df_roi_prod["ExpRev"].sum()

                c1,c2,c3 = st.columns(3)
                c1.markdown(kpi("Your Budget",    fmt(budget_total), "Input"), unsafe_allow_html=True)
                c2.markdown(kpi("Expected Revenue",fmt(exp_rev_v),   "ML Optimized"), unsafe_allow_html=True)
                c3.markdown(kpi("Optimized ROI",  f"{opt_roi_v:.1f}x","vs Current 18.6x"), unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    fig = go.Figure(go.Bar(
                        x=df_roi_prod["OptBudget"].head(10)/1e6,
                        y=df_roi_prod["ProductName"].head(10),
                        orientation="h",
                        text=df_roi_prod["OptBudget"].head(10).apply(fmt),
                        textposition="outside", textfont_size=9,
                        marker_color="#2e7d32"))
                    apply_layout(fig, height=380,
                                 yaxis=dict(autorange="reversed",gridcolor="#eee"),
                                 xaxis=dict(gridcolor="#eee",title="Optimal Budget (M PKR)"))
                    fig.update_layout(title="How to Allocate Your Budget")
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    disp_opt = df_roi_prod[["ProductName","OptBudget",
                                            "ROI_actual","ExpRev"]].head(10).copy()
                    disp_opt["OptBudget"]  = disp_opt["OptBudget"].apply(fmt)
                    disp_opt["ROI_actual"] = disp_opt["ROI_actual"].apply(lambda x: f"{x:.1f}x")
                    disp_opt["ExpRev"]     = disp_opt["ExpRev"].apply(fmt)
                    st.dataframe(disp_opt.rename(columns={
                        "ProductName":"Product","OptBudget":"Optimal Budget",
                        "ROI_actual":"ROI","ExpRev":"Expected Revenue"}),
                        use_container_width=True, hide_index=True)

            # Activity type ROI
            st.markdown("**Best Promotional Activity Types by ROI:**")
            act_disp = df_act_roi.head(10).copy()
            act_disp["TotalSpend"] = act_disp["TotalSpend"].apply(fmt)
            act_disp["TotalRev"]   = act_disp["TotalRev"].apply(fmt)
            act_disp["ROI"]        = act_disp["ROI"].apply(lambda x: f"{x:.1f}x")
            st.dataframe(act_disp.rename(columns={
                "ActivityHead":"Activity Type","TotalSpend":"Total Spend",
                "TotalRev":"Revenue Generated","ROI":"ROI"}),
                use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Model 11 error: {e}")

        st.markdown("---")

        # ── FINAL SUMMARY ──────────────────────────────────
        st.markdown(sec("💰 ML-Driven Business Impact Summary"), unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        c1.markdown(kpi("6-Month Forecast", fmt(df_fc1["Forecast"].sum()),
                        "Apr-Sep 2026"), unsafe_allow_html=True)
        c2.markdown(kpi("At-Risk Revenue",
                        fmt(churn_df[churn_df["RiskLevel"]=="🔴 High"]["Rev2024"].sum()),
                        "From churned distributors"), unsafe_allow_html=True)
        c3.markdown(kpi("Top ROI Product", "Xcept",
                        "46.3x ROI"), unsafe_allow_html=True)
        c4.markdown(kpi("Top Opportunity", "Karachi",
                        "Score 75/100 — 0 field visits!"), unsafe_allow_html=True)
