@echo off
REM ZeroTouch Atlas Launcher Script for Windows
REM Runs the bash launcher via WSL

echo ================================
echo   ZeroTouch Atlas Launcher
echo ================================
echo.

REM Get the WSL path to the script
set "WSL_SCRIPT=/home/jevenson/.claude/lib/start_atlas.sh"

echo Starting ZeroTouch Atlas via WSL...
echo Access the app at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the bash launcher in WSL
wsl bash %WSL_SCRIPT%

pause
