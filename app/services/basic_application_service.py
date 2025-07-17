import httpx
import requests
import os
import uuid
import time
import json
import hashlib
import hmac
import base64
from datetime import datetime
from fastapi import HTTPException
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qsl, urlencode
from app.config.settings import settings


class BasicApplicationService:
    """Service for handling Basic Application API integration"""
    
    def __init__(self):
        self.basic_api_url = os.getenv("BASIC_APPLICATION_API_URL")
        
        self.BASIC_APPLICATION_USER_ID = os.getenv("BASIC_APPLICATION_USER_ID")
        self.BASIC_APPLICATION_API_KEY = os.getenv("BASIC_APPLICATION_API_KEY")
        
        # Loan type mapping
        self.loan_type_mapping = settings.LOAN_TYPE_MAPPING
    
    def _format_date(self, date_str: str) -> str:
        """
        Format date string to ISO format with timezone
        
        Args:
            date_str: Date string in DD/MM/YYYY or YYYY-MM-DD format
            
        Returns:
            str: ISO formatted date string
        """
        try:
            # Handle DD/MM/YYYY format
            if '/' in date_str:
                day, month, year = date_str.split('/')
                date_obj = datetime(int(year), int(month), int(day))
            else:
                # Handle YYYY-MM-DD format
                date_obj = datetime.fromisoformat(date_str)
            
            # Format to ISO with timezone
            return date_obj.isoformat() + "Z"
        except Exception as e:
            print(f"Error formatting date {date_str}: {e}")
            # If parsing fails, return the original string
            return date_str
    
    def _prepare_payload(self, lead_data: Dict) -> Dict:
        """
        Prepare payload for Basic Application API
        
        Args:
            lead_data: Lead data from request
            
        Returns:
            Dict: Formatted payload for Basic Application API
        """
        # Format the date properly
        dob = lead_data.get("dob")
        if dob:
            dob = self._format_date(dob)
        
        return {
            "gender": lead_data.get("gender", "Male"),
            "dateOfBirth": dob,
            "annualIncome": 0,  # Use the same value as working curl
            "id": str(uuid.uuid4()),  # Generate random GUID
            "loanType": self.loan_type_mapping.get(lead_data.get("loan_type", ""), "HL"),
            "loanAmountReq": int(lead_data.get("loan_amount", 0)),
            "customerId": "234",  # Use the same value as working curl
            "firstName": lead_data.get("first_name", ""),
            "lastName": lead_data.get("last_name", ""),
            "mobile": lead_data.get("mobile_number", ""),
            "email": lead_data.get("email", ""),
            "pincode": lead_data.get("pin_code", ""),
            "city": "",  # Use the same value as working curl
            "district": "",  # Use the same value as working curl
            "state": "",  # Use the same value as working curl
            "createdFromPemId": "",  # Can be updated based on requirements
            "pan": lead_data.get("pan_number", ""),
            "remarks": "GOOD",  # Use the same value as working curl
            "applicationAssignedToRm": "",  # Can be updated based on requirements
            "isLeadPrefilled": True,  # Use boolean instead of string
            "includeCreditScore": True,  # Use boolean instead of string
            "loanTenure": lead_data.get("loan_tenure", 0)
        }

    def normalize_url(self, url):
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        query_params = urlencode((parse_qsl(parsed.query)))
        return f"{host}{path}?{query_params}" if query_params else f"{host}{path}"

    def generate_signature_headers(self, url, method, body=None):
        if not self.BASIC_APPLICATION_USER_ID or not self.BASIC_APPLICATION_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="BASIC_APPLICATION_USER_ID and BASIC_APPLICATION_API_KEY must be configured in environment variables"
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
    
    def create_lead(self, lead_data: Dict) -> Dict:
        """
        Create lead in Basic Application API
        
        Args:
            lead_data: Lead data from request
            
        Returns:
            Dict: Response from Basic Application API
            
        Raises:
            HTTPException: If API call fails
        """
        try:
            api_payload = self._prepare_payload(lead_data)
            
            if not self.basic_api_url:
                raise HTTPException(
                    status_code=500,
                    detail="Basic Application API URL not configured"
                )
            
            # Get signature headers
            api_url = f"{self.basic_api_url}/api/v1/NewApplication/FullfilmentByBasic"
            headers = self.generate_signature_headers(api_url, "POST", api_payload)
            print("--------------------------------------------------------------")
            print(headers)
            print("----- +++++++++++++++++++++++++++++++++ ------")
            print(api_payload)
            print("----- +++++++++++++++++++++++++++++++++ ------")
            print("--------------------------------------------------------------")
            response = requests.post(api_url, headers=headers, json=api_payload)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to create lead in Basic Application API: {response.text}"
                )
                    
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling Basic Application API: {str(e)}")
    
    async def get_lead_status(self, mobile_number: Optional[str] = None, basic_application_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get lead status from Basic Application API
        
        Args:
            mobile_number: Mobile number if available
            basic_application_id: Basic Application ID if available
            
        Returns:
            Optional[Dict]: Status response or None if not found
        """
        try:
            if not self.basic_api_url:
                raise HTTPException(
                    status_code=500,
                    detail="Basic Application API URL not configured"
                )
            
            # Import database service here to avoid circular imports
            from app.services.database_service import database_service
            
            # Initialize variables
            final_mobile_number = None
            final_basic_application_id = None
            
            # Scenario 1: Both mobile number and basic_application_id are provided
            if mobile_number and basic_application_id:
                final_mobile_number = mobile_number
                final_basic_application_id = basic_application_id
                
            # Scenario 2: Only mobile number is provided, fetch basic_application_id from database
            elif mobile_number and not basic_application_id:
                lead_data = database_service.get_lead_by_mobile(mobile_number)
                
                if lead_data and lead_data.get("basic_application_id"):
                    final_mobile_number = mobile_number
                    final_basic_application_id = lead_data.get("basic_application_id")
                else:
                    return None
                    
            # Scenario 3: Only basic_application_id is provided, fetch mobile number from database
            elif basic_application_id and not mobile_number:
                lead_data = database_service.get_lead_by_application_id(basic_application_id)
                
                if lead_data and lead_data.get("mobile_number"):
                    final_mobile_number = lead_data.get("mobile_number")
                    final_basic_application_id = basic_application_id
                else:
                    return None
                    
            # Scenario 4: Neither is provided
            else:
                return None
            
            # Now we have both mobile number and basic_application_id, call the GetActivity API
            if final_mobile_number and final_basic_application_id:
                api_url = f"{self.basic_api_url}/api/v1/Application/Activity/GetActivity/{final_basic_application_id}/{final_mobile_number}"
                headers = self.generate_signature_headers(api_url, "GET")
                
                response = requests.get(api_url, headers=headers)
                    
                if response.status_code == 200:
                    return response.json()
                else:
                    return None
            else:
                return None
                    
        except HTTPException:
            raise
        except Exception as e:
            return None 