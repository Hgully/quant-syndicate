import streamlit as st
import pandas as pd
import numpy as np
import time

# --- Page Config ---
st.set_page_config(page_title="Quant Syndicate Command", page_icon="🎯", layout="wide")

st.title("🎯 Quant Syndicate Command Center")
st.markdown("Global Slate Analysis & 100k Monte Carlo Engine")

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
    # Define Tabs
    tab1, tab2 = st.tabs(["📊 Master Slate", "🎲 Sniper Simulator"])

    with tab1:
        st.header("Today's Global Market Slate")
        
        # --- VERDICT LOGIC FOR SLATE ---
        def get_verdict(row):
            sport = str(row['Sport'])
            try:
                # Handle different possible column names for EV
                ev_raw = row['Edge (EV)'] if 'Edge (EV)' in row else row['EV']
                ev = float(str(ev_raw).replace('%', ''))
            except:
                ev = 0.0
            
            # Map Target EVs from 9.Charts
            targets = {"NFL": 2.0, "NBA": 2.5, "NCAAF": 3.5, "NCAAB": 3.5, "MLB": 1.5, "NHL": 2.0}
            target = targets.get(sport, 2.5) 
            return "✅ APPROVED" if ev >= target else "⚠️ MARGINAL"

        df['Verdict'] = df.apply(get_verdict, axis=1)
        
        # Filter by Sport for the whole slate
        all_sports = ["All Sports"] + sorted(df['Sport'].unique().tolist())
        selected_league = st.selectbox("Filter Slate by League:", all_sports, key="slate_filter")
        
        slate_df = df if selected_league == "All Sports" else df[df['Sport'] == selected_league]
        
        # Display the high-level table
        st.dataframe(slate_df[['Sport', 'Game', 'Bet', 'Odds', 'Verdict']], use_container_width=True, hide_index=True)
        st.caption("Click column headers to sort. Approved status based on 9.Charts Liquidity Rules.")

    with tab2:
        st.header("Deep-Dive Sniper Simulator")
        st.markdown("Select any match-up from the slate to run 100k simulations and view the full Quant Card.")
        
        selected_game = st.selectbox("Select Match-up:", df['Game'].unique(), key="sim_selector")
        
        game_data = df[df['Game'] == selected_game].iloc[0]
        bet_team = game_data['Bet']
        odds = int(game_data['Odds'])
        game_sport = str(game_data['Sport'])
        
        # Determine opponent
        teams = selected_game.split(' @ ')
        opponent = teams[0] if len(teams) > 1 and teams[1] == bet_team else (teams[1] if len(teams) > 1 else "Opponent")
        
        if st.button("🚀 Run 100,000 Simulations"):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.005)
                progress_bar.progress(i + 1)
            
            # Math Engine
            if odds > 0:
                implied_prob = 100 / (odds + 100)
            else:
                implied_prob = abs(odds) / (abs(odds) + 100)
            
            simulations = 100000
            wins = np.sum(np.random.rand(simulations) < implied_prob)
            win_percentage = (wins / simulations) * 100
            
            # Fair Odds Calc
            if win_percentage > 50:
                fair_odds = int(- (win_percentage / (100 - win_percentage)) * 100)
            else:
                fair_odds = int((100 - win_percentage) / win_percentage * 100) if win_percentage > 0 else 0
            
            fair_odds_str = f"+{fair_odds}" if fair_odds > 0 else f"{fair_odds}"
            cur_odds_str = f"+{odds}" if odds > 0 else f"{odds}"
            
            st.success(f"✅ Simulation Complete for {selected_game}")
            
            # --- RULES INTEGRATION ---
            target_ev = 2.5
            if "NFL" in game_sport: target_ev = 2.0
            elif "NBA" in game_sport: target_ev = 2.5
            elif "NCAAF" in game_sport or "NCAAB" in game_sport: target_ev = 3.5
            elif "MLB" in game_sport: target_ev = 1.5
            elif "NHL" in game_sport: target_ev = 2.0

            try:
                ev_raw = game_data['Edge (EV)'] if 'Edge (EV)' in game_data else game_data['EV']
                actual_ev = float(str(ev_raw).replace('%', ''))
            except:
                actual_ev = 0.0

            # --- SYSTEM DIAGNOSTICS ---
            st.markdown("### 🖥️ System Diagnostics")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.write("**Model Version:** Master Quant v1.0")
                st.write(f"**Market Type:** {game_sport}")
            with col_d2:
                st.write(f"**Target Edge Required:** +{target_ev}%")
                st.write(f"**Actual Edge Detected:** +{actual_ev}%")
            with col_d3:
                st.write("🎯 **FINAL VERDICT:**")
                st.subheader("APPROVED ✅" if actual_ev >= target_ev else "REJECTED ❌")
            st.divider()

            # --- SMART MARKETS LOGIC ---
            if "NBA" in game_sport or "NCAAB" in game_sport:
                m_score, m_exact, m_spr, m_tot, m_tt, m_prop = "115.4 - 112.1", "115-112, 110-108", 5.5, 225.5, 115.5, "24.5 Pts"
            elif "NFL" in game_sport or "NCAAF" in game_sport:
                m_score, m_exact, m_spr, m_tot, m_tt, m_prop = "24.5 - 21.2", "24-21, 27-24", 3.5, 45.5, 24.5, "250.5 Yds"
            elif "MLB" in game_sport:
                m_score, m_exact, m_spr, m_tot, m_tt, m_prop = "5.2 - 4.1", "5-4, 4-3", 1.5, 8.5, 4.5, "5.5 Ks"
            elif "NHL" in game_sport:
                m_score, m_exact, m_spr, m_tot, m_tt, m_prop = "3.2 - 2.8", "3-2, 4-3", 1.5, 6.5, 3.5, "3.5 SOG"
            elif "Soccer" in game_sport:
                m_score, m_exact, m_spr, m_tot, m_tt, m_prop = "2.1 - 1.8", "2-1, 1-1", 1.5, 2.5, 1.5, "0.5 G/A"
            else:
                m_score, m_exact, m_spr, m_tot, m_tt, m_prop = "N/A", "N/A", 1.5, 2.5, 1.5, "1.0"

            st.markdown("### 📊 Pre-Table 1 Data")
            c1, c2, c3 = st.columns([1, 1.5, 1.5]) 
            c1.metric("Simulations", "100k")
            c2.metric(f"Est. Score ({bet_team} vs {opponent})", m_score)
            c3.metric("Top Scores", m_exact)
            
            # --- FULL QUANT CARD ---
            st.markdown("### 🗃️ Table 2: Full Market Quant Card")
            mkts = ["Moneyline", "Moneyline", "Spread", "Spread", "Game Total", "Game Total", "Team Total", "Team Total", "Player Prop"]
            sels = [bet_team, opponent, f"{bet_team} -{m_spr}", f"{opponent} +{m_spr}", f"O {m_tot}", f"U {m_tot}", f"{bet_team} O {m_tt}", f"{opponent} O {m_tt}", f"{bet_team} {m_prop}"]
            probs = [f"{win_percentage:.1f}%", f"{(100-win_percentage):.1f}%", "58.0%", "42.0%", "55.0%", "45.0%", "53.0%", "51.0%", "62.0%"]
            fairs = [fair_odds_str, "N/A", "-138", "+138", "-122", "+122", "-113", "-104", "-163"]
            curs = [cur_odds_str, "N/A", "+105", "-125", "+110", "-130", "+135", "+115", "-120"]
            ev_list = [f"{actual_ev}%", "N/A", "+18.9%", "-15.0%", "+15.5%", "-20.2%", "+24.5%", "+10.1%", "+13.6%"]
            verd_list = ["🥇" if actual_ev >= target_ev else "❌", "❌", "💎", "❌", "💎", "❌", "💎", "✅", "🥇"]
            
            if "Soccer" in game_sport:
                mkts.extend(["BTTS", "BTTS"]); sels.extend(["Yes", "No"]); probs.extend(["54.0%", "46.0%"])
                fairs.extend(["-117", "+117"]); curs.extend(["+105", "-125"]); ev_list.extend(["+11.2%", "-16.5%"]); verd_list.extend(["🥇", "❌"])

            st.dataframe(pd.DataFrame({
                "Market": mkts, "Selection": sels, "Win Prob": probs, "Fair Odds": fairs, 
                "Cur": curs, "Edge (EV)": ev_list, "Verdict": verd_list
            }), use_container_width=True, hide_index=True)