from fastapi import FastAPI, HTTPException, APIRouter
from models import SendOTPRequest, ResendOTPRequest, VerifyOTPRequest, OTPResponse
from whatsapp_service import whatsapp_service
from database import otp_storage
from config import settings
import re

# Create API router with prefix
router = APIRouter(prefix="/otp", tags=["OTP Operations"])
print("Starting: ", settings)

app = FastAPI(
    title="WhatsApp OTP Verification API",
    description="API for sending, resending, and verifying WhatsApp OTP using Gupshup API",
    version="1.0.0"
)

def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number to include country code 91.
    Handles various formats:
    - 917888888888 (already has country code)
    - 788888888 (without country code)
    - +917888888888 (with + prefix)
    - 917888888888 (without + prefix)
    """
    # Remove any spaces, dashes, or other separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone_number)
    
    # Remove + prefix if present
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    
    # If number starts with 91 and is 12 digits, it already has country code
    if cleaned.startswith('91') and len(cleaned) == 12:
        return '+' + cleaned
    
    # If number is 10 digits (without country code), add 91
    if len(cleaned) == 10:
        return '+91' + cleaned
    
    # If number is 11 digits and starts with 0, remove 0 and add 91
    if len(cleaned) == 11 and cleaned.startswith('0'):
        return '+91' + cleaned[1:]
    
    # If number is already 12 digits and starts with 91, add + prefix
    if len(cleaned) == 12 and cleaned.startswith('91'):
        return '+' + cleaned
    
    # If number is 9 digits (without country code), add 91
    if len(cleaned) == 9:
        return '+91' + cleaned
    
    # If number is 8 digits (without country code), add 91
    if len(cleaned) == 8:
        return '+91' + cleaned
    
    # For any other format, assume it needs country code 91
    # Remove any leading zeros
    cleaned = cleaned.lstrip('0')
    return '+91' + cleaned

def validate_phone_number(phone_number: str) -> bool:
    """Validate phone number format after normalization"""
    try:
        normalized = normalize_phone_number(phone_number)
        # Check if normalized number is valid (starts with +91 and has 10-12 digits after country code)
        pattern = r'^\+91[1-9]\d{9,11}$'
        return bool(re.match(pattern, normalized))
    except:
        return False

@app.get("/debug/whatsapp")
async def debug_whatsapp():
    """Debug endpoint to test WhatsApp service configuration"""
    return {
        "api_url": whatsapp_service.api_url,
        "api_key": whatsapp_service.api_key[:10] + "..." if whatsapp_service.api_key else None,
        "source": whatsapp_service.source,
        "template_id": whatsapp_service.template_id,
        "src_name": whatsapp_service.src_name,
        "config_source": "Environment variables loaded successfully" if whatsapp_service.api_key else "Environment variables not loaded"
    }

@app.get("/debug/test-request")
async def debug_test_request():
    """Debug endpoint to show what request would be sent"""
    test_phone = "+1234567890"
    test_otp = "123456"
    
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
        'apikey': whatsapp_service.api_key,
        'cache-control': 'no-cache'
    }
    
    data = {
        'channel': 'whatsapp',
        'source': whatsapp_service.source,
        'destination': test_phone,
        'src.name': whatsapp_service.src_name,
        'template': f'{{"id":"{whatsapp_service.template_id}","params":["{test_otp}"]}}'
    }
    
    return {
        "api_url": whatsapp_service.api_url,
        "headers": headers,
        "data": data,
        "note": "This shows the exact request that would be sent to Gupshup"
    }

@app.get("/debug/phone-normalization")
async def debug_phone_normalization():
    """Debug endpoint to test phone number normalization"""
    test_cases = [
        "917888888888",  # Already has country code
        "788888888",     # Without country code
        "+917888888888", # With + prefix
        "0788888888",    # With leading 0
        "888888888",     # 9 digits
        "88888888",      # 8 digits
        "91 788 888 8888", # With spaces
        "91-788-888-8888", # With dashes
    ]
    
    results = []
    for phone in test_cases:
        try:
            normalized = normalize_phone_number(phone)
            is_valid = validate_phone_number(phone)
            results.append({
                "original": phone,
                "normalized": normalized,
                "is_valid": is_valid
            })
        except Exception as e:
            results.append({
                "original": phone,
                "normalized": "ERROR",
                "is_valid": False,
                "error": str(e)
            })
    
    return {
        "phone_number_normalization_test": results,
        "note": "This shows how different phone number formats are normalized to +91 format"
    }

@router.post("/send", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest):
    """Send OTP to the specified phone number"""

    if not validate_phone_number(request.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    # Normalize phone number for WhatsApp service
    normalized_phone = normalize_phone_number(request.phone_number)

    # Check if OTP already exists (use original phone number for storage)
    print("phone number", request.phone_number)
    if otp_storage.is_otp_exists(request.phone_number):
        raise HTTPException(
            status_code=409,
            detail={
                "success": False,
                "message": "OTP already sent. Please wait for expiry or use resend endpoint.",
                "data": {"phone_number": request.phone_number}
            }
        )
    
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
            data={"phone_number": request.phone_number, "otp": otp}  # Include OTP for testing
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

@router.post("/resend", response_model=OTPResponse)
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
            data={"phone_number": request.phone_number, "otp": otp}  # Include OTP for testing
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

@router.post("/verify", response_model=OTPResponse)
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
        # Delete OTP after successful verification
        otp_storage.delete_otp(request.phone_number)
        
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "WhatsApp OTP API is running"}

# Include the router with prefix
app.include_router(router)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=5000) 