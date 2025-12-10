import requests
from bs4 import BeautifulSoup
from collections import defaultdict

KTC_URL = "https://keeptradecut.com/dynasty-rankings?page={page}&filters=QB|WR|RB|TE&format=0"

def scrape_ktc_sf():
    players = []

    # scrape first 10 pages (same as GitHub repo)
    for page in range(10):
        url = KTC_URL.format(page=page)
        html = requests.get(url).content
        soup = BeautifulSoup(html, "html.parser")

        player_elements = soup.find_all(class_="onePlayer")

        for el in player_elements:
            name_el   = el.find(class_="player-name")
            pos_el    = el.find(class_="position")
            value_el  = el.find(class_="value")

            if not name_el or not pos_el or not value_el:
                continue

            raw_name = name_el.get_text(strip=True)

            # remove suffix like "FA", "RFA", "BUF", "LVR", "NYG", etc.
            team_suffix = raw_name[-3:]
            if team_suffix in ["FA", "RFA"] or team_suffix.isupper():
                name = raw_name.replace(team_suffix, "").strip()
            else:
                name = raw_name

            # -------------------------------------------------------
            # MINIMAL FIX: remove rookie "R" at the end of cleaned name
            if name.endswith("R"):
                name = name[:-1].strip()
            # -------------------------------------------------------

            pos_rank = pos_el.get_text(strip=True)
            position = pos_rank[:2]
            value    = int(value_el.get_text(strip=True))

            players.append({
                "name": name,
                "position": position,
                "value": value
            })

    pos_groups = defaultdict(list)

    # Group all KTC players by position
    for p in players:
        pos_groups[p["position"]].append(p)

    # Sort each position and assign KTC positional ranks
    for _, lst in pos_groups.items():
        lst.sort(key=lambda x: x["value"], reverse=True)
        for i, player in enumerate(lst, start=1):
            player["pos_rank"] = i   # e.g., RB23, WR14, TE8

    return players
