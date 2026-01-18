import httpx
from app.settings import settings

class TokenExpiredError(Exception):
    """Raised when provider returns 401"""
    pass

class RateLimitedError(Exception):
    """Raised when provider returns 429"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after

class ProviderClient:
    def __init__(self):
        self.base_url = settings.PROVIDER_BASE_URL
        self.client_id = settings.PROVIDER_CLIENT_ID
        self.client_secret = settings.PROVIDER_CLIENT_SECRET
        self.timeout = settings.HTTP_TIMEOUT_SECONDS

    def _get_client(self):
        return httpx.Client(timeout=self.timeout)

    def exchange_code_for_token(self, code: str):
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        with self._get_client() as client:
            resp = client.post(f"{self.base_url}/token", data=data)
            resp.raise_for_status()
            return resp.json()

    def refresh_access_token(self, refresh_token: str):
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        with self._get_client() as client:
            resp = client.post(f"{self.base_url}/token", data=data)
            if resp.status_code == 401 or resp.status_code == 403:
                # If refresh token itself is expired/invalid
                raise TokenExpiredError("Refresh token expired or invalid")
            resp.raise_for_status()
            return resp.json()

    def fetch_transactions_page(self, account_id: str, access_token: str, cursor: str = None, rl: bool = False):
        params = {"account_id": account_id}
        if cursor:
            params["cursor"] = cursor
        if rl:
            params["rl"] = "true"
            
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with self._get_client() as client:
            resp = client.get(
                f"{self.base_url}/transactions", 
                params=params, 
                headers=headers
            )
            
            if resp.status_code == 401:
                raise TokenExpiredError("Access token expired")
            
            if resp.status_code == 429:
                retry_header = resp.headers.get("Retry-After", "1")
                try:
                    retry_after = int(retry_header)
                except ValueError:
                    retry_after = 1
                raise RateLimitedError(retry_after)
            
            resp.raise_for_status()
            return resp.json()
