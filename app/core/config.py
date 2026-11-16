from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""

    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"

    # Ollama LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TEMPERATURE: float = 0.2

    # Cloud Fallback (Gemini API)
    GEMINI_API_KEY: str = ""
    EXPO_PUBLIC_GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ENABLE_CLOUD_FALLBACK: bool = True

    # Voice (STT / TTS) Settings
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: Literal["cpu", "cuda"] = "cpu"
    TTS_RATE: int = 175
    TTS_VOLUME: float = 1.0

    # Safety Controls
    REQUIRE_CONFIRMATION_FOR_DESTRUCTIVE: bool = True
    AUTO_RECOVERY_MAX_RETRIES: int = 3
    MAX_TOOL_STEPS: int = 10

    # Database
    DATABASE_PATH: Path = DATA_DIR / "assistant.db"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
