@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==================================================
echo Jayuminton v1.5 browser push hosting deployment
echo Firebase project: jayuminton-push
echo ==================================================
echo.
set /p RELAY_URL=Paste the Apps Script /exec URL and press Enter: 

if "%RELAY_URL%"=="" (
  echo [ERROR] Apps Script URL is empty.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-Content -Raw 'web-push\config.template.js').Replace('__RELAY_URL__',$env:RELAY_URL) ^| Set-Content -Encoding UTF8 'web-push\config.js'"
if errorlevel 1 goto :failed

echo.
echo [1/2] Firebase login
call npx --yes firebase-tools@latest login
if errorlevel 1 goto :failed

echo.
echo [2/2] Deploy free Firebase Hosting
call npx --yes firebase-tools@latest deploy --only hosting --project jayuminton-push
if errorlevel 1 goto :failed

echo.
echo ==================================================
echo Deployment completed.
echo Open:
echo https://jayuminton-push.web.app
echo ==================================================
pause
exit /b 0

:failed
echo.
echo [ERROR] Deployment stopped. Capture the red error text.
pause
exit /b 1
