from fastapi import APIRouter, HTTPException, Query, Form, Header, Response
from pydantic import BaseModel
from typing import Optional
import uuid
import datetime
import json

router = APIRouter()

# Global state for rate limiting simulation
ratelimit_memory = set()

def reset_ratelimits():
    ratelimit_memory.clear()

@router.get("/authorize")
def authorize(
    client_id: str,
    redirect_uri: str,
    state: str
):
    auth_code = f"mockcode-{state}"
    target_url = f"{redirect_uri}?code={auth_code}&state={state}"
    return {"redirect_to": target_url}

@router.post("/token")
def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
    if client_id != "demo-client" or client_secret != "demo-secret":
        raise HTTPException(status_code=401, detail="Invalid client credentials")

    # Generate tokens
    expires_in = 120
    new_access_token = f"at_{uuid.uuid4()}_{int(datetime.datetime.now().timestamp())}"
    new_refresh_token = f"rt_{uuid.uuid4()}"

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in
    }

def generate_mock_txns(account_id: str, page: int):
    # 3 pages total: 0, 1, 2. Page 3 is empty.
    if page > 2:
        return []
    
    base_time = datetime.datetime.now() - datetime.timedelta(days=10)
    # 5 items per page
    items = []
    for i in range(5):
        idx = page * 5 + i
        provider_txn_id = f"txn_{account_id}_{idx}"
        amount = 1000 + (idx * 100) 
        posted_at = base_time + datetime.timedelta(hours=idx)
        
        items.append({
            "id": provider_txn_id,
            "amount": amount,
            "currency": "USD",
            "description": f"Mock Txn {idx} for {account_id}",
            "posted_at": posted_at.isoformat(),
            "status": "posted"
        })
    return items

@router.get("/transactions")
def transactions_endpoint(
    response: Response,
    account_id: str = Query(...),
    cursor: Optional[str] = Query(None),
    rl: Optional[bool] = Query(False)
):
    page = 0
    if cursor and cursor.startswith("p"):
        try:
            page = int(cursor[1:])
        except ValueError:
            page = 0
    
    key = f"{account_id}:{cursor}"
    
    if rl:
        if key not in ratelimit_memory:
            ratelimit_memory.add(key)
            # Return 429
            response.headers["Retry-After"] = "1"
            response.status_code = 429
            return {"detail": "rate limited"}
        else:
            # Previously blocked, now allow.
            pass

    items = generate_mock_txns(account_id, page)
    
    next_cursor = None
    if len(items) > 0 and page < 2:
        next_cursor = f"p{page+1}"
        
    return {
        "items": items,
        "next_cursor": next_cursor
    }
