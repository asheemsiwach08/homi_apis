import logging
from fastapi import APIRouter, HTTPException
from app.services.basic_application_service import BasicApplicationService
from app.models.schemas import LeadCreateDetailedRequest, LeadCreateDetailedResponse
from app.utils.validators import (
    validate_loan_type, validate_loan_amount, validate_loan_tenure,
    validate_pan_number, validate_mobile_number, validate_pin_code,
    validate_annual_income, validate_city, validate_state, validate_credit_score ,
    validate_district, validate_email, validate_first_name, validate_last_name,
    validate_gender
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=['detailed_leads'])

# Initialize services
basic_app_service = BasicApplicationService()

def validate_detailed_lead_data(lead_data: LeadCreateDetailedRequest):
    """
    Validate detailed lead data using utility validators
    
    Args:
        lead_data (LeadCreateDetailedRequest): Lead data to validate
        
    Returns:
        bool: True if validation passes
        
    Raises:
        HTTPException: If any validation fails with specific error message
    """
    
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

@router.post("/detailed_leads_create", response_model=LeadCreateDetailedResponse)
async def detailed_leads_creation(request: LeadCreateDetailedRequest):
    """
    Create a comprehensive detailed lead through multiple API stages
    
    This endpoint creates a detailed lead by:
    1. Validating all input data
    2. Creating FBB (First Bank Branch) record via CreateFBBByBasicUser API
    3. Creating Basic Fulfillment record via create_fullfilment_using_application_id API
    4. Creating Self Fulfillment record via create_self_fullfilment_lead API
    5. Saving complete lead data to Supabase database
    
    Args:
        request (LeadCreateDetailedRequest): Complete lead information including:
            - Personal details (name, email, mobile, PAN, DOB, gender)
            - Financial details (annual income, credit score)
            - Loan details (type, amount, tenure)
            - Location details (city, district, state, pin code)
            
    Returns:
        LeadCreateDetailedResponse: Contains:
            - basic_application_id: Unique ID for the application
            - reference_id: Reference ID for tracking
            - message: Success confirmation message
            
    Raises:
        HTTPException: 
            - 422: Validation errors with specific field details
            - 400: API call failures or missing required data
            - 500: Internal server errors or database issues
    """
    request_id = f"{request.mobile_number}_{request.pan_number}"
    logger.info(f"Starting detailed lead creation for {request.first_name} {request.last_name}")
    
    try:
        # Validate lead data
        validate_detailed_lead_data(request)

        # Prepare data for API calls
        api_data = {
            "annual_income": request.annual_income,
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
            "state": request.state
        }

        # Call CreateFBBByBasicUser API
        fbb_user_result = basic_app_service.create_FBB_by_basic_user(api_data)
        print(fbb_user_result,"-------------->>")
        
        if not fbb_user_result:
            print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            error_msg = "Failed to create FBB record"
            if fbb_user_result and fbb_user_result.get("responseException"):
                error_msg = fbb_user_result.get("responseException", {}).get("exceptionMessage", error_msg)
            logger.error(f"CreateFBBByBasicUser API failed: {error_msg}")
            raise HTTPException(status_code=400, detail=f"FBB creation failed: {error_msg}")

        # Extract reference ID
        application_comments = fbb_user_result.get("result", {}).get("applicationComments", [])
        reference_id = ""
        
        if application_comments and len(application_comments) > 0:
            reference_id = application_comments[0].get("refId", "")
        
        if not reference_id:
            # Try alternative extraction methods
            reference_id = fbb_user_result.get("result", {}).get("id", "")
            
        if not reference_id:
            logger.error("Failed to extract reference ID from FBB response")
            raise HTTPException(status_code=400, detail="Failed to generate Reference ID")

        # Prepare data for subsequent API calls
        fbb_result = fbb_user_result.get("result", {})
        primary_borrower = fbb_result.get("primaryBorrower", {})
        
        # Update api_data with FBB response data
        api_data["id"] = fbb_result.get("id", "")
        api_data["customerId"] = primary_borrower.get("customerId", "")
        api_data["existingEmis"] = fbb_result.get("existingEmis", 0)
        api_data["isLeadPrefilled"] = fbb_result.get("isLeadPrefilled", True)
        api_data["applicationAssignedToRm"] = fbb_result.get("applicationAssignedToRm", "")
        
        if not api_data["id"]:
            logger.error("Missing application ID from FBB response")
            raise HTTPException(status_code=400, detail="Missing application ID from FBB response")

        # Call Basic Fulfillment API
        try:
            basic_app_service.create_fullfilment_using_application_id(api_data)
        except Exception as e:
            logger.warning(f"Basic Fulfillment API warning: {str(e)}")
            # Continue processing even if this step fails

        # Call Self Fulfillment API
        self_fullfilment_result = basic_app_service.create_self_fullfilment_lead(api_data)
        
        if not self_fullfilment_result:
            error_msg = "Failed to create self fulfillment record"
            if self_fullfilment_result and self_fullfilment_result.get("responseException"):
                error_msg = self_fullfilment_result.get("responseException", {}).get("exceptionMessage", error_msg)
            logger.error(f"Self Fulfillment API failed: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Self fulfillment failed: {error_msg}")
        
        # Extract Basic Application ID
        basic_application_id = self_fullfilment_result.get("result", {}).get("basicAppId")
        
        if not basic_application_id:
            logger.error("Failed to extract Basic Application ID from self fulfillment response")
            raise HTTPException(status_code=400, detail="Failed to generate Basic Application ID")

        # Save to database
        try:
            # Import here to avoid circular imports
            from app.services.database_service import database_service
            
            db_result = database_service.save_detailed_lead_data(
                api_data, 
                fbb_user_result, 
                self_fullfilment_result
            )
            
            if db_result.get("success"):
                logger.info(f"Detailed lead saved to database with ID: {db_result.get('lead_id')}")
                
        except Exception as db_error:
            logger.error(f"Database save error: {str(db_error)}")
            # Don't fail the request if database save fails

        # Return successful response
        logger.info(f"Successfully created detailed lead - Basic App ID: {basic_application_id}")
        
        return LeadCreateDetailedResponse(
            basic_application_id=basic_application_id,
            reference_id=reference_id,
            message="Lead Created Successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in detailed lead creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

