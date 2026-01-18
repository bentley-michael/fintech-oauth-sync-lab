import time
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db import SessionLocal, utcnow
from app.models import Connection, Transaction, SyncState
from app.provider_client import ProviderClient, TokenExpiredError, RateLimitedError
from app.crypto import encrypt_str, decrypt_str
from app.settings import settings

logger = logging.getLogger(__name__)

def run_sync(account_id: str, rl: bool = False) -> dict:
    stats = {
        "pages_fetched": 0,
        "items_fetched": 0,
        "inserted": 0,
        "updated": 0,
        "rate_limit_retries": 0
    }
    
    db = SessionLocal()
    client = ProviderClient()
    
    try:
        connection = db.query(Connection).filter(Connection.account_id == account_id).first()
        if not connection:
            raise ValueError(f"No connection found for account {account_id}")
            
        sync_state = db.query(SyncState).filter(SyncState.account_id == account_id).first()
        if not sync_state:
            sync_state = SyncState(account_id=account_id)
            db.add(sync_state)
            db.commit()
            db.refresh(sync_state)
            
        cursor = sync_state.cursor
        access_token = decrypt_str(connection.access_token_enc)
        refresh_token = decrypt_str(connection.refresh_token_enc)
        
        while True:
            # Attempt to fetch page with retries for Rate Limit
            page_data = None
            retries = 0
            
            while retries <= settings.RATE_LIMIT_MAX_RETRIES:
                try:
                    page_data = client.fetch_transactions_page(account_id, access_token, cursor, rl=rl)
                    stats["pages_fetched"] += 1
                    break # Success, exit retry loop
                    
                except TokenExpiredError:
                    # Refresh logic
                    logger.info("Token expired, refreshing...")
                    try:
                        new_tokens = client.refresh_access_token(refresh_token)
                        access_token = new_tokens["access_token"]
                        connection.access_token_enc = encrypt_str(access_token)
                        # Optionally update refresh token if provided
                        if "refresh_token" in new_tokens:
                            refresh_token = new_tokens["refresh_token"]
                            connection.refresh_token_enc = encrypt_str(refresh_token)
                        db.commit()
                        # Retry the request immediately without counting index against rate limit
                        continue 
                    except Exception as e:
                        logger.error(f"Failed to refresh token: {e}")
                        raise
                
                except RateLimitedError as e:
                    retries += 1
                    if retries > settings.RATE_LIMIT_MAX_RETRIES:
                        raise Exception("Max rate limit retries exceeded")
                    
                    stats["rate_limit_retries"] += 1
                    # Exponential backoff: retry_after * (2 ^ (retry-1))
                    sleep_time = e.retry_after * (2 ** (retries - 1))
                    logger.warning(f"Rate limited. Sleeping {sleep_time}s")
                    time.sleep(sleep_time)

            if not page_data:
                break
                
            items = page_data.get("items", [])
            stats["items_fetched"] += len(items)
            
            for item in items:
                # Idempotent Upsert
                # check existing
                provider_txn_id = item["id"]
                existing = db.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.provider_txn_id == provider_txn_id
                ).first()
                
                if existing:
                    # Update fields
                    existing.amount = item["amount"]
                    existing.description = item["description"]
                    # ... other fields
                    existing.raw_json = str(item)
                    stats["updated"] += 1
                else:
                    new_txn = Transaction(
                        account_id=account_id,
                        provider_txn_id=provider_txn_id,
                        amount=item["amount"],
                        currency=item["currency"],
                        description=item["description"],
                        posted_at=datetime.fromisoformat(item["posted_at"]),
                        raw_json=str(item)
                    )
                    db.add(new_txn)
                    stats["inserted"] += 1
            
            db.commit()
            
            next_cursor = page_data.get("next_cursor")
            
            # Update checkpoint
            sync_state.cursor = next_cursor
            sync_state.last_synced_at = utcnow()
            db.commit()
            
            cursor = next_cursor
            if not cursor:
                break
                
        return stats
        
    finally:
        db.close()
