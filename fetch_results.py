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

DEFAULT_SCORE_KEYS = [
    "soccer_fifa_world_cup",
    "baseball_mlb",
    "basketball_nba",
    "basketball_wnba",
    "tennis_atp_wimbledon",
    "tennis_wta_wimbledon",
    "cricket_odi",
    "cricket_test_match",
    "esports_lol",
    "esports_cs2",
    "esports_dota2",
]

FIELDNAMES = [
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


def append_unique(keys: list[str], value: str) -> None:
    if value and value != "upcoming" and value not in keys:
        keys.append(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_score_sport_keys() -> list[str]:
    keys: list[str] = []
    path = DATA / "upcoming_matches.csv"
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                source = row.get("source", "")
                if source.startswith("the-odds-api:"):
                    key = source.split(":", 2)[1]
                    append_unique(keys, key)

    for row in read_csv(DATA / "settled_results.csv"):
        append_unique(keys, row.get("sport_key", ""))

    env_keys = [item.strip() for item in os.environ.get("ODDS_SPORT_KEYS", "").split(",") if item.strip()]
    for key in env_keys:
        append_unique(keys, key)

    for key in DEFAULT_SCORE_KEYS:
        append_unique(keys, key)

    return keys


def merge_results(existing: list[dict[str, str]], incoming: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for row in existing:
        match_id = row.get("id", "")
        if match_id:
            merged[match_id] = {field: row.get(field, "") for field in FIELDNAMES}

    for row in incoming:
        match_id = row.get("id", "")
        if not match_id:
            continue
        current = merged.get(match_id)
        if current and current.get("source", "").startswith("manual:"):
            continue
        merged[match_id] = {field: row.get(field, "") for field in FIELDNAMES}

    rows = list(merged.values())
    rows.sort(key=lambda item: item.get("commence_time", ""), reverse=True)
    return rows


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

    for sport_key in read_score_sport_keys():
        query = {
            "apiKey": api_key,
            "daysFrom": os.environ.get("ODDS_SCORE_DAYS", "7"),
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

    existing = read_csv(DATA / "settled_results.csv")
    rows = merge_results(existing, rows)
    with (DATA / "settled_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    report["written_rows"] = len(rows)
    report["incoming_rows"] = sum(item.get("finished", 0) for item in report["sports"].values() if isinstance(item.get("finished", 0), int))
    report["preserved_existing_rows"] = len(existing)
    (REPORTS / "results_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote settled results: {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
