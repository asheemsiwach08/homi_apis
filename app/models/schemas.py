from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict


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

class LeadCreateRequest(BaseModel):
    loan_type: str
    loan_amount: float
    loan_tenure: int
    pan_number: str
    first_name: str
    last_name: str
    gender: Optional[str] = None
    mobile_number: str
    email: EmailStr
    dob: str
    pin_code: str

class LeadCreateDetailedRequest(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[str] = None
    mobile_number: str
    credit_score: int
    pan_number: str
    annual_income: float
    loan_type: str
    loan_amount: float
    loan_tenure: int
    city: str
    district: str
    state: str
    pin_code: str
    email: EmailStr
    dob: str
    
class LeadStatusRequest(BaseModel):
    mobile_number: Optional[str] = None
    basic_application_id: Optional[str] = None

class LeadCreateResponse(BaseModel):
    basic_application_id: str
    message: str

class LeadStatusResponse(BaseModel):
    status: str
    message: str

class WhatsAppMessageRequest(BaseModel):
    message: str = Field(..., description="WhatsApp message content")

class WhatsAppStatusResponse(BaseModel):
    success: bool
    message: str
    status: Optional[str] = None
    application_id: Optional[str] = None

 