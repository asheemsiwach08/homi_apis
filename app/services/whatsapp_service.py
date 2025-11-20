import json
import httpx
import random
from fastapi import HTTPException
from app.config.settings import settings

class WhatsAppService:
    """Service for handling WhatsApp message sending using Gupshup API with different templates"""
    
    def __init__(self):
        self.api_template_url = settings.GUPSHUP_API_TEMPLATE_URL
        self.api_msg_url = settings.GUPSHUP_API_MSG_URL
        self.api_key = settings.GUPSHUP_API_KEY
        self.source = settings.GUPSHUP_SOURCE

        # Template configurations
        self.whatsapp_otp_template_id = settings.GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID
        self.lead_creation_template_id = settings.GUPSHUP_LEAD_CREATION_TEMPLATE_ID
        self.lead_status_template_id = settings.GUPSHUP_LEAD_STATUS_TEMPLATE_ID

        self.whatsapp_otp_src_name = settings.GUPSHUP_WHATSAPP_OTP_SRC_NAME
        self.lead_creation_src_name = settings.GUPSHUP_LEAD_CREATION_SRC_NAME
        self.lead_status_src_name = settings.GUPSHUP_LEAD_STATUS_SRC_NAME

    def validate_app_config(self, app_name: str) -> dict:
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


    def generate_otp(self) -> str:
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))

    async def send_otp(self, phone_number: str, otp: str) -> dict:
        """Send OTP via WhatsApp using Gupshup API"""
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apikey': self.api_key,
            'cache-control': 'no-cache'
        }
        
        data = {
            'channel': 'whatsapp',
            'source': self.source,
            'destination': phone_number,
            'src.name': self.whatsapp_otp_src_name,
            'template': f'{{"id":"{self.whatsapp_otp_template_id}","params":["{otp}"]}}'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_template_url,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                # Gupshup API returns 202 for successful submissions (accepted for processing)
                if response.status_code in [200, 202]:
                    try:
                        # Try to parse JSON response
                        response_data = response.json()
                        # Ensure response_data is a dictionary
                        if isinstance(response_data, dict):
                            data_dict = response_data
                        else:
                            data_dict = {"response": str(response_data)}
                    except json.JSONDecodeError:
                        # If JSON parsing fails, use text response
                        data_dict = {"response": response.text}
                    
                    return {
                        "success": True,
                        "message": "OTP sent successfully",
                        "data": data_dict
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to send OTP. Status: {response.status_code}",
                        "data": {"error": response.text}
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Error sending OTP: {str(e)}",
                "data": {"error": str(e)}
            }

    
    async def send_lead_creation_confirmation(self, customer_name: str, loan_type: str, basic_application_id: str, phone_number: str) -> dict:
        """
        Send lead creation confirmation message using Gupshup template
        
        Args:
            customer_name: Customer's full name
            loan_type: Type of loan
            basic_application_id: Generated basic application ID
            phone_number: Customer's phone number
            
        Returns:
            dict: Response with success status and message
        """
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apikey': self.api_key,
            'cache-control': 'no-cache'
        }
        
        # Template parameters for lead creation
        template_params = [
            customer_name,
            # loan_type,
            basic_application_id
        ]
        
        data = {
            'channel': 'whatsapp',
            'source': self.source,
            'destination': phone_number,
            'src.name': self.lead_creation_src_name,
            'template': f'{{"id":"{self.lead_creation_template_id}","params":{json.dumps(template_params)}}}'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_template_url,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                # Gupshup API returns 202 for successful submissions
                if response.status_code in [200, 202]:
                    try:
                        response_data = response.json()
                        data_dict = response_data if isinstance(response_data, dict) else {"response": str(response_data)}
                    except json.JSONDecodeError:
                        data_dict = {"response": response.text}
                    
                    return {
                        "success": True,
                        "message": "Lead creation confirmation sent successfully",
                        "data": data_dict
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to send lead creation confirmation. Status: {response.status_code}",
                        "data": {"error": response.text}
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Error sending lead creation confirmation: {str(e)}",
                "data": {"error": str(e)}
            }
    
    async def send_lead_status_update(self, phone_number: str, name: str, status: str) -> dict:
        """
        Send lead status update message using Gupshup template
        
        Args:
            phone_number: Customer's phone number
            name: Customer's full name
            status: Current lead status
            
        Returns:
            dict: Response with success status and message
        """
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apikey': self.api_key,
            'cache-control': 'no-cache'
        }
        
        # Template parameters for lead status
        template_params = [name, status]
        
        data = {
            'channel': 'whatsapp',
            'source': self.source,
            'destination': phone_number,
            'src.name': self.lead_status_src_name,
            'template': f'{{"id":"{self.lead_status_template_id}","params":{json.dumps(template_params)}}}'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_template_url,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                # Gupshup API returns 202 for successful submissions
                if response.status_code in [200, 202]:
                    try:
                        response_data = response.json()
                        data_dict = response_data if isinstance(response_data, dict) else {"response": str(response_data)}
                    except json.JSONDecodeError:
                        data_dict = {"response": response.text}
                    
                    return {
                        "success": True,
                        "message": "Lead status update sent successfully",
                        "data": data_dict
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to send lead status update. Status: {response.status_code}",
                        "data": {"error": response.text}
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Error sending lead status update: {str(e)}",
                "data": {"error": str(e)}
            }

    async def send_message(self, phone_number: str, message: str) -> dict:
        """
        Send a simple text message via WhatsApp using Gupshup API
        
        Args:
            phone_number: Customer's phone number
            message: Text message to send
            
        Returns:
            dict: Response with success status and message
        """
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apikey': self.api_key,
            'cache-control': 'no-cache'
        }
        
        data = {
            'channel': 'whatsapp',
            'source': self.source,
            'destination': phone_number,
            'message': message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_msg_url,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                # Gupshup API returns 202 for successful submissions
                if response.status_code in [200, 202]:
                    try:
                        response_data = response.json()
                        data_dict = response_data if isinstance(response_data, dict) else {"response": str(response_data)}
                    except json.JSONDecodeError:
                        data_dict = {"response": response.text}
                    
                    return {
                        "success": True,
                        "message": "Message sent successfully",
                        "data": data_dict
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to send message. Status: {response.status_code}",
                        "data": {"error": response.text}
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Error sending message: {str(e)}",
                "data": {"error": str(e)}
            }

    async def send_message_with_app_config(self, phone_number: str, message: str, app_name: str) -> dict:
        """
        Send a simple text message via WhatsApp using Gupshup API
        
        Args:
            phone_number: Customer's phone number
            message: Text message to send
            app_name: Name of the app
        Returns:
            dict: Response with success status and message
        """
        app_config = self.validate_app_config(app_name)

        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'apikey': app_config["api_key"],
            'cache-control': 'no-cache'
        }
        
        message ={"type":"text", "text": message} 

        data = {
            'channel': 'whatsapp',
            'source': app_config["source"],
            'src.name': app_config["app_name"],
            'destination': phone_number,
            'message': json.dumps(message)
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_msg_url,
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                # Gupshup API returns 202 for successful submissions
                if response.status_code in [200, 202]:
                    try:
                        response_data = response.json()
                        data_dict = response_data if isinstance(response_data, dict) else {"response": str(response_data)}
                    except json.JSONDecodeError:
                        data_dict = {"response": response.text}
                    
                    return {
                        "success": True,
                        "message": "Message sent successfully",
                        "data": data_dict
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Failed to send message. Status: {response.status_code}",
                        "data": {"error": response.text}
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Error sending message: {str(e)}",
                "data": {"error": str(e)}
            }

# Global instance
whatsapp_service = WhatsAppService() 