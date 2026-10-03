import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env
load_dotenv(BASE_DIR / ".env")

class Settings:
    GNANI_API_KEY: str = os.getenv("GNANI_API_KEY", "")
    GNANI_BASE_URL: str = os.getenv("GNANI_BASE_URL", "https://api.vachana.ai")
    
    # Default PostgreSQL URL using psycopg (v3)
    raw_db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/gnani_audio_notes")
    if raw_db_url.startswith("postgresql://") and "+psycopg" not in raw_db_url:
        DATABASE_URL: str = raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    else:
        DATABASE_URL: str = raw_db_url

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "uploads")))
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "audio notes")
    def __init__(self):
        # Ensure uploads storage directory exists
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
