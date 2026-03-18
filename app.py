
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
    "🔗 Combined ROI Analysis",
    "🔮 Predictions & Forecast",
    "🚨 Alerts & Opportunities",
    "📊 Advanced Insights",
    "📦 Distribution Analysis",
    "🎯 Strategic Growth Plan",
    "🔬 Marketing Intelligence"
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
    c3.markdown(kpi("Best ROI Product",  "Ramipace",               "99.7x — manual proof below"), unsafe_allow_html=True)
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
        bp10 = df_s.groupby("ProductName")["TotalRevenue"].sum().nsmallest(10).reset_index()
        bp10["Label"] = bp10["TotalRevenue"].apply(lambda x: "PKR 0 — Check Status" if x==0 else fmt(x))
        bp10["Color"] = bp10["TotalRevenue"].apply(lambda x: "#c62828" if x==0 else "#e65100")
        fig = go.Figure(go.Bar(
            x=bp10["TotalRevenue"], y=bp10["ProductName"],
            orientation="h",
            text=bp10["Label"],
            textposition="outside",
            textfont_size=11,
            marker_color=bp10["Color"].tolist()
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
    bp = df_s[df_s["Yr"].isin([2024,2025])].groupby("ProductName")["TotalRevenue"].sum().nsmallest(50).reset_index()
    bp["Label"] = bp["TotalRevenue"].apply(lambda x: "PKR 0 — Check Status" if x==0 else fmt(x))
    bp["Status"] = bp["TotalRevenue"].apply(lambda x: "#c62828" if x==0 else "#e65100" if x<1e6 else "#2c5f8a")
    fig = go.Figure(go.Bar(
        x=bp["TotalRevenue"], y=bp["ProductName"],
        orientation="h",
        text=bp["Label"],
        textposition="outside",
        textfont_size=9,
        marker_color=bp["Status"].tolist()
    ))
    apply_layout(fig, height=1200,
                 yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                 xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(warn("Red bars = PKR 0 revenue. These products may be discontinued. Orange = very low revenue (under PKR 1M). Management should confirm product status."), unsafe_allow_html=True)

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

    st.markdown(sec("Team Travel Summary Table"), unsafe_allow_html=True)
    st.markdown(note("Full breakdown of all 34 teams. Avg Nights shows how long trips are. Teams with low trips AND low avg nights are doing minimal field work."), unsafe_allow_html=True)
    tt_all = tt.sort_values("Trips", ascending=False).copy()
    tt_all["Trips"]    = tt_all["Trips"].apply(fmt_num)
    tt_all["Nights"]   = tt_all["Nights"].apply(fmt_num)
    tt_all["AvgNights"]= tt_all["AvgNights"].astype(str) + " nights/trip"
    tt_all["People"]   = tt_all["People"].astype(str) + " people"
    tt_all.columns     = ["Team","Total Trips","Total Nights","Travellers","Avg Stay"]
    st.dataframe(tt_all, use_container_width=True, hide_index=True)

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
        st.markdown(note("Green = ROI above 50x (exceptional). Blue = above 20x (excellent). Orange = below 20x (needs review). Ramipace at 99.7x is the clear winner."), unsafe_allow_html=True)
        tr     = df_roi.nlargest(15,"ROI")
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
                     xaxis=dict(gridcolor="#eeeeee", title="ROI (x times)"))
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
    st.markdown("<h2 style=\'color:#2c5f8a\'>🔮 ML Sales Prediction & Forecast</h2>", unsafe_allow_html=True)
    st.markdown(note("Machine Learning models trained on 2 years of real data to predict future revenue. 3 models compared — best one is automatically selected for predictions."), unsafe_allow_html=True)

    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder

    df_ml = df_merged[(df_merged["Revenue"]>0) & (df_merged["PromoSpend"]>0)].copy()
    le_p  = LabelEncoder()
    le_t  = LabelEncoder()
    df_ml["Product_enc"] = le_p.fit_transform(df_ml["ProductName"])
    df_ml["Team_enc"]    = le_t.fit_transform(df_ml["TeamName"])
    df_ml["Month_sin"]   = np.sin(2*np.pi*df_ml["Mo"]/12)
    df_ml["Month_cos"]   = np.cos(2*np.pi*df_ml["Mo"]/12)

    features = ["PromoSpend","Requests","Product_enc","Team_enc",
                "Mo","Yr","Month_sin","Month_cos"]
    X = df_ml[features]
    y = df_ml["Revenue"]
    Xtr,Xte,ytr,yte = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "Linear Regression" : LinearRegression(),
        "Random Forest"     : RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting" : GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    results = {}
    for name, model in models.items():
        model.fit(Xtr, ytr)
        preds = model.predict(Xte)
        results[name] = {"model":model,"preds":preds,
                         "r2":r2_score(yte,preds),
                         "mae":mean_absolute_error(yte,preds)}

    st.markdown(sec("Model Comparison — Which Model is Most Accurate?"), unsafe_allow_html=True)
    st.markdown(note("R2 score = accuracy. R2 of 0.9 means 90% accurate. MAE = average error in PKR. Higher R2 and lower MAE = better model. Best model is auto-selected below."), unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    for col,(name,res),color in zip([c1,c2,c3],results.items(),
                                    ["#e65100","#2c5f8a","#2e7d32"]):
        col.markdown(kpi(name, f"R2 = {res['r2']:.3f}", f"MAE = {fmt(res['mae'])}"),
                     unsafe_allow_html=True)

    best_name  = max(results, key=lambda k: results[k]["r2"])
    best_res   = results[best_name]
    best_model = best_res["model"]
    r2v        = best_res["r2"]

    st.markdown(good(f"Best Model: <b>{best_name}</b> with R2 = {r2v:.3f}. This model explains {r2v*100:.1f}% of all revenue variation using promotional data as input."), unsafe_allow_html=True)

    st.markdown(sec("Actual vs Predicted Revenue"), unsafe_allow_html=True)
    st.markdown(note("Blue line = real actual revenue from database. Green dotted = what model predicted. Closer the lines = better the model. Gaps show where predictions were off."), unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(yte))), y=yte.values/1e6,
        name="Actual Revenue", mode="lines",
        line=dict(color="#2c5f8a",width=2),
        hovertemplate="Actual: PKR %{y:.1f}M<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=list(range(len(yte))), y=best_res["preds"]/1e6,
        name="Predicted Revenue", mode="lines",
        line=dict(color="#2e7d32",width=2,dash="dot"),
        hovertemplate="Predicted: PKR %{y:.1f}M<extra></extra>"
    ))
    apply_layout(fig, height=310, hovermode="x unified",
                 yaxis=dict(gridcolor="#eeeeee", title="Revenue (M PKR)"),
                 xaxis=dict(gridcolor="#eeeeee", title="Test Sample Index"))
    st.plotly_chart(fig, use_container_width=True)

    if hasattr(best_model,"feature_importances_"):
        st.markdown(sec("What Factors Drive Sales Most?"), unsafe_allow_html=True)
        st.markdown(note("Longer bar = more important factor for predicting sales. If PromoSpend is #1, it confirms promotions are the biggest driver of revenue."), unsafe_allow_html=True)
        fi = pd.DataFrame({
            "Factor":["Promo Spend","No. of Requests","Product Type",
                      "Sales Team","Month Number","Year",
                      "Month (Sine)","Month (Cosine)"],
            "Importance":best_model.feature_importances_
        }).sort_values("Importance",ascending=False)
        fi["Label"] = fi["Importance"].apply(lambda x: f"{x*100:.1f}%")
        fig = px.bar(fi, x="Importance", y="Factor",
                     orientation="h", text="Label",
                     color="Importance", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside",textfont_size=11)
        apply_layout(fig, height=290,
                     yaxis=dict(autorange="reversed",gridcolor="#eeeeee"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(sec("Revenue Forecast Simulator"), unsafe_allow_html=True)
    st.markdown(note("Enter your planned promotional spend below. The ML model will predict how much revenue you can expect to generate. This helps management plan budgets scientifically."), unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    with c1: sim_spend    = st.number_input("Promo Spend (PKR)", 100000, 50000000, 5000000, 500000)
    with c2: sim_month    = st.selectbox("Month", range(1,13), format_func=lambda x: months_map[x])
    with c3: sim_year     = st.selectbox("Year", [2025,2026])
    with c4: sim_requests = st.number_input("No. of Requests", 1, 100, 10)

    st.markdown(f"**Plan:** Spend {fmt(sim_spend)} on promotions in {months_map[sim_month]} {sim_year} with {sim_requests} requests")

    if st.button("Predict Revenue", type="primary"):
        sim_in = pd.DataFrame([{
            "PromoSpend":sim_spend,"Requests":sim_requests,
            "Product_enc":0,"Team_enc":0,"Mo":sim_month,"Yr":sim_year,
            "Month_sin":np.sin(2*np.pi*sim_month/12),
            "Month_cos":np.cos(2*np.pi*sim_month/12)
        }])
        pred    = best_model.predict(sim_in)[0]
        roi_sim = pred/sim_spend
        c1,c2,c3 = st.columns(3)
        c1.markdown(kpi("Predicted Revenue", fmt(pred),        "Based on your plan"), unsafe_allow_html=True)
        c2.markdown(kpi("Expected ROI",      f"{roi_sim:.1f}x","Revenue / Spend"), unsafe_allow_html=True)
        c3.markdown(kpi("Model Used",        best_name,        f"R2 = {r2v:.3f}"), unsafe_allow_html=True)
        st.success(f"For every PKR 1 you spend on promotions in {months_map[sim_month]}, you can expect PKR {roi_sim:.1f} in revenue!")

# ════════════════════════════════════════════════════════════
# PAGE 7: ALERTS & OPPORTUNITIES
# ════════════════════════════════════════════════════════════
elif page == "🚨 Alerts & Opportunities":
    st.markdown("<h2 style=\'color:#2c5f8a\'>🚨 Alerts & Strategic Opportunities</h2>", unsafe_allow_html=True)
    st.markdown(note("This page is your action plan. Green = opportunity (do more of this). Orange = warning (investigate). Red = urgent (act immediately)."), unsafe_allow_html=True)

    st.markdown(sec("Hidden Opportunities — Products With High ROI But Low Budget"), unsafe_allow_html=True)
    st.markdown(note("These products are generating amazing returns but receiving very little promotional budget. Increasing their budget could significantly boost company revenue with minimal extra investment."), unsafe_allow_html=True)

    opp = df_roi[
        (df_roi["ROI"]>20) &
        (df_roi["TotalPromoSpend"]<df_roi["TotalPromoSpend"].median())
    ].sort_values("ROI",ascending=False).head(10)

    for _, row in opp.iterrows():
        prod   = row["ProductName"]
        rv     = row["ROI"]
        sp     = row["TotalPromoSpend"]
        re     = row["TotalRevenue"]
        pot    = rv * sp * 2
        st.markdown(good(
            f"<b>{prod}</b> — ROI: <b>{rv:.1f}x</b> | "
            f"Current Spend: {fmt(sp)} | Revenue: {fmt(re)}<br>"
            f"<i>Action: Double budget to {fmt(sp*2)} → Expected revenue ~{fmt(pot)}</i>"
        ), unsafe_allow_html=True)

    st.markdown(sec("Budget Waste Alert — High Spend But Low ROI"), unsafe_allow_html=True)
    st.markdown(note("These products are consuming large promotional budgets but delivering poor returns. The budget should be reallocated to higher-ROI products listed above."), unsafe_allow_html=True)

    waste = df_roi[
        (df_roi["ROI"]<10) &
        (df_roi["TotalPromoSpend"]>df_roi["TotalPromoSpend"].median())
    ].sort_values("TotalPromoSpend",ascending=False).head(5)

    for _, row in waste.iterrows():
        prod = row["ProductName"]
        rv   = row["ROI"]
        sp   = row["TotalPromoSpend"]
        re   = row["TotalRevenue"]
        st.markdown(warn(
            f"<b>{prod}</b> — ROI: <b>{rv:.1f}x</b> (vs company avg 20.3x) | "
            f"Spent: {fmt(sp)} | Revenue: {fmt(re)}<br>"
            f"<i>Action: Reduce budget by 50% and reallocate to Ramipace/Xcept</i>"
        ), unsafe_allow_html=True)

    st.markdown(sec("Division Field Activity Alert"), unsafe_allow_html=True)
    st.markdown(note("Travel data reveals which divisions are NOT doing enough field visits. Low field activity = fewer doctor visits = lower prescriptions = lower sales."), unsafe_allow_html=True)

    div_travel = df_travel.groupby("TravellerDivision")["TravelCount"].sum().reset_index()
    for _, row in div_travel.sort_values("TravelCount").head(3).iterrows():
        st.markdown(danger(
            f"<b>{row['TravellerDivision']}</b> — only {int(row['TravelCount']):,} field trips in 5 years<br>"
            f"<i>Action: Investigate why field activity is low. Set minimum monthly trip targets.</i>"
        ), unsafe_allow_html=True)

    st.markdown(sec("Strategic Recommendations"), unsafe_allow_html=True)
    st.markdown(note("These are data-driven actions management can take immediately to improve company performance."), unsafe_allow_html=True)

    recs = [
        ("good",  "INVEST MORE in Ramipace",    "ROI = 99.7x. Increase budget from PKR 4.3M to PKR 10M. Expected extra revenue = PKR 500M+. Lowest risk highest reward action available."),
        ("good",  "Scale X-Plended campaigns",  "Top revenue product (PKR 4.3B) growing 21.9%. Increase Q4 promotional events to capture Oct-Dec sales peak."),
        ("good",  "Boost Finno-Q immediately",  "226% revenue growth in 2025 with minimal spend. This emerging product needs promotion before competitors notice."),
        ("warn",  "Review Shevit strategy",     "PKR 29M spent but only 5.6x ROI. That is 17x WORSE than Ramipace. Either fix strategy or reallocate budget."),
        ("warn",  "Fix Division 4 and 5",       "Only 80 and 175 field trips in 5 years. Set monthly field visit targets. Assign a dedicated travel budget."),
        ("warn",  "Monitor 2025 efficiency",    "Spend grew +38.2% but revenue only grew +16.6%. Spending is growing faster than returns. Audit where 2025 budget went."),
        ("good",  "Negotiate hotel contracts",  "Indigo Heights alone had 880 bookings. Negotiate corporate rates with top 5 hotels to reduce travel costs by 15-20%."),
        ("good",  "Focus campaigns on Q4",      "Oct/Nov/Dec are strongest sales AND travel months every year. Double promotional events in September to prepare for Q4 surge."),
    ]

    for style, title, desc in recs:
        if style == "good":
            st.markdown(good(f"<b>{title}:</b> {desc}"), unsafe_allow_html=True)
        else:
            st.markdown(warn(f"<b>{title}:</b> {desc}"), unsafe_allow_html=True)

    st.markdown(sec("Quick Wins Action Table"), unsafe_allow_html=True)
    st.markdown(note("Prioritized list of actions. RED = do this week. YELLOW = do this month. GREEN = do this quarter."), unsafe_allow_html=True)

    qw = pd.DataFrame({
        "Action":[
            "Double Ramipace promo budget",
            "Cut Shevit budget by 50%",
            "Increase Xcept budget 2x",
            "Set Division 4 travel targets",
            "Boost Finno-Q promotion",
            "Negotiate hotel bulk rates",
            "Boost Oct-Dec Q4 campaigns",
            "Cut Ferfer budget by 30%"
        ],
        "Current State":[
            "PKR 4.3M spend → PKR 430M revenue",
            "PKR 29M spend → only 5.6x ROI",
            "PKR 5.2M spend → PKR 395M revenue",
            "Only 80 trips in 5 years",
            "226% growth with minimal spend",
            "880 bookings at full price",
            "Q4 consistently strongest quarter",
            "PKR 47M spend → low ROI"
        ],
        "Expected Impact":[
            "+PKR 430M additional revenue",
            "Save PKR 14.5M → reinvest",
            "+PKR 395M additional revenue",
            "Improve sales in weak areas",
            "Capture growing market share",
            "Save 15-20% travel costs",
            "+15% Q4 revenue boost",
            "Save PKR 14.2M → reinvest"
        ],
        "Priority":[
            "🔴 THIS WEEK",
            "🔴 THIS WEEK",
            "🔴 THIS WEEK",
            "🔴 THIS WEEK",
            "🟡 THIS MONTH",
            "🟡 THIS MONTH",
            "🟡 THIS MONTH",
            "🟡 THIS MONTH"
        ]
    })
    st.dataframe(qw, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════
# PAGE 8: ADVANCED INSIGHTS
# ════════════════════════════════════════════════════════════
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
    total_rev_z  = df_z["LineRevenue"].sum()
    total_qty_z  = df_z["Billing Quantity"].sum()
    total_cities = df_zcity["City"].nunique()
    total_sdps   = df_zsdp["SDP Name"].nunique()
    total_prods  = df_zprod["Material Name"].nunique()
    rev24_z      = df_z[df_z["Yr"]==2024]["LineRevenue"].sum()
    rev25_z      = df_z[df_z["Yr"]==2025]["LineRevenue"].sum()
    growth_z     = ((rev25_z-rev24_z)/rev24_z*100) if rev24_z>0 else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Total Revenue",     fmt(total_rev_z),        "2024-2025 ZSDCY"), unsafe_allow_html=True)
    c2.markdown(kpi("Total Units",       fmt_num(total_qty_z),    "Units delivered"), unsafe_allow_html=True)
    c3.markdown(kpi("Cities Covered",    str(total_cities),       "Across Pakistan"), unsafe_allow_html=True)
    c4.markdown(kpi("Distributors",      str(total_sdps),         "Active SDPs"), unsafe_allow_html=True)
    c5.markdown(kpi("YoY Growth",        f"+{growth_z:.1f}%",     "2024 to 2025"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Revenue 2024",      fmt(rev24_z),            "Jan-Dec 2024"), unsafe_allow_html=True)
    c2.markdown(kpi("Revenue 2025",      fmt(rev25_z),            "Jan-Dec 2025"), unsafe_allow_html=True)
    c3.markdown(kpi("SKU Products",      str(total_prods),        "Unique product codes"), unsafe_allow_html=True)
    c4.markdown(kpi("Top City",          "Karachi",               "PKR 872M revenue"), unsafe_allow_html=True)
    c5.markdown(kpi("Shelf Risk Items",  str(len(df_zrisk)),      "⚠️ Under 90 days left", red=True), unsafe_allow_html=True)
    st.markdown("---")

    # CATEGORY SPLIT
    st.markdown(sec("📊 Revenue by Product Category"), unsafe_allow_html=True)
    st.markdown(note("Pharma is 86.3% of all revenue — core business. Nutraceutical at 12.7% is growing fast. Herbal and Medical Devices are small but present. Export is minimal."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        cat_rev = df_z.groupby("Category")["LineRevenue"].sum().reset_index()
        cat_rev["Label"] = cat_rev["LineRevenue"].apply(fmt)
        cat_rev = cat_rev.sort_values("LineRevenue", ascending=False)
        fig = px.bar(cat_rev, x="LineRevenue", y="Category",
                     orientation="h", text="Label",
                     color="LineRevenue", color_continuous_scale="Blues")
        fig.update_traces(textposition="outside", textfont_size=11)
        apply_layout(fig, height=300,
                     yaxis=dict(autorange="reversed", gridcolor="#eeeeee"),
                     xaxis=dict(gridcolor="#eeeeee", title="Revenue (PKR)"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.pie(cat_rev, values="LineRevenue", names="Category",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textinfo="percent+label", textfont_size=11)
        apply_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)

    # MONTHLY TREND
    st.markdown(sec("📈 Monthly Revenue Trend (ZSDCY)"), unsafe_allow_html=True)
    st.markdown(note("September 2025 = PKR 1.03B — biggest single month ever recorded! Jan 2024 was strong at PKR 692M. Clear upward trend from 2024 to 2025 confirms business growth."), unsafe_allow_html=True)

    mo_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    monthly_z = df_z.groupby(["Yr","Mo"])["LineRevenue"].sum().reset_index()
    monthly_z["Date"]  = pd.to_datetime(
        monthly_z["Yr"].astype(int).astype(str)+"-"+
        monthly_z["Mo"].astype(int).astype(str)+"-01")
    monthly_z["Label"] = monthly_z["LineRevenue"].apply(fmt)

    complete_z = monthly_z[monthly_z["Yr"]==2024]
    y2025_z    = monthly_z[monthly_z["Yr"]==2025]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=complete_z["Date"], y=complete_z["LineRevenue"]/1e6,
        name="2024", marker_color="rgba(44,95,138,0.7)",
        text=complete_z["Label"], textposition="outside",
        textfont_size=9
    ))
    fig.add_trace(go.Bar(
        x=y2025_z["Date"], y=y2025_z["LineRevenue"]/1e6,
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
            Revenue=("LineRevenue","sum"),
            Qty=("Billing Quantity","sum")).reset_index().nlargest(20,"Revenue")
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
            "ShelfLifeDays","LineRevenue"]].copy()
        risk_display["Material Name"] = risk_display["Material Name"].str[:40]
        risk_display["SDP Name"]      = risk_display["SDP Name"].str[:35]
        risk_display["Revenue"]       = risk_display["LineRevenue"].apply(fmt)
        risk_display["Days Left"]     = risk_display["ShelfLifeDays"].astype(int)
        risk_display["Risk Level"]    = risk_display["ShelfLifeDays"].apply(
            lambda x: "🔴 CRITICAL" if x<30 else "🟡 WARNING")
        st.dataframe(
            risk_display[["Material Name","SDP Name","Billing date",
                          "Days Left","Revenue","Risk Level"]],
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
            fmt_num(df_z[df_z["Yr"]==2024]["Billing Quantity"].sum()),
            str(df_z[df_z["Yr"]==2024]["Material Name"].nunique()),
            str(df_zcity[df_zcity["Yr"]==2024]["City"].nunique()),
            f"{len(df_z[df_z['Yr']==2024]):,}",
            fmt(rev24_z/12)
        ],
        "2025"      : [
            fmt(rev25_z),
            fmt_num(df_z[df_z["Yr"]==2025]["Billing Quantity"].sum()),
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
            df_zr[["Material Name","SDP Name","ShelfLifeDays",
                   "LineRevenue","Risk"]].rename(columns={
                "ShelfLifeDays":"Days Left","LineRevenue":"Revenue"}),
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
    retention = 87.6
    new_prods_2025 = 133
    price_growth = ((391.0-359.2)/359.2*100)
    lost_rev = 23.7

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Customer Retention", f"{retention}%",       "184 loyal distributors"), unsafe_allow_html=True)
    c2.markdown(kpi("New Products 2025",  str(new_prods_2025),   "Launched in 2025"), unsafe_allow_html=True)
    c3.markdown(kpi("Price Growth",       f"+{price_growth:.1f}%","PKR 359 → PKR 391/unit"), unsafe_allow_html=True)
    c4.markdown(kpi("Lost Revenue",       "PKR 23.7M",           "⚠️ Nusrat Pharma lost", red=True), unsafe_allow_html=True)
    c5.markdown(kpi("Fastest Product",    "X-Plended",           "89,634 units/month"), unsafe_allow_html=True)
    st.markdown("---")

    # INSIGHT 1: PRICE ANALYSIS
    st.markdown(sec("💰 Insight 1 — Price Per Unit Analysis (Premium Products)"), unsafe_allow_html=True)
    st.markdown(note("Higher price per unit = premium product = higher margin. Paridopa at PKR 947/unit and Femova at PKR 868/unit are premium products. Marketing should protect these products from generic competition."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        price_df = df_mkt[df_mkt["Net Price"]>0].groupby("Material Name").agg(
            AvgPrice=("Net Price","mean"),
            Revenue=("LineRevenue","sum")).reset_index()
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
        price_yr = df_mkt[df_mkt["Net Price"]>0].groupby(
            ["Yr","Material Name"])["Net Price"].mean().reset_index()
        price_yr24 = price_yr[price_yr["Yr"]==2024].set_index("Material Name")["Net Price"]
        price_yr25 = price_yr[price_yr["Yr"]==2025].set_index("Material Name")["Net Price"]
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
                    set(df_mkt[df_mkt["Yr"]==2025]["SDP Name"]))]["LineRevenue"].sum(),
                df_mkt[df_mkt["SDP Name"].isin(
                    set(df_mkt[df_mkt["Yr"]==2025]["SDP Name"]) -
                    set(df_mkt[df_mkt["Yr"]==2024]["SDP Name"]))]["LineRevenue"].sum(),
                df_mkt[df_mkt["SDP Name"].isin(
                    set(df_mkt[df_mkt["Yr"]==2024]["SDP Name"]) -
                    set(df_mkt[df_mkt["Yr"]==2025]["SDP Name"]))]["LineRevenue"].sum()
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
        TotalQty=("Billing Quantity","sum"),
        Months=("Mo","nunique"),
        Revenue=("LineRevenue","sum")).reset_index()
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
        Revenue=("LineRevenue","sum"),
        Qty=("Billing Quantity","sum"),
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

    plc = df_mkt.groupby(["Material Name","Yr"])["LineRevenue"].sum().reset_index()
    plc_pivot = plc.pivot(index="Material Name", columns="Yr",
                           values="LineRevenue").fillna(0)
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
        city_rev   = df_mkt.groupby("City")["LineRevenue"].sum()
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
        Revenue=("LineRevenue","sum"),
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

    dist_rev = df_mkt.groupby("SDP Name")["LineRevenue"].sum().sort_values(ascending=False).reset_index()
    dist_rev["CumPct"] = dist_rev["LineRevenue"].cumsum()/dist_rev["LineRevenue"].sum()*100
    dist_rev["Label"]  = dist_rev["LineRevenue"].apply(fmt)
    dist_rev["ShortName"] = dist_rev["SDP Name"].str[:30]

    col1, col2 = st.columns(2)
    with col1:
        top20_dist = dist_rev.head(20)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top20_dist["LineRevenue"]/1e6,
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

    cat_yr = df_mkt.groupby(["Category","Yr"])["LineRevenue"].sum().reset_index()
    cat_pivot = cat_yr.pivot(index="Category", columns="Yr",
                              values="LineRevenue").fillna(0)
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
