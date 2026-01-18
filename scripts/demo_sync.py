import httpx
import time
import sys

BASE_URL = "http://127.0.0.1:8000"
ACCOUNT_ID = "user_123"

def run_demo():
    print("--- 1. START CONNECT ---")
    try:
        resp = httpx.post(f"{BASE_URL}/connect/start", json={"account_id": ACCOUNT_ID})
        resp.raise_for_status()
    except httpx.ConnectError:
        print("Error: Could not connect to server. Make sure it's running (uvicorn app.main:app).")
        sys.exit(1)

    data = resp.json()
    auth_url = data["authorize_url"]
    state = data["state"]
    print(f"Got Authorize URL: {auth_url}")

    # Simulate user visiting the auth_url
    # Only possible because it's our mock provider in the same process/port
    print("\n--- 2. AUTHORIZE (Mock User Click) ---")
    try:
        # We don't need a real browser. The authorize URL is a GET to /provider/authorize
        # which returns a JSON with 'redirect_to'.
        # Note: In a real app authorize endpoint returns HTML.
        # Here we mock it as returning JSON for automation ease or just manually parsing the redirect?
        # My provider mock returns JSON {"redirect_to": ...}
        
        # We need to parse the params from auth_url
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)
        
        # Call provider authorize endpoint
        # NOTE: auth_url is full url.
        resp = httpx.get(auth_url)
        resp.raise_for_status()
        redirect_to = resp.json()["redirect_to"]
        print(f"Provider redirected to: {redirect_to}")
        
    except Exception as e:
        print(f"Failed to mock authorize: {e}")
        sys.exit(1)

    print("\n--- 3. CALLBACK ---")
    # Simulate browser following redirect to callback
    # redirect_to is something like http://.../callback?code=...&state=...
    resp = httpx.get(redirect_to)
    resp.raise_for_status()
    print("Callback Response:", resp.json())

    print("\n--- 4. RUN SYNC (First Run) ---")
    resp = httpx.post(f"{BASE_URL}/sync/run", json={"account_id": ACCOUNT_ID})
    resp.raise_for_status()
    print("Sync Stats:", resp.json())
    
    print("\n--- 5. RUN SYNC (Second Run - Idempotency) ---")
    resp = httpx.post(f"{BASE_URL}/sync/run", json={"account_id": ACCOUNT_ID})
    resp.raise_for_status()
    print("Sync Stats:", resp.json())
    
    print("\n--- 6. RUN SYNC (Simulate Rate Limit) ---")
    # Requesting rl=True forces the provider to 429 once
    resp = httpx.post(f"{BASE_URL}/sync/run", json={"account_id": ACCOUNT_ID, "rl": True}, timeout=30.0)
    resp.raise_for_status()
    print("Sync Stats:", resp.json())
    
    print("\n--- 7. LIST TRANSACTIONS ---")
    resp = httpx.get(f"{BASE_URL}/transactions", params={"account_id": ACCOUNT_ID})
    txns = resp.json()
    print(f"Found {len(txns)} transactions.")
    if txns:
        print("Sample:", txns[0])

if __name__ == "__main__":
    run_demo()
