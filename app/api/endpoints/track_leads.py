import logging
from fastapi import APIRouter, HTTPException
from app.utils.validators import validate_mobile_number
from app.services.whatsapp_service import whatsapp_service
from app.services.database_service import database_service
from app.services.basic_application_service import BasicApplicationService
from app.models.schemas import (LeadStatusRequest, LeadStatusResponse,
                                BookAppointmentRequest, BookAppointmentResponse)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["track_leads"])

# Initialize services
basic_app_service = BasicApplicationService()

############################################################################################
                                # Validate Book Appointment Data
############################################################################################

def validate_book_appointment_data(request:BookAppointmentRequest):
    """Validate book appointment data"""
    if not request.environment:
        raise HTTPException(status_code=422, detail="Environment is required")
    
    if not request.date or not request.time:
        raise HTTPException(status_code=422, detail="Date and time are required")
    
    if not request.reference_id:
        raise HTTPException(status_code=422, detail="Reference ID is required")


############################################################################################
                                 # Lead Status API #
############################################################################################

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
            
            # Save status to Supabase leads database
            try:
                if status_request.basic_application_id:
                    # Update status using basic application ID in leads table
                    database_service.update_lead_status(status_request.basic_application_id, str(status), environment=status_request.environment)
                    logger.info(f"Status updated in leads database for application ID: {status_request.basic_application_id}")
                elif status_request.mobile_number:
                    # Get lead data by mobile number from leads table and update status
                    lead_data_list = database_service.get_leads_by_mobile(status_request.mobile_number, environment=status_request.environment)
                    if lead_data_list:
                        # Get the most recent lead (first in the list since ordered by created_at desc)
                        lead_data = lead_data_list[0]
                        basic_app_id = lead_data.get("basic_app_id")
                        if basic_app_id:
                            database_service.update_lead_status(str(basic_app_id), str(status), environment=status_request.environment)
                            logger.info(f"Status updated in leads database for mobile: {status_request.mobile_number}")
            except Exception as db_error:
                logger.error(f"Failed to update status in leads database: {db_error}")
            
            # Get mobile number for WhatsApp (either from request or database)
            mobile_number_for_whatsapp = status_request.mobile_number

            # If no mobile number in request but we have basic_application_id, try to get it from leads database
            if not mobile_number_for_whatsapp and status_request.basic_application_id:
                lead_data_list = database_service.get_leads_by_basic_app_id(status_request.basic_application_id, environment=status_request.environment)
                if lead_data_list:
                    lead_data = lead_data_list[0]  # Get the most recent record
                    mobile_number_for_whatsapp = lead_data.get("customer_mobile")
            
            # Send WhatsApp notification with the status
            if mobile_number_for_whatsapp:
                try:
                    lead_data_list = database_service.get_leads_by_mobile(mobile_number_for_whatsapp, environment=status_request.environment)
                    
                    if lead_data_list:
                        lead_data = lead_data_list[0]  # Get the most recent record
                        name = lead_data.get("customer_first_name", "") + " " + lead_data.get("customer_last_name", "")
                        
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


############################################################################################
                                # Book Appointment API #
############################################################################################

@router.post("/book_appointment", response_model=BookAppointmentResponse)
async def rm_book_appointment(request:BookAppointmentRequest):
    "Book an appointment"
    try:
        # Validate lead data
        validate_book_appointment_data(request)

        # Prepare data for Application API
        api_data = {"date": request.date, "time": request.time, "reference_id": request.reference_id} 

        # Call Basic Application API - Create Lead(CreateAppointmentByBasicUser)
        result = basic_app_service.create_appointment_by_basic_user(api_data)
        logger.info(f"Book appointment API call completed for reference: {request.reference_id}")

        basic_app_id = result.get("result",{}).get("basicAppId", "")
        if not basic_app_id:
            raise HTTPException(status_code=400, detail="Failed to get basic application ID")
        
        # Save to database
        try:
            from app.services.database_service import database_service
            
            db_result = database_service.save_book_appointment_data(api_data, result, environment=request.environment)
        except Exception as db_error:
            logger.error(f"Failed to save book appointment to database. - {db_error}")
            # Don't fail the request if database save fails

        return BookAppointmentResponse(
            basic_application_id=basic_app_id,
            message="Appointment Booked Successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

