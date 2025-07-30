from time import struct_time
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict

####################################### Request Schemas #####################################
class SendOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to send OTP to")

class ResendOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to resend OTP to")

class VerifyOTPRequest(BaseModel):
    phone_number: str = Field(..., description="Phone number to verify OTP for")
    otp: str = Field(..., description="OTP to verify")

class WhatsAppMessageRequest(BaseModel):
    message: str = Field(..., description="WhatsApp message content")

# class LeadCreateRequest(BaseModel):
#     loan_type: str
#     loan_amount: float
#     loan_tenure: int
#     pan_number: str
#     first_name: str
#     last_name: str
#     gender: Optional[str] = None
#     mobile_number: str
#     email: EmailStr
#     dob: str
#     pin_code: str

class LeadCreateRequest(BaseModel):
    firstName: str
    lastName: str
    gender: Optional[str] = None
    mobile: str
    creditScore: int
    pan: str
    loanType: str
    loanAmountReq: float
    loanTenure: int
    pincode: str
    email: EmailStr
    dateOfBirth: str

class LeadFlashRequest(BaseModel):
    firstName: str
    lastName: str
    gender: Optional[str] = None
    mobile: str
    creditScore: int
    pan: str
    loanType: str
    loanAmountReq: float
    loanTenure: int
    pincode: str
    email: EmailStr
    dateOfBirth: str
    applicationId: str
    propertyIdentified: str
    propertyName: str
    estimatedPropertyValue: str
    propertyType: str
    agreementType: str
    unitType: str
    location: str
    usageType: str
    unitNumber: str

class BookAppointmentRequest(BaseModel):
  date: str
  time: str
  reference_id: str
    
class LeadStatusRequest(BaseModel):
    mobile_number: Optional[str] = None
    basic_application_id: Optional[str] = None

####################################### Response Schemas #####################################
class LeadCreateResponse(BaseModel):
    basic_application_id: str
    reference_id: str
    message: str

class LeadCreateResponse(BaseModel):
    basic_application_id: str
    applicationId:str
    reference_id: str
    message: str

class LeadFlashResponse(BaseModel):
    basic_application_id: str
    reference_id: str
    message: str

class BookAppointmentResponse(BaseModel):
    basic_application_id: str
    message: str

class LeadStatusResponse(BaseModel):    
    status: str
    message: str

class WhatsAppStatusResponse(BaseModel):
    success: bool
    message: str
    status: Optional[str] = None
    application_id: Optional[str] = None

class OTPResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None 

 