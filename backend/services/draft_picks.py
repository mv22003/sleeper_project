# backend/services/draft_picks.py

"""
Draft pick domain logic.

Responsibilities:
- Determine which draft seasons are relevant
- Generate default draft picks for all teams
- Apply traded pick mutations
- Return picks grouped by owner_id

This module contains NO API calls.
"""

from collections import defaultdict


# Internal helpers
def _collect_pick_seasons(league: dict, traded_picks: list[dict]) -> list[int]:
    """
    Determine which draft seasons should exist.

    Includes:
    - All seasons referenced by traded picks
    - The upcoming draft year (league.season + 1)
    """
    seasons = set()

    for p in traded_picks:
        seasons.add(int(p["season"]))

    # Always include the next draft year
    seasons.add(int(league["season"]) + 1)

    return sorted(seasons)


def _generate_default_picks(
    league: dict,
    rosters: list[dict],
    seasons: list[int]
) -> list[dict]:
    """
    Generate all default draft picks assuming no trades occurred.
    """
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


def _apply_traded_picks(
    default_picks: list[dict],
    traded_picks: list[dict]
) -> list[dict]:
    """
    Apply traded pick mutations to the default pick universe.
    """
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


def build_league_picks(
    league: dict,
    rosters: list[dict],
    traded_picks: list[dict]
) -> dict[str, list[dict]]:
    """
    Build all draft picks for a league and group them by owner_id.
    """
    seasons = _collect_pick_seasons(league, traded_picks)

    default_picks = _generate_default_picks(
        league=league,
        rosters=rosters,
        seasons=seasons
    )

    all_picks = _apply_traded_picks(default_picks, traded_picks)

    # Map roster_id -> owner_id
    roster_id_to_owner = {
        r["roster_id"]: str(r.get("owner_id"))
        for r in rosters
    }

    picks_by_owner = defaultdict(list)

    for raw_pick in all_picks:
        pick = _normalize_pick(raw_pick, roster_id_to_owner)

        # Only attach if ownership resolved correctly
        if pick["current_owner_id"]:
            picks_by_owner[pick["current_owner_id"]].append(pick)

    return dict(picks_by_owner)


def _normalize_pick(pick: dict, roster_id_to_owner: dict) -> dict:
    return {
        "season": int(pick["season"]),
        "round": int(pick["round"]),
        "original_owner_id": roster_id_to_owner.get(
            int(pick["original_owner_roster_id"])
        ),
        "current_owner_id": roster_id_to_owner.get(
            int(pick["current_owner_roster_id"])
        ),
        "source": pick.get("source", "generated")
    }

