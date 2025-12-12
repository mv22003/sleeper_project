import re


def build_roster_positions(client, roster, ktc_data):
    """
    Build a positional breakdown of a roster enriched with KTC values.

    Responsibilities:
    - Resolve Sleeper player IDs into full player objects
    - Match players to KeepTradeCut values using normalized names
    - Group players by position
    - Sort players within each position by KTC value
    - Compute total KTC value per position

    Returns:
        positions (dict): Players grouped by position
        totals (dict): Total KTC value per position
    """
    # Fetch the global Sleeper player dictionary (id → player data)
    players = client.get_players()

    # Build a lookup table for KTC players using normalized names
    ktc_by_name = {
        normalize_name(p["name"]): p for p in ktc_data
    }

    # Position buckets used by the UI
    positions = {"QB": [], "RB": [], "WR": [], "TE": []}

    # Iterate through player IDs owned by the roster
    for pid in roster.get("players", []):
        p = players.get(str(pid))
        if not p:
            continue

        # Normalize Sleeper player name for KTC matching
        norm_name = normalize_name(p.get("full_name"))
        ktc_entry = ktc_by_name.get(norm_name)

        # Append player info enriched with KTC data
        positions[p["position"]].append({
            "id": pid,
            "name": p.get("full_name"),
            "position": p.get("position"),
            "team": p.get("team", "FA"),
            "headshot": p.get("metadata", {}).get("headshot"),
            "ktc_value": ktc_entry["value"] if ktc_entry else 0,
            "ktc_pos_rank": ktc_entry["pos_rank"] if ktc_entry else None
        })

    # Sort players within each position by descending KTC value
    for lst in positions.values():
        lst.sort(key=lambda p: p["ktc_value"], reverse=True)

    # Compute total KTC value per position
    totals = {
        pos: sum(p["ktc_value"] for p in lst)
        for pos, lst in positions.items()
    }

    return positions, totals


def normalize_name(name: str) -> str:
    """
    Normalize player names to improve matching across data sources.

    This function removes:
    - Capitalization differences
    - Punctuation
    - Short tokens (team abbreviations, noise)
    - Common suffixes (Jr, Sr, III, etc.)

    The output is designed for fuzzy name matching, not display.
    """
    if not name:
        return ""

    # Convert to lowercase for consistent matching
    name = name.lower()

    # Remove punctuation and special characters
    name = re.sub(r"[^a-z0-9\s]", "", name)

    # Remove short tokens (often team abbreviations or noise)
    name = re.sub(r"\b[a-z]{2,3}\b", "", name)

    # Remove generational suffixes
    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    parts = [p for p in name.split() if p not in suffixes]

    return " ".join(parts).strip()
