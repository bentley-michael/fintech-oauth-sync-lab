# Fintech OAuth Sync Lab

A self-contained lab environment to demonstrate building a robust financial data synchronization engine using Python (FastAPI), including OAuth2 flow, pagination handling, rate-limit backoff, and idempotent logic/resumption.

## Features
- **Local Sandbox**: In-memory "Mock Provider" mimics a real bank API with OAuth tokens, pagination, and rate limits.
- **Robust Sync**: Handles token refresh, cursor-based pagination, exponential backoff for 429s, and atomic upserts.
- **Secure**: Fernet (AES-128-CBC) encryption for tokens using `cryptography`.
- **Stateless-ish**: OAuth state stored in DB with TTL.
- **Observability**: JSON structured logging with request ID correlation.
- **Test Coverage**: End-to-end integration tests using `TestClient`.

## setup
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # OR
   pip install fastapi uvicorn httpx pydantic-settings sqlalchemy pytest respx python-multipart cryptography
   ```

2. **Run the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Run the demo script** (in another terminal):
   ```bash
   python scripts/demo_sync.py
   ```

   You should see:
   - OAuth authorize flow simulation.
   - Successful token exchange.
   - Initial sync of 15 transactions (3 pages).
   - Idempotent re-run (0 inserted, 15 updated).
   - Rate-limit handling demonstration (retries and succeeds).

## Tests
Run the test suite:

**Windows PowerShell Setup (Recommended Python 3.11+, tested on 3.12):**
```powershell
# Create venv
py -3.12 -m venv .venv
# Activate
.\.venv\Scripts\Activate.ps1
# Update pip
python -m pip install -U pip
# Install editable
pip install -e .
# Run tests
pytest
```

All tests should pass, covering OAuth, pagination, rate-limiting, and state recovery.

## Production Considerations Not Implemented
- **Secret Management**: Keys are currently loaded from env/defaults. In production, use AWS KMS, HashiCorp Vault, or Azure Key Vault.
- **Distributed State**: Currently using SQLite. For high scale, move `oauth_states` and `sync_state` to Redis or PostgreSQL.
- **Distributed Locking**: `run_sync` is safe for single-worker, but multiple workers for the same `account_id` could race. Use Redis locks (Redlock) or DB row locks (`SELECT FOR UPDATE`).
- **Metrics**: Add Prometheus/DataDog metrics for: sync_duration, pages_fetched, token_refreshes, 429_events.
- **Circuit Breaker**: If provider is down, stop retrying globally.

## Project Structure
- `app/`: Main application code.
  - `provider_mock.py`: Simulates the external bank API.
  - `sync.py`: The core synchronization logic.
- `scripts/`: Demo automation.
- `tests/`: Integration tests.
