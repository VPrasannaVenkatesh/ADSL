@echo off
title Banking Behavioural Risk Analysis Platform Launcher
echo ======================================================================
echo Starting Banking Behavioural Risk Analysis Platform
echo ======================================================================

echo [1/6] Launching Module 1 API and Live Simulator (Port 8000)...
start "Backend - Simulator & API (Port 8000)" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --port 8000"

echo [2/6] Launching Module 2 Risk Monitoring API (Port 8001)...
start "Backend - Risk API (Port 8001)" cmd /k "cd /d %~dp0backend && python -m uvicorn risk_api:app --port 8001"

echo [3/6] Launching Module 3 Decentralized Coordinator API (Port 8002)...
start "Backend - Coordinator API (Port 8002)" cmd /k "cd /d %~dp0backend && python -m uvicorn coordinator_api:app --port 8002"

echo [4/6] Launching Live Transaction Simulator Dashboard (Port 5173)...
start "Frontend - Simulator Dashboard (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo [5/6] Launching Bank-Level Risk Monitoring Dashboard (Port 5174)...
start "Frontend - Risk Dashboard (Port 5174)" cmd /k "cd /d %~dp0risk-dashboard && npm run dev"

echo [6/6] Launching Decentralized Risk Coordinator Dashboard (Port 5175)...
start "Frontend - Coordinator Dashboard (Port 5175)" cmd /k "cd /d %~dp0coordinator-dashboard && npm run dev"

echo ======================================================================
echo All 6 services started!
echo - Simulator Dashboard:           http://localhost:5173
echo - Risk Monitoring Dashboard:     http://localhost:5174
echo - Coordinator Dashboard:         http://localhost:5175
echo - Main Simulator API / Docs:     http://localhost:8000/docs
echo ======================================================================
