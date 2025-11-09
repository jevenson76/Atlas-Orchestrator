' Auto-execute installer VBScript
Set objShell = CreateObject("WScript.Shell")
objShell.Run "\\wsl.localhost\Ubuntu\home\jevenson\.claude\lib\CLICK_TO_INSTALL.bat", 1, False
Set objShell = Nothing