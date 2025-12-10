from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sleeper import SleeperClient

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

# Sleeper client instance
client = SleeperClient()

# --------------------------------------------------------
# HOME PAGE
# --------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# --------------------------------------------------------
# FORM HANDLER -> SHOW ROSTER PAGE
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

    # Get rosters
    rosters = client.get_rosters(league_id)
    roster = next((r for r in rosters if r.get("owner_id") == user_id), None)

    if not roster:
        return templates.TemplateResponse(
            "roster.html",
            {"request": request, "error": f"User '{username}' not in league '{league_id}'.", "data": None}
        )

    # Player database
    players = client.get_players()

    # Organize players by position
    positions = {
        "QB": [],
        "RB": [],
        "WR": [],
        "TE": [],
        "K": [],
        "DEF": [],
        "OTHER": []
    }

    for pid in roster.get("players", []):
        p = players.get(str(pid))
        if not p:
            continue

        team = p.get("team", "FA")
        team_logo = None
        if team not in [None, "FA"]:
            team_logo = f"https://a.espncdn.com/i/teamlogos/nfl/500/{team.lower()}.png"

        # Try official provided headshot
        headshot = p.get("metadata", {}).get("headshot")

        # Use modern Sleeper fallback format (correct one)
        if not headshot:
            headshot = f"https://sleepercdn.com/content/nfl/players/thumb/{pid}.jpg"

        player_info = {
            "id": pid,
            "name": p.get("full_name"),
            "position": p.get("position"),
            "team": team,
            "headshot": headshot,
            "team_logo": team_logo
        }



        pos = p.get("position")

        if pos in positions:
            positions[pos].append(player_info)
        else:
            positions["OTHER"].append(player_info)

    # Build clean response
    data = {
        "username": username,
        "season": season,
        "league": {
            "league_id": league_id,
            "name": league.get("name")
        },
        "positions": positions
    }

    return templates.TemplateResponse(
        "roster.html",
        {"request": request, "data": data, "error": None}
    )
