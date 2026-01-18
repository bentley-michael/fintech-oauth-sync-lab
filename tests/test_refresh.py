from app.models import Connection, Transaction
from app.crypto import encrypt_str
from app.settings import settings
import httpx
import respx

def test_token_refresh_flow(client, db):
    account_id = "user_refresh_verify"
    
    # 1. Setup connection with EXPIRED token (simulated by mocking the provider response)
    # Actually, the token string itself doesn't matter unless we parse it.
    # Our mocked provider logic uses stateless logic unless we override it.
    # We will use respx to intercept calls to PROVIDER_BASE_URL.
    
    # But wait, ProviderClient uses httpx.Client().
    # Conftest.py patches ProviderClient._get_client to return a TestClient(app).
    # This means calls go to the IN-PROCESS app provider endpoints.
    # To test refresh, we need the provider endpoint to return 401 first.
    
    # Option A: Modify the in-process provider mock to return 401 based on some header/flag.
    # Option B: Use respx and UNPATCH `_get_client` for this test?
    # Option C: Just rely on `ProviderClient` logic.
    
    # Let's try Option A: The provider mock doesn't currently validate tokens for expiration
    # (it just generates them).
    # However, `ProviderClient` raises `TokenExpiredError` if status is 401.
    # So we need the mock provider to return 401.
    
    # Let's add a temporary override or just Mock the `fetch_transactions_page` on the client?
    # No, we want to test the full loop in `sync.py`.
    
    # Easiest way: Mock `ProviderClient.fetch_transactions_page` to raise TokenExpiredError once,
    # then call original.
    # But `sync.py` instantiates `ProviderClient` locally.
    
    # Let's use `unittest.mock.patch` on `app.sync.ProviderClient`.
    
    from unittest.mock import MagicMock, patch
    
    conn = Connection(
        account_id=account_id,
        access_token_enc=encrypt_str("old_invalid_token"),
        refresh_token_enc=encrypt_str("rt_valid")
    )
    db.add(conn)
    db.commit()
    
    # We need to mock the `fetch_transactions_page` method of the instance created inside `run_sync`.
    # And also `refresh_access_token`.
    
    with patch("app.sync.ProviderClient") as MockProviderClient:
        # Create a mock instance
        mock_instance = MockProviderClient.return_value
        
        # Setup side_effect for fetch: First raise, then return data
        from app.provider_client import TokenExpiredError
        
        # Page data for success
        success_page = {
            "items": [{"id": "txn_ref_1", "amount": 500, "currency": "USD", "description": "Refreshed Txn", "posted_at": "2023-01-01T12:00:00"}],
            "next_cursor": None
        }
        
        mock_instance.fetch_transactions_page.side_effect = [
            TokenExpiredError("Expired"),
            success_page
        ]
        
        # Setup refresh return
        mock_instance.refresh_access_token.return_value = {
            "access_token": "new_refreshed_at",
            "refresh_token": "new_refreshed_rt", # Optional update
            "expires_in": 3600
        }
        
        # Run sync via API
        resp = client.post("/sync/run", json={"account_id": account_id})
        assert resp.status_code == 200
        stats = resp.json()["stats"]
        
        # Assertions
        assert mock_instance.refresh_access_token.called
        assert mock_instance.fetch_transactions_page.call_count == 2
        
        assert stats["inserted"] == 1
        
        # Check DB for updated tokens
        db.expire_all() # reload
        conn_updated = db.query(Connection).filter_by(account_id=account_id).first()
        # The stored token should be encrypted version of "new_refreshed_at"
        # We can't easily decrypt it without the key, but we can try decrypting it now.
        # Wait, encryption is deterministic only if salt is fixed? 
        # Fernet produces different ciphertext for same plaintext each time (IV).
        # We just decrypt and compare.
        from app.crypto import decrypt_str
        assert decrypt_str(conn_updated.access_token_enc) == "new_refreshed_at"
        assert decrypt_str(conn_updated.refresh_token_enc) == "new_refreshed_rt"
