"""
main.py

FastAPI entry point for the Sleeper Dynasty Analyzer.

Responsibilities:
- Configure the FastAPI application
- Register middleware (CORS)
- Initialize shared clients (SleeperClient)
- Define HTTP endpoints
- Delegate business logic to service modules

for testing run:
uvicorn backend.main:app --reload


"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from sleeper import SleeperClient

# Service modules contain all non-trivial logic
from backend.services.ktc import *
from backend.services.leagues import *
from backend.services.players import *
from backend.services.lineup import *


# Create the FastAPI application
app = FastAPI(
    title="Sleeper API",
    description="Sleeper Dynasty League Analyzer",
    version="1.0.0"
)

# Enable cross-origin requests so frontend JS can call API endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jinja2 template engine for HTML rendering
templates = Jinja2Templates(directory="templates")

# Single shared client for all Sleeper API requests
client = SleeperClient()


@app.get("/user_leagues")
def user_leagues(username: str):
    """
    Return all dynasty leagues for a user, grouped by league name.

    This endpoint is called asynchronously by the frontend
    after the user enters their username.
    """
    # Resolve username → user_id
    user = client.get_user(username)

    # Sleeper returns an object without user_id when user is invalid
    if "user_id" not in user:
        return {"error": "User not found"}

    # Delegate season scanning & dynasty filtering to the service layer
    return get_all_user_leagues(client, user["user_id"])


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Render the landing page.

    The page itself handles all dynamic behavior (JS),
    this endpoint only serves the template.
    """
    return templates.TemplateResponse(
        "home.html",
        {"request": request}
    )


@app.get("/show_roster", response_class=HTMLResponse)
def show_roster(request: Request, username: str, league_id: str):
    """
    Render the roster breakdown for a specific league.

    This endpoint performs orchestration:
    - Validate inputs
    - Fetch data from external APIs
    - Shape data for template consumption
    """

    # Fetch and validate the user
    user = client.get_user(username)
    if "user_id" not in user:
        return templates.TemplateResponse(
            "roster.html",
            {
                "request": request,
                "error": f"User '{username}' not found.",
                "data": None
            }
        )

    user_id = user["user_id"]

    # Fetch league metadata to confirm validity and extract season
    league = client.get_league(league_id)

    # Fetch number of roster slots for each position, bench, IR & TAXI
    roster_slots = normalize_roster_slots(
        league.get("roster_positions", []),
        league.get("settings", {})
    )

    if "league_id" not in league:
        return templates.TemplateResponse(
            "roster.html",
            {
                "request": request,
                "error": f"League '{league_id}' not found.",
                "data": None
            }
        )

    season = league.get("season")

    # Identify the roster owned by this user in the league
    rosters = client.get_rosters(league_id)
    roster = next(
        (r for r in rosters if r.get("owner_id") == user_id),
        None
    )

    if not roster:
        return templates.TemplateResponse(
            "roster.html",
            {
                "request": request,
                "error": "User does not own a roster in this league.",
                "data": None
            }
        )

    # Fetch KeepTradeCut values (cached to avoid repeated scraping)
    ktc_data = get_ktc_values()

    # Build a fast lookup table using normalized player names
    ktc_by_name = {
        normalize_name(item["name"]): item
        for item in ktc_data
    }

    # Fetch the global Sleeper player dictionary
    players = client.get_players()

    # Buckets used to group players for display
    positions = {
        "QB": [],
        "RB": [],
        "WR": [],
        "TE": [],
        "OTHER": []
    }

    # Translate raw player IDs into display-ready player objects
    for pid in roster.get("players", []):
        player = players.get(str(pid))
        if not player:
            continue

        # Team and team logo (skip free agents)
        team = player.get("team", "FA")
        team_logo = (
            f"https://a.espncdn.com/i/teamlogos/nfl/500/{team.lower()}.png"
            if team not in [None, "FA"]
            else None
        )

        # Prefer Sleeper headshot, fall back to default CDN
        headshot = (
            player.get("metadata", {}).get("headshot")
            or f"https://sleepercdn.com/content/nfl/players/thumb/{pid}.jpg"
        )

        # Match Sleeper player to KTC value using normalized names
        norm_name = normalize_name(player.get("full_name"))
        ktc_entry = ktc_by_name.get(norm_name)

        player_info = {
            "id": pid,
            "name": player.get("full_name"),
            "position": player.get("position"),
            "team": team,
            "headshot": headshot,
            "team_logo": team_logo,
            "ktc_value": ktc_entry["value"] if ktc_entry else 0,
            "ktc_pos_rank": ktc_entry["pos_rank"] if ktc_entry else None
        }

        # Assign player to the appropriate position bucket
        pos = player_info["position"]
        positions[pos if pos in positions else "OTHER"].append(player_info)

    # Sort each position group by descending KTC value
    for lst in positions.values():
        lst.sort(key=lambda p: p["ktc_value"], reverse=True)

    # Compute total KTC value per position group
    totals = {
        pos: sum(p["ktc_value"] for p in lst)
        for pos, lst in positions.items()
    }

    # Final object passed to the template renderer
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
        {
            "request": request,
            "data": data,
            "error": None
        }
    )