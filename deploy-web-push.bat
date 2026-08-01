@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==================================================
echo Jayuminton v1.5 unified member page + browser push
echo Firebase project: jayuminton-push
echo ==================================================
echo.
set /p RELAY_URL=Paste the notification Apps Script /exec URL and press Enter: 

if "%RELAY_URL%"=="" (
  echo [ERROR] Apps Script URL is empty.
  pause
  exit /b 1
)

set RELAY_URL=%RELAY_URL%
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=Get-Content -Raw 'web-push\config.template.js'; $t=$t.Replace('__RELAY_URL__',$env:RELAY_URL); [IO.File]::WriteAllText((Resolve-Path 'web-push\config.js'),$t,(New-Object Text.UTF8Encoding($false)))"
if errorlevel 1 goto :failed

echo.
echo [1/2] Firebase login
call npx --yes firebase-tools@latest login
if errorlevel 1 goto :failed

echo.
echo [2/2] Deploy one-page member PWA
call npx --yes firebase-tools@latest deploy --only hosting --project jayuminton-push
if errorlevel 1 goto :failed

echo.
echo ==================================================
echo Deployment completed.
echo Use this as the ONLY member URL:
echo https://jayuminton-push.web.app/
echo ==================================================
pause
exit /b 0

:failed
echo.
echo [ERROR] Deployment stopped. Capture the red error text.
pause
exit /b 1
