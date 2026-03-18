import streamlit as st
import pandas as pd
import numpy as np
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Quant Syndicate Terminal", page_icon="🎯", layout="wide")

# --- 1. THE SAFE DATA LOADER ---
@st.cache_data(ttl=60)
def load_data():
    # Replace this URL with your actual GitHub RAW URL
    RAW_URL = "https://raw.githubusercontent.com/hgully/quant-syndicate/main/ev_log.csv"
    
    try:
        # We add a timestamp to the URL to force GitHub to give us the FRESH version
        df = pd.read_csv(f"{RAW_URL}?nocache={time.time()}")
        
        # 🛡️ SAFETY SHIELD: Add missing columns if they don't exist in the CSV
        if 'Result' not in df.columns:
            df['Result'] = "Pending"
        if 'QES' not in df.columns:
            df['QES'] = 0.0
        if 'Sport' not in df.columns:
            df['Sport'] = "NBA"
            
        return df
    except Exception as e:
        st.warning(f"📡 Waiting for Cloud Database... (Error: {e})")
        return pd.DataFrame()

# --- 2. THE MASTER SIMULATION ENGINE ---
def run_mcsde(sport, sims=100000):
    sport = str(sport).upper()
    
    # Logic to switch math based on Sport
    if any(x in sport for x in ["NBA", "NCAAB", "NFL", "NCAAF"]):
        # High Scoring (Normal Dist)
        h_lam, a_lam, vol = 114.5, 110.2, 12.0
        h_s = np.random.normal(h_lam, vol, sims)
        a_s = np.random.normal(a_lam, vol, sims)
    else:
        # Low Scoring (Poisson Dist)
        h_lam, a_lam = 1.8, 1.2
        h_s = np.random.poisson(h_lam, sims)
        a_s = np.random.poisson(a_lam, sims)
        
    return h_s, a_s

# --- 3. THE UI LAYOUT ---
st.title("🎯 Quant Syndicate AI Terminal")

df = load_data()

tab1, tab2 = st.tabs(["📊 Global Slate", "🎲 Master Simulation"])

with tab1:
    if not df.empty:
        st.header("System Performance Tally")
        
        # Calculate stats only if games are graded
        graded = df[df['Result'] != "Pending"]
        
        if not graded.empty:
            wins = len(graded[graded['Result'].str.contains("Won", na=False)])
            losses = len(graded[graded['Result'].str.contains("Lost", na=False)])
            total = wins + losses
            wr = (wins / total * 100) if total > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Win Rate", f"{wr:.1f}%")
            c2.metric("Total Plays", total)
            c3.metric("Status", "STABLE")
        else:
            st.info("📡 All current plays are 'Pending'. No graded results to show yet.")

        st.divider()
        st.subheader("Current Master Slate")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("Database is empty. Please run your Mac simulation script.")

with tab2:
    if not df.empty:
        selected_game = st.selectbox("Select Matchup for Deep Sim:", df['Game'].unique())
        row = df[df['Game'] == selected_game].iloc[0]
        
        if st.button("🚀 Run 100k MCSDE Engine"):
            with st.spinner("Calibrating Volatility..."):
                h_s, a_s = run_mcsde(row['Sport'])
                
                a_win_p = np.mean(a_s > h_s) * 100
                h_win_p = 100 - a_win_p
                
                col1, col2 = st.columns(2)
                col1.metric(f"{selected_game.split('@')[0]} Win Prob", f"{a_win_p:.1f}%")
                col2.metric(f"{selected_game.split('@')[1]} Win Prob", f"{h_win_p:.1f}%")
                
                st.write(f"**Projected Average Score:** {np.mean(a_s):.1f} - {np.mean(h_s):.1f}")
    else:
        st.write("Load data in Tab 1 first.")

# --- FOOTER ---
st.caption(f"Last Cloud Sync: {time.strftime('%H:%M:%S')}")