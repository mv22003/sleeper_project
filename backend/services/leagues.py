from collections import defaultdict
import time


# --------------------------------------------------
# User Leagues Cache
# --------------------------------------------------
# Cache is keyed by user_id because leagues are user-specific
USER_LEAGUES_CACHE = {}
USER_LEAGUES_CACHE_TIME = {}
USER_LEAGUES_CACHE_TTL = 3600 * 6  # 6 hours


def get_all_user_leagues(client, user_id: str, start_year=2018, end_year=2025):
    """
    Retrieve and group all dynasty leagues for a user across multiple seasons.

    Responsibilities:
    - Query Sleeper for user leagues season-by-season
    - Filter out non-dynasty leagues
    - Group leagues by league name
    - Preserve league_id and season for frontend selection
    - Sort seasons newest → oldest for usability
    """

    # --------------------------------------------------
    # Cache check (fast exit)
    # --------------------------------------------------
    cached = USER_LEAGUES_CACHE.get(user_id)
    cached_time = USER_LEAGUES_CACHE_TIME.get(user_id)

    if cached and cached_time and (time.time() - cached_time) < USER_LEAGUES_CACHE_TTL:
        print("CACHE HIT: user leagues", user_id)
        return cached
    
    print("CACHE MISS: user leagues", user_id)

    # Dictionary keyed by league name, each value is a list of seasons
    grouped = defaultdict(list)

    # Iterate through each NFL season in the configured range
    for season in range(start_year, end_year + 1):
        leagues = client.get_user_leagues(user_id, season)

        for league in leagues:

            # Sleeper league type:
            # 2 = dynasty, other values represent redraft / bestball / etc.
            if league.get("settings", {}).get("type") != 2:
                continue

            # Store only the fields needed by the frontend
            grouped[league["name"]].append({
                "league_id": league["league_id"],
                "season": season,
                "avatar": league.get("avatar")
            })

    # Sort each league's seasons from newest to oldest
    # This allows the UI to default to the most recent season
    for lst in grouped.values():
        lst.sort(key=lambda x: x["season"], reverse=True)

    # --------------------------------------------------
    # Store result in cache
    # --------------------------------------------------
    USER_LEAGUES_CACHE[user_id] = grouped
    USER_LEAGUES_CACHE_TIME[user_id] = time.time()

    return grouped
