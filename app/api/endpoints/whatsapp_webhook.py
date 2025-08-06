import re
import json
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, Form
from app.models.schemas import WhatsAppStatusResponse
from app.services.basic_application_service import BasicApplicationService
from app.services.whatsapp_service import whatsapp_service
from app.services.database_service import database_service
from app.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["whatsapp-webhook"])

# Initialize services
basic_app_service = BasicApplicationService()

############################################################################################
                                # WhatsApp Webhook Validation
############################################################################################

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
        'loan details',
        'loan application'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in status_keywords)

############################################################################################
                                # WhatsApp Webhook API
############################################################################################

@router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook endpoint that receives WhatsApp messages from Gupshup
    This endpoint is called automatically by WhatsApp when a message is received
    """
    try:
        # Get the raw body as JSON
        body = await request.json()
        logger.info(f"Received webhook payload: {json.dumps(body, indent=2)}")
        
        # Extract data from Gupshup payload structure
        app_name = body.get("app")
        timestamp = body.get("timestamp")
        message_type = body.get("type")
        payload_data = body.get("payload", {})
        
        # Extract message details from payload
        message_id = payload_data.get("id")
        source = payload_data.get("source")  # This is the sender's phone number
        message_type_detail = payload_data.get("type")
        message_payload = payload_data.get("payload", {})
        sender = payload_data.get("sender", {})
        
        # Extract the actual message text
        if message_type_detail == "text":
            message_text = message_payload.get("text", "")
        else:
            message_text = "Non-text message received"
        
        # Extract sender details
        sender_phone = sender.get("phone", source)  # Use source as fallback
        sender_name = sender.get("name", "")
        country_code = sender.get("country_code", "")
        dial_code = sender.get("dial_code", "")
        
        logger.info(f"Received WhatsApp message from {sender_phone}: {message_text}")
        
        # Save the user message to database only if mobile number is available
        message_id = None
        if sender_phone:
            try:
                message_data = {
                    "mobile": sender_phone,
                    "message": message_text,
                    "payload": json.dumps(body)  # Save the entire payload as JSON string
                }
                
                save_result = database_service.save_whatsapp_message(message_data)
                message_id = save_result.get('message_id')
                logger.info(f"User message saved to database with ID: {message_id}")
                
            except Exception as save_error:
                logger.error(f"Failed to save user message to database: {save_error}")
                message_id = None
                # Continue processing even if save fails
        else:
            logger.info("Skipping database save - mobile number is None")
        
        # Check if this is a status check request
        if not is_status_check_request(message_text):
            # Send a helpful response for non-status messages
            await whatsapp_service.send_message(
                phone_number=sender_phone,
                message="Hi! To check your application status, please send a message like 'Check my application status' along with your mobile number."
            )
            
            return {"status": "success", "message": "Non-status message handled"}
        
        # Extract phone number from sender's phone
        if sender_phone:
            # Clean the phone number
            phone_number = str(sender_phone).strip()
            
            # Remove +91 prefix if present (only if it's at the beginning)
            if phone_number.startswith('+91'):
                phone_number = phone_number[3:]  # Remove +91
            elif phone_number.startswith('91') and len(phone_number) > 10:
                # Only remove 91 if it's a country code (phone number is longer than 10 digits)
                phone_number = phone_number[2:]
            
            # Ensure it's exactly 10 digits for Indian mobile numbers
            if len(phone_number) == 10:
                # Valid 10-digit number
                pass
            elif len(phone_number) > 10:
                # Take the last 10 digits
                phone_number = phone_number[-10:]
            elif len(phone_number) < 10:
                # Too short, might be invalid
                phone_number = None
        else:
            phone_number = None
        
        logger.info(f"Processing status check for phone: {phone_number}")
        
        if not phone_number:
            # Send error message via WhatsApp
            error_message = "We couldn't identify your mobile number. Please try again."
            await whatsapp_service.send_message(
                phone_number=sender_phone,
                message=error_message
            )
            
            return {
                "status": "error",
                "message": "Phone number not found",
                "phone_number": None
            }
        
        # Try to get status from Basic Application API
        api_status = await basic_app_service.get_lead_status(
            mobile_number=str(phone_number),
        )

        if api_status:
            # Extract status from API response
            status = api_status.get("result", {}).get("latestStatus", "Not found")
            response_message = f"Your application status is: {status}"
            
            # Get lead data from database for WhatsApp response
            lead_data = database_service.get_leads_by_mobile(phone_number)[0]  # Get the first record
            
            # Save status to Supabase database
            try:
                if lead_data and lead_data.get("basic_app_id"):
                    basic_app_id = lead_data.get("basic_app_id")
                    if basic_app_id:
                        database_service.update_lead_status(str(basic_app_id), str(status))
                        logger.info(f"Status updated in database for mobile: {phone_number}")
            except Exception as db_error:
                logger.error(f"Failed to update status in database: {db_error}")
            
            # Send WhatsApp response with the status
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
                    phone_number=sender_phone,
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
                phone_number=sender_phone,
                message=error_message
            )
            
            return {
                "status": "error",
                "message": "Application not found",
                "phone_number": phone_number
            }
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        # Send error message to user if we have the phone number
        try:
            if 'sender_phone' in locals():
                await whatsapp_service.send_message(
                    phone_number=sender_phone,
                    message="Sorry, there was an error processing your request. Please try again later."
                )
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

############################################################################################
                                # WhatsApp Webhook Verification API
############################################################################################

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
        logger.info("Webhook verified successfully")
        return int(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed") 