from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_BASE_URL: str = "http://127.0.0.1:8000"
    DATABASE_URL: str = "sqlite:///./app.db"
    TOKEN_KEY: str = "dev-token-key-change-me"
    
    PROVIDER_BASE_URL: str = "http://127.0.0.1:8000/provider"
    PROVIDER_CLIENT_ID: str = "demo-client"
    PROVIDER_CLIENT_SECRET: str = "demo-secret"
    
    RATE_LIMIT_MAX_RETRIES: int = 5
    HTTP_TIMEOUT_SECONDS: int = 10

settings = Settings()
