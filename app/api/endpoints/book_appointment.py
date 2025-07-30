import logging
from fastapi import APIRouter, HTTPException
from app.services.database_service import database_service
from app.services.basic_application_service import BasicApplicationService
from app.models.schemas import BookAppointmentRequest, BookAppointmentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=['book_appointment'])

# Initialize services
basic_app_service = BasicApplicationService()

def validate_book_appointment_data(request:BookAppointmentRequest):
    """Validate book appointment data"""
    if not request.date or not request.time:
        raise HTTPException(status_code=422, detail="Date and time are required")
    
    if not request.reference_id:
        raise HTTPException(status_code=422, detail="Reference ID is required")


@router.post("/book_appointment", response_model=BookAppointmentResponse)
async def rm_book_appointment(request:BookAppointmentRequest):
    "Book an appointment"
    try:
        # Validate lead data
        validate_book_appointment_data(request)

        # Prepare data for Detailed Application API
        api_data = {"date": request.date, "time": request.time, "reference_id": request.reference_id} 

        # Call Basic Application API - Create Detailed Lead(CreateFBBByBasicUser)
        result = basic_app_service.create_appointment_by_basic_user(api_data)
        logger.info(f"Book appointment API call completed for reference: {request.reference_id}")

        # Save to database
        try:
            from app.services.database_service import database_service
            
            db_result = database_service.save_book_appointment_data(api_data, result)
        except Exception as db_error:
            logger.error(f"Failed to save book appointment to database. - {db_error}")
            # Don't fail the request if database save fails

        return BookAppointmentResponse(
            basic_application_id="",#result.get("basic_app_id", ""),
            message="Appointment Booked Successfully."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

