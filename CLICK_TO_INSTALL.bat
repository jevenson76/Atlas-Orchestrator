@echo off
title Installing Sync Wrapper Demo...
color 0B
cls

echo.
echo     ************************************************
echo     *                                              *
echo     *       SYNC WRAPPER DEMO - INSTALLER         *
echo     *                                              *
echo     ************************************************
echo.
echo     Starting installation...
echo.

:: Navigate to the installation directory
cd /d "\\wsl$\Ubuntu\home\jevenson\.claude\lib"

:: Check if we're in the right place
if not exist "install-launcher.ps1" (
    color 0C
    echo.
    echo     ERROR: Installation files not found!
    echo.
    echo     Trying alternative path...
    cd /d "\\wsl.localhost\Ubuntu\home\jevenson\.claude\lib"

    if not exist "install-launcher.ps1" (
        echo.
        echo     ERROR: Could not find installation files.
        echo     Please ensure WSL is running.
        echo.
        pause
        exit /b 1
    )
)

echo     [OK] Installation files found
echo.
echo     Creating shortcuts...
echo.

:: Run the installer
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "install-launcher.ps1"

:: Check result
if %ERRORLEVEL% EQU 0 (
    color 0A
    echo.
    echo     ************************************************
    echo     *                                              *
    echo     *         INSTALLATION SUCCESSFUL!             *
    echo     *                                              *
    echo     ************************************************
    echo.
    echo     Shortcuts created at:
    echo       √ Desktop: Sync Wrapper Demo
    echo       √ Start Menu: Claude Tools folder
    echo       √ Quick Access: ClaudeTools folder
    echo.
    echo     ************************************************
    echo.
    echo     You can now double-click the desktop icon
    echo     to launch the demo!
    echo.
) else (
    color 0E
    echo.
    echo     Installation may have encountered issues.
    echo     Please check the messages above.
    echo.
)

echo     Press any key to close this window...
pause >nul
exit