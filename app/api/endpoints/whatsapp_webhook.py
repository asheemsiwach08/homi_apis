import re
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Form
from app.models.schemas import WhatsAppStatusResponse
from app.services.basic_application_service import BasicApplicationService
from app.services.whatsapp_service import whatsapp_service
from app.services.database_service import database_service
from app.utils.validators import validate_mobile_number
from app.config.settings import settings

router = APIRouter(prefix="/api_v1", tags=["whatsapp-webhook"])

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

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request,
    payload: str = Form(...),
    mobile: str = Form(...),
    name: str = Form(default=None),
    message: str = Form(default=None),
    channel: str = Form(...),
    timestamp: str = Form(...)
):
    """
    Webhook endpoint that receives WhatsApp messages from Gupshup
    This endpoint is called automatically by WhatsApp when a message is received
    """
    try:
        print(f"Received WhatsApp message from {mobile}: {message}")
        
        # Check if this is a status check request
        if not is_status_check_request(message):
            # Send a helpful response for non-status messages
            await whatsapp_service.send_message(
                phone_number=mobile,
                message="Hi! To check your application status, please send a message like 'Check my application status' along with your mobile number."
            )
            return {"status": "success", "message": "Non-status message handled"}
        
        # Extract phone number and application ID from message
        # phone_number = extract_phone_number_from_message(message)
        # application_id = extract_application_id_from_message(message)

        # print("application_id:-", application_id)
        print("mobile:-", mobile)
        
        # If no phone number found in message, use the sender's number
        if mobile:
            phone_number = mobile.replace('+91', '').replace('91', '')
        print("phone_number:-", phone_number)
        
        # Try to get status from Basic Application API
        api_status = await basic_app_service.get_lead_status(
            mobile_number=str(phone_number),
            # basic_application_id=None
        )
        
        if api_status:
            # Extract status from API response
            status = api_status.get("result", {}).get("latestStatus", "Not found")
            response_message = f"Your application status is: {status}"
            
            # Get lead data from database for WhatsApp response
            lead_data = database_service.get_lead_by_mobile(phone_number)
            
            # Save status to Supabase database
            try:
                if lead_data and lead_data.get("basic_application_id"):
                    basic_app_id = lead_data.get("basic_application_id")
                    if basic_app_id:
                        database_service.update_lead_status(str(basic_app_id), str(status))
                        print(f"Status updated in database for mobile: {phone_number}")
            except Exception as db_error:
                print(f"Failed to update status in database: {db_error}")
            
            # Send WhatsApp response with the status
            print("lead_data:-", lead_data)
            if lead_data:
                name = lead_data.get("first_name", "") + " " + lead_data.get("last_name", "")
                        
                # Send the status update to WhatsApp
                await whatsapp_service.send_lead_status_update(
                    phone_number="+91" + phone_number,
                    name=name,
                    status=str(status)
                )
            else:
                # Send simple message if lead data not found
                await whatsapp_service.send_message(
                    phone_number=mobile,
                    message=response_message
                )
            
            return {
                "status": "success",
                "message": "Status sent successfully",
                "application_status": str(status),
                "phone_number": phone_number
            }
        else:
            # Send error message via WhatsApp
            error_message = "We couldn't find your application details. Please check your mobile number or application ID."
            await whatsapp_service.send_message(
                phone_number=mobile,
                message=error_message
            )
            
            return {
                "status": "error",
                "message": "Application not found",
                "phone_number": phone_number
            }
        
    except Exception as e:
        print(f"Error processing WhatsApp webhook: {str(e)}")
        # Send error message to user
        try:
            await whatsapp_service.send_message(
                phone_number=mobile,
                message="Sorry, there was an error processing your request. Please try again later."
            )
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/whatsapp/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None
):
    """
    Webhook verification endpoint for WhatsApp Business API
    This is called by WhatsApp to verify your webhook URL
    """
    # Get verify token from environment variables
    verify_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token and hub_challenge:
        print("Webhook verified successfully")
        return int(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed") 