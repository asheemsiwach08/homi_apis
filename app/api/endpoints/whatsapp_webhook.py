import re
import json
import logging
from typing import Optional, Dict, Any, Tuple, List
from fastapi import APIRouter, HTTPException, Request, Form
from app.models.schemas import WhatsAppStatusResponse
from app.services.basic_application_service import BasicApplicationService
from app.services.whatsapp_service import whatsapp_service
from app.services.database_service import database_service
from app.config.settings import settings
from app.services.campaign_services import generate_user_response
from app.services.campaign_services import to_utc_dt


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["whatsapp-webhook"])

# Initialize services
basic_app_service = BasicApplicationService()

############################################################################################
                                # WhatsApp Webhook Validation
############################################################################################

def is_status_check_request(message: str) -> bool:
    """Check if the message is requesting application status"""
    status_keywords = [
        'check my application status',
        'application status',
        'loan status',
        'status check',
        'track application',
        'application tracking',
        'loan application status',
        'check status',
        'my application',
        'loan details',
        'loan application'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in status_keywords)

############################################################################################
                                # WhatsApp Webhook API
############################################################################################

# @router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook endpoint that receives WhatsApp messages from Gupshup
    This endpoint is called automatically by WhatsApp when a message is received
    """
    try:
        # Log request details for debugging
        content_type = request.headers.get("content-type", "")
        logger.info(f"Webhook received - Content-Type: {content_type}")
        
        # Get the raw body first
        raw_body = await request.body()
        logger.info(f"Raw body length: {len(raw_body)} bytes")
        
        # Handle different content types
        if not raw_body:
            logger.warning("Received empty webhook body")
            return {"status": "error", "message": "Empty request body"}
        
        # Try to parse as JSON
        try:
            if content_type.startswith("application/json"):
                body = await request.json()
            else:
                # Try to parse raw body as JSON anyway
                body_text = raw_body.decode('utf-8')
                logger.info(f"Raw body text: {body_text[:500]}...")  # Log first 500 chars
                body = json.loads(body_text)
        except json.JSONDecodeError as json_error:
            logger.error(f"JSON decode error: {json_error}")
            logger.error(f"Raw body: {raw_body.decode('utf-8', errors='ignore')}")
            
            # Check if it's form data
            if content_type.startswith("application/x-www-form-urlencoded"):
                # Handle form data
                form_data = await request.form()
                logger.info(f"Received form data: {dict(form_data)}")
                return {"status": "error", "message": "Form data not supported, expecting JSON"}
            
            return {"status": "error", "message": f"Invalid JSON: {str(json_error)}"}
        
        logger.info(f"Received webhook payload: {json.dumps(body, indent=2)}")
        
        # Extract data from Gupshup payload structure
        app_name = body.get("app")
        timestamp = body.get("timestamp")
        message_type = body.get("type")
        payload_data = body.get("payload", {})
        
        # Extract message details from payload
        message_id = payload_data.get("id")
        source = payload_data.get("source")  # This is the sender's phone number
        message_type_detail = payload_data.get("type")
        message_payload = payload_data.get("payload", {})
        sender = payload_data.get("sender", {})
        
        # Extract the actual message text
        if message_type_detail == "text":
            message_text = message_payload.get("text", "")
        else:
            message_text = "Non-text message received"
        
        # Extract sender details
        sender_phone = sender.get("phone", source)  # Use source as fallback
        sender_name = sender.get("name", "")
        country_code = sender.get("country_code", "")
        dial_code = sender.get("dial_code", "")
        
        logger.info(f"Received WhatsApp message from {sender_phone}: {message_text}")
        
        # Save the user message to database only if mobile number is available
        message_id = None
        if sender_phone:
            try:
                message_data = {
                    "mobile": sender_phone,
                    "message": message_text,
                    "payload": json.dumps(body)  # Save the entire payload as JSON string
                }
                
                save_result = database_service.save_whatsapp_message(message_data)
                message_id = save_result.get('message_id')
                logger.info(f"User message saved to database with ID: {message_id}")
                
            except Exception as save_error:
                logger.error(f"Failed to save user message to database: {save_error}")
                message_id = None
                # Continue processing even if save fails
        else:
            logger.info("Skipping database save - mobile number is None")
        
        # Check if this is a status check request
        if not is_status_check_request(message_text):
            # Send a helpful response for non-status messages
            await whatsapp_service.send_message(
                phone_number=sender_phone,
                message="Hi! To check your application status, please send a message like 'Check my application status' along with your mobile number."
            )
            
            return {"status": "success", "message": "Non-status message handled"}
        
        # Extract phone number from sender's phone
        if sender_phone:
            # Clean the phone number
            phone_number = str(sender_phone).strip()
            
            # Remove +91 prefix if present (only if it's at the beginning)
            if phone_number.startswith('+91'):
                phone_number = phone_number[3:]  # Remove +91
            elif phone_number.startswith('91') and len(phone_number) > 10:
                # Only remove 91 if it's a country code (phone number is longer than 10 digits)
                phone_number = phone_number[2:]
            
            # Ensure it's exactly 10 digits for Indian mobile numbers
            if len(phone_number) == 10:
                # Valid 10-digit number
                pass
            elif len(phone_number) > 10:
                # Take the last 10 digits
                phone_number = phone_number[-10:]
            elif len(phone_number) < 10:
                # Too short, might be invalid
                phone_number = None
        else:
            phone_number = None
        
        logger.info(f"Processing status check for phone: {phone_number}")
        
        if not phone_number:
            # Send error message via WhatsApp
            error_message = "We couldn't identify your mobile number. Please try again."
            await whatsapp_service.send_message(
                phone_number=sender_phone,
                message=error_message
            )
            
            return {
                "status": "error",
                "message": "Phone number not found",
                "phone_number": None
            }
        
        # Try to get status from Basic Application API
        api_status = await basic_app_service.get_lead_status(
            mobile_number=str(phone_number),
        )

        if api_status:
            # Extract status from API response
            status = api_status.get("result", {}).get("latestStatus", "Not found")
            response_message = f"Your application status is: {status}"
            
            # Get lead data from database for WhatsApp response
            lead_data = database_service.get_leads_by_mobile(phone_number)[0]  # Get the first record
            
            # Save status to Supabase database
            try:
                if lead_data and lead_data.get("basic_app_id"):
                    basic_app_id = lead_data.get("basic_app_id")
                    if basic_app_id:
                        database_service.update_lead_status(str(basic_app_id), str(status))
                        logger.info(f"Status updated in database for mobile: {phone_number}")
            except Exception as db_error:
                logger.error(f"Failed to update status in database: {db_error}")
            
            # Send WhatsApp response with the status
            if lead_data:
                name = lead_data.get("first_name", "") + " " + lead_data.get("last_name", "")
                        
                # Send the status update to WhatsApp
                await whatsapp_service.send_lead_status_update(
                    phone_number="+91" + phone_number,
                    name=name,
                    status=str(status)
                )
            else:
                # Send simple message if lead data not found
                await whatsapp_service.send_message(
                    phone_number=sender_phone,
                    message=response_message
                )
            
            return {
                "status": "success",
                "message": "Status sent successfully",
                "application_status": str(status),
                "phone_number": phone_number
            }
        else:
            # Send error message via WhatsApp
            error_message = "We couldn't find your application details. Please check your mobile number or application ID."
            await whatsapp_service.send_message(
                phone_number=sender_phone,
                message=error_message
            )
            
            return {
                "status": "error",
                "message": "Application not found",
                "phone_number": phone_number
            }
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        # Send error message to user if we have the phone number
        try:
            if 'sender_phone' in locals():
                await whatsapp_service.send_message(
                    phone_number=sender_phone,
                    message="Sorry, there was an error processing your request. Please try again later."
                )
        except:
            pass
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

############################################################################################
                                # New WhatsApp Webhook API
############################################################################################

def process_message_data(payload: dict, requested_data: dict) -> dict:
    """
    Process the message data and insert the requested data
    Args:
        payload: The payload of the message
        requested_data: The requested data
    Returns:
        dict: The requested data
    """
    msg_type = payload.get("type", "")  # text, image, video, audio, document, location, contact, etc.
    if msg_type =="text":
        text = payload.get("payload", {}).get("text", "")
        inbound_id = payload.get("id", "")
        sender = payload.get("sender", {})
    
        requested_data["phone"] = sender.get("phone", "")
        requested_data["user_message"] = text
        requested_data["response_to_user"] = ""

        # Pop the data which should not be updated
        requested_data.pop("billing_details")
        requested_data.pop("event_details")

        # If message type is text, and text is based on context
        requested_data["wa_id"] = payload.get("context", {}).get("id", "")
        requested_data["gs_id"] = payload.get("context", {}).get("gsId", "")
        requested_data["previous_message"] = payload.get("context", {}).get("postbackText", "")
        requested_data["app_phone_number"] = payload.get("context", {}).get("from", "")

        # Update the sender details
        requested_data["sender_details"]["phone"] = sender.get("phone", "")
        requested_data["sender_details"]["name"] = sender.get("name", "")
        requested_data["sender_details"]["country_code"] = sender.get("country_code", "")
        requested_data["sender_details"]["dial_code"] = sender.get("dial_code", "")
        
        requested_data["message_details"]["text"] = text
        requested_data["message_details"]["inbound_id"] = inbound_id
        requested_data["message_details"]["created_at"] = to_utc_dt(payload.get("timestamp", None)).isoformat() # Convert the timestamp to UTC datetime and format for database
        
        # Set root-level created_at and updated_at for database table
        timestamp_iso = to_utc_dt(payload.get("timestamp", None)).isoformat()
        requested_data["created_at"] = timestamp_iso # Convert the timestamp to UTC datetime and format for database
        requested_data["updated_at"] = timestamp_iso # Set updated_at to same value as created_at for new records
        
        requested_data["fallback_trigger"] = False  # Setting it False as this is the msg we received from user
        requested_data["retry_count"] = 0  # Setting it 0 as this is the first message
        
    return requested_data

def process_message_event_data(payload: dict, requested_data: dict) -> dict:
    """
    Process the message event data and update the requested data
    Args:
        payload: The payload of the message event
        requested_data: The requested data
    Returns:
        dict: The requested data
    """
    status = payload.get("type", "")
    wa_id = payload.get("id", "")
    gs_id = payload.get("gsId", "")
    destination = payload.get("dest", "")
    ts = payload.get("payload", {}).get("ts", "")

    # Pop the data which should not be updated
    requested_data.pop("message_details")
    requested_data.pop("sender_details")
    requested_data.pop("billing_details")

    # Update the requested data
    requested_data["phone"] = destination
    requested_data["wa_id"] = wa_id
    requested_data["gs_id"] = gs_id
    requested_data["phone"] = destination
    requested_data["event_details"]["event_status"] = status
    requested_data["event_details"]["event_wa_id"] = wa_id
    requested_data["event_details"]["event_gs_id"] = gs_id
    requested_data["event_details"]["event_destination"] = destination
    requested_data["event_details"]["event_updated_at"] = to_utc_dt(ts).isoformat() # Convert the timestamp to UTC datetime and format for database
    
    # Set root-level updated_at for database table
    event_timestamp_iso = to_utc_dt(ts).isoformat()
    requested_data["updated_at"] = event_timestamp_iso # Set updated_at for event records

    return requested_data

def process_billing_event_data(payload: dict, requested_data: dict) -> dict:
    """
    Process the billing event data and insert the requested data
    Args:
        payload: The payload of the billing event
        requested_data: The requested data
    Returns:
        dict: The requested data
    """
    ded = payload.get("deductions", {})
    refs = payload.get("references", {})
    billable = ded.get("billable")
    category = ded.get("category")
    policy = ded.get("policy", ded.get("model"))
    wa_id = refs.get("id")
    gs_id = refs.get("gsId")
    destination = refs.get("destination")

    # Pop the data which should not be updated
    requested_data.pop("message_details")
    requested_data.pop("sender_details")
    requested_data.pop("event_details")

    # Update the requested data
    requested_data["phone"] = destination
    requested_data["wa_id"] = wa_id
    requested_data["gs_id"] = gs_id
    requested_data["billing_details"]["billing_deductions"] = ded
    requested_data["billing_details"]["billing_references"] = refs
    requested_data["billing_details"]["billing_billable"] = billable
    requested_data["billing_details"]["billing_category"] = category
    requested_data["billing_details"]["billing_policy"] = policy
    requested_data["billing_details"]["billing_wa_id"] = wa_id
    requested_data["billing_details"]["billing_gs_id"] = gs_id
    requested_data["billing_details"]["billing_updated_at"] = to_utc_dt(payload.get("timestamp", None)).isoformat() 

    # Set root-level updated_at for database table
    billing_timestamp_iso = to_utc_dt(payload.get("timestamp", None)).isoformat() 
    requested_data["updated_at"] = billing_timestamp_iso # Set updated_at for billing records

    return requested_data
            
def extract_data_from_body(body: dict) -> dict:
    """
    Extract data from Gupshup payload structure

    Args:
        body: Gupshup payload structure
    Returns:
        dict: data containing all details of the message
    """
    # Extract data from Gupshup payload structure
    app_name = body.get("app")
    timestamp = body.get("timestamp")
    message_type = body.get("type")
    payload_data = body.get("payload", {})
    
    # Extract message details from payload
    message_id = payload_data.get("id")
    source = payload_data.get("source")  # This is the sender's phone number
    message_type_detail = payload_data.get("type")
    message_payload = payload_data.get("payload", {})
    sender = payload_data.get("sender", {})
    
    # Extract the actual message text
    if message_type_detail == "text":
        message_text = message_payload.get("text", "")
    else:
        message_text = "Non-text message received"
    
    # Extract sender details
    sender_phone = sender.get("phone", source)  # Use source as fallback
    sender_name = sender.get("name", "")
    country_code = sender.get("country_code", "")
    dial_code = sender.get("dial_code", "")

    logger.info(f"Received WhatsApp message from {sender_phone}: {message_text} with app name: {app_name}")
    return {
        "app_name": app_name,
        "timestamp": to_utc_dt(timestamp).isoformat() if timestamp else None,  # Convert timestamp to ISO format for database
        "message_type": message_type,
        "user_message": message_text,
        "source": source,
        "mobile": sender_phone,
        "response_to_user": "",
        "template_id": "1234567890",
        "template_name": "welcome",
        "payload": json.dumps(body),
        "message_details": {
            "message_id": message_id,
            "message": message_text,
            "message_type_detail": message_type_detail,
            "message_payload": message_payload
        },
        "sender_details": {
            "phone": sender_phone,
            "name": sender_name,
            "country_code": country_code,
            "dial_code": dial_code
        }
    }

@router.post("/whatsapp/gupshup/webhook")
async def gupshup_whatsapp_webhook(request: Request):
    """
    Webhook endpoint that receives WhatsApp messages from Gupshup
    This endpoint is called automatically by WhatsApp when a message is received
    """
    
    # try:
        # Log request details for debugging
    content_type = request.headers.get("content-type", "")
    # content_type = "application/json"
    logger.info(f"Webhook received - Content-Type: {content_type}")
    
    # Get the raw body first
    raw_body = await request.body() # TODO: Uncomment this while deploying & remove the below line
    # raw_body = request.get("body", "")
    logger.info(f"Raw body length: {len(raw_body)} bytes")

    #-------------------------------------------------------------------------#
    # TODO: Remove this after testing
    # body = {
    #         "app": "HomiAi",
    #         "timestamp": 1762324484943,
    #         "version": 2,
    #         "type": "message",
    #         "payload": {
    #             "id": "wamid.HBgMOTE3OTg4MzYyMjgzFQIAEhgUM0E2ODE4RUJEODc0N0YxRDVDOTYA",
    #             "source": "917988362283",
    #             "type": "text",
    #             "payload": {
    #             "text": "Mumbai"
    #             },
    #             "sender": {
    #             "phone": "917988362283",
    #             "name": "Asheem Siwach",
    #             "country_code": "91",
    #             "dial_code": "7988362283"
    #             }
    #         }
    #         }

    # raw_body = json.dumps(body)
    #-------------------------------------------------------------------------#
    
    # Handle different content types
    # if not raw_body:
    #     # TODO: Remove this after testing
    #     await whatsapp_service.send_message_with_app_config(
    #         phone_number="917988362283",
    #         message="Empty request body",
    #         app_name="Homfinity"
    #         )
    #     logger.warning("Received empty webhook body")
    #     return {"status": "error", "message": "Empty request body"}
    
    # Try to parse as JSON
    try:
        if content_type.startswith("application/json"):
            body = await request.json() # TODO: Uncomment this while deploying & remove the below line
            # body = request.get("body", "")
        else:
            # Try to parse raw body as JSON anyway
            body_text = raw_body.decode('utf-8') # TODO: Uncomment this while deploying & remove the below line
            # body_text = raw_body 
            logger.info(f"Raw body text: {body_text[:500]}...")  # Log first 500 chars
            body = json.loads(body_text)
    except json.JSONDecodeError as json_error:
        logger.error(f"JSON decode error: {json_error}")
        logger.error(f"Raw body: {raw_body.decode('utf-8', errors='ignore')}")
        
        # Check if it's form data
        if content_type.startswith("application/x-www-form-urlencoded"):
            # Handle form data
            form_data = await request.form() # TODO: Uncomment this while deploying & remove the below line
            # form_data = request.get("form", "")
            logger.info(f"Received form data: {dict(form_data)}")
            return {"status": "error", "message": "Form data not supported, expecting JSON"}
        
        return {"status": "error", "message": f"Invalid JSON: {str(json_error)}"}
    
    logger.info(f"Received webhook payload: {json.dumps(body, indent=2)}")

    ## Deep 1:- Extract the data in more depth
    requested_data = {"sender_details":{}, "message_details":{}, "event_details":{}, "billing_details":{}}
    # Deep 1.1: Extract the body type and payload 
    top_level_type = body.get("type", "")
    payload = body.get("payload", {})

    requested_data["app_name"] = body.get("app", "Not Defined")  # Can be used to identify the app name
    requested_data["message_type"] = top_level_type
    requested_data["payload"] = body.get("payload", {})
    
    # Deep 1.2: Extract the data from the payload
    try: 
        if top_level_type == "message":
            requested_data = process_message_data(payload, requested_data)

            if requested_data:
                # Save inbound message to the database
                try:
                    inbound_insert_result = database_service.save_whatsapp_conversation(table_name="whatsapp_conversation_test", message_data=requested_data, environment="orbit")
                    requested_data["record_id"] = inbound_insert_result.get("message_id", "")
                except Exception as e:
                    logger.error(f"Error saving conversation to database: {str(e)}")
                    return {"status": "error", "message": "Error saving conversation to database", "error": str(e)} 

                try:
                    # Restructure the data from the body
                    # message_data = extract_data_from_body(body)
                    # user_text = message_data["user_message"]

                    data = await generate_user_response(data=requested_data)
                    print("\n\nGenerate User Response: ", data)
                    print("----------------------------------------------------")
                except Exception as e:
                    logger.warning(f"Error generating user response: {str(e)}")
                    return {"status":"error", "message": "Error generating user response", "error": str(e)}



        elif top_level_type == "message-event":
            requested_data = process_message_event_data(payload, requested_data)

            if requested_data:
                try:
                    event_update_result = database_service.update_record(
                        table_environment="whatsapp_campaigns",
                        table_name="whatsapp_conversation_test",
                        record_col_name="wa_id",
                        record_id=requested_data["wa_id"],
                        update_data=requested_data,
                        environment="orbit"
                    )
                    requested_data["record_id"] = event_update_result.get("message_id", "")
                except Exception as e:
                    logger.error(f"Error updating event data to database: {str(e)}")
                    return {"status": "error", "message": "Error updating event data to database", "error": str(e)}

        elif top_level_type == "billing-event":
            requested_data = process_billing_event_data(payload, requested_data)

            if requested_data:
                try:
                    billing_update_result = database_service.update_record(
                        table_environment="whatsapp_campaigns",
                        table_name="whatsapp_conversation_test",
                        record_col_name="wa_id",
                        record_id=requested_data["wa_id"],
                        update_data=requested_data,
                        environment="orbit"
                    )
                    requested_data["record_id"] = billing_update_result.get("message_id", "")
                except Exception as e:
                    logger.warning(f"Error updating billing data to database: {str(e)}")
                    return {"status": "error", "message": "Error updating billing data to database", "error": str(e)}

        else:
            logger.warning(f"Unknown event type: {top_level_type}")
            return {"status": "error", "message": "Unknown event type", "error": "unknown_event_type"}

        return {"status": "success", "message": "Event processed successfully", "requested_data": requested_data}
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        return {"status": "error", "message": "Error processing WhatsApp webhook", "error": str(e)}

            




    # Saving the message data to the database
    # save_result = database_service.save_whatsapp_conversation(message_data)
    # logger.info(f"2nd Conversation saved to database: {save_result}")
    

    # except Exception as e:
    #     logger.error(f"Error processing WhatsApp webhook: {str(e)}")
    #     return {"status": "error", "message": "Error processing WhatsApp webhook", "error": str(e)}


############################################################################################
                                # WhatsApp Webhook Verification API
############################################################################################

@router.get("/whatsapp/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None
):
    """
    Webhook verification endpoint for WhatsApp Business API
    This is called by WhatsApp to verify your webhook URL
    """
    # Get verify token from environment variables
    verify_token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token and hub_challenge:
        logger.info("Webhook verified successfully")
        return int(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed") 