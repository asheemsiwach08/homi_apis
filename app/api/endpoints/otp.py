import logging
from fastapi import HTTPException, APIRouter
from app.models.schemas import SendOTPRequest, ResendOTPRequest, VerifyOTPRequest, OTPResponse
from app.services.whatsapp_service import whatsapp_service
from app.services.database_service import otp_storage
from app.config.settings import settings
from app.utils.validators import validate_phone_number, normalize_phone_number

logger = logging.getLogger(__name__)

# Create API router with prefix
router = APIRouter(prefix="/api_v1", tags=["OTP Operations"])

############################################################################################
                                # OTP Send API
############################################################################################

@router.post("/otp_send", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest):
    """Send OTP to the specified phone number"""

    if not validate_phone_number(request.phone_number):
        logger.error(f"Invalid phone number format: {request.phone_number}")
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    # Normalize phone number for WhatsApp service
    normalized_phone = normalize_phone_number(request.phone_number)

    # Generate OTP
    otp = whatsapp_service.generate_otp()
    
    # Conditional check if the user wants to send consent request
    if not request.user_check:
        whatspp_otp_template_id = "594a8689-00f9-422d-87df-0ba8987d1469"
        whatsapp_consent_template_id = "2fb0ec1f-2c63-459e-a347-57cc76fc21fb"

        consent_request = {
            "phone_number": request.phone_number, 
            "app_name": request.environement if request.environement else "orbit", 
            "template_id": whatspp_otp_template_id if request.user_check else whatsapp_consent_template_id
        }

        # Send consent request
        consent_request_response = await send_consent_request(consent_request)
        logger.info("consent requested", consent_request_response)
        if consent_request_response.get("success"):
            consent_message = consent_request_response.get("message", "")

        # Send OTP via WhatsApp using normalized phone number
        result = await whatsapp_service.send_otp(normalized_phone, otp, template_id=whatsapp_consent_template_id)
    
    else:
        consent_message = "no consent request sent"
        # Send OTP via WhatsApp using normalized phone number
        result = await whatsapp_service.send_otp(normalized_phone, otp)
        
    if result["success"]:
        # Store OTP locally with expiry
        expiry_seconds = settings.OTP_EXPIRY_MINUTES * 60
        otp_storage.set_otp(request.phone_number, otp, expiry_seconds)
        
        return OTPResponse(
            success=True,
            message="OTP sent successfully" + ", " + consent_message,
            data={"phone_number": request.phone_number, "otp": otp}  # Include OTP for testing, Remove it later
        )
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": result.get("message", "OTP generation failed.") + ", " + consent_request_response.get("message", "") if consent_request_response else "",
                "data": result.get("data") or {"error": result.get("error", "Unknown error"), "raw_result": result}
            }
        )

############################################################################################
                                # OTP Resend API
############################################################################################

@router.post("/otp_resend", response_model=OTPResponse)
async def resend_otp(request: ResendOTPRequest):
    """Resend OTP to the specified phone number"""

    if not validate_phone_number(request.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    # Normalize phone number for WhatsApp service
    normalized_phone = normalize_phone_number(request.phone_number)
    
    # Generate new OTP
    otp = whatsapp_service.generate_otp()
    
    # Send OTP via WhatsApp using normalized phone number
    result = await whatsapp_service.send_otp(normalized_phone, otp)
    
    if result["success"]:
        # Store new OTP locally with expiry (overwrites existing)
        expiry_seconds = settings.OTP_EXPIRY_MINUTES * 60
        otp_storage.set_otp(request.phone_number, otp, expiry_seconds)
        
        return OTPResponse(
            success=True,
            message="OTP resent successfully",
            data={"phone_number": request.phone_number, "otp": otp}  # Include OTP for testing, Remove it later
        )
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": result["message"],
                "data": result.get("data", {"error": "Unknown error"})
            }
        )

############################################################################################
                                # OTP Verify API
############################################################################################

@router.post("/otp_verify", response_model=OTPResponse)
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP for the specified phone number"""
    if not validate_phone_number(request.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    # Get stored OTP
    stored_otp = otp_storage.get_otp(request.phone_number)
    
    if not stored_otp:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "message": "OTP not found or expired",
                "data": {"phone_number": request.phone_number}
            }
        )
    
    # Verify OTP
    if stored_otp == request.otp:
        # Mark OTP as used after successful verification
        otp_storage.mark_otp_as_used(request.phone_number)
        
        return OTPResponse(
            success=True,
            message="OTP verified successfully",
            data={"phone_number": request.phone_number}
        )
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "message": "Invalid OTP",
                "data": {"phone_number": request.phone_number}
            }
        )


############################################################################################
                                # Consent Request Function
############################################################################################
from app.services.database_service import database_service
from datetime import datetime, timedelta

import secrets
import string
def generate_random_string(length=12):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def send_consent_request(consent_request):
    """Request consent from the user"""

    # Get the data from the database if any record is present for the phone number
    data = database_service.get_records_from_table(table_environment="homfinity", 
    table_name="user_consent", 
    col_name="phone", 
    col_value=consent_request.get("phone_number"),\
        where_clauses = [
                {"column": "phone", "operator": "eq", "value": consent_request.get("phone_number")},
                {"column": "expired_at", "operator": "gt", "value": datetime.now()},
            ],
            limit=1)
    
    # Conditional check if the consent request is already present
    if not data or len(data) == 0:
        # Generate a new link
        user_consent_link = generate_random_string(12)

        # Create the request object for the template message
        from app.api.endpoints.gupshup_apis import DemoTemplateMessageRequest, send_template_message
        template_request = DemoTemplateMessageRequest(
            app_name=consent_request.get("app_name") if consent_request.get("app_name") else "orbit",
            phone_number="+91"+ str(consent_request.get("phone_number")),
            template_id=consent_request.get("template_id") if consent_request.get("template_id") else "2fb0ec1f-2c63-459e-a347-57cc76fc21fb",
            template_params=[user_consent_link]
        )
        
        template_response = await send_template_message(template_request)

        database_service.save_whatsapp_conversation(environment="orbit", 
        table_name="user_consent", 
        message_data={
            "phone": consent_request.get("phone_number"), 
            "user_link": user_consent_link,
            "retry_count": 0,
            "expired_at": (datetime.now() + timedelta(days=30)).isoformat()
        }
        )
        return {"success": True, "message": "Consent request sent successfully"}

    # elif data and len(data) > 0:
    #     print("I am here in the elif block")
    #     retry_count = data[0].get("retry_count", 0)
    #     if retry_count >= 3:
    #         return {"success": False, "message": "Consent request already exists and retry count is greater than 3"}

    elif data and len(data) == 1:
        return {"success": True, "message": "Consent request already exists"}
    else:
        return {"success": False, "message": "Unable to send consent request, Consent request not found"}

