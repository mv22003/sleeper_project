# backend/services/extract_data.py

from backend.services.lineup import normalize_roster_slots


def _collect_pick_seasons(league, traded_picks):
    seasons = set()

    for p in traded_picks:
        seasons.add(int(p["season"]))

    seasons.add(int(league["season"]) + 1)

    return sorted(seasons)


def _generate_default_picks(league, rosters, seasons):
    picks = []
    draft_rounds = league["settings"]["draft_rounds"]

    for season in seasons:
        for r in rosters:
            roster_id = r["roster_id"]
            for rd in range(1, draft_rounds + 1):
                picks.append({
                    "season": season,
                    "round": rd,
                    "original_owner_roster_id": roster_id,
                    "current_owner_roster_id": roster_id,
                    "source": "generated"
                })

    return picks


def _apply_traded_picks(default_picks, traded_picks):
    index = {
        (p["season"], p["round"], p["original_owner_roster_id"]): p
        for p in default_picks
    }

    for tp in traded_picks:
        key = (
            int(tp["season"]),
            int(tp["round"]),
            int(tp["roster_id"])
        )

        if key not in index:
            continue

        index[key]["current_owner_roster_id"] = int(tp["owner_id"])
        index[key]["source"] = "traded"
        index[key]["previous_owner_roster_id"] = int(
            tp.get("previous_owner_id", tp["roster_id"])
        )

    return list(index.values())


def build_dynasty_snapshot(client, league_id):
    league = client.get_league(league_id)
    if not league or "league_id" not in league:
        raise ValueError(f"Invalid league_id or league not found: {league_id}")

    rosters = client.get_rosters(league_id)
    players_db = client.get_players()
    traded_picks = client.get_traded_picks(league_id)

    snapshot = {
        "league": {
            "league_id": league_id,
            "name": league.get("name"),
            "season": int(league.get("season")),
            "total_rosters": league.get("total_rosters"),
            "settings": league.get("settings", {}),
            "roster_slots": normalize_roster_slots(
                league.get("roster_positions", []),
                league.get("settings", {})
            ),
        },
        "teams": {}
    }

    for r in rosters:
        owner_id = str(r.get("owner_id"))

        snapshot["teams"][owner_id] = {
            "roster_id": r["roster_id"],
            "players": [],
            "picks": [],
            "starters": r.get("starters", []),
            "reserve": r.get("reserve", []),
            "record": {
                "wins": r.get("settings", {}).get("wins"),
                "losses": r.get("settings", {}).get("losses"),
                "ties": r.get("settings", {}).get("ties"),
                "fpts": r.get("settings", {}).get("fpts"),
                "fpts_against": r.get("settings", {}).get("fpts_against"),
            }
        }

        for pid in r.get("players", []):
            player = players_db.get(str(pid))
            if not player:
                continue

            snapshot["teams"][owner_id]["players"].append({
                "player_id": str(pid),
                "name": player.get("full_name"),
                "position": player.get("position"),
                "team": player.get("team", "FA"),
                "status": player.get("status"),
                "birth_date": player.get("birth_date"),
            })

    pick_seasons = _collect_pick_seasons(league, traded_picks)

    default_picks = _generate_default_picks(
        league=league,
        rosters=rosters,
        seasons=pick_seasons
    )

    all_picks = _apply_traded_picks(default_picks, traded_picks)

    roster_id_to_owner = {
        r["roster_id"]: str(r.get("owner_id"))
        for r in rosters
    }

    for p in all_picks:
        owner_id = roster_id_to_owner.get(p["current_owner_roster_id"])
        if owner_id:
            snapshot["teams"][owner_id]["picks"].append(p)

    return snapshot


def debug_snapshot(snapshot):
    print("League:", snapshot["league"]["name"])
    print("Season:", snapshot["league"]["season"])
    print("Teams:", len(snapshot["teams"]))
    print("")

    for owner, team in snapshot["teams"].items():
        print(
            f"Owner {owner} | "
            f"Players: {len(team['players'])} | "
            f"Picks: {len(team['picks'])}"
        )
