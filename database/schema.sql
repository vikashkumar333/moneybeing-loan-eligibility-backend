-- ==============================================================================
-- MoneyBeing Loan Eligibility & Lead Management System - Production Schema DDL
-- ==============================================================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Admin',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 2. LEADS TABLE
CREATE TABLE IF NOT EXISTS leads (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    mobile VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100) NULL,
    date_of_birth DATE NOT NULL,
    city VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    loan_type VARCHAR(30) NOT NULL,
    employment_type VARCHAR(30) NOT NULL,
    monthly_income NUMERIC(15, 2) NOT NULL,
    loan_amount NUMERIC(15, 2) NOT NULL,
    property_value NUMERIC(15, 2) NOT NULL,
    credit_score INTEGER NULL,
    bre_status VARCHAR(30) NULL,
    rejection_reasons JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_lead_monthly_income_positive CHECK (monthly_income >= 0),
    CONSTRAINT chk_lead_loan_amount_positive CHECK (loan_amount > 0),
    CONSTRAINT chk_lead_property_value_positive CHECK (property_value > 0),
    CONSTRAINT chk_lead_credit_score_range CHECK (credit_score IS NULL OR (credit_score >= 300 AND credit_score <= 900)),
    CONSTRAINT chk_lead_loan_type CHECK (loan_type IN ('HOME_LOAN', 'LAP', 'Home Loan', 'Loan Against Property')),
    CONSTRAINT chk_lead_employment_type CHECK (employment_type IN ('SALARIED', 'SELF_EMPLOYED', 'Salaried', 'Self Employed')),
    CONSTRAINT chk_lead_bre_status CHECK (bre_status IS NULL OR bre_status IN ('ELIGIBLE', 'NOT_ELIGIBLE', 'PENDING', 'Eligible', 'Not Eligible', 'Pending'))
);

CREATE INDEX IF NOT EXISTS idx_leads_mobile ON leads(mobile);
CREATE INDEX IF NOT EXISTS idx_leads_full_name ON leads(full_name);
CREATE INDEX IF NOT EXISTS idx_leads_bre_status ON leads(bre_status);
CREATE INDEX IF NOT EXISTS idx_leads_loan_type ON leads(loan_type);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_credit_score ON leads(credit_score);
CREATE INDEX IF NOT EXISTS idx_lead_created_status ON leads(created_at, bre_status);

-- 3. BRE RULES TABLE
CREATE TABLE IF NOT EXISTS bre_rules (
    id BIGSERIAL PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    operator VARCHAR(10) NOT NULL,
    rule_value VARCHAR(100) NOT NULL,
    failure_message TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 1,
    created_by INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_bre_rule_priority_positive CHECK (priority > 0),
    CONSTRAINT chk_bre_rule_operator CHECK (operator IN ('>=', '<=', '>', '<', '==', '!='))
);

CREATE INDEX IF NOT EXISTS idx_bre_rules_is_active ON bre_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_bre_rules_priority ON bre_rules(priority);
CREATE INDEX IF NOT EXISTS idx_bre_rule_active_priority ON bre_rules(is_active, priority);

-- 4. LEAD BRE RESULTS TABLE
CREATE TABLE IF NOT EXISTS lead_bre_results (
    id BIGSERIAL PRIMARY KEY,
    lead_id BIGINT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    rule_id BIGINT NULL REFERENCES bre_rules(id) ON DELETE SET NULL,
    is_passed BOOLEAN NOT NULL,
    failure_message TEXT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lead_bre_lead_id ON lead_bre_results(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_bre_rule_id ON lead_bre_results(rule_id);
CREATE INDEX IF NOT EXISTS idx_lead_bre_lead_rule ON lead_bre_results(lead_id, rule_id);

-- 5. AUDIT LOGS TABLE
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id BIGINT NULL,
    old_value JSONB NULL,
    new_value JSONB NULL,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_created ON audit_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_action ON audit_logs(entity, action);
