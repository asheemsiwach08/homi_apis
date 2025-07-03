#!/usr/bin/env python3
"""
Simple test script to demonstrate the WhatsApp OTP API functionality.
This script shows how to use the API endpoints with example requests.
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ Health check passed\n")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False

def test_phone_normalization():
    """Test phone number normalization"""
    print("📞 Testing phone number normalization...")
    try:
        response = requests.get(f"{BASE_URL}/debug/phone-normalization")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Phone normalization test passed\n")
            return True
        else:
            print("❌ Phone normalization test failed\n")
            return False
    except Exception as e:
        print(f"❌ Phone normalization test failed: {e}\n")
        return False

def test_send_otp(phone_number):
    """Test sending OTP"""
    print(f"📱 Testing send OTP to {phone_number}...")
    try:
        response = requests.post(
            f"{BASE_URL}/otp/send",
            json={"phone_number": phone_number}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Send OTP test passed\n")
            return True
        else:
            print("❌ Send OTP test failed\n")
            return False
    except Exception as e:
        print(f"❌ Send OTP test failed: {e}\n")
        return False

def test_resend_otp(phone_number):
    """Test resending OTP"""
    print(f"🔄 Testing resend OTP to {phone_number}...")
    try:
        response = requests.post(
            f"{BASE_URL}/otp/resend",
            json={"phone_number": phone_number}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Resend OTP test passed\n")
            return True
        else:
            print("❌ Resend OTP test failed\n")
            return False
    except Exception as e:
        print(f"❌ Resend OTP test failed: {e}\n")
        return False

def test_verify_otp(phone_number, otp):
    """Test verifying OTP"""
    print(f"🔐 Testing verify OTP for {phone_number} with OTP: {otp}...")
    try:
        response = requests.post(
            f"{BASE_URL}/otp/verify",
            json={"phone_number": phone_number, "otp": otp}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Verify OTP test passed\n")
            return True
        else:
            print("❌ Verify OTP test failed\n")
            return False
    except Exception as e:
        print(f"❌ Verify OTP test failed: {e}\n")
        return False

def test_invalid_phone_number():
    """Test with invalid phone number"""
    print("🚫 Testing with invalid phone number...")
    try:
        response = requests.post(
            f"{BASE_URL}/otp/send",
            json={"phone_number": "invalid_phone"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✅ Invalid phone number test passed (expected error)\n")
            return True
        else:
            print("❌ Invalid phone number test failed\n")
            return False
    except Exception as e:
        print(f"❌ Invalid phone number test failed: {e}\n")
        return False

def main():
    """Main test function"""
    print("🚀 Starting WhatsApp OTP API Tests\n")
    print("=" * 50)
    
    # Test phone numbers with different formats
    test_phones = [
        "917888888888",  # Already has country code
        "788888888",     # Without country code
        "+917888888888", # With + prefix
        "0788888888",    # With leading 0
    ]
    
    # Run tests
    tests = [
        ("Health Check", lambda: test_health_check()),
        ("Phone Number Normalization", lambda: test_phone_normalization()),
        ("Invalid Phone Number", lambda: test_invalid_phone_number()),
    ]
    
    # Add tests for each phone number format
    for phone in test_phones:
        tests.append((f"Send OTP ({phone})", lambda p=phone: test_send_otp(p)))
    
    tests.extend([
        ("Resend OTP", lambda: test_resend_otp(test_phones[0])),
        ("Verify OTP (with dummy OTP)", lambda: test_verify_otp(test_phones[0], "123456")),
    ])
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 Running: {test_name}")
        if test_func():
            passed += 1
        print("-" * 30)
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    print("\n💡 Note: For actual OTP testing, replace the test phone numbers with real ones.")
    print("💡 The verify OTP test uses a dummy OTP and will fail unless you use the actual OTP sent.")
    print("\n🔗 New API Endpoints:")
    print("   - POST /otp/send")
    print("   - POST /otp/resend") 
    print("   - POST /otp/verify")
    print("   - GET /health")
    print("   - GET /debug/phone-normalization")

if __name__ == "__main__":
    main() 