@echo off
chcp 65001 >nul
echo ==============================================
echo 슬랙봇 윈도우 시작프로그램 등록 스크립트
echo ==============================================

set "startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "vbs_path=%~dp0hidden_start.vbs"

echo 단축 아이콘을 생성 중입니다...

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%temp%\CreateShortcut.vbs"
echo sLinkFile = "%startup_folder%\SlackBot_AutoStart.lnk" >> "%temp%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%temp%\CreateShortcut.vbs"
echo oLink.TargetPath = "%vbs_path%" >> "%temp%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%~dp0" >> "%temp%\CreateShortcut.vbs"
echo oLink.Save >> "%temp%\CreateShortcut.vbs"

cscript //nologo "%temp%\CreateShortcut.vbs"
del "%temp%\CreateShortcut.vbs"

echo.
echo [성공] 윈도우 시작프로그램에 슬랙봇이 등록되었습니다!
echo 이제 노트북 컴퓨터를 켤 때마다 자동으로 봇이 숨김 상태(백그라운드)로 작동합니다.
echo.
echo 당장 지금 봇을 켜시려면 폴더 안에 있는 'hidden_start.vbs'를 더블클릭하세요!
echo.
pause
