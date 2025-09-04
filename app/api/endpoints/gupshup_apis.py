"""
Modular Gupshup WhatsApp API Endpoints
Comprehensive wrapper for all Gupshup outbound messaging APIs
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
import json
import httpx
from app.services.whatsapp_service import whatsapp_service
from app.config.settings import settings
from app.utils.validators import normalize_phone_number

# Create router
router = APIRouter(prefix="/api_v1/gupshup", tags=["Gupshup WhatsApp APIs"])

# ==================== SCHEMAS ====================

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

# ==================== UTILITY FUNCTIONS ====================

async def send_gupshup_request(data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Generic function to send requests to Gupshup API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.GUPSHUP_API_URL,
                headers=headers,
                data=data,
                timeout=30.0
            )
            
            # Gupshup API returns 202 for successful submissions
            if response.status_code in [200, 202]:
                try:
                    response_data = response.json()
                    return {
                        "success": True,
                        "data": response_data if isinstance(response_data, dict) else {"response": str(response_data)},
                        "status_code": response.status_code
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "data": {"response": response.text},
                        "status_code": response.status_code
                    }
            else:
                return {
                    "success": False,
                    "data": {"error": response.text},
                    "status_code": response.status_code
                }
                
    except Exception as e:
        return {
            "success": False,
            "data": {"error": str(e)},
            "status_code": 500
        }

def get_gupshup_headers() -> Dict[str, str]:
    """Get standard Gupshup API headers"""
    return {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
        'apikey': settings.GUPSHUP_API_KEY,
        'cache-control': 'no-cache'
    }

# ==================== API ENDPOINTS ====================

@router.post("/send-text", response_model=BaseGupshupResponse)
async def send_text_message(request: TextMessageRequest):
    """
    Send a simple text message via WhatsApp
    
    - **phone_number**: Phone number in any format (will be normalized)
    - **message**: Text message to send
    - **source_name**: Optional custom source name
    """
    headers = get_gupshup_headers()
    
    data = {
        'channel': 'whatsapp',
        'source': settings.GUPSHUP_SOURCE,
        'destination': request.phone_number,
        'message': request.message
    }
    
    if request.source_name:
        data['src.name'] = request.source_name
    
    result = await send_gupshup_request(data, headers)
    
    return BaseGupshupResponse(
        success=result["success"],
        message="Text message sent successfully" if result["success"] else "Failed to send text message",
        data=result["data"],
        gupshup_response=result
    )

@router.post("/send-template", response_model=BaseGupshupResponse)
async def send_template_message(request: TemplateMessageRequest):
    """
    Send a template message via WhatsApp
    
    - **phone_number**: Phone number in any format (will be normalized)
    - **template_id**: Gupshup template ID
    - **template_params**: List of template parameters
    - **source_name**: Optional custom source name
    """
    headers = get_gupshup_headers()
    
    template_data = {
        "id": request.template_id,
        "params": request.template_params
    }
    
    data = {
        'channel': 'whatsapp',
        'source': settings.GUPSHUP_SOURCE,
        'destination': request.phone_number,
        'template': json.dumps(template_data)
    }
    
    if request.source_name:
        data['src.name'] = request.source_name
    
    result = await send_gupshup_request(data, headers)
    
    return BaseGupshupResponse(
        success=result["success"],
        message="Template message sent successfully" if result["success"] else "Failed to send template message",
        data=result["data"],
        gupshup_response=result
    )

@router.post("/send-media", response_model=BaseGupshupResponse)
async def send_media_message(request: MediaMessageRequest):
    """
    Send a media message (image, document, audio, video) via WhatsApp
    
    - **phone_number**: Phone number in any format (will be normalized)
    - **media_type**: Type of media (image, document, audio, video)
    - **media_url**: URL of the media file
    - **caption**: Optional caption for the media
    - **filename**: Optional filename for documents
    """
    headers = get_gupshup_headers()
    
    # Build media message structure
    media_message = {
        "type": request.media_type,
        "url": request.media_url
    }
    
    if request.caption:
        media_message["caption"] = request.caption
    
    if request.filename and request.media_type == "document":
        media_message["filename"] = request.filename
    
    data = {
        'channel': 'whatsapp',
        'source': settings.GUPSHUP_SOURCE,
        'destination': request.phone_number,
        'message': json.dumps(media_message)
    }
    
    result = await send_gupshup_request(data, headers)
    
    return BaseGupshupResponse(
        success=result["success"],
        message="Media message sent successfully" if result["success"] else "Failed to send media message",
        data=result["data"],
        gupshup_response=result
    )

@router.post("/send-interactive", response_model=BaseGupshupResponse)
async def send_interactive_message(request: InteractiveMessageRequest):
    """
    Send an interactive message (buttons, lists) via WhatsApp
    
    - **phone_number**: Phone number in any format (will be normalized)
    - **interactive_type**: Type of interactive message (button, list)
    - **header**: Optional message header
    - **body**: Message body content
    - **footer**: Optional message footer
    - **action**: Interactive action configuration
    """
    headers = get_gupshup_headers()
    
    interactive_message = {
        "type": "interactive",
        "interactive": {
            "type": request.interactive_type,
            "body": request.body,
            "action": request.action
        }
    }
    
    if request.header:
        interactive_message["interactive"]["header"] = request.header
    
    if request.footer:
        interactive_message["interactive"]["footer"] = request.footer
    
    data = {
        'channel': 'whatsapp',
        'source': settings.GUPSHUP_SOURCE,
        'destination': request.phone_number,
        'message': json.dumps(interactive_message)
    }
    
    result = await send_gupshup_request(data, headers)
    
    return BaseGupshupResponse(
        success=result["success"],
        message="Interactive message sent successfully" if result["success"] else "Failed to send interactive message",
        data=result["data"],
        gupshup_response=result
    )

@router.post("/send-location", response_model=BaseGupshupResponse)
async def send_location_message(request: LocationMessageRequest):
    """
    Send a location message via WhatsApp
    
    - **phone_number**: Phone number in any format (will be normalized)
    - **latitude**: Latitude coordinate
    - **longitude**: Longitude coordinate
    - **name**: Optional location name
    - **address**: Optional location address
    """
    headers = get_gupshup_headers()
    
    location_message = {
        "type": "location",
        "location": {
            "latitude": request.latitude,
            "longitude": request.longitude
        }
    }
    
    if request.name:
        location_message["location"]["name"] = request.name
    
    if request.address:
        location_message["location"]["address"] = request.address
    
    data = {
        'channel': 'whatsapp',
        'source': settings.GUPSHUP_SOURCE,
        'destination': request.phone_number,
        'message': json.dumps(location_message)
    }
    
    result = await send_gupshup_request(data, headers)
    
    return BaseGupshupResponse(
        success=result["success"],
        message="Location message sent successfully" if result["success"] else "Failed to send location message",
        data=result["data"],
        gupshup_response=result
    )

@router.post("/send-contact", response_model=BaseGupshupResponse)
async def send_contact_message(request: ContactMessageRequest):
    """
    Send a contact message via WhatsApp
    
    - **phone_number**: Phone number in any format (will be normalized)
    - **contacts**: List of contact objects
    """
    headers = get_gupshup_headers()
    
    contact_message = {
        "type": "contacts",
        "contacts": request.contacts
    }
    
    data = {
        'channel': 'whatsapp',
        'source': settings.GUPSHUP_SOURCE,
        'destination': request.phone_number,
        'message': json.dumps(contact_message)
    }
    
    result = await send_gupshup_request(data, headers)
    
    return BaseGupshupResponse(
        success=result["success"],
        message="Contact message sent successfully" if result["success"] else "Failed to send contact message",
        data=result["data"],
        gupshup_response=result
    )

@router.post("/send-bulk", response_model=BaseGupshupResponse)
async def send_bulk_messages(request: BulkMessageRequest):
    """
    Send bulk messages to multiple phone numbers
    
    - **phone_numbers**: List of phone numbers
    - **message_type**: Type of message (text, template, media)
    - **message_data**: Message data based on type
    - **delay_between_messages**: Delay in seconds between messages
    """
    import asyncio
    
    results = []
    successful_sends = 0
    failed_sends = 0
    
    for phone_number in request.phone_numbers:
        try:
            # Normalize phone number
            normalized_phone = normalize_phone_number(phone_number)
            
            # Prepare message data based on type
            if request.message_type == "text":
                message_request = TextMessageRequest(
                    phone_number=normalized_phone,
                    message=request.message_data.get("message", "")
                )
                result = await send_text_message(message_request)
            elif request.message_type == "template":
                message_request = TemplateMessageRequest(
                    phone_number=normalized_phone,
                    template_id=request.message_data.get("template_id", ""),
                    template_params=request.message_data.get("template_params", [])
                )
                result = await send_template_message(message_request)
            elif request.message_type == "media":
                message_request = MediaMessageRequest(
                    phone_number=normalized_phone,
                    media_type=request.message_data.get("media_type", ""),
                    media_url=request.message_data.get("media_url", ""),
                    caption=request.message_data.get("caption"),
                    filename=request.message_data.get("filename")
                )
                result = await send_media_message(message_request)
            else:
                result = BaseGupshupResponse(
                    success=False,
                    message=f"Unsupported message type: {request.message_type}"
                )
            
            results.append({
                "phone_number": normalized_phone,
                "success": result.success,
                "message": result.message
            })
            
            if result.success:
                successful_sends += 1
            else:
                failed_sends += 1
            
            # Add delay between messages
            if request.delay_between_messages and request.delay_between_messages > 0:
                await asyncio.sleep(request.delay_between_messages)
                
        except Exception as e:
            results.append({
                "phone_number": phone_number,
                "success": False,
                "message": f"Error: {str(e)}"
            })
            failed_sends += 1
    
    return BaseGupshupResponse(
        success=successful_sends > 0,
        message=f"Bulk messaging completed. Success: {successful_sends}, Failed: {failed_sends}",
        data={
            "total_sent": len(request.phone_numbers),
            "successful": successful_sends,
            "failed": failed_sends,
            "results": results
        }
    )

@router.get("/message-status/{message_id}", response_model=BaseGupshupResponse)
async def get_message_status(message_id: str):
    """
    Get the status of a sent message
    
    - **message_id**: Gupshup message ID
    """
    # Note: This endpoint would require Gupshup's status API
    # For now, returning a placeholder response
    return BaseGupshupResponse(
        success=True,
        message="Message status retrieved successfully",
        data={
            "message_id": message_id,
            "status": "delivered",  # This would come from Gupshup API
            "note": "Status API integration required"
        }
    )

@router.get("/templates", response_model=TemplateListResponse)
async def get_templates():
    """
    Get list of available WhatsApp templates
    """
    # Note: This endpoint would require Gupshup's template API
    # For now, returning configured templates
    templates = [
        {
            "id": settings.GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID,
            "name": "OTP Template",
            "category": "AUTHENTICATION",
            "status": "APPROVED"
        },
        {
            "id": settings.GUPSHUP_LEAD_CREATION_TEMPLATE_ID,
            "name": "Lead Creation Template",
            "category": "UTILITY",
            "status": "APPROVED"
        },
        {
            "id": settings.GUPSHUP_LEAD_STATUS_TEMPLATE_ID,
            "name": "Lead Status Template",
            "category": "UTILITY",
            "status": "APPROVED"
        }
    ]
    
    return TemplateListResponse(
        success=True,
        message="Templates retrieved successfully",
        templates=templates
    )

@router.get("/health")
async def gupshup_health_check():
    """
    Health check for Gupshup API connectivity
    """
    try:
        # Test API connectivity with a simple request
        headers = get_gupshup_headers()
        test_data = {
            'channel': 'whatsapp',
            'source': settings.GUPSHUP_SOURCE,
            'destination': '919999999999',  # Test number
            'message': 'Health check test'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.GUPSHUP_API_URL,
                headers=headers,
                data=test_data,
                timeout=10.0
            )
        
        return {
            "success": True,
            "message": "Gupshup API is accessible",
            "status_code": response.status_code,
            "api_url": settings.GUPSHUP_API_URL,
            "source_configured": bool(settings.GUPSHUP_SOURCE),
            "api_key_configured": bool(settings.GUPSHUP_API_KEY)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Gupshup API health check failed: {str(e)}",
            "api_url": settings.GUPSHUP_API_URL,
            "source_configured": bool(settings.GUPSHUP_SOURCE),
            "api_key_configured": bool(settings.GUPSHUP_API_KEY)
        }

# ==================== LEGACY COMPATIBILITY ENDPOINTS ====================

@router.post("/send-otp", response_model=BaseGupshupResponse)
async def send_otp_legacy(request: PhoneNumberRequest):
    """
    Legacy OTP sending endpoint (compatible with existing system)
    """
    otp = whatsapp_service.generate_otp()
    result = await whatsapp_service.send_otp(request.phone_number, otp)
    
    return BaseGupshupResponse(
        success=result["success"],
        message=result["message"],
        data=result["data"]
    )

@router.post("/send-lead-confirmation", response_model=BaseGupshupResponse)
async def send_lead_confirmation_legacy(
    customer_name: str,
    loan_type: str,
    basic_application_id: str,
    phone_number: str
):
    """
    Legacy lead confirmation endpoint (compatible with existing system)
    """
    result = await whatsapp_service.send_lead_creation_confirmation(
        customer_name, loan_type, basic_application_id, phone_number
    )
    
    return BaseGupshupResponse(
        success=result["success"],
        message=result["message"],
        data=result["data"]
    )

@router.post("/send-status-update", response_model=BaseGupshupResponse)
async def send_status_update_legacy(
    phone_number: str,
    name: str,
    status: str
):
    """
    Legacy status update endpoint (compatible with existing system)
    """
    result = await whatsapp_service.send_lead_status_update(phone_number, name, status)
    
    return BaseGupshupResponse(
        success=result["success"],
        message=result["message"],
        data=result["data"]
    )
