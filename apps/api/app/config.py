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
    
    # Autonomous Quant Mode & Autonomy Spectrum
    AUTONOMOUS_EXECUTION: bool = True
    AUTONOMY_LEVEL: str = "GUARDED_AUTONOMOUS"

    # Multi-Provider LLM Gateway (Gemini, OpenAI, Groq, Anthropic, DeepSeek, Ollama, Custom)
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None

    # Groq Cloud (Ultra-Fast LPUs)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Anthropic Claude
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-20241022"

    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Local Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    
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
