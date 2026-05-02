# AutoOS Master Launch Script

Write-Host "Cleaning up previous sessions..." -ForegroundColor Gray
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Stop-Process -Name node -Force -ErrorAction SilentlyContinue

Write-Host "Starting AutoOS Gateway..." -ForegroundColor Cyan

# 1. Start the FastAPI Backend
Write-Host "Starting Backend Server..." -ForegroundColor Yellow
$BackendProcess = Start-Process -FilePath ".\server\.venv\Scripts\python.exe" -ArgumentList "-m server.main" -PassThru -WindowStyle Hidden

# 2. Start the Frontend (Electron + React)
Write-Host "Starting Desktop UI..." -ForegroundColor Yellow
Set-Location .\app
npm run dev

# Cleanup when the UI is closed
Write-Host "Shutting down Backend..." -ForegroundColor Red
Stop-Process -Id $BackendProcess.Id -Force
Set-Location ..
Write-Host "Done." -ForegroundColor Green
