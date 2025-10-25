import streamlit as st
import feedparser
import pandas as pd
import plotly.express as px
import tldextract
from datetime import datetime

# -------------------------------
# 1. Sidebar Options
# -------------------------------
st.set_page_config(page_title="Lithium Battery News Monitor", layout="wide")

st.title("🔋 Lithium Battery News Dashboard")
st.markdown("This dashboard monitors **Lithium Battery supply risks** from global news feeds.")

# Choose commodity (extendable later)
commodity = st.sidebar.selectbox("Select Commodity", ["Lithium", "Rubber", "Nickel", "Cobalt"])

# Keywords for filtering
keywords = ["tariff", "ban", "strike", "disruption", "policy", "shortage"]

# -------------------------------
# 2. Fetch News Data
# -------------------------------
rss_url = f"https://news.google.com/rss/search?q={commodity}+export+disruption+OR+{commodity}+shortage+OR+{commodity}+tariff"
feed = feedparser.parse(rss_url)

# Country & Region mappings
countries = ["China", "Australia", "Chile", "Argentina", "Bolivia", "India", "Indonesia", "US", "Canada"]
region_map = {
    "China": "Asia",
    "Australia": "Oceania",
    "Chile": "South America",
    "Argentina": "South America",
    "Bolivia": "South America",
    "India": "Asia",
    "Indonesia": "Asia",
    "US": "North America",
    "Canada": "North America",
    "Unknown": "Other"
}

domain_country_map = {
    "chinadaily": "China",
    "scmp": "China",
    "theaustralian": "Australia",
    "smh": "Australia",
    "reuters": "US",
    "bloomberg": "US",
    "bnamericas": "Chile"
}

# Process news
data = []
for entry in feed.entries:
    title = entry.title
    link = entry.link
    published = entry.published if "published" in entry else None
    risk = "High" if any(word.lower() in title.lower() for word in keywords) else "Normal"

    # Detect country
    detected_country = "Unknown"
    for c in countries:
        if c.lower() in title.lower():
            detected_country = c
            break
    if detected_country == "Unknown":
        domain = tldextract.extract(link).domain
        detected_country = domain_country_map.get(domain, "Unknown")

    region = region_map.get(detected_country, "Other")

    data.append([title, link, published, risk, detected_country, region])

df = pd.DataFrame(data, columns=["Title", "Link", "Published", "Risk", "Country", "Region"])

# -------------------------------
# 3. Charts
# -------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📊 Risk Summary")
    fig_risk = px.bar(df.groupby("Risk").size().reset_index(name="Count"),
                      x="Risk", y="Count", color="Risk")
    st.plotly_chart(fig_risk, use_container_width=True)

with col2:
    st.subheader("🌍 News by Country")
    fig_country = px.bar(df.groupby("Country").size().reset_index(name="Count"),
                         x="Country", y="Count", color="Country")
    st.plotly_chart(fig_country, use_container_width=True)

with col3:
    st.subheader("🗺️ News by Region")
    fig_region = px.pie(df, names="Region", title="Region Breakdown")
    st.plotly_chart(fig_region, use_container_width=True)

# -------------------------------
# 4. Interactive News Table
# -------------------------------
st.subheader("📰 Latest News Articles")

risk_filter = st.selectbox("Filter by Risk", ["All"] + df["Risk"].unique().tolist())
country_filter = st.selectbox("Filter by Country", ["All"] + df["Country"].unique().tolist())

filtered = df.copy()
if risk_filter != "All":
    filtered = filtered[filtered["Risk"] == risk_filter]
if country_filter != "All":
    filtered = filtered[filtered["Country"] == country_filter]

for _, row in filtered.iterrows():
    st.markdown(f"- [{row['Title']}]({row['Link']})  \n  📅 {row['Published']} | 🏳️ {row['Country']} | ⚠️ {row['Risk']}")
# -------------------------------
# 5. Export Disruption Data for MILP
# -------------------------------
st.subheader("⚙️ Export Disruption Summary for MILP Optimization")

# Default impact values by risk level
risk_defaults = {
    "High":  {"LT_add_periods": 1, "Cap_mult": 0.6, "Sea_block": 0, "Air_block": 0, "Trans_cost_add": 2.0},
    "Medium":{"LT_add_periods": 0, "Cap_mult": 0.8, "Sea_block": 0, "Air_block": 0, "Trans_cost_add": 1.0},
    "Low":   {"LT_add_periods": 0, "Cap_mult": 0.9, "Sea_block": 0, "Air_block": 0, "Trans_cost_add": 0.5},
    "Normal": {"LT_add_periods": 0, "Cap_mult": 1.0, "Sea_block": 0, "Air_block": 0, "Trans_cost_add": 0.0}
}

# Prepare disruption summary per country
if not df.empty:
    disruption_rows = []
    today = datetime.now()
    month_start = today.replace(day=1).strftime("%Y-%m-%d")
    month_end = today.replace(day=28).strftime("%Y-%m-%d")

    for country, group in df.groupby("Country"):
        # Identify most severe risk level
        risk_levels = ["Normal", "Low", "Medium", "High"]
        group_risks = group["Risk"].unique().tolist()
        top_risk = max(group_risks, key=lambda r: risk_levels.index(r)) if group_risks else "Normal"

        impact = risk_defaults.get(top_risk, risk_defaults["Normal"])

        disruption_rows.append({
            "Country": country,
            "Risk": top_risk,
            "Start": month_start,
            "End": month_end,
            "LT_add_periods": impact["LT_add_periods"],
            "Cap_mult": impact["Cap_mult"],
            "Sea_block": impact["Sea_block"],
            "Air_block": impact["Air_block"],
            "Trans_cost_add": impact["Trans_cost_add"]
        })

    disruption_df = pd.DataFrame(disruption_rows)
    st.dataframe(disruption_df)

    # Download button for MILP
    st.download_button(
        label="⬇️ Download disruptions.csv for MILP Model",
        data=disruption_df.to_csv(index=False).encode("utf-8"),
        file_name="disruptions.csv",
        mime="text/csv"
    )
else:
    st.warning("No disruption data available yet — try refreshing the RSS feed.")
