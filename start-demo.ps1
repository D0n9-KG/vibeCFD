$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

Write-Host "Starting backend and frontend for the submarine workflow demo..." -ForegroundColor Cyan

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$backendPath'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload"
)

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$frontendPath'; npm run dev -- --host 127.0.0.1 --port 5173"
)

Write-Host ""
Write-Host "Frontend: http://127.0.0.1:5173" -ForegroundColor Green
Write-Host "Backend : http://127.0.0.1:8010/api/health" -ForegroundColor Green
