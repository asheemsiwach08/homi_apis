from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HOM-i Whatsapp OTP,Lead Creation & Status API",
        "version": "1.0.0",
        "endpoints": {
            "send_otp": "POST /api_v1/otp_send",
            "resend_otp": "POST /api_v1/otp_resend",
            "verify_otp": "POST /api_v1/otp_verify",
            "create_lead": "POST /api_v1/lead_create",
            "get_status": "POST /api_v1/lead_status"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "HOM-i API"} 