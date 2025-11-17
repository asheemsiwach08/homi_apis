from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone
from fastapi import HTTPException
from app.services.database_service import database_service
import logging
logger = logging.getLogger(__name__)


def to_utc_dt(ts: Optional[int]) -> datetime:
    """
    Convert provider timestamps (ms or sec) to UTC datetime.
    Accepts None; returns now() in that case to avoid crashes (adjust if you prefer).
    """
    if ts is None:
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
def get_campaign_history(data: dict) -> Tuple[str, str]:
    # Get campaign history for the user
    campaign_history = database_service.get_records_from_table(
        table_environment="whatsapp_campaigns", 
        table_name="campaign_history", 
        col_name="app_name", 
        col_value=data.get("app_name", ""),
        where_clauses = [
            {"column": "phone", "operator": "eq", "value": data.get("phone", "")},
            {"column": "is_active", "operator": "eq", "value": "TRUE"},
        ]
    )

    if campaign_history:
        current_template_id = campaign_history[0]["current_template_id"]
        app = data["app_name"]
        return current_template_id, app # Return the current template id and app name


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

    if len(result) == 2:
        return result[1], result[0].get("id", ""), result[0].get("previous_message", "")    # Return the second record as dictionary and the first record id
    else:
        return None, result[0].get("id", ""), result[0].get("previous_message", "")
   

def get_response_config_details(data: dict):
    # Get the response config details for the current template id

    response_config = data.get("response_config", {})
    
    if response_config:
        nodes = [node.get("id","") for node in response_config.get("nodes", [])]
        return nodes

def get_node_details(id: str, data: dict):
    # Get the node details for the given node id
    nodes = data.get("response_config", {}).get("nodes", [])
    for node in nodes:
        if node.get("id") == id:
            return node

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
            
            # Check if we found a good match (threshold: 70)
            if best_match_score >= 70 and best_match_row:
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

            # Check if we found a good match (threshold: 70)
            if best_match_score >= 70 and best_match_option:
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
        logger.info(f"\t ♾️ Fallback message: {fallback_message}")
        logger.info(f"\t ➡️ Staying on current node: {next_node_id}")
        return {"fallback_message": fallback_message, "retry_count": retry_count, "next_node_id": next_node_id}
    else:
        logger.info(f"\t ❌ No match found and fallback is disabled")
        return {"fallback_message": default_message, "retry_count": 0, "next_node_id": current_node_id}

#------------------------------------------------ Node Type Logic Ends ----------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------#


async def generate_user_response(data: dict):

    # print(f"✨ 🔍 Data: {data}")

    # TODO: 1. Lets decide some variable first
    # TODO: 2. Add a check to see if we got the session id in the data or not if not then generate new session id whilie initiating the campaign
    # TODO: 3. Find the past record in the whatsapp_conversation table for the given mobile number and session 
    # TODO: 4. Then implement this node logic for adding new record in the whatsapp_conversation table
    

    # Generate user response based on campaign history and template response configuration
    try:
        campaign_history = get_campaign_history(data)
        current_template_id, app_name = campaign_history
        logger.info(f"✅ Current template id: {current_template_id} and app name: {app_name}")
    except Exception as e:
        logger.error(f"Error in getting campaign history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in getting campaign history: {str(e)}")

    # Get the template response configuration for the current template id
    try:
        template_response_config = get_template_response_config(application_name=app_name, template_id=current_template_id)
        # logger.info(f"✅ Template response configuration: {template_response_config}")
    except Exception as e:
        logger.error(f"Error in getting template response configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in getting template response configuration: {str(e)}")

    # OPTIONAL: it can be removed if not needed
    try:
        nodes_data = get_response_config_details(data=template_response_config)
        logger.info(f"✅ Nodes data:" ) #{nodes_data}")
    except Exception as e:
        logger.error(f"Error in getting nodes data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in getting nodes data: {str(e)}")

    # Get the whatsapp conversation history
    try:
        whatsapp_conversation_history, latest_conversation_id, previous_message = get_whatsapp_conversation_history(mobile_number=data.get("phone", ""), application_name=app_name, session_id="")
        logger.info(f"✅ Whatsapp latest conversation history:" ) #{whatsapp_conversation_history}")
    except Exception as e:
        logger.error(f"Error in getting whatsapp conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in getting whatsapp conversation history: {str(e)}")

    ## TODO: Add a check here to see if current node & session id is present in conversation history
    ## If present, then get the response from the conversation history
    ## If not present, then add a fallback response


    # Move to nodes
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
    
    print(f"➡️‼️ User message: {data['user_message']} ‼️ Current node id: {current_node_id} ‼️ Next node id: {next_node_id} ‼️ Fallback trigger: {fallback_trigger} ‼️ Retry count: {retry_count}")

    if retry_count > 3:
        # TODO: Add a fallback response
        logger.info(f"\t❌Retry count is greater than 3, adding a fallback response - Retry count: {retry_count}")


    ## ---------------------------------------- NODE LOGIC ----------------------------------------------------##
    # Node Logic 1.1:- for Current Node (If current node id is present in conversation history)
    if current_node_id not in ["", None, "undefined", "null", "None"]:
        current_node_details = get_node_details(id=current_node_id, data=template_response_config)
        logger.info(f"✨Current node details: {current_node_details}")

        # Node Logic 1.2:-Match the user message with the current node message/options
        user_message = data['user_message']

        # TODO: Node Logic 1.2.1:- Might need to check the type of response we need for the template, it might be options, text etc
        response_check_type = current_node_details.get("type", "").lower()

        fallback_message = None
        # Node Logic 1.2.1:- Handle multiple node types
        if response_check_type == "list":
            list_response = list_type_node_logic(user_message=user_message, current_node=current_node_details)
            print(f"🚧‼️ List response: {list_response}")
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
                # print(f"✨ 🔍 Fallback response: {fallback_response}")
                next_node_id = fallback_response.get("next_node_id", "")
                fallback_message = fallback_response.get("fallback_message", "")
                total_retry_count = fallback_response.get("retry_count", 0)
                retry_count += 1   # Increment the retry count by 1

        elif response_check_type == "quick_reply":
            quick_reply_response = quick_reply_type_node_logic(user_message=user_message, current_node=current_node_details, template_config=template_response_config)
            print(f"🪪‼️ Quick reply response: {quick_reply_response}")
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
                # print(f"🪪‼️ Fallback response: {fallback_response}")
                next_node_id = fallback_response.get("next_node_id", "")
                fallback_message = fallback_response.get("fallback_message", "")
                total_retry_count = fallback_response.get("retry_count", 0)
                retry_count += 1   # Increment the retry count by 1

        else:
            print(f"🚧‼️ Invalid metadata info ---->>")
            logger.error(f"Invalid response type found in template, please check and implement the logic for the same - Nodel Logic 1.2.1.1 - {response_check_type}")
            raise HTTPException(status_code=400, detail=f"Invalid response type found in template, please check and implement the logic for the same - Nodel Logic 1.2.1.1 - {response_check_type}")

        print(f"✨ 🔍 Response to user: {response_to_user}")
        print(f"✨ 🔍 Next node id: {next_node_id}")
        print(f"✨ 🔍 Retry count: {retry_count}")
        print(f"✨ 🔍 Node type: {node_type}")
        print(f"✨ 🔍 Node level: {node_level}")
        print(f"✨ 🔍 Fallback message: {fallback_message}")
        print(f"✨ 🔍 Fallback trigger: {fallback_trigger}")
       
       # Assign the fallback message to the response to user if no response to user is found
        if not response_to_user:
            response_to_user = fallback_message
        else:
            retry_count = int(0)
            fallback_trigger = False

        # breakpoint()
        # Save the response to the conversation history
        save_response = database_service.update_record(
            table_environment="whatsapp_campaigns",
            table_name="whatsapp_conversation_test",
            record_col_name="id",
            record_id=latest_conversation_id,
            update_data={
                "template_id": current_template_id,
                "template_name": template_response_config.get("app_name", ""),
                "current_node_id": next_node_id,   # Fix the current & next node thing
                "response_to_user": response_to_user,
                "fallback_trigger": fallback_trigger,
                "retry_count": retry_count,
                "node_level": node_level,
                "previous_message": previous_message
            }
        )
        logger.info(f"✅ Saved the response in conversation history")
        # print(f"✨ 🔍 Save response: {save_response}")

    else:
        node_details = get_node_details(id=nodes_data[0], data=template_response_config)
        node_type = node_details.get("type", "")
        metadata = node_details.get("metadata", {})
        content = node_details.get("content", "")


        # TODO: Change the logic for fallback response - add AI implemented fallback response
        if not whatsapp_conversation_history:
            # Send the current template along with the AI fallback response
            from app.api.endpoints.gupshup_apis import send_template_message, DemoTemplateMessageRequest
            requested = DemoTemplateMessageRequest(app_name=app_name, phone_number=data.get("phone", ""), template_id=current_template_id, template_params=['Delhi','Mumbai'], source_name="AI Fallback Response")
            print(f"✨ 🔍 Requested: {requested}")
            # template_response = await send_template_message(request=requested)
            template_response = ""
            print(f"✨ 🔍 Template response: {template_response}")
            response_to_user = template_response.message if hasattr(template_response, 'message') else "I'm sorry, I didn't understand your message. Please try again."

            fallback_trigger = True
            retry_count += 1

            print("CONTENT:", content)
            print("RESPONSE TO USER:", response_to_user)

            try:
                save_response = database_service.update_record(
                    table_environment="whatsapp_campaigns",
                    table_name="whatsapp_conversation_test",
                    record_col_name="id",
                    record_id=latest_conversation_id,
                    update_data={
                        "template_id": current_template_id,
                        "template_name": template_response_config.get("app_name", ""),
                        "current_node_id": nodes_data[0] if len(nodes_data) > 0 else "",  # Fix the current & next node thing
                        "response_to_user": response_to_user,
                        "fallback_trigger": fallback_trigger,
                        "retry_count": int(retry_count),
                        "node_level": int(template_response_config.get("response_config", {}).get("nodes", [])[0].get("level", "0")),
                    }
                )
                # print(f"✨ 🔍 Save response: {save_response}")
                logger.info(f"✅ Saved the response in conversation history")
            except Exception as e:
                logger.error(f"Error in saving response: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error in saving response: {str(e)}")

    # TODO: Implement the logic to send the response to the user
    print("-----------------------------------------------------------------------------------------------------------------")

    # TO use metadata we need to check the type, content first then move to metadata
    print("Type:-", node_type)
    print("Content:", response_to_user)  # Implement this later
    content = response_to_user
    print("Metadata:", metadata)

    from app.api.endpoints.gupshup_apis import send_message, MessageRequest
    if node_type == "text" and content != "":
        print("Sending text message to the user")
        requested = MessageRequest(app_name=app_name, phone_number=data.get("phone", ""), message={"type":"text", "text": content})
        print(f"✨ 🔍 Requested: {requested}")
        message_response = await send_message(request=requested)
        print(f"✨ 🔍 Message response: {message_response}")

    elif node_type == "list" and content != "":
        print("Sending list message to the user")
        list_message_data = generate_list_message_data(message_id=latest_conversation_id, content=content,metadata=metadata)
        requested = MessageRequest(app_name=app_name, phone_number=data.get("phone", ""), message=list_message_data)
        print(f"✨ 🔍 Requested: {requested}")
        message_response = await send_message(request=requested)
        print(f"✨ 🔍 Message response: {message_response}")
        

    elif node_type == "quick_reply" and content != "":
        print("Sending quick reply message to the user")
        quick_reply_message_data = generate_quick_reply_message_data(message_id=latest_conversation_id, content=content,metadata=metadata)
        requested = MessageRequest(app_name=app_name, phone_number=data.get("phone", ""), message=quick_reply_message_data)
        print(f"✨ 🔍 Requested: {requested}")
        message_response = await send_message(request=requested)
        print(f"✨ 🔍 Message response: {message_response}")
    else:
        print("Invalid node type")



##################################### Shift Upwards ######################################################
def generate_list_message_data(message_id, content, metadata):
    metadata_sections = metadata.get("sections", [])

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

    return {
        "type": "list", 
        "title": metadata.get("body", ""),
        "body": metadata.get("header", ""), 
        "footer": metadata.get("footer", ""), 
        "msgid": message_id, 
        "globalButtons": globalButtons, 
        "items": items
    }


def generate_quick_reply_message_data(message_id, content, metadata):
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
        "header":content,
        "text":"this is the body",
        "caption":"this is the footer"
    }
    return {
        "type":"quick_reply", 
        "msgid":message_id, 
        "content":content_data, 
        "options":options_list
    }