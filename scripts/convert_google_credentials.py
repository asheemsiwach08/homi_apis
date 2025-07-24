#!/usr/bin/env python3
"""
Utility script to convert Google Sheets credentials JSON file to environment variables.
This helps secure credentials for GitHub deployment.
"""

import json
import base64
import sys
import os

def convert_json_to_env_vars(json_file_path):
    """Convert Google credentials JSON file to environment variables format."""
    
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            creds_data = json.load(f)
        
        print("=" * 60)
        print("GOOGLE CREDENTIALS CONVERSION")
        print("=" * 60)
        
        # Option 1: Base64 encoded JSON (Recommended)
        json_str = json.dumps(creds_data)
        encoded_json = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        print("\n🔐 OPTION 1: Base64 Encoded JSON (Recommended for production)")
        print("-" * 60)
        print(f"GOOGLE_CREDENTIALS_JSON={encoded_json}")
        
        # Option 2: Individual environment variables
        print("\n🔧 OPTION 2: Individual Environment Variables")
        print("-" * 60)
        
        field_mapping = {
            'type': 'GOOGLE_CREDENTIALS_TYPE',
            'project_id': 'GOOGLE_CREDENTIALS_PROJECT_ID',
            'private_key_id': 'GOOGLE_CREDENTIALS_PRIVATE_KEY_ID',
            'private_key': 'GOOGLE_CREDENTIALS_PRIVATE_KEY',
            'client_email': 'GOOGLE_CREDENTIALS_CLIENT_EMAIL',
            'client_id': 'GOOGLE_CREDENTIALS_CLIENT_ID',
            'auth_uri': 'GOOGLE_CREDENTIALS_AUTH_URI',
            'token_uri': 'GOOGLE_CREDENTIALS_TOKEN_URI',
            'auth_provider_x509_cert_url': 'GOOGLE_CREDENTIALS_AUTH_PROVIDER_X509_CERT_URL',
            'client_x509_cert_url': 'GOOGLE_CREDENTIALS_CLIENT_X509_CERT_URL'
        }
        
        for json_key, env_var in field_mapping.items():
            value = creds_data.get(json_key, '')
            if value:
                # Handle private key formatting
                if json_key == 'private_key':
                    # Escape newlines for environment variable storage
                    escaped_value = value.replace('\n', '\\n')
                    print(f'{env_var}="{escaped_value}"')
                else:
                    print(f"{env_var}={value}")
        
        # Option 3: Plain JSON (Alternative)
        print("\n📄 OPTION 3: Plain JSON (Alternative)")
        print("-" * 60)
        print(f"GOOGLE_CREDENTIALS_JSON_PLAIN='{json_str}'")
        
        print("\n" + "=" * 60)
        print("VALIDATION CHECK")
        print("=" * 60)
        
        # Validate the JSON structure
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
        missing_fields = [field for field in required_fields if not creds_data.get(field)]
        
        if missing_fields:
            print(f"⚠️  WARNING: Missing required fields: {missing_fields}")
        else:
            print("✅ All required fields are present")
        
        # Check private key format
        private_key = creds_data.get('private_key', '')
        if private_key:
            if private_key.startswith('-----BEGIN PRIVATE KEY-----') and private_key.endswith('-----END PRIVATE KEY-----'):
                print("✅ Private key format looks correct")
            else:
                print("⚠️  WARNING: Private key format may be incorrect")
        
        print("\n" + "=" * 60)
        print("DEPLOYMENT INSTRUCTIONS")
        print("=" * 60)
        print("1. Choose ONE of the options above")
        print("2. Add the environment variables to your .env file")
        print("3. For GitHub Actions, add them as repository secrets")
        print("4. For production deployment, use Option 1 (Base64)")
        print("5. Never commit the original JSON file to GitHub")
        print("6. Add the JSON file to .gitignore")
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("- If using Option 2, ensure private key has proper \\n escaping")
        print("- Test with Option 1 (Base64) first - it's more reliable")
        print("- Check that service account has access to your Google Sheets")
        print("- Verify all environment variables are set correctly")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file_path}' not found")
        return False
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in file '{json_file_path}'")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_google_credentials.py <path_to_credentials.json>")
        print("Example: python convert_google_credentials.py ./credentials/service-account.json")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    if not os.path.exists(json_file_path):
        print(f"❌ Error: File '{json_file_path}' does not exist")
        sys.exit(1)
    
    success = convert_json_to_env_vars(json_file_path)
    
    if success:
        print("\n✅ Conversion completed successfully!")
        print("Copy the environment variables to your .env file")
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1) 