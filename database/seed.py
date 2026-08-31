import os
import sys
import logging

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from models.user import User
from models.bre_rule import BRERule
from core.security import get_password_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("moneybeing.seed")


DEFAULT_BRE_RULES = [
    {
        "rule_name": "Minimum Age",
        "field_name": "age",
        "operator": ">=",
        "rule_value": "21",
        "failure_message": "Applicant age must be at least 21 years old",
        "priority": 1,
    },
    {
        "rule_name": "Maximum Age",
        "field_name": "age",
        "operator": "<=",
        "rule_value": "60",
        "failure_message": "Applicant age must not exceed 60 years old",
        "priority": 2,
    },
    {
        "rule_name": "Minimum Monthly Income",
        "field_name": "monthly_income",
        "operator": ">=",
        "rule_value": "30000",
        "failure_message": "Monthly income must be at least ₹30,000",
        "priority": 3,
    },
    {
        "rule_name": "Minimum Credit Score",
        "field_name": "credit_score",
        "operator": ">=",
        "rule_value": "700",
        "failure_message": "Credit score below minimum requirement of 700",
        "priority": 4,
    },
    {
        "rule_name": "Loan to Property Value Ratio",
        "field_name": "loan_ratio",
        "operator": "<=",
        "rule_value": "80",
        "failure_message": "Loan amount cannot exceed 80% of the property value",
        "priority": 5,
    },
]


def seed_database(db: Session) -> None:
    logger.info("Seeding initial database records...")

    # 1. Seed Admin User
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        logger.info("Creating default admin user: 'admin'")
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("AdminPassword123"),
            role="Admin",
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info(f"Admin user created with ID: {admin_user.id}")
    else:
        logger.info(f"Admin user already exists with ID: {admin_user.id}")

    # 2. Seed Default BRE Rules
    for rule_data in DEFAULT_BRE_RULES:
        existing_rule = db.query(BRERule).filter(BRERule.rule_name == rule_data["rule_name"]).first()
        if not existing_rule:
            logger.info(f"Creating BRE Rule: {rule_data['rule_name']}")
            rule = BRERule(
                rule_name=rule_data["rule_name"],
                field_name=rule_data["field_name"],
                operator=rule_data["operator"],
                rule_value=rule_data["rule_value"],
                failure_message=rule_data["failure_message"],
                priority=rule_data["priority"],
                is_active=True,
                created_by=admin_user.id,
            )
            db.add(rule)
        else:
            logger.info(f"BRE Rule '{rule_data['rule_name']}' already exists.")

    db.commit()
    logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
