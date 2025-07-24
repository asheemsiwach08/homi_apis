from app.config.config import config
from typing import Dict, Any, Optional
import logging
import requests
from app.services.processing import processing_service
from app.utils.timezone_utils import get_ist_timestamp
logger = logging.getLogger(__name__)

class BasicApplicationService:
    """Client for interacting with bank application APIs."""

    def __init__(self):
        """Initialize Bank API client."""
        self.basic_config = config.get_basic_application_config()
        self.base_url = self.basic_config['base_url']
        self.api_token = self.basic_config['api_token']
        self.timeout = self.basic_config['timeout']
        self.retry_attempts = self.basic_config['retry_attempts']
        
        # Debug configuration
        logger.info(f"Basic Application Service initialized:")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  API Token configured: {'Yes' if self.api_token else 'No'}")
        logger.info(f"  Timeout: {self.timeout}")
        
        if not self.base_url:
            logger.error("BASIC_API_BASE_URL is not configured")
        if not self.api_token:
            logger.error("BASIC_API_TOKEN is not configured")

    def verify_application(self, application_id: str):
        """Verify a basic application using the API."""

        if not application_id:
            logger.warning("No application ID provided for verification")
            return "No application ID provided"

        api_payload = {
                "BankAppIds": f"{application_id}"
            }

        endpoint = self.basic_config['endpoints'].get('verify_application', '/api/v1/Disbursement/GetDisbursementsByBankAppIds')
        url = f"{self.base_url}{endpoint}#?BankAppIds={application_id}"    #{application_id}"
        return self._make_api_request(url, "GET", api_payload)

    
    def _make_api_request(self, url: str, method: str, api_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        if not url:
            logger.error("Basic API URL not configured")
            return self._create_error_result("Basic API URL not configured")

        if not self.api_token:
            logger.error("Basic API token not configured")
            return self._create_error_result("Basic API token not configured")

        try:
            headers = {
                'accept': 'text/plain',
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }

            logger.debug(f"Making API request to: {url}")
            logger.debug(f"Headers: {headers}")
            
            # Use proper requests structure
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=api_payload, timeout=self.timeout)
            else:
                return self._create_error_result(f"Unsupported HTTP method: {method}")
            
            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    data = result.get("result", [])
                    if len(data) != 0:
                        logger.info("API request successful!")
                        return self._create_success_result(data)
                    else:
                        logger.info("No data found in the response")
                        return self._create_error_result("No data found in the response")
                except Exception as json_error:
                    logger.error(f"Failed to parse JSON response: {str(json_error)}")
                    return self._create_error_result(f"Failed to parse JSON response: {str(json_error)}")
            else:
                logger.error(f"API request failed with status {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return self._create_error_result(f"API request failed with status {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            error_msg = "Request timeout"
            logger.error(error_msg)
            return self._create_error_result(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(error_msg)
            return self._create_error_result(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return self._create_error_result(error_msg)
    
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

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create an error API response result.
        
        Args:
            error_message: Error message
            status_code: HTTP status code
        """
        return {
            'success': False,
            'data': None,
            'error': error_message,
            'timestamp': self._get_current_timestamp()
        }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in IST timezone.
        
        Returns:
            Current timestamp string in IST
        """
        return get_ist_timestamp()

    def batch_data_extraction(self, application_ids: list[str]) -> Dict[str, Dict[str, Any]]:
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
                print(f"Error in batch verification  {str(e)}")
                # logger.error("Error in batch verification", 
                #            application_id=app_id,
                #            error=str(e))
                results[app_id] = self._create_error_result(f"Batch verification error: {str(e)}")
        
        # logger.info("Batch verification completed", 
        #            total_applications=len(application_ids),
        #            successful_verifications=len([r for r in results.values() if r.get('success')]))
        
        return results 