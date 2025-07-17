from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.database_service import database_service

router = APIRouter(prefix="/api_v1", tags=["whatsapp-messages"])

@router.get("/whatsapp/messages")
async def get_whatsapp_messages(
    mobile_number: Optional[str] = Query(None, description="Filter by mobile number"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    direction: Optional[str] = Query(None, description="Filter by direction (inbound/outbound)")
):
    """
    Get WhatsApp messages from database
    
    Args:
        mobile_number: Filter by mobile number
        limit: Number of messages to return (1-100)
        direction: Filter by message direction
        
    Returns:
        List of WhatsApp messages
    """
    try:
        if mobile_number:
            # Get messages for specific mobile number
            messages = database_service.get_whatsapp_messages_by_mobile(mobile_number, limit)
        else:
            # Get all messages (you might want to add pagination here)
            messages = database_service.get_whatsapp_messages_by_mobile("", limit)
        
        # Filter by direction if specified
        if direction and direction.lower() in ['inbound', 'outbound']:
            messages = [msg for msg in messages if msg.get('direction') == direction.lower()]
        
        return {
            "success": True,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving WhatsApp messages: {str(e)}"
        )

@router.get("/whatsapp/messages/stats")
async def get_whatsapp_message_stats():
    """
    Get WhatsApp message statistics
    
    Returns:
        Message statistics
    """
    try:
        stats = database_service.get_whatsapp_message_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving message statistics: {str(e)}"
        )

@router.get("/whatsapp/messages/{mobile_number}")
async def get_messages_by_mobile(mobile_number: str, limit: int = Query(50, ge=1, le=100)):
    """
    Get WhatsApp messages for a specific mobile number
    
    Args:
        mobile_number: Mobile number to search for
        limit: Number of messages to return
        
    Returns:
        List of messages for the mobile number
    """
    try:
        messages = database_service.get_whatsapp_messages_by_mobile(mobile_number, limit)
        
        return {
            "success": True,
            "mobile_number": mobile_number,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving messages for {mobile_number}: {str(e)}"
        ) 