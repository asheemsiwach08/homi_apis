"""
Configuration management for the application.
Handles environment variables from .env file.
"""

import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for the application."""
    
    def __init__(self):
        """Initialize configuration manager."""
        load_dotenv()
        logger.info("Configuration loaded from environment variables")
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value from environment variables.
        
        Args:
            key: Environment variable name
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return os.getenv(key, default)
    
    # TODO: Remove this method once Gmail is implemented and working
    def get_zoho_config(self) -> Dict[str, Any]:
        """Get Zoho Mail configuration."""
        return {
            'email': self.get('ZOHO_EMAIL'),
            'password': self.get('ZOHO_PASSWORD'),
            'imap_server': self.get('ZOHO_IMAP_SERVER', 'imap.zoho.com'),
            'imap_port': int(self.get('ZOHO_IMAP_PORT', '993')),
            'folder': self.get('EMAIL_FOLDER', 'INBOX'),
            'search_criteria': self.get('EMAIL_SEARCH_CRITERIA', 'ALL'),
            'max_emails_per_batch': int(self.get('MAX_EMAILS_PER_BATCH', '50')),
            'months_back': int(self.get('EMAIL_MONTHS_BACK', '3')),
            'start_months_back': int(self.get('EMAIL_START_MONTHS_BACK', '4')),
            'end_months_back': int(self.get('EMAIL_END_MONTHS_BACK', '3'))
        }

    def get_gmail_config(self) -> Dict[str, Any]:
        """Get Zoho Mail configuration."""
        return {
            'email': self.get('GMAIL_ADDRESS'),
            'password': self.get('GMAIL_PASSWORD'),
            'imap_server': self.get('GMAIL_IMAP_SERVER', 'imap.gmail.com'),
            'imap_port': int(self.get('GMAIL_IMAP_PORT', '993')),
            'folder': self.get('EMAIL_FOLDER', 'INBOX'),
            'search_criteria': self.get('EMAIL_SEARCH_CRITERIA', 'ALL'),
            'max_emails_per_batch': int(self.get('MAX_EMAILS_PER_BATCH', '50')),
            'months_back': int(self.get('EMAIL_MONTHS_BACK', '3')),
            'start_months_back': int(self.get('EMAIL_START_MONTHS_BACK', '4')),
            'end_months_back': int(self.get('EMAIL_END_MONTHS_BACK', '3'))
        }

    def get_alert_email_config(self) -> Dict[str, Any]:
        """Get alert email configuration."""
        return {
            'sender_email': self.get('ALERT_EMAIL_SENDER_ADDRESS'),
            'sender_password': self.get('ALERT_EMAIL_PASSWORD'),
            'smtp_server': self.get('ALERT_EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(self.get('ALERT_IMAP_SMTP_PORT', '587')),
            'recipient_emails': self.get('ALERT_EMAIL_RECEIVER_ADDRESS')
        }
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return {
            'api_key': self.get('OPENAI_API_KEY'),
            'model': self.get('OPENAI_MODEL', 'gpt-4'),
            'max_tokens': int(self.get('OPENAI_MAX_TOKENS', '2000')),
            'temperature': float(self.get('OPENAI_TEMPERATURE', '0.0'))
        }
    
    def get_basic_application_config(self) -> Dict[str, Any]:
        """Get Basic API configuration."""
        return {
            'base_url': self.get('BASIC_API_BASE_URL'),
            'api_token': self.get('BASIC_API_TOKEN'),
            'user_id': self.get('BASIC_APPLICATION_USER_ID'),
            'timeout': int(self.get('BASIC_API_TIMEOUT', '30')),
            'retry_attempts': int(self.get('MAX_RETRIES', '3')),
            'endpoints': {
                'verify_application': self.get('BASIC_API_ENDPOINT', '/api/v1/Disbursement/GetDisbursementsByBankAppIds')
            }
        }
    
    def get_amazon_s3_config(self) -> Dict[str, Any]:
        """Get Amazon S3 configuration."""
        return {
            'bucket_name': self.get('S3_BUCKET'),
            'access_key_id': self.get('AWS_ACCESS_KEY_ID'),
            'secret_access_key': self.get('AWS_SECRET_ACCESS_KEY'),
            'region_name': self.get('AWS_REGION')
        }
    
    # def get_sheets_config(self) -> Dict[str, Any]:
    #     """Get Google Sheets configuration."""
    #     return {
    #         'credentials_file': self.get('GOOGLE_CREDENTIALS_FILE') or self.get('GOOGLE_SHEETS_CREDENTIALS_FILE'),
    #         'spreadsheet_id': self.get('GOOGLE_SPREADSHEET_ID') or self.get('GOOGLE_SHEETS_SPREADSHEET_ID', '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'),
    #         'range': self.get('GOOGLE_WORKSHEET_NAME') or self.get('GOOGLE_SHEETS_RANGE', 'Sheet1!A:Z'),
    #         'update_batch_size': int(self.get('SHEETS_UPDATE_BATCH_SIZE', '10')),
    #         # Support for separate historical and live sheets
    #         'historical_spreadsheet_id': self.get('GOOGLE_HISTORICAL_SPREADSHEET_ID'),
    #         'historical_worksheet_name': self.get('GOOGLE_HISTORICAL_WORKSHEET_NAME', 'Historical_Disbursements'),
    #         'live_spreadsheet_id': self.get('GOOGLE_LIVE_SPREADSHEET_ID'),
    #         'live_worksheet_name': self.get('GOOGLE_LIVE_WORKSHEET_NAME', 'Live_Disbursements'),
    #     }
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return {
            'log_level': self.get('LOG_LEVEL', 'INFO'),
            'batch_size': int(self.get('BATCH_SIZE', '10')),
            'processing_delay': int(self.get('PROCESSING_DELAY', '5')),
            'max_retries': int(self.get('MAX_RETRIES', '3')),
            'months_back': int(self.get('EMAIL_MONTHS_BACK', '3')),
            'start_months_back': int(self.get('EMAIL_START_MONTHS_BACK', '4')),
            'end_months_back': int(self.get('EMAIL_END_MONTHS_BACK', '3')),
            'save_attachments': self.get('SAVE_ATTACHMENTS', 'false').lower() == 'true'
        }
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present."""
        required_configs = [
            ('ZOHO_EMAIL', 'Zoho email address'),
            ('ZOHO_PASSWORD', 'Zoho password'),
            ('OPENAI_API_KEY', 'OpenAI API key'),
            ('BASIC_API_BASE_URL', 'Basic API base URL'),
            ('BASIC_API_TOKEN', 'Basic API token'),
            ('BASIC_APPLICATION_USER_ID', 'Basic application user ID')
            # ('GOOGLE_SHEETS_CREDENTIALS_FILE', 'Google Sheets credentials file'),
            # ('GOOGLE_SHEETS_SPREADSHEET_ID', 'Google Sheets spreadsheet ID')
        ]
        
        missing_configs = []
        for key, description in required_configs:
            if not self.get(key):
                missing_configs.append(f"{key} ({description})")
        
        if missing_configs:
            logger.error(f"Missing required configuration: {missing_configs}")
            return False
            
        logger.info("Configuration validation passed")
        return True


# Global configuration instance
config = Config() 