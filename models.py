from pydantic import BaseModel, Field
from typing import Optional

class SendOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to send OTP to")

class ResendOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to resend OTP to")

class VerifyOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to verify OTP for")
    otp: str = Field(..., description="OTP to verify")

class OTPResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None 