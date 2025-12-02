import json
import logging
from typing import Tuple
from fastapi import APIRouter, Request

from app.services.campaign_services import to_utc_dt
from app.services.whatsapp_service import whatsapp_service
from app.services.database_service import database_service
from app.api.endpoints.whatsapp_webhook import is_status_check_request
from app.services.basic_application_service import BasicApplicationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["whatsapp-webhook"])

# Initialize services
basic_app_service = BasicApplicationService()

############################################################################################
                                # New WhatsApp Webhook API
############################################################################################


@router.post("/whatsapp/gupshup/webhook")
async def gupshup_whatsapp_webhook(request: Request):
    """
    Webhook endpoint that receives WhatsApp messages from Gupshup
    This endpoint is called automatically by WhatsApp when a message is received
    """
    
    # try:
        # Log request details for debugging
    content_type = request.headers.get("content-type", "") # TODO: Uncomment this while deploying & remove the below line
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

                # First check if the message is an application status check request
                if is_status_check_request(requested_data.get("user_message", "")):
                    logger.info(f"✅ Application status check request received")
                    user_response = await send_application_status_update(data=requested_data)
                    return {"status": "success", "message": "Application status update sent successfully", "user_response": user_response}
                
                # If the message is not an application status check request, then check if it is a campaign message or not
                whatsapp_window_open, requested_data, whatsapp_user_data = is_campaign_message(requested_data=requested_data)
                if whatsapp_window_open:
                    logger.info(f"✅ User Message belogs to the Campaign & Whatsapp window open: {whatsapp_window_open}")
                    from app.services.campaign_services import generate_user_response
                    user_response = await generate_user_response(
                        data=requested_data, 
                        whatsapp_user_data=whatsapp_user_data
                    )
                    logger.info(f"✅ Generate User Response: {user_response}")
                    pass
                else:
                    logger.info(f"✅ No campaign message or application request found. Lets use the AI fallback response.")
                    from app.services.campaign_services import handle_unwanted_message
                    repsonse = await handle_unwanted_message(requested_data=requested_data)
                    logger.info(f"✅ Handle Unwanted Message: {repsonse}")
                    pass

                    

                        # TODO: Implement the logic to generate the user response for the non-campaign
                        # Using the AI fallback response
                            # user_message = data["user_message"]
                            # ai_response = "" #generate_ai_response(user_message=user_message)
                            # ai_response = {"template_id": "0922869a-cd33-4fed-83af-39376d8ccfb5", "template_params": ["Delhi", "Mumbai"]}
                            # if ai_response:
                            #     template_id = ai_response.get("template_id", "")
                            #     template_params = ai_response.get("template_params", [])

                            # #Add the template message based on AI response
                            # # from app.api.endpoints.gupshup_apis import send_template_message, DemoTemplateMessageRequest
                            # # requested = DemoTemplateMessageRequest(app_name=app_name, phone_number=data.get("phone", ""), template_id=template_id, template_params=template_params)
                            # # print(f"✨ 🔍 Requested: {requested}")
                            # # template_response = await send_template_message(request=requested)
                            # template_response = ""
                            # print(f"✨ 🔍 Template response: {template_response}")
                            # response_to_user = template_response.message if hasattr(template_response, 'message') else "I'm sorry, I didn't understand your message. Please try again."
                        # TODO: Implement AI fallback response here - for now just adding simple text response
                        # response_to_user = "Sorry, I didn't understand your message. Please try again. Try with a different message. No record found for the given app name and phone number."
                        # fallback_trigger = True
                        # requested = MessageRequest(app_name=app_name, phone_number=data.get("phone", ""), message={"type":"text", "text": response_to_user})
                        # print(f"✨ 🔍 Requested: {requested}")
                        # message_response = await send_message(request=requested)
                        # logger.info(f"\t❌ No record found for the given app name and phone number, adding a fallback response - Retry count: {retry_count}")

        elif top_level_type == "message-event":
            requested_data = process_message_event_data(payload, requested_data)
            print(f"✨ 🔍 Requested data from message event: {requested_data}")

            if requested_data:
                try:
                    event_update_result = database_service.update_record(
                        table_environment="whatsapp_campaigns",
                        table_name="whatsapp_conversation_test",
                        record_col_name="gs_id",
                        record_id=requested_data["gs_id"],
                        update_data=requested_data,
                        environment="orbit"
                    )
                    # requested_data["record_id"] = event_update_result.get("message_id", "")
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
                        record_col_name="gs_id",
                        record_id=requested_data["gs_id"],
                        update_data=requested_data,
                        environment="orbit"
                    )
                    # requested_data["record_id"] = billing_update_result.get("message_id", "")
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


############################################ Services #####################################

async def send_application_status_update(data: dict):

    phone_number = data.get("phone", None)
    
    if phone_number is None:
        return {
            "status": "error",
            "message": "We couldn't identify your mobile number. Please try again.",
            "phone_number": None
        }
    else:
        phone_number = phone_number.strip()[-10:]
    # Try to get status from Basic Application API
    api_status = await basic_app_service.get_lead_status(mobile_number=str(phone_number))

    application_status_update_data = {
        "application_status": "Not found",
        "phone_number": phone_number,
        "remarks": "",
    }
    if api_status:
        # Extract status from API response
        status = api_status.get("result", {}).get("latestStatus", "Not found")
        # response_message = f"Your application status is: {status}"
        application_status_update_data["application_status"] = str(status)
        
        # Get lead data from database for WhatsApp response
        lead_data = database_service.get_leads_by_mobile(phone_number)[0]  # Get the first record
        
        # Save status to Supabase database
        try:
            if lead_data and lead_data.get("basic_app_id"):
                basic_app_id = lead_data.get("basic_app_id")
                if basic_app_id:
                    database_service.update_lead_status(str(basic_app_id), str(status))
                    logger.info(f"Status updated in database for mobile: {phone_number}")

                name = lead_data.get("first_name", "") + " " + lead_data.get("last_name", "")        
                # Send the status update to WhatsApp
                await whatsapp_service.send_lead_status_update(
                    phone_number="+91" + phone_number,
                    name=name,
                    status=str(status)
                )
                application_status_update_data["remarks"] = "Status updated in leads table and user notified via WhatsApp"
        except Exception as db_error:
            logger.error(f"Failed to update status in database: {db_error}")
            message = "Sorry, there was an error processing your request. Please try again later."
            await whatsapp_service.send_message(
                phone_number="+91" + phone_number,
                message=message
            )
            application_status_update_data["remarks"] = "Failed to update status in database and send WhatsApp message" + str(db_error)

    else:
        logger.info(f"❎ No lead data found for phone number: {phone_number}")
        # Send simple message if lead data not found
        message = "We couldn't find your application details. Please check your mobile number or application ID."
        await whatsapp_service.send_message(
            phone_number="+91" + phone_number,
            message=message
        )
        application_status_update_data["application_status"] = message
        application_status_update_data["remarks"] = "No lead data found for phone number in database & User notified via WhatsApp"
        
        # Update the whatsapp record to whatsapp conversation table
        update_data = {"remarks": application_status_update_data["remarks"],
            "is_check_application_request": True,
            "response_to_user": application_status_update_data["application_status"]
        }
        
        update_result = database_service.update_record(
            table_environment="whatsapp_campaigns",
            table_name="whatsapp_conversation_test",
            record_col_name="id",
            record_id=data.get("record_id", ""),
            update_data=update_data,
            environment="orbit"
        )
        logger.info(f"🔷Whatsapp record process successfull for send application status update")
        if update_result:
            application_status_update_data["remarks"] = "No lead data found for phone number in database, user notified via WhatsApp & Whatsapp record updated in database"
        return application_status_update_data

    
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
    
        requested_data["phone"] = sender.get("phone", None)
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
    gs_id = payload.get("gsId", "") if "gsId" in payload.keys() else payload.get("id", "")
    wa_id = payload.get("id", "")
    # gs_id = payload.get("gsId", "")
    destination = payload.get("dest", "")
    ts = payload.get("payload", {}).get("ts", "")

    # Pop the data which should not be updated
    requested_data.pop("message_details")
    requested_data.pop("sender_details")
    requested_data.pop("billing_details")

    # Update the requested data
    # requested_data["phone"] = destination   # keep uncommented 
    requested_data["wa_id"] = wa_id
    requested_data["gs_id"] = gs_id
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
    gs_id = refs.get("gsId", "") if "gsId" in refs.keys() else refs.get("id", "")
    wa_id = refs.get("id")
    destination = refs.get("destination")

    # Pop the data which should not be updated
    requested_data.pop("message_details")
    requested_data.pop("sender_details")
    requested_data.pop("event_details")

    # Update the requested data
    # requested_data["phone"] = destination  # keep uncommented 
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


def is_campaign_message(requested_data: dict) -> Tuple[bool, dict, dict]:
    from app.services.campaign_services import get_campaign_history, calculate_time_difference_hours, get_whatsapp_conversation_history
    is_campaign_message, current_template_id, app_name, campaign_history_time = get_campaign_history(data=requested_data)
    logger.info(f"✅ Campaign message found: {is_campaign_message} with template id: {current_template_id} and app name: {app_name} and campaign history time: {campaign_history_time}")
    
    whatsapp_window_open = False
    whatsapp_user_data = {}
    if is_campaign_message:
        # Now check if any whatsapp message received from the user in the last 24 hours
        whatsapp_conversation_history, latest_conversation_id, previous_message = get_whatsapp_conversation_history(mobile_number=requested_data.get("phone", ""), application_name=app_name, session_id="")
        
        if whatsapp_conversation_history and isinstance(whatsapp_conversation_history, dict):
            last_message_time = whatsapp_conversation_history.get("created_at")
            last_message_time_difference = calculate_time_difference_hours(last_message_time)
            last_campaign_message_time_difference = calculate_time_difference_hours(campaign_history_time)
            
            if last_message_time_difference <= 24 or last_campaign_message_time_difference <= 24:
                logger.info(f"✅ Found a campaign message in the last 24 hours along with the conversation history")
                whatsapp_user_data = {"latest_conversation_id": latest_conversation_id, "previous_message": previous_message, "whatsapp_conversation_history": whatsapp_conversation_history,
                "campaign_history_time": campaign_history_time, "current_template_id": current_template_id, "app_name": app_name, "is_campaign_message": is_campaign_message}
                whatsapp_window_open = True
            else:
                logger.info(f"❌ No campaign message in the last 24 hours found no conversation history")
                whatsapp_window_open = False
        else:  # If campaign message is found but not conversation history is found
            logger.info(f"✅ Found a campaign message but no conversation history found")
            whatsapp_user_data = {"latest_conversation_id": requested_data["record_id"], "previous_message": "", "whatsapp_conversation_history": {}, 
            "campaign_history_time": campaign_history_time, "current_template_id": current_template_id, "app_name": app_name, "is_campaign_message": is_campaign_message}
            whatsapp_window_open = True

    # Update the requested data with the whatsapp window open and template id     
    requested_data["whatsapp_window_open"] = whatsapp_window_open
    requested_data["template_id"] = current_template_id

    return whatsapp_window_open, requested_data, whatsapp_user_data

