import pandas as pd
import numpy as np
import requests
import datetime
import os
import subprocess

# ==========================================
# 1. QUANT SYNDICATE MASTER PROTOCOL
# ==========================================
EV_THRESHOLDS = {
    "NCAAB":  {"Spread": 0.03,  "Total": 0.03,  "ML": 0.035},
    "NCAAF":  {"Spread": 0.03,  "Total": 0.03,  "ML": 0.035},
    "NFL":    {"Spread": 0.015, "Total": 0.015, "ML": 0.02},
    "NBA":    {"Spread": 0.02,  "Total": 0.02,  "ML": 0.025},
    "MLB":    {"Spread": 0.02,  "Total": 0.02,  "ML": 0.015}, 
    "NHL":    {"Spread": 0.03,  "Total": 0.025, "ML": 0.02},  
    "SOCCER": {"Spread": 0.02,  "Total": 0.02,  "ML": 0.025}, 
    "UFC":    {"Spread": 0.00,  "Total": 0.03,  "ML": 0.03}   
}

API_KEY = "d896ce4f4c52fb4b3837aef60ef574ef" 

# ==========================================
# 2. THE MARKET INTELLIGENCE API (PULL LIVE ODDS)
# ==========================================
def get_live_vegas_odds(sport="basketball_ncaab"):
    print(f"📡 Pinging Vegas API for {sport} lines...")
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
    params = {
        'apiKey': API_KEY,
        'regions': 'us',
        'markets': 'h2h', # Just pulling Moneyline to test the plumbing tonight
        'oddsFormat': 'american'
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.status_code}. Check your API Key.")
        return []
        
    odds_data = response.json()
    live_games = []
    
    for game in odds_data:
        home_team = game['home_team']
        away_team = game['away_team']
        
        best_home_ml = -10000
        best_away_ml = -10000
        
        # Scan all bookmakers for the absolute best price (Line Shopping)
        for book in game.get('bookmakers', []):
            for market in book.get('markets', []):
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        if outcome['name'] == home_team and outcome['price'] > best_home_ml:
                            best_home_ml = outcome['price']
                        elif outcome['name'] == away_team and outcome['price'] > best_away_ml:
                            best_away_ml = outcome['price']
                            
        # Only add games that have actual odds listed
        if best_home_ml != -10000 and best_away_ml != -10000:
            live_games.append({
                "Sport": "NCAAB",
                "Game": f"{away_team} @ {home_team}",
                "Home Team": home_team,
                "Away Team": away_team,
                "Home ML Best": best_home_ml,
                "Away ML Best": best_away_ml
            })
            
    print(f"✅ Secured live lines for {len(live_games)} games.")
    return live_games

# ==========================================
# 3. MATH ENGINE (AMERICAN ODDS)
# ==========================================
def calculate_ev(win_prob, american_odds):
    if american_odds > 0:
        payout_multiplier = (american_odds / 100.0) + 1.0
    else:
        payout_multiplier = (100.0 / abs(american_odds)) + 1.0
    return (win_prob * payout_multiplier) - 1.0

# ==========================================
# 4. MONTE CARLO SIMULATOR (n=100k)
# ==========================================
def simulate_game(away_rating, home_rating, simulations=100000):
    away_scores = np.random.normal(loc=away_rating, scale=10.0, size=simulations)
    home_scores = np.random.normal(loc=home_rating, scale=10.0, size=simulations)
    
    home_ml_prob = np.sum(home_scores > away_scores) / simulations
    away_ml_prob = np.sum(away_scores > home_scores) / simulations
    
    return {"Home ML Prob": home_ml_prob, "Away ML Prob": away_ml_prob}

# ==========================================
# 5. THE BET GAUNTLET (EVALUATOR)
# ==========================================
def evaluate_play(sport, market_type, win_prob, american_odds):
    ev = calculate_ev(win_prob, american_odds)
    threshold = EV_THRESHOLDS.get(sport, EV_THRESHOLDS["NCAAB"]).get(market_type, 0.03)
    
    if ev >= (threshold + 0.02):
        rating = "🥇⭐⭐⭐⭐ Strong Play"
    elif ev >= threshold:
        rating = "🥈⭐⭐⭐ Standard Play"
    elif ev > 0:
        rating = "❌ PASS (Low Edge)"
    else:
        rating = "❌ PASS (Negative EV)"
        
    return round(ev * 100, 2), rating

# ==========================================
# 6. MASTER EXECUTION LOOP
# ==========================================
def run_daily_slate():
    print(f"\n[{datetime.datetime.now()}] 🚀 INITIALIZING QUANT SYNDICATE ENGINE...")
    
    live_games = get_live_vegas_odds("basketball_ncaab")
    
    if not live_games:
        print("⚠️ No live games found or API hit a wall. Exiting.")
        return

    results = []
    
    print("\n🤖 Running 100,000 Monte Carlo Sims per game...")
    for g in live_games:
        # Note: Since we haven't built the ML scraper for true Power Ratings yet, 
        # we give both teams a flat 75 rating just to test the API plumbing.
        sims = simulate_game(away_rating=75.0, home_rating=75.0)
        
        # Evaluate Home Team
        home_ev, home_rating = evaluate_play("NCAAB", "ML", sims["Home ML Prob"], g["Home ML Best"])
        results.append({
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Sport": "NCAAB",
            "Game": g["Game"],
            "Bet": f"{g['Home Team']} ML",
            "Odds": g["Home ML Best"],
            "EV": f"{home_ev}%",
            "Result": "Pending",
            "QES Rating": home_rating
        })
        
    df = pd.DataFrame(results)
    
    df.to_csv("ev_log.csv", index=False)
        
    print("\n💾 Saved to Local Vault. Pushing to GitHub...")

    try:
        subprocess.run(["git", "add", "ev_log.csv"], check=True)
        subprocess.run(["git", "commit", "-m", "Live Odds API Sync"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("☁️ SUCCESS: Live Vegas Slate beamed to Dashboard.")
    except Exception as e:
        print("⚠️ Cloud sync failed. Check GitHub token.")

if __name__ == "__main__":
    run_daily_slate()