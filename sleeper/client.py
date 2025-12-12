import requests
import time


# Base URL for the Sleeper public API
BASE_URL = "https://api.sleeper.app/v1"

# Cache for Sleeper players endpoint (large and mostly static)
PLAYERS_CACHE = None
PLAYERS_CACHE_TIME = 0
PLAYERS_CACHE_TTL = 3600 * 24  # 24 hours

# Cache for league rosters (short-lived for freshness)
ROSTERS_CACHE = {}
ROSTERS_CACHE_TIME = {}
ROSTERS_CACHE_TTL = 60  # 60 seconds


class SleeperClient:
    """
    Thin wrapper around the Sleeper public API.

    Purpose:
    - Centralize all HTTP requests to Sleeper
    - Provide clearly named methods for each API endpoint
    - Cache expensive or frequently accessed responses

    This class contains no business logic.
    """

    def __init__(self):
        # Store base API URL for reuse
        self.base = BASE_URL

    def get_user(self, username: str):
        """
        Fetch a Sleeper user by username.
        """
        url = f"{self.base}/user/{username}"
        return requests.get(url).json()

    def get_user_leagues(self, user_id: str, season: int):
        """
        Fetch all leagues for a user for a specific NFL season.
        """
        url = f"{self.base}/user/{user_id}/leagues/nfl/{season}"
        return requests.get(url).json()

    def get_league(self, league_id: str):
        """
        Fetch metadata for a specific league.
        """
        url = f"{self.base}/league/{league_id}"
        return requests.get(url).json()

    def get_rosters(self, league_id: str):
        global ROSTERS_CACHE, ROSTERS_CACHE_TIME

        cached = ROSTERS_CACHE.get(league_id)
        cached_time = ROSTERS_CACHE_TIME.get(league_id)

        # Cache hit: return cached rosters
        if cached and cached_time and (time.time() - cached_time) < ROSTERS_CACHE_TTL:
            return cached

        # Cache miss: fetch from Sleeper
        url = f"{self.base}/league/{league_id}/rosters"
        data = requests.get(url).json()

        # Store in cache
        ROSTERS_CACHE[league_id] = data
        ROSTERS_CACHE_TIME[league_id] = time.time()

        return data



    def get_matchups(self, league_id: str, week: int):
        """
        Fetch weekly matchup data for a league.
        """
        url = f"{self.base}/league/{league_id}/matchups/{week}"
        return requests.get(url).json()

    def get_players(self):
        """
        Fetch the full Sleeper NFL players dictionary.

        Cached aggressively because the payload is large and rarely changes.
        """
        global PLAYERS_CACHE, PLAYERS_CACHE_TIME

        # Return cached data if still valid
        if PLAYERS_CACHE and (time.time() - PLAYERS_CACHE_TIME) < PLAYERS_CACHE_TTL:
            return PLAYERS_CACHE

        # Fetch fresh data from Sleeper API
        url = f"{self.base}/players/nfl"
        data = requests.get(url).json()

        # Update cache
        PLAYERS_CACHE = data
        PLAYERS_CACHE_TIME = time.time()

        return data
