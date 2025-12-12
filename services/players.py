import re

def build_roster_positions(client, roster, ktc_data):
    players = client.get_players()

    ktc_by_name = {
        normalize_name(p["name"]): p for p in ktc_data
    }

    positions = {"QB": [], "RB": [], "WR": [], "TE": []}

    for pid in roster.get("players", []):
        p = players.get(str(pid))
        if not p:
            continue

        norm_name = normalize_name(p.get("full_name"))
        ktc_entry = ktc_by_name.get(norm_name)

        positions[p["position"]].append({
            "id": pid,
            "name": p.get("full_name"),
            "position": p.get("position"),
            "team": p.get("team", "FA"),
            "headshot": p.get("metadata", {}).get("headshot"),
            "ktc_value": ktc_entry["value"] if ktc_entry else 0,
            "ktc_pos_rank": ktc_entry["pos_rank"] if ktc_entry else None
        })

    for lst in positions.values():
        lst.sort(key=lambda p: p["ktc_value"], reverse=True)

    totals = {pos: sum(p["ktc_value"] for p in lst) for pos, lst in positions.items()}

    return positions, totals



def normalize_name(name: str) -> str:
    if not name:
        return ""

    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\b[a-z]{2,3}\b", "", name)

    suffixes = {"jr", "sr", "ii", "iii", "iv", "v"}
    parts = [p for p in name.split() if p not in suffixes]

    return " ".join(parts).strip()
