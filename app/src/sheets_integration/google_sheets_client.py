"""
Google Sheets client for appending bank application data.
"""

import os
import json
from typing import List, Dict, Any
import logging
from datetime import datetime, timezone, timedelta
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config.config import config
from app.utils.timezone_utils import get_ist_timestamp_formatted

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """Client for appending bank application data to Google Sheets."""
    
    def __init__(self):
        """Initialize Google Sheets client."""
        self.sheets_config = config.get_sheets_config()
        self.credentials_file = self.sheets_config['credentials_file']
        self.spreadsheet_id = self.sheets_config['spreadsheet_id']
        self.range_name = self.sheets_config['range']
        self.service = None
        
        # Debug logging
        # logger.info(f"Google Sheets Client initialized with:")
        # logger.info(f"  Credentials file: {self.credentials_file}")
        # logger.info(f"  Spreadsheet ID: {self.spreadsheet_id}")
        # logger.info(f"  Range: {self.range_name}")
        
    def authenticate(self) -> bool:
        """Authenticate with Google Sheets API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Define the scope
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            
            credentials = None
            
            # Option 1: Try environment variable with base64 encoded JSON
            google_creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if google_creds_json:
                try:
                    import base64
                    # Decode base64 encoded JSON
                    creds_data = json.loads(base64.b64decode(google_creds_json).decode('utf-8'))
                    # logger.info("Using Google credentials from environment variable (base64)")
                    credentials = ServiceAccountCredentials.from_service_account_info(
                        creds_data, 
                        scopes=scope
                    )
                except Exception as e:
                    logger.error(f"Failed to parse base64 Google credentials: {e}")
            
            # Option 2: Try environment variable with plain JSON
            if not credentials:
                google_creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON_PLAIN')
                if google_creds_json:
                    try:
                        creds_data = json.loads(google_creds_json)
                        logger.info("Using Google credentials from environment variable (plain JSON)")
                        credentials = ServiceAccountCredentials.from_service_account_info(
                            creds_data, 
                            scopes=scope
                        )
                    except Exception as e:
                        logger.error(f"Failed to parse plain JSON Google credentials: {e}")
            
            # Option 3: Try individual environment variables
            if not credentials:
                private_key = os.getenv('GOOGLE_CREDENTIALS_PRIVATE_KEY')
                
                # Fix private key formatting if needed
                if private_key:
                    # Remove quotes if present
                    private_key = private_key.strip('"\'')
                    # Fix newline formatting
                    if '\\n' in private_key:
                        private_key = private_key.replace('\\n', '\n')
                    # Remove any trailing whitespace/newlines that might interfere
                    private_key = private_key.rstrip()
                    # Ensure proper BEGIN/END format
                    if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                        logger.error("Private key does not start with proper header")
                    if not private_key.endswith('-----END PRIVATE KEY-----'):
                        logger.error(f"Private key does not end with proper footer. Ends with: '{private_key[-50:]}'")
                        # Try to fix it by removing trailing characters
                        if '-----END PRIVATE KEY-----' in private_key:
                            end_index = private_key.rfind('-----END PRIVATE KEY-----') + len('-----END PRIVATE KEY-----')
                            private_key = private_key[:end_index]
                            logger.info("Fixed private key ending")
                
                google_creds = {
                    'type': os.getenv('GOOGLE_CREDENTIALS_TYPE'),
                    'project_id': os.getenv('GOOGLE_CREDENTIALS_PROJECT_ID'),
                    'private_key_id': os.getenv('GOOGLE_CREDENTIALS_PRIVATE_KEY_ID'),
                    'private_key': private_key,
                    'client_email': os.getenv('GOOGLE_CREDENTIALS_CLIENT_EMAIL'),
                    'client_id': os.getenv('GOOGLE_CREDENTIALS_CLIENT_ID'),
                    'auth_uri': os.getenv('GOOGLE_CREDENTIALS_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
                    'token_uri': os.getenv('GOOGLE_CREDENTIALS_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
                    'auth_provider_x509_cert_url': os.getenv('GOOGLE_CREDENTIALS_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
                    'client_x509_cert_url': os.getenv('GOOGLE_CREDENTIALS_CLIENT_X509_CERT_URL')
                }
                
                # Check if all required fields are present
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
                if all(google_creds.get(field) for field in required_fields):
                    try:
                        # logger.info("Using Google credentials from individual environment variables")
                        logger.debug(f"Private key starts with: {private_key[:50] if private_key else 'None'}...")
                        credentials = ServiceAccountCredentials.from_service_account_info(
                            google_creds, 
                            scopes=scope
                        )
                    except Exception as e:
                        logger.error(f"Failed to create credentials from environment variables: {e}")
                        logger.error(f"Private key length: {len(private_key) if private_key else 0}")
                        logger.error(f"Project ID: {google_creds.get('project_id')}")
                        logger.error(f"Client email: {google_creds.get('client_email')}")
            
            # Option 4: Fallback to credentials file
            if not credentials and hasattr(self, 'credentials_file') and os.path.exists(self.credentials_file):
                logger.info("Falling back to credentials file")
                # Try to determine the type of credentials file
                with open(self.credentials_file, 'r') as f:
                    creds_data = json.load(f)
                
                # Check if it's a service account file
                if 'type' in creds_data and creds_data['type'] == 'service_account':
                    logger.info("Using service account authentication from file")
                    credentials = ServiceAccountCredentials.from_service_account_file(
                        self.credentials_file, 
                        scopes=scope
                    )
                # Check if it's an OAuth client credentials file
                elif 'installed' in creds_data or 'web' in creds_data:
                    logger.warning("OAuth client credentials detected. For production use, consider using a service account.")
                    logger.info("Attempting OAuth authentication...")
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_file, 
                            scope
                        )
                        # Use local server with specific port
                        credentials = flow.run_local_server(port=8080, open_browser=True)
                    except Exception as oauth_error:
                        logger.error(f"OAuth authentication failed: {str(oauth_error)}")
                        logger.error("Please configure redirect URIs in Google Cloud Console or use a service account")
                        return False
                else:
                    logger.error("Unknown credentials file format. Please use a service account JSON file.")
                    return False
            
            if not credentials:
                logger.error("No valid Google credentials found. Please set environment variables or provide credentials file.")
                return False
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=credentials)
            
            logger.info("Successfully authenticated with Google Sheets API")
            return True
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets API: {str(e)}")
            return False
    
    def get_existing_bank_app_ids(self) -> Dict[str, Any]:
        """Get existing bank application IDs and loan account numbers from the Google Sheet with row positions.
        
        Returns:
            Dictionary with existing data and their row positions
        """
        try:
            if not self.service:
                logger.error("Google Sheets service not initialized")
                return {'records': {}, 'bank_app_ids': [], 'loan_account_numbers': []}
                
            # Get all data from the sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.info("No existing data found in Google Sheets")
                return {'records': {}, 'bank_app_ids': [], 'loan_account_numbers': []}
            
            # Skip header row (first row)
            data_rows = values[1:] if len(values) > 1 else []
            
            existing_records = {}  # Key: identifier, Value: {row_index, data}
            existing_bank_app_ids = []
            existing_loan_account_numbers = []
            
            for row_index, row in enumerate(data_rows, start=2):  # Start at 2 because row 1 is headers
                if len(row) < 22:  # Ensure we have enough columns (at least up to loan account number)
                    continue
                    
                # Column B = Bank App ID, Column R = Loan Account Number
                bank_app_id = row[1] if len(row) > 1 and row[1].strip() else None  # Column B
                loan_account_number = row[17] if len(row) > 17 and row[17].strip() else None  # Column R
                
                if bank_app_id and bank_app_id != 'Not found':
                    bank_app_id = str(bank_app_id).strip()
                    existing_bank_app_ids.append(bank_app_id)
                    existing_records[bank_app_id] = {
                        'row_index': row_index,
                        'data': row,
                        'identifier_type': 'bankAppId'
                    }
                
                if loan_account_number and loan_account_number != 'Not found':
                    loan_account_number = str(loan_account_number).strip()
                    existing_loan_account_numbers.append(loan_account_number)
                    # If we don't already have this record by bankAppId, add it by loan account number
                    if bank_app_id not in existing_records:
                        existing_records[loan_account_number] = {
                            'row_index': row_index,
                            'data': row,
                            'identifier_type': 'loanAccountNumber'
                        }
            
            logger.info(f"Found {len(existing_records)} existing records in Google Sheets")
            
            return {
                'records': existing_records,
                'bank_app_ids': existing_bank_app_ids,
                'loan_account_numbers': existing_loan_account_numbers
            }
            
        except HttpError as e:
            logger.error(f"Error retrieving data from Google Sheets: {str(e)}")
            return {'records': {}, 'bank_app_ids': [], 'loan_account_numbers': []}
        except Exception as e:
            logger.error(f"Unexpected error retrieving data: {str(e)}")
            return {'records': {}, 'bank_app_ids': [], 'loan_account_numbers': []}
    
    def append_bank_application_data(self, applications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Append bank application data to Google Sheets with update capability.
        
        Args:
            applications: List of bank application dictionaries
            
        Returns:
            Update statistics dictionary
        """
        stats = {
            'total_processed': 0,
            'new_records': 0,
            'updated_records': 0,
            'duplicates_skipped': 0,
            'filtered_out': 0,
            'errors': 0
        }
        
        if not self.service:
            logger.error("Google Sheets service not initialized")
            stats['errors'] += 1
            return stats
        
        try:
            # Ensure headers exist
            self._ensure_headers_exist()
            
            # Filter applications to only include disbursed records
            disbursed_applications = []
            for app in applications:
                stats['total_processed'] += 1
                
                disbursement_stage = app.get('disbursementStage', '').strip()
                
                # Only process records with disbursementStage = "Disbursed"
                if disbursement_stage == 'Disbursed':
                    disbursed_applications.append(app)
                    logger.debug(f"Including disbursed record: {app.get('bankAppId', 'No ID')} - {app.get('firstName', '')} {app.get('lastName', '')}")
                else:
                    stats['filtered_out'] += 1
                    logger.info(f"Filtering out non-disbursed record (status: '{disbursement_stage}'): {app.get('bankAppId', 'No ID')} - {app.get('firstName', '')} {app.get('lastName', '')}")
            
            logger.info(f"Filtered {len(disbursed_applications)} disbursed records from {len(applications)} total applications (only saving 'Disbursed' status records)")
            
            # If no disbursed records, return early
            if not disbursed_applications:
                logger.info("No disbursed records to save to Google Sheets (only records with disbursementStage='Disbursed' are saved)")
                return stats
            
            # Get existing bank application IDs and loan account numbers for duplicate checking
            existing_data = self.get_existing_bank_app_ids()
            existing_records = existing_data['records']
            existing_bank_app_ids = existing_data['bank_app_ids']
            existing_loan_account_numbers = existing_data['loan_account_numbers']
            
            logger.info(f"Found {len(existing_records)} existing records in Google Sheets")
            
            new_records = []
            records_to_update = []
            
            for app in disbursed_applications:
                
                # Extract both identifiers for checking
                bank_app_id = app.get('bankAppId')
                loan_account_number = app.get('loanAccountNumber')
                
                # Clean up the identifiers
                bank_app_id = str(bank_app_id).strip() if bank_app_id and bank_app_id != 'Not found' else None
                loan_account_number = str(loan_account_number).strip() if loan_account_number and loan_account_number != 'Not found' else None
                
                # Check if we have at least one identifier
                if not bank_app_id and not loan_account_number:
                    logger.warning("Skipping record without bankAppId or loanAccountNumber")
                    continue
                
                # Check if this record already exists
                existing_record = None
                identifier_used = None
                
                if bank_app_id and bank_app_id in existing_records:
                    existing_record = existing_records[bank_app_id]
                    identifier_used = bank_app_id
                elif loan_account_number and loan_account_number in existing_records:
                    existing_record = existing_records[loan_account_number]
                    identifier_used = loan_account_number
                
                if existing_record:
                    # Check if update is needed
                    if self._should_update_record(app, existing_record['data']):
                        # Prepare updated row data
                        updated_row_data = self._prepare_bank_application_row(app)
                        records_to_update.append({
                            'row_index': existing_record['row_index'],
                            'data': updated_row_data,
                            'identifier': identifier_used
                        })
                        stats['updated_records'] += 1
                        logger.info(f"Updating existing record for {identifier_used}")
                    else:
                        stats['duplicates_skipped'] += 1
                        logger.info(f"No changes detected for {identifier_used}, skipping")
                else:
                    # New record
                    identifier_info = []
                    if bank_app_id:
                        identifier_info.append(f"bankAppId: {bank_app_id}")
                    if loan_account_number:
                        identifier_info.append(f"loanAccountNumber: {loan_account_number}")
                    
                    logger.info(f"Adding new record with {', '.join(identifier_info)}")
                    
                    # Prepare row data for bank application
                    row_data = self._prepare_bank_application_row(app)
                    new_records.append(row_data)
                    stats['new_records'] += 1
                    
                    # Add to existing lists to prevent duplicates within the same batch
                    if bank_app_id:
                        existing_bank_app_ids.append(bank_app_id)
                    if loan_account_number:
                        existing_loan_account_numbers.append(loan_account_number)

            # Update existing records first
            if records_to_update:
                self._update_existing_records(records_to_update)
                logger.info(f"Updated {len(records_to_update)} existing records")

            # Add new records
            if new_records:
                body = {
                    'values': new_records,
                    'majorDimension': 'ROWS'  # Explicitly specify rows
                }
                
                logger.info(f"Appending {len(new_records)} new rows to Google Sheets")
                
                result = self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=self.range_name,
                    valueInputOption='RAW',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
                
                updated_cells = result.get('updates', {}).get('updatedCells', 0)
                updated_rows = result.get('updates', {}).get('updatedRows', 0)
                logger.info(f"Successfully appended bank application data - New rows: {updated_rows}, Updated cells: {updated_cells}")
            
            return stats
            
        except HttpError as e:
            logger.error(f"Google Sheets API error during bank application data append: {str(e)}")
            stats['errors'] += 1
            return stats
        except Exception as e:
            logger.error(f"Error during bank application data append: {str(e)}")
            stats['errors'] += 1
            return stats
    
    def _ensure_headers_exist(self):
        """Ensure that the spreadsheet has proper headers."""
        try:
            # Check if the first row has headers
            header_range = f"{self.range_name.split('!')[0]}!A1:V1"  # First row with all columns
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=header_range
            ).execute()
            
            values = result.get('values', [])
            
            # If no headers or empty, add them
            if not values or not values[0] or values[0][0] != 'Timestamp':
                logger.info("Adding headers to Google Sheets")
                headers = [
                    'Timestamp',                # A
                    'Bank Application ID',      # B
                    'Basic Application ID',     # C
                    'Basic Disbursement ID',    # D
                    'First Name',               # E
                    'Last Name',                # F
                    'Mobile Number',            # G
                    'Bank Name',                # H
                    'Product Type',             # I
                    'Disbursement Amount',      # J
                    'Loan Sanction Amount',     # K
                    'Disbursed On',             # L
                    'Disbursed Created On',     # M
                    'Sanction Date',            # N
                    'Disbursement Stage',       # O
                    'Disbursement Status',      # P
                    'Verification Status',      # Q
                    'Loan Account Number',      # R
                    'PDD',                      # S
                    'OTC',                      # T
                    'Sourcing Channel',         # U
                    'Sourcing Code'             # V
                ]
                
                body = {
                    'values': [headers],
                    'majorDimension': 'ROWS'
                }
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=header_range,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                logger.info("Headers added successfully")
                
        except Exception as e:
            logger.warning(f"Could not add headers: {str(e)}")
            # Continue without headers if there's an issue
    
    def _prepare_bank_application_row(self, app: Dict[str, Any]) -> List[str]:
        """Prepare row data for bank application data.
        
        Args:
            app: Bank application dictionary
            
        Returns:
            List of cell values for the row
        """
        def safe_str(value, default=''):
            """Safely convert value to string, handling None and empty values."""
            if value is None or value == '' or value == 'Not found':
                return default
            return str(value)
        
        # Extract data from bank application
        # Generate IST timestamp
        timestamp = get_ist_timestamp_formatted()
        
        # Basic application info
        first_name = safe_str(app.get('firstName'))
        last_name = safe_str(app.get('lastName'))
        
        bank_app_id = safe_str(app.get('bankAppId'))
        basic_app_id = safe_str(app.get('basicAppId'))
        basic_disb_id = safe_str(app.get('basicDisbId'))
        
        # Financial data (keep as numbers for spreadsheet calculations)
        disbursement_amount = app.get('disbursementAmount', 0) if app.get('disbursementAmount') not in [None, '', 'Not found'] else 0
        loan_sanction_amount = app.get('loanSanctionAmount', 0) if app.get('loanSanctionAmount') not in [None, '', 'Not found'] else 0
        
        # Dates
        disbursed_on = safe_str(app.get('disbursedOn'))
        disbursed_created_on = safe_str(app.get('disbursedCreatedOn'))
        sanction_date = safe_str(app.get('sanctionDate'))
        
        # Status and stage
        disbursement_stage = safe_str(app.get('disbursementStage'))
        disbursement_status = safe_str(app.get('disbursementStatus'))
        verification_status = safe_str(app.get('VerificationStatus'))
        
        # Contact and other info
        mobile = safe_str(app.get('primaryborrowerMobile'))
        bank_name = safe_str(app.get('appBankName'))
        product_type = safe_str(app.get('applicationProductType'))
        
        # Additional fields
        loan_account_number = safe_str(app.get('loanAccountNumber'))
        pdd = safe_str(app.get('pdd'))
        otc = safe_str(app.get('otc'))
        sourcing_channel = safe_str(app.get('sourcingChannel'))
        sourcing_code = safe_str(app.get('sourcingCode'))
        
        # Return row data in a comprehensive format (each element will be a cell in the row)
        row = [
            timestamp,                    # A - Timestamp
            bank_app_id,                  # B - Bank Application ID (primary key for duplicates)
            basic_app_id,                 # C - Basic Application ID
            basic_disb_id,                # D - Basic Disbursement ID
            first_name,                   # E - First Name
            last_name,                    # F - Last Name
            mobile,                       # G - Mobile Number
            bank_name,                    # H - Bank Name
            product_type,                 # I - Product Type
            disbursement_amount,          # J - Disbursement Amount (as number)
            loan_sanction_amount,         # K - Loan Sanction Amount (as number)
            disbursed_on,                 # L - Disbursed On
            disbursed_created_on,         # M - Disbursed Created On
            sanction_date,                # N - Sanction Date
            disbursement_stage,           # O - Disbursement Stage
            disbursement_status,          # P - Disbursement Status
            verification_status,          # Q - Verification Status
            loan_account_number,          # R - Loan Account Number
            pdd,                          # S - PDD
            otc,                          # T - OTC
            sourcing_channel,             # U - Sourcing Channel
            sourcing_code                 # V - Sourcing Code
        ]
        
        # Log the row structure for debugging
        logger.debug(f"Prepared row with {len(row)} columns: {[f'{chr(65+i)}={v}' for i, v in enumerate(row[:5])]}")
        
        return row
    
    def _should_update_record(self, new_app: Dict[str, Any], existing_row: List[str]) -> bool:
        """Check if an existing record should be updated based on new data.
        
        Args:
            new_app: New application data
            existing_row: Existing row data from Google Sheets
            
        Returns:
            True if update is needed, False otherwise
        """
        try:
            # Key fields that should trigger an update if changed
            update_trigger_fields = [
                ('disbursementStage', 14),     # Column O (index 14)
                ('disbursementStatus', 15),    # Column P (index 15) 
                ('disbursementAmount', 9),     # Column J (index 9)
                ('disbursedOn', 11),          # Column L (index 11)
                ('sanctionDate', 13),         # Column N (index 13)
                ('primaryborrowerMobile', 6), # Column G (index 6)
                ('pdd', 18),                  # Column S (index 18)
                ('otc', 19),                  # Column T (index 19)
            ]
            
            for field_name, column_index in update_trigger_fields:
                new_value = str(new_app.get(field_name, '')).strip()
                existing_value = str(existing_row[column_index]).strip() if len(existing_row) > column_index else ''
                
                # Skip if both are empty or "Not found"
                if (not new_value or new_value == 'Not found') and (not existing_value or existing_value == 'Not found'):
                    continue
                
                # Check for important status changes
                if field_name == 'disbursementStage':
                    # Update if status changes from any state to "Disbursed"
                    if new_value == 'Disbursed' and existing_value != 'Disbursed':
                        logger.info(f"Status change detected: {existing_value} → {new_value}")
                        return True
                    # Update if status changes from "Pending" to any other state
                    elif existing_value == 'Pending' and new_value != 'Pending' and new_value:
                        logger.info(f"Status change detected: {existing_value} → {new_value}")
                        return True
                
                # Check for new information being added
                elif field_name in ['disbursementAmount', 'disbursedOn', 'sanctionDate', 'primaryborrowerMobile']:
                    # Update if we have new data and existing is empty/not found
                    if new_value and new_value != 'Not found' and (not existing_value or existing_value == 'Not found'):
                        logger.info(f"New {field_name} data: {new_value}")
                        return True
                    # Update if values are different and new value is not empty
                    elif new_value and new_value != existing_value:
                        logger.info(f"{field_name} changed: {existing_value} → {new_value}")
                        return True
                
                # Check for verification status updates
                elif field_name in ['pdd', 'otc']:
                    if new_value and new_value != existing_value:
                        logger.info(f"{field_name} verification updated: {existing_value} → {new_value}")
                        return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking if update needed: {str(e)}")
            return False
    
    def _update_existing_records(self, records_to_update: List[Dict[str, Any]]) -> None:
        """Update existing records in Google Sheets.
        
        Args:
            records_to_update: List of records with row_index and new data
        """
        try:
            for record in records_to_update:
                row_index = record['row_index']
                new_data = record['data']
                identifier = record['identifier']
                
                # Create range for this specific row (A to V columns)
                range_name = f"{self.range_name.split('!')[0]}!A{row_index}:V{row_index}"
                
                body = {
                    'values': [new_data],
                    'majorDimension': 'ROWS'
                }
                
                # Update the row
                result = self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                updated_cells = result.get('updatedCells', 0)
                logger.info(f"Updated row {row_index} for {identifier} - Updated cells: {updated_cells}")
                
        except Exception as e:
            logger.error(f"Error updating existing records: {str(e)}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass 