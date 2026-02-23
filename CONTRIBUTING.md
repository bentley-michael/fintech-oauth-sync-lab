# Contributing

Thanks for your interest! Here is how to run the project locally.

## Setup (PowerShell)

1.  **Clone the repo**
    ```powershell
    git clone https://github.com/bentley-michael/fintech-oauth-sync-lab.git
    cd fintech-oauth-sync-lab
    ```

2.  **Create virtual env**
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

3.  **Install dependencies**
    ```powershell
    python -m pip install -U pip
    python -m pip install -e ".[test]"
    ```

## Run Tests

We use `pytest` for testing.

```powershell
python -m pytest
```

## Run the App

Start the FastAPI server locally:

```powershell
uvicorn app.main:app --reload
```
