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
echo [1/2] Cleaning up previous sessions...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

echo [2/2] Launching Windows Native Backend...
:: Use cmd /k to keep the window open if the backend crashes
start "AutoOS Backend" cmd /k ".\.venv\Scripts\python.exe server\main.py"

echo.
echo Launching Desktop UI...
echo ======================================================
echo  IMPORTANT: Wait until the Backend window shows:
echo  "Uvicorn running on http://0.0.0.0:8765"
echo  before sending any commands to the assistant.
echo ======================================================
cd app
call npm run dev

echo.
echo Stopping Backend Services...
taskkill /F /IM python.exe /T >nul 2>&1
cd ..
echo Done.
pause
