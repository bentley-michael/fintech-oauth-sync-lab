from app.models import Connection
from app.crypto import encrypt_str

def test_rate_limit_handling(client, db):
    account_id = "user_rl"
    
    conn = Connection(
        account_id=account_id,
        access_token_enc=encrypt_str("at_test"),
        refresh_token_enc=encrypt_str("rt_test")
    )
    db.add(conn)
    db.commit()
    
    # Run sync with rl=True
    # Mock provider logic: if rl=True, first request returns 429, then subsequent succeed.
    resp = client.post("/sync/run", json={"account_id": account_id, "rl": True})
    assert resp.status_code == 200
    stats = resp.json()["stats"]
    
    assert stats["rate_limit_retries"] >= 1
    assert stats["items_fetched"] == 15 # Still completes
