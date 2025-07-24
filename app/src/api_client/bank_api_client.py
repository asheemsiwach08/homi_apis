"""
Bank API client for verifying bank applications.
"""

import httpx
import time
from typing import Dict, Any, Optional
import logging

from app.config.config import config

logger = logging.getLogger(__name__)


class BankAPIClient:
    """Client for interacting with bank application APIs."""
    
    def __init__(self):
        """Initialize Bank API client."""
        self.bank_config = config.get_bank_api_config()
        self.base_url = self.bank_config['base_url']
        self.api_key = self.bank_config['api_key']
        self.timeout = self.bank_config['timeout']
        self.retry_attempts = self.bank_config['retry_attempts']
        
    def verify_application(self, application_id: str) -> Dict[str, Any]:
        """Verify a bank application using the API.
        
        Args:
            application_id: Bank application ID to verify
            
        Returns:
            Verification results dictionary
        """
        if not application_id:
            logger.warning("No application ID provided for verification")
            return self._create_error_result("No application ID provided")
        
        endpoint = self.bank_config['endpoints'].get('verify_application', '/api/v1/applications/{application_id}/verify')
        url = f"{self.base_url}{endpoint.format(application_id=application_id)}"
        
        return self._make_api_request(url, "GET")
    
    def get_application_details(self, application_id: str) -> Dict[str, Any]:
        """Get detailed information about a bank application.
        
        Args:
            application_id: Bank application ID
            
        Returns:
            Application details dictionary
        """
        if not application_id:
            logger.warning("No application ID provided for details retrieval")
            return self._create_error_result("No application ID provided")
        
        endpoint = self.bank_config['endpoints'].get('get_application', '/api/v1/applications/{application_id}')
        url = f"{self.base_url}{endpoint.format(application_id=application_id)}"
        
        return self._make_api_request(url, "GET")
    
    def _make_api_request(self, url: str, method: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an API request with retry logic.
        
        Args:
            url: API endpoint URL
            method: HTTP method (GET, POST, etc.)
            data: Request data (for POST/PUT requests)
            
        Returns:
            API response dictionary
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        for attempt in range(self.retry_attempts):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    if method.upper() == "GET":
                        response = client.get(url, headers=headers)
                    elif method.upper() == "POST":
                        response = client.post(url, headers=headers, json=data)
                    elif method.upper() == "PUT":
                        response = client.put(url, headers=headers, json=data)
                    else:
                        return self._create_error_result(f"Unsupported HTTP method: {method}")
                    
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            logger.info("API request successful", 
                                      url=url, 
                                      status_code=response.status_code)
                            return self._create_success_result(result)
                        except Exception as e:
                            logger.warning("Failed to parse JSON response", 
                                         url=url, 
                                         error=str(e))
                            return self._create_success_result({"raw_response": response.text})
                    
                    elif response.status_code == 404:
                        logger.warning("Application not found", 
                                     url=url, 
                                     status_code=response.status_code)
                        return self._create_error_result("Application not found", status_code=404)
                    
                    elif response.status_code == 401:
                        logger.error("Authentication failed", 
                                   url=url, 
                                   status_code=response.status_code)
                        return self._create_error_result("Authentication failed", status_code=401)
                    
                    else:
                        logger.error("API request failed", 
                                   url=url, 
                                   status_code=response.status_code,
                                   response_text=response.text)
                        return self._create_error_result(f"API request failed with status {response.status_code}")
                        
            except httpx.TimeoutException:
                logger.warning("API request timeout", 
                             url=url, 
                             attempt=attempt + 1,
                             max_attempts=self.retry_attempts)
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    return self._create_error_result("Request timeout after all retry attempts")
                    
            except httpx.RequestError as e:
                logger.error("API request error", 
                           url=url, 
                           error=str(e),
                           attempt=attempt + 1)
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return self._create_error_result(f"Request error: {str(e)}")
                    
            except Exception as e:
                logger.error("Unexpected error in API request", 
                           url=url, 
                           error=str(e))
                return self._create_error_result(f"Unexpected error: {str(e)}")
        
        return self._create_error_result("All retry attempts failed")
    
    def _create_success_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a successful API response result.
        
        Args:
            data: API response data
            
        Returns:
            Success result dictionary
        """
        return {
            'success': True,
            'data': data,
            'error': None,
            'timestamp': self._get_current_timestamp()
        }
    
    def _create_error_result(self, error_message: str, status_code: Optional[int] = None) -> Dict[str, Any]:
        """Create an error API response result.
        
        Args:
            error_message: Error message
            status_code: HTTP status code (optional)
            
        Returns:
            Error result dictionary
        """
        result = {
            'success': False,
            'data': None,
            'error': error_message,
            'timestamp': self._get_current_timestamp()
        }
        
        if status_code:
            result['status_code'] = status_code
            
        return result
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp string
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def batch_verify_applications(self, application_ids: list[str]) -> Dict[str, Dict[str, Any]]:
        """Verify multiple applications in batch.
        
        Args:
            application_ids: List of application IDs to verify
            
        Returns:
            Dictionary mapping application IDs to verification results
        """
        results = {}
        
        for app_id in application_ids:
            try:
                result = self.verify_application(app_id)
                results[app_id] = result
            except Exception as e:
                logger.error("Error in batch verification", 
                           application_id=app_id,
                           error=str(e))
                results[app_id] = self._create_error_result(f"Batch verification error: {str(e)}")
        
        logger.info("Batch verification completed", 
                   total_applications=len(application_ids),
                   successful_verifications=len([r for r in results.values() if r.get('success')]))
        
        return results 