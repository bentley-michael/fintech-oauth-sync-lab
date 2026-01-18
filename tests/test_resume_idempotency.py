from app.models import Connection, Transaction, SyncState
from app.crypto import encrypt_str

def test_idempotency(client, db):
    account_id = "user_idem"
    conn = Connection(
        account_id=account_id,
        access_token_enc=encrypt_str("at_test"),
        refresh_token_enc=encrypt_str("rt_test")
    )
    db.add(conn)
    db.commit()
    
    # Run 1
    resp1 = client.post("/sync/run", json={"account_id": account_id})
    assert resp1.status_code == 200
    stats1 = resp1.json()["stats"]
    assert stats1["inserted"] == 15
    
    # Run 2
    resp2 = client.post("/sync/run", json={"account_id": account_id})
    assert resp2.status_code == 200
    stats2 = resp2.json()["stats"]
    assert stats2["inserted"] == 0
    # Might be 'updated' if logic detects change or blindly updates.
    # Our logic: checks existing. If exists, updates.
    assert stats2["updated"] == 15
    
    # Verify DB count stable
    count = db.query(Transaction).filter_by(account_id=account_id).count()
    assert count == 15

def test_resume_cursor(client, db):
    account_id = "user_resume"
    conn = Connection(
        account_id=account_id,
        access_token_enc=encrypt_str("at_test"),
        refresh_token_enc=encrypt_str("rt_test")
    )
    db.add(conn)
    
    # Manually insert sync state with cursor "p1" (skip page 0)
    ss = SyncState(account_id=account_id, cursor="p1")
    db.add(ss)
    db.commit()
    
    resp = client.post("/sync/run", json={"account_id": account_id})
    assert resp.status_code == 200
    stats = resp.json()["stats"]
    
    # Page 0 has 5 items. Page 1 has 5. Page 2 has 5.
    # Starting at p1 should fetch p1 and p2 -> 10 items.
    assert stats["items_fetched"] == 10
    assert stats["inserted"] == 10
