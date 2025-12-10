from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sleeper import SleeperClient
import requests
import re
import time

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


# --------------------------------------------------------
# Utility — Normalize player names for KTC matching
# --------------------------------------------------------
def normalize_name(name: str):
    if not name:
        return ""

    name = name.lower()

    # remove punctuation
    name = re.sub(r"[^a-z0-9\s]", "", name)

    # remove team abbreviations (NO, BUF, CHI, etc.)
    name = re.sub(r"\b[a-z]{2,3}\b", "", name)

    # remove suffixes
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    parts = name.split()
    parts = [p for p in parts if p not in suffixes]

    # collapse multiple spaces
    name = " ".join(parts)
    return name.strip()



# --------------------------------------------------------
# KTC Value Fetcher
# Credits to: https://github.com/ees4/KeepTradeCut-Scraper/blob/main
# --------------------------------------------------------
from backend.ktc_scraper import scrape_ktc_sf

def get_ktc_values():
    global KTC_CACHE, KTC_CACHE_TIME

    if KTC_CACHE and (time.time() - KTC_CACHE_TIME) < KTC_CACHE_TTL:
        print("Using cached KTC data")
        return KTC_CACHE

    print("Scraping fresh KTC data...")
    data = scrape_ktc_sf()

    KTC_CACHE = data
    KTC_CACHE_TIME = time.time()

    return data



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
        ktc_value = ktc_entry["value"] if ktc_entry else 0



        player_info = {
            "id": pid,
            "name": p.get("full_name"),
            "position": p.get("position"),
            "team": team,
            "headshot": headshot,
            "team_logo": team_logo,
            "ktc_value": ktc_value,
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
