================================================================================
BANKING BEHAVIOURAL RISK ANALYSIS PLATFORM & TRANSACTION SIMULATOR
Project Overview, Tech Stack, Multi-Bank Architecture & Setup Guide
Version: 2.0.0 (Up to Date)
================================================================================

WELCOME TO THE PROJECT!
This file gives you and your Antigravity AI assistant all the information
needed to understand, set up, and run the entire multi-bank platform.

--------------------------------------------------------------------------------
1. WHAT IS THIS PROJECT?
--------------------------------------------------------------------------------
This platform simulates realistic digital banking transactions across three
major independent commercial banks (SBI, AXIS, and IOB) and feeds those
transactions through an AI-driven risk scoring, honeypot decoy, and lien
enforcement architecture.

The project is divided into 3 distinct subsystems:

[MODULE 1] TRANSACTION SIMULATOR (Frontend: 5173, Backend: 8000)
- Connects to 3 independent PostgreSQL databases (sbi_db, axis_db, iob_db).
- Generates realistic normal, business, and mule/fraud transactions.
- Tracks 8-state transaction lifecycles:
    * PROCESSING
    * COMPLETED
    * MONITORING
    * HONEYPOT
    * LIEN_APPLIED
    * RELEASED
    * RESTRICTED
    * FROZEN
- Displays dedicated Honeypot Status (NOT_TRANSFERRED, TRANSFERRED, ACTIVE, RELEASED)
  and Lien Status (NO_LIEN, LIEN_APPLIED, LIEN_RELEASED).
- Simulation modes: BALANCED MIX (Default), NORMAL MIX, BUSINESS MIX, MULE MIX.
- Tick speeds: SLOW, NORMAL, FAST.
- Clean banking transaction table with search, bank filter, status filter,
  type filter, column sorting, pagination, and expandable detail rows.
- Account Explorer drawer for personal & business accounts.
- IMPORTANT: The Transaction Simulator DOES NOT perform machine learning.
  All ML risk scoring, GNN analysis, and Network graphs belong to Modules 2 & 3.

[MODULE 2] BANK-LEVEL RISK MONITORING / ADSL (Frontend: 5174, Backend: 8001)
- Bank security operations center (SOC).
- Tabular XGBoost behavioural risk scoring.
- Feature importance attribution.
- Dynamic account risk monitoring.
- Honeypot redirection and Lien application engine.

[MODULE 3] DECENTRALIZED RISK COORDINATOR (Frontend: 5175, Backend: 8002)
- Cross-bank consortium coordination.
- PyTorch Geometric Graph Neural Networks (GNN / GAT / GraphSAGE).
- Multi-hop mule ring and circular flow tracing.
- NetworkX graph visualizer.

--------------------------------------------------------------------------------
2. COMPLETE TECHNOLOGY STACK
--------------------------------------------------------------------------------
BACKEND & CORE SERVICES:
- Python 3.11 / 3.12
- FastAPI (High-performance async ASGI web framework)
- Uvicorn (ASGI production server)
- Pydantic v2 (Data validation and schema enforcement)
- PostgreSQL 15 / 16 (Relational database engine)
- psycopg2-binary (Direct connection pooling; ZERO ORM for strict performance)
- python-dotenv (Environment configuration)

MACHINE LEARNING & GRAPH ANALYTICS:
- XGBoost (Tabular behavioural gradient boosting)
- Scikit-Learn (Classical ML, scalers, evaluation metrics)
- PyTorch & PyTorch Geometric (PyG) (Graph neural networks)
- NetworkX (Network graph creation, traversal, and cycle detection)
- NumPy & Pandas (Data processing and array mathematics)

FRONTEND DASHBOARDS:
- React 18 & React 19 (Component-based UI)
- Vite 6 (Lightning-fast frontend build tooling)
- Vanilla CSS & CSS Modules (Glassmorphism dark theme: #030712)
- Lucide React (Enterprise vector icons)
- JetBrains Mono & Outfit (High-clarity financial typography)
- Axios & Native Fetch (HTTP API client)

SCRIPTS & RUNNERS:
- Windows Batch (start_all.bat)
- Windows PowerShell (start_all.ps1)

--------------------------------------------------------------------------------
3. PORTS & SERVICES DIRECTORY
--------------------------------------------------------------------------------
Port 8000 -> Module 1 Simulator API        (Docs: http://localhost:8000/docs)
Port 8001 -> Module 2 Bank Risk API       (Docs: http://localhost:8001/docs)
Port 8002 -> Module 3 Coordinator API      (Docs: http://localhost:8002/docs)
Port 5173 -> TRANSACTION SIMULATOR UI      (URL:  http://localhost:5173)
Port 5174 -> Bank Risk Monitoring UI       (URL:  http://localhost:5174)
Port 5175 -> Coordinator & GNN UI          (URL:  http://localhost:5175)

--------------------------------------------------------------------------------
4. MULTI-BANK DATABASE ARCHITECTURE
--------------------------------------------------------------------------------
The platform maintains THREE independent PostgreSQL databases:
1. sbi_db  -> State Bank of India
2. axis_db -> Axis Bank
3. iob_db  -> Indian Overseas Bank

Configuration file: backend/.env
Example configuration:
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5432
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=your_postgres_password
  POSTGRES_DB=postgres

  SBI_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/sbi_db
  AXIS_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/axis_db
  IOB_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/iob_db

--------------------------------------------------------------------------------
5. FIRST-TIME INSTALLATION (STEP-BY-STEP)
--------------------------------------------------------------------------------
PREREQUISITES:
1. Python 3.11 or 3.12 installed and added to PATH.
2. Node.js 18+ (LTS) installed.
3. PostgreSQL 14+ installed and running on port 5432.

STEP 1: Python Virtual Environment & Backend Dependencies
  Open PowerShell in the project root:
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    cd backend
    pip install -r requirements.txt
    cd ..

STEP 2: Install Frontend Dependencies (All 3 Dashboards)
    cd frontend
    npm install
    cd ..\risk-dashboard
    npm install
    cd ..\coordinator-dashboard
    npm install
    cd ..

STEP 3: Initialize and Populate the 3 Bank Databases
    cd backend
    python database/create_databases.py
    python database/populate_databases.py
    python database/migrate_and_validate.py
    cd ..

--------------------------------------------------------------------------------
6. HOW TO RUN THE SYSTEM
--------------------------------------------------------------------------------
EASIEST METHOD: ONE-CLICK STARTUP
Simply double-click:
    start_all.bat
Or run in PowerShell:
    .\start_all.ps1

This automatically starts all 6 services in separate windows:
- Simulator UI:                       http://localhost:5173
- Bank Risk Monitoring UI:            http://localhost:5174
- Coordinator UI:                     http://localhost:5175
- Simulator API & Swagger Docs:       http://localhost:8000/docs

MANUAL METHOD (RUNNING INDIVIDUALLY IN SEPARATE TERMINALS):
Terminal 1: cd backend && python -m uvicorn main:app --port 8000
Terminal 2: cd backend && python -m uvicorn risk_api:app --port 8001
Terminal 3: cd backend && python -m uvicorn coordinator_api:app --port 8002
Terminal 4: cd frontend && npm run dev
Terminal 5: cd risk-dashboard && npm run dev
Terminal 6: cd coordinator-dashboard && npm run dev

--------------------------------------------------------------------------------
7. HOW TO RUN AUTOMATED TESTS
--------------------------------------------------------------------------------
1. Test all 3 backend APIs (8000, 8001, 8002):
    python test_apis.py

2. Validate live simulator, multi-bank routing, and dynamic ledger calculations:
    cd backend
    python scripts/validate_live_simulator.py

3. Build frontends for production:
    cd frontend && npm run build
    cd ..\risk-dashboard && npm run build
    cd ..\coordinator-dashboard && npm run build

--------------------------------------------------------------------------------
8. INSTRUCTIONS FOR ANTIGRAVITY AI ASSISTANT
--------------------------------------------------------------------------------
If you are Antigravity helping the developer, follow these golden rules:

1. ARCHITECTURAL BOUNDARIES:
   - Keep the Transaction Simulator (frontend/src/) purely for transaction
     generation, multi-bank ledger viewing, and lifecycle status display.
   - Do NOT add XGBoost scoring, GNN models, or NetworkX graphs into frontend/src/.
   - All ML belongs in backend/risk_engine, backend/gnn_detection,
     risk-dashboard, or coordinator-dashboard.

2. DATABASE INTEGRITY:
   - Keep sbi_db, axis_db, and iob_db as separate independent databases.
   - Do NOT introduce an ORM (SQLAlchemy, Django, Alembic). All queries use
     psycopg2 connection pools in backend/database/db_connection.py.

3. TRANSACTION STATUS SYSTEM:
   - Supported statuses: PROCESSING, COMPLETED, MONITORING, HONEYPOT,
     LIEN_APPLIED, RELEASED, RESTRICTED, FROZEN.
   - Honeypot statuses: NOT_TRANSFERRED, TRANSFERRED, ACTIVE, RELEASED.
   - Lien statuses: NO_LIEN, LIEN_APPLIED, LIEN_RELEASED.

4. RECENT CHANGES (v2.0):
   - Renamed dashboard to "TRANSACTION SIMULATOR".
   - Clean banking table with search, bank filter, status filter, type filter.
   - Speed buttons (SLOW, NORMAL, FAST) and Mix buttons (BALANCED, NORMAL,
     BUSINESS, MULE).
   - Removed NetworkGraphView from the Simulator dashboard.

================================================================================
End of Guide. Happy Coding!
================================================================================
