#!/usr/bin/env python3
"""
Test script to validate Google Sheets credentials from environment variables.
"""

import os
import json
import base64
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

def test_credentials():
    """Test different credential loading methods."""
    
    print("🔍 GOOGLE CREDENTIALS TEST")
    print("=" * 50)
    
    # Test Method 1: Base64 encoded JSON
    print("\n1️⃣ Testing Base64 encoded JSON...")
    google_creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if google_creds_json:
        try:
            creds_data = json.loads(base64.b64decode(google_creds_json).decode('utf-8'))
            print(f"✅ Base64 decoded successfully")
            print(f"   Project ID: {creds_data.get('project_id')}")
            print(f"   Client Email: {creds_data.get('client_email')}")
            
            # Test creating credentials
            credentials = ServiceAccountCredentials.from_service_account_info(
                creds_data, 
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            print("✅ Credentials created successfully from base64 JSON")
            return True
            
        except Exception as e:
            print(f"❌ Base64 method failed: {e}")
    else:
        print("⚠️  GOOGLE_CREDENTIALS_JSON not set")
    
    # Test Method 2: Individual environment variables
    print("\n2️⃣ Testing individual environment variables...")
    
    required_vars = [
        'GOOGLE_CREDENTIALS_TYPE',
        'GOOGLE_CREDENTIALS_PROJECT_ID',
        'GOOGLE_CREDENTIALS_PRIVATE_KEY_ID',
        'GOOGLE_CREDENTIALS_PRIVATE_KEY',
        'GOOGLE_CREDENTIALS_CLIENT_EMAIL',
        'GOOGLE_CREDENTIALS_CLIENT_ID'
    ]
    
    # Check if all required vars are set
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        return False
    
    print("✅ All required environment variables are set")
    
    # Get and process private key
    private_key = os.getenv('GOOGLE_CREDENTIALS_PRIVATE_KEY')
    if private_key:
        print(f"   Private key length: {len(private_key)}")
        print(f"   Starts with: {private_key[:30]}...")
        print(f"   Ends with: ...{private_key[-30:]}")
        
        # Fix formatting
        private_key = private_key.strip('"\'')
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
            print("   Fixed \\n escaping")
        
        # Remove trailing whitespace
        private_key = private_key.rstrip()
        print(f"   After cleanup - Ends with: ...{private_key[-30:]}")
        
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Private key doesn't start with proper header")
            return False
        if not private_key.endswith('-----END PRIVATE KEY-----'):
            print(f"❌ Private key doesn't end with proper footer")
            print(f"   Actually ends with: '{private_key[-50:]}'")
            # Try to fix it
            if '-----END PRIVATE KEY-----' in private_key:
                end_index = private_key.rfind('-----END PRIVATE KEY-----') + len('-----END PRIVATE KEY-----')
                private_key = private_key[:end_index]
                print("   🔧 Fixed private key ending")
            else:
                return False
        
        print("✅ Private key format looks correct")
    
    # Create credentials object
    google_creds = {
        'type': os.getenv('GOOGLE_CREDENTIALS_TYPE'),
        'project_id': os.getenv('GOOGLE_CREDENTIALS_PROJECT_ID'),
        'private_key_id': os.getenv('GOOGLE_CREDENTIALS_PRIVATE_KEY_ID'),
        'private_key': private_key,
        'client_email': os.getenv('GOOGLE_CREDENTIALS_CLIENT_EMAIL'),
        'client_id': os.getenv('GOOGLE_CREDENTIALS_CLIENT_ID'),
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs'
    }
    
    print(f"   Project ID: {google_creds['project_id']}")
    print(f"   Client Email: {google_creds['client_email']}")
    
    try:
        credentials = ServiceAccountCredentials.from_service_account_info(
            google_creds,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        print("✅ Credentials created successfully from individual variables")
        return True
        
    except Exception as e:
        print(f"❌ Individual variables method failed: {e}")
        return False

def test_sheets_access():
    """Test actual Google Sheets access."""
    print("\n3️⃣ Testing Google Sheets access...")
    
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    if not spreadsheet_id:
        print("⚠️  GOOGLE_SPREADSHEET_ID not set, skipping sheets test")
        return
    
    try:
        from googleapiclient.discovery import build
        
        # Try to get credentials using the same logic as the main app
        credentials = None
        
        # Try base64 first
        google_creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if google_creds_json:
            try:
                creds_data = json.loads(base64.b64decode(google_creds_json).decode('utf-8'))
                credentials = ServiceAccountCredentials.from_service_account_info(
                    creds_data,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                print("   Using base64 credentials for sheets test")
            except Exception as e:
                print(f"   Base64 credentials failed: {e}")
        
        # If base64 failed, try individual variables
        if not credentials:
            print("   Trying individual environment variables...")
            private_key = os.getenv('GOOGLE_CREDENTIALS_PRIVATE_KEY')
            if private_key:
                private_key = private_key.strip('"\'')
                if '\\n' in private_key:
                    private_key = private_key.replace('\\n', '\n')
                private_key = private_key.rstrip()
                
                google_creds = {
                    'type': os.getenv('GOOGLE_CREDENTIALS_TYPE'),
                    'project_id': os.getenv('GOOGLE_CREDENTIALS_PROJECT_ID'),
                    'private_key_id': os.getenv('GOOGLE_CREDENTIALS_PRIVATE_KEY_ID'),
                    'private_key': private_key,
                    'client_email': os.getenv('GOOGLE_CREDENTIALS_CLIENT_EMAIL'),
                    'client_id': os.getenv('GOOGLE_CREDENTIALS_CLIENT_ID'),
                    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                    'token_uri': 'https://oauth2.googleapis.com/token',
                    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs'
                }
                
                credentials = ServiceAccountCredentials.from_service_account_info(
                    google_creds,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                print("   Using individual variable credentials for sheets test")
        
        if not credentials:
            print("❌ Could not create credentials")
            return
        
        # Build the service
        service = build('sheets', 'v4', credentials=credentials)
        
        # Try to access the spreadsheet
        sheet = service.spreadsheets()
        result = sheet.get(spreadsheetId=spreadsheet_id).execute()
        
        print(f"✅ Successfully accessed spreadsheet: {result.get('properties', {}).get('title', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"❌ Sheets access failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Google Credentials Test...\n")
    
    success = test_credentials()
    
    if success:
        test_sheets_access()
        print("\n🎉 Credentials test completed successfully!")
    else:
        print("\n❌ Credentials test failed!")
        print("\n💡 Troubleshooting suggestions:")
        print("1. Run the conversion script: python scripts/convert_google_credentials.py your-file.json")
        print("2. Use Option 1 (Base64) as it's more reliable")
        print("3. Check that all environment variables are set correctly")
        print("4. Verify the private key format in your JSON file") 