# IS-601 Module 10 — Secure User Model

A FastAPI application demonstrating a secure user model with password hashing, Pydantic schema validation, SQLAlchemy ORM integration, and a CI/CD pipeline.


## What Was Implemented

### 1. SQLAlchemy User Model (`app/models/__init__.py`)
| Column | Type | Constraints |
|---|---|---|
| `id` | Integer | Primary key, indexed |
| `username` | String(50) | Unique, not null, indexed |
| `email` | String(255) | Unique, not null, indexed |
| `password_hash` | String(128) | Not null |
| `created_at` | DateTime (timezone-aware) | Not null, defaults to `NOW()` |

### 2. Pydantic Schemas (`app/schemas/__init__.py`)
- **`UserCreate`** — accepts `username`, `email` (validated as `EmailStr`), and `password`
- **`UserRead`** — returns `id`, `username`, `email`, and `created_at`; never exposes `password_hash`

### 3. Password Hashing (`app/hashing/__init__.py`)
Passwords are never stored in plain text.

- **`hash_password(password)`** — generates a random 16-byte salt, computes `SHA3-256(salt + password)`, and returns `"<salt_hex>$<digest_hex>"`
- **`verify_password(plain, hashed)`** — splits the stored value, re-hashes the candidate with the stored salt, and compares digests


## Running Locally with Docker

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Start all containers

```bash
docker-compose up --build
```

This starts three services:

| Service | URL | Description |
|---|---|---|
| FastAPI app | http://localhost:8000 | Calculator web interface |
| FastAPI docs | http://localhost:8000/docs | Interactive Swagger UI |
| pgAdmin | http://localhost:5050 | Database browser |
| PostgreSQL | localhost:5432 | Database (internal) |

The `users` table is created automatically on startup — both by Postgres running `sql/init.sql` on first boot and by SQLAlchemy's `create_all()` at app startup.

### Stop containers

```bash
docker-compose down
```

To also remove the database volume (full reset):

```bash
docker-compose down -v
```


## Browsing the Database with pgAdmin

1. Open http://localhost:5050
2. Log in: **Email** `admin@example.com` / **Password** `admin`
3. Add a new server:
   - **Name:** any name (e.g. `local`)
   - **Host:** `db`
   - **Port:** `5432`
   - **Username:** `postgres`
   - **Password:** `postgres`
   - **Database:** `fastapi_db`
4. Navigate to **Servers → local → Databases → fastapi_db → Schemas → public → Tables → users**

## Running Tests

### Unit tests (no database needed)

```bash
COVERAGE_FILE=/tmp/.coverage python -m pytest tests/unit -v
```

Covers:
- `hash_password` returns a salted `salt$digest` string
- Same password produces different hashes (random salt)
- `verify_password` accepts correct password, rejects wrong one
- `UserCreate` rejects invalid/missing emails and fields
- `UserRead` maps from ORM objects correctly
- `get_db` session lifecycle

### Integration tests (requires PostgreSQL)

Start the database container first:

```bash
docker-compose up -d db
```

Then run:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
COVERAGE_FILE=/tmp/.coverage \
python -m pytest tests/integration -v
```

Covers:
- User creation persists to the database
- `created_at` is set automatically
- `password_hash` is stored, not the plain-text password
- Duplicate `username` raises `IntegrityError`
- Duplicate `email` raises `IntegrityError`
- Invalid emails are rejected by the schema before hitting the database

### All tests with coverage report

```bash
docker-compose up -d db
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
COVERAGE_FILE=/tmp/.coverage \
python -m pytest tests/unit tests/integration -v
```

Expected result: **100% coverage** across all `app/` modules.

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/test.yml`) runs on every push and pull request to `main`:

1. **Unit tests** — no external dependencies
2. **Integration tests** — against a Postgres service container
3. **E2E tests** — starts the FastAPI server and uses Playwright
4. **Security scan** — Trivy scans the Docker image for HIGH/CRITICAL CVEs
5. **Deploy** — pushes to Docker Hub on successful `main` branch builds

## DockerHub Link
https://hub.docker.com/repository/docker/adrianchen8662/is-601-module-10-secure-user-model/general