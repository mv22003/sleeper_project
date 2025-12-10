import requests

BASE_URL = "https://api.sleeper.app/v1"

class SleeperClient:
    def __init__(self):
        self.base = BASE_URL

    def get_user(self, username: str):
        """Fetch a user by username."""
        url = f"{self.base}/user/{username}"
        return requests.get(url).json()

    def get_user_leagues(self, user_id: str, season: int):
        """Fetch all leagues for a user for a given NFL season."""
        url = f"{self.base}/user/{user_id}/leagues/nfl/{season}"
        return requests.get(url).json()

    def get_league(self, league_id: str):
        """Fetch league metadata."""
        url = f"{self.base}/league/{league_id}"
        return requests.get(url).json()

    def get_rosters(self, league_id: str):
        """Fetch roster info for a league."""
        url = f"{self.base}/league/{league_id}/rosters"
        return requests.get(url).json()

    def get_matchups(self, league_id: str, week: int):
        """Fetch matchups for a specific week in a league."""
        url = f"{self.base}/league/{league_id}/matchups/{week}"
        return requests.get(url).json()

    def get_players(self):
        """Fetch the full Sleeper players dictionary."""
        url = f"{self.base}/players/nfl"
        return requests.get(url).json()
