import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamgamelog

# ==========================================
# PAGE SETUP
# ==========================================
st.set_page_config(page_title="Quant Syndicate Dashboard", layout="wide")
st.title("📈 Quant Syndicate Command Center")
st.markdown("Your proprietary suite for Top-Down Arbitrage and Bottom-Up Game Projections.")

# Create two clean tabs for your two different engines
tab1, tab2 = st.tabs(["🎯 Top-Down Arbitrage (+EV)", "🏀 Bottom-Up NBA Simulator (Monte Carlo)"])

# ==========================================
# TAB 1: TOP-DOWN ARBITRAGE (EV LOG)
# ==========================================
with tab1:
    file_name = "ev_log.csv"
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        if not df.empty:
            df['Edge Value'] = df['Edge (EV)'].str.rstrip('%').astype(float)
            
            st.subheader("Market Pulse")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total +EV Bets Found", len(df))
            col2.metric("Most Targeted Sportsbook", df['Sportsbook'].mode()[0])
            col3.metric("Average Edge Found", f"{round(df['Edge Value'].mean(), 2)}%")
            
            st.divider()
            st.subheader("Syndicate Betting Ledger")
            st.dataframe(df.drop(columns=['Edge Value']), width='stretch')
        else:
            st.info("The ev_log.csv file exists, but it's empty. Let your bot find some bets!")
    else:
        st.warning("⚠️ No database found! Make sure your bot has logged at least one bet to 'ev_log.csv'.")

# ==========================================
# TAB 2: BOTTOM-UP NBA SIMULATOR
# ==========================================
with tab2:
    st.subheader("🎲 100k-Iteration Matchup Simulator")
    st.markdown("Select two teams to ping NBA.com live servers and mathematically project the True Market Price.")
    
    # List of all 30 NBA Teams for the dropdowns
    nba_team_list = [
        "Hawks", "Celtics", "Nets", "Hornets", "Bulls", "Cavaliers", "Mavericks", "Nuggets", 
        "Pistons", "Warriors", "Rockets", "Pacers", "Clippers", "Lakers", "Grizzlies", "Heat", 
        "Bucks", "Timberwolves", "Pelicans", "Knicks", "Thunder", "Magic", "76ers", "Suns", 
        "Trail Blazers", "Kings", "Spurs", "Raptors", "Jazz", "Wizards"
    ]
    
    colA, colB = st.columns(2)
    with colA:
        team_a_input = st.selectbox("Away Team", nba_team_list, index=1) # Defaults to Celtics
    with colB:
        team_b_input = st.selectbox("Home Team", nba_team_list, index=13) # Defaults to Lakers
        
    if st.button("🚀 Run 100,000 Simulations", type="primary", use_container_width=True):
        
        # A cool loading spinner while the API works
        with st.spinner('Connecting to NBA servers & crunching the math...'):
            
            # --- API LOGIC INSIDE THE DASHBOARD ---
            def get_live_team_stats(team_name):
                nba_teams = teams.get_teams()
                team_dict = next((t for t in nba_teams if team_name.lower() in t['full_name'].lower()), None)
                if not team_dict:
                    return None, None, None
                gamelog = teamgamelog.TeamGameLog(team_id=team_dict['id']).get_data_frames()[0]
                mean_score = gamelog['PTS'].mean()
                std_dev = gamelog['PTS'].std()
                time.sleep(0.6) 
                return team_dict['full_name'], mean_score, std_dev

            # Fetch Data
            team_a, a_mean, a_std = get_live_team_stats(team_a_input)
            team_b, b_mean, b_std = get_live_team_stats(team_b_input)
            
            if team_a and team_b:
                st.success("✅ NBA Data successfully ingested!")
                
                # Show the raw stats
                st.write(f"**{team_a}** -> Average Points: {round(a_mean,1)} | Volatility: ±{round(a_std,1)}")
                st.write(f"**{team_b}** -> Average Points: {round(b_mean,1)} | Volatility: ±{round(b_std,1)}")
                st.divider()
                
                # Math Engine
                simulations = 100000
                team_a_scores = np.random.normal(loc=a_mean, scale=a_std, size=simulations)
                team_b_scores = np.random.normal(loc=b_mean, scale=b_std, size=simulations)
                
                a_win_prob = np.sum(team_a_scores > team_b_scores) / simulations
                b_win_prob = np.sum(team_b_scores > team_a_scores) / simulations
                
                def get_american_odds(prob):
                    if prob > 0.50:
                        return int((prob / (1.0 - prob)) * -100)
                    else:
                        return int((100.0 / prob) - 100)
                
                # Display the Final True Odds cleanly
                st.subheader("🚨 True Market Price Generated")
                res_col1, res_col2 = st.columns(2)
                res_col1.metric(f"{team_a} True Odds", get_american_odds(a_win_prob), f"Win Prob: {round(a_win_prob*100, 1)}%")
                res_col2.metric(f"{team_b} True Odds", get_american_odds(b_win_prob), f"Win Prob: {round(b_win_prob*100, 1)}%")
            else:
                st.error("There was an issue fetching the team data from the NBA.")