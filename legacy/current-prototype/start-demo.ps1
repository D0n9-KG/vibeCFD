$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

Write-Host "Starting agent executor, backend, and frontend for the submarine workflow demo..." -ForegroundColor Cyan

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$backendPath'; python -m uvicorn app.claude_executor_main:app --host 127.0.0.1 --port 8020"
)

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "`$env:SUBMARINE_EXECUTION_ENGINE='agent_executor'; `$env:SUBMARINE_EXECUTOR_BASE_URL='http://127.0.0.1:8020'; Set-Location '$backendPath'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8010"
)

Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$frontendPath'; npm run dev -- --host 127.0.0.1 --port 5173"
)

Write-Host ""
Write-Host "Frontend: http://127.0.0.1:5173" -ForegroundColor Green
Write-Host "Backend : http://127.0.0.1:8010/api/health" -ForegroundColor Green
Write-Host "Agent   : http://127.0.0.1:8020/api/health" -ForegroundColor Green
