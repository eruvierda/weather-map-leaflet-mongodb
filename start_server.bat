@echo off
setlocal

:: Ensure we are running from the project root
pushd %~dp0

echo ==================================================
echo   Weather Map - UI and API Server Launcher
echo ==================================================
echo.

echo [1/2] Starting UI static server (serve_local.py)...
start "UI Server" cmd /k python serve_local.py
if errorlevel 1 (
    echo   !! Failed to start UI server. Check that Python is installed and serve_local.py exists.
) else (
    echo   -> UI server window opened.
)
echo.

echo [2/2] Starting Weather API server (openmeteo\weather_api_server.py)...
start "Weather API" cmd /k python openmeteo\weather_api_server.py
if errorlevel 1 (
    echo   !! Failed to start Weather API server. Ensure dependencies are installed.
) else (
    echo   -> Weather API server window opened.
)
echo.
echo All servers launched in separate terminals. Close their windows to stop.

popd
endlocal
pause