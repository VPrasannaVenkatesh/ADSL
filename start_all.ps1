# PowerShell launcher for Banking Behavioural Risk Analysis Platform
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Starting Banking Behavioural Risk Analysis Platform" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

$Root = $PSScriptRoot

Write-Host "[1/6] Launching Module 1 API & Live Simulator (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; python -m uvicorn main:app --port 8000"

Write-Host "[2/6] Launching Module 2 Risk Monitoring API (Port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; python -m uvicorn risk_api:app --port 8001"

Write-Host "[3/6] Launching Module 3 Decentralized Coordinator API (Port 8002)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; python -m uvicorn coordinator_api:app --port 8002"

Write-Host "[4/6] Launching Live Transaction Simulator Dashboard (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\frontend'; npm run dev"

Write-Host "[5/6] Launching Bank-Level Risk Monitoring Dashboard (Port 5174)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\risk-dashboard'; npm run dev"

Write-Host "[6/6] Launching Decentralized Risk Coordinator Dashboard (Port 5175)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\coordinator-dashboard'; npm run dev"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "All 6 services started!" -ForegroundColor Green
Write-Host " - Simulator Dashboard:           http://localhost:5173" -ForegroundColor White
Write-Host " - Risk Monitoring Dashboard:     http://localhost:5174" -ForegroundColor White
Write-Host " - Coordinator Dashboard:         http://localhost:5175" -ForegroundColor White
Write-Host " - Main Simulator API / Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
