# FastAPI + SQLModel + Alembic + PostgreSQL 18

A modern RESTful API application built with **Python 3.14**, managed with **uv**, and backed by **PostgreSQL 18** using **SQLModel** and **Alembic**. Configuration is managed cleanly via **pydantic-settings** with `.env` support.

---

## Features

- **Python 3.14 & uv**: Fast, reproducible dependency management and execution.
- **FastAPI**: High-performance async web framework with automatic OpenAPI documentation.
- **SQLModel & SQLAlchemy 2.0**: Unified Pydantic and SQLAlchemy ORM models with `psycopg` (v3).
- **Alembic Migrations**: Fully configured database versioning and automated migrations.
- **Pydantic-Settings**: Type-safe settings loaded directly from `.env`.
- **Field Validations & Descriptions**:
  - `name` fields for both Company and Employee are validated (not null, 1 to 255 characters).
  - Explicit field descriptions rendered in OpenAPI / Swagger docs (`/docs` and `/redoc`).
- **Automatic Timestamps**:
  - `updated` timestamp column on both `companies` and `employees` tables.
  - Automatically populated on creation and refreshed on every update.
- **Relational Data Model**:
  - `companies`: One-to-many relationship with employees.
  - `employees`: One-to-one relationship to a parent company (fields: `id`, `name`, `birthday`, `company_id`, `updated`).
- **Full CRUD Support**: Complete CRUD operations for both companies and employees.
- **Dedicated Routes**:
  - `/companies`: Create, read, paginate, update, and delete companies with nested employee details.
  - `/employees`: Create, read, paginate, filter, update, and delete employees with company details.
- **Code Quality with Ruff**:
  - Configured via `ruff.toml` with default rules (Pyflakes, pycodestyle, isort, pyupgrade, bugbear).
- **Automated Dockerized Test Suite**:
  - **Pytest Unit Tests (`tests/test_crud.py`)**: Tests CRUD methods, relational integrity, constraints, timestamp updates, and random data seeding.
  - **FastAPI TestClient Tests (`tests/test_api.py`)**: Tests all HTTP endpoints, status codes, query filters, OpenAPI documentation schemas, and error cases (404, 422).
  - Both test suites automatically launch an isolated **PostgreSQL 18 container in Docker**, apply Alembic migrations, populate randomized test data, execute tests, and destroy the container upon completion.
- **GitHub Actions CI/CD**:
  - **CI Workflow (`.github/workflows/ci.yml`)**: Runs Ruff linting, formatting checks, and the full test suite on push/PR.
  - **CD Workflow (`.github/workflows/deploy.yml`)**: Retrieves application parameters from AWS Systems Manager (SSM) Parameter Store or AWS Secrets Manager into `.env`, builds the Docker image, and deploys it to Amazon ECR.

---

## Project Structure

```text
fastapi-sqlmodel/
├── .github/
│   └── workflows/
│       ├── ci.yml        # GitHub Actions CI (Ruff linting, formatting, & tests)
│       └── deploy.yml    # GitHub Actions CD (AWS SSM params & ECR deployment)
├── .dockerignore         # Docker ignore rules
├── .env                  # Local environment configuration
├── .env.example          # Template environment configuration
├── .python-version       # Python version specification (3.14)
├── Dockerfile            # Container build specification with Python 3.14 & uv
├── pyproject.toml        # uv project metadata and dependencies
├── ruff.toml             # Ruff linter and formatter configuration
├── README.md             # Project documentation
├── alembic.ini           # Alembic configuration
├── alembic/              # Migration scripts and environment
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 1f90392a7dd7_initial_migration.py
│       └── 9c04b43e1623_add_updated_column_to_companies_and_.py
├── app/
│   ├── __init__.py
│   ├── config.py         # pydantic-settings configuration
│   ├── database.py       # SQLModel engine and session dependency
│   ├── models.py         # Company & Employee SQLModel entities with validations
│   ├── schemas.py        # Request/response schemas with field validations & descriptions
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── company.py    # Company CRUD operations
│   │   └── employee.py   # Employee CRUD operations
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── companies.py  # /companies API router
│   │   └── employees.py  # /employees API router
│   └── main.py           # FastAPI application & entrypoint
└── tests/
    ├── __init__.py
    ├── conftest.py       # Docker PostgreSQL 18 fixture, Alembic runner & Faker seeder
    ├── test_crud.py      # Pytest unit tests for CRUD, validations & models
    └── test_api.py       # FastAPI TestClient endpoint & validation tests
```

---

## Prerequisites

1. **Python 3.14**
2. **uv** (v0.6+): Install via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`
3. **Docker**: Running Docker daemon for PostgreSQL 18 containerization and test suites.

---

## Quickstart

### 1. Environment Setup

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Ensure the variables match your local setup:

```env
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fastapi_db
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/fastapi_db
PROJECT_NAME="FastAPI SQLModel Company & Employee API"
```

### 2. Install Dependencies

Install all dependencies into the virtual environment using `uv`:

```bash
uv sync
```

### 3. Start Local PostgreSQL 18 (Docker)

If you don't already have a PostgreSQL 18 instance running, start one using Docker:

```bash
docker run -d \
  --name postgres18 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=fastapi_db \
  -p 5432:5432 \
  postgres:18
```

### 4. Run Database Migrations

Apply database migrations using Alembic:

```bash
uv run alembic upgrade head
```

To create a new migration revision after modifying models:

```bash
uv run alembic revision --autogenerate -m "Add new columns"
```

### 5. Start the FastAPI Development Server

Launch the server with live reload:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatively, run the project CLI entrypoint:

```bash
uv run fastapi-sqlmodel
```

Open your browser to explore the API:
- **Interactive OpenAPI Documentation (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

### 6. Run with Docker

To build and run the application container:

```bash
# Build the Docker image
docker build -t fastapi-sqlmodel:latest .

# Run the container (connecting to host PostgreSQL or Docker network)
docker run -d \
  --name fastapi-app \
  -p 8000:8000 \
  --env-file .env \
  fastapi-sqlmodel:latest
```

---

## Code Quality & Linting (Ruff)

The project includes a `ruff.toml` configuration enforcing code style, formatting, and imports:

- **Run linter**:
  ```bash
  uv run ruff check .
  ```
- **Automatically fix lint issues**:
  ```bash
  uv run ruff check --fix .
  ```
- **Check formatting**:
  ```bash
  uv run ruff format --check .
  ```
- **Format code**:
  ```bash
  uv run ruff format .
  ```

---

## API Endpoints

### Companies (`/companies`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/companies/` | Create a new company (name: 1-255 characters, not null) |
| `GET` | `/companies/` | List companies with pagination (`offset`, `limit`) |
| `GET` | `/companies/{company_id}` | Get company by ID with its list of employees |
| `PUT` | `/companies/{company_id}` | Update company name (automatically updates `updated` timestamp) |
| `DELETE` | `/companies/{company_id}` | Delete company (cascades to employees) |

### Employees (`/employees`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/employees/` | Create a new employee (name: 1-255 characters, optional `birthday` & `company_id`) |
| `GET` | `/employees/` | List employees with pagination and optional `company_id` filter |
| `GET` | `/employees/{employee_id}` | Get employee by ID with associated company details |
| `PUT` | `/employees/{employee_id}` | Update employee details (automatically updates `updated` timestamp) |
| `DELETE` | `/employees/{employee_id}` | Delete an employee |

---

## Testing

The project includes **2 test sets**:
1. **Pytest Unit Tests (`tests/test_crud.py`)**: Tests CRUD methods, SQLModel entities, validation limits (1-255 characters, not null), timestamp changes, and one-to-many relationship integrity.
2. **FastAPI TestClient Tests (`tests/test_api.py`)**: Tests all FastAPI endpoints, serialization, validation errors (422), timestamp verification, and OpenAPI documentation descriptions.

### Docker Test Container Lifecycle

When you run tests:
1. `tests/conftest.py` spins up a new isolated `postgres:18` container on an ephemeral host port (preventing port collisions with port 5432).
2. It waits for the container to become completely healthy and ready to accept queries.
3. It automatically executes Alembic migrations (`alembic upgrade head`) against the container.
4. It seeds random companies and employees using `Faker`.
5. Tests execute against the live PostgreSQL 18 instance.
6. The container is automatically stopped and destroyed during teardown.

### Run All Tests

```bash
uv run pytest
```

### Run Unit Tests Only

```bash
uv run pytest tests/test_crud.py
```

### Run FastAPI TestClient Endpoint Tests Only

```bash
uv run pytest tests/test_api.py
```

---

## GitHub Actions & AWS ECR Deployment

### 1. CI Workflow (`.github/workflows/ci.yml`)

Triggers on every `push` and `pull_request` to `main` and `master`:
1. Installs Python 3.14 and dependencies via `uv`.
2. Runs `uv run ruff check .` and `uv run ruff format --check .`.
3. Runs all Pytest suites with the automated PostgreSQL 18 Docker container.

### 2. CD Workflow (`.github/workflows/deploy.yml`)

Triggers on `push` to `main`/`master` or via manual `workflow_dispatch`:
1. Authenticates to AWS via `aws-actions/configure-aws-credentials`.
2. Retrieves required parameters from **AWS Systems Manager (SSM) Parameter Store** or **AWS Secrets Manager**, writing them into `.env`.
3. Falls back gracefully to `.env.example` if no remote parameters are found.
4. Logs in to **Amazon ECR** via `aws-actions/amazon-ecr-login`.
5. Builds the production Docker image, tags it with the commit SHA and `latest`, and pushes it to your ECR repository.

#### Configuration Storage in AWS

The deployment pipeline is designed to fetch runtime configuration and database credentials from either **AWS Systems Manager Parameter Store** or **AWS Secrets Manager**, with an automatic fallback:

##### Option 1: AWS Systems Manager (SSM) Parameter Store

Parameters are stored using a hierarchical path prefix configured by `SSM_PARAMETER_PATH` (defaults to `/fastapi-sqlmodel/prod/`). The deployment script queries all parameters under this prefix and strips the path prefix to form the environment variable name (e.g., `/fastapi-sqlmodel/prod/DATABASE_URL` becomes `DATABASE_URL`).

Example commands to create parameters using the AWS CLI:

```bash
# Standard parameters (Type: String)
aws ssm put-parameter \
  --name "/fastapi-sqlmodel/prod/POSTGRES_SERVER" \
  --value "postgres.internal" \
  --type "String"

aws ssm put-parameter \
  --name "/fastapi-sqlmodel/prod/POSTGRES_PORT" \
  --value "5432" \
  --type "String"

aws ssm put-parameter \
  --name "/fastapi-sqlmodel/prod/POSTGRES_USER" \
  --value "postgres" \
  --type "String"

aws ssm put-parameter \
  --name "/fastapi-sqlmodel/prod/POSTGRES_DB" \
  --value "fastapi_db" \
  --type "String"

# Sensitive parameters (Type: SecureString with KMS encryption)
aws ssm put-parameter \
  --name "/fastapi-sqlmodel/prod/POSTGRES_PASSWORD" \
  --value "your_secure_password" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/fastapi-sqlmodel/prod/DATABASE_URL" \
  --value "postgresql+psycopg://postgres:your_secure_password@postgres.internal:5432/fastapi_db" \
  --type "SecureString"
```

##### Option 2: AWS Secrets Manager

Alternatively (or in addition), you can store credentials as a single JSON key-value secret in AWS Secrets Manager and provide the secret name via the `AWS_SECRET_NAME` GitHub Secret.

Example command to create the secret using the AWS CLI:

```bash
aws secretsmanager create-secret \
  --name "fastapi-sqlmodel/prod/credentials" \
  --description "Production credentials for fastapi-sqlmodel app" \
  --secret-string '{
    "POSTGRES_SERVER": "postgres.internal",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "your_secure_password",
    "POSTGRES_DB": "fastapi_db",
    "DATABASE_URL": "postgresql+psycopg://postgres:your_secure_password@postgres.internal:5432/fastapi_db"
  }'
```

The CD workflow fetches the secret, parses the JSON keys, and appends each `KEY=VALUE` pair to the `.env` file.

##### Fallback to Local `.env` / `.env.example`

If neither AWS SSM Parameter Store nor AWS Secrets Manager is configured, or if the AWS credentials lack permissions to access them:
1. The CD workflow checks if a local `.env` has already been populated.
2. If `.env` is empty or does not exist, the workflow **automatically falls back to `.env.example`**, ensuring the build and deployment succeed without crashing.
3. For local container execution or testing, simply maintain your local `.env` file — AWS access is never strictly required.

#### Required GitHub Secrets & Variables

To enable the deployment workflow, configure the following in your GitHub repository (**Settings > Secrets and variables > Actions**):

| Secret / Variable | Type | Description |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | Secret | AWS Access Key with permissions for ECR and SSM/Secrets Manager |
| `AWS_SECRET_ACCESS_KEY` | Secret | AWS Secret Access Key |
| `AWS_REGION` | Variable/Secret | Target AWS Region (e.g., `us-east-1`) |
| `ECR_REPOSITORY` | Variable/Secret | Target Amazon ECR repository name (e.g., `fastapi-sqlmodel`) |
| `SSM_PARAMETER_PATH` | Variable/Secret | (Optional) Path in SSM Parameter Store (default: `/fastapi-sqlmodel/prod/`) |
| `AWS_SECRET_NAME` | Secret | (Optional) Name of AWS Secrets Manager secret if used |
