@echo off
echo.
echo ========================================
echo   INSTALLING SYNC WRAPPER DEMO
echo ========================================
echo.

cd /d "\\wsl$\Ubuntu\home\jevenson\.claude\lib"
powershell.exe -ExecutionPolicy Bypass -File "\\wsl$\Ubuntu\home\jevenson\.claude\lib\install-launcher.ps1"

echo.
echo Installation complete!
pause