import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Quant Syndicate AI Terminal", layout="wide")
st.title("🎯 Quant Syndicate AI Terminal")

if os.path.exists("ev_log.csv"):
    try:
        df = pd.read_csv("ev_log.csv")
        
        # FIX: If the CSV is empty or corrupted, create a dummy row so it doesn't crash
        if df.empty or 'Sport' not in df.columns:
            st.warning("📡 Waiting for fresh data from iMac...")
        else:
            # 1. Sidebar Filters
            st.sidebar.header("🕹️ Terminal Controls")
            selected_sports = st.sidebar.multiselect("Sports:", df['Sport'].unique(), default=df['Sport'].unique())
            
            # 2. Filter Data
            filtered_df = df[df['Sport'].isin(selected_sports)]

            # 3. High-Value Section
            st.subheader("🚀 Elite Syndicate Signals")
            if 'Verdict' in filtered_df.columns:
                top_plays = filtered_df[filtered_df['Verdict'].isin(['💎', '🥇'])]
                st.dataframe(top_plays, use_container_width=True, hide_index=True)

            # 4. Global Board
            st.subheader("📊 Global Board")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Waiting for data synchronization... ({e})")
else:
    st.warning("⚠️ ev_log.csv not found. Please run the engine on your iMac.")