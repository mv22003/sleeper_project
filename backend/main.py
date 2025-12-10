from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sleeper import SleeperClient

# --------------------------------------------------------
# Setup FastAPI App
# --------------------------------------------------------
app = FastAPI(title="Sleeper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create global instance of the Sleeper client
client = SleeperClient()

# --------------------------------------------------------
# Root Test Endpoint
# --------------------------------------------------------
@app.get("/")
def home():
    return {"message": "API is running!"}

# --------------------------------------------------------
# 1. ROSTER FOR ONE SEASON
# --------------------------------------------------------
@app.get("/roster/{username}/{season}")
def get_user_roster_by_season(username: str, season: int):
    """
    Returns the user's roster for a given NFL season.
    This is the foundation for comparing seasons.
    """
    # 1. Fetch user
    user = client.get_user(username)
    if "user_id" not in user:
        return {"error": "User not found"}

    user_id = user["user_id"]

    # 2. Fetch user's leagues for this season
    leagues = client.get_user_leagues(user_id, season)
    if not leagues:
        return {"error": f"No leagues found for {season}"}

    # 3. Pick FIRST league (later you'll let user choose)
    league = leagues[0]
    league_id = league["league_id"]

    # 4. Fetch rosters
    rosters = client.get_rosters(league_id)

    # 5. Find THIS user's roster
    roster = next((r for r in rosters if r.get("owner_id") == user_id), None)
    if not roster:
        return {"error": "Roster not found for user in this league"}

    # 6. Fetch Sleeper player database
    players = client.get_players()

    # 7. Convert player IDs → readable info
    detailed_players = []
    for pid in roster.get("players", []):
        p = players.get(str(pid))
        if not p:
            continue
        detailed_players.append({
            "id": pid,
            "name": p.get("full_name"),
            "position": p.get("position"),
            "team": p.get("team"),
        })

    return {
        "username": username,
        "season": season,
        "league_name": league.get("name"),
        "league_id": league_id,
        "record": {
            "wins": roster.get("settings", {}).get("wins"),
            "losses": roster.get("settings", {}).get("losses"),
        },
        "players": detailed_players,
    }

# --------------------------------------------------------
# 2. LEAGUE HISTORY FOR THIS USER
# --------------------------------------------------------
@app.get("/league_history/{league_id}/{username}")
def get_league_history(league_id: str, username: str):
    """
    Walks backwards through previous_league_id to reconstruct
    this user's full dynasty history inside a league.
    """
    # Fetch user ID
    user = client.get_user(username)
    if "user_id" not in user:
        return {"error": "User not found"}

    user_id = user["user_id"]

    history = {}
    current_league_id = league_id

    # Follow the chain of league IDs backwards
    while current_league_id:
        league = client.get_league(current_league_id)
        if not league or "season" not in league:
            break

        season_year = league["season"]

        # Fetch rosters for this season
        rosters = client.get_rosters(current_league_id)
        roster = next((r for r in rosters if r.get("owner_id") == user_id), None)

        # Save roster for this season
        history[season_year] = {
            "league_id": current_league_id,
            "roster": roster
        }

        # Move to previous season
        current_league_id = league.get("previous_league_id")

    return {
        "username": username,
        "history": history
    }
