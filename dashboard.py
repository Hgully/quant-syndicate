import streamlit as st
import pandas as pd

# Page config
st.set_page_config(page_title="Quant Syndicate Terminal", layout="wide", page_icon="🎯")

st.title("🎯 Quant Syndicate AI Terminal")
st.markdown("---")

# 1. Load the Database
@st.cache_data(ttl=60) # Refreshes data every 60 seconds
def load_data():
    try:
        return pd.read_csv("ev_log.csv")
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found in ev_log.csv. Run the engine first.")
else:
    # 2. Top-Level Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Active Games", len(df))
    col2.metric("Active Sports", df['Sport'].nunique())
    
    # Count how many +EV plays we found (excluding the ❌ PASS)
    actionable_plays = len(df[~df['QES Rating'].str.contains("❌")])
    col3.metric("Actionable +EV Plays", actionable_plays)

    st.markdown("### 🎛️ Terminal Filters")
    
    # 3. Interactive Filters
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # Let the user pick which sports to view
        sport_list = df['Sport'].unique().tolist()
        selected_sports = st.multiselect("Select Sports:", sport_list, default=sport_list)
        
    with filter_col2:
        # Let the user filter out the trash bets
        hide_passes = st.checkbox("Hide '❌ PASS' Ratings (Show Only +EV Plays)")

    # 4. Apply Filters
    filtered_df = df[df['Sport'].isin(selected_sports)]
    if hide_passes:
        filtered_df = filtered_df[~filtered_df['QES Rating'].str.contains("❌")]

    # 5. Display the Cleaned Data
    st.markdown("### 📊 Global Slate")
    
    # Use st.dataframe for an interactive, sortable table
    st.dataframe(
        filtered_df, 
        use_container_width=True,
        hide_index=True
    )