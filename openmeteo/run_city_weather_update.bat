@echo off
echo Starting City Weather Update...
echo.

cd /d "%~dp0"
python update_city_weather.py

echo.
echo City Weather Update completed.
pause
