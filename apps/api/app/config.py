from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
_DB_PATH = _ROOT_DIR / "voltron.db"

class Settings(BaseSettings):
    PROJECT_NAME: str = "VOLTRON AI Options Decision System"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    # Alpaca Credentials & Endpoints
    ALPACA_API_KEY: str = "PKTEST_DUMMY_KEY"
    ALPACA_SECRET_KEY: str = "SKTEST_DUMMY_SECRET"
    ALPACA_PAPER: bool = True
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"
    ALPACA_DATA_URL: str = "https://data.alpaca.markets"
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_DB_PATH}"
    
    # Options Intelligence MCP (Person 1) & Alpaca MCP
    USE_MOCK_QUANT: bool = False
    VOLTRON_MCP_URL: Optional[str] = "http://localhost:8001"
    ALPACA_MCP_URL: Optional[str] = "http://localhost:8002"
    
    # Autonomous Quant Mode (Dispatches directly to Alpaca when Risk Compiler passes)
    AUTONOMOUS_EXECUTION: bool = True

    # Google Gemini LLM Multi-Agent Reasoning
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.6-flash"
    
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
