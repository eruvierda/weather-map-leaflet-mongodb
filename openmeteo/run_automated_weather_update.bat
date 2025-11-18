@echo off
echo Running Automated Weather Data Update...
echo.

cd /d "%~dp0"
python update_all_weather_auto.py

echo.
echo Automated Weather Update completed.
