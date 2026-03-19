import streamlit as st
import pandas as pd
import os

# Set Page Config
st.set_page_config(page_title="Quant Syndicate AI Terminal", layout="wide")

st.title("🎯 Quant Syndicate AI Terminal")
st.markdown("---")

# 1. Load the Data
if os.path.exists("ev_log.csv"):
    df = pd.read_csv("ev_log.csv")
    
    # 2. Sidebar Filters
    st.sidebar.header("🕹️ Terminal Controls")
    
    # Sport Filter
    if 'Sport' in df.columns:
        all_sports = sorted(df['Sport'].unique().tolist())
        selected_sports = st.sidebar.multiselect("Filter by Sport:", all_sports, default=all_sports)
    
    # Market Filter
    if 'Market' in df.columns:
        all_markets = sorted(df['Market'].unique().tolist())
        selected_markets = st.sidebar.multiselect("Filter by Market:", all_markets, default=all_markets)

    # Filtering Logic
    mask = (df['Sport'].isin(selected_sports)) & (df['Market'].isin(selected_markets))
    filtered_df = df[mask]

    # 3. High-Value Alert Section
    st.subheader("🚀 Elite Syndicate Signals")
    if 'Verdict' in filtered_df.columns:
        top_plays = filtered_df[filtered_df['Verdict'].isin(['💎', '🥇'])]
        if not top_plays.empty:
            st.table(top_plays) # Using st.table for maximum stability
        else:
            st.info("Scanning board for 💎 Max or 🥇 Strong plays...")

    st.markdown("---")

    # 4. Global Board
    st.subheader("📊 Global Board")
    
    column_order = ["Market", "Selection", "Win Prob", "Fair Odds", "Cur", "Edge (EV)", "QES", "Verdict", "Rating", "Sport"]
    actual_cols = [c for c in column_order if c in filtered_df.columns]
    
    # Display the interactive table
    st.dataframe(filtered_df[actual_cols], use_container_width=True, hide_index=True)

else:
    st.warning("⚠️ No data found. Run the engine on your iMac.")

st.sidebar.markdown("---")
st.sidebar.write("✅ System Status: **ACTIVE**")