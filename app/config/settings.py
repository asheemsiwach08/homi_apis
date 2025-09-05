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

    BASIC_APPLICATION_AGENT_USER_ID = os.getenv("BASIC_APPLICATION_AGENT_USER_ID", "")
    BASIC_APPLICATION_AGENT_API_KEY = os.getenv("BASIC_APPLICATION_AGENT_API_KEY", "")

    # Gupshup WhatsApp API Configuration
    GUPSHUP_API_TEMPLATE_URL = os.getenv("GUPSHUP_API_TEMPLATE_URL", "https://api.gupshup.io/wa/api/v1/template/msg")
    GUPSHUP_API_MSG_URL = os.getenv("GUPSHUP_API_MSG_URL", "https://api.gupshup.io/wa/api/v1/msg")
    GUPSHUP_API_KEY = os.getenv("GUPSHUP_API_KEY", "")
    GUPSHUP_SOURCE = os.getenv("GUPSHUP_SOURCE", "")

    # Multi-App Gupshup Configuration
    # App configurations are loaded dynamically from environment variables
    # Format: GUPSHUP_APP_{APP_NAME}_API_KEY and GUPSHUP_APP_{APP_NAME}_APP_ID
    @property
    def GUPSHUP_APPS(self) -> dict:
        """
        Load Gupshup app configurations from environment variables
        
        Expected environment variables:
        - GUPSHUP_APP_HOMI_API_KEY=your_homi_api_key
        - GUPSHUP_APP_HOMI_APP_ID=your_homi_app_id
        - GUPSHUP_APP_ORBIT_API_KEY=your_orbit_api_key
        - GUPSHUP_APP_ORBIT_APP_ID=your_orbit_app_id
        """
        apps = {}
        
        # Get all environment variables that start with GUPSHUP_APP_
        for key, value in os.environ.items():
            if key.startswith("GUPSHUP_APP_") and key.endswith("_API_KEY"):
                # Extract app name from key (e.g., GUPSHUP_APP_HOMI_API_KEY -> HOMI)
                app_name = key.replace("GUPSHUP_APP_", "").replace("_API_KEY", "")
                
                # Get corresponding app_id
                app_id_key = f"GUPSHUP_APP_{app_name}_APP_ID"
                app_id = os.getenv(app_id_key, "")
                
                # Get optional source for this app
                source_key = f"GUPSHUP_APP_{app_name}_SOURCE"
                source = os.getenv(source_key, self.GUPSHUP_SOURCE)
                
                if value and app_id:  # Both API key and app ID must be present
                    apps[app_name.lower()] = {
                        "api_key": value,
                        "app_id": app_id,
                        "source": source,
                        "app_name": app_name.lower()
                    }
        
        return apps
    
    def get_gupshup_config(self, app_name: str) -> dict:
        """
        Get Gupshup configuration for a specific app
        
        Args:
            app_name: Name of the app (case-insensitive)
            
        Returns:
            Dict with api_key, app_id, source, and app_name
            Falls back to default configuration if app not found
        """
        app_name_lower = app_name.lower()
        apps = self.GUPSHUP_APPS
        
        if app_name_lower in apps:
            return apps[app_name_lower]
        else:
            # Fallback to default configuration
            return {
                "api_key": self.GUPSHUP_API_KEY,
                "app_id": "",  # No default app_id
                "source": self.GUPSHUP_SOURCE,
                "app_name": "default"
            }

    # Gupshup WhatsApp Templates
    GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID = os.getenv("GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID", "")
    GUPSHUP_WHATSAPP_OTP_SRC_NAME = os.getenv("GUPSHUP_WHATSAPP_OTP_SRC_NAME", "HomiAi")

    GUPSHUP_LEAD_CREATION_TEMPLATE_ID = os.getenv("GUPSHUP_LEAD_CREATION_TEMPLATE_ID", "")
    GUPSHUP_LEAD_CREATION_SRC_NAME = os.getenv("GUPSHUP_LEAD_CREATION_SRC_NAME", "")

    GUPSHUP_LEAD_STATUS_TEMPLATE_ID = os.getenv("GUPSHUP_LEAD_STATUS_TEMPLATE_ID", "")
    GUPSHUP_LEAD_STATUS_SRC_NAME = os.getenv("GUPSHUP_LEAD_STATUS_SRC_NAME", "")
    
    # Supabase Configuration
    SUPABASE_ORBIT_URL = os.getenv("SUPABASE_ORBIT_URL")
    SUPABASE_ORBIT_SERVICE_ROLE_KEY = os.getenv("SUPABASE_ORBIT_SERVICE_ROLE_KEY")

    SUPABASE_HOMFINITY_URL = os.getenv("SUPABASE_HOMFINITY_URL")
    SUPABASE_HOMFINITY_SERVICE_ROLE_KEY = os.getenv("SUPABASE_HOMFINITY_SERVICE_ROLE_KEY")
    
    # Database Environment Configuration
    DEFAULT_DATABASE_ENVIRONMENT = os.getenv("DEFAULT_DATABASE_ENVIRONMENT", "orbit")  # 'orbit' or 'homfinity'
    
    # Environment-specific OTP Configuration (legacy support)
    SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("SUPABASE_HOMFINITY_URL"))  # Fallback for OTP storage
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_HOMFINITY_SERVICE_ROLE_KEY"))  # Fallback for OTP storage

    # OTP Configuration
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "3"))

    # WhatsApp Webhook Configuration
    # WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "homi_whatsapp_webhook_2024_secure_token_123")

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
