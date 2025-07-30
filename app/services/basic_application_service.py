import httpx
import requests
import os
import uuid
import time
import json
import hashlib
import hmac
import base64
import logging
from datetime import datetime
from fastapi import HTTPException
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qsl, urlencode
from app.config.settings import settings

logger = logging.getLogger(__name__)


class BasicApplicationService:
    """Service for handling Basic Application API integration"""
    
    def __init__(self):
        self.basic_api_url = os.getenv("BASIC_APPLICATION_API_URL")
        
        self.BASIC_APPLICATION_USER_ID = os.getenv("BASIC_APPLICATION_USER_ID")
        self.BASIC_APPLICATION_API_KEY = os.getenv("BASIC_APPLICATION_API_KEY")

        self.BASIC_APPLICATION_AGENT_USER_ID = os.getenv("BASIC_APPLICATION_AGENT_USER_ID")
        self.BASIC_APPLICATION_AGENT_API_KEY = os.getenv("BASIC_APPLICATION_AGENT_API_KEY")
        
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
            logger.error(f"Error formatting date {date_str}: {e}")
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

    # Detailed Leads Creation API Payload - CreateFBBByBasicUser
    def _prepare_FBB_by_basic_user_payload(self, lead_data: Dict) -> Dict:
        """
        Prepare FBB by basic user payload for Basic Application API
        
        Args:
            lead_data: Lead data from request
            
        Returns:
            Dict: Formatted payload for Basic Application API
        """
        # Format the date properly
        dob = lead_data.get("dob")
        if dob:
            dob = self._format_date(dob)
        
        return {"annualIncome":0,
                "applicationAssignedToRm": "2762f5b5-ecdc-4826-b003-f332b658e6f4",
                "city": lead_data.get("city", ""),
                "createdFromPemId": "string", 
                "creditScore": lead_data.get("creditScore", 0),
                "creditScoreTypeId": "string", 
                "customerId": "234", 
                "dateOfBirth": lead_data.get("dateOfBirth", ""),  
                "district": lead_data.get("district", ""),
                "email": lead_data.get("email", ""),
                "firstName": lead_data.get("firstName", ""),
                "gender": lead_data.get("gender", ""),
                "id": "6749d3e6-0c69-4148-a200-667c165ab18c", 
                "includeCreditScore": True,
                "isLeadPrefilled": True,
                "lastName": lead_data.get("lastName", ""),
                "loanAmountReq": lead_data.get("loanAmountReq", 0),
                "loanTenure": lead_data.get("loanTenure", 0),
                "loanType": lead_data.get("loanType", "HL"),
                "mobile": lead_data.get("mobile", ""),
                "pan": lead_data.get("pan", ""),
                "pincode": lead_data.get("pincode", "126102"),
                "qrShortCode": "BAE000247",
                "remarks":"good", 
                "state": lead_data.get("state", "")}

    # Detailed Leads Creation API Payload - SelfFullfilment
    def _prepare_self_fullfilment_payload(self, lead_data: Dict) -> Dict:
        """
        Prepare self fullfilment payload for Basic Application API
        
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
                "annualIncome": lead_data.get("annualIncome", 0),
                "city": lead_data.get("city", ""),
                "coBorrowerIncome": lead_data.get("coBorrowerIncome", 0),
                "dateOfBirth": lead_data.get("dateOfBirth", ""),
                "district": lead_data.get("district", ""),
                "documents": [],
                "email": lead_data.get("email", ""),
                "existingEmis": lead_data.get("existingEmis", ""),
                "firstName": lead_data.get("firstName", ""),
                "gender": lead_data.get("gender", ""),
                "id": lead_data.get("applicationId", ""),
                "lastName": lead_data.get("lastName", ""),
                "loanAmountReq": lead_data.get("loanAmountReq", 0),
                "loanType": lead_data.get("loanType", "HL"),
                "mobile": lead_data.get("mobile", ""),
                "pincode": lead_data.get("pincode", ""),
                "professionId": "34e544e6-1e22-49f4-a56a-44c14a32b484", # TODO: Get it my mapping(to be done)
                "professionName": "Salaried", # TODO: Get it my mapping(to be done)
                "state": lead_data.get("state", ""),
                "selfCompanyTypeName": "",
                "pan": lead_data.get("pan", ""),
                "canCustomerUploadDocuments": False,
                "isOsvByConsultantAvailable": False,
                "isLeadPrefilled": lead_data.get("isLeadPrefilled", False),
                "includeCreditScore": lead_data.get("includeCreditScore", False),
                "recentCreditReportExists": False,
                "salaryCreditModeId": "ef70c7ce-577a-4302-a485-adccdf31968d", # TODO: Get it my mapping(to be done)
                "loanTenure": lead_data.get("loanTenure", 0),
                "isPropertyIdentified": False,
                "isReferralLead": False,
                "propertyDistrict": "",
                "propertyPincode": "",
                "builderId": "",
                "projectId": "",
                "towerId": "",
                "builderName": "",
                "propertyProjectName": "",
                "towerName": "",
                "creditScoreTypeId": "string",
                "creditScoreTypeName": "",
                "creditScore": 0,
                "creditScoreStatus": "",
                "isVistedNextPage": True,
                "manualCreditScore": 0,
                "salaryCreditModeName": "",
                "selfCompanyTypeId": "",
                "companyName": "",
                "propertyTypeId": "",
                "propertyValue": "",
                "loanUsageTypeId": "",
                "aggrementTypeId": "",
                "towerUnitType": ""
            }

# {"aggrementTypeId": "",
#                 "annualIncome":lead_data.get("annual_income", 0),
#                 "applicationAssignedToRm": lead_data.get("applicationAssignedToRm", ""), 
#                 "builderId": "", 
#                 "builderName": "", 
#                 "city": lead_data.get("city", ""),
#                 "coBorrowerIncome": "", 
#                 "companyId": "",
#                 "companyName": "", 
#                 "createdFromPemId": "",
#                 "creditScore": lead_data.get("credit_score", 0),
#                 "creditScoreTypeId": "",
#                 "customerId": lead_data.get("customerId", ""),
#                 "dateOfBirth": lead_data.get("date_of_birth", ""),
#                 "district": lead_data.get("district", ""),
#                 "email": lead_data.get("email", ""),
#                 "existingEmis": lead_data.get("existingEmis", ""),
#                 "firstName": lead_data.get("first_name", ""),
#                 "gender": lead_data.get("gender", ""),
#                 "id": lead_data.get("id", "6a645ede-de6f-4bf4-8e05-0830b7dafaaf"), 
#                 "includeCreditScore": True,
#                 "isLeadPrefilled": lead_data.get("isLeadPrefilled", False), 
#                 "isPropertyIdentified": "",
#                 "lastName": lead_data.get("last_name", ""),
#                 "loanAmountReq": lead_data.get("loan_amount_req", 0),
#                 "loanTenure": lead_data.get("loan_tenure", 0),
#                 "loanType": lead_data.get("loan_type", "HL"),
#                 "loanUsageTypeId": "",
#                 "mobile": lead_data.get("mobile", ""),
#                 "pan": lead_data.get("pan", ""),
#                 "pincode": lead_data.get("pincode", "126102"),
#                 "professionId": "714624ae-b86f-4ffc-a710-389d6905ddd9",  ## TODO: Get it from YD Poonia
#                 "professionName": "Private", ## TODO: Get it from YD Poonia
#                 "projectId": "",
#                 "propertyAddress": "",
#                 "propertyCity": "",
#                 "propertyDistrict": "",
#                 "propertyPincode": "",
#                 "propertyProjectName": "",
#                 "propertyState": "",
#                 "propertyTypeId": "",
#                 "propertyValue": "",
#                 "qrShortCode": "BAE000247",
#                 "remarks":"",
#                 "salaryCreditModeId": "",
#                 "selfCompanyTypeId": "",
#                 "selfCompanyTypeName": "",
#                 "state": lead_data.get("state", ""),
#                 "towerId": "",
#                 "towerName": "",
#                 "towerUnitType": "",
#                 }

    # Book Appointment Creation API Payload - CreateTaskOrComment
    def _prepare_book_appointment_payload(self, lead_data: Dict) -> Dict:
        """
        Prepare book appointment payload for Basic Application API
        
        Args:
            lead_data: Lead data from request
            
        Returns:
            Dict: Formatted payload for Basic Application API
        """
        # Format the dueDate properly with comprehensive date/time parsing
        date = lead_data.get("date", "")
        time = lead_data.get("time", "")
        
        # Import required modules for date/time handling
        from datetime import datetime, timezone
        import re
        
        def parse_and_format_datetime(date_str, time_str):
            """Parse various date/time formats and return ISO 8601 format"""
            try:
                # Clean inputs
                clean_date = date_str.strip().replace('T', '') if date_str else ""
                clean_time = time_str.strip().replace('T', '') if time_str else ""
                
                # Handle different date formats
                if clean_date:
                    # Try to parse different date formats
                    date_formats = [
                        "%Y-%m-%d",      # 2025-07-30
                        "%d-%m-%Y",      # 17-07-2025
                        "%m/%d/%Y",      # 07/17/2025
                        "%d/%m/%Y",      # 17/07/2025
                        "%Y/%m/%d",      # 2025/07/17
                    ]
                    
                    parsed_date = None
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(clean_date, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not parsed_date:
                        # If all formats fail, use current date
                        parsed_date = datetime.now()
                else:
                    parsed_date = datetime.now()
                
                # Handle different time formats
                if clean_time:
                    # Remove AM/PM and convert to 24-hour format
                    time_clean = clean_time.upper()
                    is_pm = 'PM' in time_clean
                    is_am = 'AM' in time_clean
                    
                    # Remove AM/PM indicators
                    time_clean = re.sub(r'\s*(AM|PM)\s*', '', time_clean)
                    
                    # Try to parse different time formats
                    time_formats = [
                        "%H:%M:%S",      # 17:30:00
                        "%H:%M",         # 17:30
                        "%I:%M:%S",      # 5:30:00 (12-hour)
                        "%I:%M",         # 5:30 (12-hour)
                    ]
                    
                    parsed_time = None
                    for fmt in time_formats:
                        try:
                            time_obj = datetime.strptime(time_clean, fmt).time()
                            hour = time_obj.hour
                            
                            # Convert 12-hour to 24-hour if AM/PM was present
                            if is_pm and hour != 12:
                                hour += 12
                            elif is_am and hour == 12:
                                hour = 0
                            
                            parsed_time = time_obj.replace(hour=hour)
                            break
                        except ValueError:
                            continue
                    
                    if not parsed_time:
                        # Default to current time if parsing fails
                        parsed_time = datetime.now().time()
                else:
                    parsed_time = datetime.now().time()
                
                # Combine date and time
                combined_datetime = datetime.combine(parsed_date.date(), parsed_time)
                
                # Return in ISO 8601 format
                return combined_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                
            except Exception as e:
                # Fallback to current datetime if all else fails
                return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        # Generate properly formatted dueDate
        if date or time:
            due_date = parse_and_format_datetime(date, time)
        else:
            # Default to current time + 1 hour if no date/time provided
            from datetime import timedelta
            due_date = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        
        return {
                "comment": f"call back at {date} {time}",
                "assignedTo": "Self",
                "dueDate": due_date,
                "visibleTo": "BasicUsers",
                "assignedToUserId": "dabfb1c0-2ac6-4d9f-90f8-1fbbd4f68108", ##TODO: Hom-i Bot User id
                "assignedToUserName": "Hom-i", #TODO: Hom-i name
                "assignedToUserRefCode": "",
                "spaToTaskAssigneeRoleId": "",
                "sendupdateviawhatsapp": "",
                "uploadedDocs": [],
                "tagIds": [],
                "createdByTenantName": "Basic Enterprises Private Limited",
                "createdByUserName": "Hom-i", #TODO: Hom-i name
                "refId": lead_data.get("reference_id", ""),
                "customerWAnotificationDirection": "None",
                "refType": "Application",
                "type": "Task"
            }

  
    def normalize_url(self, url):
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        query_params = urlencode((parse_qsl(parsed.query)))
        return f"{host}{path}?{query_params}" if query_params else f"{host}{path}"

    def generate_signature_headers(self, url, method, body=None, user_id=None, api_key=None):
        if not user_id or not api_key:
            raise HTTPException(
                status_code=500,
                detail="BASIC_APPLICATION_USER_ID and BASIC_APPLICATION_API_KEY must be configured in environment variables"
            )
        
        body_str = json.dumps(body) if body else ""
        normalized = self.normalize_url(url)
        timestamp = int(datetime.now().timestamp())
        nonce = str(uuid.uuid4())
        body_md5 = hashlib.md5(body_str.encode()).hexdigest().lower() if body_str else ""
        message = user_id + str(timestamp) + normalized + method.lower() + nonce + body_md5
        signature = base64.b64encode(hmac.new(api_key.encode(), message.encode(), hashlib.sha512).digest()).decode()
        headers = {
            "accept": "text/plain",
            "Content-Type": "application/json-patch+json",
            "UserId": user_id,
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
            headers = self.generate_signature_headers(
                api_url, "POST",
                 api_payload,
                 self.BASIC_APPLICATION_AGENT_USER_ID,
                 self.BASIC_APPLICATION_AGENT_API_KEY)
            response = requests.post(api_url, headers=headers, json=api_payload)

            if response.status_code in [200, 201]:
                try:
                    # Check if response has content before parsing JSON
                    if response.text.strip():
                        return response.json()
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Empty response received from Basic Application API"
                        )
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error: {json_error}")
                    logger.error(f"Response text: {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid JSON response from Basic Application API: {response.text}"
                    )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to create lead in Basic Application API: {response.text}"
                )
                    
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling Basic Application API: {str(e)}")
    
    # Detailed Leads Creation API using CreateFBBByBasicUser
    def create_FBB_by_basic_user(self, lead_data: Dict) -> Dict:
        """
        Create detailed lead in Basic Application API(CreateFBBByBasicUser)
        
        Args:
            lead_data: Lead data from request
            
        Returns:
            Dict: Response from Basic Application API
            
        Raises:
            HTTPException: If API call fails
        """
        try:
            api_payload = self._prepare_FBB_by_basic_user_payload(lead_data)
            
            if not self.basic_api_url:
                raise HTTPException(
                    status_code=500,
                    detail="Basic Application API URL not configured"
                )
            # Get signature headers
            api_url = f"{self.basic_api_url}/api/v1/NewApplication/CreateFBBByBasicUser"
            headers = self.generate_signature_headers(
                api_url, "POST",
                 api_payload,
                 self.BASIC_APPLICATION_USER_ID,
                 self.BASIC_APPLICATION_API_KEY)

            response = requests.post(api_url, headers=headers, json=api_payload)
            print("Lead Create:", response.text)

            if response.status_code in [200, 201]:
                try:
                    # Check if response has content before parsing JSON
                    if response.text.strip():
                        return response.json()
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Empty response received from Basic Application API- CreateFBBByBasicUser"
                        )
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error: {json_error}")
                    logger.error(f"Response text: {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid JSON response from Basic Application API: {response.text}"
                    )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to create lead in Basic Application API(CreateFBBByBasicUser): {response.text}"
                )
                    
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling Basic Application API: {str(e)}")
    
    # API for Fullfilment by Basic User by application id
    def create_fullfilment_using_application_id(self, lead_data: Dict) -> Dict:
        """
        Use this API to create fullfilment by basic user by application id

        Agrs:
            lead_data: Lead data from request
        Returns:
            Dict: Response from Basic Application API
        Raises:
            HTTPException: If API call fails
        """
        application_id = lead_data.get("applicationId", "")
        if not application_id:
            raise HTTPException(status_code=400, detail="Application ID not found")
        try:
            api_payload = {
            "applicationId": application_id,
            "confirm": True,
            }
            if not self.basic_api_url:
                    raise HTTPException(
                        status_code=500,
                        detail="Basic Application API URL not configured"
                    )
            
            # Get signature headers
            api_url = f"{self.basic_api_url}/api/v1/Application/Activity/BasicFullFilment"
            headers = self.generate_signature_headers(
                api_url, "PUT",
                 api_payload,
                 self.BASIC_APPLICATION_USER_ID,
                 self.BASIC_APPLICATION_API_KEY)
            response = requests.put(api_url, headers=headers, json=api_payload)
            print("**********************",response.text, response.status_code,"**********************")

            if response.status_code in [200, 201]:
                try:
                    # Check if response has content before parsing JSON
                    if response.text.strip():
                        return response.json()
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Empty response received from Basic Application API- Basic Fullfilment"
                        )
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error: {json_error}")
                    logger.error(f"Response text: {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid JSON response from Basic Application API: {response.text}"
                    )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to create lead in Basic Application API(Basic Fullfilment): {response.text}"
                )
                    
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling Basic Application API: {str(e)}")
    

    # Detailed Leads Creation API using SelfFullfilment
    def create_self_fullfilment_lead(self, lead_data: Dict) -> Dict:
        """
        Create detailed lead in Basic Application API(SelfFullfilment)
        
        Args:
            lead_data: Lead data from request
            
        Returns:
            Dict: Response from Basic Application API
            
        Raises:
            HTTPException: If API call fails
        """
        try:
            api_payload = self._prepare_self_fullfilment_payload(lead_data)
            logger.info(f"API Payload: SelfFullfilment {api_payload}")
            
            if not self.basic_api_url:
                raise HTTPException(
                    status_code=500,
                    detail="Basic Application API URL not configured"
                )
            
            # Get signature headers
            api_url = f"{self.basic_api_url}/api/v1/NewApplication/SelfFullfilment"
            headers = self.generate_signature_headers(
                api_url, "PUT",
                 api_payload,
                 self.BASIC_APPLICATION_USER_ID,
                 self.BASIC_APPLICATION_API_KEY)
            response = requests.put(api_url, headers=headers, json=api_payload)

            if response.status_code in [200, 201]:
                try:
                    # Check if response has content before parsing JSON
                    if response.text.strip():
                        return response.json()
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Empty response received from Basic Application API- SelfFullfilment"
                        )
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error: {json_error}")
                    logger.error(f"Response text: {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid JSON response from Basic Application API: {response.text}"
                    )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to create lead in Basic Application API(SelfFullfilment): {response.text}"
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
                headers = self.generate_signature_headers(
                    api_url,
                     "GET",
                     None,
                     self.BASIC_APPLICATION_USER_ID,
                     self.BASIC_APPLICATION_API_KEY)
                
                response = requests.get(api_url, headers=headers)
                    
                if response.status_code == 200:
                    try:
                        # Check if response has content before parsing JSON
                        if response.text.strip():
                            return response.json()
                        else:
                            logger.error("Empty response received from Basic Application API")
                            return None
                    except json.JSONDecodeError as json_error:
                        logger.error(f"JSON parsing error: {json_error}")
                        logger.error(f"Response text: {response.text}")    
                        return None
                else:
                    logger.error(f"API call failed with status code: {response.status_code}")
                    logger.error(f"Response text: {response.text}")
                    return None
            else:
                return None
                    
        except HTTPException:
            raise
        except Exception as e:
            return None 


    # Detailed Leads Creation API using CreateFBBByBasicUser
    def create_appointment_by_basic_user(self, lead_data: Dict) -> Dict:
        """
        Create/book appointment in Basic Application API
        
        Args:
            lead_data: Lead data from request
            
        Returns:
            Dict: Response from Basic Application API
            
        Raises:
            HTTPException: If API call fails
        """
        try:
            api_payload = self._prepare_book_appointment_payload(lead_data)
            
            if not self.basic_api_url:
                raise HTTPException(
                    status_code=500,
                    detail="Basic Application API URL not configured"
                )
            # Get signature headers
            api_url = f"{self.basic_api_url}/api/v1/ApplicationCommentsAndTasks/CreateTaskOrComment"
            headers = self.generate_signature_headers(
                api_url, "POST",
                 api_payload,
                 self.BASIC_APPLICATION_USER_ID,
                 self.BASIC_APPLICATION_API_KEY)
            response = requests.post(api_url, headers=headers, json=api_payload)

            if response.status_code in [200, 201]:
                try:
                    # Check if response has content before parsing JSON
                    if response.text.strip():
                        return response.json()
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail="Empty response received from Basic Application API- CreateTaskOrComment"
                        )
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON parsing error: {json_error}")
                    logger.error(f"Response text: {response.text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid JSON response from Basic Application API: {response.text}"
                    )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to create lead in Basic Application API(CreateTaskOrComment): {response.text}"
                )
                    
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling Basic Application API: {str(e)}")
    