from __future__ import annotations

import csv
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = DATA / "raw"
REPORTS = ROOT / "reports"

SEASONS = ["2324", "2425", "2526"]
LEAGUES = {
    "E0": "Premier League",
    "SP1": "La Liga",
    "I1": "Serie A",
    "D1": "Bundesliga",
    "F1": "Ligue 1",
}


def ensure_dirs() -> None:
    DATA.mkdir(exist_ok=True)
    RAW.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)


def download(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "private-predictor/1.0"})
        with urllib.request.urlopen(req, timeout=25) as response:
            body = response.read()
        if len(body) < 100:
            return False
        dest.write_bytes(body)
        return True
    except (urllib.error.URLError, TimeoutError):
        return False


def parse_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date: {value}")


def as_float(row: dict[str, str], *keys: str) -> tuple[float | None, str | None]:
    for key in keys:
        value = row.get(key, "").strip()
        if value:
            try:
                return float(value), key
            except ValueError:
                continue
    return None, None


def choose_odds(row: dict[str, str]) -> tuple[dict[str, float | None], str]:
    home, home_col = as_float(row, "AvgCH", "B365CH", "MaxCH", "AvgH", "B365H", "MaxH")
    draw, draw_col = as_float(row, "AvgCD", "B365CD", "MaxCD", "AvgD", "B365D", "MaxD")
    away, away_col = as_float(row, "AvgCA", "B365CA", "MaxCA", "AvgA", "B365A", "MaxA")
    over25, over_col = as_float(row, "AvgC>2.5", "B365C>2.5", "MaxC>2.5", "Avg>2.5", "B365>2.5", "Max>2.5")
    btts, btts_col = as_float(row, "B365CYes", "B365Yes")

    used = [col for col in (home_col, draw_col, away_col, over_col, btts_col) if col]
    timing = "closing" if any(col and "C" in col for col in used) else "pre_closing"
    return (
        {
            "home": home,
            "draw": draw,
            "away": away,
            "over25": over25,
            "btts": btts,
        },
        timing,
    )


def normalize_rows() -> tuple[list[dict[str, str]], dict]:
    rows: list[dict[str, str]] = []
    quality = {
        "downloaded_files": 0,
        "source_rows": 0,
        "usable_rows": 0,
        "missing_result": 0,
        "missing_1x2_odds": 0,
        "duplicates": 0,
        "by_league": {},
        "odds_timing": {"closing": 0, "pre_closing": 0},
    }
    seen: set[tuple[str, str, str, str]] = set()

    for season in SEASONS:
        for code, league in LEAGUES.items():
            path = RAW / f"{season}_{code}.csv"
            if not path.exists():
                continue
            quality["downloaded_files"] += 1
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    quality["source_rows"] += 1
                    if not row.get("Date") or not row.get("HomeTeam") or not row.get("AwayTeam"):
                        continue
                    if not row.get("FTHG") or not row.get("FTAG"):
                        quality["missing_result"] += 1
                        continue
                    odds, timing = choose_odds(row)
                    if not odds["home"] or not odds["draw"] or not odds["away"]:
                        quality["missing_1x2_odds"] += 1
                        continue
                    try:
                        date = parse_date(row["Date"])
                    except ValueError:
                        continue
                    key = (date, league, row["HomeTeam"], row["AwayTeam"])
                    if key in seen:
                        quality["duplicates"] += 1
                        continue
                    seen.add(key)
                    quality["usable_rows"] += 1
                    quality["by_league"][league] = quality["by_league"].get(league, 0) + 1
                    quality["odds_timing"][timing] += 1
                    rows.append(
                        {
                            "date": date,
                            "league": league,
                            "home": row["HomeTeam"],
                            "away": row["AwayTeam"],
                            "home_score": row["FTHG"],
                            "away_score": row["FTAG"],
                            "odds_home": str(odds["home"]),
                            "odds_draw": str(odds["draw"]),
                            "odds_away": str(odds["away"]),
                            "odds_over25": "" if odds["over25"] is None else str(odds["over25"]),
                            "odds_btts": "" if odds["btts"] is None else str(odds["btts"]),
                            "odds_timing": timing,
                            "source": f"football-data:{season}:{code}",
                        }
                    )
    rows.sort(key=lambda item: (item["date"], item["league"], item["home"], item["away"]))
    return rows, quality


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "date",
        "league",
        "home",
        "away",
        "home_score",
        "away_score",
        "odds_home",
        "odds_draw",
        "odds_away",
        "odds_over25",
        "odds_btts",
        "odds_timing",
        "source",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ensure_dirs()
    failures = []
    for season in SEASONS:
        for code in LEAGUES:
            url = f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
            dest = RAW / f"{season}_{code}.csv"
            if not download(url, dest):
                failures.append(url)

    rows, quality = normalize_rows()
    if not rows:
        print("No usable rows downloaded.")
        return 1

    write_csv(DATA / "historical_matches.csv", rows)
    quality["date_min"] = rows[0]["date"]
    quality["date_max"] = rows[-1]["date"]
    quality["failed_downloads"] = failures
    quality["generated_at"] = datetime.now().isoformat(timespec="seconds")
    (REPORTS / "data_quality.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Historical rows: {len(rows)}")
    print(f"Date range: {quality['date_min']} to {quality['date_max']}")
    print(f"Reports: {REPORTS / 'data_quality.json'}")
    if failures:
        print(f"Failed downloads: {len(failures)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
