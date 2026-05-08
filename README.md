# PharmEvo Business Intelligence Dashboard

**Author:** Ryan Sheikh (Intern)  
**Built:** 2025–2026  
**Tech:** Python · Streamlit · Pandas · Plotly · scikit-learn  
**Live URL:** Deployed via Streamlit Cloud (linked to GitHub repository `pharmevo-dashboard`)

---

## What this dashboard does

A 9-page interactive business intelligence dashboard that consolidates four PharmEvo data sources into one place for management decision-making. It covers secondary sales (DSR), primary distribution (ZSDCY), promotional activities (FTTS), travel (FTTS), budget allocation, and includes machine-learning forecasts.

**The 9 pages:**

1. **📈 Sales Analysis** — Secondary sales (DSR), product-level revenue, growth, seasonality
2. **💰 Promotional Analysis** — FTTS promotional spend, team/product breakdowns, timing, ROI
3. **✈️ Travel Analysis** — FTTS travel patterns, city activity, division performance
4. **📦 Distribution Analysis** — ZSDCY primary sales, SKU growth, city-level distribution, category mix
5. **🔬 Strategic Intelligence Hub** — 5 tabs of cross-database insights, BCG matrix, executive findings
6. **🤖 ML Intelligence** — Revenue forecasts (Gradient Boosting MAPE 7.30%), product trajectories, churn risk
7. **💼 Budget Intelligence** — Allocated vs spent, transfer pattern, approval-chain bottlenecks
8. **📌 Personal Dashboard** — User-customizable view (pick any 44 KPIs/charts to display)
9. **👔 Management View** — Pre-built tabs for NSM (Sales), CMO (Marketing), and CEO/CFO

---

## How the data flows (architecture)

```
┌──────────────────────────────────────────────────────────────────────┐
│  PHARMEVO SOURCE SYSTEMS (live SQL Servers, accessible only via VPN) │
│                                                                      │
│  ┌─────────────────────────────┐    ┌────────────────────────────┐   │
│  │ DSR SQL Server              │    │ FTTS SQL Server            │   │
│  │ dsr.pharmevo.biz:14430      │    │ ftts.pharmevo.biz:14430    │   │
│  │ Database: PEVODSR           │    │ Database: pevoappftts      │   │
│  │ • VW_Sales (current)        │    │ • RequestMaster            │   │
│  │ • 18 monthly archive views  │    │ • Request_Activity_Details │   │
│  │   (jan24, feb24...)         │    │ • ProductMaster            │   │
│  │                             │    │ • vw_TravelRequest_Summary │   │
│  │                             │    │ • Product_Budget           │   │
│  │                             │    │ • RequestTransferBudget    │   │
│  │                             │    │ • MarketingExpenseRequest..│   │
│  │ ZSDCY data is exported      │    │                            │   │
│  │ from SAP into Excel files   │    │                            │   │
│  │ (one per quarter)           │    │                            │   │
│  └─────────────────────────────┘    └────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                          │ pulled via VPN
                          ▼
       ┌──────────────────────────────────────────┐
       │  REFRESH JUPYTER NOTEBOOK (Ryan's laptop) │
       │                                          │
       │  • Connects via ODBC + VPN               │
       │  • Runs SQL queries                      │
       │  • Cleans/aggregates with pandas         │
       │  • Writes CSV files                      │
       │  • Trains ML models, saves forecasts     │
       └──────────────────────────────────────────┘
                          │ saves to local disk
                          ▼
       ┌──────────────────────────────────────────┐
       │  CSV FILES (in GitHub repo)              │
       │  ~30 files. 7 are core inputs.           │
       │  See "File inventory" below.             │
       └──────────────────────────────────────────┘
                          │ git push
                          ▼
       ┌──────────────────────────────────────────┐
       │  STREAMLIT CLOUD (auto-deploys on push)  │
       │  • Loads CSVs at startup                 │
       │  • Caches in memory for 24 hours         │
       │  • Serves dashboard at public URL        │
       └──────────────────────────────────────────┘
                          │ HTTPS
                          ▼
                     ┌─────────────┐
                     │  USERS      │
                     └─────────────┘
```

---

## Why CSV instead of live SQL?

This was a deliberate design choice with three reasons:

1. **Streamlit Cloud cannot reach PharmEvo's databases.** Both `dsr.pharmevo.biz:14430` and `ftts.pharmevo.biz:14430` require VPN access. Streamlit Cloud's hosted servers sit outside the VPN. Direct live SQL is therefore physically impossible from Streamlit Cloud.

2. **Performance.** Querying live SQL on every page render would make the dashboard 5–30 seconds slow per click. CSV loading is sub-second, and Streamlit's `@st.cache_data` further caches results in memory.

3. **Reliability.** If the SQL server is down or slow, the dashboard would crash. CSV files mean the dashboard is always available.

**Trade-off:** Data freshness depends on when the CSVs were last refreshed. Currently this is a **monthly** process (see "Refresh process" below).

If live data is required, the dashboard would need to be deployed inside PharmEvo's network (on an internal server with VPN access) — that's a separate IT project.

---

## Refresh process (monthly)

The data is refreshed once a month using a Jupyter notebook on Ryan's laptop:

1. **Connect to VPN** (PharmEvo VPN required to reach DSR/FTTS servers)
2. **Open the refresh notebook** (`refresh_data.ipynb`)
3. **Run all cells.** This will:
   - Query DSR for current sales (`VW_Sales`) — results saved to `sales_clean.csv` / `.gz`
   - Query FTTS for activities, travel, budget — saved to corresponding CSVs
   - Process ZSDCY Excel files (newest quarter exported from SAP) — saved to `zsdcy_*.csv` files
   - Re-train ML models and save forecasts
4. **Verify** by checking the last date in each CSV (a `data_refreshed.txt` file is auto-written with timestamps)
5. **Commit and push** to GitHub:
   ```bash
   git add *.csv *.csv.gz data_refreshed.txt
   git commit -m "Monthly data refresh: <Month YYYY>"
   git push
   ```
6. **Streamlit Cloud auto-deploys** within ~2 minutes. Hard-refresh browser to see new data.

**Refresh cadence:** Monthly is the current schedule. Could be moved to weekly or automated via a scheduled GitHub Action / internal cron job.

---

## File inventory — what feeds the dashboard

The repository accumulated test artifacts and one-off CSVs over months of iteration. Here is the **definitive list of files actually loaded by `app.py`**:

### Code & config (REQUIRED — every deployment)
- `app.py` — the dashboard application (~5,600 lines)
- `requirements.txt` — Python package list for Streamlit Cloud
- `.gitignore` — git config

### Data — core inputs (REQUIRED — these are read on every page load)

**Sales:**
- `sales_clean.csv` *or* `sales_clean.csv.gz` — DSR secondary sales (Pages 1, 5, 9 + Strategic Hub)

**Promotional Activities:**
- `activities_clean.csv` *or* `activities_clean.csv.gz` — FTTS promotional activities (Pages 2, 5, 9)

**Travel:**
- `travel_clean.csv` *or* `travel_clean.csv.gz` — FTTS travel records (Pages 3, 5)

**Distribution (ZSDCY):**
- `zsdcy_clean.csv` *or* `zsdcy_clean.csv.gz` — main ZSDCY data, monthly granularity (Pages 4, 5)
- `zsdcy_products.csv` — pre-aggregated SKU totals (Page 4)
- `zsdcy_cities.csv` — pre-aggregated city totals (Page 4)
- `zsdcy_sdp.csv` — pre-aggregated distributor (SDP) totals (Page 4)
- `zsdcy_growth.csv` — pre-computed YoY growth fallback (Page 4)

**Budget:**
- `budget_allocated.csv` *or* `budget_allocated.csv.gz` — Product_Budget table dump (Page 7)
- `budget_transfers.csv` *or* `budget_transfers.csv.gz` — RequestTransferBudget table (Page 7)
- `marketing_expenses.csv` *or* `marketing_expenses.csv.gz` — MarketingExpenseRequestDetail (Page 7)
- `product_team_map.csv` — ve_Product_Team_Division_Mapping (Page 7)
- `allocated_vs_spent.csv` *or* `allocated_vs_spent.csv.gz` — pre-computed allocated-vs-spent rollup (Page 7)
- `merged_analysis.csv` — merged sales+activities cross-table (Page 7)
- `roi_analysis.csv` — pre-computed ROI rollup (Page 7)

**ML outputs (REQUIRED for Page 6):**
- `ml_forecast_revenue.csv` — revenue forecast (next 6 months)
- `ml_forecast_products.csv` — per-product forecast
- `ml_roi_products.csv` — ROI ranking with ML features
- `ml_master.csv` — feature matrix for the model
- `ml_churn_risk.csv` — products at risk of declining
- `ml_territory_scores.csv` — territory-level ML scores

**Refresh tracking:**
- `data_refreshed.txt` — auto-written timestamp file showing when each CSV was last refreshed

### Data — optional / supporting (used on specific Page 4 secondary sections)
- `zsdcy_velocity.csv` — SKU sell-through velocity
- `zsdcy_shelf_risk.csv` — SKUs at risk of stocking out / over-stocking
- `zsdcy_lifecycle.csv` — product-lifecycle classification
- `zsdcy_monthly.csv` — monthly ZSDCY rollup (used by some advanced views)
- `zsdcy_agg.csv` — alternative aggregation

### Data — NOT required by `app.py` (legacy / one-off, can be deleted)
None of the files in the listing fall into this category at the moment — all are referenced somewhere.

---

## Reproducing the dashboard locally

```bash
# 1. Clone the repo
git clone https://github.com/ryansheikh/pharmevo-dashboard.git
cd pharmevo-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run locally
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`.

---

## Known limitations

1. **Data freshness** — depends on monthly refresh cycle. Today's data is not in the dashboard.
2. **ZSDCY data** — currently uses a slim aggregated CSV (no `Material Name` column). Some Page 4 SKU-level analyses fall back to calendar-year (2024 vs 2025) instead of fiscal-year. To fix, regenerate `zsdcy_clean.csv` with `Material Name` included.
3. **Karachi travel under-counts** — sales reps make local Karachi visits without raising travel requests, so the travel database under-represents Karachi activity. This is noted in Page 3 captions.
4. **Streamlit Cloud has 25 MB per-file upload limit** — large CSVs are gzipped (`.csv.gz`) to stay under this limit.

---

## Project growth & reasoning

The dashboard evolved through 30+ supervisor feedback rounds. Key design decisions:

- **Pakistan fiscal year (Jul–Jun)** — used everywhere instead of calendar year, since PharmEvo's reporting follows this cycle.
- **Net Sales for headlines, Gross Sales for ROI Formula 1** — Net = SaleFlag in (S, R), Gross = S only. ROI uses Gross to avoid the appearance of penalizing returns/discounts.
- **4 ROI formulas (F1–F4)** — F3 (Net ÷ (Promo + Travel)) is recommended for true GTM ROI; F1 is shown for continuity with PharmEvo's existing reporting.
- **ML models per metric** — Gradient Boosting Regressor for revenue (MAPE 7.30%), Naive YoY for ZSDCY units (more stable for distribution data).

---

## Contact

For questions about the dashboard architecture, data lineage, or to extend it:  
**Ryan Sheikh** — [your email here]
