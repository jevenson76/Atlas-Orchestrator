# Direct PowerShell installer execution
$scriptPath = "\\wsl.localhost\Ubuntu\home\jevenson\.claude\lib\install-launcher.ps1"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  SYNC WRAPPER DEMO INSTALLER" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Execute the installer directly
& $scriptPath

Write-Host ""
Write-Host "Installation process completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")