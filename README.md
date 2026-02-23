# Fintech OAuth Sync Lab

![CI](https://github.com/bentley-michael/fintech-oauth-sync-lab/actions/workflows/ci.yml/badge.svg)

Production-grade financial data synchronization engine demonstrating OAuth2 flows, intelligent rate limiting, and fault-tolerant API integration patterns used by fintech platforms like Plaid, Stripe, and modern banking APIs.

🎯 Skills Demonstrated
Backend Engineering • API Integration • OAuth2 Security • Distributed Systems Patterns • Financial Services • Test-Driven Development

Python • FastAPI • SQLAlchemy • OAuth2 • REST APIs • Pytest • GitHub Actions • CI/CD
🏗️ Architecture
mermaid
graph TB
    subgraph "Client Application"
        A[User/App]
    end
    
    subgraph "FastAPI Server"
        B[OAuth Controller]
        C[Sync Engine]
        D[Provider Client]
        E[Database Layer]
    end
    
    subgraph "External Services"
        F[Mock Bank Provider]
        G[Real Financial APIs]
    end
    
    A -->|1. Initiate OAuth| B
    B -->|2. Redirect to Provider| F
    F -->|3. Auth Code| B
    B -->|4. Exchange Token| F
    B -->|5. Store Encrypted Token| E
    A -->|6. Trigger Sync| C
    C -->|7. Refresh Token if Needed| D
    D -->|8. Paginated Requests| F
    D -.->|Production| G
    C -->|9. Idempotent Upsert| E
    
    style C fill:#00a393
    style D fill:#00a393
    style E fill:#4a9eff
✨ Key Features
🔐 Secure OAuth2 Implementation
Token Lifecycle Management: Automatic refresh with encrypted storage using Fernet (AES-256)
State Validation: CSRF protection with time-bound state tokens
Secure by Default: No plaintext credentials in database
🔄 Intelligent Synchronization Engine
python
# Core sync pattern
✓ Cursor-based pagination (handles millions of records)
✓ Exponential backoff with jitter (429 rate limit handling)
✓ Resumable checkpoints (crash recovery)
✓ Idempotent upserts (exactly-once semantics)
📊 Production-Ready Patterns
Structured Logging: JSON logs with request ID correlation
Comprehensive Testing: Integration tests with >85% coverage
CI/CD Pipeline: Automated testing on every commit
Mock Provider: Isolated testing environment with realistic behaviors
🚀 Quick Start
Prerequisites
Python 3.12+
pip 23.0+
Installation (Windows PowerShell)
powershell
# 1. Clone and navigate
git clone https://github.com/bentley-michael/fintech-oauth-sync-lab.git
cd fintech-oauth-sync-lab

# 2. Create virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
python -m pip install -U pip
pip install -e .

# 4. Start the server
uvicorn app.main:app --reload
API Documentation: http://127.0.0.1:8000/docs

Run the Demo
powershell
python scripts/demo_sync.py
Expected Output:

[INFO] Starting OAuth flow for account: demo_user_123
[INFO] ✓ Authorization successful - exchanging code for token
[INFO] ✓ Token encrypted and stored securely
[INFO] Starting sync...
[INFO] Page 1/3: Retrieved 5 transactions
[INFO] Page 2/3: Retrieved 5 transactions (rate limited - backing off 2.1s)
[INFO] Page 3/3: Retrieved 5 transactions
[SUCCESS] Sync complete: 15 inserted, 0 updated, 0 skipped

Re-running immediately...
[INFO] Idempotency check: All transactions already exist
[SUCCESS] Sync complete: 0 inserted, 15 updated, 0 skipped
🧪 Testing
bash
# Run all tests with coverage
python -m pytest -v --cov=app --cov-report=term-missing

# Run specific test suite
python -m pytest tests/test_sync.py -v

# Run with detailed logging
python -m pytest -v -s
Test Coverage Highlights:

✅ OAuth state validation and expiration
✅ Token refresh edge cases
✅ Pagination cursor handling
✅ Rate limit retry with exponential backoff
✅ Concurrent sync prevention
✅ Database transaction rollback
📁 Project Structure
fintech-oauth-sync-lab/
├── app/
│   ├── main.py                 # FastAPI application & routes
│   ├── sync.py                 # Core sync engine with retry logic
│   ├── provider_client.py      # HTTP client with OAuth headers
│   ├── provider_mock.py        # Built-in mock bank API
│   ├── models.py               # SQLAlchemy ORM models
│   └── db.py                   # Database session management
├── scripts/
│   └── demo_sync.py            # Interactive demonstration
├── tests/
│   ├── test_oauth.py           # OAuth flow tests
│   ├── test_sync.py            # Sync engine tests
│   └── test_rate_limiting.py  # Backoff algorithm tests
├── .github/workflows/
│   └── ci.yml                  # GitHub Actions pipeline
└── pyproject.toml              # Project dependencies & metadata
🎓 Design Decisions
Why Cursor-Based Pagination?
Traditional offset pagination breaks with high-volume inserts. Cursor-based pagination guarantees consistency even when data changes during sync.

Why Exponential Backoff?
Linear retry can amplify rate limit violations across multiple clients. Exponential backoff with jitter distributes retry attempts, reducing thundering herd problems.

Why Idempotent Upserts?
Network failures can cause duplicate requests. Idempotent operations ensure exactly-once semantics without complex distributed locking.

## Security Notes

- OAuth tokens are encrypted at rest before persistence.
- `TOKEN_KEY` must be rotated and managed via a secret manager in production.
- OAuth state is time-bound and validated to reduce CSRF risk.
- Retry/backoff logic prevents aggressive client behavior during provider rate limiting.
- Enforce HTTPS/TLS and avoid logging secrets or raw token values.

🏭 Production Considerations
⚠️ Not Implemented (By Design)
This is a learning lab focused on core patterns. Production deployment would require:

Component	Lab Approach	Production Approach
Secrets	Environment variables	AWS Secrets Manager / HashiCorp Vault
Database	SQLite (single-file)	PostgreSQL with read replicas
OAuth State	SQLite with TTL	Redis cluster with TTL
Sync Locking	In-memory flag	Distributed lock (Redis/Redlock)
Observability	JSON logs	Datadog/Prometheus + APM
Error Handling	Retry logic	+ Circuit breaker + dead letter queue
🔮 Scaling Path
Horizontal Scaling: Move to Redis for shared state
Queue-Based Architecture: Add Celery/RQ for async syncs
Multi-Region: Deploy read replicas, CDN for static assets
Monitoring: Add Sentry for error tracking, Prometheus for metrics
🤝 Contributing
This is a portfolio/learning project, but feedback is welcome!

Fork the repository
Create a feature branch (git checkout -b feature/improvement)
Run tests (pytest)
Submit a pull request
📜 License
MIT License - Feel free to use this as a reference or starting point for your own projects.

🔗 Connect
Michael Bentley - LinkedIn • Portfolio • Email

💡 Interested in discussing API integration patterns, OAuth security, or fintech engineering? Let's connect!

<p align="center"> <sub>Built with ❤️ using FastAPI and modern Python best practices</sub> </p>
