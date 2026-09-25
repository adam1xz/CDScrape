@echo off
set /p "id=Enter playlist (blank to skip download): "
set /p "ans=Burn (none/data/audio): "
set /p "fol=Album: "
set /p "dry=Dry run, no disc written (y/n): "
set "dryflag="
if /i "%dry%"=="y" set "dryflag=--dry-run"
cd /d "%~dp0"
if "%id%"=="" (
    .venv\Scripts\python.exe main.py --burn-only %fol% --burn %ans% %dryflag%
) else (
    .venv\Scripts\python.exe main.py "%id%" --out %fol% --burn %ans% %dryflag%
)
pause
