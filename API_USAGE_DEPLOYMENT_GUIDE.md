# HOM-i WhatsApp OTP Verification API - API Usage and Deployment Guide

## Overview
This guide details the API usage, endpoints, payloads, responses, error handling, and common CURL examples for HOM-i WhatsApp OTP Verification API hosted at:

**Base URL:** `http://localhost:5000/api_v1`

## API Endpoints
<!-- 
### 1. Health Check
- **Method:** GET
- **Path:** `/health`
- **Description:** Check if the API service is running.
- **Response:** 200 OK with service status.

**Example Response:**
```json
{
  "status": "healthy",
  "service": "HOM-i API"
}
``` -->

### 2. Send OTP
- **Method:** POST
- **Path:** `/otp_send`
- **Description:** Sends an OTP to a provided phone number via WhatsApp.
- **Payload:**
```json
{
  "phone_number": "string (various formats supported)"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "data": {
    "phone_number": "788888888",
    "otp": "123456"
  }
}
```

**Error:** 400 Bad Request for invalid phone number.

### 3. Verify OTP
- **Method:** POST
- **Path:** `/otp_verify`
- **Description:** Validates an OTP sent to the user's WhatsApp number.
- **Payload:**
```json
{
  "phone_number": "string",
  "otp": "string (6 digits)"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "data": {
    "phone_number": "788888888"
  }
}
```

### 4. Resend OTP
- **Method:** POST
- **Path:** `/otp_resend`
- **Description:** Resends the OTP to a specified phone number.
- **Payload:**
```json
{
  "phone_number": "string"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "OTP resent successfully",
  "data": {
    "phone_number": "788888888",
    "otp": "654321"
  }
}
```

### 5. Create Lead
- **Method:** POST
- **Path:** `/lead_create`
- **Description:** Creates a new lead in the Basic Application.
- **Payload:**
```json
{
  "first_name": "string",
  "last_name": "string",
  "mobile_number": "string",
  "email": "string",
  "pan_number": "string",
  "loan_type": "string",
  "loan_amount": "number",
  "loan_tenure": "integer",
  "gender": "string (optional)",
  "dob": "string",
  "pin_code": "string"
}
```

**Success Response:**
```json
{
  "basic_application_id": "BA123456789",
  "message": "Lead Created Successfully."
}
```

### 6. Lead Status
- **Method:** POST
- **Path:** `/lead_status`
- **Description:** Retrieves the status of a lead using either mobile number or Basic Application ID.
- **Payload:**
```json
{
  "mobile_number": "string (optional)",
  "basic_application_id": "string (optional)"
}
```

**Success Response:**
```json
{
  "status": "Application Under Review",
  "message": "Your lead status is: Application Under Review"
}
```

### 7. Create Lead
- **Method:** POST
- **Path:** `/create_lead`
- **Description:** Creates a comprehensive lead through FBB (First Bank Branch) processing with complete customer information and flexible optional fields.
- **Payload:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "mobile": "7999999999",
  "email": "john.doe@example.com",
  "pan": "ABCDE1234F",
  "loanType": "HL",
  "loanAmountReq": 100000,
  "loanTenure": 24,
  "creditScore": 750,
  "pincode": "126102",
  "dateOfBirth": "1996-12-08",
  "gender": "Male",
  "annualIncome": 1200000,
  "applicationAssignedToRm": "b3981dc9-02b3-44be-be96-5a09a5547d51",
  "remarks": "Priority lead",
  "state": "HARYANA",
  "qrShortCode": "BAE000247",
  "customerId": "CX123",
  "includeCreditScore": true,
  "isLeadPrefilled": true
}
```

**Success Response:**
```json
{
  "basic_application_id": "B002BJF",
  "reference_id": "adfd2272-c572-420d-bafc-b134ed3a0aa3",
  "message": "Lead Created Successfully."
}
```

**Features:**
- Multi-stage API processing with comprehensive validation
- Automatic database storage with complete audit trail
- Error handling for each processing stage
- Integration with CreateFBBByBasicUser and SelfFullfilment APIs
- Flexible optional fields for enhanced data capture

### 8. Lead Flash (Complete Application Processing)
- **Method:** POST
- **Path:** `/lead_flash`
- **Description:** Processes a complete application workflow including property and profession details through Self-Fulfillment API.
- **Payload:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "mobile": "7999999999",
  "email": "john.doe@example.com",
  "pan": "ABCDE1234F",
  "loanType": "HL",
  "loanAmountReq": 100000,
  "loanTenure": 24,
  "creditScore": 750,
  "pincode": "126102",
  "dateOfBirth": "1996-12-08",
  "gender": "Male",
  "applicationId": "adfd2272-c572-420d-bafc-b134ed3a0aa3",
  "professionId": "34e544e6-1e22-49f4-a56a-44c14a32b484",
  "professionName": "Salaried",
  "propertyIdentified": "Yes",
  "propertyName": "Green Valley Apartments",
  "propertyType": "Apartment",
  "agreementType": "Sale Deed",
  "location": "Gurgaon",
  "propertyValue": 8500000,
  "salaryCreditModeId": "ef70c7ce-577a-4302-a485-adccdf31968d",
  "salaryCreditModeName": "Bank Transfer",
  "companyName": "Tech Solutions Inc"
}
```

**Success Response:**
```json
{
  "basic_application_id": "B002BJF",
  "reference_id": "adfd2272-c572-420d-bafc-b134ed3a0aa3",
  "message": "Lead Flash processed successfully"
}
```

**Features:**
- Complete application workflow processing
- Property and profession information capture
- Self-fulfillment API integration
- Full application status update
- Database storage with complete audit trail

### 9. Book Appointment
- **Method:** POST
- **Path:** `/book_appointment`
- **Description:** Books an appointment by creating a task/comment in the Basic Application system.
- **Payload:**
```json
{
  "date": "30-07-2025",
  "time": "6:00 PM",
  "reference_id": "TEST_REF_123456"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Appointment booked successfully",
  "appointment_id": "83648839-b281-433b-841b-6a58a55fef00",
  "basic_app_id": "B0027J8",
  "comment_ref": "TH9O8YM2GPT"
}
```

**Features:**
- Integration with Basic Application API CreateTaskOrComment
- Flexible date/time format support
- Automatic database storage of appointment details
- Complete audit trail and status tracking

### 9. WhatsApp Webhook
- **Method:** POST
- **Path:** `/whatsapp/webhook`
- **Description:** Receives WhatsApp messages from Gupshup for status inquiries.
- **Method:** GET
- **Path:** `/whatsapp/webhook`
- **Description:** Webhook verification endpoint for WhatsApp Business API.

### 10. Historical Disbursements Processing
- **Method:** POST
- **Path:** `/historical/start`
- **Description:** Start historical email processing job for disbursement data extraction.
- **Payload:**
```json
{
  "days_back": 7,
  "email_folders": ["INBOX"],
  "subject_filter": "disbursement",
  "sender_filter": "bank@example.com"
}
```

### 11. Live Disbursements Monitoring
- **Method:** POST
- **Path:** `/live/start`
- **Description:** Start live email monitoring for real-time disbursement tracking.
- **Method:** POST
- **Path:** `/live/stop`
- **Description:** Stop live email monitoring.

### 12. Job Status Tracking
- **Method:** GET
- **Path:** `/historical/status/{job_id}`
- **Description:** Get status of historical processing job.
- **Method:** GET
- **Path:** `/live/status`
- **Description:** Get status of live monitoring service.

## Phone Number Formats Supported

The API automatically normalizes phone numbers to include the country code **91** (India) for WhatsApp services. The system handles various input formats:

### Supported Input Formats:
- **`9173457840`** - 10 digits starting with 91 (actual phone number)
- **`917888888888`** - Already has country code (12 digits)
- **`788888888`** - Without country code (9 digits)
- **`+917888888888`** - With + prefix
- **`0788888888`** - With leading 0 (11 digits)
- **`888888888`** - 9 digits without country code
- **`88888888`** - 8 digits without country code
- **`91 788 888 8888`** - With spaces
- **`91-788-888-8888`** - With dashes

### Normalization Rules:
1. **Removes** spaces, dashes, parentheses, and other separators
2. **Removes** + prefix if present
3. **Smart processing**: Distinguishes between country codes and actual phone numbers
4. **Adds** country code **91** if not present
5. **Removes** leading 0 if present
6. **Returns** normalized format: `+91XXXXXXXXXX`

### Validation Regex:
`^\+91[1-9]\d{9,11}$`

## Loan Types Supported

The API supports automatic mapping of loan types to Basic Application codes:

- **Home Loan**: `HL`
- **Loan Against Property**: `LAP`
- **Personal Loan**: `PL`
- **Business Loan**: `BL`
- **Car Loan**: `CL`
- **Education Loan**: `EL`

## Example CURL Commands

### Send OTP
```bash
curl -X POST "http://localhost:5000/api_v1/otp_send" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "917888888888"}'
```

### Verify OTP
```bash
curl -X POST "http://localhost:5000/api_v1/otp_verify" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "917888888888", "otp": "123456"}'
```

### Resend OTP
```bash
curl -X POST "http://localhost:5000/api_v1/otp_resend" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "917888888888"}'
```

### Create Lead
```bash
curl -X POST "http://localhost:5000/api_v1/lead_create" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "mobile_number": "917888888888",
    "email": "john.doe@example.com",
    "pan_number": "ABCDE1234F",
    "loan_type": "home loan",
    "loan_amount": 500000,
    "loan_tenure": 36,
    "gender": "male",
    "dob": "15/03/1990",
    "pin_code": "400001"
  }'
```

### Lead Status by Mobile Number
```bash
curl -X POST "http://localhost:5000/api_v1/lead_status" \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "917888888888"}'
```

### Lead Status by Application ID
```bash
curl -X POST "http://localhost:5000/api_v1/lead_status" \
  -H "Content-Type: application/json" \
  -d '{"basic_application_id": "BA123456789"}'
```

### Create Lead
```bash
curl -X POST "http://localhost:5000/api_v1/create_lead" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "mobile": "7999999999",
    "email": "john.doe@example.com",
    "pan": "ABCDE1234F",
    "loanType": "HL",
    "loanAmountReq": 100000,
    "loanTenure": 24,
    "creditScore": 750,
    "pincode": "126102",
    "dateOfBirth": "1996-12-08",
    "gender": "Male",
    "annualIncome": 1200000,
    "state": "HARYANA",
    "remarks": "Priority lead"
  }'
```

### Lead Flash
```bash
curl -X POST "http://localhost:5000/api_v1/lead_flash" \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "John",
    "lastName": "Doe",
    "mobile": "7999999999",
    "email": "john.doe@example.com",
    "pan": "ABCDE1234F",
    "loanType": "HL",
    "loanAmountReq": 100000,
    "loanTenure": 24,
    "creditScore": 750,
    "pincode": "126102",
    "dateOfBirth": "1996-12-08",
    "gender": "Male",
    "applicationId": "adfd2272-c572-420d-bafc-b134ed3a0aa3",
    "professionId": "34e544e6-1e22-49f4-a56a-44c14a32b484",
    "professionName": "Salaried",
    "propertyIdentified": "Yes",
    "propertyName": "Green Valley Apartments",
    "propertyValue": 8500000
  }'
```

### Book Appointment
```bash
curl -X POST "http://localhost:5000/api_v1/book_appointment" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "30-07-2025",
    "time": "6:00 PM",
    "reference_id": "TEST_REF_123456"
  }'
```

<!-- ### Health Check
```bash
curl -X GET "http://localhost:5000/api_v1/health"
``` -->

### Start Historical Disbursements Processing
```bash
curl -X POST "http://localhost:5000/api_v1/historical/start" \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 30,
    "email_folders": ["INBOX"],
    "subject_filter": "disbursement"
  }'
```

### Start Live Disbursements Monitoring
```bash
curl -X POST "http://localhost:5000/api_v1/live/start" \
  -H "Content-Type: application/json"
```

### Check Job Status
```bash
curl -X GET "http://localhost:5000/api_v1/historical/status/{job_id}"
```

## Error Responses Format

```json
{
  "detail": {
    "success": false,
    "message": "Error description",
    "data": {
      "error": "Additional error details"
    }
  }
}
```

## Common Errors

| Status | Error | Detail |
|--------|-------|--------|
| 400 | Invalid phone number format | Phone number must be a valid Indian mobile number |
| 400 | Invalid OTP | The OTP code provided is incorrect |
| 404 | OTP not found or expired | The OTP has expired. Please request a new one. |
| 404 | Lead not found | No lead found with the specified criteria |
| 422 | Validation error | Invalid input data format |
| 500 | Internal server error | An unexpected error occurred |

## Status Codes

- **200:** OK - Request successful
- **400:** Bad Request - Invalid input data
- **404:** Not Found - Resource not found
- **409:** Conflict - Resource already exists
- **422:** Unprocessable Entity - Validation error
- **429:** Too Many Requests - Rate limit exceeded
- **500:** Internal Server Error - Server error

## OTP Storage & Lifecycle

### Enhanced Storage Architecture
- **Primary**: Dedicated `SupabaseOTPStorage` service for persistent cloud storage
- **Fallback**: Thread-safe `LocalOTPStorage` with in-memory operations
- **Intelligent Failover**: Automatic fallback during service initialization if Supabase unavailable
- **Service Separation**: Independent OTP storage (`otp_storage`) and general database operations (`database_service`)
- **Smart Initialization**: Comprehensive logging and error handling for storage selection
- **Automatic expiry**: OTPs expire after 3 minutes (configurable)

### OTP Lifecycle
1. **Creation**: OTP is stored with `is_used = false` and expiry timestamp
2. **Verification**: OTP is marked as `is_used = true` (not deleted)
3. **Expiry**: Expired OTPs are automatically marked as `is_used = true`
4. **Cleanup**: Used and expired OTPs remain in database for audit trails

## Environment Variables

### Required Configuration
```bash
# Basic Application API Configuration
BASIC_APPLICATION_API_URL=your_basic_api_url
BASIC_APPLICATION_USER_ID=your_user_id
BASIC_APPLICATION_API_KEY=your_api_key

# Gupshup WhatsApp API Configuration
GUPSHUP_API_KEY=your_gupshup_api_key
GUPSHUP_SOURCE=your_gupshup_source_number
GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID=your_otp_template_id
GUPSHUP_LEAD_CREATION_TEMPLATE_ID=your_lead_creation_template_id
GUPSHUP_LEAD_STATUS_TEMPLATE_ID=your_lead_status_template_id

# Supabase Configuration (Optional - falls back to local storage if not configured)
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# OTP Configuration
OTP_EXPIRY_MINUTES=3

# WhatsApp Webhook Configuration
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token

# Email Processing Configuration
ZOHO_EMAIL=your_zoho_email@domain.com
ZOHO_PASSWORD=your_zoho_password
OPENAI_API_KEY=your_openai_api_key

# Google Sheets Configuration
GOOGLE_CREDENTIALS_JSON=base64_encoded_service_account_json
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
GOOGLE_WORKSHEET_NAME=your_worksheet_name
```

## Deployment Options

### Option 1: Local Development
```bash
# Clone the repository
git clone <repository-url>
cd otpVerification

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Run the application
python -m app.main
```

### Option 2: Docker Deployment
```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up --build -d
```

### Option 3: Direct Docker
```bash
# Build the image
docker build -t homi-api .

# Run the container
docker run -d \
  -p 5000:5000 \
  --env-file .env \
  homi-api
```

## Notes

- Always ensure phone numbers are passed in a format that can be normalized.
- OTPs expire in 180 seconds (3 minutes).
<!-- - Use the `/health` endpoint to confirm service is live before integration testing. -->
- The API automatically handles phone number normalization for WhatsApp services.
- **Enhanced Storage**: Intelligent dual-layer storage with automatic Supabase → Local fallback.
- **Service Architecture**: Separated OTP storage and database services for optimal reliability.
- **Improved Error Handling**: Better variable scope management and comprehensive error logging.
- WhatsApp notifications are sent for lead creation and status updates.

## Google Sheets Integration

For disbursement tracking, the API integrates with Google Sheets:

1. **Setup Google Service Account:**
   - Create a service account in Google Cloud Console
   - Download the JSON credentials file
   - Convert to base64 using: `python scripts/convert_google_credentials.py credentials.json`

2. **Configure Environment:**
   ```bash
   GOOGLE_CREDENTIALS_JSON=base64_encoded_json
   GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
   GOOGLE_WORKSHEET_NAME=Sheet1
   ```

3. **Share Spreadsheet:**
   - Share your Google Sheet with the service account email
   - Grant "Editor" permissions for write access

## Contact & Support

- For technical assistance, contact the development team or system administrator.
- Refer to inline code documentation and `/docs` endpoint for API documentation.
<!-- - Check the `/health` endpoint for service status and configuration validation. -->

---

**End of Document** 