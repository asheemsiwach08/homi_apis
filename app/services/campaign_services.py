from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from app.services.database_service import database_service
import logging
logger = logging.getLogger(__name__)


def to_utc_dt(ts: Optional[int]) -> datetime:
    """
    Convert provider timestamps (ms or sec) to UTC datetime.
    Accepts None; returns now() in that case to avoid crashes (adjust if you prefer).
    """
    # Handle None or empty values
    if ts is None or ts == "" or ts == "None":
        return datetime.now(tz=timezone.utc)
    
    # Convert string to int if needed
    try:
        if isinstance(ts, str):
            # Handle empty string or invalid string
            if ts.strip() == "":
                return datetime.now(tz=timezone.utc)
            ts = int(ts)
        elif not isinstance(ts, (int, float)):
            # If it's not a number type, return current time
            return datetime.now(tz=timezone.utc)
    except (ValueError, TypeError):
        # If conversion fails, return current time
        logger.warning(f"Invalid timestamp format: {ts}, using current time")
        return datetime.now(tz=timezone.utc)
    
    # Heuristic: >10_000_000_000 => looks like ms
    if ts > 10_000_000_000:
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    return datetime.fromtimestamp(ts, tz=timezone.utc)



def calculate_time_difference_hours(datetime_string: str) -> float:
    """
    Calculate the time difference between a given datetime string and current UTC time in hours
    
    Args:
        datetime_string: ISO format datetime string (e.g., '2025-11-06T06:28:38+00:00')
        
    Returns:
        float: Time difference in hours (positive if datetime_string is in the future, 
                negative if in the past)
                
    Raises:
        HTTPException: If datetime string format is invalid
    """
    try:
        # Parse the input datetime string
        if datetime_string.endswith('Z'):
            # Handle 'Z' timezone indicator
            input_datetime = datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
        else:
            # Handle standard ISO format with timezone
            input_datetime = datetime.fromisoformat(datetime_string)
        
        # Ensure the input datetime is timezone-aware (convert to UTC if needed)
        if input_datetime.tzinfo is None:
            # If no timezone info, assume UTC
            input_datetime = input_datetime.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if it has timezone info
            input_datetime = input_datetime.astimezone(timezone.utc)
        
        # Get current UTC time
        current_utc = datetime.now(timezone.utc)
        
        # Calculate the difference
        time_diff = current_utc - input_datetime
        
        # Convert to hours
        hours_difference = time_diff.total_seconds() / 3600
        print("Hours difference: ", hours_difference)
        
        return hours_difference
        
    except ValueError as e:
        logger.error(f"Invalid datetime format: {datetime_string}, Error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid datetime format: {datetime_string}. Expected ISO format like '2025-11-06T06:28:38+00:00'"
        )
    except Exception as e:
        logger.error(f"Error calculating time difference: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating time difference: {str(e)}"
        )



#--------------------------------------------- Database Operations ---------------------------------------------#
def get_campaign_history(data: dict) -> Tuple[bool, str, str, str]:
    # Get campaign history for the user
    try:
        campaign_history = database_service.get_records_from_table(
            table_environment="whatsapp_campaigns", 
            table_name="campaign_history", 
            col_name="app_name", 
            col_value=data.get("app_name", ""),
            where_clauses = [
                {"column": "phone", "operator": "eq", "value": data.get("phone", "")},
                {"column": "is_active", "operator": "eq", "value": "TRUE"},
            ],
            order_by="created_at",
            ascending=False,
            limit=1
        )

        if campaign_history:
            current_template_id = campaign_history[0]["current_template_id"]
            app = data["app_name"]
            campaign_history_time = campaign_history[0]["created_at"]
            return True, current_template_id, app, campaign_history_time # Return the current template id and app name
        else:
            logger.error(f"❌ No record found for the given app name and phone number: {data.get('app_name', '')} and {data.get('phone', '')}")
            return False, None, None, None # Return False and None values
    except Exception as e:
        logger.error(f"❌ Error in getting campaign history - get_campaign_history: {str(e)}")
        return False, None, None, None # Return False and None values

def get_all_templates_info(application_name: str):
    """ Get all the templates info for the given app name """
    templates_info = database_service.get_records_from_table(
        table_environment="whatsapp_campaigns", 
        table_name="template_response_configs", 
        col_name="app_name", 
        col_value=application_name
    )
    return templates_info

def get_template_response_config(application_name: str, template_id: str) -> Optional[Dict]:
    # Get template response configuration for the user
    template_response_config = database_service.get_records_from_table(
        table_environment="whatsapp_campaigns", 
        table_name="template_response_configs", 
        col_name="app_name", 
        col_value=application_name,
        where_clauses = [{"column": "template_id", "operator": "eq", "value": template_id}]
    )
    
    if template_response_config:
        return template_response_config[0]   # Return the first record as dictionary

def get_whatsapp_conversation_history(mobile_number: str,application_name: str, session_id: str) -> List[Dict]:
    # Get template response configuration for the user
    result = database_service.get_records_from_table(
        table_environment="whatsapp_campaigns", 
        table_name="whatsapp_conversation_test", 
        col_name="phone", 
        col_value=mobile_number,
        where_clauses = [{"column": "app_name", "operator": "eq", "value": application_name}],
        # ,{"column": "session_id", "operator": "eq", "value": session_id}],
        order_by="created_at",
        ascending=False,
        limit=2
    )
    if result and len(result) == 2:
        return result[1], result[0].get("id", ""), result[0].get("previous_message", "")    # Return the second record as dictionary and the first record id
    elif result and len(result) == 1:
        return None, result[0].get("id", ""), result[0].get("previous_message", "")
    else: return None, None, None
   

def get_response_config_details(data: dict) -> list:
    """ Get the response config details for the current template id """

    response_config = data.get("response_config", {})

    if not isinstance(response_config, dict) or len(response_config) == 0:
        return []

    nodes = []
    if response_config:
        for node in response_config.get("nodes", []):
            if isinstance(node, dict) and node.get("id") != None and node.get("id") != "":
                nodes.append(node.get("id", ""))
    return nodes if len(nodes) > 0 else []

def get_node_details(id: str, data: dict) -> dict:
    """ Get the node details for the given node id """
    nodes = data.get("response_config", {}).get("nodes", [])
    
    if not isinstance(nodes, list) or len(nodes) == 0:
        return {}
    
    for node in nodes:
        if not isinstance(node, dict) or not node.get("id"):
            continue
            
        if node.get("id") == id:
            return node
    return {}

def get_message_id(message_response: dict):
    message_id = ""
    if message_response and hasattr(message_response, 'success') and message_response.success:
        # Check if messageId is in the direct data field
        if hasattr(message_response, 'data') and message_response.data and isinstance(message_response.data, dict):
            message_id = message_response.data.get("messageId", "")
            if message_id:
                logger.info(f"🔷Message id: {message_id} found in the whatsapp message response (direct data)")
        
        # Check if messageId is in the gupshup_response data field
        if not message_id and hasattr(message_response, 'gupshup_response') and message_response.gupshup_response and isinstance(message_response.gupshup_response, dict):
            gupshup_data = message_response.gupshup_response.get("data", {})
            if isinstance(gupshup_data, dict):
                message_id = gupshup_data.get("messageId", "")
                if message_id:
                    logger.info(f"🔷Message id: {message_id} found in the whatsapp message response (gupshup_response)")
    
    if not message_id:
        logger.info(f"🔷No message id found in the whatsapp message response")
    return message_id


#------------------------------------------ Database Operations End --------------------------------------------#
#---------------------------------------------------------------------------------------------------------------#

#------------------------------------------------ Node Type Logic ----------------------------------------------#

def list_type_node_logic(user_message: str, current_node: dict):

    # Find the best match among all options
    best_match_score = 0
    best_match_row = None
    next_node_id = None

    try:
        template_data = current_node.get("metadata", {}).get("sections", [])
    except:
        return {"next_node_id": None, "response_to_user": current_node.get("content", ""), "type": current_node.get("type", ""), "level": current_node.get("level", "")}
    
    try:
        if template_data:
            from rapidfuzz import fuzz
            for section in template_data:
                for row in section.get("rows", []):
                    print(f"✨ 🔍 Row: {row}")
                    # Calculate similarity score
                    title_score = fuzz.partial_ratio(user_message.lower(), row.get("title", "").lower())
                    description_score = fuzz.partial_ratio(user_message.lower(), row.get("description", "").lower())
                    postback_score = fuzz.partial_ratio(user_message.lower(), row.get("postbackText", "").lower())
                    
                    # Take the highest score among title, description, and postbackText
                    max_score = max(title_score, description_score, postback_score)
                    logger.info(f"✨ 🔍 Max score: {max_score}")
                    
                    if max_score > best_match_score:
                        best_match_score = max_score
                        best_match_row = row
            
            # Check if we found a good match (threshold: 90)
            if float(best_match_score) >= float(90) and best_match_row:
                # Get next node ID from nextNodes mapping using row id
                # level = current_node.get("level", "")
                next_node_data = current_node.get("nextNodes", {}).get(f"next_0", {})       # TODO: Change this to nextNodeId after testing
                next_node_id = next_node_data.get("nodeId", "")
                next_level = next_node_data.get("level", "")
                node_type = next_node_data.get("type", "")
                content = next_node_data.get("content", "")

                logger.info(f"✅ User message matched with option: {best_match_row.get('title', '')} (Score: {best_match_score})")
                logger.info(f"➡️ Next node id will be: {next_node_id}")
                return {"next_node_id": next_node_id, "response_to_user": content, "type": node_type, "level": next_level}
            else:
                logger.info(f"\t ❌ No good match found (Best score: {best_match_score})")
                return {"next_node_id": None, "response_to_user": None, "type": current_node.get("type", ""), "level": current_node.get("level", "")}
    except Exception as e:
        logger.error(f"Error in list type node logic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in list type node logic: {str(e)}")

def quick_reply_type_node_logic(template_config, user_message: str, current_node: dict ):

    # Find the best match among all options
    best_match_score = 0
    best_match_row = None
    next_node_id = None

    try:
        template_data = current_node.get("metadata", {}).get("options", [])
    except:
        return {"next_node_id": None, "response_to_user": current_node.get("content", ""), "type": current_node.get("type", ""), "level": current_node.get("level", "")}
    
    try:
        if template_data:
            from rapidfuzz import fuzz
            for option in template_data:
                title_score = fuzz.partial_ratio(user_message.lower(), option.get("title", "").lower())
                description_score = fuzz.partial_ratio(user_message.lower(), option.get("description", "").lower())
                postback_score = fuzz.partial_ratio(user_message.lower(), option.get("postbackText", "").lower())
                
                # Take the highest score among title, description, and postbackText
                max_score = max(title_score, description_score, postback_score)
                if max_score > best_match_score:
                    best_match_score = max_score
                    best_match_option = option

            # Check if we found a good match (threshold: 90)
            if float(best_match_score) >= 90 and best_match_option:
                # Get next node ID from nextNodes mapping using row id
                print("Best match option ----------->", best_match_option)
                next_node_data_list = [node for node in template_config.get("response_config", {}).get("nodes", []) if node.get("id") == best_match_option.get("nextNodeId")]  # Selecting the one node with the best match   
                if isinstance(next_node_data_list, list) and len(next_node_data_list) > 0:
                    next_node_data = next_node_data_list[0]
                else:
                    raise HTTPException(status_code=400, detail=f"No next node data found for the best match option: {best_match_option.get('title', '')}")
                next_node_id = next_node_data.get("id", "")
                next_level = next_node_data.get("level", "")
                node_type = next_node_data.get("type", "")
                content = next_node_data.get("content", "")

                logger.info(f"✅ User message matched with option: {best_match_option.get('title', '')} (Score: {best_match_score})")
                logger.info(f"➡️ Next node id will be: {next_node_id}")
                return {"next_node_id": next_node_id, "response_to_user": content, "type": node_type, "level": next_level}
            else:
                logger.info(f"\t ❌ No good match found (Best score: {best_match_score})")
                return {"next_node_id": None, "response_to_user": None, "type": current_node.get("type", ""), "level": current_node.get("level", "")}
    except Exception as e:
        logger.error(f"Error in quick replies type node logic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in quick replies type node logic: {str(e)}")
    
def get_fallback_response(node_data: dict, default_message: str) -> dict:
    fallback_response = node_data.get("metadata", {}).get("fallback", {})
    fallback_enabled = fallback_response.get("enabled", True)
    current_node_id = node_data.get("id", "")

    if fallback_enabled:
        fallback_message = fallback_response.get("message", default_message)
        retry_count = fallback_response.get("retryCount", 3)
        next_node_id = current_node_id  # Stay on current node for retry
        logger.info(f"♾️ Fallback message: {fallback_message}")
        logger.info(f"➡️ Staying on current node: {next_node_id}")
        return {"fallback_message": fallback_message, "retry_count": retry_count, "next_node_id": next_node_id}
    else:
        logger.info(f"❌ No match found and fallback is disabled")
        return {"fallback_message": default_message, "retry_count": 0, "next_node_id": current_node_id}

#------------------------------------------------ Node Type Logic Ends ----------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------#


async def generate_user_response(data: dict, whatsapp_user_data: dict):

    if isinstance(whatsapp_user_data, dict):
        logger.info(f"✅ Whatsapp user data found")
        latest_conversation_id = whatsapp_user_data.get("latest_conversation_id", "")
        previous_message = whatsapp_user_data.get("previous_message", "")
        whatsapp_conversation_history = whatsapp_user_data.get("whatsapp_conversation_history", {})
        current_template_id = whatsapp_user_data.get("current_template_id", "")
        app_name = whatsapp_user_data.get("app_name", "")

    # Get the template response configuration for the current template id
    try:
        template_response_config = get_template_response_config(application_name=app_name, template_id=current_template_id)
        if not isinstance(template_response_config, dict) or len(template_response_config) == 0:
            logger.warning(f"🟠 No template response configuration found")
            return {"error": f"No template response configuration found"}
        logger.info(f"✅ Template response configuration found")#{template_response_config}")
    except Exception as e:
        logger.error(f"❌ Error in getting template response configuration: {str(e)}")
        return {"error": f"Error in getting template response configuration: {str(e)}"}

    # Get nodes data from the template response configuration
    try:
        nodes_data = get_response_config_details(data=template_response_config)
        if not isinstance(nodes_data, list) or len(nodes_data) == 0:
            logger.warning(f"🟠 No nodes data found in the template response configuration")
            return {"error": f"No nodes data found in the template response configuration"}
        logger.info(f"✅ Nodes data found")
    except Exception as e:
        logger.error(f"❌ Error in getting nodes data: {str(e)}")
        return {"error": f"Error in getting nodes data: {str(e)}"}

    # Move to nodes
    logger.info(f"🔷 Whatsapp conversation history: {whatsapp_conversation_history}")
    if whatsapp_conversation_history and isinstance(whatsapp_conversation_history, dict):
        current_node_id = whatsapp_conversation_history.get("current_node_id", "")
        next_node_id = whatsapp_conversation_history.get("next_node_id", "")
        fallback_trigger = whatsapp_conversation_history.get("fallback_trigger", "")
        retry_count = whatsapp_conversation_history.get("retry_count", 0)
    else:
        current_node_id = ""
        next_node_id = ""
        fallback_trigger = ""
        retry_count = 0
    logger.info(f"🔷Retry count: {retry_count} for the conversation id: {latest_conversation_id}")
    print(f"➡️‼️ User message: {data['user_message']} ‼️ Current node id: {current_node_id} ‼️ Next node id: {next_node_id} ‼️ Fallback trigger: {fallback_trigger} ‼️ Retry count: {retry_count}")

    if int(retry_count) >= 3:
        # TODO: Implement AI fallback response here - for now just adding simple text response
        logger.warning(f"🟠 Retry count is greater than 3: {retry_count}")
        response_to_user = "Sorry, I didn't understand your message. Please try again. Try with a different message."
        fallback_trigger = True
        retry_count += 1
        from app.api.endpoints.gupshup_apis import send_message, MessageRequest
        requested = MessageRequest(app_name=app_name, phone_number=data.get("phone", ""), message={"type":"text", "text": response_to_user})
        print(f"✨ 🔍 Requested: {requested}")
        message_response = await send_message(request=requested)

        logger.info(f"❌ Retry count is greater than 3, adding a fallback response - Retry count: {retry_count}")
        return {"response_to_user": response_to_user, "fallback_trigger": fallback_trigger}


    logger.info(f"🔷 Current node id: {current_node_id}")
    logger.info(f"🔷 Nodes data: {nodes_data}")

    ## ----------------------------------------------- NODE LOGIC ------------------------------------------------------##
    if current_node_id in ["", None, "undefined", "null", "None"] and isinstance(nodes_data, list) and len(nodes_data) > 0:
        logger.info(f"🔷Getting into the nodes data logic for new conversation")
        node_details = get_node_details(id=nodes_data[0], data=template_response_config)
        node_type = node_details.get("type", "")
        metadata = node_details.get("metadata", {})
        content = node_details.get("content", "")
        current_node_id = node_details.get("id", "") if isinstance(node_details, dict) and node_details.get("id") != None and node_details.get("id") != "" else ""
        logger.info(f"🔷 Based on new conversation, the current node id: {current_node_id}")

    # Node Logic 1.1:- for Current Node (If current node id is present in conversation history)
    if current_node_id not in ["", None, "undefined", "null", "None"]:
        logger.info(f"🔷 Getting into the nodes data logic for existing conversation")
        current_node_details = get_node_details(id=current_node_id, data=template_response_config)
        logger.info(f"🟢 Current node details: {current_node_details}")

        # Node Logic 1.2:- Match the user message with the current node message/options
        user_message = data['user_message']

        # TODO: Node Logic 1.2.1:- Might need to check the type of response we need for the template, it might be options, text etc
        response_check_type = current_node_details.get("type", "").lower()
        print(f"✨ 🔍 Response check type: {response_check_type}")

        fallback_message = ""
        fallback_trigger = False
        # Node Logic 1.2.1:- Handle multiple node types
        if response_check_type == "list":
            list_response = list_type_node_logic(user_message=user_message, current_node=current_node_details)
            logger.info(f"🟢 List response: {list_response}")
            next_node_id = list_response.get("next_node_id", "")
            response_to_user = list_response.get("response_to_user", "")
            node_type = list_response.get("type", "")
            node_level = list_response.get("level", "")

            if isinstance(next_node_id, str) and next_node_id != None:
                metadata = get_node_details(id=next_node_id, data=template_response_config).get("metadata", {})
            else: 
                metadata = get_node_details(id=current_node_id, data=template_response_config).get("metadata", {})

            if not next_node_id and not response_to_user:    # No good match found, handle fallback
                fallback_response = get_fallback_response(node_data=current_node_details, default_message="I'm sorry, I didn't understand your selection. Please choose from the list above.")
                logger.info(f"🟡 Fallback response: {fallback_response}")
                next_node_id = fallback_response.get("next_node_id", "")
                fallback_message = fallback_response.get("fallback_message", "")
                fallback_trigger = True
                if fallback_message == "" and fallback_trigger == True:
                    fallback_message = "I'm sorry, I didn't understand your selection. Please choose from the list above."
                    metadata = get_node_details(id=current_node_id, data=template_response_config).get("metadata", {})
                total_retry_count = fallback_response.get("retry_count", 0)
                retry_count += 1   # Increment the retry count by 1

        elif response_check_type == "quick_reply":
            quick_reply_response = quick_reply_type_node_logic(user_message=user_message, current_node=current_node_details, template_config=template_response_config)
            logger.info(f"🟢 Quick reply response: {quick_reply_response}")
            next_node_id = quick_reply_response.get("next_node_id", "")
            response_to_user = quick_reply_response.get("response_to_user", "")
            node_type = quick_reply_response.get("type", "")
            node_level = quick_reply_response.get("level", "")
           
            if isinstance(next_node_id, str) and next_node_id != None:
                metadata = get_node_details(id=next_node_id, data=template_response_config).get("metadata", {})
            else: 
                metadata = get_node_details(id=current_node_id, data=template_response_config).get("metadata", {})

            if not next_node_id and not response_to_user:    # No good match found, handle fallback
                fallback_response = get_fallback_response(node_data=current_node_details, default_message="I'm sorry, I didn't understand your selection. Please choose from the list above.")
                logger.info(f"🟡 Fallback response: {fallback_response}")
                next_node_id = fallback_response.get("next_node_id", "")
                fallback_message = fallback_response.get("fallback_message", "")
                fallback_trigger = True
                if fallback_message == "" and fallback_trigger == True:
                    fallback_message = "I'm sorry, I didn't understand your selection. Please choose from the above options."
                    metadata = get_node_details(id=current_node_id, data=template_response_config).get("metadata", {})
                total_retry_count = fallback_response.get("retry_count", 0)
                retry_count += 1   # Increment the retry count by 1

        # TODO: Add the logic for text type node
        else:
            logger.warning(f"🟠 Invalid metadata info ---->>")
            logger.error(f"Invalid response type found in template, please check and implement the logic for the same - Nodel Logic 1.2.1.1 - {response_check_type}")
            return {"error": f"Invalid response type found in template, please check and implement the logic for the same - Nodel Logic 1.2.1.1 - {response_check_type}"}

        print(f"✨ 🔍 Response to user: {response_to_user}")
        print(f"✨ 🔍 Next node id: {next_node_id}")
        print(f"✨ 🔍 Retry count: {retry_count}")
        print(f"✨ 🔍 Node type: {node_type}")
        print(f"✨ 🔍 Node level: {node_level}")
        print(f"✨ 🔍 Fallback message: {fallback_message}")
        print(f"✨ 🔍 Fallback trigger: {fallback_trigger}")
       
       # Assign the fallback message to the response to user if no response to user is found
        # if not response_to_user:
        #     response_to_user = fallback_message
        # else:
        #     retry_count = int(0)   # TODO: Check if this is correct
        #     fallback_trigger = False

      
    # TO use metadata we need to check the type, content first then move to metadata
    logger.info(f"🔷 Getting into the send message logic")
    print(f"✨ 🔍 Response to user: {response_to_user}")
    content = response_to_user

    from app.api.endpoints.gupshup_apis import send_message, MessageRequest
    if node_type == "text" and content != "":
        logger.info(f"🟢 Sending text message to the user")
        whatsapp_message_data = {"type":"text", "text": content}
        requested = MessageRequest(app_name=app_name, phone_number=data.get("phone", ""), message=whatsapp_message_data)
        print(f"✨ 🔍 Requested: {requested}")
        message_response = await send_message(request=requested)

    elif node_type == "list" and content != "":
        logger.info(f"🟢 Sending list message to the user")
        whatsapp_message_data = generate_list_message_data(message_id=latest_conversation_id, content=content, metadata=metadata, fallback_message=fallback_message, fallback_trigger=fallback_trigger)
        requested = MessageRequest(app_name=app_name, phone_number=data.get("phone", ""), message=whatsapp_message_data)
        print(f"✨ 🔍 Requested: {requested}")
        message_response = await send_message(request=requested)   

    elif node_type == "quick_reply" and content != "":
        logger.info(f"🟢 Sending quick reply message to the user")
        whatsapp_message_data = generate_quick_reply_message_data(message_id=latest_conversation_id, content=content,metadata=metadata, fallback_message=fallback_message, fallback_trigger=fallback_trigger)
        requested = MessageRequest(app_name=app_name, phone_number=data.get("phone", ""), message=whatsapp_message_data)
        print(f"✨ 🔍 Requested: {requested}")
        message_response = await send_message(request=requested)
    else:
        logger.warning(f"🟠 Invalid node type: {node_type}")
        return {"error": f"Invalid node type: {node_type}"}


    # Combine text for response_to_user based on the node type
    if  not isinstance(response_to_user, str) or response_to_user is None or response_to_user == "":
        response_to_user = combine_whatsapp_message_text(whatsapp_message_data)

    # Save the message id from the whatsapp message response in conversation history - logic for status update
    message_id = get_message_id(message_response=message_response)
    update_data={
                "wa_id": message_id, # message id - whatsapp message id
                "template_id": current_template_id,
                "template_name": template_response_config.get("app_name", ""),
                "current_node_id": next_node_id,   # Fix the current & next node thing
                "response_to_user": response_to_user,
                "fallback_trigger": fallback_trigger,
                "retry_count": retry_count,
                "node_level": node_level,
                "previous_message": previous_message,
                "is_campaign_message": True,
                "remarks": "User response saved in conversation history for campaign message"
            }
    print(f"✨ 🔍 Update data: {update_data}")
    # Save the response to the conversation history
    logger.info(f"🔷Getting into the save response to conversation history logic")
    save_response = database_service.update_record(
            table_environment="whatsapp_campaigns",
            table_name="whatsapp_conversation_test",
            record_col_name="id",
            record_id=latest_conversation_id,
            update_data=update_data,
            environment="orbit"
        )
    if save_response:
        logger.info(f"✅ Saved the final response in conversation history")
    else:
        return {"error": f"Error in saving response: {save_response}"}




##################################### Shift Upwards ######################################################

def combine_whatsapp_message_text(message_data: dict) -> str:
    """
    Combine text elements from WhatsApp message dictionary to create response_to_user string
    
    Args:
        message_data: WhatsApp message dictionary (list or quick_reply type)
        
    Returns:
        str: Combined text for response_to_user
    """
    if not isinstance(message_data, dict):
        logger.error(f"❌ Invalid message data: {message_data}")
        return ""
    
    message_type = message_data.get("type", "")
    combined_text_parts = []
    
    if message_type == "list":
        # Extract title, body, footer
        title = message_data.get("title", "").strip()
        body = message_data.get("body", "").strip()
        footer = message_data.get("footer", "").strip()
        
        # Add non-empty parts
        if title:
            combined_text_parts.append(title)
        if body:
            combined_text_parts.append(body)
        if footer:
            combined_text_parts.append(footer)
            
        # Extract options text
        items = message_data.get("items", [])
        options_text = []
        for item in items:
            options = item.get("options", [])
            for option in options:
                option_title = option.get("title", "").strip()
                if option_title:
                    options_text.append(f"• {option_title}")
        
        if options_text:
            combined_text_parts.append("Options:\n" + "\n".join(options_text))
            
    elif message_type == "quick_reply":
        # Extract content text
        content = message_data.get("content", {})
        if isinstance(content, dict):
            header = content.get("header", "").strip()
            text = content.get("text", "").strip()
            caption = content.get("caption", "").strip()
            
            if header:
                combined_text_parts.append(header)
            if text:
                combined_text_parts.append(text)
            if caption:
                combined_text_parts.append(caption)
        
        # Extract options text
        options = message_data.get("options", [])
        options_text = []
        for option in options:
            option_title = option.get("title", "").strip()
            if option_title:
                options_text.append(f"• {option_title}")
        
        if options_text:
            combined_text_parts.append("Options:\n" + "\n".join(options_text))
    
    # Join all parts with double newlines for better readability
    return "\n\n".join(combined_text_parts) if combined_text_parts else ""


def generate_list_message_data(message_id, content, metadata, fallback_message, fallback_trigger):
    metadata_sections = metadata.get("sections", [])
    if fallback_trigger:
        fallback_message = fallback_message
    else:
        fallback_message = ""

    items = []
    for section in metadata_sections:
        options_list = []
        for row in section.get("rows", []):
            section_data = {
                "type": "text",
                "title": row.get("title", ""),
                "description": row.get("description", ""),
                "postbackText": row.get("postbackText", ""),
            }
            options_list.append(section_data)
        items.append({"title": section.get("title", ""),
                "options": options_list})
   
    globalButtons = [{"type": "text", "title": "Choose One"}]

    return {"type": "list", 
        "title": metadata.get("body", ""),
        "body": metadata.get("header", ""), 
        "footer": metadata.get("footer", "") + "\n" + str(fallback_message), 
        "msgid": message_id, 
        "globalButtons": globalButtons, 
        "items": items
    }


def generate_quick_reply_message_data(message_id, content, metadata, fallback_message, fallback_trigger):
    if fallback_trigger:
        fallback_message = fallback_message
    else:
        fallback_message = ""

    metadata_options =metadata.get("options", [])
    options_list = []
    for option in metadata_options:
        option_type = option.get("type", "text")
        option_title = option.get("title", "")
        option_postbackText = option.get("postbackText", "")
        options_list.append({
            "type":option_type,
            "title":option_title,
            "postbackText":option_postbackText
        })
    content_data = {
        "type":"text",
        "header":str(fallback_message) + "\n" + str(content),
        "text":"this is the body",
        "caption":"this is the footer"
    }
    return {
        "type":"quick_reply", 
        "msgid":message_id, 
        "content":content_data, 
        "options":options_list
    }

#-----------------------------------------------------------------------------------------------------------------------#
################################################ AI RESPONSE GENERATION #################################################
#-----------------------------------------------------------------------------------------------------------------------#

async def handle_unwanted_message(requested_data: dict):

    from app.services.campaign_services import get_all_templates_info
    templates_info = get_all_templates_info(application_name=requested_data.get("app_name", ""))
    
    if not isinstance(templates_info, list) or len(templates_info) == 0:
        logger.warning(f"🟠 No templates info found")
        return {"error": f"No templates info found"}

    # Gather the tempalte details in a dictionary
    template_details = {}
    for template_info in templates_info:
        template_details[template_info.get("template_name")] = {
                                                            "template_id": template_info.get("template_id", ""),
                                                            "template_description": template_info.get("template_description", ""),
                                                            "template_response_config": template_info.get("template_response_config", {})
                                                            }

    if template_details:
        template_details_string = ""
        for template_name, template_info in template_details.items():
            template_details_string += f"Template name: {template_name}, Template description: {template_info.get('template_description', '')}\n"

    prompt = f"""You are a message-analysis assistant for a WhatsApp campaign automation system.

            You will receive:
            1. A user's WhatsApp message.
            2. A list of available templates. Each template has:
            - template_name
            - template_description
            - (optional) use-case category such as marketing, sales, follow-up, onboarding, reminders, etc.

            Your goals:
            - Carefully understand what the user is saying and what their intent is.
            - Compare the user’s intent with the template descriptions.
            - ALWAYS choose exactly ONE template that best fits the user’s message.
            - If more than one template could work, pick the one that is most relevant and useful for the user right now.

            For the WhatsApp reply message you generate:
            - First, ACKNOWLEDGE or ENGAGE with the user's message in a natural way
            (e.g., answer their question briefly, respond to their interest, or react to what they said).
            - Then, SMOOTHLY TRANSITION into the campaign flow that matches the chosen template.
            This means:
            - Gently guiding them toward the next step of the campaign (e.g., “tap below to explore offers”, 
                “reply with X to continue”, “click the button/list to proceed”, etc.),
            - Keeping the tone friendly, helpful, and conversational.
            - The reply must be aligned with the chosen template’s description and purpose.
            - The message should feel like a natural continuation of the conversation, not a random sales pitch.

            Constraints:
            - You must ALWAYS select one template.
            - Do NOT invent a template name that is not in the provided list.


            Return your answer ONLY in this JSON format (no extra text):

            {{
            "template_name": "<the_chosen_template_name>",
            "message_for_user": "<the WhatsApp reply text you want to send to the user>"
            }}

            Here is the user's message:
            {requested_data.get('user_message', '')}

            Here are the available templates:
            {template_details_string}

            Now analyse and return the best matching template.
            """
    # Implement the logic to generate the user response for the non-campaign
    from app.src.ai_analyzer import OpenAIAnalyzer
    ai_analyzer = OpenAIAnalyzer()
    ai_response = ai_analyzer.analyze_anything(prompt=prompt)
    if ai_response:
        import json
        ai_response = json.loads(ai_response)
        template_name = ai_response.get("template_name", "")
        message_for_user = ai_response.get("message_for_user", "")
        logger.info(f"✅ AI response: {ai_response}")
        logger.info(f"✅ Templates info: {template_details.keys()}")
    else:
        template_name = "no_matching_template"
        message_for_user = "I'm sorry, I didn't understand your message. Please try again."

    logger.info(f"🟢 Sending text message to the user (not from campaign/application request)")
    whatsapp_message_data = {"type":"text", "text": message_for_user}
    try:
        from app.api.endpoints.gupshup_apis import send_message, MessageRequest
        requested = MessageRequest(app_name=requested_data.get("app_name", ""), phone_number=requested_data.get("phone", ""), message=whatsapp_message_data)
        print(f"✨ 🔍 Requested: {requested}")
        message_response = await send_message(request=requested)
        message_id = get_message_id(message_response=message_response)
    except Exception as e:
        logger.warning(f"🟠 Error in sending text message to the user: {str(e)}")
        return {"error": f"Error in sending text message to the user: {str(e)}"}

    # Gather the update data
    update_data = {"wa_id": message_id if message_id else "", 
    "response_to_user": message_for_user if message_for_user else "",
    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "remarks": "User replied using AI response generated by the system"
    }
    # Save the data to the whatsapp conversation table
    database_service.update_record(
        table_environment="whatsapp_campaigns",
        table_name="whatsapp_conversation_test",
        record_col_name="id",
        record_id=requested_data["record_id"],
        update_data=update_data,
        environment="orbit"
    )

    return {"status": "success", "message": "AI response generated successfully", "template_name": template_name, "message_for_user": message_for_user}
