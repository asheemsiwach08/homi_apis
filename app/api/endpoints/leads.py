import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import LeadCreateRequest, LeadCreateResponse, LeadStatusRequest, LeadStatusResponse
from app.services.basic_application_service import BasicApplicationService
from app.services.whatsapp_service import whatsapp_service
from app.services.database_service import database_service
from app.utils.validators import (
    validate_loan_type, validate_loan_amount, validate_loan_tenure,
    validate_pan_number, validate_mobile_number, validate_pin_code
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["leads"])

# Initialize services
basic_app_service = BasicApplicationService()

def validate_lead_data(lead_data: LeadCreateRequest):
    """Validate lead data using utility validators"""
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

@router.post("/lead_create", response_model=LeadCreateResponse)
async def create_lead(lead_data: LeadCreateRequest):
    """Create a new lead"""
    try:
        # Validate lead data
        validate_lead_data(lead_data)
        
        # Prepare data for Basic Application API
        api_data = {
            "loan_type": lead_data.loan_type,
            "loan_amount": lead_data.loan_amount,
            "loan_tenure": lead_data.loan_tenure,
            "pan_number": lead_data.pan_number,
            "first_name": lead_data.first_name,
            "last_name": lead_data.last_name,
            "gender": lead_data.gender,
            "mobile_number": lead_data.mobile_number,
            "email": lead_data.email,
            "dob": lead_data.dob,
            "pin_code": lead_data.pin_code
        }
        
        # Call Basic Application API
        result = basic_app_service.create_lead(api_data)

        # Extract application ID from Basic API response
        basic_application_id = result.get("result", {}).get("basicAppId")
        reference_id = result.get("result", {}).get("applicationComments",{})[0].get("refId")

        if not basic_application_id:
            raise HTTPException(status_code=400, detail="Failed to generate Basic Application ID")
        
        # Save lead data to Supabase database
        try:
            db_result = database_service.save_lead_data(api_data, result)
        except Exception as db_error:
            logger.error(f"Failed to save lead to database. - {db_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save lead data to database: {str(db_error)}"
            )
        
        # Send WhatsApp confirmation for lead creation
        try:
            customer_name = f"{lead_data.first_name} {lead_data.last_name}"
            await whatsapp_service.send_lead_creation_confirmation(
                customer_name=customer_name,
                loan_type=lead_data.loan_type,
                basic_application_id=basic_application_id,
                phone_number="+91" + lead_data.mobile_number
            )
        except Exception as whatsapp_error:
            logger.error(f"Failed to send WhatsApp confirmation. - {whatsapp_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send WhatsApp confirmation: {str(whatsapp_error)}"
            )
        
        return LeadCreateResponse(
            basic_application_id=basic_application_id,
            reference_id=reference_id,
            message="Lead Created Successfully."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal server error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/lead_status", response_model=LeadStatusResponse)
async def get_lead_status(status_request: LeadStatusRequest):
    """Get lead status by various identifiers"""
    try:
        # Validate that at least one identifier is provided
        if not any([status_request.mobile_number, status_request.basic_application_id]):
            raise HTTPException(status_code=400, detail="Either mobile number or basic application ID must be provided")
        
        # Validate mobile number if provided
        if status_request.mobile_number and not validate_mobile_number(status_request.mobile_number):
            raise HTTPException(status_code=422, detail="Mobile number must be 10 digits")
        
        # Try to get status from Basic Application API using basic application ID or mobile number
        api_status = await basic_app_service.get_lead_status(
            mobile_number=status_request.mobile_number,
            basic_application_id=status_request.basic_application_id
        )
        
        if api_status:
            # Extract status from API response
            status = api_status.get("result",{}).get("latestStatus","Not found")
            message = f"Your lead status is: {status}"
            
            # Save status to Supabase database
            try:
                if status_request.basic_application_id:
                    # Update status using basic application ID
                    database_service.update_lead_status(status_request.basic_application_id, str(status))
                    logger.info(f"Status updated in database for application ID: {status_request.basic_application_id}")
                elif status_request.mobile_number:
                    # Get lead data by mobile number and update status
                    lead_data = database_service.get_lead_by_mobile(status_request.mobile_number)
                    if lead_data and lead_data.get("basic_application_id"):
                        basic_app_id = lead_data.get("basic_application_id")
                        if basic_app_id:
                            database_service.update_lead_status(str(basic_app_id), str(status))
                            logger.info(f"Status updated in database for mobile: {status_request.mobile_number}")
            except Exception as db_error:
                logger.error(f"Failed to update status in database: {db_error}")
            
            # Get mobile number for WhatsApp (either from request or database)
            mobile_number_for_whatsapp = status_request.mobile_number

            # If no mobile number in request but we have basic_application_id, try to get it from database
            if not mobile_number_for_whatsapp and status_request.basic_application_id:
                lead_data = database_service.get_lead_by_application_id(status_request.basic_application_id)
                if lead_data:
                    mobile_number_for_whatsapp = lead_data.get("mobile_number")
            
            # Send WhatsApp notification with the status
            if mobile_number_for_whatsapp:
                try:
                    lead_data = database_service.get_lead_by_mobile(mobile_number_for_whatsapp)
                    
                    if lead_data:
                        name = lead_data.get("first_name", "") + " " + lead_data.get("last_name", "")
                        
                        # Send the status update to WhatsApp
                        await whatsapp_service.send_lead_status_update(
                            phone_number="+91" + mobile_number_for_whatsapp,
                            name=name,
                            status=str(status)
                        )
                except Exception as whatsapp_error:
                    logger.error(f"Failed to send WhatsApp status update: {whatsapp_error}")
            
            return LeadStatusResponse(status=str(status), message=message)
        else:
            return LeadStatusResponse(
                status="Not Found",
                message="We couldn’t find your details. You can track your application manually at: https://www.basichomeloan.com/track-your-application"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 
