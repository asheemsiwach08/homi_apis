# HOM-i WhatsApp OTP, Lead Creation & Status API

A comprehensive FastAPI-based REST API for WhatsApp OTP verification, lead creation, and status tracking using Gupshup API with Supabase PostgreSQL storage and automatic fallback to local storage.

## Features

- ✅ **WhatsApp OTP Management**
  - Send OTP via WhatsApp using Gupshup API
  - Resend OTP functionality
  - Verify OTP with 3-minute expiry
  - Phone number validation and normalization
- ✅ **Lead Management**
  - Create leads with Basic Application API integration
  - Track lead status by mobile number or application ID
  - Comprehensive lead data validation
- ✅ **WhatsApp Notifications**
  - Lead creation confirmation messages
  - Lead status update notifications
  - Multiple template support for different use cases
- ✅ **Storage & Infrastructure**
  - Supabase PostgreSQL for persistent storage
  - Automatic fallback to local storage
  - Thread-safe operations
  - Audit trails and data retention
- ✅ **API Features**
  - RESTful API design with proper HTTP status codes
  - Comprehensive error handling
  - Async/await support
  - Environment variable configuration
  - Debug endpoints for troubleshooting
- ✅ **Development & Deployment**
  - Modular project structure
  - Docker support with multi-stage builds
  - Docker Compose for easy deployment
  - Comprehensive testing support

## Project Structure

```
otpVerification/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # Main API router
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── otp.py          # OTP-related endpoints
│   │       ├── leads.py        # Lead management endpoints
│   │       └── health.py       # Health check endpoint
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

   # Gupshup WhatsApp API Configuration
   GUPSHUP_API_KEY=your_gupshup_api_key
   GUPSHUP_SOURCE=your_source_number
   GUPSHUP_API_URL=https://api.gupshup.io/wa/api/v1/template/msg

   # WhatsApp Templates
   GUPSHUP_WHATSAPP_OTP_TEMPLATE_ID=your_otp_template_id
   GUPSHUP_WHATSAPP_OTP_SRC_NAME=HomiAi
   GUPSHUP_LEAD_CREATION_TEMPLATE_ID=your_lead_creation_template_id
   GUPSHUP_LEAD_CREATION_SRC_NAME=your_lead_creation_src_name
   GUPSHUP_LEAD_STATUS_TEMPLATE_ID=your_lead_status_template_id
   GUPSHUP_LEAD_STATUS_SRC_NAME=your_lead_status_src_name

   # Supabase Configuration (Optional - falls back to local storage if not configured)
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

   # OTP Configuration
   OTP_EXPIRY_MINUTES=3
   ```

5. **Set up Supabase (Optional)**
   
   **a. Create a Supabase project:**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note down your project URL and API keys
   
   **b. Create the database tables:**
   - Go to your Supabase dashboard
   - Navigate to SQL Editor
   - Run the SQL scripts from `database_setup/` directory
   
   **c. Get your API keys:**
   - Go to Settings > API
   - Copy your Project URL, anon key, and service_role key

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
   docker build -t homi-api .

   # Run the container
   docker run -d \
     -p 5000:5000 \
     --env-file .env \
     homi-api
   ```

## Phone Number Validation & Normalization

The API automatically normalizes phone numbers to include the country code **91** (India) for WhatsApp services. The system handles various input formats:

### Supported Input Formats:
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
3. **Adds** country code **91** if not present
4. **Removes** leading 0 if present (e.g., 0788888888 → +917888888888)
5. **Returns** normalized format: `+91XXXXXXXXXX`

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

The API uses a sophisticated storage system with the following behavior:

### Storage Solutions
- **Primary**: Supabase PostgreSQL for persistent OTP storage
- **Fallback**: Local in-memory storage if Supabase is unavailable
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

### Database Schema
```sql
CREATE TABLE otp_storage (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    otp VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE
);

CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    basic_application_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255),
    relation_id VARCHAR(255),
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    mobile_number VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    pan_number VARCHAR(10) NOT NULL,
    loan_type VARCHAR(50) NOT NULL,
    loan_amount DECIMAL(15,2) NOT NULL,
    loan_tenure INTEGER NOT NULL,
    gender VARCHAR(10),
    dob DATE,
    pin_code VARCHAR(6) NOT NULL,
    basic_api_response JSONB,
    status VARCHAR(50) DEFAULT 'created',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### OTP Operations

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

#### 1. Create Lead
```http
POST /api_v1/lead_create
Content-Type: application/json

{
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
```

**Response:**
```json
{
    "basic_application_id": "APP123456789",
    "message": "Lead Created Successfully."
}
```

#### 2. Get Lead Status
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

### Health Check

#### Health Status
```http
GET /api_v1/health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z"
}
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

## Testing

### Test OTP Operations
```bash
# Test OTP send
curl -X POST "http://localhost:5000/api_v1/otp_send" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "788888888"}'

# Test OTP verify
curl -X POST "http://localhost:5000/api_v1/otp_verify" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "788888888", "otp": "123456"}'
```

### Test Lead Operations
```bash
# Test lead creation
curl -X POST "http://localhost:5000/api_v1/lead_create" \
  -H "Content-Type: application/json" \
  -d '{
    "loan_type": "home_loan",
    "loan_amount": 5000000,
    "loan_tenure": 20,
    "pan_number": "ABCDE1234F",
    "first_name": "John",
    "last_name": "Doe",
    "mobile_number": "788888888",
    "email": "john.doe@example.com",
    "dob": "15/06/1990",
    "pin_code": "400001"
  }'

# Test lead status
curl -X POST "http://localhost:5000/api_v1/lead_status" \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "788888888"}'
```

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

- **Health Check**: `GET /api_v1/health`
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