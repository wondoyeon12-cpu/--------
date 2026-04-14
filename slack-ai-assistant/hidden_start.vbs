Set WshShell = CreateObject("WScript.Shell")
scriptFolder = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run chr(34) & scriptFolder & "\run_slackbot.bat" & Chr(34), 0
Set WshShell = Nothing
