import re
from typing import Optional
from fastapi import APIRouter, HTTPException
from app.models.schemas import WhatsAppMessageRequest, WhatsAppStatusResponse
from app.services.basic_application_service import BasicApplicationService
from app.services.database_service import database_service
from app.utils.validators import validate_mobile_number

router = APIRouter(prefix="/api_v1", tags=["whatsapp"])

# Initialize services
basic_app_service = BasicApplicationService()

def extract_phone_number_from_message(message: str) -> Optional[str]:
    """Extract phone number from WhatsApp message"""
    # Patterns to match phone numbers in various formats
    patterns = [
        r'\b(\d{10})\b',  # 10 digits
        r'\b(\d{12})\b',  # 12 digits (with country code)
        r'\+\d{1,3}(\d{10})\b',  # +91 followed by 10 digits
        r'\b(\d{4}[-.\s]?\d{3}[-.\s]?\d{3})\b',  # 4-3-3 format
        r'\b(\d{5}[-.\s]?\d{5})\b',  # 5-5 format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            # Clean the number (remove spaces, dashes, dots)
            number = re.sub(r'[-.\s]', '', match.group(1))
            # If it's 10 digits, it's likely a mobile number
            if len(number) == 10:
                return number
            # If it's 12 digits and starts with 91, extract the last 10
            elif len(number) == 12 and number.startswith('91'):
                return number[2:]
    
    return None

def extract_application_id_from_message(message: str) -> Optional[str]:
    """Extract application ID from WhatsApp message"""
    # Look for patterns like "application id", "app id", "ID", etc.
    patterns = [
        r'(?:application\s+id|app\s+id|id)\s*[:\-]?\s*([A-Za-z0-9]{6,})',
        r'\b([A-Za-z0-9]{6,})\b',  # Any 6+ character alphanumeric string
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def is_status_check_request(message: str) -> bool:
    """Check if the message is requesting application status"""
    status_keywords = [
        'check my application status',
        'application status',
        'loan status',
        'status check',
        'track application',
        'application tracking',
        'loan application status',
        'check status',
        'my application',
        'loan details'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in status_keywords)

@router.post("/whatsapp/process_message", response_model=WhatsAppStatusResponse)
async def process_whatsapp_message(request: WhatsAppMessageRequest):
    """Process WhatsApp message and check application status if requested"""
    try:
        # Check if this is a status check request
        if not is_status_check_request(request.message):
            return WhatsAppStatusResponse(
                success=False,
                message="This message doesn't appear to be a status check request."
            )
        
        # Extract phone number and application ID from message
        phone_number = extract_phone_number_from_message(request.message)
        application_id = extract_application_id_from_message(request.message)
        
        # If no phone number found in message, return error
        if not phone_number:
            return WhatsAppStatusResponse(
                success=False,
                message="No mobile number found in the message. Please include your mobile number in the message."
            )
        
        # Validate phone number
        if not validate_mobile_number(phone_number):
            return WhatsAppStatusResponse(
                success=False,
                message="Invalid phone number format. Please provide a valid 10-digit mobile number."
            )
        
        # Try to get status from Basic Application API
        api_status = await basic_app_service.get_lead_status(
            mobile_number=phone_number,
            basic_application_id=application_id
        )
        
        if api_status:
            # Extract status from API response
            status = api_status.get("result", {}).get("latestStatus", "Not found")
            message = f"Your application status is: {status}"
            
            # Save status to Supabase database
            try:
                if application_id:
                    # Update status using application ID
                    database_service.update_lead_status(application_id, str(status))
                    print(f"Status updated in database for application ID: {application_id}")
                elif phone_number:
                    # Get lead data by mobile number and update status
                    lead_data = database_service.get_lead_by_mobile(phone_number)
                    if lead_data and lead_data.get("basic_application_id"):
                        basic_app_id = lead_data.get("basic_application_id")
                        if basic_app_id:
                            database_service.update_lead_status(str(basic_app_id), str(status))
                            print(f"Status updated in database for mobile: {phone_number}")
            except Exception as db_error:
                print(f"Failed to update status in database: {db_error}")
            
            return WhatsAppStatusResponse(
                success=True,
                message=message,
                status=str(status),
                application_id=application_id
            )
        else:
            return WhatsAppStatusResponse(
                success=False,
                message="We couldn't find your application details. Please check your mobile number or application ID."
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 