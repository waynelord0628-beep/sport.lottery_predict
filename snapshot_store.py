from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


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


def dedupe_latest_snapshots(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        match_id = row.get("id", "")
        if not match_id:
            continue
        if match_id not in latest or row.get("snapshot_at", "") > latest[match_id].get("snapshot_at", ""):
            latest[match_id] = row
    return latest


def build_snapshot_backtest() -> list[dict[str, str]]:
    snapshots = dedupe_latest_snapshots(read_csv(DATA / "prediction_snapshots.csv"))
    results = read_csv(DATA / "settled_results.csv")
    rows = []
    for result in results:
        match_id = result.get("id", "")
        snap = snapshots.get(match_id)
        if not snap:
            continue
        pick_key = snap.get("top_key", "")
        won = result_won(pick_key, result.get("result", ""))
        odds = float(snap.get("best_odds") or 0) if pick_key == snap.get("best_key") else 0.0
        profit = (odds - 1) if won and odds else (1 if won else -1)
        rows.append(
            {
                "id": match_id,
                "snapshot_at": snap.get("snapshot_at", ""),
                "sport": snap.get("sport", ""),
                "league": snap.get("league", ""),
                "kickoff": snap.get("kickoff", ""),
                "home": snap.get("home", ""),
                "away": snap.get("away", ""),
                "pick_key": pick_key,
                "pick_label": snap.get("top_label", ""),
                "pick_prob": snap.get("top_prob", ""),
                "pick_odds": snap.get("best_odds", "") if pick_key == snap.get("best_key") else "",
                "pick_ev": snap.get("best_ev", "") if pick_key == snap.get("best_key") else "",
                "result": result.get("result", ""),
                "score": f'{result.get("home_score", "")}-{result.get("away_score", "")}',
                "won": "true" if won else "false",
                "profit": round(profit, 4),
                "source": result.get("source", ""),
            }
        )
    rows.sort(key=lambda item: (item["kickoff"], item["snapshot_at"]), reverse=True)
    return rows


def main() -> int:
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
