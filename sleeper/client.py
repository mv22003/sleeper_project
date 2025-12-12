import requests

# Base URL for the Sleeper public API
BASE_URL = "https://api.sleeper.app/v1"


class SleeperClient:
    """
    Thin wrapper around the Sleeper public API.

    Purpose:
    - Centralize all HTTP requests to Sleeper
    - Provide clearly named methods for each API endpoint
    - Keep request logic out of route handlers and services

    This class intentionally contains no business logic.
    """

    def __init__(self):
        # Store base API URL for reuse
        self.base = BASE_URL

    def get_user(self, username: str):
        """
        Fetch a Sleeper user by username.

        Args:
            username (str): Sleeper username

        Returns:
            dict: User object returned by Sleeper.
                  If user does not exist, response will not contain 'user_id'.
        """
        url = f"{self.base}/user/{username}"
        return requests.get(url).json()

    def get_user_leagues(self, user_id: str, season: int):
        """
        Fetch all leagues for a user for a specific NFL season.

        Args:
            user_id (str): Sleeper user ID
            season (int): NFL season year

        Returns:
            list[dict]: List of league objects for that season.
        """
        url = f"{self.base}/user/{user_id}/leagues/nfl/{season}"
        return requests.get(url).json()

    def get_league(self, league_id: str):
        """
        Fetch metadata for a specific league.

        Args:
            league_id (str): Sleeper league ID

        Returns:
            dict: League metadata including name, season, and settings.
        """
        url = f"{self.base}/league/{league_id}"
        return requests.get(url).json()

    def get_rosters(self, league_id: str):
        """
        Fetch all rosters for a league.

        Args:
            league_id (str): Sleeper league ID

        Returns:
            list[dict]: One roster per team in the league.
        """
        url = f"{self.base}/league/{league_id}/rosters"
        return requests.get(url).json()

    def get_matchups(self, league_id: str, week: int):
        """
        Fetch weekly matchup data for a league.

        Args:
            league_id (str): Sleeper league ID
            week (int): Week number (1–18)

        Returns:
            list[dict]: Matchup data for the given week.
        """
        url = f"{self.base}/league/{league_id}/matchups/{week}"
        return requests.get(url).json()

    def get_players(self):
        """
        Fetch the full Sleeper NFL players dictionary.

        Returns:
            dict: Mapping of player_id → player metadata.

        Notes:
            - This is a large payload
            - Sleeper recommends caching this response
            - Used as the source of truth for player names, positions, teams
        """
        url = f"{self.base}/players/nfl"
        return requests.get(url).json()
