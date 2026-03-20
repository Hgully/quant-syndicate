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
            df_sport = df[df['Sport'] == sport_name]
            return pd.Series(df_sport.Rating.values, index=df_sport.Team).to_dict()
        except: return {}
    return {}

def fetch_global_intelligence():
    intel = {}
    print("🧠 GATHERING GLOBAL INTELLIGENCE...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for sport_key, config in SPORT_CONFIGS.items():
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
            print(f"   ✅ {config['name']} Intelligence Cached.")
        except:
            intel[config["name"]] = load_backup_intel(config["name"])
    return intel

def run_simulations(away, home, intel, config):
    sport_intel = intel.get(config["name"], {})
    def get_rating(team_name):
        return next((float(v) for k, v in sport_intel.items() if str(team_name) in str(k) or str(k) in str(team_name)), 0.0)
    a_r, h_r = get_rating(away), get_rating(home)
    hfa = 3.5 if config["name"] == "NCAAB" else 2.4 if config["name"] == "NBA" else 0.2
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

def run_global_engine():
    current_time = datetime.datetime.now().strftime('%I:%M %p')
    print(f"\n[{current_time}] 🚀 SYNDICATE ENGINE INITIALIZED")
    global_intel = fetch_global_intelligence()
    results = []
    strong_plays = []
    
    for api_key, config in SPORT_CONFIGS.items():
        url = f"https://api.the-odds-api.com/v4/sports/{api_key}/odds/"
        params = {'apiKey': API_KEY, 'regions': 'us', 'markets': 'h2h,spreads,totals', 'oddsFormat': 'american'}
        try:
            res = requests.get(url, params=params)
            if res.status_code == 200:
                games = res.json()
                print(f"📡 Sweeping {len(games)} {config['name']} games...")
                for g in games:
                    h_t, a_t = g.get('home_team'), g.get('away_team')
                    a_scores, h_scores = run_simulations(a_t, h_t, global_intel, config)
                    has_data = any(str(a_t) in str(k) or str(h_t) in str(k) for k in global_intel.get(config["name"], {}).keys())
                    if not has_data: continue

                    for b in g.get('bookmakers', [])[:1]:
                        for m in b.get('markets', []):
                            market_type = m['key']
                            for o in m['outcomes']:
                                selection_name = o['name']
                                price, point = o['price'], o.get('point', 0)
                                prob = 0
                                if market_type == 'h2h':
                                    m_label, s_label = "Moneyline", f"{selection_name} ML"
                                    prob = np.sum(a_scores > h_scores)/100000 if selection_name == a_t else np.sum(h_scores > a_scores)/100000
                                elif market_type == 'spreads':
                                    m_label, s_label = "Spread", f"{selection_name} {'+'+str(point) if point > 0 else point}"
                                    prob = np.sum((a_scores + point) > h_scores)/100000 if selection_name == a_t else np.sum((h_scores + point) > a_scores)/100000
                                elif market_type == 'totals':
                                    m_label, s_label = "Game Total", f"{selection_name.upper()} {point}"
                                    prob = np.sum((a_scores + h_scores) > point)/100000 if selection_name.lower() == 'over' else np.sum((a_scores + h_scores) < point)/100000

                                ev = calculate_ev(prob, price)
                                if ev > 0:
                                    fair_odds = calculate_fair_odds(prob)
                                    qes, verd, stars = generate_qes_rating(ev, prob)
                                    results.append({"Market": m_label, "Selection": s_label, "Win Prob": f"{round(prob*100, 1)}%", "Fair Odds": fair_odds, "Cur": price, "Edge (EV)": f"+{round(ev*100, 1)}%", "QES": qes, "Verdict": verd, "Rating": stars, "Sport": config["name"]})
                                    if stars in ["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐"]:
                                        strong_plays.append(f"🚨 *{stars} {verd} PLAY*\n\n*Sport:* {config['name']}\n*Market:* {m_label}\n*Selection:* {s_label}\n*Odds:* {price} (Fair: {fair_odds})\n*Win Prob:* {round(prob*100,1)}%\n*EV:* +{round(ev*100,1)}%\n*QES:* {qes}")
        except: continue

    # --- HEARTBEAT / DUMMY DATA INJECTION ---
    if not results:
        results.append({"Market": "System Check", "Selection": "[Heartbeat Active]", "Win Prob": "100%", "Fair Odds": "N/A", "Cur": 0, "Edge (EV)": "0%", "QES": 1.0, "Verdict": "📡", "Rating": "SCANNING", "Sport": "ALL"})

    df_output = pd.DataFrame(results)
    df_output = df_output.sort_values(by="QES", ascending=False)
    df_output.to_csv("ev_log.csv", index=False)
    
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Heartbeat Update: {current_time}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"\n☁️ TERMINAL UPDATED. (Edges Found: {len(results)-1 if '[Heartbeat Active]' in str(results) else len(results)})")
        for play in strong_plays: send_telegram_alert(play)
    except Exception as e: print(f"⚠️ Push Failed: {e}")

if __name__ == "__main__":
    run_global_engine()