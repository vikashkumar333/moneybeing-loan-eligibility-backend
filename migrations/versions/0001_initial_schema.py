"""Initial database schema with users, leads, bre_rules, lead_bre_results, and audit_logs

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-30 01:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='Admin'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 2. leads table
    op.create_table(
        'leads',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('mobile', sa.String(length=15), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('pincode', sa.String(length=10), nullable=False),
        sa.Column('loan_type', sa.String(length=30), nullable=False),
        sa.Column('employment_type', sa.String(length=30), nullable=False),
        sa.Column('monthly_income', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('loan_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('property_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('credit_score', sa.Integer(), nullable=True),
        sa.Column('bre_status', sa.String(length=30), nullable=True),
        sa.Column('rejection_reasons', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('monthly_income >= 0', name='chk_lead_monthly_income_positive'),
        sa.CheckConstraint('loan_amount > 0', name='chk_lead_loan_amount_positive'),
        sa.CheckConstraint('property_value > 0', name='chk_lead_property_value_positive'),
        sa.CheckConstraint('(credit_score IS NULL) OR (credit_score >= 300 AND credit_score <= 900)', name='chk_lead_credit_score_range'),
        sa.CheckConstraint("loan_type IN ('HOME_LOAN', 'LAP', 'Home Loan', 'Loan Against Property')", name='chk_lead_loan_type'),
        sa.CheckConstraint("employment_type IN ('SALARIED', 'SELF_EMPLOYED', 'Salaried', 'Self Employed')", name='chk_lead_employment_type'),
        sa.CheckConstraint("bre_status IS NULL OR bre_status IN ('ELIGIBLE', 'NOT_ELIGIBLE', 'PENDING', 'Eligible', 'Not Eligible', 'Pending')", name='chk_lead_bre_status'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mobile')
    )
    op.create_index(op.f('ix_leads_id'), 'leads', ['id'], unique=False)
    op.create_index(op.f('ix_leads_mobile'), 'leads', ['mobile'], unique=True)
    op.create_index(op.f('ix_leads_full_name'), 'leads', ['full_name'], unique=False)
    op.create_index(op.f('ix_leads_loan_type'), 'leads', ['loan_type'], unique=False)
    op.create_index(op.f('ix_leads_bre_status'), 'leads', ['bre_status'], unique=False)
    op.create_index(op.f('ix_leads_credit_score'), 'leads', ['credit_score'], unique=False)
    op.create_index(op.f('ix_leads_created_at'), 'leads', ['created_at'], unique=False)
    op.create_index('idx_lead_created_status', 'leads', ['created_at', 'bre_status'], unique=False)

    # 3. bre_rules table
    op.create_table(
        'bre_rules',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('field_name', sa.String(length=50), nullable=False),
        sa.Column('operator', sa.String(length=10), nullable=False),
        sa.Column('rule_value', sa.String(length=100), nullable=False),
        sa.Column('failure_message', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('priority > 0', name='chk_bre_rule_priority_positive'),
        sa.CheckConstraint("operator IN ('>=', '<=', '>', '<', '==', '!=')", name='chk_bre_rule_operator'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bre_rules_id'), 'bre_rules', ['id'], unique=False)
    op.create_index(op.f('ix_bre_rules_is_active'), 'bre_rules', ['is_active'], unique=False)
    op.create_index(op.f('ix_bre_rules_priority'), 'bre_rules', ['priority'], unique=False)
    op.create_index('idx_bre_rule_active_priority', 'bre_rules', ['is_active', 'priority'], unique=False)

    # 4. lead_bre_results table
    op.create_table(
        'lead_bre_results',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('lead_id', sa.BigInteger(), nullable=False),
        sa.Column('rule_id', sa.BigInteger(), nullable=True),
        sa.Column('is_passed', sa.Boolean(), nullable=False),
        sa.Column('failure_message', sa.Text(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['bre_rules.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lead_bre_results_id'), 'lead_bre_results', ['id'], unique=False)
    op.create_index(op.f('ix_lead_bre_results_lead_id'), 'lead_bre_results', ['lead_id'], unique=False)
    op.create_index(op.f('ix_lead_bre_results_rule_id'), 'lead_bre_results', ['rule_id'], unique=False)
    op.create_index('idx_lead_bre_lead_rule', 'lead_bre_results', ['lead_id', 'rule_id'], unique=False)

    # 5. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.BigInteger(), nullable=True),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity'), 'audit_logs', ['entity'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index('idx_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_audit_logs_entity_action', 'audit_logs', ['entity', 'action'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('lead_bre_results')
    op.drop_table('bre_rules')
    op.drop_table('leads')
    op.drop_table('users')
