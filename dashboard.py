import streamlit as st
import pandas as pd
import numpy as np
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Quant Syndicate Terminal", page_icon="🎯", layout="wide")

# --- THE AUTO-SYNC DATA LOADER ---
@st.cache_data(ttl=5)
def load_data():
    RAW_URL = "https://raw.githubusercontent.com/hgully/quant-syndicate/main/ev_log.csv"
    try:
        t = time.time()
        df = pd.read_csv(f"{RAW_URL}?nocache={t}")
        if 'Result' not in df.columns: df['Result'] = "Pending"
        if 'QES' not in df.columns: df['QES'] = 0.0
        return df
    except Exception as e:
        return pd.DataFrame()

# --- THE UI ---
st.title("🎯 Quant Syndicate AI Terminal")

# Create the Tabs!
tab1, tab2 = st.tabs(["📊 Global Slate", "🎲 Master Simulation"])

# ==========================================
# TAB 1: THE LIVE SLATE (From your iMac)
# ==========================================
with tab1:
    df = load_data()
    if not df.empty:
        st.header("System Performance Tally")
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
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Last Cloud Sync: {time.strftime('%H:%M:%S')} (v.{int(time.time())})")
    else:
        st.warning("Database currently empty. Waiting for iMac to push data...")

# ==========================================
# TAB 2: INTERACTIVE MONTE CARLO SIMULATOR
# ==========================================
with tab2:
    st.header("🎲 Manual Monte Carlo Engine")
    st.markdown("Run a custom 100k simulation right in the browser.")
    
    col1, col2 = st.columns(2)
    with col1:
        away_team = st.text_input("Away Team", "Suns")
        away_rating = st.number_input("Away Power Rating", value=114.5, step=1.0)
    with col2:
        home_team = st.text_input("Home Team", "Celtics")
        home_rating = st.number_input("Home Power Rating", value=115.5, step=1.0)
        
    sims = st.slider("Number of Simulations", 1000, 100000, 10000)
    
    if st.button("🚀 Run Simulation"):
        with st.spinner('Calculating alternate realities...'):
            time.sleep(0.5) # UI feel
            
            # Math Engine
            raw_a = np.random.normal(loc=away_rating, scale=12.0, size=sims)
            raw_b = np.random.normal(loc=home_rating, scale=12.0, size=sims)
            
            scores_a = np.maximum(np.round(raw_a), 0).astype(int)
            scores_b = np.maximum(np.round(raw_b), 0).astype(int)
            
            a_wins = np.sum(scores_a > scores_b)
            b_wins = np.sum(scores_b > scores_a)
            
            a_prob = (a_wins / sims) * 100
            b_prob = (b_wins / sims) * 100
            
            st.success("Simulation Complete!")
            
            c1, c2 = st.columns(2)
            c1.metric(label=f"{away_team} Win Probability", value=f"{a_prob:.1f}%")
            c2.metric(label=f"{home_team} Win Probability", value=f"{b_prob:.1f}%")
