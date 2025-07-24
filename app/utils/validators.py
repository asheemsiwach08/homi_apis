import re
from typing import List
from pydantic import BaseModel, Field
from app.config.settings import settings

###############################################################################
               # Validators for Lead Creation & Whatsapp OTP
###############################################################################
def validate_pan_number(pan: str) -> bool:
    """Validate PAN number format"""
    return bool(re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan))

def validate_mobile_number(mobile: str) -> bool:
    """Validate mobile number format"""
    return bool(re.match(r'^[0-9]{10}$', mobile))

def validate_pin_code(pin: str) -> bool:
    """Validate PIN code format"""
    return bool(re.match(r'^[0-9]{6}$', pin))

def validate_loan_amount(amount: float) -> bool:
    """Validate loan amount"""
    return amount > 0

def validate_loan_tenure(tenure: int) -> bool:
    """Validate loan tenure"""
    return tenure > 0

def validate_loan_type(loan_type: str) -> bool:
    """Validate loan type"""
    valid_types = settings.LOAN_TYPE_MAPPING.keys()
    return loan_type in valid_types 

def validate_phone_number(phone_number: str) -> bool:
    """Validate phone number format after normalization"""
    try:
        normalized = normalize_phone_number(phone_number)
        # Check if normalized number is valid (starts with +91 and has 10-12 digits after country code)
        pattern = r'^\+91[1-9]\d{9,11}$'
        return bool(re.match(pattern, normalized))
    except:
        return False

def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize phone number to include country code 91.
    Handles various formats:
    - 9173457840 (10 digits starting with 91 - actual phone number)
    - 917888888888 (12 digits with country code)
    - 788888888 (without country code)
    - +917888888888 (with + prefix)
    - 0788888888 (with leading 0)
    """
    # Remove any spaces, dashes, or other separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone_number)
    
    # Remove + prefix if present
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    
    # If number is exactly 10 digits and starts with 91, it's a valid phone number
    # Don't treat 91 as country code in this case
    if len(cleaned) == 10 and cleaned.startswith('91'):
        return '+91' + cleaned
    
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


###############################################################################
                   # Validators for BasicVerify
###############################################################################
class BankApplication(BaseModel):
    """Model class for bank application data."""
    
    # Basic Information
    bankerEmail: str = Field(default="")
    firstName: str = Field(default="")
    lastName: str = Field(default="")
    loanAccountNumber: str = Field(default="")
    
    # Dates
    disbursedOn: str = Field(default="Not found")
    disbursedCreatedOn: str = Field(default="Not found")
    sanctionDate: str = Field(default="Not found")
    
    # Financial Information
    disbursementAmount: float = Field(default=0)
    loanSanctionAmount: float = Field(default=0)

    # Application IDs
    bankAppId: str = Field(default="Not found")
    basicAppId: str = Field(default="Not found")
    basicDisbId: str = Field(default="Not found")
    
    # Bank Information
    appBankName: str = Field(default="Not found")
    
    # Status Information
    disbursementStage: str = Field(default="Not Disbursed")
    # disbursementStatus: str = Field(default="VerifiedByAI")
    
    # Contact Information
    primaryborrowerMobile: str = Field(default="Not found")
    
    # Verification Status
    pdd: str = Field(default="Not found")  # PDD - Post Disbursement Document
    otc: str = Field(default="Not found")  # OTC - One Time Charge
    
    # Sourcing Information
    sourcingChannel: str = Field(default="Not found")
    sourcingCode: str = Field(default="Not found")
    
    # Product Information
    applicationProductType: str = Field(default="Not found")
    
    # Data Validation
    dataFound: bool = Field(default=False)

class BankThreadApplications(BaseModel):
    """Model class for bank application thread data."""
    disbursements: List[BankApplication]
