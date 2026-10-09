# CMRS — Django REST Backend

Backend for the Cash Management & Reconciliation System (CMRS) assessment.

## Architecture

- Django
- Django REST Framework
- PostgreSQL
- JWT authentication
- Role-based access control
- Decimal fields for all monetary values
- OpenAPI / Swagger documentation

The backend models the assessment lifecycle:

Customer → Collection Agent → Branch → Bank Deposit → Company Account

## Main modules

- Authentication / users / roles
- Customers
- Loans
- Repayment schedules
- Repayments / receipts
- Agent cash submissions
- Branch reconciliation
- Bank deposits
- Settlement tracking
- Dashboard summary
- Exception visibility

## Roles

- ADMIN
- BRANCH_MANAGER
- COLLECTION_AGENT
- BRANCH_OPERATOR

Permissions are enforced at the API layer.

## Setup

### 1. Create PostgreSQL database

Using psql:

```sql
CREATE DATABASE cmrs_db;
```

### 2. Create virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy:

```text
.env.example -> .env
```

Then set your PostgreSQL password and database settings.

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create admin

```bash
python manage.py createsuperuser
```

### 7. Run server

```bash
python manage.py runserver
```

API:

```text
http://127.0.0.1:8000/api/
```

Admin:

```text
http://127.0.0.1:8000/admin/
```

Swagger:

```text
http://127.0.0.1:8000/api/docs/
```

## JWT authentication

POST:

```text
/api/auth/token/
```

Body:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Refresh:

```text
/api/auth/token/refresh/
```

Send the access token on protected endpoints:

```text
Authorization: Bearer <access_token>
```

## Important business rules implemented

1. Financial values use DecimalField rather than floating point.
2. A repayment automatically receives a unique receipt/reference number.
3. Partial repayments are supported.
4. Over-collection is detected.
5. Duplicate-looking repayments are blocked when the same customer, loan, date and amount are repeated.
6. Agent cash submissions compare expected and received amounts.
7. Reconciliation calculates discrepancy.
8. Approved reconciliation records are locked against normal modification.
9. Bank deposits are only created from reconciled cash.
10. Bank reference numbers are unique.
11. Settlement can expose a mismatch between deposited and settled amounts.
12. Rejected submissions cannot be deposited.
13. Audit events are recorded for important state changes.

## Seed demo data

```bash
python manage.py seed_demo
```

This creates:

- Demo branch
- Admin
- Branch manager
- Collection agents
- Customers
- Loans
- Repayment schedules
- Repayments
- Agent submissions
- Reconciliation records
- Bank deposits

Demo credentials are printed by the command.

## API endpoints

### Authentication

```text
POST /api/auth/token/
POST /api/auth/token/refresh/
```

### Health check

```text
GET /api/health/
```

### Dashboard

```text
GET /api/dashboard/summary/
```

### Customers

```text
GET    /api/customers/
POST   /api/customers/
GET    /api/customers/{id}/
PATCH  /api/customers/{id}/
```

### Loans

```text
GET    /api/loans/
POST   /api/loans/
GET    /api/loans/{id}/
PATCH  /api/loans/{id}/
```

### Repayment schedules

```text
GET /api/schedules/
POST /api/schedules/
```

### Repayments

```text
GET  /api/repayments/
POST /api/repayments/
GET  /api/repayments/{id}/
```

### Agent cash submissions

```text
GET  /api/submissions/
POST /api/submissions/
POST /api/submissions/{id}/approve/
POST /api/submissions/{id}/reject/
```

### Reconciliation

```text
GET /api/reconciliation/
GET /api/reconciliation/{id}/
POST /api/reconciliation/{id}/approve/
POST /api/reconciliation/{id}/reject/
```

### Bank deposits

```text
GET  /api/deposits/
POST /api/deposits/
GET  /api/deposits/{id}/
```

### Settlements

```text
GET  /api/settlements/
POST /api/settlements/
POST /api/settlements/{id}/mark-settled/
```

## Filtering

Several list endpoints support query parameters such as:

```text
?branch=1
?agent=2
?status=PENDING
?customer=5
?date=2026-10-08
```

The React frontend can later call these APIs with Axios/fetch.

## Production notes

Before deployment:

- Set DEBUG=False.
- Use a strong SECRET_KEY.
- Restrict ALLOWED_HOSTS.
- Restrict CORS_ALLOWED_ORIGINS.
- Use HTTPS.
- Store secrets in environment variables.
- Run `python manage.py check --deploy`.
- Configure PostgreSQL backups.
- Add production logging and monitoring.


## Collection assignment workflow
- Managers assign each customer to a collection agent from Customer Management.
- Agents see unpaid installments for their assigned customers in Collections.
- Record Payment from a task automatically uses its customer, loan, schedule, and remaining installment amount.
- Agents can record an unsuccessful collection attempt with a reason.
- Run `python manage.py migrate` after updating the backend.
