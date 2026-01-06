# dashboard.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# --- Configuration ---
st.set_page_config(layout="wide", page_title="Scheme Savvy Analytics")
DB_PATH = 'analytics.db'

# --- Data Loading ---
@st.cache_data
def load_data():
    """Loads data from the SQLite database and caches it."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM searches", conn)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # Extract date for time-series analysis
        df['date'] = df['timestamp'].dt.date
        return df
    except Exception as e:
        st.error(f"Could not load data from analytics.db. Have you run process_logs.py? Error: {e}")
        return pd.DataFrame()

df = load_data()

# --- Dashboard UI ---
st.title("Scheme Savvy - BDA Dashboard")
st.markdown("Analyzing user search patterns to improve our service.")

if df.empty:
    st.warning("No analytics data found.")
else:
    # --- Key Performance Indicators (KPIs) ---
    st.header("Key Metrics")
    total_searches = len(df)
    total_fallbacks = df['web_fallback'].sum()
    fallback_rate = (total_fallbacks / total_searches) * 100 if total_searches > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Searches", f"{total_searches}")
    col2.metric("Web Fallbacks", f"{total_fallbacks}")
    col3.metric("Fallback Rate", f"{fallback_rate:.2f}%")

    st.divider()

    # --- Visualizations ---
    st.header("Search Insights")
    col1, col2 = st.columns(2)

    with col1:
        # What are the most popular search terms?
        st.subheader("Top 20 Most Searched Terms")
        top_queries = df['query'].str.lower().value_counts().nlargest(20)
        st.dataframe(top_queries)
        
        # Which categories are most searched?
        st.subheader("Searches by Category")
        category_counts = df['category_context'].value_counts().nlargest(10)
        fig_cat = px.bar(category_counts, x=category_counts.index, y=category_counts.values, labels={'x':'Category', 'y':'Count'}, title="Top 10 Searched Categories")
        st.plotly_chart(fig_cat)

    with col2:
        # Which searches are failing? (Most actionable insight!)
        st.subheader("Top Searches with Zero Local Results")
        zero_results_df = df[df['local_results'] == 0]
        zero_results_queries = zero_results_df['query'].str.lower().value_counts().nlargest(20)
        st.dataframe(zero_results_queries)
        st.info("Actionable Insight: These terms represent gaps in our database. Consider adding schemes that match these queries.")

    st.divider()

    # --- Time-Series Analysis ---
    st.header("Usage Over Time")
    searches_per_day = df.groupby('date').size().reset_index(name='count')
    fig_time = px.line(searches_per_day, x='date', y='count', title="Total Searches Per Day", markers=True)
    st.plotly_chart(fig_time, use_container_width=True)