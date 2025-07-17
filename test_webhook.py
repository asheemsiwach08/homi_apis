#!/usr/bin/env python3
"""
Test script for WhatsApp Webhook
This script simulates webhook calls to test the functionality
"""

import requests
import json

# API base URL (adjust as needed)
BASE_URL = "http://localhost:5000"

def test_webhook():
    """Test the WhatsApp webhook endpoint"""
    
    print("Testing WhatsApp Webhook")
    print("=" * 40)
    
    # Test cases
    test_cases = [
        {
            "name": "Status check request",
            "data": {
                "payload": "test_payload",
                "mobile": "+919876543210",
                "message": "Check my application status",
                "channel": "whatsapp",
                "timestamp": "1234567890"
            }
        },
        {
            "name": "Non-status message",
            "data": {
                "payload": "test_payload",
                "mobile": "+919876543210",
                "message": "Hello, how are you?",
                "channel": "whatsapp",
                "timestamp": "1234567890"
            }
        },
        {
            "name": "Status check with different format",
            "data": {
                "payload": "test_payload",
                "mobile": "+919876543210",
                "message": "I want to check my loan status",
                "channel": "whatsapp",
                "timestamp": "1234567890"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{BASE_URL}/api_v1/whatsapp/webhook",
                data=test_case["data"],
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the API server.")
            print("Make sure the server is running on http://localhost:5000")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def test_manual_processing():
    """Test the manual WhatsApp message processing endpoint"""
    
    print("\n" + "=" * 40)
    print("Testing Manual WhatsApp Processing")
    print("=" * 40)
    
    test_cases = [
        {
            "name": "Status check with phone number",
            "data": {
                "message": "Check my application status. My mobile number is 9876543210"
            }
        },
        {
            "name": "Simple status check",
            "data": {
                "message": "I want to check my application status"
            }
        }
    ]
    
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
            print("Make sure the server is running on http://localhost:5000")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def test_lead_status():
    """Test the lead status endpoint"""
    
    print("\n" + "=" * 40)
    print("Testing Lead Status Endpoint")
    print("=" * 40)
    
    test_cases = [
        {
            "name": "Status check by mobile number",
            "data": {
                "mobile_number": "9876543210"
            }
        },
        {
            "name": "Status check by application ID",
            "data": {
                "basic_application_id": "APP123456"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{BASE_URL}/api_v1/lead_status",
                json=test_case["data"],
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        except requests.exceptions.ConnectionError:
            print("Error: Could not connect to the API server.")
            print("Make sure the server is running on http://localhost:5000")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Run all tests
    test_webhook()
    test_manual_processing()
    test_lead_status()
    
    print("\n" + "=" * 40)
    print("Test Summary")
    print("=" * 40)
    print("✅ Webhook tests completed")
    print("✅ Manual processing tests completed")
    print("✅ Lead status tests completed")
    print("\nCheck the responses above to verify functionality.") 