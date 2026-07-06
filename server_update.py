from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WEB_ROOT = Path(os.environ.get("WEB_ROOT", "/var/www/sport-lottery-predictor"))


def run(args: list[str]) -> int:
    print("+", " ".join(args), flush=True)
    proc = subprocess.run(args, cwd=ROOT)
    return proc.returncode


def copy_web() -> None:
    WEB_ROOT.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "style.css", "app.js", "dashboard_data.js"):
        shutil.copy2(ROOT / name, WEB_ROOT / name)


def main() -> int:
    # Historical soccer data is free and safe to refresh. Upcoming odds need THE_ODDS_API_KEY.
    fetch_code = run([sys.executable, str(ROOT / "fetch_data.py")])
    if fetch_code != 0:
        print("fetch_data.py failed; continuing with existing historical data")

    if os.environ.get("THE_ODDS_API_KEY"):
        odds_code = run([sys.executable, str(ROOT / "fetch_odds_api.py")])
        if odds_code != 0:
            print("fetch_odds_api.py did not update upcoming odds; keeping existing upcoming CSV")
    else:
        print("THE_ODDS_API_KEY is not set; keeping manual upcoming CSV")

    factors_code = run([sys.executable, str(ROOT / "fetch_factors.py")])
    if factors_code != 0:
        print("fetch_factors.py failed; keeping existing team factors")

    if os.environ.get("THE_ODDS_API_KEY"):
        results_code = run([sys.executable, str(ROOT / "fetch_results.py")])
        if results_code != 0:
            print("fetch_results.py failed; keeping existing settled results")

    model_code = run([sys.executable, str(ROOT / "model.py")])
    if model_code != 0:
        return model_code

    copy_web()
    print(f"Published dashboard to {WEB_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
