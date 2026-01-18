import uuid
import logging
from datetime import timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.settings import settings
from app.db import engine, Base, get_db, utcnow
from app.models import Connection, Transaction, OAuthState
from app.crypto import encrypt_str
from app.provider_mock import router as provider_router
from app.provider_client import ProviderClient
from app.sync import run_sync
from app.logging_config import configure_logging

# Create tables
Base.metadata.create_all(bind=engine)

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Fintech OAuth Sync Lab")

@app.middleware("http")
async def add_request_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add context to logger? For now we just use a logger adapter or manually log
    # For simplicity, we just log start/end
    
    extra = {"request_id": request_id, "method": request.method, "path_url": request.url.path}
    logger.info("Request started", extra=extra)
    
    response = await call_next(request)
    
    response.headers["X-Request-Id"] = request_id
    logger.info(f"Request finished with status {response.status_code}", extra=extra)
    return response

app.include_router(provider_router, prefix="/provider", tags=["mock-provider"])

class StartConnectRequest(BaseModel):
    account_id: str

class SyncRequest(BaseModel):
    account_id: str
    rl: bool = False

@app.post("/connect/start")
def start_connect(req: StartConnectRequest, request: Request, db: Session = Depends(get_db)):
    state = str(uuid.uuid4())
    
    # Store state in DB with TTL
    oauth_state = OAuthState(
        state=state,
        account_id=req.account_id,
        expires_at=utcnow() + timedelta(minutes=10)
    )
    db.add(oauth_state)
    db.commit()
    
    redirect_uri = f"{settings.APP_BASE_URL}/connect/callback"
    
    # Check provider mock directly or construct URL
    # In real world, we construct the URL to redirec the user to.
    auth_url = (
        f"{settings.PROVIDER_BASE_URL}/authorize"
        f"?client_id={settings.PROVIDER_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    
    logger.info(f"Started connect flow for account {req.account_id}", extra={"request_id": request.state.request_id})
    return {"authorize_url": auth_url, "state": state}

@app.get("/connect/callback")
def connect_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    # Lookup state
    oauth_state_row = db.query(OAuthState).filter(OAuthState.state == state).first()
    
    if not oauth_state_row:
        logger.warning(f"Invalid state received: {state}", extra={"request_id": request.state.request_id})
        raise HTTPException(status_code=400, detail="Invalid state")
        
    # Handle naive/aware comparison. DB likely returns naive (UTC context).
    expires_at = oauth_state_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if expires_at < utcnow():
        db.delete(oauth_state_row)
        db.commit()
        logger.warning(f"Expired state received: {state}", extra={"request_id": request.state.request_id})
        raise HTTPException(status_code=400, detail="State expired")
    
    account_id = oauth_state_row.account_id
    
    # Use once and delete
    db.delete(oauth_state_row)
    db.commit()
        
    client = ProviderClient()
    try:
        tokens = client.exchange_code_for_token(code)
    except Exception as e:
        logger.error(f"Token exchange failed: {e}", extra={"request_id": request.state.request_id})
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")
        
    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in")
    
    # Store connection
    conn = db.query(Connection).filter(Connection.account_id == account_id).first()
    if not conn:
        conn = Connection(account_id=account_id)
        db.add(conn)
        
    conn.access_token_enc = encrypt_str(access_token)
    conn.refresh_token_enc = encrypt_str(refresh_token) if refresh_token else None
    # Calculate expires_at ... skipped for brevity, not critical for sync lab logic
    
    db.commit()
    
    return {"status": "connected", "account_id": account_id}

@app.post("/sync/run")
def trigger_sync(req: SyncRequest, request: Request):
    try:
        logger.info(f"Triggering sync for {req.account_id}", extra={"request_id": request.state.request_id})
        stats = run_sync(req.account_id, rl=req.rl)
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Sync exception: {e}", extra={"request_id": request.state.request_id})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transactions")
def list_transactions(
    account_id: str,
    limit: int = 200,
    db: Session = Depends(get_db)
):
    txns = db.query(Transaction).filter(
        Transaction.account_id == account_id
    ).order_by(Transaction.posted_at.desc()).limit(limit).all()
    
    return txns
