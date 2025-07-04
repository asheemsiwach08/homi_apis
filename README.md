# WhatsApp OTP Verification API

A FastAPI-based REST API for sending, resending, and verifying WhatsApp OTP using the Gupshup API. The OTP is valid for 3 minutes and uses Supabase PostgreSQL for storage with automatic fallback to local storage.

## Features

- ✅ Send OTP via WhatsApp using Gupshup API
- ✅ Resend OTP functionality
- ✅ Verify OTP with 3-minute expiry
- ✅ Supabase PostgreSQL OTP storage
- ✅ Automatic fallback to local storage
- ✅ Phone number validation
- ✅ Comprehensive error handling
- ✅ Async/await support
- ✅ Environment variable configuration
- ✅ Debug endpoints for troubleshooting
- ✅ Test script included
- ✅ Docker support with multi-stage builds
- ✅ Docker Compose for easy deployment
- ✅ Organized API routes with /otp prefix

## Prerequisites

- Python 3.8+ (for local development)
- Docker & Docker Compose (for containerized deployment)
- Gupshup WhatsApp API account
- Supabase account and project (optional - falls back to local storage)

## Installation

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd otpVerification
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` file with your configuration:
   ```env
   # Gupshup WhatsApp API Configuration
   GUPSHUP_API_KEY=your_api_key_here
   GUPSHUP_SOURCE=your_source_number
   GUPSHUP_TEMPLATE_ID=your_template_id
   GUPSHUP_SRC_NAME=your_src_name
   GUPSHUP_API_URL=https://api.gupshup.io/wa/api/v1/template/msg

   # Supabase Configuration (Optional - falls back to local storage if not configured)
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

   # OTP Configuration
   OTP_EXPIRY_MINUTES=3
   ```

4. **Set up Supabase (Optional)**
   
   **a. Create a Supabase project:**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Note down your project URL and API keys
   
   **b. Create the database table:**
   - Go to your Supabase dashboard
   - Navigate to SQL Editor
   - Run the SQL script from `supabase_setup.sql`
   
   **c. Get your API keys:**
   - Go to Settings > API
   - Copy your Project URL, anon key, and service_role key

5. **Run the application**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 5000 --reload
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
   docker build -t whatsapp-otp-api .

   # Run the container
   docker run -d \
     -p 5000:5000 \
     --env-file .env \
     whatsapp-otp-api
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
```

## API Endpoints

### 1. Send OTP
**POST** `/otp/send`

Send OTP to a phone number via WhatsApp.

**Request Body:**
```json
{
  "phone_number": "+1234567890"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "OTP sent successfully",
  "data": {
    "phone_number": "+1234567890",
    "otp": "123456"
  }
}
```

**Error Responses:**
- **400 Bad Request** - Invalid phone number format
- **409 Conflict** - OTP already sent (use resend endpoint)
- **500 Internal Server Error** - WhatsApp service failure

### 2. Resend OTP
**POST** `/otp/resend`

Resend OTP to a phone number (generates new OTP).

**Request Body:**
```json
{
  "phone_number": "+1234567890"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "OTP resent successfully",
  "data": {
    "phone_number": "+1234567890",
    "otp": "123456"
  }
}
```

**Error Responses:**
- **400 Bad Request** - Invalid phone number format
- **500 Internal Server Error** - WhatsApp service failure

### 3. Verify OTP
**POST** `/otp/verify`

Verify the OTP sent to a phone number. **Note**: After successful verification, the OTP is marked as used in the database instead of being deleted, allowing for audit trails and analytics.

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "data": {
    "phone_number": "+1234567890"
  }
}
```

**Error Responses:**
- **400 Bad Request** - Invalid phone number format or invalid OTP
- **404 Not Found** - OTP not found or expired

### 4. Health Check
**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "WhatsApp OTP API is running"
}
```

### 5. Debug Endpoints

#### Debug WhatsApp Configuration
**GET** `/debug/whatsapp`

Check WhatsApp service configuration (API keys, URLs, etc.).

**Response:**
```json
{
  "api_url": "https://api.gupshup.io/wa/api/v1/template/msg",
  "api_key": "your_api_key...",
  "source": "your_source_number",
  "template_id": "your_template_id",
  "src_name": "your_src_name",
  "config_source": "Environment variables loaded successfully"
}
```

#### Debug Test Request
**GET** `/debug/test-request`

Show what request would be sent to Gupshup API.

**Response:**
```json
{
  "api_url": "https://api.gupshup.io/wa/api/v1/template/msg",
  "headers": {...},
  "data": {...},
  "note": "This shows the exact request that would be sent to Gupshup"
}
```

#### Debug Phone Number Normalization
**GET** `/debug/phone-normalization`

Test phone number normalization with various input formats.

**Response:**
```json
{
  "phone_number_normalization_test": [
    {
      "original": "917888888888",
      "normalized": "+917888888888",
      "is_valid": true
    },
    {
      "original": "788888888",
      "normalized": "+917888888888",
      "is_valid": true
    },
    {
      "original": "+917888888888",
      "normalized": "+917888888888",
      "is_valid": true
    }
  ],
  "note": "This shows how different phone number formats are normalized to +91 format"
}
```

## API Documentation

Once the server is running, you can access:
- **Interactive API docs**: http://localhost:5000/docs
- **ReDoc documentation**: http://localhost:5000/redoc

## Usage Examples

### Using curl

1. **Send OTP (various phone number formats):**
   ```bash
   # With country code
   curl -X POST "http://localhost:5000/otp/send" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "917888888888"}'
   
   # Without country code (will be normalized to +91)
   curl -X POST "http://localhost:5000/otp/send" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "788888888"}'
   
   # With + prefix
   curl -X POST "http://localhost:5000/otp/send" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+917888888888"}'
   
   # With leading 0
   curl -X POST "http://localhost:5000/otp/send" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "0788888888"}'
   ```

2. **Resend OTP:**
   ```bash
   curl -X POST "http://localhost:5000/otp/resend" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "788888888"}'
   ```

3. **Verify OTP:**
   ```bash
   curl -X POST "http://localhost:5000/otp/verify" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "788888888", "otp": "123456"}'
   ```

4. **Test with invalid phone number:**
   ```bash
   curl -X POST "http://localhost:5000/otp/send" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "0123456789"}' \
        -w "\nHTTP Status: %{http_code}\n"
   ```

5. **Test with expired OTP:**
   ```bash
   curl -X POST "http://localhost:5000/otp/verify" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+1234567890", "otp": "999999"}' \
        -w "\nHTTP Status: %{http_code}\n"
   ```

### Using Python requests

```python
import requests

# Send OTP (various formats supported)
phone_numbers = [
    "917888888888",    # With country code
    "788888888",       # Without country code (normalized to +91)
    "+917888888888",   # With + prefix
    "0788888888"       # With leading 0
]

for phone in phone_numbers:
    response = requests.post("http://localhost:5000/otp/send", 
                            json={"phone_number": phone})
    print(f"Phone: {phone} -> Response: {response.json()}")

# Verify OTP
response = requests.post("http://localhost:5000/otp/verify", 
                        json={"phone_number": "788888888", "otp": "123456"})
print(response.json())
```

### Using the Test Script

```bash
python test_api.py
```

## Project Structure

```
otpVerification/
├── main.py              # FastAPI application and endpoints
├── config.py            # Configuration and environment variables
├── database.py          # Supabase/local OTP storage implementation
├── whatsapp_service.py  # Gupshup API integration
├── models.py            # Pydantic models for validation
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables template
├── supabase_setup.sql   # Supabase table creation script
├── test_api.py          # Test script for API endpoints
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose for development
├── docker-compose.prod.yml # Docker Compose for production
├── .dockerignore        # Docker ignore rules
├── .gitignore           # Git ignore rules
├── .cursorrules         # Cursor editor rules
└── README.md           # Project documentation
```

## Docker Features

### Dockerfile
- **Multi-stage build** for optimized image size
- **Security-focused** with non-root user
- **Python 3.11** slim base image
- **System dependencies** for PostgreSQL support

### Docker Compose
- **Development setup** with hot reload
- **Production setup** with security hardening
- **Environment variable management**
- **Volume mounting** for logs
- **Network isolation**
- **Resource limits** (production)

### Security Features
- **Non-root user** execution
- **Read-only filesystem** (production)
- **No new privileges** security option
- **Temporary filesystem** for /tmp
- **Resource limits** to prevent abuse

## Storage Solution

The API uses **Supabase PostgreSQL** for OTP management with automatic fallback to local storage:

- ✅ **Persistent storage** - OTPs survive server restarts (Supabase)
- ✅ **Automatic fallback** - Falls back to local storage if Supabase unavailable
- ✅ **Automatic expiry** - OTPs expire after 3 minutes
- ✅ **Scalable** - Supports multiple server instances
- ✅ **Secure** - Row-level security and proper authentication
- ✅ **Automatic cleanup** - Expired OTPs are marked as used
- ✅ **Thread-safe** - Local storage uses locks for concurrent access

### Database Schema (Supabase)

```sql
CREATE TABLE otp_storage (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    otp VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE
);
```

## Error Handling

The API includes comprehensive error handling with proper HTTP status codes:

### HTTP Status Codes
- **200 OK** - Successful operations
- **400 Bad Request** - Invalid phone number format, invalid OTP
- **404 Not Found** - OTP not found or expired
- **409 Conflict** - OTP already sent (use resend endpoint)
- **500 Internal Server Error** - WhatsApp service failure, server errors

### Error Response Format
```json
{
  "detail": {
    "success": false,
    "message": "Error description",
    "data": {
      "phone_number": "+1234567890",
      "additional_info": "..."
    }
  }
}
```

### Common Error Scenarios
- **Invalid phone number format**: Returns 400 Bad Request
- **OTP not found/expired**: Returns 404 Not Found
- **Invalid OTP**: Returns 400 Bad Request
- **OTP already exists**: Returns 409 Conflict
- **WhatsApp service failure**: Returns 500 Internal Server Error
- **Network issues**: Handles timeouts and connection errors
- **Database errors**: Graceful fallback to local storage
- **Gupshup API errors**: Proper status code handling (202 = success)

## Security Considerations

- OTPs are stored securely in Supabase PostgreSQL or local memory
- OTPs are automatically marked as used after expiry
- Phone number validation is implemented
- Environment variables for sensitive configuration
- No OTP logging for security
- Row-level security support in Supabase
- Service role authentication for database access
- Thread-safe operations for concurrent access
- Docker security hardening in production

## Troubleshooting

### Supabase Connection Issues
1. **Check API keys**: Verify your Supabase URL and service role key
2. **Check table**: Ensure the `otp_storage` table exists (run `supabase_setup.sql`)
3. **Check permissions**: Verify service role has proper permissions
4. **Fallback**: The system will automatically fall back to local storage

### WhatsApp Delivery Issues
1. **Check Gupshup configuration**: Verify API key and template ID
2. **Check phone number**: Ensure correct international format
3. **Check template approval**: Verify template is approved by WhatsApp
4. **Check account status**: Ensure Gupshup account is active
5. **Status 202**: This is normal - means message is queued for delivery

### Docker Issues
1. **Build errors**: Check Dockerfile and requirements.txt
2. **Environment variables**: Ensure .env file is properly configured
3. **Port conflicts**: Change port mapping if 5000 is in use
4. **Container logs**: Check logs with `docker logs <container_id>`

### Quick Debug Steps
1. **Check configuration**: `curl http://localhost:5000/debug/whatsapp`
2. **Check request format**: `curl http://localhost:5000/debug/test-request`
3. **Run test script**: `python test_api.py`
4. **Check Docker logs**: `docker logs <container_id>`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 