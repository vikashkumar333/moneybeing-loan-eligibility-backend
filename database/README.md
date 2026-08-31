# Database Management & Migrations

## Prerequisites
- PostgreSQL 16+ or Docker Compose.
- Python virtual environment activated (`.venv`).

---

## 1. Environment Configuration
Ensure `.env` contains your PostgreSQL connection parameters:

```env
DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/moneybeing_db"
```

---

## 2. Running Alembic Migrations

To apply all migrations to the latest version:
```bash
alembic upgrade head
```

To create a new migration:
```bash
alembic revision --autogenerate -m "describe_migration"
```

To rollback the last migration:
```bash
alembic downgrade -1
```

---

## 3. Database Seeding

To seed the default admin account (`admin` / `Admin@123`) and the 5 default dynamic BRE rules:
```bash
python database/seed.py
```

---

## 4. Resetting the Database
To wipe and re-initialize the database cleanly:
```bash
# In PostgreSQL terminal or pgAdmin:
DROP DATABASE IF EXISTS moneybeing_db;
CREATE DATABASE moneybeing_db;

# Run migrations and seed:
alembic upgrade head
python database/seed.py
```
