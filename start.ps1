# AutoOS Master Launch Script

Write-Host "Checking environment dependencies..." -ForegroundColor Gray

# Check Python
if (!(Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Error: Python virtual environment not found. Please run 'python -m venv .venv' and install requirements." -ForegroundColor Red
    exit 1
}

# Check Node modules
if (!(Test-Path ".\app\node_modules")) {
    Write-Host "Node modules missing in 'app'. Running 'npm install'..." -ForegroundColor Yellow
    Set-Location .\app
    npm install
    Set-Location ..
}

Write-Host "Cleaning up previous sessions..." -ForegroundColor Gray
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Stop-Process -Name node -Force -ErrorAction SilentlyContinue
Stop-Process -Name electron -Force -ErrorAction SilentlyContinue

Write-Host "Starting AutoOS Gateway..." -ForegroundColor Cyan

# 1. Start the FastAPI Backend
Write-Host "Starting Backend Server..." -ForegroundColor Yellow
$BackendProcess = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m server.main" -PassThru -NoNewWindow

# Wait for backend to initialize
Start-Sleep -Seconds 3

# 2. Start the Frontend (Electron + React)
Write-Host "Starting Desktop UI..." -ForegroundColor Yellow
Set-Location .\app
npm run dev

# Cleanup when the UI is closed
Write-Host "Shutting down Backend..." -ForegroundColor Red
if ($BackendProcess) {
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
}
Set-Location ..
Write-Host "Done." -ForegroundColor Green
