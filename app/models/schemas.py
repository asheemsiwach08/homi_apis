
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

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
    annualIncome: Optional[float] = None
    applicationAssignedToRm: Optional[str] = None
    createdFromPemId: Optional[str] = None
    creditScoreTypeId: Optional[str] = None
    customerId: Optional[str] = None
    includeCreditScore: Optional[bool] = None
    isLeadPrefilled: Optional[bool] = None
    qrShortCode: Optional[str] = None
    remarks: Optional[str] = None
    state: Optional[str] = None

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
    professionId: str
    professionName: str
    propertyIdentified: Optional[str] = None
    propertyName: Optional[str] = None
    propertyType: Optional[str] = None
    agreementType: Optional[str] = None
    unitType: Optional[str] = None
    location: Optional[str] = None
    usageType: Optional[str] = None
    unitNumber: Optional[str] = None
    #
    salaryCreditModeId: Optional[str] = None
    salaryCreditModeName: Optional[str] = None
    selfCompanyTypeId: Optional[str] = None
    companyName: Optional[str] = None
    propertyTypeId: Optional[str] = None
    propertyValue: Optional[float] = None
    loanUsageTypeId: Optional[str] = None
    aggrementTypeId: Optional[str] = None

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

 