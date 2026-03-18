import streamlit as st
import pandas as pd
import numpy as np
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Quant Syndicate Terminal", page_icon="🎯", layout="wide")

# --- THE AUTO-SYNC DATA LOADER ---
@st.cache_data(ttl=5) # Forces a check every 5 seconds
def load_data():
    # THE RAW URL (Ensure this matches your repo name exactly)
    RAW_URL = "https://raw.githubusercontent.com/hgully/quant-syndicate/main/ev_log.csv"
    
    try:
        # THE CACHE BUSTER: Adds a unique timestamp to the URL so GitHub can't serve old data
        t = time.time()
        df = pd.read_csv(f"{RAW_URL}?nocache={t}")
        
        # SAFETY: Add missing columns if they aren't in the CSV yet
        if 'Result' not in df.columns: df['Result'] = "Pending"
        if 'QES' not in df.columns: df['QES'] = 0.0
            
        return df
    except Exception as e:
        st.error(f"📡 Cloud Syncing... (Attempting to reach GitHub)")
        return pd.DataFrame()

# --- THE UI ---
st.title("🎯 Quant Syndicate AI Terminal")

df = load_data()

if not df.empty:
    st.header("System Performance Tally")
    
    # Only calculate wins for graded games
    graded = df[df['Result'] != "Pending"]
    if not graded.empty:
        wins = len(graded[graded['Result'].str.contains("Won", na=False)])
        losses = len(graded[graded['Result'].str.contains("Lost", na=False)])
        wr = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        st.success(f"Current Win Rate: {wr:.1f}%")
    else:
        st.info("📡 All current plays are 'Pending'. No graded results to show yet.")

    st.divider()
    st.subheader("Current Master Slate")
    
    # This displays your new 7-sport slate
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.caption(f"Last Cloud Sync: {time.strftime('%H:%M:%S')} (v.{int(time.time())})")
else:
    st.warning("Database currently empty. Run your Mac script to push the new slate!")