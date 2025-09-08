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
    # Format: {APP_NAME}_GUPSHUP_API_KEY, {APP_NAME}_GUPSHUP_APP_ID and {APP_NAME}_GUPSHUP_APP_NAME
    @property
    def GUPSHUP_APPS(self) -> dict:
        """
        Load Gupshup app configurations from environment variables
        
        Expected environment variables:
        - BASICHOMELOAN_GUPSHUP_API_KEY=your_basichomeloan_api_key
        - BASICHOMELOAN_GUPSHUP_APP_ID=your_basichomeloan_app_id
        - BASICHOMELOAN_GUPSHUP_APP_NAME=your_basichomeloan_app_name
        - IRABYBASIC_GUPSHUP_API_KEY=your_irabybasic_api_key
        - IRABYBASIC_GUPSHUP_APP_ID=your_irabybasic_app_id
        - IRABYBASIC_GUPSHUP_APP_NAME=your_irabybasic_app_name
        """
        apps = {}
        
        # Handle new format: {APP_NAME}_GUPSHUP_APP_ID, {APP_NAME}_GUPSHUP_API_KEY and {APP_NAME}_GUPSHUP_APP_NAME
        for key, value in os.environ.items():
            if key.endswith("_GUPSHUP_APP_ID") and value:
                # Extract app name from key (e.g., BASICHOMELOAN_GUPSHUP_APP_ID -> BASICHOMELOAN)
                app_name = key.replace("_GUPSHUP_APP_ID", "")
                
                # Get corresponding API key
                api_key_key = f"{app_name}_GUPSHUP_API_KEY"
                api_key = os.getenv(api_key_key, self.GUPSHUP_API_KEY)
                
                # Get corresponding app_name (Gupshup app name)
                app_name_key = f"{app_name}_GUPSHUP_APP_NAME"
                gupshup_app_name = os.getenv(app_name_key, "")
                
                # Get optional source for this app
                source_key = f"{app_name}_GUPSHUP_SOURCE"
                source = os.getenv(source_key, self.GUPSHUP_SOURCE)
                
                # For new format, we need at least app_id and api_key
                # app_name is optional but recommended
                if value and api_key:  # Both app ID and API key must be present
                    apps[app_name.lower()] = {
                        "api_key": api_key,
                        "app_id": value,
                        "app_name": gupshup_app_name if gupshup_app_name else app_name.lower(),
                        "source": source,
                        "internal_name": app_name.lower()
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
