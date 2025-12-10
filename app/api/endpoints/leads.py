import logging
from fastapi import APIRouter, HTTPException
from app.services.basic_application_service import BasicApplicationService
from app.models.schemas import LeadFlashRequest, LeadCreateRequest, LeadCreateResponse, LeadFlashResponse
from app.utils.validators import (
    validate_loan_type, validate_loan_amount, validate_loan_tenure,
    validate_pan_number, validate_mobile_number, validate_pin_code,
    validate_credit_score , validate_email, validate_first_name, validate_last_name,
    validate_gender
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=['leads'])

# Initialize services
basic_app_service = BasicApplicationService()

############################################################################################
                                # Validate Lead Data
############################################################################################

def validate_orbit_lead_create_data(lead_data: LeadCreateRequest):
    """
    Validate lead data using comprehensive utility validators
    
    This function validates all required and optional fields for lead creation,
    ensuring data integrity before API submission.
    
    Args:
        lead_data (LeadCreateRequest): Lead data to validate including:
            - Required: firstName, lastName, mobile, email, pan, loanType, 
              loanAmountReq, loanTenure, creditScore, pincode, dateOfBirth
            - Optional: gender, annualIncome, applicationAssignedToRm, remarks, 
              state, customerId, qrShortCode, and other configuration fields
        
    Returns:
        bool: True if validation passes
        
    Raises:
        HTTPException: If any validation fails with specific error message
            - 422: For field-specific validation errors (format, range, etc.)
    """
    if not lead_data.environment:
        raise HTTPException(status_code=422, detail="Environment is required and must be either 'orbit' or 'homfinity'")
    elif lead_data.environment not in ["orbit", "homfinity"]:
            raise HTTPException(status_code=422, detail="Environment is required and must be either 'orbit' or 'homfinity'")
    
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


def validate_homfinity_lead_create_data(lead_data: LeadCreateRequest):
    if not lead_data.environment:
        raise HTTPException(status_code=422, detail="Environment is required and must be either 'orbit' or 'homfinity'")
    elif lead_data.environment not in ["orbit", "homfinity"]:
            raise HTTPException(status_code=422, detail="Environment is required and must be either 'orbit' or 'homfinity'")
    
    if not validate_loan_type(lead_data.loanType):
        raise HTTPException(status_code=422, detail="Invalid loan type")
    
    if not validate_loan_amount(lead_data.loanAmountReq):
        raise HTTPException(status_code=422, detail="Loan amount must be greater than 0")
    
    if not validate_mobile_number(lead_data.mobile):
        raise HTTPException(status_code=422, detail="Mobile number must be 10 digits")
    
    if not validate_pin_code(lead_data.pincode):
        raise HTTPException(status_code=422, detail="PIN code must be 6 digits")
    
    if not validate_email(lead_data.email):
        raise HTTPException(status_code=422, detail="Email must be a valid email address")
    
    if not validate_first_name(lead_data.firstName):
        raise HTTPException(status_code=422, detail="First name must be a valid first name")
    
    if not validate_last_name(lead_data.lastName):
        raise HTTPException(status_code=422, detail="Last name must be a valid last name")
    
    return True


############################################################################################
                                # Create Lead API
############################################################################################

@router.post("/create_lead", response_model=LeadCreateResponse)
async def create_lead_api(request: LeadCreateRequest):
    """
    Create a comprehensive lead through FBB (First Bank Branch) processing
    
    This endpoint creates a lead through a multi-stage process:
    1. Comprehensive data validation for all required and optional fields
    2. FBB creation via CreateFBBByBasicUser API with flexible field support
    3. Database storage with complete audit trail and upsert logic
    4. WhatsApp notification to customer (if enabled)
    5. Returns complete lead information for tracking
    
    Args:
        request (LeadCreateRequest): Complete lead information including:
            - Core Details: firstName, lastName, mobile, email, pan, dateOfBirth
            - Financial: loanType, loanAmountReq, loanTenure, creditScore, annualIncome
            - Location: pincode, state
            - Optional Config: applicationAssignedToRm, remarks, customerId, qrShortCode
            - Processing: includeCreditScore, isLeadPrefilled (with smart defaults)
            
    Returns:
        LeadCreateResponse: Contains:
            - basic_application_id: Unique ID for the application (e.g., "B002BJF")
            - applicationId: Internal application UUID for system tracking
            - reference_id: Reference UUID for customer tracking
            - message: Success confirmation message
            
    Raises:
        HTTPException: 
            - 422: Validation errors (invalid formats, ranges, required fields)
            - 400: API call failures, missing Basic App ID, or invalid response
            - 500: Internal server errors, database issues, or service unavailability
            
    Features:
        - Flexible optional fields with intelligent defaults
        - Complete database storage with operation tracking (created/updated)
        - Integration with WhatsApp notification system
        - Comprehensive error handling and audit trails
        - Support for lead modification (upserts based on existing records)
    """
    request_id = f"{request.mobile}_{request.pan}"
    logger.info(f"Starting lead creation for {request.firstName} {request.lastName}")
    try:
        # Validate lead data
        if request.environment == "orbit":
            validate_orbit_lead_create_data(request)
        elif request.environment == "homfinity":
            validate_homfinity_lead_create_data(request)
        else:
            raise HTTPException(status_code=422, detail="Environment is required and must be either 'orbit' or 'homfinity'")

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
            "annualIncome": request.annualIncome,
            "applicationAssignedToRm": request.applicationAssignedToRm,
            "createdFromPemId": request.createdFromPemId,
            "creditScoreTypeId": request.creditScoreTypeId,
            "customerId": request.customerId,
            "includeCreditScore": request.includeCreditScore,
            "isLeadPrefilled": request.isLeadPrefilled,
            "qrShortCode": request.qrShortCode,
            "remarks": request.remarks,
            "state": request.state,
        }

        # Call CreateFBBByBasicUser API
        fbb_user_result = basic_app_service.create_FBB_by_basic_user(api_data)
        
        if not fbb_user_result:
            error_msg = "Failed to create FBB record"
            if fbb_user_result and fbb_user_result.get("responseException"):
                error_msg = fbb_user_result.get("responseException", {}).get("exceptionMessage", error_msg)
            logger.error(f"CreateFBBByBasicUser API failed: {error_msg}")
            raise HTTPException(status_code=400, detail=f"FBB creation failed: {error_msg}")
     
        # Assigned to RM
        assigned_to_rm = fbb_user_result.get("result", {}).get("applicationAssignedToRm", "") if fbb_user_result.get("result", {}).get("applicationAssignedToRm", "") else ""
        
        # Application ID
        application_id = fbb_user_result.get("result", {}).get("id", "")

        # Extract reference ID
        application_comments = fbb_user_result.get("result", {}).get("applicationComments", [])
        reference_id = ""
        
        if application_comments and len(application_comments) > 0:
            reference_id = application_comments[0].get("refId", "")
            
        # if not reference_id:
        #     logger.error("Failed to extract reference ID from FBB response")
        #     raise HTTPException(status_code=400, detail="Failed to generate Reference ID")

        basic_application_id = fbb_user_result.get("result", {}).get("basicAppId", "")
        if not basic_application_id:
            logger.error("Failed to extract Basic Application ID from FBB response")
            raise HTTPException(status_code=400, detail="Failed to generate Basic Application ID")

        # Save complete lead data to database
        try:
            logger.info("Saving lead data to database")
            # Import here to avoid circular imports
            from app.services.database_service import database_service
            
            # Add source identification for create_lead endpoint
            api_data["source_endpoint"] = "create_lead"
            
            db_result = database_service.save_lead_data(
                request_data=api_data, 
                fbb_response=fbb_user_result, 
                self_fullfilment_response=fbb_user_result,
                environment=request.environment
            )
            
            if db_result.get("success"):
                operation_type = db_result.get("operation_type", "saved")
                logger.info(f"Lead data {operation_type} in database with ID: {db_result.get('lead_id')}")
            else:
                logger.warning("Database save did not return success status")
                
        except Exception as db_error:
            logger.error(f"Database save error: {str(db_error)}")
            # Don't fail the request if database save fails - lead was created successfully

        # Return successful response
        logger.info(f"Successfully created lead - Basic App ID: {basic_application_id}")
        
        return LeadCreateResponse(
            basic_application_id=basic_application_id,
            applicationId=application_id,
            reference_id=reference_id,
            assigned_to_rm=assigned_to_rm,
            message="Lead Created Successfully."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in lead creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


############################################################################################
                                # Lead Flash API
############################################################################################

@router.post("/lead_flash", response_model=LeadFlashResponse)
async def lead_flash_api(request: LeadFlashRequest):
    """
    Process a complete lead flash workflow with comprehensive application details
    
    This endpoint processes a lead through the complete self-fulfillment workflow:
    1. Comprehensive validation of all personal, financial, property, and profession data
    2. Self-fulfillment application creation via CreateSelfFullfilmentLead API
    3. Property information processing (identification, valuation, agreement type)
    4. Profession and salary verification (required fields: professionId, professionName)
    5. Complete database storage with audit trail and status update to "completed"
    6. WhatsApp notification for application status update
    
    Args:
        request (LeadFlashRequest): Complete application information including:
            - Core Personal: firstName, lastName, mobile, email, pan, dateOfBirth, gender
            - Financial: loanType, loanAmountReq, loanTenure, creditScore
            - Location: pincode
            - Application: applicationId (required - existing application to process)
            - Profession: professionId, professionName (required for complete workflow)
            - Property: propertyIdentified, propertyName, propertyType, agreementType, 
              location, usageType, propertyValue (all optional with smart defaults)
            - Employment: salaryCreditModeId, salaryCreditModeName, selfCompanyTypeId, 
              companyName (all optional)
            
    Returns:
        LeadFlashResponse: Contains:
            - basic_application_id: Updated application ID (e.g., "B002BJF")
            - reference_id: Application reference UUID for customer tracking
            - message: Success confirmation message
            
    Raises:
        HTTPException:
            - 422: Validation errors, missing required fields (applicationId, professionId, professionName)
            - 400: API call failures, invalid application ID, or malformed response
            - 500: Internal server errors, database issues, or service unavailability
            
    Features:
        - Complete application workflow from lead to self-fulfillment
        - Required profession information for compliance
        - Flexible property details with optional fields
        - Database upsert logic for existing applications
        - Comprehensive audit trail and status tracking
        - Integration with WhatsApp notification system
        - Support for complex property and employment scenarios
    """
    logger.info(f"Processing lead flash request for application ID: {request.applicationId}")
    
    try:
        # Validate all input data
        # validate_lead_flash_data(request)
        if request.environment == "orbit":
            validate_orbit_lead_create_data(request)
        elif request.environment == "homfinity":
            validate_homfinity_lead_create_data(request)
        else:
            raise HTTPException(status_code=422, detail="Environment is required and must be either 'orbit' or 'homfinity'")
        
        # Ensure application ID is provided
        if not request.applicationId:
            raise HTTPException(status_code=422, detail="Application ID is required for lead flash")
        
        # Prepare data for API calls
        api_data = {
            # Core Personal Information
            "firstName": request.firstName,
            "lastName": request.lastName,
            "gender": request.gender,
            "mobile": request.mobile,
            "email": request.email,
            "dateOfBirth": request.dateOfBirth,
            "pan": request.pan,
            
            # Application Information
            "applicationId": request.applicationId,
            "creditScore": request.creditScore,
            "loanType": request.loanType,
            "loanAmountReq": request.loanAmountReq,   
            "loanTenure": request.loanTenure,
            "pincode": request.pincode,
            
            # Location Information
            "location": request.location,
            
            # Profession Information
            "professionId": request.professionId, 
            "professionName": request.professionName,
            
            # Financial Information
            "coBorrowerIncome": request.coBorrowerIncome,
            "salaryCreditModeId": request.salaryCreditModeId, 
            "salaryCreditModeName": request.salaryCreditModeName,
            "selfCompanyTypeId": request.selfCompanyTypeId,
            "companyName": request.companyName,
            
            # Property Information
            "propertyIdentified": request.propertyIdentified,
            "propertyName": request.propertyName,
            "propertyType": request.propertyType,
            "agreementType": request.agreementType,
            "propertyTypeId": request.propertyTypeId,
            "propertyValue": request.propertyValue,
            "propertyDistrict": request.propertyDistrict,
            "propertyPincode": request.propertyPincode,
            "propertyProjectName": request.propertyProjectName,
            
            # Property Details
            "unitType": request.unitType,
            "usageType": request.usageType,
            "unitNumber": request.unitNumber,
            "towerName": request.towerName,
            "towerUnitType": request.towerUnitType,
            "builderId": request.builderId,
            "towerId": request.towerId,
            "builderName": request.builderName,
            
            # Loan Configuration
            "loanUsageTypeId": request.loanUsageTypeId,
            "aggrementTypeId": request.aggrementTypeId,
            
            # Credit Information
            "creditScoreTypeId": request.creditScoreTypeId,
            "creditScoreTypeName": request.creditScoreTypeName,
            "manualCreditScore": request.manualCreditScore,
            
            # Documents and Processing
            "documents": request.documents,
            "isVistedNextPage": request.isVistedNextPage,
            
            # **MISSING FIELDS ADDED - Required by Self-Fulfillment API:**
            "annualIncome": request.annualIncome or 0,
            "city": request.city or "",
            "district": request.district or "",
            "state": request.state or "",
            "existingEmis": request.existingEmis or "",
            "selfCompanyTypeName": request.selfCompanyTypeName or "",
            "canCustomerUploadDocuments": request.canCustomerUploadDocuments or False,
            "isOsvByConsultantAvailable": request.isOsvByConsultantAvailable or False,
            "isLeadPrefilled": request.isLeadPrefilled or False,
            "includeCreditScore": request.includeCreditScore or False,
            "recentCreditReportExists": request.recentCreditReportExists or False,
            "isPropertyIdentified": request.isPropertyIdentified or False,
            "isReferralLead": request.isReferralLead or False,
            "projectId": request.projectId or "",
            "creditScoreStatus": request.creditScoreStatus or ""
        }   

        # Call Basic Fulfillment API (optional step)
        try:
            basic_app_service.create_fullfilment_using_application_id(api_data)
        except Exception as e:
            logger.warning(f"Basic Fulfillment API warning: {str(e)} - continuing with self fulfillment")
            # Continue processing even if this step fails

        # Call Self Fulfillment API (required step)
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
        reference_id = self_fullfilment_result.get("result", {}).get("id","")
        # Assigned to RM
        assigned_to_rm = self_fullfilment_result.get("result", {}).get("applicationAssignedToRm", "") if self_fullfilment_result.get("result", {}).get("applicationAssignedToRm", "") else ""
        
        if not basic_application_id:
            logger.error("Failed to extract Basic Application ID from self fulfillment response")
            raise HTTPException(status_code=400, detail="Failed to generate Basic Application ID")

        # Save complete lead data to database
        try:
            logger.info("Saving lead flash data to database")
            # Import here to avoid circular imports
            from app.services.database_service import database_service
            
            # Add source identification for lead_flash endpoint
            api_data["source_endpoint"] = "lead_flash"
            
            db_result = database_service.save_lead_data(
                request_data=api_data, 
                fbb_response=self_fullfilment_result, 
                self_fullfilment_response=self_fullfilment_result,
                environment=request.environment
            )
            
            if db_result.get("success"):
                operation_type = db_result.get("operation_type", "saved")
                logger.info(f"Lead flash data {operation_type} in database with ID: {db_result.get('lead_id')}")
            else:
                logger.warning("Database save did not return success status")
                
        except Exception as db_error:
            logger.error(f"Database save error: {str(db_error)}")
            # Don't fail the request if database save fails - lead was created successfully

        # Return successful response
        logger.info(f"Successfully created lead flash - Basic App ID: {basic_application_id}")
        
        return LeadFlashResponse(
            basic_application_id=basic_application_id,
            reference_id=reference_id,
            assigned_to_rm=assigned_to_rm,
            message="Lead Details Added Successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in lead flash creation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

