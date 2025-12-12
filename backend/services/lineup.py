from collections import defaultdict


def normalize_roster_slots(roster_positions: list[str], settings: dict) -> dict:
    """
    Normalize Sleeper roster configuration into a single roster_slots dictionary.

    Returns a dict containing:
    - starter slot counts (QB, RB, WR, TE, FLEX, SUPER_FLEX, etc.)
    - bench slots (BN)
    - IR slots (IR)
    - taxi slots (TAXI)
    """

    roster_slots = defaultdict(int)

    # Starters and bench come from roster_positions
    for slot in roster_positions:
        roster_slots[slot] += 1

    # IR and taxi slots live in league settings
    ir_slots = settings.get("reserve_slots", 0) or 0
    taxi_slots = settings.get("taxi_slots", 0) or 0

    if ir_slots:
        roster_slots["IR"] = ir_slots

    if taxi_slots:
        roster_slots["TAXI"] = taxi_slots

    return dict(roster_slots)
