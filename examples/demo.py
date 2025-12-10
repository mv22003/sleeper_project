from sleeper import SleeperClient

def print_separator():
    print("\n" + "="*50 + "\n")

def main():
    client = SleeperClient()

    print_separator()
    print("=== Sleeper API Full Demo ===")
    print_separator()

    username = input("Enter your Sleeper username: ").strip()
    season = int(input("Enter season year (e.g., 2025): ").strip())

    print_separator()
    print(f"Fetching user '{username}'...")
    user = client.get_user(username)
    print(user)

    if "user_id" not in user:
        print("\n❌ Error: User not found.\n")
        return

    user_id = user["user_id"]

    print_separator()
    print(f"Fetching leagues for {season}...")
    leagues = client.get_user_leagues(user_id, season)
    print(f"Found {len(leagues)} leagues.")

    for i, league in enumerate(leagues, start=1):
        print(f"{i}. {league['name']} (ID: {league['league_id']})")

    if not leagues:
        print("\n❌ No leagues found for this season.")
        return

    # Select a league
    print_separator()
    league_index = int(input("Select a league number to test functions: ")) - 1
    league = leagues[league_index]
    league_id = league["league_id"]

    print(f"\nSelected league: {league['name']} (ID: {league_id})")

    # Fetch league metadata
    print_separator()
    print("Fetching league metadata...")
    league_data = client.get_league(league_id)
    print(league_data)

    # Fetch rosters
    print_separator()
    print("Fetching rosters...")
    rosters = client.get_rosters(league_id)
    print(f"Found {len(rosters)} rosters.")
    print(rosters)

    # Fetch matchups
    print_separator()
    week = int(input("Enter a week number to fetch matchups (1–18): ").strip())
    print(f"\nFetching matchups for week {week}...")
    matchups = client.get_matchups(league_id, week)
    print(matchups)

    # Fetch players
    print_separator()
    print("Fetching all NFL players (this is a large download)...")
    players = client.get_players()
    print(f"Total players returned: {len(players)}")

    # Print example player
    sample_key = next(iter(players))
    print("\nSample player entry:")
    print(players[sample_key])

    print_separator()
    print("Demo complete.")

if __name__ == "__main__":
    main()
