from __future__ import annotations

import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

SPORTS = {
    "upcoming": {"sport": "mixed", "league": "Upcoming"},
    "baseball_mlb": {"sport": "baseball", "league": "MLB"},
    "esports_lol": {"sport": "esports", "league": "LoL"},
    "esports_cs2": {"sport": "esports", "league": "CS2"},
    "esports_dota2": {"sport": "esports", "league": "Dota 2"},
}


def get_json(url: str) -> tuple[list | dict, dict[str, str]]:
    req = urllib.request.Request(url, headers={"User-Agent": "private-predictor/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        return json.loads(response.read().decode("utf-8")), headers


def fetch_json(url: str) -> tuple[list | dict | None, dict[str, str], str | None]:
    try:
        payload, headers = get_json(url)
        return payload, headers, None
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return None, {}, f"HTTP {exc.code}: {body[:300]}"
    except Exception as exc:
        return None, {}, str(exc)


def decimal_price(price) -> float | None:
    if price is None:
        return None
    return float(price)


def sport_group(sport_key: str) -> str:
    if sport_key.startswith("baseball_"):
        return "baseball"
    if sport_key.startswith("esports_"):
        return "esports"
    if sport_key.startswith("soccer_"):
        return "soccer"
    if sport_key.startswith("basketball_"):
        return "basketball"
    if sport_key.startswith("americanfootball_"):
        return "football"
    if sport_key.startswith("icehockey_"):
        return "hockey"
    if sport_key.startswith("cricket_"):
        return "cricket"
    return sport_key.split("_", 1)[0] if "_" in sport_key else sport_key


def best_h2h(bookmakers: list[dict], home: str, away: str) -> tuple[float | None, float | None, float | None, str | None]:
    best_home = None
    best_draw = None
    best_away = None
    seen_books = []
    for book in bookmakers:
        for market in book.get("markets", []):
            if market.get("key") != "h2h":
                continue
            seen_books.append(book.get("key", "book"))
            for outcome in market.get("outcomes", []):
                name = outcome.get("name")
                price = decimal_price(outcome.get("price"))
                if name == home and price:
                    best_home = price if best_home is None else max(best_home, price)
                elif name and name.lower() == "draw" and price:
                    best_draw = price if best_draw is None else max(best_draw, price)
                elif name == away and price:
                    best_away = price if best_away is None else max(best_away, price)
    return best_home, best_draw, best_away, ",".join(sorted(set(seen_books))) if seen_books else None


def main() -> int:
    api_key = os.environ.get("THE_ODDS_API_KEY", "").strip()
    if not api_key:
        print("Set THE_ODDS_API_KEY first. Keeping manual upcoming_matches.csv.")
        return 2

    rows = []
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sports": {},
        "requests_remaining": None,
        "requests_used": None,
    }
    default_sports = "upcoming,baseball_mlb,esports_lol"
    sport_keys = [item.strip() for item in os.environ.get("ODDS_SPORT_KEYS", default_sports).split(",") if item.strip()]
    seen_events: set[str] = set()

    for api_sport in sport_keys:
        meta = SPORTS.get(api_sport, {"sport": sport_group(api_sport), "league": api_sport})
        query = {
            "apiKey": api_key,
            "regions": os.environ.get("ODDS_REGIONS", "us,uk,eu,au"),
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }
        url = f"https://api.the-odds-api.com/v4/sports/{api_sport}/odds/?" + urllib.parse.urlencode(query)
        payload, headers, error = fetch_json(url)
        if payload is None:
            report["sports"][api_sport] = {"error": error, "events": 0}
            continue

        report["requests_remaining"] = headers.get("x-requests-remaining")
        report["requests_used"] = headers.get("x-requests-used")
        count = 0
        for event in payload:
            event_id = event.get("id") or f'{api_sport}:{event.get("home_team")}:{event.get("away_team")}:{event.get("commence_time")}'
            if event_id in seen_events:
                continue
            seen_events.add(event_id)
            home = event.get("home_team")
            away = event.get("away_team")
            if not home or not away:
                continue
            home_odds, draw_odds, away_odds, books = best_h2h(event.get("bookmakers", []), home, away)
            if not home_odds or not away_odds:
                continue
            event_sport_key = event.get("sport_key") or api_sport
            rows.append(
                {
                    "id": event_id,
                    "sport": sport_group(event_sport_key) if api_sport == "upcoming" else meta["sport"],
                    "league": event.get("sport_title") or meta["league"],
                    "kickoff": event.get("commence_time", ""),
                    "home": home,
                    "away": away,
                    "odds_home": home_odds,
                    "odds_draw": "" if draw_odds is None else draw_odds,
                    "odds_away": away_odds,
                    "odds_over25": "",
                    "odds_btts": "",
                    "odds_timing": "api_snapshot",
                    "source": f"the-odds-api:{event_sport_key}:{books or 'unknown'}",
                }
            )
            count += 1
        report["sports"][api_sport] = {"events": count}

    if not rows:
        (REPORTS / "odds_api_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("No upcoming odds found. Keeping manual upcoming_matches.csv.")
        return 1

    fieldnames = [
        "id",
        "sport",
        "league",
        "kickoff",
        "home",
        "away",
        "odds_home",
        "odds_draw",
        "odds_away",
        "odds_over25",
        "odds_btts",
        "odds_timing",
        "source",
    ]
    with (DATA / "upcoming_matches.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    report["written_rows"] = len(rows)
    (REPORTS / "odds_api_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote upcoming matches: {len(rows)}")
    print(f"Requests remaining: {report['requests_remaining']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
