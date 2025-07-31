"""
Processing service for bank application verification.
Handles signature generation and API communication.
"""

import hmac
import json
import uuid
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qsl, urlencode

from app.config.config import config


class ProcessingService:
    """Service for processing bank applications and generating API signatures."""
    
    def __init__(self):
        """Initialize the processing service."""
        self.basic_application_config = config.get_basic_application_config()
        self.BASIC_APPLICATION_USER_ID = self.basic_application_config.get('user_id')
        self.BASIC_APPLICATION_API_KEY = self.basic_application_config.get('api_token')
    
    def generate_signature_headers(self, url: str, method: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Generate signature headers for API authentication.
        
        Args:
            url: The API endpoint URL
            method: HTTP method (GET, POST, etc.)
            body: Request body (optional)
            
        Returns:
            Dictionary containing authentication headers
        """
        if not self.BASIC_APPLICATION_USER_ID or not self.BASIC_APPLICATION_API_KEY:
            raise ValueError(
                "BASIC_APPLICATION_USER_ID and BASIC_APPLICATION_API_KEY must be configured in environment variables"
            )
        
        body_str = json.dumps(body) if body else ""
        normalized = self.normalize_url(url)
        timestamp = int(datetime.now().timestamp())
        nonce = str(uuid.uuid4())
        body_md5 = hashlib.md5(body_str.encode()).hexdigest().lower() if body_str else ""
        message = self.BASIC_APPLICATION_USER_ID + str(timestamp) + normalized + method.lower() + nonce + body_md5
        signature = base64.b64encode(hmac.new(self.BASIC_APPLICATION_API_KEY.encode(), message.encode(), hashlib.sha512).digest()).decode()
        
        headers = {
            "accept": "text/plain",
            "Content-Type": "application/json-patch+json",
            "UserId": self.BASIC_APPLICATION_USER_ID,
            "CurrentTimestamp": str(timestamp),
            "Authorization": f"Signature {signature}",
            "Nonce": nonce
        }
        return headers
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for signature generation.
        
        Args:
            url: The URL to normalize
            
        Returns:
            Normalized URL string
        """
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        query_params = urlencode((parse_qsl(parsed.query)))
        return f"{host}{path}?{query_params}" if query_params else f"{host}{path}"
    
    def process_bank_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a bank application.
        
        Args:
            application_data: Application data to process
            
        Returns:
            Processed application data
        """
        # Add processing logic here
        return application_data


# Global instance
processing_service = ProcessingService()