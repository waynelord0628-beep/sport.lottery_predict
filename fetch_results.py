from __future__ import annotations

import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


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


def read_upcoming_sport_keys() -> list[str]:
    keys = []
    path = DATA / "upcoming_matches.csv"
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                source = row.get("source", "")
                if source.startswith("the-odds-api:"):
                    key = source.split(":", 2)[1]
                    if key and key not in keys:
                        keys.append(key)
    env_keys = [item.strip() for item in os.environ.get("ODDS_SPORT_KEYS", "").split(",") if item.strip()]
    for key in env_keys:
        if key != "upcoming" and key not in keys:
            keys.append(key)
    return keys or ["baseball_mlb", "soccer_fifa_world_cup"]


def winner_from_scores(scores: list[dict]) -> tuple[str, str, str] | None:
    if len(scores) < 2:
        return None
    parsed = []
    for item in scores:
        try:
            parsed.append((item.get("name", ""), int(float(item.get("score", 0)))))
        except (TypeError, ValueError):
            return None
    if parsed[0][1] > parsed[1][1]:
        result = "home"
    elif parsed[0][1] < parsed[1][1]:
        result = "away"
    else:
        result = "draw"
    return str(parsed[0][1]), str(parsed[1][1]), result


def main() -> int:
    api_key = os.environ.get("THE_ODDS_API_KEY", "").strip()
    if not api_key:
        print("Set THE_ODDS_API_KEY first. Skipping scores.")
        return 2

    rows = []
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sports": {},
        "requests_remaining": None,
        "requests_used": None,
    }

    for sport_key in read_upcoming_sport_keys():
        query = {
            "apiKey": api_key,
            "daysFrom": "3",
            "dateFormat": "iso",
        }
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/?" + urllib.parse.urlencode(query)
        payload, headers, error = fetch_json(url)
        if payload is None:
            report["sports"][sport_key] = {"error": error, "finished": 0}
            continue
        report["requests_remaining"] = headers.get("x-requests-remaining")
        report["requests_used"] = headers.get("x-requests-used")
        count = 0
        for event in payload:
            if not event.get("completed"):
                continue
            scores = winner_from_scores(event.get("scores") or [])
            if not scores:
                continue
            home_score, away_score, result = scores
            rows.append(
                {
                    "id": event.get("id", ""),
                    "sport_key": sport_key,
                    "sport_title": event.get("sport_title", ""),
                    "commence_time": event.get("commence_time", ""),
                    "home": event.get("home_team", ""),
                    "away": event.get("away_team", ""),
                    "home_score": home_score,
                    "away_score": away_score,
                    "result": result,
                    "completed": "true",
                    "source": f"the-odds-api:scores:{sport_key}",
                }
            )
            count += 1
        report["sports"][sport_key] = {"finished": count}

    fieldnames = [
        "id",
        "sport_key",
        "sport_title",
        "commence_time",
        "home",
        "away",
        "home_score",
        "away_score",
        "result",
        "completed",
        "source",
    ]
    with (DATA / "settled_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    report["written_rows"] = len(rows)
    (REPORTS / "results_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote settled results: {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
