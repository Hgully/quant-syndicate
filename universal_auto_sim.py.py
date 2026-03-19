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

# --- CREDENTIALS (PASTE YOURS HERE) ---
API_KEY = "d896ce4f4c52fb4b3837aef60ef574ef" 
TELEGRAM_TOKEN = "7786273213:AAH_reyqYhuiw5UyujV7KEVoN4dDmFVjPNM"
TELEGRAM_CHAT_ID = "5059837143"

SPORT_CONFIGS = {
    "basketball_ncaab": {"name": "NCAAB", "avg": 75.0, "var": 10.0, "url": "https://www.sports-reference.com/cbb/seasons/2026-ratings.html"},
    "basketball_nba":   {"name": "NBA",   "avg": 115.0,"var": 12.0, "url": "https://www.basketball-reference.com/leagues/NBA_2026_standings.html"},
    "icehockey_nhl":    {"name": "NHL",   "avg": 3.2,  "var": 1.5,  "url": "https://www.hockey-reference.com/leagues/NHL_2026.html"},
    "baseball_mlb":     {"name": "MLB",   "avg": 4.5,  "var": 2.5,  "url": "https://www.baseball-reference.com/leagues/majors/2026-standings.shtml"},
    "soccer_epl":       {"name": "SOCCER","avg": 1.5,  "var": 1.2,  "url": "https://fbref.com/en/comps/9/stats/Premier-League-Stats"},
    "mma_mixed_martial_arts": {"name": "UFC", "avg": 50.0, "var": 10.0, "url": "https://www.tsn.ca/mma/ufc-rankings-1.1553535"},
    "tennis_atp":       {"name": "TENNIS","avg": 50.0, "var": 10.0, "url": ""}
}

# ==========================================
# 2. TELEGRAM SIGNAL BROADCASTER
# ==========================================
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            return True
        else:
            print(f"   ⚠️ Telegram Rejected Message: {res.text}")
            return False
    except Exception as e:
        print(f"   ⚠️ Telegram Alert Error: {e}")
        return False

# ==========================================
# 3. INTELLIGENCE GATHERING 
# ==========================================
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for sport_key in ["basketball_ncaab", "basketball_nba", "icehockey_nhl", "soccer_epl", "mma_mixed_martial_arts"]:
        config = SPORT_CONFIGS[sport_key]
        if not config["url"]: continue
        try:
            time.sleep(1.5)
            res = requests.get(config["url"], headers=headers, timeout=15)
            if res.status_code != 200:
                print(f"   ⚠️ {config['name']} Blocked. Using Backup Vault.")
                intel[config["name"]] = load_backup_intel(config["name"])
                continue
            df_list = pd.read_html(io.StringIO(res.text), flavor='lxml')
            df = df_list[0]
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(-1)
            
            if config["name"] == "NCAAB": intel["NCAAB"] = pd.Series(df.SRS.values, index=df['School']).to_dict()
            elif config["name"] == "NBA": intel["NBA"] = pd.Series(df.SRS.values, index=df['Western Conference']).to_dict()
            elif config["name"] == "NHL": intel["NHL"] = pd.Series(df.SRS.values, index=df['Unnamed: 0']).to_dict()
            elif config["name"] == "SOCCER": intel["SOCCER"] = pd.Series(df.xG.values, index=df['Squad']).to_dict()
            elif config["name"] == "UFC":
                ufc_map = {}
                for d in df_list:
                    for i, r in d.iterrows():
                        try:
                            name, rank = str(r[1]), str(r[0])
                            score = 10.0 if 'C' in rank else 9.5 - (float(rank) * 0.25) if rank.isdigit() else 5.0
                            ufc_map[name] = score
                        except: continue
                intel["UFC"] = ufc_map
            print(f"   ✅ {config['name']} Intelligence Cached.")
        except:
            print(f"   ⚠️ {config['name']} Scrape Error. Using Backup Vault.")
            intel[config["name"]] = load_backup_intel(config["name"])
    return intel

# ==========================================
# 4. MONTE CARLO CORE (THE MISSING MATH)
# ==========================================
def calculate_ev(win_prob, ml):
    payout = (ml/100 + 1) if ml > 0 else (100/abs(ml) + 1)
    return (win_prob * payout) - 1

def simulate_match(away, home, intel, config):
    sport_intel = intel.get(config["name"], {})
    def get_rating(team_name):
        for key, val in sport_intel.items():
            if str(team_name) in str(key) or str(key) in str(team_name):
                try: return float(val)
                except: return 0.0
        return 0.0
    a_r, h_r = get_rating(away), get_rating(home)
    hfa = 3.5 if config["name"] == "NCAAB" else 2.4 if config["name"] == "NBA" else 0.2
    
    a_sims = np.random.normal(config["avg"] + a_r, config["var"], 100000)
    h_sims = np.random.normal(config["avg"] + h_r + hfa, config["var"], 100000)
    return np.sum(h_sims > a_sims) / 100000

# ==========================================
# 4.5 NEW SYNDICATE GRADING MATH
# ==========================================
def calculate_fair_odds(prob):
    if prob <= 0 or prob >= 1: return "+0"
    if prob > 0.5:
        odds = (prob / (1 - prob)) * -100
        return f"{int(odds)}"
    else:
        odds = ((1 - prob) / prob) * 100
        return f"+{int(odds)}"

def generate_qes_rating(ev, prob):
    if ev <= 0:
        return 1.0, "❌ PASS", ""
    
    score = round(min(10.0, 5.0 + (ev * 40)), 1)
    
    if prob > 0.54 and ev >= 0.05:
        return max(score, 9.0), "💎 MAX", "⭐⭐⭐⭐⭐"
    elif ev >= 0.035:
        return score, "🥇 STRONG", "⭐⭐⭐⭐"
    elif ev >= 0.02:
        return score, "🥈 STANDARD", "⭐⭐⭐"
    elif ev >= 0.01:
        return score, "🥉 SPECULATIVE", "⭐⭐"
    else:
        return score, "LEAN", "⭐"

# ==========================================
# 5. EXECUTION LOOP (NEW UI FORMAT)
# ==========================================
def run_global_engine():
    current_time = datetime.datetime.now().strftime('%I:%M %p')
    print(f"\n[{current_time}] 🚀 SYNDICATE ENGINE INITIALIZED")
    global_intel = fetch_global_intelligence()
    results = []
    strong_plays = []
    
    for api_key, config in SPORT_CONFIGS.items():
        url = f"https://api.the-odds-api.com/v4/sports/{api_key}/odds/"
        params = {'apiKey': API_KEY, 'regions': 'us', 'markets': 'h2h', 'oddsFormat': 'american'}
        
        try:
            res = requests.get(url, params=params)
            if res.status_code == 200:
                games = res.json()
                print(f"📡 Sweeping {len(games)} {config['name']} games...")
                for g in games:
                    commence_time_str = g.get('commence_time', '')
                    if commence_time_str:
                        clean_time = commence_time_str.replace('Z', '+00:00')
                        match_time = datetime.datetime.fromisoformat(clean_time)
                        now = datetime.datetime.now(datetime.timezone.utc)
                        if (match_time - now).days > 7:
                            continue 
                    
                    h_t, a_t = g.get('home_team'), g.get('away_team')
                    best_ml = -10000
                    for b in g.get('bookmakers', []):
                        for m in b.get('markets', []):
                            if m['key'] == 'h2h':
                                for o in m['outcomes']:
                                    if o['name'] == h_t and o['price'] > best_ml: 
                                        best_ml = o['price']
                    
                    if best_ml == -10000: continue
                    
                    # Run Simulation
                    prob = simulate_match(a_t, h_t, global_intel, config)
                    ev = calculate_ev(prob, best_ml)
                    
                    # New Math & Grading
                    fair_odds = calculate_fair_odds(prob)
                    qes_score, verdict, stars = generate_qes_rating(ev, prob)
                    
                    # Sniper Check
                    sport_intel = global_intel.get(config["name"], {})
                    has_data = any(str(a_t) in str(k) or str(h_t) in str(k) for k in sport_intel.keys())
                    
                    if not has_data:
                        qes_score = 1.0
                        verdict = "BLIND PASS"
                        stars = "❌"
                        
                    if (stars == "⭐⭐⭐⭐⭐" or stars == "⭐⭐⭐⭐") and has_data:
                        alert_msg = f"🚨 *{stars} {verdict} PLAY*\n\n*Sport:* {config['name']}\n*Match:* {a_t} @ {h_t}\n*Bet:* {h_t} ML\n*Odds:* {best_ml} (Fair: {fair_odds})\n*Win Prob:* {round(prob*100, 1)}%\n*EV Edge:* {round(ev*100, 2)}%\n*Rating:* {qes_score}/10"
                        strong_plays.append(alert_msg)

                    results.append({
                        "Time": current_time,
                        "Sport": config["name"], 
                        "Game": f"{a_t} @ {h_t}",
                        "Selection": f"{h_t} ML", 
                        "Win Prob": f"{round(prob*100, 1)}%",
                        "Fair Line": fair_odds,
                        "Current Odds": best_ml,
                        "EV Edge": f"{round(ev*100, 2)}%", 
                        "Score (1-10)": qes_score,
                        "Verdict": f"{stars} {verdict}"
                    })
        except Exception as e: 
            print(f"⚠️ Odds Fetch Error for {config['name']}: {e}")
            continue

    if results:
        pd.DataFrame(results).to_csv("ev_log.csv", index=False)
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Master UI Override"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("\n☁️ SYNDICATE TERMINAL UPDATED (NEW UI DEPLOYED).")
            
            for play in strong_plays:
                success = send_telegram_alert(play)
                if success:
                    print(f"📣 Signal Sent to Telegram: {play.splitlines()[2]}")
                time.sleep(0.5) 
                
        except Exception as e: 
            print(f"⚠️ Git Push Failed: {e}")
    else:
        print("⚠️ No data collected.")

if __name__ == "__main__":
    run_global_engine()