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

def validate_phone_number(phone_number: str) -> bool:
    """Validate phone number format"""
    # Basic validation - can be enhanced based on requirements
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone_number))

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

@router.post("/send", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest):
    """Send OTP to the specified phone number"""
    print("Settings: ", settings)
    if not validate_phone_number(request.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    print("Debug 1: Validate phone number")
    
    # Check if OTP already exists
    if otp_storage.is_otp_exists(request.phone_number):
        return OTPResponse(
            success=False,
            message="OTP already sent. Please wait for expiry or use resend endpoint.",
            data={"phone_number": request.phone_number}
        )
    print("Debug 2: OTP already exists")
    
    # Generate OTP
    otp = whatsapp_service.generate_otp()
    print("Debug 3: Generate OTP")
    
    # Send OTP via WhatsApp
    result = await whatsapp_service.send_otp(request.phone_number, otp)
    print("Debug 4: Send OTP")
    
    if result["success"]:
        # Store OTP locally with expiry
        expiry_seconds = settings.OTP_EXPIRY_MINUTES * 60
        otp_storage.set_otp(request.phone_number, otp, expiry_seconds)
        print("Debug 5: Store OTP")
        
        return OTPResponse(
            success=True,
            message="OTP sent successfully",
            data={"phone_number": request.phone_number, "otp": otp}  # Include OTP for testing
        )
    else:
        print("Debug 6: Send OTP failed")
        return OTPResponse(
            success=False,
            message=result.get("message", "OTP generation failed."),
            data=result.get("data") or {"error": result.get("error", "Unknown error"), "raw_result": result}
        )

@router.post("/resend", response_model=OTPResponse)
async def resend_otp(request: ResendOTPRequest):
    """Resend OTP to the specified phone number"""
    print("Debug 7: Resend OTP")
    if not validate_phone_number(request.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    # Generate new OTP
    otp = whatsapp_service.generate_otp()
    print("Debug 8: Generate new OTP")
    
    # Send OTP via WhatsApp
    result = await whatsapp_service.send_otp(request.phone_number, otp)
    print("Debug 9: Send OTP")
    
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
        return OTPResponse(
            success=False,
            message=result["message"],
            data=result.get("data", {"error": "Unknown error"})
        )

@router.post("/verify", response_model=OTPResponse)
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP for the specified phone number"""
    if not validate_phone_number(request.phone_number):
        raise HTTPException(status_code=400, detail="Invalid phone number format")
    
    # Get stored OTP
    stored_otp = otp_storage.get_otp(request.phone_number)
    
    if not stored_otp:
        return OTPResponse(
            success=False,
            message="OTP not found or expired",
            data={"phone_number": request.phone_number}
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
        return OTPResponse(
            success=False,
            message="Invalid OTP",
            data={"phone_number": request.phone_number}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "WhatsApp OTP API is running"}

# Include the router with prefix
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)