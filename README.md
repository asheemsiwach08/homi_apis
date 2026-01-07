# HOM-i WhatsApp OTP, Lead Creation & Status API

A comprehensive FastAPI-based REST API for WhatsApp OTP verification, lead creation, status tracking, and email-based disbursement processing using Gupshup API with intelligent Supabase PostgreSQL storage and automatic local storage fallback.

## Features

- ✅ **WhatsApp OTP Management**
  - Send OTP via WhatsApp using Gupshup API
  - Resend OTP functionality
  - Verify OTP with 3-minute expiry
  - Phone number validation and normalization
- ✅ **Lead Management**
  - Create leads with Basic Application API integration
  - **Comprehensive lead creation** with flexible field support (optional fields for enhanced data capture)
  - **Lead flash processing** for complete application workflow
  - Track lead status by mobile number or application ID
  - **Appointment booking** with calendar integration
  - Comprehensive lead data validation and storage with upsert logic
- ✅ **Email Processing & Disbursements**
  - **Historical disbursement processing** from email archives
  - **Live email monitoring** for real-time disbursement tracking
  - **AI-powered email analysis** using OpenAI for data extraction
  - **Google Sheets integration** for automated data updates
  - Support for multiple email providers (Zoho Mail)
- ✅ **WhatsApp Integration**
  - Lead creation confirmation messages
  - Lead status update notifications
  - Intelligent message parsing for status requests
  - Automatic webhook processing for real-time message handling
  - Multiple template support for different use cases
- ✅ **Storage & Infrastructure**
  - **Multi-Environment Database Support**: Orbit (primary) and Homfinity (secondary) environments
  - **Intelligent Storage Fallback**: Primary Supabase PostgreSQL with automatic local storage fallback
  - **Separated OTP Storage**: Dedicated OTP storage service with independent failover
  - **Database Service Architecture**: Modular database services with automatic environment selection
  - **Environment-Specific Operations**: Automatic table-to-environment mapping with manual override support
  - Google Sheets integration with secure credential management
  - Thread-safe operations and comprehensive audit trails
- ✅ **API Features**
  - RESTful API design with proper HTTP status codes
  - Background job processing for email analysis
  - Comprehensive error handling and async/await support
  - Environment variable configuration
- ✅ **Development & Deployment**
  - Secure credential management for production
  - Docker support with multi-stage builds
  - Comprehensive testing and debugging tools

## Project Structure

```
otpVerification/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── src/                    # Email processing & disbursements module
│   │   ├── ai_analyzer/        # OpenAI-powered email analysis
│   │   ├── api_client/         # External API integrations
│   │   ├── data_processing/    # Data transformation utilities
│   │   ├── email_processor/    # Email monitoring and parsing
│   │   └── sheets_integration/ # Google Sheets client
│   ├── api/
│   │   └── endpoints/
│   │       ├── otp.py         # OTP operations
│   │       ├── leads.py       # Lead management
│   │       ├── whatsapp_webhook.py # WhatsApp webhook handler
│   │       ├── historical_disbursements.py # Historical email processing
│   │       └── live_disbursements.py # Live email monitoring
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # Main API router
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── otp.py          # OTP-related endpoints
│   │       ├── leads.py        # Lead management endpoints
│   │       ├── whatsapp.py     # WhatsApp message processing
│   │       ├── whatsapp_webhook.py # WhatsApp webhook (automatic)
<!-- │   │       └── health.py       # Health check endpoint -->
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Application configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database_service.py # Database operations
│   │   ├── whatsapp_service.py # WhatsApp API integration
│   │   └── basic_application_service.py # Basic Application API
│   └── utils/
│       ├── __init__.py
│       └── validators.py       # Data validation utilities
├── database_setup/             # Database setup scripts
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Development Docker setup
├── docker-compose.prod.yml     # Production Docker setup
├── env.example                 # Environment variables template
└── README.md                   # This file
```

## Prerequisites

- Python 3.8+ (for local development)
- Docker & Docker Compose (for containerized deployment)
- Gupshup WhatsApp API account
- Basic Application API credentials
- Supabase account and project (optional - falls back to local storage)

## Installation

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd otpVerification
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` file with your configuration:
   ```env
   # Server Configuration
   HOST=0.0.0.0
   PORT=5000
   DEBUG=True

   # Basic Application API Configuration
   BASIC_APPLICATION_API_URL=your_basic_api_url
   BASIC_APPLICATION_USER_ID=your_user_id
   BASIC_APPLICATION_API_KEY=your_api_key

   # Gupshup WhatsApp API Configuration (Default/Legacy)
   GUPSHUP_API_KEY=your_gupshup_api_key
   GUPSHUP_SOURCE=your_source_number
   GUPSHUP_API_TEMPLATE_URL=https://api.gupshup.io/wa/api/v1/template/msg
   GUPSHUP_API_MSG_URL=https://api.gupshup.io/wa/api/v1/msg

   # Multi-App Gupshup Configuration (New Format)
   # Configure multiple Gupshup apps with their own API keys and app IDs
   # Format: {APP_NAME}_GUPSHUP_API_KEY, {APP_NAME}_GUPSHUP_APP_ID, {APP_NAME}_GUPSHUP_APP_NAME
   
   # Basic Home Loan App Configuration
   BASICHOMELOAN_GUPSHUP_API_KEY=your_basichomeloan_api_key
   BASICHOMELOAN_GUPSHUP_APP_ID=your_basichomeloan_app_id
   BASICHOMELOAN_GUPSHUP_APP_NAME=your_basichomeloan_app_name
   BASICHOMELOAN_GUPSHUP_SOURCE=your_basichomeloan_source_number
   
   # Iraby Basic App Configuration
   IRABYBASIC_GUPSHUP_API_KEY=your_irabybasic_api_key
   IRABYBASIC_GUPSHUP_APP_ID=your_irabybasic_app_id
   IRABYBASIC_GUPSHUP_APP_NAME=your_irabybasic_app_name
   IRABYBASIC_GUPSHUP_SOURCE=your_irabybasic_source_number

   ... other apps

   # WhatsApp Templates
   GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID=your_otp_template_id
   GUPSHUP_WHATSAPP_OTP_SRC_NAME=source_name
   GUPSHUP_LEAD_CREATION_TEMPLATE_ID=your_lead_creation_template_id
   GUPSHUP_LEAD_CREATION_SRC_NAME=your_lead_creation_src_name
   GUPSHUP_LEAD_STATUS_TEMPLATE_ID=your_lead_status_template_id
   GUPSHUP_LEAD_STATUS_SRC_NAME=your_lead_status_src_name

   # Multi-Environment Supabase Configuration
   # Orbit Environment (Primary - Main business operations)
   SUPABASE_ORBIT_URL=your_orbit_supabase_project_url
   SUPABASE_ORBIT_SERVICE_ROLE_KEY=your_orbit_supabase_service_role_key
   
   # Homfinity Environment (Secondary - OTP and utilities)
   SUPABASE_HOMFINITY_URL=your_homfinity_supabase_project_url
   SUPABASE_HOMFINITY_SERVICE_ROLE_KEY=your_homfinity_supabase_service_role_key
   
   # Default Database Environment (orbit or homfinity)
   DEFAULT_DATABASE_ENVIRONMENT=orbit
   
   # Legacy Configuration (Optional - for backward compatibility)
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

   # Google Sheets Configuration (for disbursement tracking)
   GOOGLE_CREDENTIALS_JSON=base64_encoded_service_account_json
   GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
   GOOGLE_WORKSHEET_NAME=your_worksheet_name

   # OTP Configuration
   OTP_EXPIRY_MINUTES=3
   ```

5. **Set up Multi-Environment Supabase**
   
   The system supports two Supabase environments for better separation of concerns:
   
   **a. Create Supabase Projects:**
   - **Orbit Environment** (Primary): Main business operations (leads, appointments, disbursements)
   - **Homfinity Environment** (Secondary): OTP storage and utility operations
   - Go to [supabase.com](https://supabase.com) and create both projects
   
   **b. Configure Database Tables:**
   - For **Orbit Environment**: Run SQL scripts for leads, appointments, disbursements, whatsapp_messages tables
   - For **Homfinity Environment**: Run SQL scripts for otp_storage and any utility tables
   - Navigate to SQL Editor in each project and run the appropriate scripts from `database_setup/` directory
   
   **c. Environment Variable Setup:**
   ```bash
   # Orbit Environment (Primary)
   SUPABASE_ORBIT_URL=https://your-orbit-project.supabase.co
   SUPABASE_ORBIT_SERVICE_ROLE_KEY=your-orbit-service-role-key
   
   # Homfinity Environment (Secondary)  
   SUPABASE_HOMFINITY_URL=https://your-homfinity-project.supabase.co
   SUPABASE_HOMFINITY_SERVICE_ROLE_KEY=your-homfinity-service-role-key
   
   # Default Environment
   DEFAULT_DATABASE_ENVIRONMENT=orbit
   ```
   
   **d. Single Environment Setup (Alternative):**
   If you prefer using a single environment, configure only one set and the system will automatically adapt:
   ```bash
   # Use only Orbit for everything
   SUPABASE_ORBIT_URL=your_supabase_url
   SUPABASE_ORBIT_SERVICE_ROLE_KEY=your_service_role_key
   ```

6. **Run the application**
   ```bash
   python -m app.main
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
   ```

### Option 2: Docker Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd otpVerification
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Build and run with Docker Compose**

   **Development:**
   ```bash
   docker-compose up --build
   ```

   **Production:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

4. **Or build and run with Docker directly**
   ```bash
   # Build the image
   docker build -t homfinity-api .

   # Run the container
   docker run -d \
     -p 5000:5000 \
     --env-file .env \
     homfinity-api
   ```

## Phone Number Validation & Normalization

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
   - `9173457840` (10 digits) → `+919173457840` (preserves the 91 as part of phone number)
   - `917888888888` (12 digits) → `+917888888888` (treats 91 as country code)
4. **Adds** country code **91** if not present
5. **Removes** leading 0 if present (e.g., 0788888888 → +917888888888)
6. **Returns** normalized format: `+91XXXXXXXXXX`

### Validation Pattern:
- **Pattern**: `^\+91[1-9]\d{9,11}$`
- **Final format**: Must start with `+91` followed by 10-12 digits
- **Examples**:
  - ✅ `+917888888888` (valid)
  - ✅ `+918888888888` (valid)
  - ❌ `+910888888888` (starts with 0 after country code)
  - ❌ `+91888888888` (too short)
  - ❌ `+918888888888888` (too long)

**Note**: All phone numbers are automatically normalized to the `+91` format before being sent to WhatsApp services, regardless of the input format provided by the user.

## OTP Storage & Lifecycle

The API uses a sophisticated dual-layer storage system with intelligent fallback mechanisms:

### Storage Architecture
- **Primary**: Dedicated `SupabaseOTPStorage` for persistent cloud storage
- **Fallback**: Thread-safe `LocalOTPStorage` with in-memory operations
- **Automatic Failover**: Seamless fallback if Supabase is unavailable during initialization
- **Service Separation**: Independent OTP storage service (`otp_storage`) separate from general database operations (`database_service`)
- **Smart Initialization**: Tries Supabase first, falls back to local storage with comprehensive logging
- **Automatic expiry**: OTPs expire after 3 minutes (configurable)

### OTP Lifecycle
1. **Creation**: OTP is stored with `is_used = false` and expiry timestamp
2. **Verification**: OTP is marked as `is_used = true` (not deleted)
3. **Expiry**: Expired OTPs are automatically marked as `is_used = true`
4. **Cleanup**: Used and expired OTPs remain in database for audit trails

### Benefits of Marking as Used vs Deleting
- **Audit Trails**: Track OTP usage patterns and verification history
- **Analytics**: Analyze OTP success rates and user behavior
- **Security**: Maintain records for security investigations
- **Compliance**: Meet regulatory requirements for data retention
- **Debugging**: Easier troubleshooting of OTP-related issues

## Database Service Architecture

The application uses a modular database service architecture for optimal performance and reliability:

### Service Separation
- **`otp_storage`**: Dedicated service for OTP operations with automatic fallback
  - Used in: OTP endpoints (`app/api/endpoints/otp.py`)
  - Import: `from app.services.database_service import otp_storage`
  - Methods: `set_otp()`, `get_otp()`, `mark_otp_as_used()`

- **`database_service`**: General database operations for leads, disbursements, etc.
  - Used in: Lead management, disbursements, WhatsApp messages, appointments
  - Import: `from app.services.database_service import database_service`
  - Methods: Lead CRUD, disbursement tracking, message storage, etc.

### Intelligent Initialization
```python
# Global instance with fallback mechanism
try:
    otp_storage = SupabaseOTPStorage()
    logger.info("Successfully initialized Supabase OTP storage")
except Exception as e:
    logger.error(f"Warning: Could not initialize Supabase storage: {e}")
    logger.error("Falling back to local storage...")
    otp_storage = LocalOTPStorage()
    logger.info("Successfully initialized Local OTP storage as fallback")
```

### Architecture Benefits
- **Reliability**: OTP service never fails due to Supabase issues
- **Performance**: Local fallback ensures fast OTP operations
- **Separation of Concerns**: Different data types use appropriate storage strategies
- **Maintainability**: Clear service boundaries and responsibilities


## API Endpoints

All endpoints use the `/api_v1` prefix and return JSON responses with consistent error handling.

### 🔐 OTP Operations

#### 1. Send OTP
```http
POST /api_v1/otp_send
Content-Type: application/json

{
    "phone_number": "788888888"
}
```

**Response:**
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

#### 2. Resend OTP
```http
POST /api_v1/otp_resend
Content-Type: application/json

{
    "phone_number": "788888888"
}
```

#### 3. Verify OTP
```http
POST /api_v1/otp_verify
Content-Type: application/json

{
    "phone_number": "788888888",
    "otp": "123456"
}
```

### Lead Management

#### 1. Create Lead (Simple)
```http
POST /api_v1/lead_create
Content-Type: application/json

{
  "firstName": "Ram",
  "lastName": "Singh",
  "gender": "male",
  "mobile": "7988888888",
  "creditScore": 500,
  "pan": "ABCDE1234F",
  "loanType": "HL",
  "loanAmountReq": 100,
  "loanTenure": 2,
  "pincode": "126112",
  "email": "user@example.com",
  "dateOfBirth": "12/08/2002",
  "annualIncome": 0,
  "applicationAssignedToRm": "string",
  "createdFromPemId": "string",
  "creditScoreTypeId": "string",
  "customerId": "string",
  "includeCreditScore": true,
  "isLeadPrefilled": true,
  "qrShortCode": "BAE0001JC",
  "remarks": "good",
  "state": "string"
}
```

**Response:**
```json
{
    "basic_application_id": "APP123456789",
    "message": "Lead Created Successfully."
}
```

#### 2. Create Lead (Comprehensive)
```http
POST /api_v1/create_lead
Content-Type: application/json

{
  "firstName": "Ram",
  "lastName": "Singh",
  "gender": "male",
  "mobile": "7988888888",
  "creditScore": 500,
  "pan": "ABCDE1234F",
  "loanType": "HL",
  "loanAmountReq": 100,
  "loanTenure": 2,
  "pincode": "126112",
  "email": "user@example.com",
  "dateOfBirth": "12/08/2002",
  "applicationId": "b427d560-43f7-43e7-8fe3-43b86ab89c66",
  "professionId": "34e544e6-1e22-49f4-a56a-44c14a32b484",
  "professionName": "Salaried",
  "propertyIdentified": "string",
  "propertyName": "string",
  "propertyType": "string",
  "agreementType": "string",
  "coBorrowerIncome": 0,
  "unitType": "string",
  "location": "string",
  "usageType": "string",
  "unitNumber": "string",
  "salaryCreditModeId": "string",
  "salaryCreditModeName": "string",
  "selfCompanyTypeId": "string",
  "companyName": "string",
  "propertyTypeId": "string",
  "propertyValue": 0,
  "loanUsageTypeId": "string",
  "aggrementTypeId": "string"
}
```

**Response:**
```json
{
    "basic_application_id": "B002BJF",
    "reference_id": "adfd2272-c572-420d-bafc-b134ed3a0aa3",
    "message": "Lead Created Successfully."
}
```

**Features:**
- Multi-stage processing (FBB → Basic Fulfillment → Self Fulfillment)
- Comprehensive data validation and error handling
- Automatic database storage with complete audit trail
- Integration with multiple Basic Application APIs
- Flexible optional fields for enhanced data capture

#### 3. Lead Flash (Complete Application Processing)
```http
POST /api_v1/lead_flash
Content-Type: application/json

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
    "propertyValue": 8500000
}
```

**Response:**
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

#### 4. Book Appointment
```http
POST /api_v1/book_appointment
Content-Type: application/json

{
    "date": "30-07-2025",
    "time": "6:00 PM",
    "reference_id": "cc9a13c6-06f6-4a2d-b219-5055d3489a19"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Appointment booked successfully",

    "basic_app_id": "B0027J8",

}
```

**Features:**
- Integration with Basic Application API for task/comment creation
- Automatic database storage of appointment details
- Support for flexible date/time formats
- Complete audit trail and status tracking

#### 5. Get Lead Status
```http
POST /api_v1/lead_status
Content-Type: application/json

{
    "mobile_number": "788888888"
}
```

**Or:**
```http
POST /api_v1/lead_status
Content-Type: application/json

{
    "basic_application_id": "APP123456789"
}
```

**Response:**
```json
{
    "status": "Under Review",
    "message": "Your lead status is: Under Review"
}
```

#### 6. Process WhatsApp Message
```http
POST /api_v1/whatsapp/process_message
Content-Type: application/json

{
    "message": "I want to check my application status. My mobile number is 9876543210",
    "phone_number": "+919876543210"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Your application status is: Under Review",
    "status": "Under Review",
    "application_id": "APP123456"
}
```

#### 4. WhatsApp Webhook (Automatic)
```http
POST /api_v1/whatsapp/webhook
Content-Type: application/json

{
  "app": "docdeck",
  "timestamp": 1718007189549,
  "version": 2,
  "type": "message",
  "payload": {
    "id": "ABEGkZUTIXZ0Ago6jWqOZm-Sz0WD",
    "source": "917888888888",
    "type": "text",
    "payload": {
      "text": "Check my application status"
    },
    "sender": {
      "phone": "917888888888",
      "name": "John Doe",
      "country_code": "91",
      "dial_code": "7888888888"
    }
  }
}
```

**Supported Message Formats:**
- "I want to check my application status"
- "Please check my loan status"
- "Application status check"
- "Track my application"
- "My application ID is APP123456"
- "Check status for mobile 9876543210"

### Gupshup WhatsApp APIs (Modular Wrapper)

The API provides comprehensive modular endpoints for all Gupshup WhatsApp outbound messaging capabilities, designed for easy UI integration:

#### 1. Send Text Message
```http
POST /api_v1/gupshup/send-text
Content-Type: application/json

{
    "phone_number": "788888888",
    "message": "Hello! This is a test message from HOM-i.",
    "source_name": "HomiAi"
}
```

#### 2. Send Template Message
```http
POST /api_v1/gupshup/send-template
Content-Type: application/json

{
    "phone_number": "788888888",
    "template_id": "your_template_id",
    "template_params": ["John Doe", "APP123456"],
    "source_name": "HomiAi"
}
```

#### 3. Send Media Message
```http
POST /api_v1/gupshup/send-media
Content-Type: application/json

{
    "phone_number": "788888888",
    "media_type": "image",
    "media_url": "https://example.com/image.jpg",
    "caption": "Check out this property!",
    "filename": "property_image.jpg"
}
```

**Supported Media Types:**
- `image` - Images (JPG, PNG, GIF)
- `document` - PDFs, Word docs, etc.
- `audio` - Audio files
- `video` - Video files

#### 4. Send Interactive Message (Buttons)
```http
POST /api_v1/gupshup/send-interactive
Content-Type: application/json

{
    "phone_number": "788888888",
    "interactive_type": "button",
    "header": {
        "type": "text",
        "text": "Choose an option"
    },
    "body": {
        "text": "Please select what you'd like to do:"
    },
    "footer": {
        "text": "HOM-i Support"
    },
    "action": {
        "buttons": [
            {
                "type": "reply",
                "reply": {
                    "id": "check_status",
                    "title": "Check Status"
                }
            },
            {
                "type": "reply",
                "reply": {
                    "id": "contact_support",
                    "title": "Contact Support"
                }
            }
        ]
    }
}
```

#### 5. Send Interactive Message (List)
```http
POST /api_v1/gupshup/send-interactive
Content-Type: application/json

{
    "phone_number": "788888888",
    "interactive_type": "list",
    "header": {
        "type": "text",
        "text": "Select Loan Type"
    },
    "body": {
        "text": "Choose the type of loan you're interested in:"
    },
    "footer": {
        "text": "HOM-i Loans"
    },
    "action": {
        "button": "View Options",
        "sections": [
            {
                "title": "Loan Types",
                "rows": [
                    {
                        "id": "home_loan",
                        "title": "Home Loan",
                        "description": "Buy your dream home"
                    },
                    {
                        "id": "lap",
                        "title": "Loan Against Property",
                        "description": "Unlock property value"
                    }
                ]
            }
        ]
    }
}
```

#### 6. Send Location Message
```http
POST /api_v1/gupshup/send-location
Content-Type: application/json

{
    "phone_number": "788888888",
    "latitude": 28.6139,
    "longitude": 77.2090,
    "name": "HOM-i Office",
    "address": "New Delhi, India"
}
```

#### 7. Send Contact Message
```http
POST /api_v1/gupshup/send-contact
Content-Type: application/json

{
    "phone_number": "788888888",
    "contacts": [
        {
            "name": {
                "formatted_name": "HOM-i Support",
                "first_name": "HOM-i"
            },
            "phones": [
                {
                    "phone": "+919876543210",
                    "type": "MAIN"
                }
            ]
        }
    ]
}
```

#### 8. Send Bulk Messages
```http
POST /api_v1/gupshup/send-bulk
Content-Type: application/json

{
    "phone_numbers": ["788888888", "799999999", "777777777"],
    "message_type": "text",
    "message_data": {
        "message": "Welcome to HOM-i! Your loan application is being processed."
    },
    "delay_between_messages": 5
}
```

**Bulk Message Types:**
- `text` - Simple text messages
- `template` - Template-based messages
- `media` - Media messages

#### 9. Check Message Status
```http
GET /api_v1/gupshup/message-status/{message_id}
```

#### 10. Get Available Templates
```http
GET /api_v1/gupshup/templates
```

**Response:**
```json
{
    "success": true,
    "message": "Templates retrieved successfully",
    "templates": [
        {
            "id": "otp_template_id",
            "name": "OTP Template",
            "category": "AUTHENTICATION",
            "status": "APPROVED"
        }
    ]
}
```

#### 11. Health Check
```http
GET /api_v1/gupshup/health
```

**Response:**
```json
{
    "success": true,
    "message": "Gupshup API is accessible",
    "status_code": 202,
    "api_url": "https://api.gupshup.io/wa/api/v1/msg",
    "source_configured": true,
    "api_key_configured": true
}
```

#### Legacy Compatibility Endpoints

The API maintains backward compatibility with existing endpoints:

#### Send OTP (Legacy)
```http
POST /api_v1/gupshup/send-otp
Content-Type: application/json

{
    "phone_number": "788888888"
}
```

#### Send Lead Confirmation (Legacy)
```http
POST /api_v1/gupshup/send-lead-confirmation
Content-Type: application/json

{
    "customer_name": "John Doe",
    "loan_type": "HL",
    "basic_application_id": "APP123456",
    "phone_number": "788888888"
}
```

#### Send Status Update (Legacy)
```http
POST /api_v1/gupshup/send-status-update
Content-Type: application/json

{
    "phone_number": "788888888",
    "name": "John Doe",
    "status": "Under Review"
}
```

### WhatsApp Message Storage

All WhatsApp messages with valid mobile numbers are automatically saved to the Supabase database for audit trails and analytics. Messages with None or empty mobile numbers are skipped to prevent invalid data storage.

#### Message Storage Endpoints

**Get All Messages:**
```http
GET /api_v1/whatsapp/messages?limit=50&direction=inbound
```

**Get Message Statistics:**
```http
GET /api_v1/whatsapp/messages/stats
```

**Get Messages by Mobile Number:**
```http
GET /api_v1/whatsapp/messages/9876543210?limit=20
```

**Response Format:**
```json
{
    "success": true,
    "messages": [
        {
            "id": 1,
            "mobile_number": "9876543210",
            "sender_name": "John Doe",
            "message_text": "Check my application status",
            "direction": "inbound",
            "timestamp": "2024-01-15T10:30:00Z",
            "processed": true,
            "processing_result": {
                "status": "success",
                "application_status": "Under Review"
            }
        }
    ],
    "count": 1
}
```

### Email Processing & Disbursements

#### 1. Process Historical Disbursements
```http
POST /api_v1/historical_disbursements
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "app_password",
    "folder": "INBOX",
    "limit": 100,
    "days_back": 30,
    "include_attachments": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "Historical disbursements processed successfully",
    "summary": {
        "total_emails": 45,
        "processed_emails": 42,
        "disbursement_emails": 15,
        "google_sheets_updates": 15,
        "processing_time": "2.5 minutes"
    }
}
```

#### 2. Start Live Disbursement Monitoring
```http
POST /api_v1/live_disbursements
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "app_password",
    "folder": "INBOX",
    "check_interval": 60,
    "include_attachments": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "Live disbursement monitoring started",
    "monitoring": {
        "status": "active",
        "check_interval": 60,
        "last_check": "2024-01-15T10:30:00Z"
    }
}
```

**Features:**
- **AI-powered email analysis** using OpenAI for automatic data extraction
- **Google Sheets integration** for real-time disbursement tracking
- **Attachment processing** for PDF and document analysis
- **Intelligent email filtering** to identify disbursement-related messages
- **Automatic data normalization** and validation
- **Background processing** for live monitoring
- **Comprehensive logging** and error handling

#### 3. Live Disbursements Health Check (Dedicated Endpoint)
```http
GET /api_v1/live_disbursements_health
```

**Note:** This endpoint provides the same health check as included in the main `/api_v1/health` endpoint. Use this if you only need live disbursements health status.

**Response:** Same format as the `live_disbursements` section in the main health endpoint.

**Component Status Values:**
- `healthy`: Component is working correctly
- `unhealthy`: Component has issues but may still function
- `error`: Component encountered an error during health check

### Health Check & Environment Status

#### Comprehensive Health Check
```http
GET /api_v1/health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "service": "HOM-i WhatsApp OTP, Lead Creation & Status API",
    "version": "1.0.0",
    "database_environments": {
        "orbit": {"available": true, "error": null},
        "homfinity": {"available": true, "error": null}
    },
    "environment_config": {
        "default_environment": "orbit",
        "orbit_configured": true,
        "homfinity_configured": true,
        "orbit_client_initialized": true,
        "homfinity_client_initialized": true,
        "table_environment_mapping": {
            "leads": "orbit",
            "appointments": "orbit",
            "disbursements": "orbit",
            "whatsapp_messages": "orbit",
            "otp_storage": "homfinity"
        }
    },
    "live_disbursements": {
        "overall_status": "healthy",
        "components": {
            "database": {
                "status": "healthy",
                "details": {
                    "orbit_available": true,
                    "homfinity_available": true,
                    "default_client_available": true,
                    "default_environment": "orbit"
                }
            },
            "email_client": {
                "status": "healthy",
                "details": {
                    "gmail_available": false,
                    "zoho_available": true
                }
            },
            "ai_analyzer": {
                "status": "healthy",
                "details": {
                    "configured": true,
                    "model": "gpt-4",
                    "client_initialized": true
                }
            },
            "basic_application_service": {
                "status": "healthy",
                "details": {
                    "api_url_configured": true,
                    "user_id_configured": true,
                    "api_key_configured": true,
                    "agent_user_id_configured": true,
                    "agent_api_key_configured": true
                }
            },
            "monitoring": {
                "status": "healthy",
                "details": {
                    "is_running": false,
                    "started_at": null,
                    "last_check": null,
                    "thread_alive": false,
                    "emails_processed": 0,
                    "disbursements_found": 0,
                    "error_count": 0
                }
            }
        }
    }
}
```

**Status Codes:**
- **200**: Service is healthy or degraded (some components may be unhealthy)
- **503**: Service is unhealthy (critical components are down)

**Note:** The main health endpoint (`/api_v1/health`) now includes comprehensive health checks for live disbursements service. You can also use the dedicated endpoint (`/api_v1/live_disbursements_health`) for live disbursements-specific health checks.

### Multi-Environment Database Operations

All database operations support environment specification:

#### Automatic Environment Selection (Recommended)
```python
# System automatically chooses the correct environment
database_service.save_lead_data(request_data, fbb_response, self_fullfilment_response)
database_service.get_leads_by_mobile("9876543210")
```

#### Explicit Environment Selection
```python
# Force specific environment
database_service.save_lead_data(request_data, fbb_response, self_fullfilment_response, environment="orbit")
database_service.get_leads_by_mobile("9876543210", environment="homfinity")
```

#### Environment Validation
```python
# Check environment status
status = database_service.validate_environments()
env_info = database_service.get_environment_info()
```

## Loan Type Mapping

The API supports various loan types with automatic mapping to Basic Application API codes:

| Input Loan Type | Mapped Code | Description |
|----------------|-------------|-------------|
| `home_loan`, `Home Loan`, `HOME LOAN` | `HL` | Home Loan |
| `loan_against_property`, `Loan Against Property`, `LAP` | `LAP` | Loan Against Property |
| `personal_loan` | `PL` | Personal Loan |
| `business_loan` | `BL` | Business Loan |
| `car_loan` | `CL` | Car Loan |
| `education_loan` | `EL` | Education Loan |

## Error Handling

The API returns appropriate HTTP status codes for different scenarios:

- **200**: Success
- **400**: Bad Request (invalid data, missing parameters)
- **404**: Not Found (OTP not found, lead not found)
- **409**: Conflict (OTP already sent)
- **422**: Validation Error (invalid format)
- **500**: Internal Server Error

### Error Response Format
```json
{
    "success": false,
    "message": "Error description",
    "data": {
        "phone_number": "788888888",
        "error": "Additional error details"
    }
}
```

## Database Setup

### WhatsApp Messages Table

To enable WhatsApp message storage, run the following SQL script in your Supabase SQL editor:

```sql
-- Run database_setup/whatsapp_messages_table.sql
```

This creates:
- `whatsapp_messages` table for storing all messages
- Indexes for better performance
- Functions for message statistics
- Views for recent messages

### Required Tables

1. **OTP Storage**: `database_setup/supabase_setup.sql`
2. **Leads Management**: `database_setup/supabase_setup.sql`
3. **WhatsApp Messages**: `database_setup/whatsapp_messages_table.sql`

## Troubleshooting

### Common Issues

1. **Supabase Connection Error**
   ```
   Error: 'str' object has no attribute 'headers'
   ```
   **Solution**: Check your Supabase credentials in `.env` file

2. **Supabase Permission Error**
   ```
   Error: permission denied for table otp_storage
   ```
   **Solution**: Run the database setup scripts and grant proper permissions

3. **WhatsApp API Error**
   ```
   Error: Failed to send OTP. Status: 400
   ```
   **Solution**: Verify Gupshup API credentials and template configuration

4. **Basic Application API Error**
   ```
   Error: Failed to create lead in Basic Application API
   ```
   **Solution**: Check Basic Application API credentials and URL

### Debug Endpoints

- **Comprehensive Health Check**: `GET /api_v1/health` - Overall API health status including database environments, live disbursements service, and all dependencies
- **Live Disbursements Health Check**: `GET /api_v1/live_disbursements_health` - Dedicated endpoint for live disbursements service health (also included in main health endpoint)
- **WhatsApp Service**: Check logs for WhatsApp service initialization
- **Database Service**: Check logs for database connection status

### Environment Variables Checklist

Ensure all required environment variables are set:

- [ ] `BASIC_APPLICATION_API_URL`
- [ ] `BASIC_APPLICATION_USER_ID`
- [ ] `BASIC_APPLICATION_API_KEY`
- [ ] `GUPSHUP_API_KEY`
- [ ] `GUPSHUP_SOURCE`
- [ ] `GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID`
- [ ] `GUPSHUP_LEAD_CREATION_TEMPLATE_ID`
- [ ] `GUPSHUP_LEAD_STATUS_TEMPLATE_ID`
- [ ] `SUPABASE_URL` (optional)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` (optional)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above 