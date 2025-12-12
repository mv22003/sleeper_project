from collections import defaultdict

def get_all_user_leagues(client, user_id: str, start_year=2018, end_year=2025):
    grouped = defaultdict(list)

    for season in range(start_year, end_year + 1):
        leagues = client.get_user_leagues(user_id, season)

        for league in leagues:

            # ✅ FILTER: only include dynasty leagues
            if league.get("settings", {}).get("type") != 2:
                continue

            grouped[league["name"]].append({
                "league_id": league["league_id"],
                "season": season,
                "avatar": league.get("avatar")
            })

    # Sort leagues newest → oldest
    for lst in grouped.values():
        lst.sort(key=lambda x: x["season"], reverse=True)

    return grouped
