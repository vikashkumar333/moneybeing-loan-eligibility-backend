# MoneyBeing Loan Eligibility & Lead Management System

## Overview
MoneyBeing is a production-grade Loan Eligibility & Lead Management System built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Pydantic**, and **Redis**.

---

## Architecture & Layers
1. **API Routers (`api/v1/`)**: Thin HTTP entry points with validation, rate-limiting, and RBAC (`Admin` / `Viewer`).
2. **Service Layer (`services/`)**: Centralized business logic (`AuthService`, `LeadService`, `CreditScoreService`, `BREService`, `DashboardService`, `BRERuleService`).
3. **Engine Layer (`engine/`)**: In-memory rule evaluator with operator registry (`>=`, `<=`, `>`, `<`, `==`, `!=`) and applicant context derivation.
4. **Integration Layer (`integrations/credit_score/`)**: Provider-agnostic credit bureau adapter (`CibilCreditScoreProvider`, `MockCreditScoreProvider`).
5. **Repository Layer (`repositories/`)**: Database access layer with PostgreSQL pooling and optimized indexing.

---

## Lead Management APIs (Admin Protected)
- `GET /api/v1/leads`: Paginated lead list with multi-column search (`full_name`, `mobile`, `email`), filtering (`loan_type`, `employment_type`, `bre_status`, `city`, `date_from`, `date_to`), and whitelisted sorting.
- `GET /api/v1/leads/{id}`: Detailed view of a lead, including full customer profile and complete BRE rule evaluation audit records.

---

## Dashboard APIs (Admin Protected)
- `GET /api/v1/dashboard/stats`: Aggregated metrics using PostgreSQL SQL `COUNT`, `SUM`, and `AVG` (`total_leads`, `eligible_leads`, `rejected_leads`, `average_credit_score`).
- `GET /api/v1/dashboard/lead-distribution`: Segmented breakdown by loan type, employment type, and eligibility status.

---

## Dynamic BRE Rule Management (Admin Protected)
- `GET /api/v1/bre-rules`: List all configured rules in evaluation order (`priority ASC, id ASC`).
- `POST /api/v1/bre-rules`: Create new business rule with strict field & operator validation.
- `PUT /api/v1/bre-rules/{id}`: Modify rule threshold or failure message with automatic audit logging.
- `DELETE /api/v1/bre-rules/{id}`: Soft-delete/deactivate rule without destroying audit history.
- `PATCH /api/v1/bre-rules/{id}/status`: Toggle active status.

---

## Credit Score Integration
- `CREDIT_SCORE_PROVIDER=mock`: Deterministic local development and test mode.
- `CREDIT_SCORE_PROVIDER=cibil`: Production/Sandbox adapter with HTTP timeouts and transient retry policies.
