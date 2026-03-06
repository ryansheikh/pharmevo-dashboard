
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import numpy as np
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Pharmevo BI", page_icon="💊", layout="wide")

st.markdown("""
<style>
.kpi-card {
    background: linear-gradient(135deg, #1a1d2e, #2d2d44);
    border: 1px solid #3d3d5c; border-radius: 12px;
    padding: 20px; text-align: center; margin: 5px;
}
.kpi-value { font-size: 26px; font-weight: 800; color: #00d4ff; margin: 8px 0; }
.kpi-label { font-size: 12px; color: #a0a0b0; text-transform: uppercase; letter-spacing: 1px; }
.kpi-delta { font-size: 13px; color: #00ff88; font-weight: 600; }
.insight-box {
    background: linear-gradient(135deg, #1a2d1a, #1a1d2e);
    border-left: 4px solid #00ff88; border-radius: 8px;
    padding: 15px; margin: 8px 0; color: #e0e0e0; font-size: 14px;
}
.warning-box {
    background: linear-gradient(135deg, #2d1a1a, #1a1d2e);
    border-left: 4px solid #ff4444; border-radius: 8px;
    padding: 15px; margin: 8px 0; color: #e0e0e0; font-size: 14px;
}
.sec-header {
    font-size: 18px; font-weight: 700; color: #00d4ff;
    border-bottom: 2px solid #00d4ff; padding-bottom: 6px; margin: 15px 0 10px 0;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    ds = pd.read_csv("data/processed/sales_clean.csv")
    da = pd.read_csv("data/processed/activities_clean.csv")
    dm = pd.read_csv("data/processed/merged_analysis.csv")
    dr = pd.read_csv("data/processed/roi_analysis.csv")
    with open("data/processed/kpis.json") as f:
        kpis = json.load(f)
    ds["Date"] = pd.to_datetime(ds["Date"])
    da["Date"] = pd.to_datetime(da["Date"])
    return ds, da, dm, dr, kpis

df_sales, df_act, df_merged, df_roi, kpis = load_data()

months_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
              7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

PLOT_LAYOUT = dict(
    plot_bgcolor="#1a1d2e", paper_bgcolor="#1a1d2e",
    font_color="white",
    xaxis=dict(gridcolor="#2d2d44"),
    yaxis=dict(gridcolor="#2d2d44")
)

# ── SIDEBAR ──────────────────────────────────────────────────
st.sidebar.title("💊 Pharmevo BI")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", [
    "🏠 Executive Summary",
    "📈 Sales Analysis",
    "💰 Promotional Analysis",
    "🔗 Combined ROI Analysis",
    "🔮 Predictions & Forecast",
    "🚨 Alerts & Opportunities"
])
st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")
year_filter = st.sidebar.multiselect(
    "Year(s)", options=sorted(df_sales["Yr"].unique()),
    default=sorted(df_sales["Yr"].unique()))
team_filter = st.sidebar.multiselect(
    "Team(s)", options=sorted(df_sales["TeamName"].unique()), default=[])

df_s = df_sales[df_sales["Yr"].isin(year_filter)]
df_a = df_act[df_act["Yr"].isin(year_filter)]
if team_filter:
    df_s = df_s[df_s["TeamName"].isin(team_filter)]
    df_a = df_a[df_a["RequestorTeams"].str.upper().isin(
        [t.upper() for t in team_filter])]

def kpi_card(label, value, delta):
    return f"""<div class='kpi-card'>
        <div class='kpi-label'>{label}</div>
        <div class='kpi-value'>{value}</div>
        <div class='kpi-delta'>{delta}</div>
    </div>"""

def insight(text):
    return f"<div class='insight-box'>{text}</div>"

def warning(text):
    return f"<div class='warning-box'>{text}</div>"

def sec(text):
    return f"<div class='sec-header'>{text}</div>"

def apply_layout(fig, height=350, **kwargs):
    layout = dict(PLOT_LAYOUT)
    layout["height"] = height
    layout.update(kwargs)
    fig.update_layout(**layout)
    return fig

# ════════════════════════════════════════
# PAGE 1: EXECUTIVE SUMMARY
# ════════════════════════════════════════
if page == "🏠 Executive Summary":
    st.markdown("<h1 style='color:#00d4ff'>💊 Pharmevo Business Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#a0a0b0'>Sales & Promotional Analytics | 2017-2026 | SQL Server</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### Key Performance Indicators")
    cols = st.columns(5)
    kpis_row1 = [
        ("Total Revenue",    "PKR 47.8B",  "↑ +16.6% YoY"),
        ("Units Sold",       "153.1M",     "2024-2026"),
        ("Promo Investment", "PKR 7.67B",  "↑ +38.2% in 2025"),
        ("Overall ROI",      "20.3x",      "PKR 1 → PKR 20.3"),
        ("Doctors Targeted", "10,040",     "Unique Doctors"),
    ]
    for col, (label, value, delta) in zip(cols, kpis_row1):
        col.markdown(kpi_card(label, value, delta), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cols2 = st.columns(5)
    kpis_row2 = [
        ("Top Product",      "X-Plended",   "PKR 4.3B Revenue"),
        ("Top Team",         "Challengers", "PKR 6.5B Revenue"),
        ("Best ROI Product", "Ramipace",    "99.7x ROI"),
        ("Discount Rate",    "1.5%",        "PKR 749M discounts"),
        ("Promo Correlation","0.784",       "Strong same-month link"),
    ]
    for col, (label, value, delta) in zip(cols2, kpis_row2):
        col.markdown(kpi_card(label, value, delta), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(sec("📈 Monthly Revenue Trend"), unsafe_allow_html=True)
    monthly  = df_s.groupby("Date")["TotalRevenue"].sum().reset_index()
    complete = monthly[monthly["Date"].dt.year < 2026]
    partial  = monthly[monthly["Date"].dt.year >= 2026]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=complete["Date"], y=complete["TotalRevenue"]/1e6,
        name="Revenue", line=dict(color="#00d4ff", width=2.5),
        fill="tozeroy", fillcolor="rgba(0,212,255,0.1)", mode="lines+markers"))
    fig.add_trace(go.Scatter(
        x=partial["Date"], y=partial["TotalRevenue"]/1e6,
        name="2026 Partial", line=dict(color="#ffa500", width=2.5, dash="dash"),
        mode="lines+markers"))
    apply_layout(fig, height=320, hovermode="x unified",
                 yaxis=dict(gridcolor="#2d2d44", title="Revenue (M PKR)"))
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("🏆 Top 10 Products by Revenue"), unsafe_allow_html=True)
        tp = df_s.groupby("ProductName")["TotalRevenue"].sum().nlargest(10).reset_index()
        fig = px.bar(tp, x="TotalRevenue", y="ProductName", orientation="h",
                     color="TotalRevenue", color_continuous_scale="Blues")
        apply_layout(fig, height=340, yaxis=dict(autorange="reversed", gridcolor="#2d2d44"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(sec("👥 Top 10 Teams by Revenue"), unsafe_allow_html=True)
        tt = df_s.groupby("TeamName")["TotalRevenue"].sum().nlargest(10).reset_index()
        fig = px.bar(tt, x="TotalRevenue", y="TeamName", orientation="h",
                     color="TotalRevenue", color_continuous_scale="Greens")
        apply_layout(fig, height=340, yaxis=dict(autorange="reversed", gridcolor="#2d2d44"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(insight("🌟 <b>Revenue grew 16.6%</b> from 2024 to 2025 — PKR 20.2B to PKR 23.6B"), unsafe_allow_html=True)
        st.markdown(insight("🌟 <b>COVID-19 proven:</b> 2020 saw -33.7% drop, then +68.6% recovery in 2021"), unsafe_allow_html=True)
        st.markdown(insight("🌟 <b>0.784 correlation</b> — promo spend has strong same-month sales impact"), unsafe_allow_html=True)
    with col2:
        st.markdown(insight("🌟 <b>Ramipace ROI = 99.7x</b> — PKR 4.3M spend generates PKR 430M revenue"), unsafe_allow_html=True)
        st.markdown(warning("⚠️ <b>Shevit:</b> PKR 29M spent but only 5.6x ROI — needs strategy review"), unsafe_allow_html=True)
        st.markdown(warning("⚠️ <b>2026 is partial year</b> (Jan-Mar only) — do not compare with full years"), unsafe_allow_html=True)

# ════════════════════════════════════════
# PAGE 2: SALES ANALYSIS
# ════════════════════════════════════════
elif page == "📈 Sales Analysis":
    st.markdown("<h2 style='color:#00d4ff'>📈 Sales Deep Analysis</h2>", unsafe_allow_html=True)

    yearly = df_s[df_s["Yr"] < 2026].groupby("Yr").agg(
        Revenue=("TotalRevenue","sum"),
        Units=("TotalUnits","sum"),
        Invoices=("InvoiceCount","sum")).reset_index()

    c1,c2,c3 = st.columns(3)
    for col, field, title, color in zip(
        [c1,c2,c3], ["Revenue","Units","Invoices"],
        ["Revenue (PKR)","Units Sold","Invoices"],
        ["#00d4ff","#00ff88","#ffa500"]):
        with col:
            fig = px.bar(yearly, x="Yr", y=field, title=title,
                         color_discrete_sequence=[color])
            apply_layout(fig, height=260,
                         xaxis=dict(gridcolor="#2d2d44", tickmode="array", tickvals=yearly["Yr"]),
                         yaxis=dict(gridcolor="#2d2d44"))
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Product Revenue 2024 vs 2025"), unsafe_allow_html=True)
        ry = df_s[df_s["Yr"].isin([2024,2025])].groupby(["ProductName","Yr"])["TotalRevenue"].sum().reset_index()
        top15 = ry.groupby("ProductName")["TotalRevenue"].sum().nlargest(15).index
        ry = ry[ry["ProductName"].isin(top15)]
        fig = px.bar(ry, x="TotalRevenue", y="ProductName", color="Yr",
                     barmode="group", orientation="h",
                     color_discrete_map={2024:"#00d4ff", 2025:"#00ff88"})
        apply_layout(fig, height=500, yaxis=dict(autorange="reversed", gridcolor="#2d2d44"))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(sec("Fastest Growing Products 2024 to 2025"), unsafe_allow_html=True)
        r24 = df_s[df_s["Yr"]==2024].groupby("ProductName")["TotalRevenue"].sum()
        r25 = df_s[df_s["Yr"]==2025].groupby("ProductName")["TotalRevenue"].sum()
        gdf = pd.DataFrame({"y2024":r24,"y2025":r25}).dropna()
        gdf = gdf[gdf["y2024"] > 5000000]
        gdf["Growth"] = ((gdf["y2025"]-gdf["y2024"])/gdf["y2024"]*100)
        gdf = gdf.sort_values("Growth", ascending=False).head(15).reset_index()
        fig = px.bar(gdf, x="Growth", y="ProductName", orientation="h",
                     color="Growth", color_continuous_scale="Greens")
        apply_layout(fig, height=500,
                     yaxis=dict(autorange="reversed", gridcolor="#2d2d44"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(sec("📅 Sales Seasonality Heatmap"), unsafe_allow_html=True)
    heat = df_s[df_s["Yr"]<2026].groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
    heat["Month"] = heat["Mo"].map(months_map)
    hp = heat.pivot(index="Yr", columns="Month", values="TotalRevenue")
    hp = hp.reindex(columns=list(months_map.values()))
    fig = px.imshow(hp/1e6, color_continuous_scale="Blues", aspect="auto",
                    labels=dict(color="Revenue (M PKR)"))
    apply_layout(fig, height=220)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Darker = higher revenue. Oct-Dec are consistently the strongest months.")

# ════════════════════════════════════════
# PAGE 3: PROMOTIONAL ANALYSIS
# ════════════════════════════════════════
elif page == "💰 Promotional Analysis":
    st.markdown("<h2 style='color:#00d4ff'>💰 Promotional Spend Analysis</h2>", unsafe_allow_html=True)

    total_sp = df_a["TotalAmount"].sum()
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Promo Spend",  f"PKR {total_sp/1e9:.2f}B")
    with c2: st.metric("Total Requests",     f"{df_a['RequestCount'].sum():,.0f}")
    with c3: st.metric("Avg per Request",    f"PKR {total_sp/max(df_a['RequestCount'].sum(),1):,.0f}")
    with c4: st.metric("Peak Year", "2025",  delta="PKR 1.37B")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Promotional Spend Trend 2017-2026"), unsafe_allow_html=True)
        ysp = df_a.groupby("Yr")["TotalAmount"].sum().reset_index()
        fig = px.bar(ysp, x="Yr", y="TotalAmount", color="TotalAmount",
                     color_continuous_scale="Blues")
        fig.add_scatter(x=ysp["Yr"], y=ysp["TotalAmount"],
                        mode="lines+markers", line=dict(color="#00ff88", width=2))
        apply_layout(fig, height=300,
                     xaxis=dict(gridcolor="#2d2d44", tickmode="array", tickvals=ysp["Yr"]),
                     yaxis=dict(gridcolor="#2d2d44"),
                     coloraxis_showscale=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(sec("Spend by Activity Type"), unsafe_allow_html=True)
        asp = df_a.groupby("ActivityHead")["TotalAmount"].sum().nlargest(10).reset_index()
        fig = px.pie(asp, values="TotalAmount", names="ActivityHead",
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        apply_layout(fig, height=300)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("Top 10 Teams by Promo Spend"), unsafe_allow_html=True)
        tsp = df_a.groupby("RequestorTeams")["TotalAmount"].sum().nlargest(10).reset_index()
        fig = px.bar(tsp, x="TotalAmount", y="RequestorTeams", orientation="h",
                     color="TotalAmount", color_continuous_scale="Oranges")
        apply_layout(fig, height=340,
                     yaxis=dict(autorange="reversed", gridcolor="#2d2d44"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(sec("Top 10 Products by Promo Investment"), unsafe_allow_html=True)
        psp = df_a.groupby("Product")["TotalAmount"].sum().nlargest(10).reset_index()
        fig = px.bar(psp, x="TotalAmount", y="Product", orientation="h",
                     color="TotalAmount", color_continuous_scale="Purples")
        apply_layout(fig, height=340,
                     yaxis=dict(autorange="reversed", gridcolor="#2d2d44"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(sec("Budget Allocation by GL Head"), unsafe_allow_html=True)
    gl = df_a.groupby("GLHead")["TotalAmount"].sum().nlargest(8).reset_index()
    fig = make_subplots(rows=1, cols=2, specs=[[{"type":"bar"},{"type":"pie"}]])
    fig.add_trace(go.Bar(x=gl["TotalAmount"], y=gl["GLHead"],
                         orientation="h", marker_color="#00d4ff"), row=1, col=1)
    fig.add_trace(go.Pie(values=gl["TotalAmount"], labels=gl["GLHead"]), row=1, col=2)
    apply_layout(fig, height=320, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════
# PAGE 4: COMBINED ROI
# ════════════════════════════════════════
elif page == "🔗 Combined ROI Analysis":
    st.markdown("<h2 style='color:#00d4ff'>🔗 Combined ROI Analysis</h2>", unsafe_allow_html=True)
    st.markdown(insight("🔬 <b>Key Finding:</b> Promotional spend and same-month revenue show <b>0.784 correlation</b>. Every PKR 1 spent generates PKR 20.3 in revenue on average."), unsafe_allow_html=True)

    st.markdown(sec("Promo Spend vs Revenue Monthly"), unsafe_allow_html=True)
    msp   = df_a.groupby("Date")["TotalAmount"].sum().reset_index()
    mrv   = df_s.groupby("Date")["TotalRevenue"].sum().reset_index()
    combo = pd.merge(msp, mrv, on="Date", how="inner")
    fig   = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=combo["Date"], y=combo["TotalAmount"]/1e6,
                         name="Promo Spend (M PKR)",
                         marker_color="rgba(255,165,0,0.7)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=combo["Date"], y=combo["TotalRevenue"]/1e6,
                             name="Revenue (M PKR)",
                             line=dict(color="#00d4ff", width=3),
                             mode="lines+markers"), secondary_y=True)
    apply_layout(fig, height=340, hovermode="x unified")
    fig.update_yaxes(title_text="Promo Spend (M PKR)", gridcolor="#2d2d44", secondary_y=False)
    fig.update_yaxes(title_text="Revenue (M PKR)",     gridcolor="#2d2d44", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(sec("ROI Bubble Chart by Product"), unsafe_allow_html=True)
        rp = df_roi[(df_roi["TotalPromoSpend"]>0) & (df_roi["ROI"]<200)].copy()
        fig = px.scatter(rp, x="TotalPromoSpend", y="TotalRevenue",
                         size="ROI", color="ROI", hover_name="ProductName",
                         color_continuous_scale="RdYlGn", size_max=50)
        apply_layout(fig, height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Bigger bubble = higher ROI. Top-left corner = high ROI + low spend = invest more!")
    with col2:
        st.markdown(sec("Top 15 Products by ROI"), unsafe_allow_html=True)
        tr     = df_roi.nlargest(15, "ROI")
        colors = ["#00ff88" if r>50 else "#00d4ff" if r>20 else "#ffa500" for r in tr["ROI"]]
        fig    = go.Figure(go.Bar(
            x=tr["ROI"], y=tr["ProductName"], orientation="h",
            marker_color=colors,
            text=[f"{r:.1f}x" for r in tr["ROI"]], textposition="outside"))
        apply_layout(fig, height=400,
                     yaxis=dict(autorange="reversed", gridcolor="#2d2d44"),
                     xaxis=dict(gridcolor="#2d2d44", title="ROI"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(sec("Team ROI Summary"), unsafe_allow_html=True)
    tdf = pd.DataFrame({
        "Team":      ["CHALLENGERS","BRAVO","METABOLIZERS","LEGENDS","CHAMPIONS",
                      "WINNERS","WARRIORS","ALPHA","BONE SAVIORS","TITANS"],
        "Promo Spend":["PKR 118.6M","PKR 44.9M","PKR 81.7M","PKR 78.1M","PKR 37.5M",
                       "PKR 67.2M","PKR 75.5M","PKR 61.4M","PKR 133.6M","PKR 101.7M"],
        "Revenue":   ["PKR 4.53B","PKR 1.52B","PKR 2.38B","PKR 2.10B","PKR 1.07B",
                      "PKR 1.49B","PKR 1.59B","PKR 1.11B","PKR 2.32B","PKR 1.33B"],
        "ROI":       ["38.2x","33.9x","29.1x","26.8x","28.7x",
                      "22.3x","21.0x","18.0x","17.4x","13.1x"]
    })
    st.dataframe(tdf, use_container_width=True, hide_index=True)

# ════════════════════════════════════════
# PAGE 5: PREDICTIONS
# ════════════════════════════════════════
elif page == "🔮 Predictions & Forecast":
    st.markdown("<h2 style='color:#00d4ff'>🔮 Sales Prediction and Forecast</h2>", unsafe_allow_html=True)

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

    features = ["PromoSpend","Requests","Product_enc","Team_enc","Mo","Yr","Month_sin","Month_cos"]
    X = df_ml[features]
    y = df_ml["Revenue"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "Linear Regression" : LinearRegression(),
        "Random Forest"     : RandomForestRegressor(n_estimators=100, random_state=42),
        "Gradient Boosting" : GradientBoostingRegressor(n_estimators=100, random_state=42)
    }
    results = {}
    for name, model in models.items():
        model.fit(Xtr, ytr)
        preds = model.predict(Xte)
        results[name] = {
            "model": model, "preds": preds,
            "r2":  r2_score(yte, preds),
            "mae": mean_absolute_error(yte, preds)
        }

    st.markdown(sec("Model Comparison"), unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    for col,(name,res),color in zip([c1,c2,c3],results.items(),["#ffa500","#00d4ff","#00ff88"]):
        r2v  = res["r2"]
        maev = res["mae"]
        col.markdown(kpi_card(name, f"R2 = {r2v:.3f}", f"MAE = PKR {maev:,.0f}"), unsafe_allow_html=True)

    best_name  = max(results, key=lambda k: results[k]["r2"])
    best_res   = results[best_name]
    best_model = best_res["model"]
    r2v        = best_res["r2"]

    st.markdown(insight(f"🏆 <b>Best Model: {best_name}</b> — R2 = {r2v:.3f} — explains {r2v*100:.1f}% of revenue variance"), unsafe_allow_html=True)

    st.markdown(sec("Actual vs Predicted Revenue"), unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(yte))), y=yte.values/1e6,
                             name="Actual",    mode="lines", line=dict(color="#00d4ff",width=2)))
    fig.add_trace(go.Scatter(x=list(range(len(yte))), y=best_res["preds"]/1e6,
                             name="Predicted", mode="lines",
                             line=dict(color="#00ff88",width=2,dash="dot")))
    apply_layout(fig, height=300, hovermode="x unified",
                 yaxis=dict(gridcolor="#2d2d44", title="Revenue (M PKR)"))
    st.plotly_chart(fig, use_container_width=True)

    if hasattr(best_model, "feature_importances_"):
        st.markdown(sec("What Drives Sales - Feature Importance"), unsafe_allow_html=True)
        fi = pd.DataFrame({"Feature":features,
                           "Importance":best_model.feature_importances_}
                         ).sort_values("Importance", ascending=False)
        fig = px.bar(fi, x="Importance", y="Feature", orientation="h",
                     color="Importance", color_continuous_scale="Blues")
        apply_layout(fig, height=280,
                     yaxis=dict(autorange="reversed", gridcolor="#2d2d44"),
                     coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(sec("Revenue Forecast Simulator"), unsafe_allow_html=True)
    st.markdown("Predict revenue based on your planned promotional spend")
    c1,c2,c3,c4 = st.columns(4)
    with c1: sim_spend    = st.number_input("Promo Spend (PKR)", 100000, 50000000, 5000000, 500000)
    with c2: sim_month    = st.selectbox("Month", range(1,13), format_func=lambda x: months_map[x])
    with c3: sim_year     = st.selectbox("Year", [2025,2026])
    with c4: sim_requests = st.number_input("No. of Requests", 1, 100, 10)

    if st.button("Predict Revenue", type="primary"):
        sim_in = pd.DataFrame([{
            "PromoSpend":sim_spend, "Requests":sim_requests,
            "Product_enc":0, "Team_enc":0, "Mo":sim_month, "Yr":sim_year,
            "Month_sin":np.sin(2*np.pi*sim_month/12),
            "Month_cos":np.cos(2*np.pi*sim_month/12)
        }])
        pred    = best_model.predict(sim_in)[0]
        roi_sim = pred / sim_spend
        c1,c2,c3 = st.columns(3)
        c1.markdown(kpi_card("Predicted Revenue", f"PKR {pred/1e6:.1f}M", best_name), unsafe_allow_html=True)
        c2.markdown(kpi_card("Expected ROI",      f"{roi_sim:.1f}x",      "Revenue / Spend"), unsafe_allow_html=True)
        c3.markdown(kpi_card("Model Used",        best_name,              f"R2 = {r2v:.3f}"), unsafe_allow_html=True)

# ════════════════════════════════════════
# PAGE 6: ALERTS
# ════════════════════════════════════════
elif page == "🚨 Alerts & Opportunities":
    st.markdown("<h2 style='color:#00d4ff'>🚨 Alerts and Strategic Opportunities</h2>", unsafe_allow_html=True)

    st.markdown(sec("Hidden Opportunities - Underinvested Products"), unsafe_allow_html=True)
    st.markdown("High ROI but low promo spend — these products deserve more budget!", unsafe_allow_html=True)
    opp = df_roi[
        (df_roi["ROI"] > 20) &
        (df_roi["TotalPromoSpend"] < df_roi["TotalPromoSpend"].median())
    ].sort_values("ROI", ascending=False).head(10)

    for _, row in opp.iterrows():
        prod    = row["ProductName"]
        roi_val = row["ROI"]
        spend   = row["TotalPromoSpend"]
        rev     = row["TotalRevenue"]
        pot     = roi_val * spend * 2
        txt = f"🌟 <b>{prod}</b> — ROI: <b>{roi_val:.1f}x</b><br>Spend: PKR {spend:,.0f} — Revenue: PKR {rev:,.0f}<br><i>Doubling spend could generate ~PKR {pot:,.0f}</i>"
        st.markdown(insight(txt), unsafe_allow_html=True)

    st.markdown(sec("Budget Waste Alerts - Low ROI Products"), unsafe_allow_html=True)
    waste = df_roi[
        (df_roi["ROI"] < 10) &
        (df_roi["TotalPromoSpend"] > df_roi["TotalPromoSpend"].median())
    ].sort_values("TotalPromoSpend", ascending=False).head(5)

    for _, row in waste.iterrows():
        prod    = row["ProductName"]
        roi_val = row["ROI"]
        spend   = row["TotalPromoSpend"]
        rev     = row["TotalRevenue"]
        txt = f"⚠️ <b>{prod}</b> — ROI: <b>{roi_val:.1f}x</b> vs 20x company average<br>Spent: PKR {spend:,.0f} — Revenue: PKR {rev:,.0f}<br><i>Consider reviewing promotional strategy</i>"
        st.markdown(warning(txt), unsafe_allow_html=True)

    st.markdown(sec("Strategic Recommendations"), unsafe_allow_html=True)
    recs = [
        ("Reallocate Budget",  "Move 20% of Shevit/Ferfer budget to Ramipace/Xcept — could add PKR 500M+ in revenue"),
        ("Scale X-Plended",    "Top product at PKR 4.3B with 21.9% growth — increase promo investment now"),
        ("Focus on Oct-Dec",   "Historically strongest months — concentrate promotional events in Q4"),
        ("Team Challengers",   "Highest ROI team at 38.2x — replicate their strategy across all teams"),
        ("Finno-Q Emerging",   "226% growth in 2025 — needs immediate promotional support"),
        ("COVID Reserve",      "2021 showed +68.6% bounce after COVID — maintain emergency promo budget"),
    ]
    for title, desc in recs:
        st.markdown(insight(f"<b>{title}:</b> {desc}"), unsafe_allow_html=True)

    st.markdown(sec("Quick Wins Summary Table"), unsafe_allow_html=True)
    qw = pd.DataFrame({
        "Action":         ["Increase Ramipace budget 2x","Increase Xcept budget 2x",
                           "Cut Shevit budget 50%","Cut Ferfer budget 30%",
                           "Boost Oct-Dec campaigns"],
        "Current Spend":  ["PKR 4.3M","PKR 5.2M","PKR 29M","PKR 47M","Varies"],
        "Expected Impact":["+PKR 430M revenue","+PKR 395M revenue",
                           "Save PKR 14.5M","Save PKR 14.2M","+15% Q4 revenue"],
        "Priority":       ["HIGH","HIGH","MEDIUM","MEDIUM","LOW"]
    })
    st.dataframe(qw, use_container_width=True, hide_index=True)
