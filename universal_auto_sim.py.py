import numpy as np
import pandas as pd
import time
import os
from datetime import datetime
from github import Github, GithubException, Auth
import requests

def get_live_ncaab_games():
    """Fetches today's live College Basketball slate using ESPN's public API."""
    print("📡 Pinging ESPN API for today's live NCAAB slate...")
    url = "http://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
    
    try:
        response = requests.get(url)
        data = response.json()
        games = []
        
        for event in data.get('events', []):
            competitors = event['competitions'][0]['competitors']
            
            # Isolate the Home and Away teams
            home_team = next(c['team']['shortDisplayName'] for c in competitors if c['homeAway'] == 'home')
            away_team = next(c['team']['shortDisplayName'] for c in competitors if c['homeAway'] == 'away')
            
            games.append((away_team, home_team))
            
        print(f"✅ Found {len(games)} live NCAAB games on the board.")
        return games
    except Exception as e:
        print(f"❌ API Failure: {e}")
        return []
# ==========================================
# 1. HELPER FUNCTIONS
# ==========================================
def get_american_odds(prob):
    """Converts a true probability into American Fair Odds."""
    if prob <= 0: return "+99999"
    if prob >= 1.0: return "-99999"
    if prob > 0.50: return int((prob / (1.0 - prob)) * -100)
    else: return int((100.0 / prob) - 100)

# ==========================================
# 2. THE UNIVERSAL API ADAPTER (REALISM TUNED)
# ==========================================
def get_universal_team_stats(sport, team_name):
    """
    Tuned Baselines for Realistic Scoring. 
    NCAAB averages ~71, NFL ~23, NBA ~114.
    """
    time.sleep(0.1) 
    
    baselines = {
        "NBA":   {'off': 114.5, 'def': 114.5, 'vol': 12.0},
        "NCAAB": {'off': 71.2,  'def': 71.2,  'vol': 10.5}, # Tuned for College
        "NFL":   {'off': 23.2,  'def': 23.2,  'vol': 13.5},
        "NCAAF": {'off': 28.5,  'def': 28.5,  'vol': 14.5},
        "NHL":   {'off': 3.1,   'def': 3.1,   'vol': 1.1}, 
        "MLB":   {'off': 4.4,   'def': 4.4,   'vol': 1.9}, 
        "SOCCER":{'off': 1.4,   'def': 1.4,   'vol': 0.8}  
    }
    
    base = baselines.get(sport.upper(), baselines["NBA"])
    # Random modifier to simulate team strength differences
    modifier = np.random.uniform(-0.08, 0.08) 
    
    return {
        'name': team_name,
        'off_mean': base['off'] * (1 + modifier),
        'def_mean': base['def'] * (1 - modifier), 
        'volatility': base['vol']
    }

# ==========================================
# 3. THE MULTI-SPORT DPIM SIMULATOR
# ==========================================
def simulate_universal_match(sport, team_a_input, team_b_input, target_odds=-110):
    sport = sport.upper()
    print(f"🤖 Simulating {sport}: {team_a_input} @ {team_b_input}...")
    
    team_a = get_universal_team_stats(sport, team_a_input)
    team_b = get_universal_team_stats(sport, team_b_input)
    
    # Matchup Blending (DPIM)
    a_expected = (team_a['off_mean'] + team_b['def_mean']) / 2
    b_expected = (team_b['off_mean'] + team_a['def_mean']) / 2
    
    simulations = 100000
    
    # --- DYNAMIC PHYSICS ENGINE ---
    if sport in ["NBA", "NCAAB", "NFL", "NCAAF"]:
        # Basketball/Football uses Normal Distribution for 'Chunky' scoring
        raw_a = np.random.normal(loc=a_expected, scale=team_a['volatility'], size=simulations)
        raw_b = np.random.normal(loc=b_expected, scale=team_b['volatility'], size=simulations)
    else:
        # Soccer/Hockey/Baseball uses Poisson for 'Event-based' scoring
        raw_a = np.random.poisson(lam=a_expected, size=simulations)
        raw_b = np.random.poisson(lam=b_expected, size=simulations)
    
    # REALISM: Round to whole integers and prevent negative scores
    team_a_scores = np.maximum(np.round(raw_a), 0).astype(int)
    team_b_scores = np.maximum(np.round(raw_b), 0).astype(int)
    
    # OT Tie-Breaker Logic (Prevents ties in sports that don't have them)
    ties = team_a_scores == team_b_scores
    if sport in ["NBA", "NCAAB", "NFL", "NHL"]:
        ot_winner = np.random.rand(simulations) > 0.5
        team_a_scores[ties & ot_winner] += 1
        team_b_scores[ties & ~ot_winner] += 1

    a_win_prob = np.sum(team_a_scores > team_b_scores) / simulations
    b_win_prob = 1.0 - a_win_prob
    
    # Calculate EV based on standard -110 juice (1.909 decimal)
    decimal_odds = 1.909 
    if a_win_prob > b_win_prob:
        bet_team = team_a['name']
        ev_perc = ((a_win_prob * decimal_odds) - 1) * 100
    else:
        bet_team = team_b['name']
        ev_perc = ((b_win_prob * decimal_odds) - 1) * 100

    return {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Sport": sport,
        "Game": f"{team_a['name']} @ {team_b['name']}",
        "Bet": f"{bet_team} ML",
        "Odds": target_odds,
        "EV": f"{ev_perc:.1f}%",
        "Result": "Pending", # Added to prevent Dashboard crashes
        "QES": round(ev_perc * 0.85, 2) # Quant Edge Score calculation
    }

# ==========================================
# 4. GITHUB CLOUD UPLOADER (SECURE & MODERN)
# ==========================================
def push_to_github(file_path="ev_log.csv", repo_name="hgully/quant-syndicate"):
    print("\n☁️ Connecting to GitHub Vault...")
    token = os.getenv("GITHUB_TOKEN") 
    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        repo = g.get_repo(repo_name)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # We explicitly tell it to use the 'main' branch
        contents = repo.get_contents(file_path, ref="main") 
        repo.update_file(
            path=contents.path, 
            message=f"🤖 Update: {datetime.now().strftime('%H:%M')}", 
            content=content, 
            sha=contents.sha,
            branch="main" # <--- FORCE MAIN BRANCH
        )
        print(f"✅ Success! Pushed to MAIN branch.")
    except Exception as e:
        print(f"❌ PUSH FAILED: {e}")

# ==========================================
# 5. MASTER EXECUTION PIPELINE
# ==========================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 QUANT SYNDICATE: LIVE API SLATE GENERATOR")
    print("=" * 60)
    
    results = []
    
    # 1. Auto-Fetch the real games for today
    todays_ncaab_games = get_live_ncaab_games()
    
    # 2. Feed every real game into your 100k Simulator
    for away, home in todays_ncaab_games:
        results.append(simulate_universal_match("NCAAB", away, home))
        
    # Failsafe: If no college games are playing today, run a test game
    if len(results) == 0:
        print("⚠️ No NCAAB games found today. Running diagnostic...")
        results.append(simulate_universal_match("NBA", "Suns", "Celtics"))
    
    # 3. Save to CSV
    df = pd.DataFrame(results)
    csv_file = "ev_log.csv"
    df.to_csv(csv_file, index=False)
    print(f"\n💾 Local Database ({csv_file}) ready with {len(results)} live games.")
    
    # 4. Push to GitHub
    push_to_github(file_path=csv_file)
    print("=" * 60)
    print("🏁 PIPELINE COMPLETE")
    print("=" * 60)