# SubLedger

Subscription billing backend built with Django REST Framework. Each business domain is an independent Django app, with database access in repositories and orchestration/business rules in services.

## Low-Level Design

| App | Model | Responsibility |
| --- | --- | --- |
| `plans` | `Plan` | Price, currency, billing cycle, and availability |
| `customers` | `Customer` | Customer profile and unique email |
| `subscriptions` | `Subscription` | Customer-plan lifecycle and billing period |
| `invoices` | `Invoice` | Period charges, due dates, and payment state |
| `payments` | `PaymentAttempt` | Successful and failed payment records |
| `ledger` | `LedgerEntry` | Append-only charge and payment history |

Request flow: URL router -> DRF viewset -> schema validation -> service -> repository -> Django model/database. Services coordinate transactions across domains; repositories own ORM query/write operations. Models and database constraints protect core invariants even when a service is bypassed.

Invoice generation and successful payment recording are atomic. An invoice generation creates its charge ledger entry in the same transaction. A successful payment updates invoice balance, records the attempt, and appends a payment ledger entry atomically; failed attempts do not change balances. Ledger APIs are read-only, and model/queryset operations reject updates and deletes.

## API

All endpoints are under `/api/`:

| Resource | Endpoints |
| --- | --- |
| Plans | `GET/POST /plans/`, `GET/PUT/PATCH/DELETE /plans/{id}/` |
| Customers | `GET/POST /customers/`, `GET/PUT/PATCH/DELETE /customers/{id}/` |
| Subscriptions | `GET/POST /subscriptions/`, `GET /subscriptions/{id}/`, `POST /subscriptions/{id}/cancel/` |
| Invoices | `GET /invoices/`, `GET /invoices/{id}/`, `POST /invoices/generate/` |
| Payments | `GET /payments/`, `GET /payments/{id}/`, `POST /payments/` |
| Ledger | `GET /ledger/`, `GET /ledger/{id}/` |

Interactive API documentation: `/api/docs/`. OpenAPI schema: `/api/schema/`.

## Local Development

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The default local database is SQLite. To start PostgreSQL in Docker and run Django locally:

```sh
docker compose up -d
export DB_HOST=localhost
export DB_PORT=5432
python manage.py migrate
python manage.py runserver
```

The API is available at `http://localhost:8000/api/` and docs at `http://localhost:8000/api/docs/`. Set `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in the environment before starting the container to override their `subledger` defaults.
Run the API and business-rule tests for all apps with `python manage.py test customers.tests plans.tests subscriptions.tests invoices.tests payments.tests ledger.tests`.
Local debug mode permits anonymous API access. With `DJANGO_DEBUG=false`, API requests require Django Basic or Session authentication; provision an application user before deployment and serve Basic authentication only over TLS.

## Typical Billing Flow

1. Create a plan and customer.
2. Create a subscription with their IDs. Monthly, quarterly, and yearly periods are inferred; custom cycles require explicit period end dates.
3. Generate an invoice with `subscription_id` and `due_date`; period dates default to the active subscription period.
4. Record a payment with `invoice_id`, `amount`, `currency`, and `status` (`success` or `failed`).
5. Inspect payment attempts and immutable ledger entries.

Successful payments may be partial, but cannot exceed the remaining invoice balance. Provider references, when supplied, must be unique.