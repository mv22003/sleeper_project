"""
ktc.py

Credits to "ees4" for the KTC Scraper:
https://github.com/ees4/KeepTradeCut-Scraper/blob/main

This module is responsible for:
- Scraping player dynasty values from KeepTradeCut (Superflex)
- Cleaning and normalizing scraped player names
- Assigning positional ranks based on value
- Caching results to avoid repeated scraping
"""

import requests
import time
from bs4 import BeautifulSoup
from collections import defaultdict


# Base URL for KeepTradeCut Superflex dynasty rankings
# Filters restrict results to QB, WR, RB, TE only
KTC_URL = "https://keeptradecut.com/dynasty-rankings?page={page}&filters=QB|WR|RB|TE&format=0"


def scrape_ktc_sf():
    """
    Scrape KeepTradeCut Superflex dynasty rankings.

    Returns a flat list of players with:
    - name (cleaned for matching)
    - position
    - value
    - pos_rank (assigned later)
    """
    players = []

    # Scrape the first 10 pages of rankings (covers full player pool)
    for page in range(10):
        url = KTC_URL.format(page=page)
        html = requests.get(url).content
        soup = BeautifulSoup(html, "html.parser")

        # Each player row is represented by a "onePlayer" element
        player_elements = soup.find_all(class_="onePlayer")

        for el in player_elements:
            name_el   = el.find(class_="player-name")
            pos_el    = el.find(class_="position")
            value_el  = el.find(class_="value")

            # Skip malformed or non-player rows
            if not name_el or not pos_el or not value_el:
                continue

            raw_name = name_el.get_text(strip=True)

            # Remove trailing team or status suffixes (e.g., BUF, FA, RFA)
            team_suffix = raw_name[-3:]
            if team_suffix in ["FA", "RFA"] or team_suffix.isupper():
                name = raw_name.replace(team_suffix, "").strip()
            else:
                name = raw_name

            # Remove rookie "R" suffix if present
            if name.endswith("R"):
                name = name[:-1].strip()

            # Extract position from positional ranking (e.g., "RB12" → "RB")
            pos_rank = pos_el.get_text(strip=True)
            position = pos_rank[:2]

            # Convert KTC value into integer for sorting and aggregation
            value = int(value_el.get_text(strip=True))

            players.append({
                "name": name,
                "position": position,
                "value": value
            })

    # Group players by position to assign positional ranks
    pos_groups = defaultdict(list)

    for p in players:
        pos_groups[p["position"]].append(p)

    # Sort each position group by value and assign positional rank
    for _, lst in pos_groups.items():
        lst.sort(key=lambda x: x["value"], reverse=True)
        for i, player in enumerate(lst, start=1):
            player["pos_rank"] = i   # e.g., RB23, WR14, TE8

    return players


# Cached KTC dataset (in-memory)
KTC_CACHE = None

# Timestamp of last successful scrape
KTC_CACHE_TIME = 0

# Cache time-to-live: 12 hours
KTC_CACHE_TTL = 3600 * 12


def get_ktc_values():
    """
    Public entry point for retrieving KTC values.

    Uses cached data when available to avoid unnecessary scraping.
    """
    global KTC_CACHE, KTC_CACHE_TIME

    # Return cached data if it is still fresh
    if KTC_CACHE and (time.time() - KTC_CACHE_TIME) < KTC_CACHE_TTL:
        return KTC_CACHE

    # Cache is missing or expired, scrape fresh data
    data = scrape_ktc_sf()

    # Update cache and timestamp
    KTC_CACHE = data
    KTC_CACHE_TIME = time.time()

    return data
