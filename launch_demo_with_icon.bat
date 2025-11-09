@echo off
REM Sync Wrapper Demo Launcher with Icon for Windows
REM Launches the demo through WSL with visual ASCII icon

color 0B
cls

echo.
echo     ********************************************
echo     *      SYNC WRAPPER DEMO LAUNCHER         *
echo     ********************************************
echo.
echo             ASYNC ~~~~^> [S] =====^> SYNC
echo.
echo          async def      run_async_safely()
echo              ^|              ^|
echo          coroutine  --^>  result
echo.
echo     ********************************************
echo.
echo     Starting interactive GUI demo...
echo.

timeout /t 2 /nobreak > nul

wsl python3 /home/jevenson/.claude/lib/demo_sync_wrapper.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    color 0C
    echo ********************************************
    echo ERROR: Failed to launch demo
    echo.
    echo Troubleshooting:
    echo 1. Ensure WSL is installed
    echo 2. Verify Python3 is installed in WSL:
    echo    wsl python3 --version
    echo 3. Check file path:
    echo    wsl ls -la /home/jevenson/.claude/lib/demo_sync_wrapper.py
    echo 4. Install tkinter if missing:
    echo    wsl sudo apt-get install python3-tk
    echo ********************************************
    echo.
    pause
)

exit