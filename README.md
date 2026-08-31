# MoneyBeing - Loan Eligibility & Lead Management System

MoneyBeing is a production-grade, enterprise financial platform that automates loan eligibility evaluation, real-time credit score retrieval, dynamic Business Rule Engine (BRE) execution, and admin lead lifecycle management.

---

## 📑 Table of Contents
1. [Project Overview](#-project-overview)
2. [Architecture](#-architecture)
3. [Tech Stack](#-tech-stack)
4. [Prerequisites](#-prerequisites)
5. [Database Setup & Migrations](#-database-setup--migrations)
6. [Environment Variables](#-environment-variables)
7. [Backend Setup (FastAPI)](#-backend-setup-fastapi)
8. [Frontend Setup (Next.js)](#-frontend-setup-nextjs)
9. [How to Run with Docker (Recommended)](#-how-to-run-with-docker-recommended)
10. [API Documentation](#-api-documentation)
11. [Business Rule Engine (BRE) Workflow](#-business-rule-engine-bre-workflow)
12. [Credit Score API Integration](#-credit-score-api-integration)
13. [Test Credentials & Demo Test Cases](#-test-credentials--demo-test-cases)
14. [Testing & Quality Assurance](#-testing--quality-assurance)

---

## 🌟 Project Overview

The **MoneyBeing** platform enables prospective borrowers to apply for loans (Home Loans, Loan Against Property) through an intuitive 5-step application funnel. The backend evaluates each lead in real-time through:
- **Instant CIBIL / Mock Credit Scoring**: Dynamically retrieves applicant credit rating.
- **Dynamic Business Rule Engine (BRE)**: Database-driven rules evaluated in strict priority order (Age limits, Minimum Net Income, Credit Score thresholds, Loan-to-Value ratios).
- **Executive Admin Portal**: Real-time KPI dashboard, multi-dimensional lead filtering, audit logs, dynamic BRE rule configuration with live toggle and add-field capabilities, and Excel export.

---

## 🏛 Architecture

MoneyBeing follows a **Clean Layered Architecture** with strict separation of concerns:

```text
                                  ┌─────────────────────────┐
                                  │   Next.js 14 Frontend   │
                                  │   (Tailwind, Lucide UI) │
                                  └────────────┬────────────┘
                                               │ HTTP / REST
                                  ┌────────────▼────────────┐
                                  │    FastAPI API Routers  │
                                  │   (/api/v1/auth, leads) │
                                  └────────────┬────────────┘
                                               │
                                  ┌────────────▼────────────┐
                                  │      Service Layer      │
                                  │ (Auth, Lead, BRE, Score)│
                                  └──────┬───────────┬──────┘
                                         │           │
                ┌────────────────────────┴──┐     ┌──┴────────────────────────┐
                │   Business Rule Engine    │     │ Credit Score Integration  │
                │  (Operators, Evaluators)  │     │ (Mock / TransUnion CIBIL) │
                └────────────┬──────────────┘     └───────────────────────────┘
                             │
                ┌────────────▼──────────────┐
                │     Repository Layer      │
                │ (SQLAlchemy ORM + Indices)│
                └────────────┬──────────────┘
                             │
                ┌────────────▼──────────────┐
                │   PostgreSQL / SQLite     │
                │   (Relational Database)   │
                └───────────────────────────┘
```

### Key Architectural Layers:
1. **API Layer (`api/v1/`)**: Thin controllers handling request validation (Pydantic v2), route guards (JWT RBAC), rate limiting, and standard response envelopes.
2. **Service Layer (`services/`)**: Orchestrates business logic (`LeadService`, `BREService`, `BRERuleService`, `AuthService`, `DashboardService`, `CreditScoreService`).
3. **Engine Layer (`engine/`)**: In-memory rule evaluator executing registered operators (`>=`, `<=`, `>`, `<`, `==`, `!=`) against applicant context.
4. **Integration Layer (`integrations/credit_score/`)**: Adapter design pattern providing pluggable credit bureau providers (`CibilCreditScoreProvider` vs `MockCreditScoreProvider`).
5. **Repository Layer (`repositories/`)**: Database access abstractions with optimized pagination, indexing, and audit logging.

---

## 💻 Tech Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.13) | Asynchronous, high-performance REST API |
| **ORM & Database** | SQLAlchemy 2.0 & PostgreSQL 15 | Relational storage with dual SQLite fallback |
| **Database Migrations** | Alembic | Version-controlled database schema migrations |
| **Caching Engine** | Redis 7 | In-memory caching for dashboard and token blacklisting |
| **Data Validation** | Pydantic v2 | Strict schema validation, custom field validators |
| **Authentication** | JWT (PyJWT + Passlib Bcrypt) | Stateless Bearer token authentication & RBAC |
| **Frontend Framework** | Next.js 14 (App Router) | React 18, Server/Client components, SSR |
| **Styling** | Tailwind CSS + Lucide Icons | Responsive modern design system |
| **Containerization** | Docker & Docker Compose | Multi-container automated orchestration |
| **Testing** | Pytest + AnyIO + TestClient | 138 automated unit & integration tests |

---

## 📋 Prerequisites

Ensure you have the following installed on your machine:
- **Python**: `3.11+` (Recommended: Python 3.12 or 3.13)
- **Node.js**: `v18.0+` or `v20.0+` & **npm**: `v9.0+`
- **Docker & Docker Desktop**: (Optional, for containerized execution)
- **Git**: For source version control

---

## 🗄 Database Setup & Migrations

MoneyBeing supports both **PostgreSQL** (Production & Docker) and **SQLite** (Zero-setup local development).

### 1. Automatic Table Creation & Seeding
On server startup, FastAPI automatically:
- Checks and initializes all database tables (`leads`, `bre_rules`, `users`, `lead_bre_results`, `audit_logs`).
- Seeds default Admin credentials (`admin` / `AdminPassword123`).
- Seeds the 5 core default BRE evaluation rules.

### 2. Manual Alembic Migrations (PostgreSQL)
To run or generate Alembic migrations:
```powershell
# Run all pending migrations
alembic upgrade head

# Generate a new migration revision
alembic revision --autogenerate -m "add_new_columns"
```

---

## ⚙️ Environment Variables

### Backend Configuration (`.env`)
Create a `.env` file in the `moneybeing-loan-eligibility-backend` directory:

```env
# Application Settings
APP_NAME="MoneyBeing Loan Eligibility API"
APP_ENV="development"
DEBUG=True
API_V1_STR="/api/v1"

# Server
HOST="0.0.0.0"
PORT=8000
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://localhost:3001"]

# JWT Authentication
JWT_SECRET_KEY="moneybeing-production-super-secret-key-32-chars-minimum"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (Use PostgreSQL in Docker or SQLite for local zero-config)
DATABASE_URL="sqlite:///./moneybeing.db"
# DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/moneybeing_db"

# Redis Cache
REDIS_URL="redis://localhost:6379/0"
REDIS_ENABLED=False
REDIS_CACHE_TTL_SECONDS=300

# Credit Score Provider ("mock" or "cibil")
CREDIT_SCORE_PROVIDER="mock"
MOCK_CREDIT_SCORE=742
CIBIL_API_URL="https://api.cibil.com/v1/score"
CIBIL_API_KEY=""
CIBIL_CLIENT_ID=""
CIBIL_CLIENT_SECRET=""
CIBIL_TIMEOUT_SECONDS=10.0
```

### Frontend Configuration (`.env.local`)
Create a `.env.local` file in the `moneybeing-loan-eligibility-frontend` directory:

```env
NEXT_PUBLIC_API_BASE_URL="http://localhost:8000/api/v1"
```

---

## 🚀 Backend Setup (FastAPI)

#### 1. Navigate to backend directory:
```powershell
cd d:\moneybeing-loan-eligibility-backend
```

#### 2. Create and activate Python Virtual Environment:
```powershell
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

#### 3. Install dependencies:
```powershell
pip install -r requirements.txt
```

#### 4. Run database seed (Optional - auto-seeds on startup):
```powershell
python -m database.seed
```

#### 5. Start the Backend API server:
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend will be available at: **`http://127.0.0.1:8000`**

---

## 🎨 Frontend Setup (Next.js)

#### 1. Open a new terminal and navigate to frontend directory:
```powershell
cd d:\moneybeing-loan-eligibility-frontend
```

#### 2. Install NPM packages:
```powershell
npm install
```

#### 3. Start the Next.js development server:
```powershell
npm run dev
```
Frontend Web Portal will be available at: **`http://localhost:3000`**

---

## 🐳 How to Run with Docker (Recommended)

To run the entire platform (PostgreSQL, Redis, FastAPI Backend, Next.js Frontend) in one command:

```powershell
# Navigate to backend directory
cd d:\moneybeing-loan-eligibility-backend

# Start all containers in background
docker compose up -d --build
```

### Container Status:
```powershell
docker ps
```

| Service | Container Name | Mapped Port |
| :--- | :--- | :--- |
| **Frontend App** | `moneybeing-frontend` | `http://localhost:3000` |
| **Backend API** | `moneybeing-backend` | `http://localhost:8000` |
| **PostgreSQL DB** | `moneybeing-postgres` | `localhost:5433` |
| **Redis Cache** | `moneybeing-redis` | `localhost:6380` |

To stop containers:
```powershell
docker compose down
```

---

## 📚 API Documentation

Once the backend is running, interactive API documentation is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Core Endpoints Summary:

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Public | System health check and uptime |
| `POST` | `/api/v1/auth/login` | Public | Authenticate Admin and receive JWT token |
| `GET` | `/api/v1/auth/me` | Admin | Get current logged-in admin profile |
| `POST` | `/api/v1/leads` | Public | Submit loan application & run real-time BRE |
| `GET` | `/api/v1/leads` | Admin | Paginated lead listing, search, multi-filter |
| `GET` | `/api/v1/leads/{id}` | Admin | View lead details with per-rule evaluation audit |
| `GET` | `/api/v1/dashboard/stats` | Admin | Aggregate KPI metrics (total, eligible, rejected) |
| `GET` | `/api/v1/dashboard/lead-distribution` | Admin | Breakdown by loan & employment types |
| `GET` | `/api/v1/bre-rules` | Admin | List all active/inactive BRE evaluation rules |
| `POST` | `/api/v1/bre-rules` | Admin | Create a new dynamic evaluation rule |
| `PUT` | `/api/v1/bre-rules/{id}` | Admin | Edit rule threshold or failure message |
| `PATCH` | `/api/v1/bre-rules/{id}/status` | Admin | Toggle rule active status (`is_active`) |
| `DELETE` | `/api/v1/bre-rules/{id}` | Admin | Soft-deactivate a rule |

---

## 🧠 Business Rule Engine (BRE) Workflow

The BRE engine dynamically evaluates applicant eligibility without hardcoding business thresholds:

```text
 [ Applicant Context ]
 (Age, Income, Credit Score, Loan Amount, Property Value, Loan Ratio)
                 │
                 ▼
  [ Fetch Active BRE Rules from DB ]  (Ordered by priority ASC)
                 │
                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ Rule Evaluator Pipeline:                                    │
  │  1. Rule #1: age >= 21             (Applicant Min Age)      │
  │  2. Rule #2: age <= 60             (Applicant Max Age)      │
  │  3. Rule #3: monthly_income >= 30000 (Min Monthly Income)   │
  │  4. Rule #4: credit_score >= 700   (Credit Bureau Score)    │
  │  5. Rule #5: loan_ratio <= 80      (Max LTV Ratio %)        │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
  [ All Rules Passed ]                        [ >= 1 Rule Failed ]
  Decision: "Eligible"                        Decision: "Not Eligible"
  Rejection Reasons: None                     Rejection Reasons: [Messages]
         │                                               │
         └───────────────────────┬───────────────────────┘
                                 ▼
   [ Atomic DB Transaction: Lead Record + LeadBREResult Per-Rule Audit ]
```

---

## 💳 Credit Score API Integration

The platform uses the **Adapter Design Pattern** to support multiple credit bureau providers:

### 1. Mock Provider (`MockCreditScoreProvider`)
- Generates deterministic, realistic credit scores between **`620` and `830`** based on applicant details.
- Supports built-in edge case testing:
  - Mobile ending in **`...7500`** ➔ Score **`750`** *(Guaranteed Approval)*
  - Mobile ending in **`...6500`** ➔ Score **`650`** *(Guaranteed Rejection)*
  - Mobile ending in **`...0000`** ➔ Simulates **Bureau Outage / Downtime**

### 2. Live CIBIL Provider (`CibilCreditScoreProvider`)
- Authenticates against TransUnion CIBIL REST API with client credentials.
- Handles HTTP timeouts (10s), network transient retries, and error handling.

---

## 🔑 Test Credentials & Demo Test Cases

### 1. Admin Login Credentials:
- **URL**: [http://localhost:3000/login](http://localhost:3000/login)
- **Username**: `admin`
- **Password**: `AdminPassword123`

### 2. Demo Applicant Test Profiles:

#### Scenario A: Approved / Eligible Applicant
- **Name**: `Vikash Kumar`
- **Mobile**: `9876547500` (or any mobile with age >= 21 and income >= 30,000)
- **DOB**: `1998-05-15` (Age 26)
- **Monthly Income**: `₹50,000`
- **Loan Amount**: `₹5,00,000`
- **Property Value**: `₹10,00,000`
- **Result**: ✅ **Eligible** (Credit Score: ~750, LTV: 50%)

#### Scenario B: Rejected (Low Income) Applicant
- **Name**: `Rahul Sharma`
- **Mobile**: `9876543210`
- **DOB**: `1995-10-20`
- **Monthly Income**: `₹20,000` *(Fails ₹30,000 rule)*
- **Loan Amount**: `₹5,00,000`
- **Property Value**: `₹10,00,000`
- **Result**: ❌ **Not Eligible** (Reason: *Monthly income must be at least ₹30,000*)

#### Scenario C: Rejected (Low Credit Score) Applicant
- **Name**: `Amit Verma`
- **Mobile**: `9876546500` *(Simulates 650 credit score)*
- **Monthly Income**: `₹45,000`
- **Result**: ❌ **Not Eligible** (Reason: *Credit score below minimum requirement of 700*)

---

## 🧪 Testing & Quality Assurance

### Run Backend Automated Tests:
```powershell
cd d:\moneybeing-loan-eligibility-backend
.\.venv\Scripts\pytest -v
```
**Results**: `138 passed` (100% test pass rate across admin, auth, BRE, credit score, database, health, and leads test suites).

### Run Frontend Type Check & Build Validation:
```powershell
cd d:\moneybeing-loan-eligibility-frontend
npm run build
```
**Results**: `10/10 routes compiled successfully` with 0 TypeScript errors.

---

## 📄 License
This project is proprietary and confidential. Developed for the MoneyBeing Loan Eligibility & Lead Management System.
