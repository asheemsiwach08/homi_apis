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

    # # Check if OTP already exists (use original phone number for storage)
    # print("phone number", request.phone_number)
    # if otp_storage.is_otp_exists(request.phone_number):
    #     raise HTTPException(
    #         status_code=409,
    #         detail={
    #             "success": False,
    #             "message": "OTP already sent. Please wait for expiry or use resend endpoint.",
    #             "data": {"phone_number": request.phone_number}
    #         }
    #     )
    
    # Generate OTP
    otp = whatsapp_service.generate_otp()
    
    # Send OTP via WhatsApp using normalized phone number
    result = await whatsapp_service.send_otp(normalized_phone, otp)
    
    if result["success"]:
        # Store OTP locally with expiry
        expiry_seconds = settings.OTP_EXPIRY_MINUTES * 60
        otp_storage.set_otp(request.phone_number, otp, expiry_seconds)
        
        return OTPResponse(
            success=True,
            message="OTP sent successfully",
            data={"phone_number": request.phone_number}
        )
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": result.get("message", "OTP generation failed."),
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
            data={"phone_number": request.phone_number}
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

