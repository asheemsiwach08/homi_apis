import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from the absolute path inside Docker container
load_dotenv(dotenv_path=Path("/app/.env"))  # Assumes WORKDIR /app in Dockerfile

class Settings:
    # Gupshup API Configuration
    GUPSHUP_API_KEY = os.getenv("GUPSHUP_API_KEY", "")
    GUPSHUP_SOURCE = os.getenv("GUPSHUP_SOURCE", "")
    GUPSHUP_TEMPLATE_ID = os.getenv("GUPSHUP_TEMPLATE_ID", "")
    GUPSHUP_SRC_NAME = os.getenv("GUPSHUP_SRC_NAME", "HomiAi")
    GUPSHUP_API_URL = os.getenv("GUPSHUP_API_URL", "https://api.gupshup.io/wa/api/v1/template/msg")

    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # OTP Configuration
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "3"))

settings = Settings()
