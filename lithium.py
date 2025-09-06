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
