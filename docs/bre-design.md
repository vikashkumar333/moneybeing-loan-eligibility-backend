# Business Rule Engine (BRE) Design Specification

## Overview
The **MoneyBeing Business Rule Engine (BRE)** is a flexible, database-driven decision engine designed to evaluate loan applicants against configurable credit, demographic, and financial thresholds dynamically loaded from PostgreSQL.

---

## 1. Architectural Separation

```
API Request (Lead / Test Endpoint)
        ↓
    BREService
        ↓
    BREEngine (Pure In-Memory Evaluator)
    ├── OperatorRegistry (>=, <=, >, <, ==, !=)
    └── RuleEvaluator (Context Field Resolution & Type Normalization)
        ↓
BRERuleRepository (PostgreSQL bre_rules)
        ↓
Audit Persistence (lead_bre_results)
```

- **Database-Driven**: Rules reside in the `bre_rules` table. Adding, modifying, or disabling a rule takes effect immediately without code deployment or server restarts.
- **Pure Evaluation**: The core `BREEngine` and `RuleEvaluator` are stateless and decoupled from database operations for 100% testability.
- **Deterministic & Auditable**: Rules execute in order of `priority ASC, id ASC`. Every evaluation creates distinct records in `lead_bre_results` preserving a transparent historical audit trail.

---

## 2. Supported Operators
Operated strictly via Python's built-in `operator` module without `eval()` or `exec()`:
- `>=` (Greater than or equal)
- `<=` (Less than or equal)
- `>` (Greater than)
- `<` (Less than)
- `==` (Equal to)
- `!=` (Not equal to)

---

## 3. Supported Context Fields & Derivations
- **`age`**: Calculated dynamically from `date_of_birth` taking into account the exact day/month of birth against current UTC date.
- **`monthly_income`**: Exact `Decimal` monthly earnings.
- **`credit_score`**: Retrieved credit bureau integer (300-900).
- **`loan_amount`**: Requested capital amount in `Decimal`.
- **`property_value`**: Collateral property valuation in `Decimal`.
- **`loan_ratio`**: Calculated ratio `(loan_amount / property_value) * 100`. Gracefully handles `property_value <= 0`.
- **`employment_type`** & **`loan_type`**: Categorical classifications.

---

## 4. Default Seeded Rules

| Rule Name | Field | Operator | Value | Priority | Failure Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Minimum Age** | `age` | `>=` | `21` | 1 | Applicant age must be at least 21 years old |
| **Maximum Age** | `age` | `<=` | `60` | 2 | Applicant age must not exceed 60 years old |
| **Minimum Monthly Income** | `monthly_income` | `>=` | `30000` | 3 | Monthly income must be at least ₹30,000 |
| **Minimum Credit Score** | `credit_score` | `>=` | `700` | 4 | Credit score below minimum requirement of 700 |
| **Loan to Property Value Ratio** | `loan_ratio` | `<=` | `80` | 5 | Loan amount cannot exceed 80% of the property value |

---

## 5. Evaluation Decision Flow
1. Load all active rules (`is_active = True`) ordered by `priority ASC, id ASC`.
2. Evaluate **every** rule against applicant context (no early stopping) to provide complete, comprehensive feedback.
3. If all rules pass: `status = "Eligible"`, `rejection_reasons = []`.
4. If one or more rules fail: `status = "Not Eligible"`, `rejection_reasons = [rule.failure_message, ...]`.
