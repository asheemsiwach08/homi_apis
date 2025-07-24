import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # API Configuration
    API_TITLE = "HOM-i"
    API_DESCRIPTION = "API for Whatsapp OTP Send, Verification,Lead Creation, Status retrieval, WhatsApp Integration, Email Processing & Disbursements"
    API_VERSION = "1.0.0"
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Basic Application API Configuration
    BASIC_APPLICATION_API_URL = os.getenv("BASIC_APPLICATION_API_URL", "")
    BASIC_APPLICATION_USER_ID = os.getenv("BASIC_APPLICATION_USER_ID", "")
    BASIC_APPLICATION_API_KEY = os.getenv("BASIC_APPLICATION_API_KEY", "")

    # Gupshup WhatsApp API Configuration
    GUPSHUP_API_URL = os.getenv("GUPSHUP_API_URL", "https://api.gupshup.io/wa/api/v1/msg")
    GUPSHUP_API_KEY = os.getenv("GUPSHUP_API_KEY", "")
    GUPSHUP_SOURCE = os.getenv("GUPSHUP_SOURCE", "")

    # Gupshup WhatsApp Templates
    GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID = os.getenv("GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID", "")
    GUPSHUP_WHATSAPP_OTP_SRC_NAME = os.getenv("GUPSHUP_WHATSAPP_OTP_SRC_NAME", "HomiAi")

    GUPSHUP_LEAD_CREATION_TEMPLATE_ID = os.getenv("GUPSHUP_LEAD_CREATION_TEMPLATE_ID", "")
    GUPSHUP_LEAD_CREATION_SRC_NAME = os.getenv("GUPSHUP_LEAD_CREATION_SRC_NAME", "")

    GUPSHUP_LEAD_STATUS_TEMPLATE_ID = os.getenv("GUPSHUP_LEAD_STATUS_TEMPLATE_ID", "")
    GUPSHUP_LEAD_STATUS_SRC_NAME = os.getenv("GUPSHUP_LEAD_STATUS_SRC_NAME", "")
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # OTP Configuration
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "3"))

    # WhatsApp Webhook Configuration
    WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "homi_whatsapp_webhook_2024_secure_token_123")

    # Loan Type Mapping
    LOAN_TYPE_MAPPING = {
        "home_loan": "HL",
        "home loan": "HL",
        "HOME LOAN": "HL",
        "Home Loan": "HL",
        "Home loan": "HL",
        "Home Loan": "HL",
        "HL": "HL",
        "Loan Against Property": "LAP",
        "Loan against property": "LAP",
        "Loan Against Property": "LAP",
        "loan_against_property": "LAP",
        "loan against property": "LAP",
        "LAP": "LAP",
        "lap": "LAP",
        "personal_loan": "PL",
        "business_loan": "BL",
        "car_loan": "CL",
        "education_loan": "EL"
    }

# Global settings instance
settings = Settings() 
