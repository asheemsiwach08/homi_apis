import httpx
import json
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    # Get API credentials from environment variables (with fallback to hardcoded for testing)
    api_key = os.getenv("GUPSHUP_API_KEY", "")
    source = os.getenv("GUPSHUP_SOURCE", "")
    
    print(f"🔑 Using API Key: {api_key[:10]}...")
    print(f"📱 Using Source: {source}")
    print(f"📱 Destination: 917988362283")
    
    message = {"type": "text", "text": "Hello, how are you?"} 
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.gupshup.io/wa/api/v1/msg",
                headers={
                    'Cache-Control': 'no-cache',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'apikey': api_key,
                    'cache-control': 'no-cache'
                },
                data={
                    'channel': 'whatsapp',
                    'source': source,
                    'destination': '91',
                    'message': json.dumps(message)
                },
                timeout=30.0
            )
            
            print(f"📡 Response Status: {response.status_code}")
            print(f"📄 Response Text: {response.text}")
            
            if response.status_code == 202:
                print("✅ Message sent successfully!")
            elif response.status_code == 401:
                print("❌ Authentication Failed - Check your API key")
            elif response.status_code == 400:
                print("❌ Bad Request - Check your source number or message format")
            else:
                print(f"❌ Request failed with status: {response.status_code}")
                
            # Try to parse JSON response for more details
            try:
                response_json = response.json()
                print(f"📋 Response JSON: {json.dumps(response_json, indent=2)}")
            except:
                print("📋 Response is not valid JSON")
                
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
