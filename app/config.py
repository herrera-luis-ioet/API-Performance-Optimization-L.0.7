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

    class Config:
        case_sensitive = True

settings = Settings()