#!/usr/bin/env python3
"""
Test script for WhatsApp Message Processing API
This script demonstrates how to use the new WhatsApp message processing endpoint
"""

import requests
import json

# API base URL (adjust as needed)
BASE_URL = "http://localhost:8000"

def test_whatsapp_message_processing():
    """Test the WhatsApp message processing endpoint"""
    
    # Test cases with different message formats
    test_cases = [
        {
            "name": "Status check with phone number in message",
            "data": {
                "message": "I want to check my application status. My mobile number is 9876543210"
            }
        },
        {
            "name": "Status check with application ID",
            "data": {
                "message": "Please check my application status. Application ID: APP123456. My mobile is 9876543210"
            }
        },
        {
            "name": "Status check with different phone format",
            "data": {
                "message": "Check my loan status. Mobile: 987-654-3210"
            }
        },
        {
            "name": "Status check with phone number only",
            "data": {
                "message": "Check my application status for mobile 9876543210"
            }
        },
        {
            "name": "Status check without phone number",
            "data": {
                "message": "i want to check my application status"
            }
        },
        {
            "name": "Non-status check message",
            "data": {
                "message": "Hello, how are you?"
            }
        }
    ]
    
    print("Testing WhatsApp Message Processing API")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{BASE_URL}/api_v1/whatsapp/process_message",
                json=test_case["data"],
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the API server.")
            print("Make sure the server is running on http://localhost:8000")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def test_whatsapp_message_processing_curl():
    """Generate curl commands for testing"""
    
    print("\n" + "=" * 50)
    print("CURL COMMANDS FOR TESTING")
    print("=" * 50)
    
    curl_commands = [
        {
            "name": "Status check with phone number",
            "command": '''curl -X POST "http://localhost:8000/api_v1/whatsapp/process_message" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "I want to check my application status. My mobile number is 9876543210",
    "phone_number": "+919876543210"
  }' '''
        },
        {
            "name": "Status check with application ID",
            "command": '''curl -X POST "http://localhost:8000/api_v1/whatsapp/process_message" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Please check my application status. Application ID: APP123456",
    "phone_number": "+919876543210"
  }' '''
        },
        {
            "name": "Simple status check",
            "command": '''curl -X POST "http://localhost:8000/api_v1/whatsapp/process_message" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "i want to check my application status",
    "phone_number": "+919876543210"
  }' '''
        }
    ]
    
    for i, curl_test in enumerate(curl_commands, 1):
        print(f"\n{i}. {curl_test['name']}:")
        print(curl_test['command'])

if __name__ == "__main__":
    # Run the tests
    test_whatsapp_message_processing()
    
    # Show curl commands
    test_whatsapp_message_processing_curl() 