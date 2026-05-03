@echo off
setlocal

title AutoOS Native Launcher
echo ======================================================
echo   AutoOS: High-Performance Windows Native Assistant
echo ======================================================

:: OS Enforcement
if "%OS%"=="Windows_NT" goto :OS_OK
echo FATAL: AutoOS is strictly for Windows.
pause
exit /b 1

:OS_OK
:: Environment Verification
if exist ".venv\Scripts\python.exe" goto :ENV_OK
echo [ERROR] Python Virtual Environment (.venv) not found.
echo Please ensure the project is installed correctly.
pause
exit /b 1

:ENV_OK
echo [1/2] Cleaning up previous sessions and ports...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
taskkill /F /IM electron.exe /T >nul 2>&1
:: Kill anything on 8765 and 5173 via PowerShell (more robust)
powershell -Command "$p = Get-NetTCPConnection -LocalPort 8765, 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($p) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue }"
timeout /t 2 /nobreak >nul

echo [2/2] Launching Windows Native Backend...
set TF_ENABLE_ONEDNN_OPTS=0
:: Use cmd /k to keep the window open if the backend crashes
start "AutoOS Backend" cmd /k "cd /d %~dp0server && ..\.venv\Scripts\python.exe main.py"

echo.
echo Waiting for Backend to initialize...
:WAIT_BACKEND
timeout /t 1 /nobreak >nul
powershell -Command "try { $res = Invoke-WebRequest -Uri http://localhost:8765/health -UseBasicParsing -TimeoutSec 1; if ($res.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo | set /p="."
    goto :WAIT_BACKEND
)
echo [OK] Backend is Live.

echo.
echo Launching Desktop UI...
echo ======================================================
echo  READY: Assistant is connected and listening.
echo ======================================================
cd /d "%~dp0app"
call npm run dev

echo.
echo Stopping Backend Services...
taskkill /F /IM python.exe /T >nul 2>&1
cd ..
echo Done.
pause
