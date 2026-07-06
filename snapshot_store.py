from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

SNAPSHOT_FIELDS = [
    "snapshot_at",
    "id",
    "sport",
    "league",
    "kickoff",
    "home",
    "away",
    "top_key",
    "top_label",
    "top_prob",
    "top_odds",
    "best_key",
    "best_label",
    "best_ev",
    "best_odds",
    "prob_home",
    "prob_draw",
    "prob_away",
]

BACKTEST_FIELDS = [
    "id",
    "snapshot_at",
    "sport",
    "league",
    "kickoff",
    "home",
    "away",
    "pick_type",
    "pick_key",
    "pick_label",
    "pick_prob",
    "pick_odds",
    "pick_ev",
    "result",
    "score",
    "won",
    "profit",
    "source",
]


def read_dashboard() -> dict:
    raw = (ROOT / "dashboard_data.js").read_text(encoding="utf-8")
    return json.loads(raw.split("=", 1)[1].strip().rstrip(";"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def rewrite_csv_with_fields(path: Path, fieldnames: list[str]) -> None:
    rows = read_csv(path)
    if not rows:
        return
    write_csv(path, rows, fieldnames)


def snapshot_rows(dashboard: dict) -> list[dict[str, str]]:
    now = datetime.now().isoformat(timespec="seconds")
    rows = []
    for item in dashboard.get("predictions", []):
        pred = item["prediction"]
        top = pred["topSide"]
        best = pred["best"]
        probs = pred["probs"]
        rows.append(
            {
                "snapshot_at": now,
                "id": item["id"],
                "sport": item.get("sport", ""),
                "league": item.get("league", ""),
                "kickoff": item.get("kickoff", ""),
                "home": item.get("home", ""),
                "away": item.get("away", ""),
                "top_key": top.get("key", ""),
                "top_label": top.get("label", ""),
                "top_prob": top.get("prob", ""),
                "top_odds": top.get("odds", ""),
                "best_key": best.get("key", ""),
                "best_label": best.get("label", ""),
                "best_ev": best.get("ev", ""),
                "best_odds": best.get("odds", ""),
                "prob_home": probs.get("home", ""),
                "prob_draw": probs.get("draw", ""),
                "prob_away": probs.get("away", ""),
            }
        )
    return rows


def result_won(pick_key: str, result: str) -> bool:
    return pick_key == result


def parse_snapshot_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=ZoneInfo("Asia/Taipei"))
    except ValueError:
        return None


def parse_kickoff(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Taipei"))
    except ValueError:
        return None


def snapshot_by_match(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        match_id = row.get("id", "")
        if match_id:
            grouped.setdefault(match_id, []).append(row)
    for match_rows in grouped.values():
        match_rows.sort(key=lambda item: item.get("snapshot_at", ""))
    return grouped


def pick_snapshot_for_result(match_rows: list[dict[str, str]], result: dict[str, str]) -> dict[str, str] | None:
    if not match_rows:
        return None
    kickoff = parse_kickoff(result.get("commence_time", ""))
    if not kickoff:
        return match_rows[0]
    before_kickoff = [
        row
        for row in match_rows
        if (snapshot_time := parse_snapshot_time(row.get("snapshot_at", ""))) and snapshot_time <= kickoff
    ]
    return before_kickoff[-1] if before_kickoff else match_rows[0]


def to_float(value: str | None) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def backtest_pick_row(result: dict[str, str], snap: dict[str, str], pick_type: str) -> dict[str, str]:
    match_id = result.get("id", "")
    is_value = pick_type == "value"
    pick_key = snap.get("best_key" if is_value else "top_key", "")
    pick_label = snap.get("best_label" if is_value else "top_label", "")
    pick_prob = snap.get(f"prob_{pick_key}", "") if is_value else snap.get("top_prob", "")
    pick_odds = snap.get("best_odds", "") if is_value else snap.get("top_odds", "")
    pick_ev = snap.get("best_ev", "") if is_value else ""
    won = result_won(pick_key, result.get("result", ""))
    odds = to_float(pick_odds)
    profit = (odds - 1) if won and odds else (1 if won else -1)
    return {
        "id": match_id,
        "snapshot_at": snap.get("snapshot_at", ""),
        "sport": snap.get("sport", ""),
        "league": snap.get("league", ""),
        "kickoff": snap.get("kickoff", ""),
        "home": snap.get("home", ""),
        "away": snap.get("away", ""),
        "pick_type": pick_type,
        "pick_key": pick_key,
        "pick_label": pick_label,
        "pick_prob": pick_prob,
        "pick_odds": pick_odds,
        "pick_ev": pick_ev,
        "result": result.get("result", ""),
        "score": f'{result.get("home_score", "")}-{result.get("away_score", "")}',
        "won": "true" if won else "false",
        "profit": round(profit, 4),
        "source": result.get("source", ""),
    }


def build_snapshot_backtest() -> list[dict[str, str]]:
    snapshots = snapshot_by_match(read_csv(DATA / "prediction_snapshots.csv"))
    results = read_csv(DATA / "settled_results.csv")
    rows = []
    for result in results:
        match_id = result.get("id", "")
        snap = pick_snapshot_for_result(snapshots.get(match_id, []), result)
        if not snap:
            continue
        rows.append(backtest_pick_row(result, snap, "top"))
        if snap.get("best_key"):
            rows.append(backtest_pick_row(result, snap, "value"))
    rows.sort(key=lambda item: (item["kickoff"], item["snapshot_at"]), reverse=True)
    return rows


def main() -> int:
    rewrite_csv_with_fields(DATA / "prediction_snapshots.csv", SNAPSHOT_FIELDS)
    dashboard = read_dashboard()
    rows = snapshot_rows(dashboard)
    append_csv(DATA / "prediction_snapshots.csv", rows, SNAPSHOT_FIELDS)
    backtest = build_snapshot_backtest()
    write_csv(DATA / "snapshot_backtest.csv", backtest, BACKTEST_FIELDS)
    print(f"Appended snapshots: {len(rows)}")
    print(f"Snapshot backtest rows: {len(backtest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
