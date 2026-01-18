from app.models import Connection, OAuthState
from app.crypto import decrypt_str
from datetime import timedelta
from app.db import utcnow

def test_connect_flow(client, db):
    # 1. Start
    account_id = "test_user_1"
    resp = client.post("/connect/start", json={"account_id": account_id})
    assert resp.status_code == 200
    data = resp.json()
    authorize_url = data["authorize_url"]
    state = data["state"]
    
    assert "state=" + state in authorize_url
    assert "client_id=demo-client" in authorize_url
    
    # Check DB state
    state_row = db.query(OAuthState).filter_by(state=state).first()
    assert state_row is not None
    assert state_row.account_id == account_id
    
    # 2. Mock 'Authorize' at provider
    # Extract params from authorize_url
    # In integration test, we call the provider endpoint directly since we wired it up.
    # authorize_url is http://127.0.0.1:8000/provider/authorize...
    # We can just request the path part.
    from urllib.parse import urlparse
    parsed = urlparse(authorize_url)
    path_with_query = f"{parsed.path}?{parsed.query}"
    
    auth_resp = client.get(path_with_query)
    assert auth_resp.status_code == 200
    redirect_to = auth_resp.json()["redirect_to"]
    
    # 3. Callback
    # redirect_to is .../connect/callback?code=...&state=...
    parsed_cb = urlparse(redirect_to)
    path_cb = f"{parsed_cb.path}?{parsed_cb.query}"
    
    cb_resp = client.get(path_cb)
    assert cb_resp.status_code == 200
    assert cb_resp.json()["status"] == "connected"
    
    # Verify state removed logic
    # In real request, session is committed. In test client, it depends.
    # Since we use same session dependency override? Actually conftest uses a separate session fixture
    # but the app dependency override yields that same session. So changes should be visible.
    state_row_deleted = db.query(OAuthState).filter_by(state=state).first()
    assert state_row_deleted is None
    
    # 4. Verify DB
    conn = db.query(Connection).filter_by(account_id=account_id).first()
    assert conn is not None
    assert decrypt_str(conn.access_token_enc).startswith("at_")
    assert decrypt_str(conn.refresh_token_enc).startswith("rt_")

def test_expired_state(client, db):
    # Manually insert expired state
    expired_state = "expired-state-uuid"
    db.add(OAuthState(
        state=expired_state,
        account_id="expired_user",
        expires_at=utcnow() - timedelta(minutes=1)
    ))
    db.commit()
    
    resp = client.get(f"/connect/callback?code=fake&state={expired_state}")
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()
    
    # Verify deleted
    assert db.query(OAuthState).filter_by(state=expired_state).first() is None
