from backend.services.lineup import normalize_roster_slots
from backend.services.draft_picks import build_league_picks
from backend.services.leagues import normalize_league_settings


def build_dynasty_snapshot(client, league_id: str) -> dict:
    """
    Build a complete dynasty snapshot for a league.

    This function orchestrates data collection and delegates
    domain logic to service modules.
    """

    # --------------------------------------------------
    # Fetch core league data
    # --------------------------------------------------
    league = client.get_league(league_id)
    if not league or "league_id" not in league:
        raise ValueError(f"Invalid league_id or league not found: {league_id}")

    rosters = client.get_rosters(league_id)
    players_db = client.get_players()
    traded_picks = client.get_traded_picks(league_id)

    # Build league metadata
    snapshot = {
        "league": {
            "league_id": league_id,
            "name": league.get("name"),
            "season": int(league.get("season")),
            "total_rosters": league.get("total_rosters"),
            "settings": normalize_league_settings(
                    league.get("settings", {})
                ),
            "roster_slots": normalize_roster_slots(
                league.get("roster_positions", []),
                league.get("settings", {})
            ),
        },
        "teams": {}
    }

    # Build teams + players
    for r in rosters:
        owner_id = str(r.get("owner_id"))

        snapshot["teams"][owner_id] = {
            "roster_id": r["roster_id"],

            "assets": {
                "players": [],
                "picks": []
            },

            "lineup": {
                "starters": r.get("starters", []),
                "reserve": r.get("reserve", [])
            },

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

            snapshot["teams"][owner_id]["assets"]["players"].append({
                "player_id": str(pid),
                "name": player.get("full_name"),
                "position": player.get("position"),
                "team": player.get("team", "FA"),
                "birth_date": player.get("birth_date"),
            })


    # Build and attach draft picks
    picks_by_owner = build_league_picks(
        league=league,
        rosters=rosters,
        traded_picks=traded_picks
    )

    for owner_id, picks in picks_by_owner.items():
        if owner_id in snapshot["teams"]:
            snapshot["teams"][owner_id]["picks"] = picks

    return snapshot
