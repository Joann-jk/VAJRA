"""Application settings loader.

Loads environment variables from a .env file and exposes them via `settings`.
"""
from pathlib import Path
import os
from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    # try to load from working directory as a fallback
    load_dotenv()


class Settings:
    """Simple settings container. Add more values as needed."""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")


settings = Settings()
