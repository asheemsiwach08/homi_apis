from typing import Optional
from pydantic import BaseModel, EmailStr, Field

####################################### OTP Schemas #####################################

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

################################# Lead Create Schemas ##############################################

class LeadCreateRequest(BaseModel):
    firstName: str
    lastName: str
    gender: Optional[str] = None
    mobile: str
    pan: str
    email: EmailStr
    state: Optional[str] = None
    pincode: str
    loanType: str
    loanTenure: int
    loanAmountReq: float 
    dateOfBirth: str
    creditScore: int
    customerId: Optional[str] = None
    annualIncome: Optional[float] = None
    createdFromPemId: Optional[str] = None
    creditScoreTypeId: Optional[str] = None
    applicationAssignedToRm: Optional[str] = None
    includeCreditScore: Optional[bool] = None
    isLeadPrefilled: Optional[bool] = None
    qrShortCode: Optional[str] = None
    remarks: Optional[str] = None
    
class LeadCreateResponse(BaseModel):
    basic_application_id: str
    applicationId:str
    reference_id: str
    message: str

################################# Lead Flash Schemas ##############################################

class LeadFlashRequest(BaseModel):
    firstName: str
    lastName: str
    gender: Optional[str] = None
    mobile: str
    email: EmailStr
    pan: str
    dateOfBirth: str
    creditScore: int
    applicationId: str
    loanAmountReq: float
    loanTenure: int
    loanType: str
    pincode: str
    location: Optional[str] = None
    professionId: str
    professionName: str
    propertyName: Optional[str] = None
    propertyType: Optional[str] = None
    agreementType: Optional[str] = None
    propertyTypeId: Optional[str] = None
    aggrementTypeId: Optional[str] = None
    salaryCreditModeId: Optional[str] = None
    propertyIdentified: Optional[str] = None
    salaryCreditModeName: Optional[str] = None
    selfCompanyTypeId: Optional[str] = None
    loanUsageTypeId: Optional[str] = None
    propertyValue: Optional[float] = None
    companyName: Optional[str] = None
    unitNumber: Optional[str] = None
    usageType: Optional[str] = None
    unitType: Optional[str] = None

class LeadFlashResponse(BaseModel):
    basic_application_id: str
    reference_id: str
    message: str

################################# Book Appointment Schemas ##############################################

class BookAppointmentRequest(BaseModel):
    date: str
    time: str
    reference_id: str

class BookAppointmentResponse(BaseModel):
    basic_application_id: str
    message: str
    
################################# Lead Status Schemas ##############################################

class LeadStatusRequest(BaseModel):
    mobile_number: Optional[str] = None
    basic_application_id: Optional[str] = None

class LeadStatusResponse(BaseModel):    
    status: str
    message: str

################################# WhatsApp Webhook Schemas ##############################################

class WhatsAppMessageRequest(BaseModel):
    message: str = Field(..., description="WhatsApp message content")

class WhatsAppStatusResponse(BaseModel):
    application_id: Optional[str] = None
    success: bool
    message: str
    status: Optional[str] = None