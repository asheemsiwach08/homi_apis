#!/usr/bin/env python3
"""
Test script for HOM-i WhatsApp OTP, Lead Creation & Status API
Tests both OTP operations and Lead management endpoints
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
API_PREFIX = "/api_v1"

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_otp_operations():
    """Test OTP send, resend, and verify operations"""
    print("\n=== Testing OTP Operations ===")
    
    # Test phone numbers with different formats
    test_phone_numbers = [
        "917888888888",    # With country code
        "788888888",       # Without country code (will be normalized)
        "+917888888888",   # With + prefix
        "0788888888"       # With leading 0
    ]
    
    for phone in test_phone_numbers:
        print(f"\n--- Testing phone number: {phone} ---")
        
        # 1. Send OTP
        print("1. Sending OTP...")
        send_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/otp_send",
            json={"phone_number": phone}
        )
        print(f"   Status: {send_response.status_code}")
        
        if send_response.status_code == 200:
            send_data = send_response.json()
            print(f"   Response: {json.dumps(send_data, indent=2)}")
            
            # Extract OTP for verification
            otp = send_data.get("data", {}).get("otp")
            
            if otp:
                # 2. Verify OTP
                print("2. Verifying OTP...")
                verify_response = requests.post(
                    f"{BASE_URL}{API_PREFIX}/otp_verify",
                    json={"phone_number": phone, "otp": otp}
                )
                print(f"   Status: {verify_response.status_code}")
                print(f"   Response: {json.dumps(verify_response.json(), indent=2)}")
                
                # 3. Test resend OTP
                print("3. Resending OTP...")
                resend_response = requests.post(
                    f"{BASE_URL}{API_PREFIX}/otp_resend",
                    json={"phone_number": phone}
                )
                print(f"   Status: {resend_response.status_code}")
                print(f"   Response: {json.dumps(resend_response.json(), indent=2)}")
            else:
                print("   No OTP received in response")
        else:
            print(f"   Error: {send_response.text}")

def test_lead_operations():
    """Test lead creation and status operations"""
    print("\n=== Testing Lead Operations ===")
    
    # Test lead data
    lead_data = {
        "loan_type": "home_loan",
        "loan_amount": 5000000,
        "loan_tenure": 20,
        "pan_number": "ABCDE1234F",
        "first_name": "John",
        "last_name": "Doe",
        "gender": "Male",
        "mobile_number": "788888888",
        "email": "john.doe@example.com",
        "dob": "15/06/1990",
        "pin_code": "400001"
    }
    
    # 1. Create Lead
    print("1. Creating Lead...")
    create_response = requests.post(
        f"{BASE_URL}{API_PREFIX}/lead_create",
        json=lead_data
    )
    print(f"   Status: {create_response.status_code}")
    
    if create_response.status_code == 200:
        create_data = create_response.json()
        print(f"   Response: {json.dumps(create_data, indent=2)}")
        
        # Extract basic application ID
        basic_application_id = create_data.get("basic_application_id")
        
        if basic_application_id:
            # 2. Get Lead Status by mobile number
            print("2. Getting Lead Status by mobile number...")
            status_response = requests.post(
                f"{BASE_URL}{API_PREFIX}/lead_status",
                json={"mobile_number": lead_data["mobile_number"]}
            )
            print(f"   Status: {status_response.status_code}")
            print(f"   Response: {json.dumps(status_response.json(), indent=2)}")
            
            # 3. Get Lead Status by basic application ID
            print("3. Getting Lead Status by basic application ID...")
            status_response2 = requests.post(
                f"{BASE_URL}{API_PREFIX}/lead_status",
                json={"basic_application_id": basic_application_id}
            )
            print(f"   Status: {status_response2.status_code}")
            print(f"   Response: {json.dumps(status_response2.json(), indent=2)}")
        else:
            print("   No basic application ID received")
    else:
        print(f"   Error: {create_response.text}")

def test_error_scenarios():
    """Test various error scenarios"""
    print("\n=== Testing Error Scenarios ===")
    
    # 1. Test invalid phone number
    print("1. Testing invalid phone number...")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/otp_send",
        json={"phone_number": "123"}  # Invalid phone number
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # 2. Test invalid OTP
    print("2. Testing invalid OTP...")
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/otp_verify",
        json={"phone_number": "788888888", "otp": "999999"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    # 3. Test invalid lead data
    print("3. Testing invalid lead data...")
    invalid_lead_data = {
        "loan_type": "invalid_loan_type",
        "loan_amount": -1000,  # Invalid amount
        "loan_tenure": 0,      # Invalid tenure
        "pan_number": "INVALID",  # Invalid PAN
        "first_name": "John",
        "last_name": "Doe",
        "mobile_number": "123",  # Invalid mobile
        "email": "invalid-email",  # Invalid email
        "dob": "invalid-date",
        "pin_code": "123"  # Invalid PIN
    }
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/lead_create",
        json=invalid_lead_data
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")

def test_phone_number_normalization():
    """Test phone number normalization with various formats"""
    print("\n=== Testing Phone Number Normalization ===")
    
    test_cases = [
        "917888888888",    # Already has country code
        "788888888",       # Without country code
        "+917888888888",   # With + prefix
        "0788888888",      # With leading 0
        "888888888",       # 9 digits
        "88888888",        # 8 digits
        "91 788 888 8888", # With spaces
        "91-788-888-8888"  # With dashes
    ]
    
    for phone in test_cases:
        print(f"\nTesting: {phone}")
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/otp_send",
            json={"phone_number": phone}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Success: OTP sent successfully")
        else:
            print(f"   Error: {response.text}")

def main():
    """Run all tests"""
    print("🚀 Starting HOM-i API Tests")
    print("=" * 50)
    
    # Test health check first
    if not test_health_check():
        print("❌ Health check failed. Make sure the API is running.")
        return
    
    # Run all test suites
    test_otp_operations()
    test_lead_operations()
    test_error_scenarios()
    test_phone_number_normalization()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    main() 