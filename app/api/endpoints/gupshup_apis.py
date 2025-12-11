"""
Modular Gupshup WhatsApp API Endpoints
Comprehensive wrapper for all Gupshup outbound messaging APIs
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import json
import httpx
from pydantic_core.core_schema import dataclass_args_schema
from storage3.types import dataclass
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
    app_name: str = Field(..., description="Gupshup app name (e.g., 'homi', 'orbit')")
    phone_number: str = Field(..., description="Phone number (supports multiple formats)")
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

# ==================== SESSION MESSAGE SCHEMAS ====================

class SessionTextMessageRequest(PhoneNumberRequest):
    """Request for session-bound text messages"""
    message: str = Field(..., description="Text message content")

class SessionImageMessageRequest(PhoneNumberRequest):
    """Request for session-bound image messages"""
    image_url: str = Field(..., description="URL of the image file")
    caption: Optional[str] = Field(None, description="Image caption")

class SessionDocumentMessageRequest(PhoneNumberRequest):
    """Request for session-bound document messages"""
    document_url: str = Field(..., description="URL of the document file")
    filename: str = Field(..., description="Document filename")
    caption: Optional[str] = Field(None, description="Document caption")

class SessionAudioMessageRequest(PhoneNumberRequest):
    """Request for session-bound audio messages"""
    audio_url: str = Field(..., description="URL of the audio file")

class SessionVideoMessageRequest(PhoneNumberRequest):
    """Request for session-bound video messages"""
    video_url: str = Field(..., description="URL of the video file")
    caption: Optional[str] = Field(None, description="Video caption")

class SessionStickerMessageRequest(PhoneNumberRequest):
    """Request for session-bound sticker messages"""
    sticker_url: str = Field(..., description="URL of the sticker file")

class SessionReactionMessageRequest(PhoneNumberRequest):
    """Request for session-bound reaction messages"""
    message_id: str = Field(..., description="Message ID to react to")
    emoji: str = Field(..., description="Emoji for reaction")

class SessionLocationMessageRequest(PhoneNumberRequest):
    """Request for session-bound location messages"""
    latitude: float = Field(..., description="Location latitude")
    longitude: float = Field(..., description="Location longitude")
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")

class ListSection(BaseModel):
    """List section model"""
    title: str = Field(..., description="Section title")
    rows: List[Dict[str, Any]] = Field(..., description="List of rows in section")

class SessionListMessageRequest(PhoneNumberRequest):
    """Request for session-bound list messages"""
    header: Optional[str] = Field(None, description="List header text")
    body: str = Field(..., description="List body text")
    footer: Optional[str] = Field(None, description="List footer text")
    button_text: str = Field(..., description="List button text")
    sections: List[ListSection] = Field(..., description="List sections")

class QuickReplyButton(BaseModel):
    """Quick reply button model"""
    type: str = Field(default="reply", description="Button type")
    reply: Dict[str, str] = Field(..., description="Reply data with id and title")

class SessionQuickRepliesRequest(PhoneNumberRequest):
    """Request for session-bound quick reply messages"""
    header: Optional[str] = Field(None, description="Message header")
    body: str = Field(..., description="Message body")
    footer: Optional[str] = Field(None, description="Message footer")
    buttons: List[QuickReplyButton] = Field(..., description="Quick reply buttons (max 3)")

class SessionCatalogMessageRequest(PhoneNumberRequest):
    """Request for session-bound catalog messages"""
    header: Optional[str] = Field(None, description="Catalog header")
    body: str = Field(..., description="Catalog body text")
    footer: Optional[str] = Field(None, description="Catalog footer")
    action: Dict[str, Any] = Field(..., description="Catalog action parameters")

class SessionSingleProductRequest(PhoneNumberRequest):
    """Request for session-bound single product messages"""
    header: Optional[str] = Field(None, description="Product header")
    body: str = Field(..., description="Product body text")
    footer: Optional[str] = Field(None, description="Product footer")
    product_retailer_id: str = Field(..., description="Product retailer ID")

class SessionMultiProductRequest(PhoneNumberRequest):
    """Request for session-bound multi product messages"""
    header: Optional[str] = Field(None, description="Products header")
    body: str = Field(..., description="Products body text")
    footer: Optional[str] = Field(None, description="Products footer")
    catalog_id: str = Field(..., description="Catalog ID")
    product_sections: List[Dict[str, Any]] = Field(..., description="Product sections")

class CTAButton(BaseModel):
    """CTA Button model"""
    type: str = Field(..., description="Button type: url or phone_number")
    title: str = Field(..., description="Button title")
    url: Optional[str] = Field(None, description="URL for url type buttons")
    phone_number: Optional[str] = Field(None, description="Phone number for phone_number type buttons")

class SessionCTAMessageRequest(PhoneNumberRequest):
    """Request for session-bound CTA URL messages"""
    header: Optional[str] = Field(None, description="Message header")
    body: str = Field(..., description="Message body")
    footer: Optional[str] = Field(None, description="Message footer")
    buttons: List[CTAButton] = Field(..., description="CTA buttons (max 2)")

class SessionMessageResponse(BaseModel):
    """Response for session message operations"""
    success: bool
    message: str
    message_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    gupshup_response: Optional[Dict[str, Any]] = None

# ==================== TEMPLATE MESSAGE SCHEMAS ====================

class TemplateTextMessageRequest(PhoneNumberRequest):
    """Request for template-based text messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateImageMessageRequest(PhoneNumberRequest):
    """Request for template-based image messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    image_url: Optional[str] = Field(None, description="Header image URL (if template supports)")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateVideoMessageRequest(PhoneNumberRequest):
    """Request for template-based video messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    video_url: Optional[str] = Field(None, description="Header video URL (if template supports)")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateDocumentMessageRequest(PhoneNumberRequest):
    """Request for template-based document messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    document_url: Optional[str] = Field(None, description="Header document URL (if template supports)")
    filename: Optional[str] = Field(None, description="Document filename")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateLocationMessageRequest(PhoneNumberRequest):
    """Request for template-based location messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    latitude: Optional[float] = Field(None, description="Location latitude")
    longitude: Optional[float] = Field(None, description="Location longitude")
    name: Optional[str] = Field(None, description="Location name")
    address: Optional[str] = Field(None, description="Location address")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateCouponMessageRequest(PhoneNumberRequest):
    """Request for template-based coupon messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    coupon_code: str = Field(..., description="Coupon code")
    source_name: Optional[str] = Field(None, description="Custom source name")

class CarouselCard(BaseModel):
    """Carousel card model for template messages"""
    card_index: int = Field(..., description="Card index (0-based)")
    components: List[Dict[str, Any]] = Field(..., description="Card components (header, body, buttons)")

class TemplateCarouselMessageRequest(PhoneNumberRequest):
    """Request for template-based carousel messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Global template parameters")
    cards: List[CarouselCard] = Field(..., description="Carousel cards (max 10)")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateLTOMessageRequest(PhoneNumberRequest):
    """Request for template-based Limited Time Offer messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    offer_expiry: Optional[str] = Field(None, description="Offer expiry date/time")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateMPMMessageRequest(PhoneNumberRequest):
    """Request for template-based Multi Product Message"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    catalog_id: str = Field(..., description="Product catalog ID")
    product_sections: List[Dict[str, Any]] = Field(..., description="Product sections")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateCatalogMessageRequest(PhoneNumberRequest):
    """Request for template-based catalog messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    catalog_id: str = Field(..., description="Catalog ID")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateAuthenticationRequest(PhoneNumberRequest):
    """Request for template-based authentication messages (OTP, etc.)"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(..., description="Template parameters (usually includes OTP)")
    auth_type: str = Field(default="OTP", description="Authentication type")
    source_name: Optional[str] = Field(None, description="Custom source name")

class PostbackTextRequest(PhoneNumberRequest):
    """Request for postback text support messages"""
    template_id: str = Field(..., description="Gupshup template ID")
    template_params: List[str] = Field(default=[], description="Template parameters in order")
    postback_text: str = Field(..., description="Postback text for user interaction")
    source_name: Optional[str] = Field(None, description="Custom source name")

class TemplateMessageResponse(BaseModel):
    """Response for template message operations"""
    success: bool
    message: str
    message_id: Optional[str] = None
    template_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    gupshup_response: Optional[Dict[str, Any]] = None

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
        'cache-control': 'no-cache',
        "accept": "application/json",
        'content-type': 'application/x-www-form-urlencoded',
        'apikey': app_config["api_key"]
    }

async def send_template_message(app_config: dict, destination: str, template_id: str, template_params: List[str] = None, source_name: str = None) -> Dict[str, Any]:
    """
    Send a template message using Gupshup API
    
    Args:
        app_config: App configuration with API key and source
        destination: Destination phone number
        template_id: Gupshup template ID
        template_params: Template parameters list
        source_name: Optional custom source name
        
    Returns:
        Dict containing success status and response data
    """
    try:
        headers = get_gupshup_headers(app_config)
        
        data = {
            'channel': 'whatsapp',
            'source': app_config["source"],
            'destination': destination,
            'template': json.dumps({
                "id": template_id,
                "params": template_params or []
            })
        }
        
        if source_name:
            data['src.name'] = source_name
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.GUPSHUP_API_TEMPLATE_URL,
                headers=headers,
                data=data,
                timeout=30.0
            )
            
            if response.status_code in [200, 202]:
                try:
                    response_data = response.json()
                    return {
                        "success": True,
                        "data": response_data,
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
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 500
        }

async def send_session_message(app_config: dict, destination: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a session message using Gupshup API
    
    Args:
        app_config: App configuration with API key and source
        destination: Destination phone number
        message_data: Message data in Gupshup format
        
    Returns:
        Dict containing success status and response data
    """
    try:
        headers = get_gupshup_headers(app_config)
        
        data = {
            'channel': 'whatsapp',
            'source': app_config["source"],
            'destination': destination,
            'message': json.dumps(message_data)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.GUPSHUP_API_MSG_URL,
                headers=headers,
                data=data,
                timeout=30.0
            )
            
            if response.status_code in [200, 202]:
                try:
                    response_data = response.json()
                    return {
                        "success": True,
                        "data": response_data,
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
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 500
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

class MarketingMessageRequest(BaseModel):
    api_url: str
    appId: str
    data: Dict[str, Any]

@router.post("/send-marketing-message")
async def send_gupshup_marketing_request(request: MarketingMessageRequest):
    """Generic function to send requests to Gupshup API"""

    headers = {
        'cache-control': 'no-cache',
        "accept": "application/json",
        'content-type': 'application/json',
        'apikey': "rh3qjmdnats7ctrxqvjitudlo7f73xmm"
    }
    api_url = request.api_url+f"/wa/app/{request.appId}/v3/marketing/msg"
    print("API URL:----",api_url)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                headers=headers,
                data=json.dumps(request.data),
                timeout=30.0
            )
            print("RESPONSE:----",response.text ,"-------------------")
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
class SetStatusReadRequest(BaseModel):
    message_id: str = Field(..., description="Gupshup message ID")
    app_name: str = Field(..., description="Gupshup app name (e.g., 'homi', 'orbit')")

@router.post("/set-status-read", response_model=BaseGupshupResponse)
async def set_status_read(request: SetStatusReadRequest):

    # Get app-specific configuration
    app_config = validate_app_config(request.app_name)
    headers = get_gupshup_headers(app_config)
    headers = {"Authorization": headers["apikey"]}

    url = f"https://api.gupshup.io/wa/app/{app_config['app_id']}/msg/{request.message_id}/read"
    
    try:
        import requests
        response = requests.put(url, headers=headers)
        print("Mark Read Response:----",response.text ,"-------------------", response.status_code)
        if response.status_code in [200, 202]:
            success = True
            message = "Message read request submitted"
            data = response.text
        else:
            success = False
            message = f"Failed to submit read request: {response.text}"
            data = response.text
    except Exception as e:
        success = False
        message = f"Failed to submit read request: {str(e)}"
        data = {"error": str(e)}

    return BaseGupshupResponse(
        success=success,
        message=message,
        data=None,
        gupshup_response=None
    )
    
class MessageRequest(BaseModel):
    app_name: str = Field(..., description="Gupshup app name (e.g., 'homi', 'orbit')")
    phone_number: str = Field(..., description="Phone number in any format (will be normalized)")
    message: dict = Field(..., description="Message data in Gupshup format")
    source_name: Optional[str] = Field(None, description="Custom source name")

@router.post("/send-message", response_model=BaseGupshupResponse)
async def send_message(request: MessageRequest):
    """
    Send a message of any type via WhatsApp
    
    - **app_name**: Gupshup app name (e.g., 'homi', 'orbit')
    - **phone_number**: Phone number in any format (will be normalized)
    - **message**: Message data in Gupshup format
    - **source_name**: Optional custom source name
    """
    # Get app-specific configuration
    app_config = validate_app_config(request.app_name)
    headers = get_gupshup_headers(app_config)
    
    # message ={"type":"text", "text": request["message"]} 
    
    data = {
        'channel': 'whatsapp',
        'source': app_config["source"],
        'destination': request.phone_number,
        'message': json.dumps(request.message)
    }
    
    if request.source_name:
        data['src.name'] = request.source_name

    result = await send_gupshup_request(settings.GUPSHUP_API_MSG_URL, data, headers)
    
    return BaseGupshupResponse(
        success=result["success"],
        message="Message sent successfully" if result["success"] else "Failed to send message",
    )


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


class DemoTemplateMessageRequest(BaseModel):
    app_name: str
    phone_number: str
    template_id: str
    template_params: List[str]
    source_name: Optional[str] = None

@router.post("/send-template", response_model=BaseGupshupResponse)
async def send_template_message(request: DemoTemplateMessageRequest):
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

@router.get("/templates/by-app", response_model=BaseGupshupResponse)
async def get_template_by_template_id(
    app_name: str, 
    template_status: Optional[str] = None
):
    """
    Get WhatsApp template for a specific Gupshup app from Gupshup API
    
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

# ==================== SESSION MESSAGE ENDPOINTS ====================

@router.post("/session/text", response_model=SessionMessageResponse)
async def send_session_text_message(request: SessionTextMessageRequest):
    """
    Send a session-bound text message via WhatsApp
    
    Session messages are sent during an active conversation window (24 hours after user interaction).
    No template required for session messages.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        message_data = {
            "type": "text",
            "text": request.message
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            # Extract message ID from Gupshup response if available
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Text message sent successfully",
                message_id=message_id,
                data={"text": request.message, "app_name": request.app_name},
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send text message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending text message: {str(e)}"
        )

@router.post("/session/image", response_model=SessionMessageResponse)
async def send_session_image_message(request: SessionImageMessageRequest):
    """
    Send a session-bound image message via WhatsApp
    
    Supports image files with optional caption.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        message_data = {
            "type": "image",
            "image": {
                "link": request.image_url
            }
        }
        
        if request.caption:
            message_data["image"]["caption"] = request.caption
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Image message sent successfully",
                message_id=message_id,
                data={
                    "image_url": request.image_url,
                    "caption": request.caption,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send image message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending image message: {str(e)}"
        )

@router.post("/session/document", response_model=SessionMessageResponse)
async def send_session_document_message(request: SessionDocumentMessageRequest):
    """
    Send a session-bound document message via WhatsApp
    
    Supports various document formats (PDF, DOC, etc.) with filename and optional caption.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        message_data = {
            "type": "document",
            "document": {
                "link": request.document_url,
                "filename": request.filename
            }
        }
        
        if request.caption:
            message_data["document"]["caption"] = request.caption
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Document message sent successfully",
                message_id=message_id,
                data={
                    "document_url": request.document_url,
                    "filename": request.filename,
                    "caption": request.caption,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send document message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending document message: {str(e)}"
        )

@router.post("/session/audio", response_model=SessionMessageResponse)
async def send_session_audio_message(request: SessionAudioMessageRequest):
    """
    Send a session-bound audio message via WhatsApp
    
    Supports audio files in various formats.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        message_data = {
            "type": "audio",
            "audio": {
                "link": request.audio_url
            }
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Audio message sent successfully",
                message_id=message_id,
                data={
                    "audio_url": request.audio_url,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send audio message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending audio message: {str(e)}"
        )

@router.post("/session/video", response_model=SessionMessageResponse)
async def send_session_video_message(request: SessionVideoMessageRequest):
    """
    Send a session-bound video message via WhatsApp
    
    Supports video files with optional caption.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        message_data = {
            "type": "video",
            "video": {
                "link": request.video_url
            }
        }
        
        if request.caption:
            message_data["video"]["caption"] = request.caption
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Video message sent successfully",
                message_id=message_id,
                data={
                    "video_url": request.video_url,
                    "caption": request.caption,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send video message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending video message: {str(e)}"
        )

@router.post("/session/sticker", response_model=SessionMessageResponse)
async def send_session_sticker_message(request: SessionStickerMessageRequest):
    """
    Send a session-bound sticker message via WhatsApp
    
    Supports sticker files (WebP format recommended).
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        message_data = {
            "type": "sticker",
            "sticker": {
                "link": request.sticker_url
            }
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Sticker message sent successfully",
                message_id=message_id,
                data={
                    "sticker_url": request.sticker_url,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send sticker message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending sticker message: {str(e)}"
        )

@router.post("/session/reaction", response_model=SessionMessageResponse)
async def send_session_reaction_message(request: SessionReactionMessageRequest):
    """
    Send a session-bound reaction message via WhatsApp
    
    React to a specific message with an emoji.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        message_data = {
            "type": "reaction",
            "reaction": {
                "message_id": request.message_id,
                "emoji": request.emoji
            }
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Reaction sent successfully",
                message_id=message_id,
                data={
                    "reacted_to_message_id": request.message_id,
                    "emoji": request.emoji,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send reaction: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending reaction: {str(e)}"
        )

@router.post("/session/location", response_model=SessionMessageResponse)
async def send_session_location_message(request: SessionLocationMessageRequest):
    """
    Send a session-bound location message via WhatsApp
    
    Share a location with coordinates and optional name/address.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        message_data = {
            "type": "location",
            "location": {
                "latitude": request.latitude,
                "longitude": request.longitude
            }
        }
        
        if request.name:
            message_data["location"]["name"] = request.name
        
        if request.address:
            message_data["location"]["address"] = request.address
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Location message sent successfully",
                message_id=message_id,
                data={
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "name": request.name,
                    "address": request.address,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send location message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending location message: {str(e)}"
        )

@router.post("/session/list", response_model=SessionMessageResponse)
async def send_session_list_message(request: SessionListMessageRequest):
    """
    Send a session-bound list message via WhatsApp
    
    Interactive list message with multiple sections and rows.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        # Build interactive list message
        interactive_data = {
            "type": "list",
            "body": {"text": request.body}
        }
        
        if request.header:
            interactive_data["header"] = {"type": "text", "text": request.header}
        
        if request.footer:
            interactive_data["footer"] = {"text": request.footer}
        
        interactive_data["action"] = {
            "button": request.button_text,
            "sections": [
                {
                    "title": section.title,
                    "rows": section.rows
                }
                for section in request.sections
            ]
        }
        
        message_data = {
            "type": "interactive",
            "interactive": interactive_data
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="List message sent successfully",
                message_id=message_id,
                data={
                    "header": request.header,
                    "body": request.body,
                    "footer": request.footer,
                    "button_text": request.button_text,
                    "sections_count": len(request.sections),
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send list message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending list message: {str(e)}"
        )

@router.post("/session/quick-replies", response_model=SessionMessageResponse)
async def send_session_quick_replies_message(request: SessionQuickRepliesRequest):
    """
    Send a session-bound quick replies message via WhatsApp
    
    Interactive message with quick reply buttons (max 3).
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        if len(request.buttons) > 3:
            raise HTTPException(
                status_code=400,
                detail="Maximum 3 quick reply buttons allowed"
            )
        
        # Build interactive quick replies message
        interactive_data = {
            "type": "button",
            "body": {"text": request.body}
        }
        
        if request.header:
            interactive_data["header"] = {"type": "text", "text": request.header}
        
        if request.footer:
            interactive_data["footer"] = {"text": request.footer}
        
        interactive_data["action"] = {
            "buttons": [
                {
                    "type": button.type,
                    "reply": button.reply
                }
                for button in request.buttons
            ]
        }
        
        message_data = {
            "type": "interactive",
            "interactive": interactive_data
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Quick replies message sent successfully",
                message_id=message_id,
                data={
                    "header": request.header,
                    "body": request.body,
                    "footer": request.footer,
                    "buttons_count": len(request.buttons),
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send quick replies message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending quick replies message: {str(e)}"
        )

@router.post("/session/catalog", response_model=SessionMessageResponse)
async def send_session_catalog_message(request: SessionCatalogMessageRequest):
    """
    Send a session-bound catalog message via WhatsApp
    
    Display product catalog for browsing.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        # Build interactive catalog message
        interactive_data = {
            "type": "catalog_message",
            "body": {"text": request.body}
        }
        
        if request.header:
            interactive_data["header"] = {"type": "text", "text": request.header}
        
        if request.footer:
            interactive_data["footer"] = {"text": request.footer}
        
        interactive_data["action"] = request.action
        
        message_data = {
            "type": "interactive",
            "interactive": interactive_data
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Catalog message sent successfully",
                message_id=message_id,
                data={
                    "header": request.header,
                    "body": request.body,
                    "footer": request.footer,
                    "action": request.action,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send catalog message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending catalog message: {str(e)}"
        )

@router.post("/session/single-product", response_model=SessionMessageResponse)
async def send_session_single_product_message(request: SessionSingleProductRequest):
    """
    Send a session-bound single product message via WhatsApp
    
    Display a single product from catalog.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        # Build interactive single product message
        interactive_data = {
            "type": "product",
            "body": {"text": request.body}
        }
        
        if request.header:
            interactive_data["header"] = {"type": "text", "text": request.header}
        
        if request.footer:
            interactive_data["footer"] = {"text": request.footer}
        
        interactive_data["action"] = {
            "catalog_id": request.product_retailer_id,
            "product_retailer_id": request.product_retailer_id
        }
        
        message_data = {
            "type": "interactive",
            "interactive": interactive_data
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Single product message sent successfully",
                message_id=message_id,
                data={
                    "header": request.header,
                    "body": request.body,
                    "footer": request.footer,
                    "product_retailer_id": request.product_retailer_id,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send single product message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending single product message: {str(e)}"
        )

@router.post("/session/multi-product", response_model=SessionMessageResponse)
async def send_session_multi_product_message(request: SessionMultiProductRequest):
    """
    Send a session-bound multi product message via WhatsApp
    
    Display multiple products from catalog.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        # Build interactive multi product message
        interactive_data = {
            "type": "product_list",
            "body": {"text": request.body}
        }
        
        if request.header:
            interactive_data["header"] = {"type": "text", "text": request.header}
        
        if request.footer:
            interactive_data["footer"] = {"text": request.footer}
        
        interactive_data["action"] = {
            "catalog_id": request.catalog_id,
            "sections": request.product_sections
        }
        
        message_data = {
            "type": "interactive",
            "interactive": interactive_data
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="Multi product message sent successfully",
                message_id=message_id,
                data={
                    "header": request.header,
                    "body": request.body,
                    "footer": request.footer,
                    "catalog_id": request.catalog_id,
                    "sections_count": len(request.product_sections),
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send multi product message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending multi product message: {str(e)}"
        )

@router.post("/session/cta", response_model=SessionMessageResponse)
async def send_session_cta_message(request: SessionCTAMessageRequest):
    """
    Send a session-bound CTA (Call-to-Action) message via WhatsApp
    
    Interactive message with CTA buttons (URL or phone number).
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        if len(request.buttons) > 2:
            raise HTTPException(
                status_code=400,
                detail="Maximum 2 CTA buttons allowed"
            )
        
        # Build interactive CTA message
        interactive_data = {
            "type": "cta_url",
            "body": {"text": request.body}
        }
        
        if request.header:
            interactive_data["header"] = {"type": "text", "text": request.header}
        
        if request.footer:
            interactive_data["footer"] = {"text": request.footer}
        
        # Build buttons based on type
        buttons = []
        for button in request.buttons:
            if button.type == "url":
                buttons.append({
                    "type": "url",
                    "url": button.url,
                    "text": button.title
                })
            elif button.type == "phone_number":
                buttons.append({
                    "type": "phone_number",
                    "phone_number": button.phone_number,
                    "text": button.title
                })
        
        interactive_data["action"] = {"buttons": buttons}
        
        message_data = {
            "type": "interactive",
            "interactive": interactive_data
        }
        
        result = await send_session_message(app_config, request.phone_number, message_data)
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return SessionMessageResponse(
                success=True,
                message="CTA message sent successfully",
                message_id=message_id,
                data={
                    "header": request.header,
                    "body": request.body,
                    "footer": request.footer,
                    "buttons_count": len(request.buttons),
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send CTA message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending CTA message: {str(e)}"
        )

# ==================== TEMPLATE MESSAGE ENDPOINTS ====================

@router.post("/template/text", response_model=TemplateMessageResponse)
async def send_template_text_message(request: TemplateTextMessageRequest):
    """
    Send a template-based text message via WhatsApp
    
    Template messages are used for business-initiated conversations and require pre-approved templates.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            request.template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template text message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": request.template_params,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template text message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template text message: {str(e)}"
        )

@router.post("/template/image", response_model=TemplateMessageResponse)
async def send_template_image_message(request: TemplateImageMessageRequest):
    """
    Send a template-based image message via WhatsApp
    
    Template must be pre-approved and may include header image support.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        # For image templates, we might need to handle header parameters differently
        template_params = request.template_params.copy()
        
        # If image_url is provided, it might be used as a header parameter
        if request.image_url and request.image_url not in template_params:
            # Add image URL as first parameter if not already included
            template_params.insert(0, request.image_url)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template image message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "image_url": request.image_url,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template image message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template image message: {str(e)}"
        )

@router.post("/template/video", response_model=TemplateMessageResponse)
async def send_template_video_message(request: TemplateVideoMessageRequest):
    """
    Send a template-based video message via WhatsApp
    
    Template must be pre-approved and may include header video support.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        template_params = request.template_params.copy()
        
        # If video_url is provided, it might be used as a header parameter
        if request.video_url and request.video_url not in template_params:
            template_params.insert(0, request.video_url)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template video message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "video_url": request.video_url,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template video message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template video message: {str(e)}"
        )

@router.post("/template/document", response_model=TemplateMessageResponse)
async def send_template_document_message(request: TemplateDocumentMessageRequest):
    """
    Send a template-based document message via WhatsApp
    
    Template must be pre-approved and may include header document support.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        template_params = request.template_params.copy()
        
        # If document_url is provided, it might be used as a header parameter
        if request.document_url and request.document_url not in template_params:
            template_params.insert(0, request.document_url)
        
        # Add filename if provided and not in params
        if request.filename and request.filename not in template_params:
            template_params.append(request.filename)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template document message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "document_url": request.document_url,
                    "filename": request.filename,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template document message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template document message: {str(e)}"
        )

@router.post("/template/location", response_model=TemplateMessageResponse)
async def send_template_location_message(request: TemplateLocationMessageRequest):
    """
    Send a template-based location message via WhatsApp
    
    Template must be pre-approved and may include location parameters.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        template_params = request.template_params.copy()
        
        # Add location parameters if provided
        if request.latitude is not None and str(request.latitude) not in template_params:
            template_params.append(str(request.latitude))
        
        if request.longitude is not None and str(request.longitude) not in template_params:
            template_params.append(str(request.longitude))
        
        if request.name and request.name not in template_params:
            template_params.append(request.name)
        
        if request.address and request.address not in template_params:
            template_params.append(request.address)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template location message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "name": request.name,
                    "address": request.address,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template location message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template location message: {str(e)}"
        )

@router.post("/template/coupon", response_model=TemplateMessageResponse)
async def send_template_coupon_message(request: TemplateCouponMessageRequest):
    """
    Send a template-based coupon message via WhatsApp
    
    Template must be pre-approved for coupon/promotional content.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        template_params = request.template_params.copy()
        
        # Add coupon code if not already in parameters
        if request.coupon_code not in template_params:
            template_params.append(request.coupon_code)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template coupon message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "coupon_code": request.coupon_code,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template coupon message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template coupon message: {str(e)}"
        )

@router.post("/template/carousel", response_model=TemplateMessageResponse)
async def send_template_carousel_message(request: TemplateCarouselMessageRequest):
    """
    Send a template-based carousel message via WhatsApp
    
    Template must be pre-approved for carousel format with multiple cards.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        if len(request.cards) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 carousel cards allowed"
            )
        
        # For carousel templates, we need to structure the parameters differently
        # This may require a more complex template structure
        template_params = request.template_params.copy()
        
        # Add card-specific parameters
        for card in request.cards:
            template_params.extend([str(param) for component in card.components for param in component.values() if isinstance(param, (str, int, float))])
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template carousel message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "cards_count": len(request.cards),
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template carousel message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template carousel message: {str(e)}"
        )

@router.post("/template/lto", response_model=TemplateMessageResponse)
async def send_template_lto_message(request: TemplateLTOMessageRequest):
    """
    Send a template-based Limited Time Offer (LTO) message via WhatsApp
    
    Template must be pre-approved for promotional/offer content with time constraints.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        template_params = request.template_params.copy()
        
        # Add offer expiry if provided
        if request.offer_expiry and request.offer_expiry not in template_params:
            template_params.append(request.offer_expiry)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template LTO message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "offer_expiry": request.offer_expiry,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template LTO message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template LTO message: {str(e)}"
        )

@router.post("/template/mpm", response_model=TemplateMessageResponse)
async def send_template_mpm_message(request: TemplateMPMMessageRequest):
    """
    Send a template-based Multi Product Message (MPM) via WhatsApp
    
    Template must be pre-approved for product catalog display.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        template_params = request.template_params.copy()
        
        # Add catalog ID if not in parameters
        if request.catalog_id not in template_params:
            template_params.append(request.catalog_id)
        
        # Add product section information
        for section in request.product_sections:
            if isinstance(section, dict):
                for key, value in section.items():
                    if isinstance(value, str) and value not in template_params:
                        template_params.append(value)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template MPM message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "catalog_id": request.catalog_id,
                    "sections_count": len(request.product_sections),
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template MPM message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template MPM message: {str(e)}"
        )

@router.post("/template/catalog", response_model=TemplateMessageResponse)
async def send_template_catalog_message(request: TemplateCatalogMessageRequest):
    """
    Send a template-based catalog message via WhatsApp
    
    Template must be pre-approved for catalog display.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        template_params = request.template_params.copy()
        
        # Add catalog ID if not in parameters
        if request.catalog_id not in template_params:
            template_params.append(request.catalog_id)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template catalog message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "catalog_id": request.catalog_id,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template catalog message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template catalog message: {str(e)}"
        )

@router.post("/template/authentication", response_model=TemplateMessageResponse)
async def send_template_authentication_message(request: TemplateAuthenticationRequest):
    """
    Send a template-based authentication message via WhatsApp (OTP, verification codes, etc.)
    
    Template must be pre-approved for authentication/verification purposes.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            request.template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template authentication message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "auth_type": request.auth_type,
                    "params_count": len(request.template_params),
                    "app_name": request.app_name
                    # Note: We don't include actual template_params in response for security
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template authentication message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template authentication message: {str(e)}"
        )

@router.post("/template/postback", response_model=TemplateMessageResponse)
async def send_template_postback_message(request: PostbackTextRequest):
    """
    Send a template message with postback text support via WhatsApp
    
    Template must be pre-approved and support postback functionality for user interactions.
    """
    try:
        app_config = validate_app_config(request.app_name)
        
        template_params = request.template_params.copy()
        
        # Add postback text if not in parameters
        if request.postback_text not in template_params:
            template_params.append(request.postback_text)
        
        result = await send_template_message(
            app_config, 
            request.phone_number, 
            request.template_id, 
            template_params,
            request.source_name
        )
        
        if result["success"]:
            message_id = None
            if isinstance(result["data"], dict):
                message_id = result["data"].get("messageId") or result["data"].get("id")
            
            return TemplateMessageResponse(
                success=True,
                message="Template postback message sent successfully",
                message_id=message_id,
                template_id=request.template_id,
                data={
                    "template_id": request.template_id,
                    "template_params": template_params,
                    "postback_text": request.postback_text,
                    "app_name": request.app_name
                },
                gupshup_response=result["data"]
            )
        else:
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=f"Failed to send template postback message: {result['error']}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error sending template postback message: {str(e)}"
        )
