# Fintech OAuth Sync Lab

[![CI](https://github.com/bentley-michael/fintech-oauth-sync-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/bentley-michael/fintech-oauth-sync-lab/actions/workflows/ci.yml)

A self-contained lab environment demonstrating a robust financial data synchronization engine using Python (FastAPI). Key features include OAuth2 flows, cursor-based pagination, exponential backoff for 429 rate limits, and idempotent transaction upserts.

## Features
- **Local Sandbox**: Built-in Mock Provider mimics a bank API (OAuth tokens, pagination, rate limits).
- **Robust Sync**: Handles token refresh, cursor-based pagination, exponential backoff for 429s, and atomic upserts.
- **Secure**: Fernet (symmetric authenticated encryption) for tokens using `cryptography`.
- **Stateless-ish**: OAuth state stored in DB with TTL.
- **Observability**: JSON structured logging with request ID correlation.
- **Test Coverage**: End-to-end integration tests using `TestClient`.

## Setup

**Windows PowerShell (Recommended Python 3.12):**
```powershell
# Create venv
py -3.12 -m venv .venv

# Activate
.\.venv\Scripts\Activate.ps1

# Update pip
python -m pip install -U pip

# Install in editable mode (uses pyproject.toml)
pip install -e .

# Run the server
uvicorn app.main:app --reload
```

Server docs will be available at: http://127.0.0.1:8000/docs

## Quick Demo

In a new terminal (with venv activated), run:
```powershell
python scripts/demo_sync.py
```

Expected output highlights:
- **Authorization**: Simulates user consent flows.
- **First Sync**: Fetches 15 transactions across 3 pages.
- **Resume**: Re-running the script demonstrates idempotency (0 inserted, 15 updated).
- **Rate Limits**: Automatically handles and retries 429 responses.

## Tests
Run the full integration suite:

```powershell
python -m pytest -q
```

All tests should pass, covering OAuth, pagination, rate-limiting, and state recovery.

## Production Considerations Not Implemented
- **Secret Management**: Keys currently use env vars/defaults. Production should use AWS KMS or Vault.
- **Distributed State**: Uses SQLite. Production needs Redis/PostgreSQL for shared `oauth_states`.
- **Locking**: `run_sync` needs distributed locks (Redis/Redlock) to prevent race conditions on the same account.
- **Metrics**: Missing Prometheus/DataDog hooks for observability.
- **Circuit Breaker**: No global circuit breaker for provider outages.

## Project Structure
- `app/`
  - `main.py`: FastAPI entry point.
  - `sync.py`: Core synchronization engine (retry, pagination, backoff).
  - `provider_client.py`: HTTP client with auth headers.
  - `provider_mock.py`: Built-in mock provider (OAuth + paginated transactions + optional 429).
  - `models.py` / `db.py`: Database schema and connection.
- `scripts/demo_sync.py`: Interactive demo script.
- `tests/`: Integration tests via pytest.

