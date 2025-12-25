"""
Configuration management for the Inventory microservice.
Loads settings from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "inventory_db"
    
    # Application Configuration
    PORT: int = 8001
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Inventory Microservice"
    
    # CORS Configuration
    CORS_ORIGINS: list[str] = ["*"]
    
    # Observability Configuration
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831
    
    # Pagination Defaults
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
