import streamlit as st
import pandas as pd
import numpy as np

# Page config
st.set_page_config(page_title="Quant Syndicate Terminal", layout="wide", page_icon="🎯")

st.title("🎯 Quant Syndicate AI Terminal")
st.markdown("---")

# 1. Load the Database
@st.cache_data(ttl=30) 
def load_data():
    try:
        return pd.read_csv("ev_log.csv")
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

# Create the Tabs
tab1, tab2 = st.tabs(["📊 Global Slate", "🤖 Master Simulation & QES Report"])

with tab1:
    if df.empty:
        st.warning("No data found. Run the engine on your iMac.")
    else:
        st.markdown("### 🎛️ Terminal Filters")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            sport_list = df['Sport'].unique().tolist()
            selected_sports = st.multiselect("Filter by Sport:", sport_list, default=sport_list)
        with f_col2:
            hide_passes = st.checkbox("Show Only +EV Edges (Hide ❌ PASS)")

        # Filter Logic
        display_df = df[df['Sport'].isin(selected_sports)]
        if hide_passes:
            display_df = display_df[~display_df['QES Rating'].str.contains("❌")]

        st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab2:
    st.header("🤖 Monte Carlo Simulation Lab")
    st.info("Manually test edges by injecting custom Power Ratings below.")
    
    sim_col1, sim_col2 = st.columns(2)
    
    with sim_col1:
        st.subheader("Team Metrics")
        away_team = st.text_input("Away Team Name", "Away Team")
        home_team = st.text_input("Home Team Name", "Home Team")
        away_rank = st.slider(f"{away_team} Power Rating", 60.0, 130.0, 100.0)
        home_rank = st.slider(f"{home_team} Power Rating", 60.0, 130.0, 100.0)
        variance = st.number_input("Scoring Variance (Standard Deviation)", value=12.0)

    with sim_col2:
        st.subheader("Market Odds")
        away_ml = st.number_input(f"{away_team} Moneyline", value=-110)
        home_ml = st.number_input(f"{home_team} Moneyline", value=-110)
        sim_count = st.select_slider("Simulations", options=[1000, 10000, 100000], value=10000)

    if st.button("🚀 Run 100k Monte Carlo Sims"):
        # The Math Engine
        away_scores = np.random.normal(away_rank, variance, sim_count)
        home_scores = np.random.normal(home_rank, variance, sim_count)
        
        home_wins = np.sum(home_scores > away_scores)
        home_prob = home_wins / sim_count
        
        st.success(f"Simulation Complete: {home_team} wins {home_prob:.2%} of the time.")
        
        # Display Results
        res_col1, res_col2 = st.columns(2)
        res_col1.metric(f"{home_team} Win Prob", f"{home_prob:.2%}")
        
        # Calculate EV
        if home_ml > 0:
            payout = (home_ml / 100) + 1
        else:
            payout = (100 / abs(home_ml)) + 1
        
        ev = (home_prob * payout) - 1
        res_col2.metric("Expected Value (EV)", f"{ev:.2%}")