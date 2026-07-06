@echo off
setlocal
set PY=C:\Users\88697\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
if not exist "%PY%" (
  echo Python runtime not found: %PY%
  pause
  exit /b 1
)
"%PY%" "%~dp0fetch_data.py"
if errorlevel 1 (
  echo Fetch failed. Keeping existing data.
) else (
  echo Fetch complete.
)
"%PY%" "%~dp0fetch_odds_api.py"
if errorlevel 1 (
  echo Odds API not used. Keeping manual upcoming_matches.csv.
) else (
  echo Odds API upcoming odds updated.
)
"%PY%" "%~dp0model.py"
pause
