@echo off
echo Starting Unified Weather Data Update System...
echo.

cd /d "%~dp0"
python update_all_weather.py

echo.
echo Unified Weather Update System completed.
pause
