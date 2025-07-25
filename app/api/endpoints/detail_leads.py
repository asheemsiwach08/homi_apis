from fastapi import APIRouter, HTTPException
from app.models.schemas import LeadCreateDetailedRequest, LeadCreateResponse
from app.services.basic_application_service import BasicApplicationService
from app.utils.validators import (
    validate_loan_type, validate_loan_amount, validate_loan_tenure,
    validate_pan_number, validate_mobile_number, validate_pin_code,
    validate_annual_income, validate_city, validate_state, validate_credit_score ,
    validate_district, validate_email, validate_first_name, validate_last_name,
    validate_gender
)


router = APIRouter(prefix="/api_v1", tags=['leads'])

# Initialize services
basic_app_service = BasicApplicationService()

def validate_detailed_lead_data(lead_data: LeadCreateDetailedRequest):
    """Validate detailed lead data using utility validators"""

    if not validate_annual_income(lead_data.annual_income):
        raise HTTPException(status_code=422, detail="Annual income must be greater than 0")

    if not validate_loan_type(lead_data.loan_type):
        raise HTTPException(status_code=422, detail="Invalid loan type")
    
    if not validate_loan_amount(lead_data.loan_amount):
        raise HTTPException(status_code=422, detail="Loan amount must be greater than 0")
    
    if not validate_loan_tenure(lead_data.loan_tenure):
        raise HTTPException(status_code=422, detail="Loan tenure must be greater than 0")
    
    if not validate_pan_number(lead_data.pan_number):
        raise HTTPException(status_code=422, detail="PAN number must be in format: ABCDE1234F")
    
    if not validate_mobile_number(lead_data.mobile_number):
        raise HTTPException(status_code=422, detail="Mobile number must be 10 digits")
    
    if not validate_pin_code(lead_data.pin_code):
        raise HTTPException(status_code=422, detail="PIN code must be 6 digits")

    if not validate_city(lead_data.city):
        raise HTTPException(status_code=422, detail="City must be a valid city name")
    
    if not validate_state(lead_data.state):
        raise HTTPException(status_code=422, detail="State must be a valid state name")

    if not validate_district(lead_data.district):
        raise HTTPException(status_code=422, detail="District must be a valid district name")
    
    if not validate_credit_score(lead_data.credit_score):
        raise HTTPException(status_code=422, detail="Credit score must be between 0 and 1000")

    if not validate_email(lead_data.email):
        raise HTTPException(status_code=422, detail="Email must be a valid email address")
    
    if not validate_first_name(lead_data.first_name):
        raise HTTPException(status_code=422, detail="First name must be a valid first name")
    
    if not validate_last_name(lead_data.last_name):
        raise HTTPException(status_code=422, detail="Last name must be a valid last name")
    
    if not validate_gender(lead_data.gender):
        raise HTTPException(status_code=422, detail="Gender must be a valid gender")

    return True 

@router.post("/detailed_leads_creation", response_model=LeadCreateResponse)
async def detailed_leads_creation(request:LeadCreateDetailedRequest):
    "Create a new detailed lead"
    try:
        # Validate lead data
        validate_detailed_lead_data(request)

        # Prepare data for Detailed Application API
        api_data = {"annual_income": request.annual_income,
                "city": request.city,
                "credit_score": request.credit_score,
                "date_of_birth": request.dob,
                "district": request.district,
                "email": request.email,
                "first_name": request.first_name,
                "gender": request.gender,
                "last_name": request.last_name,
                "loan_amount_req": request.loan_amount,
                "loan_tenure": request.loan_tenure,
                "loan_type": request.loan_type,
                "mobile": request.mobile_number,
                "pan": request.pan_number,
                "pincode": request.pin_code,
                "state": request.state}

        # Call Basic Application API - Create Detailed Lead(CreateFBBByBasicUser)
        fbb_user_result = await basic_app_service.create_FBB_by_basic_user(api_data)
        print("FBB User Result: ", fbb_user_result)

        self_fullfilment_result = await basic_app_service.create_self_fullfilment_lead(api_data)



        # Extract application ID from Basic API response
        basic_application_id = fbb_user_result.get("result", {}).get("basicAppId")

        if not basic_application_id:
            raise HTTPException(status_code=400, detail="Failed to generate Basic Application ID")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

