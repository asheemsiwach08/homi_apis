import httpx
import random
import json
from config import settings

class WhatsAppService:
    def __init__(self):
        self.api_url = settings.GUPSHUP_API_URL
        self.api_key = settings.GUPSHUP_API_KEY
        self.source = settings.GUPSHUP_SOURCE
        self.template_id = settings.GUPSHUP_TEMPLATE_ID
        self.src_name = settings.GUPSHUP_SRC_NAME
    
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
            'src.name': self.src_name,
            'template': f'{{"id":"{self.template_id}","params":["{otp}"]}}'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
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

whatsapp_service = WhatsAppService() 