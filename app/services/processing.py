"""
Processing service for bank application verification.
Handles signature generation and API communication.
"""
import hmac
import json
import uuid
import base64
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qsl, urlencode

from app.config.config import config

logger = logging.getLogger(__name__)


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

class AmazonS3Service:
    """Service for processing Amazon S3."""

    def __init__(self):
        import boto3

        self.amazon_s3_config = config.get_amazon_s3_config()
        self.s3_bucket = self.amazon_s3_config.get('bucket_name')
        self.access_key_id = self.amazon_s3_config.get('access_key_id')
        self.secret_access_key = self.amazon_s3_config.get('secret_access_key')
        self.region_name = self.amazon_s3_config.get('region_name')

        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region_name,
            )
        except Exception as e:
            logger.warning(f"Amazon S3 client initialization failed: {str(e)}")
            self.s3_client = None


    def upload_file(self, file_path: str, key: str) -> bool:
        """Upload a file to Amazon S3."""
        try:
            self.s3_client.upload_file(file_path, self.s3_bucket, key)
            return True
        except Exception as e:
            logger.warning(f"Error uploading file to Amazon S3: {str(e)}")
            return False

    def upload_fileObject(self, file_object: bytes, key: str) -> bool:
        """Upload a file object to Amazon S3."""
        try:
            self.s3_client.upload_fileobj(file_object, self.s3_bucket, key)
            return True
        except Exception as e:
            logger.warning(f"Error uploading file object to Amazon S3: {str(e)}")
            return False

    def generate_presigned_url(self, key: str) -> str:
        """Generate a presigned URL for a file in Amazon S3."""
        try:
            return self.s3_client.generate_presigned_url('get_object', Params={'Bucket': self.s3_bucket, 'Key': key}, ExpiresIn=1800)
        except Exception as e:
            logger.warning(f"Error generating presigned URL for file in Amazon S3: {str(e)}")
            return None

########################################## Global Instances ##########################################            

# Global instance - Processing Service
processing_service = ProcessingService()

# Global instance - Amazon S3 Service
s3_service = AmazonS3Service()