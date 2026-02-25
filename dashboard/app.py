import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from analytics.metrics import (
    get_daily_counts,
    get_growth_vs_yesterday,
    get_top_authors,
    get_run_metrics,
    get_peak_day,
    get_all_runs,
)

from analytics.text_analysis import (
    get_top_keywords,
    get_trending_topics,
)

st.set_page_config(page_title="arXiv AI Research Intelligence", layout="wide")

st.title("📊 arXiv AI Research Intelligence Dashboard")

# ============================================================
# SECTION 1 — EXECUTIVE KPIs
# ============================================================

growth = get_growth_vs_yesterday()
run_metrics = get_run_metrics()
peak_day = get_peak_day()

col1, col2, col3 = st.columns(3)

with col1:
    if growth:
        st.metric(
            "📈 Growth vs Yesterday",
            f"{growth['percentage_change']}%",
            delta=f"{growth['latest_count'] - growth['previous_count']} papers",
        )
    else:
        st.metric("📈 Growth vs Yesterday", "N/A")

with col2:
    st.metric("⚙ Avg Papers per Successful Run", run_metrics["avg_per_run"])

with col3:
    if peak_day:
        st.metric("🔥 Peak Publishing Day", peak_day[0], delta=f"{peak_day[1]} papers")
    else:
        st.metric("🔥 Peak Publishing Day", "N/A")

st.divider()

# ============================================================
# SECTION 2 — DAILY RESEARCH TREND
# ============================================================

st.subheader("📈 Daily Submission Trend")

daily_data = get_daily_counts()
df_daily = pd.DataFrame(daily_data, columns=["Date", "Paper Count"])

if not df_daily.empty:
    df_daily["Date"] = pd.to_datetime(df_daily["Date"])
    df_daily = df_daily.sort_values("Date")

    st.line_chart(df_daily.set_index("Date"))

    st.subheader("📅 Detailed Daily Metrics")

    df_daily["Previous Day"] = df_daily["Paper Count"].shift(1)
    df_daily["% Change"] = (
        (df_daily["Paper Count"] - df_daily["Previous Day"]) / df_daily["Previous Day"]
    ) * 100

    st.dataframe(df_daily)
else:
    st.info("No daily data available.")

st.divider()

# ============================================================
# SECTION 3 — RUN HEALTH ANALYTICS
# ============================================================

st.subheader("⚙ Scrape Run Health")

status_data = run_metrics["status_counts"]
df_status = pd.DataFrame(status_data, columns=["Status", "Count"])

if not df_status.empty:
    st.bar_chart(df_status.set_index("Status"))
else:
    st.info("No run data available.")

st.divider()


st.divider()

# ============================================================
# SECTION 4 — DETAILED RUN HISTORY
# ============================================================

st.subheader("📋 Detailed Scrape Run History")

runs = get_all_runs()

df_runs = pd.DataFrame(
    runs,
    columns=[
        "Run ID",
        "Started At",
        "Status",
        "Total Records Inserted",
        "Error Message",
    ],
)

if not df_runs.empty:
    st.dataframe(df_runs)
else:
    st.info("No run history available.")


# ============================================================
# SECTION 5 — AUTHOR INTELLIGENCE
# ============================================================

st.subheader("🏆 Top Authors by Paper Count")

top_authors = get_top_authors()

df_authors = pd.DataFrame(top_authors, columns=["Author", "Paper Count"])

if not df_authors.empty:
    st.bar_chart(df_authors.set_index("Author"))
else:
    st.info("No author data available.")

st.divider()

# ============================================================
# SECTION 6 — RESEARCH INTELLIGENCE
# ============================================================

st.subheader("🔤 Top Keywords in Abstracts")

keywords = get_top_keywords()

df_keywords = pd.DataFrame(keywords, columns=["Keyword", "Count"])

if not df_keywords.empty:
    st.bar_chart(df_keywords.set_index("Keyword"))
else:
    st.info("No keyword data available.")

st.divider()

st.subheader("🔥 Trending Research Topics")

trending = get_trending_topics()

if trending and "top_trending" in trending:
    df_trending = pd.DataFrame(
        trending["top_trending"],
        columns=["Keyword", "Latest Count", "Previous Count", "Growth %"],
    )
    st.dataframe(df_trending)
else:
    st.info("Not enough data to compute trending topics.")
