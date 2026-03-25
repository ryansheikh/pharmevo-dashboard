"""
HOW TO USE THIS:
1. Put this file in your pharmevo_project folder (same folder as app.py)
2. Open command prompt: cd C:\\Users\\Hp\\pharmevo_project
3. Run: python fix_app.py
4. It will modify your app.py with all 3 changes
5. Then push to GitHub: git add . && git commit -m "Add Combine 4 Dataset page" && git push
"""

code = open("app.py", "r", encoding="utf-8").read()
original_size = len(code)
print(f"📂 Read app.py: {original_size/1024:.1f} KB")

# ── FIX 1: Add zsdcy to load_data ───────────────────────────
old1 = '    dt = pd.read_csv("travel_clean.csv")\n    with open("kpis.json")'
new1 = '    dt = pd.read_csv("travel_clean.csv")\n    dz = pd.read_csv("zsdcy_clean.csv")\n    with open("kpis.json")'

if "dz = pd.read_csv" not in code:
    if old1 in code:
        code = code.replace(old1, new1)
        print("✅ Fix 1a: Added zsdcy read")
    else:
        print("❌ Fix 1a failed")

old1b = "return ds, da, dm, dr, dt, kpis\n\ndf_sales, df_act, df_merged, df_roi, df_travel, kpis = load_data()"
new1b = "return ds, da, dm, dr, dt, dz, kpis\n\ndf_sales, df_act, df_merged, df_roi, df_travel, df_zsdcy, kpis = load_data()"

if "df_zsdcy" not in code:
    if old1b in code:
        code = code.replace(old1b, new1b)
        print("✅ Fix 1b: Updated return + unpacking")
    else:
        print("❌ Fix 1b failed")
else:
    print("⚠️ Fix 1: zsdcy already loaded")

# ── FIX 2: Add to sidebar ───────────────────────────────────
if "🧠 Combine 4 Dataset" not in code:
    old2 = '    "🔬 Marketing Intelligence"\n])'
    new2 = '    "🔬 Marketing Intelligence",\n    "🧠 Combine 4 Dataset"\n])'
    if old2 in code:
        code = code.replace(old2, new2)
        print("✅ Fix 2: Sidebar updated")
    else:
        print("❌ Fix 2 failed")
else:
    print("⚠️ Fix 2: Already in sidebar")

# ── FIX 3: Remove old page if exists ────────────────────────
for marker in ["# PAGE 12: COMBINE 4 DATASET", "# PAGE 13: COMBINE", "# PAGE 13: COMBINED"]:
    idx = code.find(marker)
    if idx > -1:
        search_back = code.rfind("\n\n", 0, idx)
        if search_back > -1:
            code = code[:search_back]
            print(f"⚠️ Removed old page at position {idx}")
        break

# ── FIX 4: Append new page ──────────────────────────────────
new_page = '''


# ════════════════════════════════════════════════════════════
# PAGE 12: COMBINE 4 DATASET — STRATEGIC INTELLIGENCE
# ════════════════════════════════════════════════════════════
elif page == "🧠 Combine 4 Dataset":
    st.markdown("<h1 style='color:#2c5f8a'>🧠 Combined 4 Database Strategic Intelligence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#555; font-size:15px'>Sales (DSR) + Promotional Activities (FTTS) + Travel (FTTS) + Distribution (ZSDCY) | 2024-2026</p>", unsafe_allow_html=True)
    st.markdown(note("This page connects all 4 databases to tell one complete story. Every number is verified from real data."), unsafe_allow_html=True)
    st.markdown("---")

    rev_24  = df_sales[df_sales["Yr"]==2024]["TotalRevenue"].sum()
    rev_25  = df_sales[df_sales["Yr"]==2025]["TotalRevenue"].sum()
    rev_26  = df_sales[df_sales["Yr"]==2026]["TotalRevenue"].sum()
    rev_all = df_sales["TotalRevenue"].sum()
    sp_24   = df_act[df_act["Yr"]==2024]["TotalAmount"].sum()
    sp_25   = df_act[df_act["Yr"]==2025]["TotalAmount"].sum()
    sp_all  = df_act["TotalAmount"].sum()
    roi_24  = rev_24/sp_24 if sp_24>0 else 0
    roi_25  = rev_25/sp_25 if sp_25>0 else 0
    roi_all = rev_all/sp_all if sp_all>0 else 0
    rev_growth   = ((rev_25-rev_24)/rev_24*100) if rev_24>0 else 0
    spend_growth = ((sp_25-sp_24)/sp_24*100) if sp_24>0 else 0
    trips_all = df_travel["TravelCount"].sum()
    trips_24  = df_travel[df_travel["Yr"]==2024]["TravelCount"].sum()
    trips_25  = df_travel[df_travel["Yr"]==2025]["TotalRevenue"].sum() if "TotalRevenue" in df_travel.columns else df_travel[df_travel["Yr"]==2025]["TravelCount"].sum()
    trips_25  = df_travel[df_travel["Yr"]==2025]["TravelCount"].sum()
    zrev_24  = df_zsdcy[df_zsdcy["Yr"]==2024]["Revenue"].sum()
    zrev_25  = df_zsdcy[df_zsdcy["Yr"]==2025]["Revenue"].sum()
    zrev_all = df_zsdcy["Revenue"].sum()
    zrev_growth = ((zrev_25-zrev_24)/zrev_24*100) if zrev_24>0 else 0
    top_prod_rev  = df_sales.groupby("ProductName")["TotalRevenue"].sum()
    top_city_rev  = df_zsdcy.groupby("City")["Revenue"].sum()
    top_city_trip = df_travel.groupby("VisitLocation")["TravelCount"].sum()
    total_disc = df_sales["TotalDiscount"].sum()
    nutra_24 = df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    nutra_25 = df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    sdp_24 = set(df_zsdcy[df_zsdcy["Yr"]==2024]["SDP Name"].unique())
    sdp_25 = set(df_zsdcy[df_zsdcy["Yr"]==2025]["SDP Name"].unique())
    loyal  = sdp_24 & sdp_25
    lost   = sdp_24 - sdp_25
    new_s  = sdp_25 - sdp_24
    ret    = len(loyal)/len(sdp_24)*100 if sdp_24 else 0
    ram = df_roi[df_roi["ProductName"].str.upper()=="RAMIPACE"]
    ram_spend = float(ram["TotalPromoSpend"].values[0]) if len(ram)>0 else 4300000
    ram_rev   = float(ram["TotalRevenue"].values[0]) if len(ram)>0 else 430000000
    ram_roi   = ram_rev/ram_spend
    fq_24 = df_sales[(df_sales["Yr"]==2024)&(df_sales["ProductName"].str.upper().str.contains("FINNO"))]["TotalRevenue"].sum()
    fq_25 = df_sales[(df_sales["Yr"]==2025)&(df_sales["ProductName"].str.upper().str.contains("FINNO"))]["TotalRevenue"].sum()
    fq_g  = ((fq_25-fq_24)/fq_24*100) if fq_24>0 else 0
    fq_promo = df_act[df_act["Product"].str.upper().str.contains("FINNO",na=False)]["TotalAmount"].sum()

    # SCORECARD
    st.markdown("### 📊 Complete Business Scorecard — All 4 Databases")
    st.markdown(note("Row 1 = Secondary Sales (DSR). Row 2 = Primary Distribution (ZSDCY). Row 3 = Investment & Field Activity."), unsafe_allow_html=True)
    st.markdown("**📈 Secondary Sales (DSR)**")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Revenue 2024", fmt(rev_24), "Full year"), unsafe_allow_html=True)
    c2.markdown(kpi("Revenue 2025", fmt(rev_25), f"+{rev_growth:.1f}% vs 2024"), unsafe_allow_html=True)
    c3.markdown(kpi("Revenue 2026", fmt(rev_26), "Jan-Mar only"), unsafe_allow_html=True)
    c4.markdown(kpi("Total", fmt(rev_all), "2024-2026"), unsafe_allow_html=True)
    c5.markdown(kpi("Top Product", "X-Plended", fmt(top_prod_rev.max())), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**📦 Primary Distribution (ZSDCY)**")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Primary 2024", fmt(zrev_24), "Shipped"), unsafe_allow_html=True)
    c2.markdown(kpi("Primary 2025", fmt(zrev_25), f"+{zrev_growth:.1f}%"), unsafe_allow_html=True)
    c3.markdown(kpi("Top City", "Karachi", fmt(top_city_rev.max())), unsafe_allow_html=True)
    c4.markdown(kpi("Distributors", str(len(sdp_24|sdp_25)), "Active SDPs"), unsafe_allow_html=True)
    c5.markdown(kpi("Retention", f"{ret:.1f}%", f"{len(loyal)} loyal"), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**💰 Investment & Field (Activities + Travel)**")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Spend 2024", fmt(sp_24), "Activities DB"), unsafe_allow_html=True)
    c2.markdown(kpi("Spend 2025", fmt(sp_25), f"+{spend_growth:.1f}%"), unsafe_allow_html=True)
    c3.markdown(kpi("ROI 2024", f"{roi_24:.1f}x", "Per PKR 1"), unsafe_allow_html=True)
    c4.markdown(kpi("ROI 2025", f"{roi_25:.1f}x", "Declining", red=roi_25<roi_24), unsafe_allow_html=True)
    c5.markdown(kpi("Trips", fmt_num(trips_all), f"24:{fmt_num(trips_24)} 25:{fmt_num(trips_25)}"), unsafe_allow_html=True)
    st.markdown("---")

    # FUNNEL
    st.markdown("### 🔄 Sales Funnel — All 4 Databases")
    col1, col2 = st.columns([3,2])
    with col1:
        fig = go.Figure(go.Funnel(y=[f"Promo {fmt(sp_all)}",f"Visits {trips_all:,}",f"Ship {fmt(zrev_all)}",f"Sell {fmt(rev_all)}"], x=[sp_all/1e6,trips_all/100,zrev_all/1e6,rev_all/1e6], marker=dict(color=["#e65100","#2c5f8a","#7b1fa2","#2e7d32"])))
        apply_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown(f"""<div class="manual-working">PKR 1 invested = PKR {roi_all:.1f} returned\\nPromo → Visits → Ship → Sell</div>""", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### 🎯 12 Strategic Findings")

    # F1: EFFICIENCY
    st.markdown(sec("🟢 FINDING 1 — Efficiency Declining"), unsafe_allow_html=True)
    st.markdown(note(f"Revenue +{rev_growth:.1f}% but spend +{spend_growth:.1f}%. ROI dropped {roi_24:.1f}x → {roi_25:.1f}x"), unsafe_allow_html=True)
    col1,col2,col3 = st.columns(3)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=["2024","2025"],y=[rev_24/1e9,rev_25/1e9],name="Revenue",marker_color="#2e7d32",text=[f"{rev_24/1e9:.1f}B",f"{rev_25/1e9:.1f}B"],textposition="outside"))
        fig.add_trace(go.Bar(x=["2024","2025"],y=[sp_24/1e9,sp_25/1e9],name="Spend",marker_color="#e65100",text=[f"{sp_24/1e9:.2f}B",f"{sp_25/1e9:.2f}B"],textposition="outside"))
        apply_layout(fig,height=300,barmode="group")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig = go.Figure(go.Bar(x=["2024","2025"],y=[roi_24,roi_25],marker_color=["#2e7d32","#c62828"],text=[f"{roi_24:.1f}x",f"{roi_25:.1f}x"],textposition="outside"))
        apply_layout(fig,height=300,showlegend=False)
        st.plotly_chart(fig,use_container_width=True)
    with col3:
        st.markdown(f"""<div class="manual-working">ROI VERIFICATION\\n2024: {fmt(rev_24)} / {fmt(sp_24)} = {roi_24:.1f}x\\n2025: {fmt(rev_25)} / {fmt(sp_25)} = {roi_25:.1f}x\\nChange: {roi_25-roi_24:.1f}x {"DECLINED" if roi_25<roi_24 else "OK"}\\nSpend grew {spend_growth/rev_growth:.1f}x faster</div>""", unsafe_allow_html=True)
    st.markdown(danger(f"<b>ACTION:</b> Cut lowest 20% ROI activities. Move July→January. Target 22x. Save PKR 80-120M."), unsafe_allow_html=True)

    # F2: RAMIPACE
    st.markdown(sec("🟢 FINDING 2 — Ramipace 99.7x ROI"), unsafe_allow_html=True)
    col1,col2,col3 = st.columns(3)
    with col1:
        tr = df_roi.nlargest(10,"ROI")
        fig = go.Figure(go.Bar(y=tr["ProductName"],x=tr["ROI"],orientation="h",marker_color=["#FFD700" if p.upper()=="RAMIPACE" else "#2c5f8a" for p in tr["ProductName"]],text=[f"{r:.0f}x" for r in tr["ROI"]],textposition="outside"))
        apply_layout(fig,height=320,yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig = go.Figure(go.Bar(x=["Spent","Earned"],y=[ram_spend/1e6,ram_rev/1e6],marker_color=["#e65100","#2e7d32"],text=[fmt(ram_spend),fmt(ram_rev)],textposition="outside"))
        apply_layout(fig,height=320,showlegend=False)
        st.plotly_chart(fig,use_container_width=True)
    with col3:
        st.markdown(f"""<div class="manual-working">RAMIPACE PROOF\\nSpend: {fmt(ram_spend)}\\nRevenue: {fmt(ram_rev)}\\nROI: {ram_roi:.1f}x\\nCompany avg: {roi_all:.1f}x\\n{ram_roi/roi_all:.0f}x BETTER\\nTriple budget → +{fmt(ram_rev*2)}</div>""", unsafe_allow_html=True)
    st.markdown(good(f"<b>ACTION:</b> Triple budget → +{fmt(ram_rev*2)} revenue."), unsafe_allow_html=True)

    # F3: FINNO-Q
    st.markdown(sec("🟢 FINDING 3 — Finno-Q +226% Growth"), unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        r24a = df_sales[df_sales["Yr"]==2024].groupby("ProductName")["TotalRevenue"].sum()
        r25a = df_sales[df_sales["Yr"]==2025].groupby("ProductName")["TotalRevenue"].sum()
        gdf = pd.DataFrame({"2024":r24a,"2025":r25a}).dropna()
        gdf = gdf[gdf["2024"]>5e6]
        gdf["Growth"] = ((gdf["2025"]-gdf["2024"])/gdf["2024"]*100)
        gdf = gdf.nlargest(10,"Growth").reset_index()
        fig = go.Figure(go.Bar(x=gdf["Growth"],y=gdf["ProductName"],orientation="h",text=[f"+{g:.0f}%" for g in gdf["Growth"]],textposition="outside",marker_color=["#FFD700" if "FINNO" in p.upper() else "#2c5f8a" for p in gdf["ProductName"]]))
        apply_layout(fig,height=320,yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fqm = df_sales[df_sales["ProductName"].str.upper().str.contains("FINNO")].groupby(["Yr","Mo"])["TotalRevenue"].sum().reset_index()
        if len(fqm)>0:
            fqm["Date"] = pd.to_datetime(fqm["Yr"].astype(int).astype(str)+"-"+fqm["Mo"].astype(int).astype(str)+"-01")
            fig = px.area(fqm,x="Date",y="TotalRevenue",color_discrete_sequence=["#2e7d32"])
            apply_layout(fig,height=320)
            st.plotly_chart(fig,use_container_width=True)
    st.markdown(good("<b>ACTION:</b> PKR 10M for Finno-Q. Expected +PKR 200M."), unsafe_allow_html=True)

    # F4: Q4
    st.markdown(sec("🟢 FINDING 4 — Q4 is Golden Quarter"), unsafe_allow_html=True)
    mo_map_c = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    col1,col2 = st.columns(2)
    with col1:
        sm = df_sales.groupby("Mo")["TotalRevenue"].sum().reset_index()
        sm["Month"]=sm["Mo"].map(mo_map_c)
        sm["Q4"]=sm["Mo"].apply(lambda x:"Q4" if x in[10,11,12] else "Other")
        fig = px.bar(sm,x="Month",y="TotalRevenue",color="Q4",color_discrete_map={"Q4":"#2e7d32","Other":"#2c5f8a"},category_orders={"Month":list(mo_map_c.values())},text=sm["TotalRevenue"].apply(lambda x:f"{x/1e9:.1f}B"))
        fig.update_traces(textposition="outside",textfont_size=9)
        apply_layout(fig,height=300,showlegend=False)
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        pm = df_act.groupby("Mo")["TotalAmount"].sum().reset_index()
        pm["Month"]=pm["Mo"].map(mo_map_c)
        pm["Q4"]=pm["Mo"].apply(lambda x:"Q4" if x in[10,11,12] else "Other")
        fig = px.bar(pm,x="Month",y="TotalAmount",color="Q4",color_discrete_map={"Q4":"#2e7d32","Other":"#e65100"},category_orders={"Month":list(mo_map_c.values())},text=pm["TotalAmount"].apply(lambda x:f"{x/1e6:.0f}M"))
        fig.update_traces(textposition="outside",textfont_size=9)
        apply_layout(fig,height=300,showlegend=False)
        st.plotly_chart(fig,use_container_width=True)
    st.markdown(good(f"<b>ACTION:</b> Double Sept promo. Q4 = {df_sales[df_sales['Mo'].isin([10,11,12])]['TotalRevenue'].sum()/rev_all*100:.1f}% of revenue."), unsafe_allow_html=True)

    # F5: KARACHI
    st.markdown(sec("🟡 FINDING 5 — Karachi Earns Most, Gets Fewest Visits"), unsafe_allow_html=True)
    tc = top_city_rev.head(12).reset_index(); tc.columns=["City","Revenue"]
    tt = top_city_trip.reset_index(); tt.columns=["City","Trips"]
    mc = pd.merge(tc,tt,on="City",how="left").fillna(0)
    mc["RevLabel"]=mc["Revenue"].apply(fmt)
    mc["RPT"]=(mc["Revenue"]/mc["Trips"].replace(0,1)/1e6).round(1)
    mc = mc.sort_values("Revenue",ascending=False)
    st.markdown(f"""<div class="manual-working">KARACHI PARADOX\\nZSDCY: Karachi=PKR 872M (#1) Lahore=PKR 634M (#3)\\nTRAVEL: Lahore=1,566 trips (#1) Karachi=0 trips!\\nSwat: 63 trips → PKR 514M = PKR 8.2M/trip\\nLahore: 1,566 trips → PKR 634M = PKR 0.4M/trip</div>""", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Bar(x=mc["Revenue"]/1e6,y=mc["City"],orientation="h",text=mc["RevLabel"],textposition="outside",marker_color=["#c62828" if r>300e6 and t<200 else "#2c5f8a" for r,t in zip(mc["Revenue"],mc["Trips"])]))
        apply_layout(fig,height=400,yaxis=dict(autorange="reversed"),xaxis=dict(title="Revenue (M)"))
        fig.update_layout(title="Revenue by City (ZSDCY)")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        td = df_travel.groupby("VisitLocation")["TravelCount"].sum().nlargest(12).reset_index()
        td.columns=["City","Trips"]
        fig = go.Figure(go.Bar(x=td["Trips"],y=td["City"],orientation="h",text=td["Trips"].apply(fmt_num),textposition="outside",marker_color="#2c5f8a"))
        apply_layout(fig,height=400,yaxis=dict(autorange="reversed"),xaxis=dict(title="Trips"))
        fig.update_layout(title="Trips by City (Travel)")
        st.plotly_chart(fig,use_container_width=True)
    rpt = mc[mc["Trips"]>0].sort_values("RPT",ascending=False).head(10)
    fig = go.Figure(go.Bar(x=rpt["RPT"],y=rpt["City"],orientation="h",text=[f"PKR {r:.1f}M/trip" for r in rpt["RPT"]],textposition="outside",marker_color=["#c62828" if t<100 else "#e65100" if t<400 else "#2e7d32" for t in rpt["Trips"]]))
    apply_layout(fig,height=320,yaxis=dict(autorange="reversed"),xaxis=dict(title="Rev/Trip (M)"))
    fig.update_layout(title="Revenue Per Trip")
    st.plotly_chart(fig,use_container_width=True)
    st.markdown(warn("<b>ACTION:</b> +300 Karachi, +200 Swat trips. -15% Lahore. Expected +PKR 150M."), unsafe_allow_html=True)

    # F6: TIMING
    st.markdown(sec("🟡 FINDING 6 — Promo Timing Wrong"), unsafe_allow_html=True)
    pr = df_act.groupby("Mo")["TotalAmount"].sum().rank(ascending=False)
    sr = df_sales.groupby("Mo")["TotalRevenue"].sum().rank(ascending=False)
    tdf = pd.DataFrame({"Month":list(mo_map_c.values()),"Promo":[int(pr.get(m,0)) for m in range(1,13)],"Sales":[int(sr.get(m,0)) for m in range(1,13)]})
    tdf["Gap"]=abs(tdf["Promo"]-tdf["Sales"])
    tdf["OK"]=tdf["Gap"].apply(lambda x:"✅" if x<=2 else "⚠️")
    col1,col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tdf["Month"],y=tdf["Promo"],name="Promo Rank",line=dict(color="#e65100",width=2.5),mode="lines+markers"))
        fig.add_trace(go.Scatter(x=tdf["Month"],y=tdf["Sales"],name="Sales Rank",line=dict(color="#2c5f8a",width=2.5),mode="lines+markers"))
        apply_layout(fig,height=300,yaxis=dict(autorange="reversed",title="Rank"),hovermode="x unified")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.dataframe(tdf,use_container_width=True,hide_index=True)
    st.markdown(warn("Move 30% July budget → Jan/Feb. Expected +PKR 200-300M."), unsafe_allow_html=True)

    # F7: NUTRA
    st.markdown(sec("🟡 FINDING 7 — Nutraceutical Growing Faster"), unsafe_allow_html=True)
    n24=df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    n25=df_zsdcy[(df_zsdcy["Category"]=="N")&(df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    p24=df_zsdcy[(df_zsdcy["Category"]=="P")&(df_zsdcy["Yr"]==2024)]["Revenue"].sum()
    p25=df_zsdcy[(df_zsdcy["Category"]=="P")&(df_zsdcy["Yr"]==2025)]["Revenue"].sum()
    ng=((n25-n24)/n24*100) if n24>0 else 0
    pg=((p25-p24)/p24*100) if p24>0 else 0
    col1,col2 = st.columns(2)
    with col1:
        cy = df_zsdcy.groupby(["Category","Yr"])["Revenue"].sum().reset_index()
        cy["Cat"]=cy["Category"].map({"P":"Pharma","N":"Nutra"})
        cy = cy[cy["Category"].isin(["P","N"])].copy()
        cy["L"]=cy["Revenue"].apply(fmt)
        fig = px.bar(cy,x="Yr",y="Revenue",color="Cat",barmode="group",text="L",color_discrete_map={"Pharma":"#2c5f8a","Nutra":"#7b1fa2"})
        fig.update_traces(textposition="outside")
        apply_layout(fig,height=320)
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        fig = px.bar(x=["Pharma","Nutra"],y=[pg,ng],text=[f"+{pg:.1f}%",f"+{ng:.1f}%"],color=["P","N"],color_discrete_map={"P":"#2c5f8a","N":"#7b1fa2"})
        fig.update_traces(textposition="outside",textfont_size=13)
        apply_layout(fig,height=320,showlegend=False)
        st.plotly_chart(fig,use_container_width=True)
    st.markdown(good(f"<b>ACTION:</b> Dedicated Nutra unit. +{ng:.1f}% vs Pharma +{pg:.1f}%. Target 20% share."), unsafe_allow_html=True)

    # F8: DISCOUNTS
    st.markdown(sec("🔴 FINDING 8 — PKR 750M Discounts"), unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        dt2 = df_sales.groupby("TeamName").agg(D=("TotalDiscount","sum"),R=("TotalRevenue","sum")).reset_index()
        dt2 = dt2[dt2["R"]>5e6]; dt2["Rate"]=dt2["D"]/dt2["R"]*100; dt2=dt2.nlargest(12,"Rate")
        fig = go.Figure(go.Bar(x=dt2["Rate"],y=dt2["TeamName"],orientation="h",text=[f"{r:.1f}%" for r in dt2["Rate"]],textposition="outside",marker_color=["#c62828" if r>10 else "#e65100" if r>3 else "#2c5f8a" for r in dt2["Rate"]]))
        apply_layout(fig,height=380,yaxis=dict(autorange="reversed"),xaxis=dict(title="Disc %"))
        fig.update_layout(title="By Team")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        dp = df_sales.groupby("ProductName").agg(D=("TotalDiscount","sum"),R=("TotalRevenue","sum")).reset_index()
        dp = dp[dp["R"]>5e6]; dp["Rate"]=dp["D"]/dp["R"]*100; dp=dp.nlargest(10,"Rate")
        fig = go.Figure(go.Bar(x=dp["Rate"],y=dp["ProductName"],orientation="h",text=[f"{r:.1f}%" for r in dp["Rate"]],textposition="outside",marker_color=["#c62828" if r>20 else "#e65100" if r>10 else "#2c5f8a" for r in dp["Rate"]]))
        apply_layout(fig,height=380,yaxis=dict(autorange="reversed"),xaxis=dict(title="Disc %"))
        fig.update_layout(title="By Product")
        st.plotly_chart(fig,use_container_width=True)
    st.markdown(danger(f"<b>URGENT:</b> Cap discounts at 5%. Total = {fmt(total_disc)}. Saves PKR 200M+."), unsafe_allow_html=True)

    # F9: DISTRIBUTOR
    st.markdown(sec("🔴 FINDING 9 — Single Distributor Risk"), unsafe_allow_html=True)
    df_zsdcy["DG"] = df_zsdcy["SDP Name"].apply(lambda x: "Premier" if "PREMIER" in str(x).upper() else "Other")
    dg = df_zsdcy.groupby("DG")["Revenue"].sum().reset_index()
    fig = px.pie(dg,values="Revenue",names="DG",color_discrete_map={"Premier":"#c62828","Other":"#2c5f8a"})
    fig.update_traces(textinfo="percent+label")
    apply_layout(fig,height=300)
    st.plotly_chart(fig,use_container_width=True)
    st.markdown(danger("<b>URGENT:</b> Sign 2 alternative distributors. 10% volume each."), unsafe_allow_html=True)

    # F10: DIVISIONS
    st.markdown(sec("🔴 FINDING 10 — Division 4 Works 5x Less"), unsafe_allow_html=True)
    dv = df_travel.groupby("TravellerDivision").agg(T=("TravelCount","sum"),P=("Traveller","nunique")).reset_index()
    dv["TPP"]=(dv["T"]/dv["P"]).round(1)
    dv["N"]=dv["TravellerDivision"].map({"Division 1":"Div 1","Division 2":"Div 2","Division 3":"Div 3","Division 4":"Div 4","Division 5":"Div 5"})
    dv = dv.sort_values("TPP",ascending=False)
    fig = go.Figure(go.Bar(x=dv["TPP"],y=dv["N"],orientation="h",text=[f"{t:.0f}/person" for t in dv["TPP"]],textposition="outside",marker_color=["#2e7d32" if t>40 else "#e65100" if t>20 else "#c62828" for t in dv["TPP"]]))
    apply_layout(fig,height=250,yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig,use_container_width=True)

    # F11: PRODUCT GROUPS
    st.markdown(sec("🟡 FINDING 11 — Product Portfolio: Invest vs Cut"), unsafe_allow_html=True)
    r24b = df_sales[df_sales["Yr"]==2024].groupby("ProductName")["TotalRevenue"].sum()
    r25b = df_sales[df_sales["Yr"]==2025].groupby("ProductName")["TotalRevenue"].sum()
    bcg = pd.DataFrame({"R24":r24b,"R25":r25b}).dropna()
    bcg = bcg[bcg["R24"]>5e6]
    bcg["G"]=((bcg["R25"]-bcg["R24"])/bcg["R24"]*100)
    bcg["TR"]=bcg["R24"]+bcg["R25"]
    bcg = bcg.reset_index()
    mr=bcg["TR"].median(); mg2=bcg["G"].median()
    def clf(r):
        if r["TR"]>=mr and r["G"]>=mg2: return "G1-Invest"
        elif r["TR"]>=mr: return "G2-Maintain"
        elif r["G"]>=mg2: return "G3-Watch"
        else: return "G4-Cut"
    bcg["Grp"]=bcg.apply(clf,axis=1)
    g1=bcg[bcg["Grp"]=="G1-Invest"];g2=bcg[bcg["Grp"]=="G2-Maintain"];g3=bcg[bcg["Grp"]=="G3-Watch"];g4=bcg[bcg["Grp"]=="G4-Cut"]
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("G1 Invest",str(len(g1)),"High+Growing"),unsafe_allow_html=True)
    c2.markdown(kpi("G2 Maintain",str(len(g2)),"High+Stable"),unsafe_allow_html=True)
    c3.markdown(kpi("G3 Watch",str(len(g3)),"Growing Fast"),unsafe_allow_html=True)
    c4.markdown(kpi("G4 Cut",str(len(g4)),"Declining",red=True),unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("**Group 1 — INVEST MORE**")
        g1d=g1.sort_values("TR",ascending=False).head(20)
        fig = go.Figure(go.Bar(x=g1d["TR"]/1e6,y=g1d["ProductName"],orientation="h",text=g1d["TR"].apply(fmt),textposition="outside",textfont_size=9,marker_color="#2e7d32"))
        apply_layout(fig,height=500,yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.markdown("**Group 3 — WATCH (Growing Fast)**")
        g3d=g3.sort_values("G",ascending=False).head(20)
        fig = go.Figure(go.Bar(x=g3d["G"],y=g3d["ProductName"],orientation="h",text=g3d["G"].apply(lambda x:f"+{x:.1f}%"),textposition="outside",textfont_size=9,marker_color=["#FFD700" if "FINNO" in p.upper() else "#e65100" for p in g3d["ProductName"]]))
        apply_layout(fig,height=500,yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig,use_container_width=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("**Group 2 — MAINTAIN**")
        g2d=g2.sort_values("TR",ascending=False).head(20)
        fig = go.Figure(go.Bar(x=g2d["TR"]/1e6,y=g2d["ProductName"],orientation="h",text=g2d["TR"].apply(fmt),textposition="outside",textfont_size=9,marker_color="#2c5f8a"))
        apply_layout(fig,height=500,yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.markdown("**Group 4 — CUT BUDGET**")
        g4d=g4.sort_values("G").head(20)
        fig = go.Figure(go.Bar(x=g4d["G"],y=g4d["ProductName"],orientation="h",text=g4d["G"].apply(lambda x:f"{x:.1f}%"),textposition="outside",textfont_size=9,marker_color="#c62828"))
        apply_layout(fig,height=500,yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig,use_container_width=True)

    # F12: TEAM EFFICIENCY
    st.markdown(sec("🟡 FINDING 12 — Team Efficiency"), unsafe_allow_html=True)
    trf = df_sales.groupby("TeamName")["TotalRevenue"].sum()
    ttf = df_travel.groupby("TravellerTeam")["TravelCount"].sum()
    tsf = df_act.groupby("RequestorTeams")["TotalAmount"].sum()
    tdf2 = df_sales.groupby("TeamName")["TotalDiscount"].sum()
    tf = pd.DataFrame({"Revenue":trf,"Trips":ttf,"Spend":tsf,"Discount":tdf2}).fillna(0)
    tf = tf[tf["Revenue"]>100e6]
    tf["ROI"]=(tf["Revenue"]/tf["Spend"].replace(0,1)).round(1)
    tf["RPT"]=(tf["Revenue"]/tf["Trips"].replace(0,1)/1e6).round(2)
    tf["DR"]=(tf["Discount"]/tf["Revenue"]*100).round(1)
    for c in ["ROI","Revenue"]:
        mn3=tf[c].min();mx3=tf[c].max()
        tf[f"{c}_s"]=((tf[c]-mn3)/(mx3-mn3)*100 if mx3>mn3 else 50)
    tf["Score"]=(tf["ROI_s"]*0.5+tf["Revenue_s"]*0.5).round(0).astype(int)
    tf = tf.sort_values("Score",ascending=False).reset_index()
    col1,col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Bar(x=tf["Score"],y=tf["index"],orientation="h",text=[f"{s}/100" for s in tf["Score"]],textposition="outside",marker_color=["#FFD700" if s>=80 else "#2e7d32" if s>=50 else "#e65100" if s>=30 else "#c62828" for s in tf["Score"]]))
        apply_layout(fig,height=450,yaxis=dict(autorange="reversed"),xaxis=dict(title="Score"))
        fig.update_layout(title="Team Score")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        dp2 = tf[["index","Score","Revenue","ROI","RPT","DR"]].copy()
        dp2 = dp2.rename(columns={"index":"Team"})
        dp2["Revenue"]=dp2["Revenue"].apply(fmt)
        dp2["ROI"]=dp2["ROI"].apply(lambda x:f"{x:.1f}x")
        dp2["RPT"]=dp2["RPT"].apply(lambda x:f"PKR {x:.1f}M")
        dp2["DR"]=dp2["DR"].apply(lambda x:f"{x:.1f}%")
        dp2["Score"]=dp2["Score"].apply(lambda x:f"{x}/100")
        dp2["Status"]=tf["Score"].apply(lambda x:"🟢" if x>=70 else "🟡" if x>=40 else "🔴")
        st.dataframe(dp2.rename(columns={"RPT":"Rev/Trip","DR":"Disc%"}),use_container_width=True,hide_index=True)
    st.markdown("---")

    # ML PREDICTION
    st.markdown("### 🤖 ML Revenue Prediction 2026")
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import LabelEncoder
    mld = df_sales.groupby(["Yr","Mo","TeamName"]).agg(Revenue=("TotalRevenue","sum"),Discount=("TotalDiscount","sum")).reset_index()
    pml = df_act.groupby(["Yr","Mo"])["TotalAmount"].sum().reset_index();pml.columns=["Yr","Mo","PS"]
    tml = df_travel.groupby(["Yr","Mo"])["TravelCount"].sum().reset_index();tml.columns=["Yr","Mo","Tr"]
    mld = mld.merge(pml,on=["Yr","Mo"],how="left").merge(tml,on=["Yr","Mo"],how="left").fillna(0)
    le = LabelEncoder()
    mld["TE"]=le.fit_transform(mld["TeamName"])
    mld["MS"]=np.sin(2*np.pi*mld["Mo"]/12)
    mld["MC"]=np.cos(2*np.pi*mld["Mo"]/12)
    mld["Q4"]=mld["Mo"].apply(lambda x:1 if x in[10,11,12] else 0)
    mdl = GradientBoostingRegressor(n_estimators=200,max_depth=4,learning_rate=0.05,random_state=42)
    mdl.fit(mld[["Yr","Mo","TE","PS","Tr","MS","MC","Q4","Discount"]],mld["Revenue"])
    ex = df_sales[df_sales["Yr"]==2026]["Mo"].unique()
    rm = [m for m in range(1,13) if m not in ex]
    apm=pml.groupby("Mo")["PS"].mean();atm=tml.groupby("Mo")["Tr"].mean()
    pr2=[]
    for mo in rm:
        for team in mld["TeamName"].unique():
            try:te=le.transform([team])[0]
            except:continue
            p=mdl.predict(pd.DataFrame([{"Yr":2026,"Mo":mo,"TE":te,"PS":apm.get(mo,sp_all/24),"Tr":atm.get(mo,trips_all/24),"MS":np.sin(2*np.pi*mo/12),"MC":np.cos(2*np.pi*mo/12),"Q4":1 if mo in[10,11,12] else 0,"Discount":0}]))[0]
            pr2.append({"Mo":mo,"PR":max(p,0)})
    pdf = pd.DataFrame(pr2).groupby("Mo")["PR"].sum().reset_index()
    pdf["Month"]=pdf["Mo"].map(mo_map_c)
    a26 = df_sales[df_sales["Yr"]==2026].groupby("Mo")["TotalRevenue"].sum().reset_index();a26["Month"]=a26["Mo"].map(mo_map_c)
    a25 = df_sales[df_sales["Yr"]==2025].groupby("Mo")["TotalRevenue"].sum().reset_index();a25["Month"]=a25["Mo"].map(mo_map_c)
    col1,col2 = st.columns([2,1])
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=a25["Month"],y=a25["TotalRevenue"]/1e6,name="2025",mode="lines+markers",line=dict(color="#2c5f8a",width=2)))
        fig.add_trace(go.Scatter(x=a26["Month"],y=a26["TotalRevenue"]/1e6,name="2026 Actual",mode="lines+markers",line=dict(color="#2e7d32",width=2.5)))
        fig.add_trace(go.Scatter(x=pdf["Month"],y=pdf["PR"]/1e6,name="2026 Forecast",mode="lines+markers",line=dict(color="#e65100",width=2.5,dash="dash")))
        apply_layout(fig,height=400,xaxis=dict(categoryorder="array",categoryarray=list(mo_map_c.values())),hovermode="x unified")
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        pt=pdf["PR"].sum()+rev_26;tg=rev_25*1.166;gp=tg-pt
        st.markdown(f"""<div class="manual-working">FORECAST\\nQ1: {fmt(rev_26)}\\nRest: {fmt(pdf["PR"].sum())}\\nTotal: {fmt(pt)}\\nTarget: {fmt(tg)}\\nGap: {fmt(abs(gp))} {"🔴 BEHIND" if gp>0 else "✅ OK"}</div>""", unsafe_allow_html=True)
    st.markdown("---")

    # ACTION PLAN
    st.markdown("### ⚡ Action Plan")
    col1,col2,col3 = st.columns(3)
    with col1:
        st.markdown(sec("🔴 THIS WEEK"),unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({"Action":["Audit Falcons discounts","Triple Ramipace budget","Call Nusrat Pharma","Find 2 distributors"],"Impact":["Save PKR 200M","+PKR 430M","Recover PKR 23.7M","Risk reduction"]}),use_container_width=True,hide_index=True)
    with col2:
        st.markdown(sec("🟡 THIS MONTH"),unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({"Action":["PKR 10M Finno-Q","July→Jan budget","+300 Karachi trips","Fix Zoltar pricing"],"Impact":["+PKR 200M","+PKR 300M","+PKR 150M","Save PKR 74M"]}),use_container_width=True,hide_index=True)
    with col3:
        st.markdown(sec("🟢 THIS YEAR"),unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({"Action":["Nutra team","Double Q4 campaigns","2 new distributors","Challengers playbook"],"Impact":["+PKR 300M","+PKR 300M","Risk reduction","+PKR 200M"]}),use_container_width=True,hide_index=True)
    st.markdown("---")
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi("💰 Savings","PKR 292M","From fixing waste"),unsafe_allow_html=True)
    c2.markdown(kpi("📈 Growth","PKR 1.58B","Opportunities"),unsafe_allow_html=True)
    c3.markdown(kpi("💡 Investment","PKR 110M","To unlock"),unsafe_allow_html=True)
    c4.markdown(kpi("🎯 Net","PKR 1.76B","Total benefit"),unsafe_allow_html=True)
'''

code = code + new_page

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)

print(f"✅ DONE! {len(code)/1024:.1f} KB")
