from __future__ import annotations

import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

SPORTS = {
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


def decimal_price(price) -> float | None:
    if price is None:
        return None
    return float(price)


def best_h2h(bookmakers: list[dict], home: str, away: str) -> tuple[float | None, float | None, str | None]:
    best_home = None
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
                elif name == away and price:
                    best_away = price if best_away is None else max(best_away, price)
    return best_home, best_away, ",".join(sorted(set(seen_books))) if seen_books else None


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
    now = datetime.now(timezone.utc)
    to_time = now + timedelta(days=10)

    for api_sport, meta in SPORTS.items():
        query = {
            "apiKey": api_key,
            "regions": "us,eu,uk",
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
            "commenceTimeFrom": now.isoformat().replace("+00:00", "Z"),
            "commenceTimeTo": to_time.isoformat().replace("+00:00", "Z"),
        }
        url = f"https://api.the-odds-api.com/v4/sports/{api_sport}/odds/?" + urllib.parse.urlencode(query)
        try:
            payload, headers = get_json(url)
        except Exception as exc:
            report["sports"][api_sport] = {"error": str(exc), "events": 0}
            continue

        report["requests_remaining"] = headers.get("x-requests-remaining")
        report["requests_used"] = headers.get("x-requests-used")
        count = 0
        for event in payload:
            home = event.get("home_team")
            away = event.get("away_team")
            if not home or not away:
                continue
            home_odds, away_odds, books = best_h2h(event.get("bookmakers", []), home, away)
            if not home_odds or not away_odds:
                continue
            rows.append(
                {
                    "id": event.get("id"),
                    "sport": meta["sport"],
                    "league": meta["league"],
                    "kickoff": event.get("commence_time", ""),
                    "home": home,
                    "away": away,
                    "odds_home": home_odds,
                    "odds_draw": "",
                    "odds_away": away_odds,
                    "odds_over25": "",
                    "odds_btts": "",
                    "odds_timing": "api_snapshot",
                    "source": f"the-odds-api:{api_sport}:{books or 'unknown'}",
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
