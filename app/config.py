from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "API Performance Optimization"
    API_V1_STR: str = "/api/v1"
    
    # Authentication settings
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # Cache settings
    REDIS_URL: Optional[str] = None
    CACHE_EXPIRE_IN_SECONDS: int = 60 * 5  # 5 minutes
    
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = 100  # Number of requests allowed
    RATE_LIMIT_WINDOW: int = 60  # Time window in seconds
    RATE_LIMIT_ENABLED: bool = True  # Enable/disable rate limiting

    class Config:
        case_sensitive = True

settings = Settings()
