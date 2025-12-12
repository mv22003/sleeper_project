from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sleeper import SleeperClient

from backend.services.ktc import *
from backend.services.leagues import *
from backend.services.players import *

KTC_CACHE = None
KTC_CACHE_TIME = 0
KTC_CACHE_TTL = 3600 * 12  # refresh every 12 hours

# --------------------------------------------------------
# Setup FastAPI App
# --------------------------------------------------------
app = FastAPI(title="Sleeper API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Template loader
templates = Jinja2Templates(directory="templates")

# Sleeper API client
client = SleeperClient()

@app.get("/user_leagues")
def user_leagues(username: str):
    user = client.get_user(username)
    if "user_id" not in user:
        return {"error": "User not found"}

    grouped = get_all_user_leagues(client, user["user_id"])
    return grouped


# --------------------------------------------------------
# HOME PAGE
# --------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


# --------------------------------------------------------
# SHOW ROSTER PAGE
# --------------------------------------------------------
@app.get("/show_roster", response_class=HTMLResponse)
def show_roster(request: Request, username: str, league_id: str):

    # Validate user
    user = client.get_user(username)
    if not user or "user_id" not in user:
        return templates.TemplateResponse(
            "roster.html",
            {"request": request, "error": f"User '{username}' not found.", "data": None}
        )
    user_id = user["user_id"]

    # Get league
    league = client.get_league(league_id)
    if "league_id" not in league:
        return templates.TemplateResponse(
            "roster.html",
            {"request": request, "error": f"League '{league_id}' not found.", "data": None}
        )
    season = league.get("season")

    # Find user's roster
    rosters = client.get_rosters(league_id)
    roster = next((r for r in rosters if r.get("owner_id") == user_id), None)

    if not roster:
        return templates.TemplateResponse(
            "roster.html",
            {"request": request, "error": f"User '{username}' not in league '{league_id}'.", "data": None}
        )

    # --------------------------------------------------------
    # Get KTC Values
    # --------------------------------------------------------
    ktc_data = get_ktc_values()

    # Build lookup by normalized name
    ktc_by_name = {}
    for item in ktc_data:
        norm = normalize_name(item["name"])
        ktc_by_name[norm] = item


    # --------------------------------------------------------
    # Build Player List
    # --------------------------------------------------------
    players = client.get_players()

    positions = {
        "QB": [],
        "RB": [],
        "WR": [],
        "TE": [],
        "OTHER": []
    }

    for pid in roster.get("players", []):
        p = players.get(str(pid))
        if not p:
            continue

        # -------- Team Logo --------
        team = p.get("team", "FA")
        team_logo = None
        if team not in [None, "FA"]:
            team_logo = f"https://a.espncdn.com/i/teamlogos/nfl/500/{team.lower()}.png"

        # -------- Player Headshot --------
        headshot = p.get("metadata", {}).get("headshot")
        if not headshot:
            headshot = f"https://sleepercdn.com/content/nfl/players/thumb/{pid}.jpg"

        # -------- KTC Value Lookup (normalized) --------
        norm_name = normalize_name(p.get("full_name"))
        ktc_entry = ktc_by_name.get(norm_name)
        ktc_pos_rank = ktc_entry["pos_rank"] if ktc_entry else None
        ktc_value = ktc_entry["value"] if ktc_entry else 0



        player_info = {
            "id": pid,
            "name": p.get("full_name"),
            "position": p.get("position"),
            "team": team,
            "headshot": headshot,
            "team_logo": team_logo,
            "ktc_value": ktc_value,
            "ktc_pos_rank": ktc_pos_rank
        }

        pos = p.get("position")
        if pos in positions:
            positions[pos].append(player_info)
        else:
            positions["OTHER"].append(player_info)

    # --------------------------------------------------------
    # SORT BY KTC VALUE (DESCENDING)
    # --------------------------------------------------------
    for pos, lst in positions.items():
        lst.sort(key=lambda p: p["ktc_value"], reverse=True)

    # --------------------------------------------------------
    # TOTAL VALUE PER POSITION
    # --------------------------------------------------------
    totals = {
        pos: sum(player["ktc_value"] for player in lst)
        for pos, lst in positions.items()
    }

    # --------------------------------------------------------
    # Build Page Data
    # --------------------------------------------------------
    data = {
        "username": username,
        "season": season,
        "league": {
            "league_id": league_id,
            "name": league.get("name")
        },
        "positions": positions,
        "totals": totals  
    }


    return templates.TemplateResponse(
        "roster.html",
        {"request": request, "data": data, "error": None}
    )
