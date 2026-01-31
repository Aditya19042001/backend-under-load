from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "load-testing-backend"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/loadtest"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Downstream service
    DOWNSTREAM_SERVICE_URL: str = "http://downstream-service:8001"
    DOWNSTREAM_TIMEOUT: int = 30
    
    # Performance
    WORKER_COUNT: int = 4
    MAX_CONNECTIONS: int = 100
    
    # Feature flags
    ENABLE_CIRCUIT_BREAKER: bool = False
    ENABLE_RATE_LIMITING: bool = False
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
