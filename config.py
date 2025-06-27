import os
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

class Settings:
    # Gupshup API Configuration
    GUPSHUP_API_KEY = os.getenv("GUPSHUP_API_KEY", "")
    GUPSHUP_SOURCE = os.getenv("GUPSHUP_SOURCE", "")
    GUPSHUP_TEMPLATE_ID = os.getenv("GUPSHUP_TEMPLATE_ID", "")
    GUPSHUP_SRC_NAME = os.getenv("GUPSHUP_SRC_NAME", "HomiAi")
    GUPSHUP_API_URL = os.getenv("GUPSHUP_API_URL", "https://api.gupshup.io/wa/api/v1/template/msg")
    
    # OTP Configuration
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "3"))

settings = Settings() 