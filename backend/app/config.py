"""
Configuration settings for QueryOptX Backend
"""
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "QueryOptX"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # PostgreSQL Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "queryoptx_db")
    
    # Execution safety limits
    MAX_EXECUTION_TIME_SECONDS: float = float(os.getenv("MAX_EXECUTION_TIME_SECONDS", "5.0"))
    MAX_RESULT_ROWS: int = int(os.getenv("MAX_RESULT_ROWS", "1000"))
    
    # Plan Cache settings
    PLAN_CACHE_MAX_SIZE: int = int(os.getenv("PLAN_CACHE_MAX_SIZE", "256"))
    
    # Cost model defaults
    SEQ_PAGE_COST: float = 1.0
    RANDOM_PAGE_COST: float = 4.0
    CPU_TUPLE_COST: float = 0.01
    CPU_INDEX_TUPLE_COST: float = 0.005
    CPU_OPERATOR_COST: float = 0.0025
    MEMORY_PAGE_COST: float = 0.05
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "*"]

settings = Settings()
