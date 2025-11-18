@echo off
echo Starting daily weather data update...
cd /d "%~dp0"
python scheduled_update.py
echo Daily update completed.
pause 