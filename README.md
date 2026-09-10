# Banking Behavioural Risk Analysis Platform & Transaction Simulator

[![Platform Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%20%7C%2019-61dafb.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%20%7C%2016-336791.svg)](https://www.postgresql.org/)
[![Vite](https://img.shields.io/badge/Vite-6.x-646CFF.svg)](https://vitejs.dev/)

> **Welcome to the Project!** This document contains everything you and your **Antigravity AI Coding Assistant** need to know to set up, understand, run, and develop this distributed banking simulation and behavioural risk platform.

---

## 1. System Overview & Architecture

This platform simulates real-time digital banking transactions across three major commercial banks (**SBI**, **AXIS**, and **IOB**) and provides a multi-stage risk detection, honeypot isolation, and lien enforcement pipeline.

The project is strictly partitioned into **three decoupled subsystems**:

```
+----------------------------------------------------------------------------------------------------+
|                                    DISTRIBUTED BANKING PLATFORM                                    |
+----------------------------------------------------------------------------------------------------+
                                                  |
       +------------------------------------------+------------------------------------------+
       |                                          |                                          |
       v                                          v                                          v
+-----------------------------+        +-----------------------------+        +-----------------------------+
|          MODULE 1           |        |          MODULE 2           |        |          MODULE 3           |
|    TRANSACTION SIMULATOR    | =====> |   BANK RISK MONITOR (ADSL)  | =====> | DECENTRALIZED COORDINATOR   |
|   (Ports: 8000 / 5173)      |        |   (Ports: 8001 / 5174)      |        |   (Ports: 8002 / 5175)      |
+-----------------------------+        +-----------------------------+        +-----------------------------+
| - Independent Bank DBs      |        | - Tabular XGBoost Scoring   |        | - Cross-Bank Mule Networks  |
| - Realistic Multi-Bank Txns |        | - Dynamic Account Risk      |        | - Graph Neural Nets (GNN)   |
| - Normal / Business / Mules |        | - Feature Importance        |        | - NetworkX Visualizer       |
| - 8-State Txn Lifecycles    |        | - Honeypot Deflection Rules |        | - Decentralized Consensus   |
| - Honeypot & Lien Statuses  |        | - Lien Application Engine   |        | - Multi-Hop Ring Tracing    |
| - NO Machine Learning       |        |                             |        |                             |
+-----------------------------+        +-----------------------------+        +-----------------------------+
```

### Module 1: TRANSACTION SIMULATOR (Frontend: 5173, Backend: 8000)
- **Role**: Simulates cross-bank and intra-bank transactions across 3 independent bank databases.
- **Responsibilities**:
  1. Connecting to SBI, AXIS, and IOB PostgreSQL databases.
  2. Generating balanced mixes of **Normal transactions** (UPI, IMPS, NEFT, utilities), **Business transactions** (commercial settlements, B2B, vendor, payroll), and **Mule/Fraud patterns** (Fan-In, Fan-Out, Rapid Forwarding, Multi-Hop Chains, Circular Flows, Amount Splitting).
  3. Managing transaction lifecycle: `PROCESSING`, `COMPLETED`, `MONITORING`, `HONEYPOT`, `LIEN_APPLIED`, `RELEASED`, `RESTRICTED`, `FROZEN`.
  4. Displaying `Honeypot Status` (`NOT_TRANSFERRED`, `TRANSFERRED`, `ACTIVE`, `RELEASED`) and `Lien Status` (`NO_LIEN`, `LIEN_APPLIED`, `LIEN_RELEASED`).
  5. Clean banking transaction table with column search, bank filter, status filter, type filter, sorting, and pagination.
  6. Account Explorer drawer for personal and business accounts.
- **Architectural Boundary**: The Transaction Simulator **DOES NOT** perform ML inference (no XGBoost, no GNN, no NetworkX graphs, no RL). Those reside downstream in Modules 2 & 3.

### Module 2: Bank-Level Risk Monitoring / ADSL (Frontend: 5174, Backend: 8001)
- **Role**: Bank security operations center (SOC).
- **Responsibilities**: High-throughput XGBoost feature scoring, account behavioural risk profiling, decision explanation, automated honeypot account routing, and lien enforcement.

### Module 3: Decentralized Risk Coordinator (Frontend: 5175, Backend: 8002)
- **Role**: Inter-bank consortium coordinator.
- **Responsibilities**: Aggregating cross-bank signals without sharing raw PII, executing PyTorch Geometric Graph Neural Networks (GNN / GAT), detecting multi-hop mule rings, and rendering interactive network graphs.

---

## 2. Complete Technology Stack

### Backend & Core Services
- **Language**: Python 3.11 / 3.12
- **Web Framework**: [FastAPI](https://fastapi.tiangolo.com/) with asynchronous ASGI server [Uvicorn](https://www.uvicorn.org/)
- **Data Validation & Schemas**: [Pydantic v2](https://docs.pydantic.dev/)
- **Database Engine**: [PostgreSQL 15 / 16](https://www.postgresql.org/)
- **Database Driver**: [psycopg2-binary](https://pypi.org/project/psycopg2-binary/) (Direct connection pooling; **NO ORM / NO SQLAlchemy** for strict performance and direct SQL auditing)
- **Environment Management**: [python-dotenv](https://pypi.org/project/python-dotenv/)

### Machine Learning, Graph & Analytics
- **Tabular Risk Scoring**: [XGBoost](https://xgboost.readthedocs.io/)
- **Graph Neural Networks**: [PyTorch](https://pytorch.org/) & [PyTorch Geometric (PyG)](https://pyg.org/)
- **Graph Topology & Algorithms**: [NetworkX](https://networkx.org/)
- **Classical ML & Metrics**: [Scikit-Learn](https://scikit-learn.org/)
- **Numerical Processing**: [NumPy](https://numpy.org/) & [Pandas](https://pandas.pydata.org/)

### Frontend Dashboards
- **Core UI**: [React 18 / 19](https://react.dev/)
- **Build Tooling & Dev Server**: [Vite 6](https://vitejs.dev/)
- **Styling**: Vanilla CSS / CSS Modules with modern Glassmorphism, tailored dark theme (`#030712`), and CSS grid/flex layouts
- **Icons**: [Lucide React](https://lucide.dev/)
- **Typography**: [Google Fonts](https://fonts.google.com/) — *Outfit* (Modern UI) and *JetBrains Mono* (Ledger figures and transaction IDs)
- **HTTP Client**: Native `fetch` and [Axios](https://axios-http.com/)

---

## 3. Port Allocation & Services Map

| Port | Service | Subsystem / Directory | URL / Swagger |
|---|---|---|---|
| **8000** | Simulator API & Ledger Engine | `backend/main.py` | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **8001** | Bank Risk Engine API | `backend/risk_api.py` | [http://localhost:8001/docs](http://localhost:8001/docs) |
| **8002** | Decentralized Coordinator API | `backend/coordinator_api.py` | [http://localhost:8002/docs](http://localhost:8002/docs) |
| **5173** | **TRANSACTION SIMULATOR UI** | `frontend/` | [http://localhost:5173](http://localhost:5173) |
| **5174** | Bank-Level Risk Dashboard | `risk-dashboard/` | [http://localhost:5174](http://localhost:5174) |
| **5175** | Coordinator & GNN Dashboard | `coordinator-dashboard/` | [http://localhost:5175](http://localhost:5175) |

---

## 4. Multi-Bank Database Setup (PostgreSQL)

The platform maintains **three completely independent PostgreSQL databases** to reflect realistic banking isolation:
- `sbi_db` — State Bank of India
- `axis_db` — Axis Bank
- `iob_db` — Indian Overseas Bank

### Database Credentials (`backend/.env`)
Ensure PostgreSQL is running locally on port `5432`. Create or check `backend/.env`:

```ini
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=postgres

SBI_DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/sbi_db
AXIS_DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/axis_db
IOB_DATABASE_URL=postgresql://postgres:your_postgres_password@localhost:5432/iob_db
```

---

## 5. First-Time Installation & Setup Guide

### Step 1: Clone or Open Project in IDE
Ensure your terminal is in the project root directory:
```powershell
cd c:\path\to\FinalYr
```

### Step 2: Set Up Python Virtual Environment & Dependencies
```powershell
# Create virtual environment (if not already present)
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: Install Frontend Dependencies
The project contains 3 frontends. Run `npm install` in each:
```powershell
# 1. Transaction Simulator Frontend
cd frontend
npm install
cd ..

# 2. Bank Risk Dashboard Frontend
cd risk-dashboard
npm install
cd ..

# 3. Decentralized Coordinator Dashboard Frontend
cd coordinator-dashboard
npm install
cd ..
```

### Step 4: Initialize & Populate PostgreSQL Databases
Run the database creation and seeding scripts in order:
```powershell
cd backend

# 1. Create the 3 databases (sbi_db, axis_db, iob_db) and run schema.sql
python database/create_databases.py

# 2. Populate accounts, personal/business profiles, and seed history
python database/populate_databases.py

# 3. Run schema migration & validate connection across all 3 DBs
python database/migrate_and_validate.py

cd ..
```

---

## 6. How to Run the Platform

### Option A: One-Click Startup (Recommended)
We provide pre-configured launch scripts that spawn all 6 services in their own terminal windows:

#### Using Windows Command Prompt / File Explorer:
Double-click:
```bat
start_all.bat
```

#### Using Windows PowerShell:
```powershell
.\start_all.ps1
```

All 6 services will launch automatically:
- Simulator UI: [http://localhost:5173](http://localhost:5173)
- Risk Monitoring UI: [http://localhost:5174](http://localhost:5174)
- Coordinator UI: [http://localhost:5175](http://localhost:5175)
- Simulator API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option B: Manual Startup (Terminal by Terminal)
If you want to start or debug services individually:

#### Terminal 1 — Simulator Backend (Port 8000)
```powershell
cd backend
python -m uvicorn main:app --port 8000
```

#### Terminal 2 — Bank Risk API (Port 8001)
```powershell
cd backend
python -m uvicorn risk_api:app --port 8001
```

#### Terminal 3 — Coordinator API (Port 8002)
```powershell
cd backend
python -m uvicorn coordinator_api:app --port 8002
```

#### Terminal 4 — Transaction Simulator Dashboard (Port 5173)
```powershell
cd frontend
npm run dev
```

#### Terminal 5 — Bank Risk Dashboard (Port 5174)
```powershell
cd risk-dashboard
npm run dev
```

#### Terminal 6 — Coordinator Dashboard (Port 5175)
```powershell
cd coordinator-dashboard
npm run dev
```

---

## 7. Testing & Verification

We have automated test suites to confirm that all services, databases, and APIs are healthy:

### 1. Test All API Endpoints
```powershell
python test_apis.py
```
Validates Simulator API (8000), Bank Risk API (8001), and Coordinator API (8002).

### 2. Validate Live Simulator Engine & Multi-Bank Routing
```powershell
cd backend
python scripts/validate_live_simulator.py
```
Tests:
- All 9 bank-to-bank permutations (SBI $\rightarrow$ SBI, SBI $\rightarrow$ AXIS, AXIS $\rightarrow$ IOB, etc.).
- Strict double-entry ledger balance conservation and non-negative balance checks.
- Dynamic 40+ metric behavioural recalculation.

### 3. Build Frontends for Production
```powershell
cd frontend
npm run build
cd ..\risk-dashboard
npm run build
cd ..\coordinator-dashboard
npm run build
```

---

## 8. Recent Upgrades in v2.0 (Transaction Simulator)

The **TRANSACTION SIMULATOR** dashboard was refactored with the following architectural enhancements:

1. **Explicit Separation from ML**:
   - The simulator ONLY handles bank connections, transaction generation, and displaying transaction lifecycles.
   - All XGBoost risk calculation, GNN detection, and NetworkX canvas graphs were removed from the simulator and reside exclusively in the ADSL / Coordinator dashboards.

2. **8-State Transaction Status Lifecycle**:
   - `PROCESSING`: Newly broadcast transaction awaiting validation.
   - `COMPLETED`: Approved and posted to bank ledgers.
   - `MONITORING`: Medium-risk or unusual behavior under passive observation.
   - `HONEYPOT`: Diverted into a decoy environment for observation.
   - `LIEN_APPLIED`: Transaction amount held / protected in bank ledger.
   - `RELEASED`: Cleared after observation and allowed to proceed.
   - `RESTRICTED`: Confirmed suspicious flow restricted from withdrawal.
   - `FROZEN`: Account or transaction permanently locked under fraud confirmation.

3. **Separate Honeypot & Lien Status Columns**:
   - **Honeypot Status**: `NOT_TRANSFERRED`, `TRANSFERRED`, `ACTIVE`, `RELEASED`.
   - **Lien Status**: `NO_LIEN`, `LIEN_APPLIED`, `LIEN_RELEASED`.

4. **Realistic Generation Mix Modes**:
   - `BALANCED MIX` *(Default)*: Natural mixture of genuine, business, and fraud patterns.
   - `NORMAL MIX`: High-frequency personal transfers (UPI, IMPS, utilities).
   - `BUSINESS MIX`: High-value B2B vendor payments, payroll, merchant settlements.
   - `MULE MIX`: Concentrated fraud topologies (Fan-In, Fan-Out, Rapid Forwarding, Circular).

5. **Clean Banking Transaction Table**:
   - Replaced congested cards with an enterprise-grade table:
     `Time | Sender | Sender Bank | Receiver | Receiver Bank | Amount | Type | Device | Location | Status | Honeypot | Lien`
   - Real-time search, Bank filter, Status filter, Type filter, Column sorting, and Pagination.
   - Expandable rows for deep technical transaction details.

6. **Account Registry & Explorer Drawer**:
   - Selecting any account shows:
     - **Basic Info**: Account ID, Holder Name, Bank, Account Category (Personal vs Business), Current Balance, Status.
     - **Business Metadata**: Business Category, Expected Transaction Range, Frequency Pattern.
     - **Transaction Summary**: Total Sent, Total Received, Transaction Count.
     - Zero ML risk scores or graph clutter.

---

## 9. Guide for Antigravity AI Assistant

If you are using **Google Antigravity** to help you develop, debug, or extend this project, here are the essential patterns to follow:

### Antigravity Rules of Engagement:
1. **Multi-Bank Independence**: Never merge `sbi_db`, `axis_db`, and `iob_db` into a single database. Keep transactions and ledgers separate per bank.
2. **Direct SQL / No ORM**: Do NOT introduce SQLAlchemy or Django ORM. The platform relies on direct SQL queries and connection pools via `psycopg2` in `backend/database/db_connection.py`.
3. **Transaction Simulator Scope**:
   - Keep `frontend/src/` strictly as a simulation & monitoring interface.
   - Do NOT add XGBoost scoring, GNN predictions, or NetworkX graphs into `frontend/src/`.
   - Machine learning features belong in `backend/risk_engine/`, `backend/gnn_detection/`, `risk-dashboard/`, or `coordinator-dashboard/`.
4. **Windows PowerShell Commands**:
   - When running PowerShell scripts or commands, remember that quotes must be formatted properly and non-interactive flags should be used.
   - When launching long-running servers, use `IsDaemon: true` or background tasks.
5. **Key Configuration Files**:
   - Database credentials: `backend/.env`
   - Simulator configuration: `backend/simulator/config.py`
   - Simulator engine: `backend/simulator/engine.py`
   - Simulator REST routes: `backend/main.py`
   - Frontend API client: `frontend/src/api/simulatorApi.js`

---

## 10. Repository Directory Structure

```
FinalYr/
│
├── start_all.bat                   # 1-Click launcher (Windows CMD)
├── start_all.ps1                   # 1-Click launcher (PowerShell)
├── test_apis.py                    # Automated test suite for all 3 backend APIs
├── README.md                       # Markdown Project Documentation (This file)
├── README.txt                      # Plain-text Project Guide
│
├── backend/                        # Python FastAPI Services & ML Engines
│   ├── main.py                     # Simulator API & Ledger Server (Port 8000)
│   ├── risk_api.py                 # Bank Risk API (Port 8001)
│   ├── coordinator_api.py          # Decentralized Coordinator API (Port 8002)
│   ├── requirements.txt            # Python dependencies
│   ├── .env                        # Database connection credentials
│   │
│   ├── database/                   # Database scripts & connection pooling
│   │   ├── db_connection.py        # psycopg2 connection pool (SBI, AXIS, IOB)
│   │   ├── schema.sql              # Database schema definition
│   │   ├── create_databases.py     # Creates sbi_db, axis_db, iob_db
│   │   ├── populate_databases.py   # Seeds accounts & initial transactions
│   │   └── migrate_and_validate.py # Schema migrations & health validator
│   │
│   ├── simulator/                  # Simulation Engine
│   │   ├── config.py               # Speed, mix modes, status enums
│   │   ├── engine.py               # Core live loop & lifecycle dispatcher
│   │   ├── normal_transaction_generator.py # Normal & Business txn generator
│   │   └── scenario_runner.py      # Mule pattern generator
│   │
│   ├── risk_engine/                # XGBoost Risk Scoring & Feature Extraction
│   ├── gnn_detection/              # PyTorch Geometric GNN Mule Ring Detection
│   └── scripts/                    # CLI tools & test scripts
│
├── frontend/                       # Module 1: TRANSACTION SIMULATOR Dashboard (Port 5173)
│   ├── src/
│   │   ├── App.jsx                 # Main layout (Header -> Banks -> Controls -> Summary -> Table)
│   │   ├── components/
│   │   │   ├── Header.jsx          # Title, sim clock, active bank ledger selector
│   │   │   ├── BankConnectionSection.jsx # SBI, AXIS, IOB live DB status
│   │   │   ├── SimulationControls.jsx    # Start/Pause/Stop, Speed, Mix Selector
│   │   │   ├── SummaryCards.jsx          # KPI summary cards & lien amounts
│   │   │   ├── LiveTransactionTable.jsx  # Banking table with search & filters
│   │   │   ├── AccountDrawer.jsx         # Clean account inspector drawer
│   │   │   └── BankAnalyticsView.jsx     # Account Explorer directory
│   │   └── api/
│   │       └── simulatorApi.js     # REST client for Simulator API
│   └── package.json
│
├── risk-dashboard/                 # Module 2: Bank-Level Risk Dashboard (Port 5174)
│   └── package.json
│
└── coordinator-dashboard/          # Module 3: Decentralized Coordinator Dashboard (Port 5175)
    └── package.json
```

---

## 11. Troubleshooting & FAQs

### Q1: `psycopg2.OperationalError: could not connect to server: Connection refused`
- Ensure PostgreSQL service is started:
  ```powershell
  Get-Service -Name postgresql* | Start-Service
  ```
- Check credentials in `backend/.env` matches your local PostgreSQL superuser password.

### Q2: Port Conflict (e.g. `Address already in use: 8000` or `5173`)
- Find and terminate the hanging process:
  ```powershell
  # Find PID for port 8000
  netstat -ano | findstr :8000
  # Stop the process
  taskkill /F /PID <PID>
  ```

### Q3: `npm run dev` fails with module missing
- Run clean installation:
  ```powershell
  npm cache clean --force
  npm install
  ```

---

**Built for Next-Generation Digital Banking & Distributed Financial Security.**
