@echo off
echo Running Scheduled City Weather Update...
echo.

cd /d "%~dp0"
python scheduled_city_update.py

echo.
echo Scheduled City Weather Update completed.
