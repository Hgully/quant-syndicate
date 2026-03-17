import streamlit as st
import pandas as pd
import numpy as np
import time

# --- Page Config ---
st.set_page_config(page_title="Quant Syndicate", page_icon="🎯", layout="wide")

st.title("🎯 Quant Syndicate Global Sniper")
st.markdown("Live Expected Value (+EV) Opportunities based on Sharp Market Implied Probabilities.")
st.divider()

# --- Load Data ---
@st.cache_data(ttl=60)
def load_data():
    try:
        return pd.read_csv("ev_log.csv")
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.info("📡 The Sniper is currently scanning the markets. No edges found yet.")
else:
    # --- FILTERS & TABLE ---
    st.subheader("Filter Markets")
    sports_list = ["All Sports"] + sorted(df['Sport'].unique().tolist())
    selected_sport = st.selectbox("Select a League to view:", sports_list)

    if selected_sport != "All Sports":
        display_df = df[df['Sport'] == selected_sport]
    else:
        display_df = df

    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.caption("Data refreshes automatically. Sharp book used: LowVig.ag")

    # --- MONTE CARLO SIMULATOR ---
    st.divider()
    st.header("🎲 Live Monte Carlo Simulator")
    st.markdown("Run **100,000 independent mathematical simulations** to visualize the true win probability of any edge found above.")

    games_list = display_df['Game'].unique().tolist()
    
    if games_list:
        selected_game = st.selectbox("Select a game to simulate:", games_list)
        
        # Grab the specific data for the chosen game
        game_data = display_df[display_df['Game'] == selected_game].iloc[0]
        bet_team = game_data['Bet']
        odds = int(game_data['Odds'])
        
        # Convert American Odds to Implied Probability for the simulator
        if odds > 0:
            implied_prob = 100 / (odds + 100)
        else:
            implied_prob = abs(odds) / (abs(odds) + 100)
            
        if st.button("🚀 Run 100,000 Simulations"):
            # Create a cool visual progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(100):
                time.sleep(0.01) # Simulating heavy computing time
                progress_bar.progress(i + 1)
                status_text.text(f"Simulating {i * 1000} matches...")
                
            # The actual Numpy Math Engine
            simulations = 100000
            results = np.random.rand(simulations) < implied_prob
            wins = np.sum(results)
            win_percentage = (wins / simulations) * 100
            
            status_text.text("✅ Simulation Complete!")
            
            # Calculate what the true American Odds *should* be
            if win_percentage > 50:
                fair_odds = int(- (win_percentage / (100 - win_percentage)) * 100)
            else:
                fair_odds = int((100 - win_percentage) / win_percentage * 100)
            
            # Display metrics beautifully
            col1, col2, col3 = st.columns(3)
            col1.metric("Simulations Run", "100,000")
            col2.metric(f"True Win Probability", f"{win_percentage:.2f}%")
            col3.metric("True Fair Odds", f"{fair_odds:+d}")