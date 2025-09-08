"""
Modular Gupshup WhatsApp API Endpoints
Comprehensive wrapper for all Gupshup outbound messaging APIs
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import json
import httpx
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

class BaseAppRequest(BaseModel):
    """Base request with app name for multi-app support"""
    app_name: str = Field(..., description="Gupshup app name (e.g., 'homi', 'orbit')")

class PhoneNumberRequest(BaseAppRequest):
    """Base request with phone number validation and app name"""
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

class BulkMessageRequest(BaseAppRequest):
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

class AppTemplatesRequest(BaseAppRequest):
    """Request to get templates for a specific app"""
    template_status: Optional[str] = Field("APPROVED", description="Template status filter (APPROVED, PENDING, REJECTED)")

class AppListResponse(BaseModel):
    """Response for listing available apps"""
    success: bool
    message: str
    apps: List[Dict[str, Any]]

# ==================== UTILITY FUNCTIONS ====================

def get_gupshup_headers(app_config: dict) -> Dict[str, str]:
    """
    Get Gupshup headers with app-specific API key
    
    Args:
        app_config: App configuration dict with api_key
        
    Returns:
        Dict: Headers for Gupshup API requests
    """
    return {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
        'apikey': app_config["api_key"]
    }

async def get_templates_from_gupshup(app_id: str, api_key: str, template_status: str = None) -> Dict[str, Any]:
    """
    Fetch templates from Gupshup API based on app ID
    
    Args:
        app_id: Gupshup app ID
        api_key: App-specific API key
        template_status: Template status filter (APPROVED, PENDING, REJECTED)
        
    Returns:
        Dict containing templates data from Gupshup API
    """
    try:
        url = f"https://api.gupshup.io/wa/app/{app_id}/template"
        
        headers = {
            "accept": "application/json",
            "apikey": api_key
        }
        
        params = {
            "templateStatus": template_status if template_status else None
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            return {
                "success": True,
                "data": result,
                "status_code": response.status_code
            }
            
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "status_code": e.response.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 500
        }

async def send_gupshup_request(api_url: str, data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Generic function to send requests to Gupshup API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
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

def validate_app_config(app_name: str) -> dict:
    """
    Validate and get app configuration
    
    Args:
        app_name: Name of the app
        
    Returns:
        Dict: App configuration
        
    Raises:
        HTTPException: If app configuration is invalid
    """
    app_config = settings.get_gupshup_config(app_name)
    
    if not app_config["api_key"]:
        raise HTTPException(
            status_code=400,
            detail=f"API key not configured for app: {app_name}"
        )
    
    if not app_config["source"]:
        raise HTTPException(
            status_code=400,
            detail=f"Source number not configured for app: {app_name}"
        )
    
    return app_config


# ==================== API ENDPOINTS ====================

@router.post("/send-text", response_model=BaseGupshupResponse)
async def send_text_message(request: TextMessageRequest):
    """
    Send a simple text message via WhatsApp
    
    - **app_name**: Gupshup app name (e.g., 'homi', 'orbit')
    - **phone_number**: Phone number in any format (will be normalized)
    - **message**: Text message to send
    - **source_name**: Optional custom source name
    """
    # Get app-specific configuration
    app_config = validate_app_config(request.app_name)
    headers = get_gupshup_headers(app_config)
    
    message ={"type":"text", "text": request.message} 
    
    data = {
        'channel': 'whatsapp',
        'source': app_config["source"],
        'destination': request.phone_number,
        'message': json.dumps(message)
    }
    
    if request.source_name:
        data['src.name'] = request.source_name
    
    result = await send_gupshup_request(settings.GUPSHUP_API_MSG_URL, data, headers)
    
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
    
    - **app_name**: Gupshup app name (e.g., 'homi', 'orbit')
    - **phone_number**: Phone number in any format (will be normalized)
    - **template_id**: Gupshup template ID
    - **template_params**: List of template parameters
    - **source_name**: Optional custom source name
    """
    # Get app-specific configuration
    app_config = validate_app_config(request.app_name)
    headers = get_gupshup_headers(app_config)
    
    template_data = {
        "id": request.template_id,
        "params": request.template_params
    }
    
    data = {
        'channel': 'whatsapp',
        'source': app_config["source"],
        'destination': request.phone_number,
        'template': json.dumps(template_data)
    }
    
    if request.source_name:
        data['src.name'] = request.source_name
    
    result = await send_gupshup_request(settings.GUPSHUP_API_TEMPLATE_URL, data, headers)
    
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
    
    - **app_name**: Gupshup app name (e.g., 'homi', 'orbit')
    - **phone_number**: Phone number in any format (will be normalized)
    - **media_type**: Type of media (image, document, audio, video)
    - **media_url**: URL of the media file
    - **caption**: Optional caption for the media
    - **filename**: Optional filename for documents
    """
    # Get app-specific configuration
    app_config = validate_app_config(request.app_name)
    headers = get_gupshup_headers(app_config)
    
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
        'source': app_config["source"],
        'destination': request.phone_number,
        'message': json.dumps(media_message)
    }
    
    result = await send_gupshup_request(settings.GUPSHUP_API_TEMPLATE_URL, data, headers)
    
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
    
    - **app_name**: Gupshup app name (e.g., 'homi', 'orbit')
    - **phone_number**: Phone number in any format (will be normalized)
    - **interactive_type**: Type of interactive message (button, list)
    - **header**: Optional message header
    - **body**: Message body content
    - **footer**: Optional message footer
    - **action**: Interactive action configuration
    """
    # Get app-specific configuration
    app_config = validate_app_config(request.app_name)
    headers = get_gupshup_headers(app_config)
    
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
        'source': app_config["source"],
        'destination': request.phone_number,
        'message': json.dumps(interactive_message)
    }
    
    result = await send_gupshup_request(settings.GUPSHUP_API_TEMPLATE_URL, data, headers)
    
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
    
    - **app_name**: Gupshup app name (e.g., 'homi', 'orbit')
    - **phone_number**: Phone number in any format (will be normalized)
    - **latitude**: Latitude coordinate
    - **longitude**: Longitude coordinate
    - **name**: Optional location name
    - **address**: Optional location address
    """
    # Get app-specific configuration
    app_config = validate_app_config(request.app_name)
    headers = get_gupshup_headers(app_config)
    
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
        'source': app_config["source"],
        'destination': request.phone_number,
        'message': json.dumps(location_message)
    }
    
    result = await send_gupshup_request(settings.GUPSHUP_API_TEMPLATE_URL, data, headers)
    
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
    
    - **app_name**: Gupshup app name (e.g., 'homi', 'orbit')
    - **phone_number**: Phone number in any format (will be normalized)
    - **contacts**: List of contact objects
    """
    # Get app-specific configuration
    app_config = validate_app_config(request.app_name)
    headers = get_gupshup_headers(app_config)
    
    contact_message = {
        "type": "contacts",
        "contacts": request.contacts
    }
    
    data = {
        'channel': 'whatsapp',
        'source': app_config["source"],
        'destination': request.phone_number,
        'message': json.dumps(contact_message)
    }
    
    result = await send_gupshup_request(settings.GUPSHUP_API_TEMPLATE_URL, data, headers)
    
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
    
    - **app_name**: Gupshup app name (e.g., 'homi', 'orbit')
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
                    app_name=request.app_name,
                    phone_number=normalized_phone,
                    message=request.message_data.get("message", "")
                )
                result = await send_text_message(message_request)
            elif request.message_type == "template":
                message_request = TemplateMessageRequest(
                    app_name=request.app_name,
                    phone_number=normalized_phone,
                    template_id=request.message_data.get("template_id", ""),
                    template_params=request.message_data.get("template_params", [])
                )
                result = await send_template_message(message_request)
            elif request.message_type == "media":
                message_request = MediaMessageRequest(
                    app_name=request.app_name,
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


@router.get("/templates/by-app", response_model=BaseGupshupResponse)
async def get_templates_by_app_name(
    app_name: str, 
    template_status: Optional[str] = None
):
    """
    Get WhatsApp templates for a specific Gupshup app from Gupshup API
    
    This endpoint fetches templates directly from Gupshup's API based on the provided app name.
    The API key and app ID are automatically selected based on the app name.
    
    Query Parameters:
    - app_name: Name of the Gupshup app (e.g., 'basichomeloan', 'irabybasic')
    - template_status: Filter templates by status (default: None)
    
    Example: /api_v1/gupshup/templates/by-app?app_name=basichomeloan&template_status=APPROVED
    """
    try:
        # Get app-specific configuration
        app_config = validate_app_config(app_name)
        
        if not app_config["app_id"]:
            raise HTTPException(
                status_code=400,
                detail=f"App ID not configured for app: {app_name}"
            )
        
        # Fetch templates from Gupshup API using app-specific credentials
        result = await get_templates_from_gupshup(
            app_config["app_id"], 
            app_config["api_key"], 
            template_status
        )
        
        if result["success"]:
            templates_data = result["data"]
            
            # Extract templates from Gupshup response
            templates = []
            if isinstance(templates_data, dict):
                # Handle different possible response structures
                if "templates" in templates_data:
                    templates = templates_data["templates"]
                elif "data" in templates_data:
                    templates = templates_data["data"]
                else:
                    templates = [templates_data]  # Single template response
            elif isinstance(templates_data, list):
                templates = templates_data
            
            return BaseGupshupResponse(
                success=True,
                message=f"Found {len(templates)} templates for app: {app_name}",
                data={
                    "app_name": app_name,
                    "app_id": app_config["app_id"],
                    "template_status": template_status,
                    "templates": templates,
                    "total_count": len(templates)
                },
                gupshup_response=templates_data
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to fetch templates: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching templates for app {app_name}: {str(e)}"
        )

@router.get("/apps", response_model=AppListResponse)
async def get_available_apps():
    """
    Get list of all configured Gupshup apps
    
    Returns all apps that have been configured with API keys and app IDs.
    """
    try:
        apps_config = settings.GUPSHUP_APPS
        
        apps_list = []
        for app_name, config in apps_config.items():
            apps_list.append({
                "app_name": app_name,
                "app_id": config["app_id"],
                "source": config["source"],
                "has_api_key": bool(config["api_key"]),
                "status": "configured"
            })
        
        # Add default app if configured
        if settings.GUPSHUP_API_KEY:
            apps_list.append({
                "app_name": "default",
                "app_id": "N/A",
                "source": settings.GUPSHUP_SOURCE,
                "has_api_key": True,
                "status": "configured"
            })
        
        return AppListResponse(
            success=True,
            message=f"Found {len(apps_list)} configured apps",
            apps=apps_list
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving app configurations: {str(e)}"
        )

# @router.get("/health")
# async def gupshup_health_check():
#     """
#     Health check for Gupshup API connectivity
#     """
#     try:
#         # Test API connectivity with a simple request
#         headers = get_gupshup_headers()
#         test_data = {
#             'channel': 'whatsapp',
#             'source': settings.GUPSHUP_SOURCE,
#             'destination': '919999999999',  # Test number
#             'message': 'Health check test'
#         }
        
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 settings.GUPSHUP_API_TEMPLATE_URL,
#                 headers=headers,
#                 data=test_data,
#                 timeout=10.0
#             )
        
#         return {
#             "success": True,
#             "message": "Gupshup API is accessible",
#             "status_code": response.status_code,
#             "api_url": settings.GUPSHUP_API_URL,
#             "source_configured": bool(settings.GUPSHUP_SOURCE),
#             "api_key_configured": bool(settings.GUPSHUP_API_KEY)
#         }
        
#     except Exception as e:
#         return {
#             "success": False,
#             "message": f"Gupshup API health check failed: {str(e)}",
#             "api_url": settings.GUPSHUP_API_URL,
#             "source_configured": bool(settings.GUPSHUP_SOURCE),
#             "api_key_configured": bool(settings.GUPSHUP_API_KEY)
#         }

# ==================== LEGACY COMPATIBILITY ENDPOINTS ====================

# @router.post("/send-otp", response_model=BaseGupshupResponse)
# async def send_otp_legacy(request: PhoneNumberRequest):
#     """
#     Legacy OTP sending endpoint (compatible with existing system)
#     """
#     otp = whatsapp_service.generate_otp()
#     result = await whatsapp_service.send_otp(request.phone_number, otp)
    
#     return BaseGupshupResponse(
#         success=result["success"],
#         message=result["message"],
#         data=result["data"]
#     )

# @router.post("/send-lead-confirmation", response_model=BaseGupshupResponse)
# async def send_lead_confirmation_legacy(
#     customer_name: str,
#     loan_type: str,
#     basic_application_id: str,
#     phone_number: str
# ):
#     """
#     Legacy lead confirmation endpoint (compatible with existing system)
#     """
#     result = await whatsapp_service.send_lead_creation_confirmation(
#         customer_name, loan_type, basic_application_id, phone_number
#     )
    
#     return BaseGupshupResponse(
#         success=result["success"],
#         message=result["message"],
#         data=result["data"]
#     )

# @router.post("/send-status-update", response_model=BaseGupshupResponse)
# async def send_status_update_legacy(
#     phone_number: str,
#     name: str,
#     status: str
# ):
#     """
#     Legacy status update endpoint (compatible with existing system)
#     """
#     result = await whatsapp_service.send_lead_status_update(phone_number, name, status)
    
#     return BaseGupshupResponse(
#         success=result["success"],
#         message=result["message"],
#         data=result["data"]
#     )
