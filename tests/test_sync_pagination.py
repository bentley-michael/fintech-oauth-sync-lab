from app.models import Connection, Transaction, SyncState
from app.crypto import encrypt_str

def test_sync_pagination(client, db):
    account_id = "user_pag"
    
    # 1. Setup connection manually
    conn = Connection(
        account_id=account_id,
        access_token_enc=encrypt_str("at_test"),
        refresh_token_enc=encrypt_str("rt_test"),
        provider="mock"
    )
    db.add(conn)
    db.commit()
    
    # 2. Run sync
    resp = client.post("/sync/run", json={"account_id": account_id})
    assert resp.status_code == 200
    stats = resp.json()["stats"]
    
    # Mock behavior: 3 pages (0, 1, 2) each has 5 items. Page 3 empty.
    # Total items = 15.
    assert stats["pages_fetched"] >= 3 
    assert stats["items_fetched"] == 15
    assert stats["inserted"] == 15
    
    # 3. Verify DB
    txns = db.query(Transaction).filter_by(account_id=account_id).all()
    assert len(txns) == 15
    
    # 4. Verify Sync State
    ss = db.query(SyncState).filter_by(account_id=account_id).first()
    assert ss is not None
    assert ss.cursor is None # Finished
    assert ss.last_synced_at is not None
