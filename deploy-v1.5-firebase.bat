@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo Jayuminton v1.5 Firebase Function deploy
echo Project: jayuminton-push
echo ================================================
echo.

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js is not installed.
  echo Install Node.js LTS, then run this file again.
  echo https://nodejs.org/
  pause
  exit /b 1
)

echo [1/3] Firebase login
call npx --yes firebase-tools@latest login
if errorlevel 1 goto :failed

echo.
echo [2/3] Save Firebase secret
 echo Paste the SAME value used for GitHub secret JAYUMINTON_PUSH_SHARED_SECRET.
call npx --yes firebase-tools@latest functions:secrets:set JAYUMINTON_PUSH_SECRET --project jayuminton-push
if errorlevel 1 goto :failed

echo.
echo [3/3] Deploy publishAssignment function
call npx --yes firebase-tools@latest deploy --only functions:publishAssignment --project jayuminton-push
if errorlevel 1 goto :failed

echo.
echo ================================================
echo Deployment completed.
echo Function URL:
echo https://asia-northeast3-jayuminton-push.cloudfunctions.net/publishAssignment
echo ================================================
pause
exit /b 0

:failed
echo.
echo [ERROR] Deployment stopped. Copy or screenshot the red error text.
pause
exit /b 1
