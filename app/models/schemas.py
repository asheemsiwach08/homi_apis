from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, EmailStr, Field, validator


############################### Basic Verify Approval Schemas ##################################

class BasicVerifyApprovalRequest(BaseModel):
    basicVerifyData: Dict[str, Any] = Field(..., description="Basic verification data as dictionary")
    basicVerifyStatus: Literal["VerifiedByBasic", "RejectedByBasic"] = Field(default="VerifiedByBasic", description="Verification status - either 'VerifiedByBasic' or 'RejectedByBasic'")
    rejectionComments: Optional[str] = Field(default=None, description="Comments for verification (stored in comments field in database)")
    
    
class BasicVerifyApprovalResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


################################# Book Appointment Schemas #####################################

class BookAppointmentRequest(BaseModel):
    environment: Optional[str] = "orbit"
    date: str
    time: str
    reference_id: str
    assigned_to_user_id: Optional[str] = None
    assigned_to_user_name: Optional[str] = None
    created_by_user_name: Optional[str] = None

class BookAppointmentResponse(BaseModel):
    basic_application_id: str
    message: str

################################# Disbursement Schemas #####################################

class DisbursementRecord(BaseModel):
    """Individual disbursement record."""
    # Primary Key
    ai_disbursement_id: Optional[str] = Field(None, description="Unique UUID identifier for AI-generated disbursement records")
    
    # Email Context
    banker_email: Optional[str] = None
    email_subject: Optional[str] = None
    email_date: Optional[str] = None
    processed_at: Optional[str] = None
    
    # Customer Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    primary_borrower_mobile: Optional[str] = None
    
    # Loan Account Information
    loan_account_number: Optional[str] = None
    bank_app_id: Optional[str] = None
    basic_app_id: Optional[str] = None
    basic_disb_id: Optional[str] = None
    
    # Bank Information
    app_bank_name: Optional[str] = None
    
    # Disbursement Details
    disbursement_amount: Optional[float] = None
    loan_sanction_amount: Optional[float] = None
    disbursed_on: Optional[str] = None
    disbursed_created_on: Optional[str] = None
    sanction_date: Optional[str] = None
    
    # Status Information
    disbursement_stage: Optional[str] = None
    disbursement_status: Optional[str] = None
    
    # Additional Fields
    pdd: Optional[str] = None
    otc: Optional[str] = None
    sourcing_channel: Optional[str] = None
    sourcing_code: Optional[str] = None
    application_product_type: Optional[str] = None
    
    # Comments and Notes
    comments: Optional[str] = None
    
    # Data Quality
    data_found: Optional[bool] = None
    confidence_score: Optional[float] = None
    extraction_method: Optional[str] = None
    
    # Source Information
    source_email_id: Optional[str] = None
    source_thread_id: Optional[str] = None
    attachment_count: Optional[int] = None
    
    # Internal Fields
    is_duplicate: Optional[bool] = None
    duplicate_of_id: Optional[int] = None
    manual_review_required: Optional[bool] = None
    manual_review_notes: Optional[str] = None


class DisbursementFilters(BaseModel):
    """Filters for disbursement queries."""
    bank_name: Optional[str] = None
    disbursement_stage: Optional[str] = None
    date_from: Optional[str] = Field(None, description="Filter from date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Filter to date (YYYY-MM-DD)")
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    customer_name: Optional[str] = None
    data_found: Optional[bool] = None
    manual_review_required: Optional[bool] = None


class DisbursementResponse(BaseModel):
    """Response model for disbursement queries."""
    success: bool
    message: str
    data: List[DisbursementRecord]
    total_count: int
    filtered_count: int
    page_info: Optional[Dict[str, Any]] = None


class DisbursementStatsResponse(BaseModel):
    """Response model for disbursement statistics."""
    success: bool
    message: str
    stats: Dict[str, Any]
    

################################# Lead Create Schemas #####################################

class LeadCreateRequest(BaseModel):
    environment: Optional[str] = "orbit"
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
    assigned_to_rm: Optional[str] = None
    message: str

################################# Lead Flash Schemas ##############################################

class LeadFlashRequest(BaseModel):
    environment: Optional[str] = "orbit"
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
    coBorrowerIncome: Optional[float] = None
    salaryCreditModeId: Optional[str] = None
    propertyIdentified: Optional[str] = None
    salaryCreditModeName: Optional[str] = None
    selfCompanyTypeId: Optional[str] = None
    loanUsageTypeId: Optional[str] = None
    propertyValue: Optional[float] = None
    companyName: Optional[str] = None
    unitNumber: Optional[str] = None
    usageType: Optional[str] = None
    towerName: Optional[str] = None
    unitType: Optional[str] = None
    documents: Optional[list] = None
    propertyDistrict: Optional[str] = None
    propertyPincode: Optional[str] = None
    builderId: Optional[str] = None
    towerId: Optional[str] = None
    builderName: Optional[str] = None
    creditScoreTypeId: Optional[str] = None
    creditScoreTypeName: Optional[str] = None
    isVistedNextPage: Optional[bool] = None
    manualCreditScore: Optional[int] = None
    towerUnitType: Optional[str] = None
    propertyProjectName: Optional[str] = None
    annualIncome: Optional[float] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    existingEmis: Optional[str] = None
    selfCompanyTypeName: Optional[str] = None
    canCustomerUploadDocuments: Optional[bool] = None
    isOsvByConsultantAvailable: Optional[bool] = None
    isLeadPrefilled: Optional[bool] = None
    includeCreditScore: Optional[bool] = None
    recentCreditReportExists: Optional[bool] = None
    isPropertyIdentified: Optional[bool] = None
    isReferralLead: Optional[bool] = None
    projectId: Optional[str] = None
    creditScoreStatus: Optional[str] = None

class LeadFlashResponse(BaseModel):
    basic_application_id: str
    reference_id: str
    assigned_to_rm: Optional[str] = None
    message: str

    
################################# Lead Status Schemas #####################################

class LeadStatusRequest(BaseModel):
    environment: Optional[str] = "orbit"
    mobile_number: Optional[str] = None
    basic_application_id: Optional[str] = None

class LeadStatusResponse(BaseModel):    
    status: str
    message: str

class TrackApplicationRequest(BaseModel):
    environment: Optional[str] = "orbit"
    mobile_number: Optional[str] = None
    basic_application_id: Optional[str] = None

class TrackApplicationResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None


################################# OTP Schemas #######################################

class SendOTPRequest(BaseModel):
    environement: Optional[Literal["orbit", "homfinity"]] = "orbit"
    user_check: Optional[bool] = True
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

################################# Consent Request Schemas #######################################

class ConsentRequestRequest(BaseModel):
    app_name: Optional[Literal["orbit", "homfinity"]] = "orbit"
    user_check: Optional[bool] = False
    phone_number: str = Field(..., description="Phone number to send OTP to")

class ConsentRequestResponse(BaseModel):
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Message")
    data: dict = Field(..., description="Data")


################################# WhatsApp Webhook Schemas #######################################

class WhatsAppMessageRequest(BaseModel):
    message: str = Field(..., description="WhatsApp message content")

class WhatsAppStatusResponse(BaseModel):
    application_id: Optional[str] = None
    success: bool
    message: str
    status: Optional[str] = None

################################# Gupshup API Schemas #######################################

class BaseGupshupResponse(BaseModel):
    """Base response model for all Gupshup APIs"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    gupshup_response: Optional[Dict[str, Any]] = None

class PhoneNumberRequest(BaseModel):
    """Base request with phone number validation"""
    phone_number: str = Field(..., description="Phone number (supports multiple formats)")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        from app.utils.validators import normalize_phone_number
        return normalize_phone_number(v)

class TemplateMessageRequest(PhoneNumberRequest):
    """Request for template-based messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TextMessageRequest(PhoneNumberRequest):
    """Request for simple text messages"""
    message: str = Field(..., description="Text message to send")
    source_name: Optional[str] = Field(None, description="Custom source name")

class MediaMessageRequest(PhoneNumberRequest):
    """Request for media messages"""
    media_type: str = Field(..., description="Media type: image, document, audio, video")
    media_url: str = Field(..., description="URL of the media file")
    caption: Optional[str] = Field(None, description="Caption for the media")
    filename: Optional[str] = Field(None, description="Filename for documents")

class InteractiveMessageRequest(PhoneNumberRequest):
    """Request for interactive messages (buttons, lists)"""
    interactive_type: str = Field(..., description="Type: button, list")
    header: Optional[Dict[str, Any]] = Field(None, description="Message header")
    body: Dict[str, Any] = Field(..., description="Message body")
    footer: Optional[Dict[str, Any]] = Field(None, description="Message footer")
    action: Dict[str, Any] = Field(..., description="Interactive action")

class LocationMessageRequest(PhoneNumberRequest):
    """Request for location messages"""
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")

class ContactMessageRequest(PhoneNumberRequest):
    """Request for contact messages"""
    contacts: List[Dict[str, Any]] = Field(..., description="List of contacts")

class BulkMessageRequest(BaseModel):
    """Request for bulk messaging"""
    phone_numbers: List[str] = Field(..., description="List of phone numbers")
    message_type: str = Field(..., description="Type: text, template, media")
    message_data: Dict[str, Any] = Field(..., description="Message data based on type")
    delay_between_messages: Optional[int] = Field(5, description="Delay in seconds between messages")

class MessageStatusRequest(BaseModel):
    """Request to check message status"""
    message_id: str = Field(..., description="Gupshup message ID")

class TemplateListResponse(BaseModel):
    """Response for template listing"""
    success: bool
    message: str
    templates: List[Dict[str, Any]]

