import pandas as pd
import numpy as np
import requests
import datetime
import subprocess
import io
import time
import os

# ==========================================
# 1. THE SYNDICATE MASTER PROTOCOL
# ==========================================
EV_THRESHOLDS = {
    "NCAAB": 0.035, "NBA": 0.025, "NFL": 0.02, "NCAAF": 0.035,
    "MLB": 0.015, "NHL": 0.02, "SOCCER": 0.025, "UFC": 0.03, "TENNIS": 0.02
}

API_KEY = "d896ce4f4c52fb4b3837aef60ef574ef" 
TELEGRAM_TOKEN = "7786273213:AAH_reyqYhuiw5UyujV7KEVoN4dDmFVjPNM"
TELEGRAM_CHAT_ID = "5059837143"

SPORT_CONFIGS = {
    "basketball_ncaab": {"name": "NCAAB", "avg": 75.0, "var": 10.0, "url": "https://www.sports-reference.com/cbb/seasons/2026-ratings.html"},
    "basketball_nba":   {"name": "NBA",   "avg": 115.0,"var": 12.0, "url": "https://www.basketball-reference.com/leagues/NBA_2026_standings.html"},
    "icehockey_nhl":    {"name": "NHL",   "avg": 3.2,  "var": 1.5,  "url": "https://www.hockey-reference.com/leagues/NHL_2026.html"},
    "baseball_mlb":     {"name": "MLB",   "avg": 4.5,  "var": 2.5,  "url": "https://www.baseball-reference.com/leagues/majors/2026-standings.shtml"},
    "soccer_epl":       {"name": "SOCCER","avg": 1.5,  "var": 1.2,  "url": "https://fbref.com/en/comps/9/stats/Premier-League-Stats"},
    "mma_mixed_martial_arts": {"name": "UFC", "avg": 50.0, "var": 10.0, "url": "https://www.tsn.ca/mma/ufc-rankings-1.1553535"}
}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except: return False

def load_backup_intel(sport_name):
    if os.path.exists("syndicate_ratings.csv"):
        try:
            df = pd.read_csv("syndicate_ratings.csv")
            return pd.Series(df.Rating.values, index=df.Team).to_dict()
        except: return {}
    return {}

def fetch_global_intelligence():
    intel = {}
    print("🧠 GATHERING GLOBAL INTELLIGENCE...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for sport_key, config in SPORT_CONFIGS.items():
        if not config["url"]: continue
        try:
            time.sleep(1)
            res = requests.get(config["url"], headers=headers, timeout=10)
            if res.status_code != 200:
                intel[config["name"]] = load_backup_intel(config["name"])
                continue
            df = pd.read_html(io.StringIO(res.text), flavor='lxml')[0]
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(-1)
            
            if config["name"] == "NCAAB": intel["NCAAB"] = pd.Series(df.SRS.values, index=df['School']).to_dict()
            elif config["name"] == "NBA": intel["NBA"] = pd.Series(df.SRS.values, index=df['Western Conference']).to_dict()
            elif config["name"] == "NHL": intel["NHL"] = pd.Series(df.SRS.values, index=df['Unnamed: 0']).to_dict()
            elif config["name"] == "SOCCER": intel["SOCCER"] = pd.Series(df.xG.values, index=df['Squad']).to_dict()
            elif config["name"] == "UFC":
                ufc_map = {}
                for _, r in df.iterrows():
                    try: ufc_map[str(r[1])] = 10.0 if 'C' in str(r[0]) else 9.5 - (float(r[0]) * 0.25)
                    except: continue
                intel["UFC"] = ufc_map
        except: intel[config["name"]] = load_backup_intel(config["name"])
    return intel

# ==========================================
# 4. FULL MARKET MONTE CARLO (SCORES & SPREADS)
# ==========================================
def run_simulations(away, home, intel, config):
    sport_intel = intel.get(config["name"], {})
    def get_rating(team_name):
        return next((float(v) for k, v in sport_intel.items() if str(team_name) in str(k) or str(k) in str(team_name)), 0.0)
    
    a_r, h_r = get_rating(away), get_rating(home)
    hfa = 3.5 if config["name"] == "NCAAB" else 2.4 if config["name"] == "NBA" else 0.2
    
    # Simulating 100,000 exact final scores for both teams
    a_scores = np.random.normal(config["avg"] + a_r, config["var"], 100000)
    h_scores = np.random.normal(config["avg"] + h_r + hfa, config["var"], 100000)
    return a_scores, h_scores

def calculate_ev(win_prob, odds):
    if odds == 0: return -1
    payout = (odds/100 + 1) if odds > 0 else (100/abs(odds) + 1)
    return (win_prob * payout) - 1

def calculate_fair_odds(prob):
    if prob <= 0 or prob >= 1: return "+0"
    if prob > 0.5: return f"{int((prob / (1 - prob)) * -100)}"
    else: return f"+{int(((1 - prob) / prob) * 100)}"

def generate_qes_rating(ev, prob):
    if ev <= 0: return 1.0, "❌", ""
    score = round(min(10.0, 5.0 + (ev * 40)), 1)
    if prob > 0.54 and ev >= 0.05: return max(score, 9.0), "💎", "⭐⭐⭐⭐⭐"
    elif ev >= 0.035: return score, "🥇", "⭐⭐⭐⭐"
    elif ev >= 0.02: return score, "🥈", "⭐⭐⭐"
    elif ev >= 0.01: return score, "🥉", "⭐⭐"
    else: return score, "LEAN", "⭐"

# ==========================================
# 5. EXECUTION LOOP (NEW UI FORMAT)
# ==========================================
def run_global_engine():
    print(f"\n[{datetime.datetime.now().strftime('%I:%M %p')}] 🚀 SYNDICATE ENGINE INITIALIZED")
    global_intel = fetch_global_intelligence()
    results = []
    strong_plays = []
    
    for api_key, config in SPORT_CONFIGS.items():
        # Added spreads and totals to the API call
        url = f"https://api.the-odds-api.com/v4/sports/{api_key}/odds/"
        params = {'apiKey': API_KEY, 'regions': 'us', 'markets': 'h2h,spreads,totals', 'oddsFormat': 'american'}
        
        try:
            res = requests.get(url, params=params)
            if res.status_code == 200:
                games = res.json()
                for g in games:
                    commence_time_str = g.get('commence_time', '')
                    if commence_time_str:
                        match_time = datetime.datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
                        if (match_time - datetime.datetime.now(datetime.timezone.utc)).days > 7: continue 
                    
                    h_t, a_t = g.get('home_team'), g.get('away_team')
                    
                    # Generate the array of simulated scores once per game
                    a_scores, h_scores = run_simulations(a_t, h_t, global_intel, config)
                    
                    # Sniper Check
                    sport_intel = global_intel.get(config["name"], {})
                    has_data = any(str(a_t) in str(k) or str(h_t) in str(k) for k in sport_intel.keys())
                    if not has_data: continue # Skip processing if we have no data on these teams
                    
                    # Evaluate all available markets
                    for b in g.get('bookmakers', [])[:1]: # Use the sharpest/first book to avoid duplicates
                        for m in b.get('markets', []):
                            market_type = m['key']
                            
                            for o in m['outcomes']:
                                selection_name = o['name']
                                price = o['price']
                                point = o.get('point', 0)
                                prob = 0
                                market_label = ""
                                display_selection = ""

                                # Evaluate Math based on Market Type
                                if market_type == 'h2h':
                                    market_label = "Moneyline"
                                    display_selection = f"{selection_name} ML"
                                    if selection_name == a_t: prob = np.sum(a_scores > h_scores) / 100000
                                    else: prob = np.sum(h_scores > a_scores) / 100000
                                
                                elif market_type == 'spreads':
                                    market_label = "Spread"
                                    display_selection = f"{selection_name} {point if point < 0 else '+'+str(point)}"
                                    if selection_name == a_t: prob = np.sum((a_scores + point) > h_scores) / 100000
                                    else: prob = np.sum((h_scores + point) > a_scores) / 100000
                                    
                                elif market_type == 'totals':
                                    market_label = "Game Total"
                                    display_selection = f"{selection_name.upper()} {point}"
                                    if selection_name.lower() == 'over': prob = np.sum((a_scores + h_scores) > point) / 100000
                                    else: prob = np.sum((a_scores + h_scores) < point) / 100000

                                ev = calculate_ev(prob, price)
                                fair_odds = calculate_fair_odds(prob)
                                qes_score, verdict, stars = generate_qes_rating(ev, prob)

                                if ev > 0: # Only log positive EV plays to keep the board clean
                                    results.append({
                                        "Market": market_label,
                                        "Selection": display_selection,
                                        "Win Prob": f"{round(prob*100, 1)}%",
                                        "Fair Odds": fair_odds,
                                        "Cur": price,
                                        "Edge (EV)": f"+{round(ev*100, 1)}%",
                                        "QES": qes_score,
                                        "Verdict": verdict,
                                        "Rating": stars
                                    })
                                    
                                    if stars in ["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐"]:
                                        strong_plays.append(f"🚨 *{stars} {verdict} PLAY*\n\n*Market:* {market_label}\n*Selection:* {display_selection}\n*Odds:* {price} (Fair: {fair_odds})\n*Win Prob:* {round(prob*100, 1)}%\n*EV:* +{round(ev*100, 1)}%\n*QES:* {qes_score}")

        except Exception as e: print(f"⚠️ Error: {e}")

    if results:
        df = pd.DataFrame(results)
        # Sort by QES score descending so the best plays are at the top
        df = df.sort_values(by="QES", ascending=False) 
        df.to_csv("ev_log.csv", index=False)
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Full Market Dashboard Upgrade"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("\n☁️ TERMINAL UPDATED (FULL MARKETS LIVE).")
            for play in strong_plays:
                send_telegram_alert(play)
                time.sleep(0.5) 
        except Exception as e: print(f"⚠️ Push Failed: {e}")
    else: print("⚠️ No edges found.")

if __name__ == "__main__":
    run_global_engine()