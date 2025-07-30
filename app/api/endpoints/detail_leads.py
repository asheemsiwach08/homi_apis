import logging
from fastapi import APIRouter, HTTPException
from app.services.basic_application_service import BasicApplicationService
from app.models.schemas import LeadFlashRequest, LeadCreateRequest, LeadCreateResponse, LeadFlashResponse
from app.utils.validators import (
    validate_loan_type, validate_loan_amount, validate_loan_tenure,
    validate_pan_number, validate_mobile_number, validate_pin_code,
    validate_annual_income, validate_city, validate_state, validate_credit_score ,
    validate_district, validate_email, validate_first_name, validate_last_name,
    validate_gender, validate_property_identified, validate_property_name,
    validate_estimated_property_value, validate_property_type, validate_aggrement_type,
    validate_unit_type, validate_location, validate_usage_type, validate_unit_number,
    validate_application_id
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=['leads'])

# Initialize services
basic_app_service = BasicApplicationService()

def validate_lead_create_data(lead_data: LeadCreateRequest):
    """
    Validate detailed lead data using utility validators
    
    Args:
        lead_data (LeadCreateDetailedRequest): Lead data to validate
        
    Returns:
        bool: True if validation passes
        
    Raises:
        HTTPException: If any validation fails with specific error message
    """
    if not validate_loan_type(lead_data.loanType):
        raise HTTPException(status_code=422, detail="Invalid loan type")
    
    if not validate_loan_amount(lead_data.loanAmountReq):
        raise HTTPException(status_code=422, detail="Loan amount must be greater than 0")
    
    if not validate_loan_tenure(lead_data.loanTenure):
        raise HTTPException(status_code=422, detail="Loan tenure must be greater than 0")
    
    if not validate_pan_number(lead_data.pan):
        raise HTTPException(status_code=422, detail="PAN number must be in format: ABCDE1234F")
    
    if not validate_mobile_number(lead_data.mobile):
        raise HTTPException(status_code=422, detail="Mobile number must be 10 digits")
    
    if not validate_pin_code(lead_data.pincode):
        raise HTTPException(status_code=422, detail="PIN code must be 6 digits")
    
    if not validate_credit_score(lead_data.creditScore):
        raise HTTPException(status_code=422, detail="Credit score must be between 0 and 1000")

    if not validate_email(lead_data.email):
        raise HTTPException(status_code=422, detail="Email must be a valid email address")
    
    if not validate_first_name(lead_data.firstName):
        raise HTTPException(status_code=422, detail="First name must be a valid first name")
    
    if not validate_last_name(lead_data.lastName):
        raise HTTPException(status_code=422, detail="Last name must be a valid last name")
    
    if not validate_gender(lead_data.gender):
        raise HTTPException(status_code=422, detail="Gender must be a valid gender")

    return True

def validate_lead_flash_data(lead_data: LeadFlashRequest):
    """
    Validate lead flash data using utility validators
    
    Args:
        lead_data (LeadCreateDetailedRequest): Lead data to validate
    """
    if not validate_application_id(lead_data.applicationId):
        raise HTTPException(status_code=422, detail="Application ID must be a valid application ID")
    
    if not validate_property_identified(lead_data.propertyIdentified):
        raise HTTPException(status_code=422, detail="Property identified must be a valid property identified")
    
    if not validate_property_name(lead_data.propertyName):
        raise HTTPException(status_code=422, detail="Property name must be a valid property name")
    
    if not validate_estimated_property_value(lead_data.estimatedPropertyValue):   
        raise HTTPException(status_code=422, detail="Estimated property value must be a valid estimated property value")
    
    if not validate_property_type(lead_data.propertyType):
        raise HTTPException(status_code=422, detail="Property type must be a valid property type")
    
    if not validate_aggrement_type(lead_data.agreementType):   
        raise HTTPException(status_code=422, detail="Agreement type must be a valid agreement type")
    
    if not validate_unit_type(lead_data.unitType):
        raise HTTPException(status_code=422, detail="Unit type must be a valid unit type")
    
    if not validate_location(lead_data.location):   
        raise HTTPException(status_code=422, detail="Location must be a valid location")
    
    if not validate_usage_type(lead_data.usageType):
        raise HTTPException(status_code=422, detail="Usage type must be a valid usage type")
    
    if not validate_unit_number(lead_data.unitNumber): 
        raise HTTPException(status_code=422, detail="Unit number must be a valid unit number")
    
    return True


@router.post("/create_lead", response_model=LeadCreateResponse)
async def create_lead_api(request: LeadCreateRequest):
    """
    Create a comprehensive lead through multiple API stages
    
    This endpoint creates a lead by:
    1. Validating all input data
    2. Creating FBB (First Bank Branch) record via CreateFBBByBasicUser API
    3. Extracting reference ID and Basic Application ID from response
    4. Returning successful lead creation confirmation
    
    Args:
        request (LeadCreateRequest): Complete lead information including:
            - Personal details (firstName, lastName, email, mobile, pan, dateOfBirth, gender)
            - Financial details (creditScore)
            - Loan details (loanType, loanAmountReq, loanTenure)
            - Location details (pincode)
            
    Returns:
        LeadCreateResponse: Contains:
            - basic_application_id: Unique ID for the application
            - applicationId: Application ID from FBB response
            - reference_id: Reference ID for tracking
            - message: Success confirmation message
            
    Raises:
        HTTPException: 
            - 422: Validation errors with specific field details
            - 400: API call failures or missing required data
            - 500: Internal server errors or database issues
    """
    request_id = f"{request.mobile}_{request.pan}"
    logger.info(f"Starting lead creation for {request.firstName} {request.lastName}")
    try:
        # Validate lead data
        validate_lead_create_data(request)

        # Prepare data for API calls
        api_data = {
            "creditScore": request.creditScore,
            "dateOfBirth": request.dateOfBirth,
            "email": request.email,
            "firstName": request.firstName,
            "gender": request.gender,
            "lastName": request.lastName,
            "loanAmountReq": request.loanAmountReq,
            "loanTenure": request.loanTenure,
            "loanType": request.loanType,
            "mobile": request.mobile,
            "pan": request.pan,
            "pincode": request.pincode,
        }

        # Call CreateFBBByBasicUser API
        fbb_user_result = basic_app_service.create_FBB_by_basic_user(api_data)
        
        if not fbb_user_result:
            error_msg = "Failed to create FBB record"
            if fbb_user_result and fbb_user_result.get("responseException"):
                error_msg = fbb_user_result.get("responseException", {}).get("exceptionMessage", error_msg)
            logger.error(f"CreateFBBByBasicUser API failed: {error_msg}")
            raise HTTPException(status_code=400, detail=f"FBB creation failed: {error_msg}")
     

        # Application ID
        application_id = fbb_user_result.get("result", {}).get("id", "")

        # Extract reference ID
        application_comments = fbb_user_result.get("result", {}).get("applicationComments", [])
        reference_id = ""
        
        if application_comments and len(application_comments) > 0:
            reference_id = application_comments[0].get("refId", "")
            
        if not reference_id:
            logger.error("Failed to extract reference ID from FBB response")
            raise HTTPException(status_code=400, detail="Failed to generate Reference ID")

        basic_application_id = fbb_user_result.get("result", {}).get("basicAppId", "")
        if not basic_application_id:
            logger.error("Failed to extract Basic Application ID from FBB response")
            raise HTTPException(status_code=400, detail="Failed to generate Basic Application ID")

        return LeadCreateResponse(
            basic_application_id=basic_application_id,
            applicationId=application_id,
            reference_id=reference_id,
            message="Lead Created Successfully."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in lead creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/lead_flash", response_model=LeadFlashResponse)
async def lead_flash_api(request: LeadFlashRequest):
    """
    Create a lead flash record through multiple API stages
    
    This endpoint creates a lead flash by:
    1. Validating all input data (both flash and basic lead data)
    2. Creating fulfillment record via create_fullfilment_using_application_id API
    3. Creating self fulfillment record via create_self_fullfilment_lead API
    4. Saving complete lead data to Supabase database
    
    Args:
        request (LeadFlashRequest): Complete lead flash information including:
            - All basic lead data (inherited from LeadCreateRequest)
            - Property specific details (propertyIdentified, propertyName, etc.)
            - Application ID for existing lead
            
    Returns:
        LeadFlashResponse: Contains:
            - basic_application_id: Unique ID for the application
            - reference_id: Reference ID for tracking (empty in flash)
            - message: Success confirmation message
            
    Raises:
        HTTPException: 
            - 422: Validation errors with specific field details
            - 400: API call failures or missing required data
            - 500: Internal server errors or database issues
    """
    logger.info(f"Processing lead flash request for application ID: {request.applicationId}")
    
    try:
        # Validate all input data
        validate_lead_flash_data(request)
        validate_lead_create_data(request)
        
        # Ensure application ID is provided
        if not request.applicationId:
            raise HTTPException(status_code=422, detail="Application ID is required for lead flash")
        
        # Prepare data for API calls
        api_data = {
            "firstName": request.firstName,
            "lastName": request.lastName,
            "gender": request.gender,
            "mobile": request.mobile,
            "creditScore": request.creditScore,
            "pan": request.pan,
            "loanType": request.loanType,
            "loanAmountReq": request.loanAmountReq,   
            "loanTenure": request.loanTenure,
            "pincode": request.pincode, 
            "email": request.email,
            "dateOfBirth": request.dateOfBirth,
            "applicationId": request.applicationId,
            "propertyIdentified": request.propertyIdentified,
            "propertyName": request.propertyName,
            "estimatedPropertyValue": request.estimatedPropertyValue,
            "propertyType": request.propertyType,
            "agreementType": request.agreementType,
            "unitType": request.unitType,
            "location": request.location,
            "usageType": request.usageType,
            "unitNumber": request.unitNumber
        }

        # Call Basic Fulfillment API (optional step)
        try:
            logger.info("Calling Basic Fulfillment API")
            basic_app_service.create_fullfilment_using_application_id(api_data)
            logger.info("Basic Fulfillment API completed successfully")
        except Exception as e:
            logger.warning(f"Basic Fulfillment API warning: {str(e)} - continuing with self fulfillment")
            # Continue processing even if this step fails

        # Call Self Fulfillment API (required step)
        logger.info("Calling Self Fulfillment API")
        self_fullfilment_result = basic_app_service.create_self_fullfilment_lead(api_data)
        
        if not self_fullfilment_result:
            error_msg = "Failed to create self fulfillment record"
            if self_fullfilment_result and self_fullfilment_result.get("responseException"):
                error_msg = self_fullfilment_result.get("responseException", {}).get("exceptionMessage", error_msg)
            logger.error(f"Self Fulfillment API failed: {error_msg}")
            raise HTTPException(status_code=400, detail=f"Self fulfillment failed: {error_msg}")
        
        logger.info("Self Fulfillment API completed successfully")
        
        # Extract Basic Application ID
        basic_application_id = self_fullfilment_result.get("result", {}).get("basicAppId")
        
        if not basic_application_id:
            logger.error("Failed to extract Basic Application ID from self fulfillment response")
            raise HTTPException(status_code=400, detail="Failed to generate Basic Application ID")

        # Save complete lead data to database
        try:
            logger.info("Saving lead flash data to database")
            # Import here to avoid circular imports
            from app.services.database_service import database_service
            
            db_result = database_service.save_detailed_lead_data(
                api_data, 
                self_fullfilment_result, 
                self_fullfilment_result
            )
            
            if db_result.get("success"):
                logger.info(f"Lead flash data saved to database with ID: {db_result.get('lead_id')}")
            else:
                logger.warning("Database save did not return success status")
                
        except Exception as db_error:
            logger.error(f"Database save error: {str(db_error)}")
            # Don't fail the request if database save fails - lead was created successfully

        # Return successful response
        logger.info(f"Successfully created lead flash - Basic App ID: {basic_application_id}")
        
        return LeadFlashResponse(
            basic_application_id=basic_application_id,
            reference_id="",
            message="Lead Created Successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in detailed lead creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

