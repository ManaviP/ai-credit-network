from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Community Credit Network"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # Supabase (optional)
    SUPABASE_URL: str = "https://zdwedezftuzyppkslxhr.supabase.co"
    SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpkd2VkZXpmdHV6eXBwa3NseGhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAxOTA1MTQsImV4cCI6MjA1NTU1MDUxNH0.sb_publishable_GdvNrXJpowDfXkA90b-zKw_X8PZ86o8"
    
    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    
    # Redis
    REDIS_URL: str
    
    # RabbitMQ
    RABBITMQ_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # SMS
    SMS_API_KEY: str = ""
    SMS_API_URL: str = ""
    SMS_SENDER_ID: str = "CREDIT"
    
    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Blockchain (Phase 3 - stub)
    WEB3_PROVIDER_URL: str = ""
    IPFS_GATEWAY: str = "https://ipfs.io/ipfs/"
    
    # Trust Score Thresholds
    COLD_START_SCORE: int = 300
    STABLE_CLUSTER_THRESHOLD: int = 700
    GROWING_CLUSTER_THRESHOLD: int = 500
    
    # Scoring Weights
    WEIGHT_REPAYMENT: float = 0.40
    WEIGHT_TENURE: float = 0.20
    WEIGHT_VOUCH_COUNT: float = 0.15
    WEIGHT_VOUCHER_RELIABILITY: float = 0.15
    WEIGHT_LOAN_VOLUME: float = 0.10
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
