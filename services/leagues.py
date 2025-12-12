# backend/services/leagues.py
from collections import defaultdict

def get_all_user_leagues(client, user_id: str, start_year=2018, end_year=2025):
    grouped = defaultdict(list)

    for season in range(start_year, end_year + 1):
        leagues = client.get_user_leagues(user_id, season)

        for league in leagues:
            grouped[league["name"]].append({
                "league_id": league["league_id"],
                "season": season,
                "avatar": league.get("avatar")
            })

    for leagues in grouped.values():
        leagues.sort(key=lambda x: x["season"], reverse=True)

    return grouped
