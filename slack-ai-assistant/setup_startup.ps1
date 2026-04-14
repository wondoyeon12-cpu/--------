$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\SlackBot_AutoStart.lnk")
$Shortcut.TargetPath = "C:\Users\user\OneDrive\Desktop\에이전트프로젝트\slack-ai-assistant\hidden_start.vbs"
$Shortcut.WorkingDirectory = "C:\Users\user\OneDrive\Desktop\에이전트프로젝트\slack-ai-assistant"
$Shortcut.Save()
