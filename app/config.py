import os
from pathlib import Path


DATA_PATH = Path(r"C:\Users\memeo\Downloads\entities.ftm.json")
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sanctions.db"
BATCH_SIZE = 5000
TARGET_ONLY = True

OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT: int = 60
