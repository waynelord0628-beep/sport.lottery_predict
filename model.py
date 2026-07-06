from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Odds:
    home: float
    draw: float | None
    away: float
    over25: float | None = None
    btts: float | None = None


@dataclass(frozen=True)
class Params:
    home_adv: float
    elo_k: float
    model_weight: float
    draw_floor: float


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def to_float(value: str | None, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)


def poisson(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def normalize(raw: dict[str, float]) -> dict[str, float]:
    total = sum(raw.values())
    if total <= 0:
        return {key: 1 / len(raw) for key in raw}
    return {key: value / total for key, value in raw.items()}


def match_result(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home"
    if home_score < away_score:
        return "away"
    return "draw"


def expected_score(result: str) -> tuple[float, float]:
    if result == "home":
        return 1.0, 0.0
    if result == "away":
        return 0.0, 1.0
    return 0.5, 0.5


def update_elo(home_elo: float, away_elo: float, result: str, params: Params) -> tuple[float, float]:
    expected_home = 1 / (1 + 10 ** ((away_elo - (home_elo + params.home_adv)) / 400))
    home_score, away_score = expected_score(result)
    new_home = home_elo + params.elo_k * (home_score - expected_home)
    new_away = away_elo + params.elo_k * (away_score - (1 - expected_home))
    return new_home, new_away


def odds_from_row(row: dict[str, str]) -> Odds:
    return Odds(
        float(row["odds_home"]),
        to_float(row.get("odds_draw")),
        float(row["odds_away"]),
        to_float(row.get("odds_over25")),
        to_float(row.get("odds_btts")),
    )


def market_probs(odds: Odds) -> dict[str, float]:
    raw = {"home": 1 / odds.home, "away": 1 / odds.away}
    if odds.draw:
        raw["draw"] = 1 / odds.draw
    return normalize(raw)


def elo_probs(home_elo: float, away_elo: float, params: Params, has_draw: bool) -> dict[str, float]:
    diff = home_elo + params.home_adv - away_elo
    home_base = 1 / (1 + 10 ** (-diff / 400))
    if not has_draw:
        return normalize({"home": home_base, "away": 1 - home_base})
    draw = max(params.draw_floor, 0.29 - abs(diff) / 1600)
    return normalize(
        {
            "home": home_base * (1 - draw),
            "draw": draw,
            "away": (1 - home_base) * (1 - draw),
        }
    )


def blended_probs(model: dict[str, float], market: dict[str, float], params: Params) -> dict[str, float]:
    w = params.model_weight
    return normalize({key: w * model[key] + (1 - w) * market[key] for key in market})


def factor_score(factor: dict[str, str] | None) -> float:
    if not factor:
        return 0.0
    injury = to_float(factor.get("injury_impact"), 0.0) or 0.0
    form = to_float(factor.get("form_impact"), 0.0) or 0.0
    travel = to_float(factor.get("travel_impact"), 0.0) or 0.0
    rest_days = to_float(factor.get("rest_days"), 5.0) or 5.0
    rest = max(-0.03, min(0.03, (rest_days - 4.0) * 0.0075))
    return max(-0.12, min(0.12, injury + form + travel + rest))


def apply_factor_adjustment(probs: dict[str, float], home_factor: dict[str, str] | None, away_factor: dict[str, str] | None) -> tuple[dict[str, float], dict]:
    home_score = factor_score(home_factor)
    away_score = factor_score(away_factor)
    edge = max(-0.12, min(0.12, home_score - away_score))
    if abs(edge) < 0.0001:
        return probs, {"homeScore": round(home_score, 4), "awayScore": round(away_score, 4), "edge": 0.0, "applied": False}
    adjusted = dict(probs)
    draw_share = 0.35 if "draw" in adjusted else 0.0
    side_shift = edge * (1 - draw_share)
    adjusted["home"] = max(0.01, adjusted["home"] + side_shift)
    adjusted["away"] = max(0.01, adjusted["away"] - side_shift)
    if "draw" in adjusted:
        adjusted["draw"] = max(0.01, adjusted["draw"] - abs(edge) * draw_share)
    return normalize(adjusted), {
        "homeScore": round(home_score, 4),
        "awayScore": round(away_score, 4),
        "edge": round(edge, 4),
        "applied": True,
    }


def factor_view(team: str, factor: dict[str, str] | None) -> dict:
    factor = factor or {}
    return {
        "team": team,
        "injuryImpact": to_float(factor.get("injury_impact"), 0.0) or 0.0,
        "formImpact": to_float(factor.get("form_impact"), 0.0) or 0.0,
        "restDays": to_float(factor.get("rest_days"), None),
        "travelImpact": to_float(factor.get("travel_impact"), 0.0) or 0.0,
        "notes": factor.get("notes", ""),
        "source": factor.get("source", ""),
        "updatedAt": factor.get("updated_at", ""),
    }


def predict(home: str, away: str, ratings: dict[str, float], odds: Odds, params: Params, factors: dict[str, dict[str, str]] | None = None) -> dict:
    home_elo = ratings.get(home, 1500)
    away_elo = ratings.get(away, 1500)
    has_draw = odds.draw is not None
    model = elo_probs(home_elo, away_elo, params, has_draw)
    market = market_probs(odds)
    probs = blended_probs(model, market, params)
    home_factor = (factors or {}).get(home)
    away_factor = (factors or {}).get(away)
    probs, factor_adjustment = apply_factor_adjustment(probs, home_factor, away_factor)

    diff = home_elo + params.home_adv - away_elo
    home_goals = max(0.55, 1.34 + diff / 360)
    away_goals = max(0.45, 1.12 - diff / 520)
    score_grid = []
    over25 = 0.0
    btts = 0.0
    for h in range(5):
        for a in range(5):
            prob = poisson(h, home_goals) * poisson(a, away_goals)
            if h + a > 2.5:
                over25 += prob
            if h > 0 and a > 0:
                btts += prob
            score_grid.append({"score": f"{h}-{a}", "prob": round(prob, 4)})

    score_grid.sort(key=lambda item: item["prob"], reverse=True)
    markets = [
        {"key": "home", "label": f"{home} win", "prob": probs["home"], "odds": odds.home},
        {"key": "away", "label": f"{away} win", "prob": probs["away"], "odds": odds.away},
    ]
    if has_draw:
        markets.insert(1, {"key": "draw", "label": "Draw", "prob": probs["draw"], "odds": odds.draw})
    if odds.over25:
        markets.append({"key": "over25", "label": "Over 2.5", "prob": over25, "odds": odds.over25})
    if odds.btts:
        markets.append({"key": "btts", "label": "BTTS", "prob": btts, "odds": odds.btts})

    enriched = [{**market, "ev": market["prob"] * market["odds"] - 1} for market in markets]
    best = max(enriched, key=lambda item: item["ev"])
    side_count = 3 if has_draw else 2
    top_side = max(enriched[:side_count], key=lambda item: item["prob"])
    confidence = top_side["prob"]
    tier = "high" if confidence >= 0.58 else "medium" if confidence >= 0.48 else "low"

    return {
        "homeElo": round(home_elo, 1),
        "awayElo": round(away_elo, 1),
        "probs": {key: round(value, 4) for key, value in probs.items()},
        "marketProbs": {key: round(value, 4) for key, value in market.items()},
        "modelProbs": {key: round(value, 4) for key, value in model.items()},
        "factorAdjustment": factor_adjustment,
        "factors": {
            "home": factor_view(home, home_factor),
            "away": factor_view(away, away_factor),
        },
        "expectedHomeGoals": round(home_goals, 2),
        "expectedAwayGoals": round(away_goals, 2),
        "over25": round(over25, 4),
        "btts": round(btts, 4),
        "scoreGrid": score_grid[:10],
        "best": round_market(best),
        "topSide": round_market(top_side),
        "confidence": round(confidence, 4),
        "tier": tier,
        "isValue": best["ev"] >= 0.04,
    }


def round_market(market: dict) -> dict:
    rounded = dict(market)
    rounded["prob"] = round(rounded["prob"], 4)
    rounded["ev"] = round(rounded["ev"], 4)
    return rounded


def log_loss(prob: float) -> float:
    clipped = min(max(prob, 0.001), 0.999)
    return -math.log(clipped)


def brier(probs: dict[str, float], result: str) -> float:
    return sum((probs[key] - (1.0 if key == result else 0.0)) ** 2 for key in probs)


def sequential_predictions(rows: list[dict[str, str]], params: Params) -> list[dict]:
    ratings: dict[str, float] = {}
    out = []
    for row in sorted(rows, key=lambda item: item["date"]):
        odds = odds_from_row(row)
        pred = predict(row["home"], row["away"], ratings, odds, params)
        result = match_result(int(row["home_score"]), int(row["away_score"]))
        out.append({"row": row, "prediction": pred, "result": result})
        ratings.setdefault(row["home"], 1500)
        ratings.setdefault(row["away"], 1500)
        ratings[row["home"]], ratings[row["away"]] = update_elo(ratings[row["home"]], ratings[row["away"]], result, params)
    return out


def calibrate(rows: list[dict[str, str]]) -> tuple[Params, list[dict]]:
    candidates = []
    for home_adv in (45, 60, 75, 90):
        for elo_k in (16, 24, 32):
            for model_weight in (0.0, 0.15, 0.3, 0.45, 0.6):
                for draw_floor in (0.18, 0.21, 0.24):
                    candidates.append(Params(home_adv, elo_k, model_weight, draw_floor))

    split = max(100, int(len(rows) * 0.7))
    calibration_rows = rows[:split]
    scored = []
    for params in candidates:
        preds = sequential_predictions(calibration_rows, params)
        warm = preds[60:] if len(preds) > 80 else preds
        losses = [log_loss(item["prediction"]["probs"][item["result"]]) for item in warm]
        scored.append((sum(losses) / len(losses), params))
    scored.sort(key=lambda item: item[0])
    best = scored[0][1]
    leaderboard = [
        {
            "rank": index + 1,
            "logLoss": round(score, 4),
            "homeAdv": params.home_adv,
            "eloK": params.elo_k,
            "modelWeight": params.model_weight,
            "drawFloor": params.draw_floor,
        }
        for index, (score, params) in enumerate(scored[:8])
    ]
    return best, leaderboard


def metrics(backtest: list[dict]) -> dict:
    if not backtest:
        return {}
    correct = sum(1 for item in backtest if item["prediction"]["topSide"]["key"] == item["result"])
    profit = sum(
        item["prediction"]["topSide"]["odds"] - 1 if item["prediction"]["topSide"]["key"] == item["result"] else -1
        for item in backtest
    )
    value_items = [item for item in backtest if item["prediction"]["best"]["ev"] >= 0.04]
    value_profit = sum(item["prediction"]["best"]["odds"] - 1 if market_won(item["prediction"]["best"]["key"], item) else -1 for item in value_items)
    high = [item for item in backtest if item["prediction"]["tier"] == "high"]
    buckets = calibration_buckets(backtest)
    return {
        "matches": len(backtest),
        "accuracy": round(correct / len(backtest), 4),
        "logLoss": round(sum(log_loss(item["prediction"]["probs"][item["result"]]) for item in backtest) / len(backtest), 4),
        "brier": round(sum(brier(item["prediction"]["probs"], item["result"]) for item in backtest) / len(backtest), 4),
        "roi": round(profit / len(backtest), 4),
        "valueBets": len(value_items),
        "valueRoi": round(value_profit / len(value_items), 4) if value_items else None,
        "highConfidence": {
            "matches": len(high),
            "accuracy": round(sum(1 for item in high if item["prediction"]["topSide"]["key"] == item["result"]) / len(high), 4) if high else None,
        },
        "calibration": buckets,
    }


def market_won(key: str, item: dict) -> bool:
    if key in ("home", "draw", "away"):
        return key == item["result"]
    home_score = int(item["row"]["home_score"])
    away_score = int(item["row"]["away_score"])
    if key == "over25":
        return home_score + away_score > 2.5
    if key == "btts":
        return home_score > 0 and away_score > 0
    return False


def calibration_buckets(items: list[dict]) -> list[dict]:
    bucket_defs = [(0.0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.01)]
    buckets = []
    for low, high in bucket_defs:
        bucket = [item for item in items if low <= item["prediction"]["confidence"] < high]
        if not bucket:
            continue
        hit = sum(1 for item in bucket if item["prediction"]["topSide"]["key"] == item["result"])
        avg_conf = sum(item["prediction"]["confidence"] for item in bucket) / len(bucket)
        buckets.append(
            {
                "range": f"{int(low * 100)}-{int(high * 100)}%",
                "matches": len(bucket),
                "avgConfidence": round(avg_conf, 4),
                "hitRate": round(hit / len(bucket), 4),
            }
        )
    return buckets


def train_ratings(rows: list[dict[str, str]], params: Params) -> dict[str, float]:
    ratings: dict[str, float] = {}
    for row in sorted(rows, key=lambda item: item["date"]):
        result = match_result(int(row["home_score"]), int(row["away_score"]))
        ratings.setdefault(row["home"], 1500)
        ratings.setdefault(row["away"], 1500)
        ratings[row["home"]], ratings[row["away"]] = update_elo(ratings[row["home"]], ratings[row["away"]], result, params)
    return ratings


def read_factors() -> dict[str, dict[str, str]]:
    path = DATA / "team_factors.csv"
    if not path.exists():
        return {}
    return {row["team"]: row for row in read_csv(path) if row.get("team")}


def read_settled_results() -> list[dict[str, str]]:
    path = DATA / "settled_results.csv"
    if not path.exists():
        return []
    return read_csv(path)


def read_snapshot_backtest() -> list[dict[str, str]]:
    path = DATA / "snapshot_backtest.csv"
    if not path.exists():
        return []
    return read_csv(path)


def build_dashboard() -> dict:
    historical = sorted(read_csv(DATA / "historical_matches.csv"), key=lambda item: item["date"])
    params, leaderboard = calibrate(historical)
    all_seq = sequential_predictions(historical, params)
    test_start = max(100, int(len(all_seq) * 0.7))
    test_items = all_seq[test_start:]
    display_items = test_items[-350:]
    ratings = train_ratings(historical, params)
    factors = read_factors()

    upcoming_path = DATA / "upcoming_matches.csv"
    upcoming = read_csv(upcoming_path) if upcoming_path.exists() else []
    predictions = []
    for row in upcoming:
        odds = odds_from_row(row)
        predictions.append(
            {
                "id": row.get("id") or f'{row["home"]}-{row["away"]}',
                "sport": row.get("sport", "soccer"),
                "league": row.get("league", ""),
                "kickoff": row.get("kickoff", ""),
                "home": row["home"],
                "away": row["away"],
                "odds": odds.__dict__,
                "prediction": predict(row["home"], row["away"], ratings, odds, params, factors),
            }
        )

    backtest = [
        {
            "date": item["row"]["date"],
            "league": item["row"]["league"],
            "home": item["row"]["home"],
            "away": item["row"]["away"],
            "score": f'{item["row"]["home_score"]}-{item["row"]["away_score"]}',
            "result": item["result"],
            "oddsTiming": item["row"].get("odds_timing", "unknown"),
            "source": item["row"].get("source", ""),
            "prediction": item["prediction"],
        }
        for item in display_items
    ]

    report = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "params": params.__dict__,
        "leaderboard": leaderboard,
        "metrics": metrics(test_items),
        "displayBacktestRows": len(backtest),
        "ratingsCount": len(ratings),
    }
    (REPORTS / "model_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "generatedAt": report["generatedAt"],
        "params": report["params"],
        "leaderboard": leaderboard,
        "metrics": report["metrics"],
        "ratings": dict(sorted((team, round(rating, 1)) for team, rating in ratings.items())),
        "predictions": predictions,
        "backtest": backtest,
        "settledResults": read_settled_results(),
        "snapshotBacktest": read_snapshot_backtest(),
    }


def main() -> None:
    payload = build_dashboard()
    output = ROOT / "dashboard_data.js"
    output.write_text(
        "window.PREDICTOR_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {output}")
    print(f"Predictions: {len(payload['predictions'])}")
    print(f"Backtest rows: {len(payload['backtest'])}")
    print(f"Accuracy: {payload['metrics'].get('accuracy')}")
    print(f"Log loss: {payload['metrics'].get('logLoss')}")


if __name__ == "__main__":
    main()
