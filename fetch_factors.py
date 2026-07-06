from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    for candidate in (value.replace("Z", "+00:00"), value[:10]):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def load_manual() -> dict[str, dict[str, str]]:
    rows = read_csv(DATA / "team_factors_manual.csv")
    return {row["team"]: row for row in rows if row.get("team")}


def last_played_map(historical: list[dict[str, str]]) -> dict[str, datetime]:
    out: dict[str, datetime] = {}
    for row in historical:
        date = parse_date(row.get("date", ""))
        if not date:
            continue
        for team in (row.get("home"), row.get("away")):
            if team and (team not in out or date > out[team]):
                out[team] = date
    return out


def rest_days(team: str, kickoff: datetime | None, last_played: dict[str, datetime]) -> str:
    if not kickoff or team not in last_played:
        return ""
    days = (kickoff.replace(tzinfo=None) - last_played[team].replace(tzinfo=None)).days
    if days < 0:
        return ""
    return str(min(days, 14))


def default_factor(team: str, kickoff: datetime | None, last_played: dict[str, datetime]) -> dict[str, str]:
    rest = rest_days(team, kickoff, last_played)
    notes = "自動計算休息天數；尚未接入可靠傷兵 API"
    if not rest:
        notes = "尚無可比對的近期賽果；未輸入傷兵資料"
    return {
        "team": team,
        "injury_impact": "0.00",
        "form_impact": "0.00",
        "rest_days": rest,
        "travel_impact": "0.00",
        "notes": notes,
        "source": "auto:historical_rest",
        "updated_at": datetime.now().date().isoformat(),
    }


def merge_factor(auto: dict[str, str], manual: dict[str, str] | None) -> dict[str, str]:
    if not manual:
        return auto
    merged = dict(auto)
    for key, value in manual.items():
        if key == "team":
            continue
        if value not in (None, ""):
            merged[key] = value
    merged["source"] = manual.get("source") or "manual"
    merged["updated_at"] = manual.get("updated_at") or merged["updated_at"]
    return merged


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = ["team", "injury_impact", "form_impact", "rest_days", "travel_impact", "notes", "source", "updated_at"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    historical = read_csv(DATA / "historical_matches.csv")
    upcoming = read_csv(DATA / "upcoming_matches.csv")
    manual = load_manual()
    last_played = last_played_map(historical)
    teams: dict[str, dict[str, str]] = {}

    for row in upcoming:
        kickoff = parse_date(row.get("kickoff", ""))
        for team in (row.get("home"), row.get("away")):
            if team and team not in teams:
                teams[team] = merge_factor(default_factor(team, kickoff, last_played), manual.get(team))

    # Preserve manual-only teams so they remain visible when their next match appears later.
    for team, factor in manual.items():
        if team not in teams:
            teams[team] = merge_factor(default_factor(team, None, last_played), factor)

    rows = sorted(teams.values(), key=lambda item: item["team"])
    write_csv(DATA / "team_factors.csv", rows)
    print(f"Wrote team factors: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
