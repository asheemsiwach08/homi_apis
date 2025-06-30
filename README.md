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

## Prerequisites

- Python 3.8+
- Gupshup WhatsApp API account
- Supabase account and project (optional - falls back to local storage)

## Installation

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
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### 1. Send OTP
**POST** `/send-otp`

Send OTP to a phone number via WhatsApp.

**Request Body:**
```json
{
  "phone_number": "+1234567890"
}
```

**Response:**
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

### 2. Resend OTP
**POST** `/resend-otp`

Resend OTP to a phone number (generates new OTP).

**Request Body:**
```json
{
  "phone_number": "+1234567890"
}
```

**Response:**
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

### 3. Verify OTP
**POST** `/verify-otp`

Verify the OTP sent to a phone number.

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP verified successfully",
  "data": {
    "phone_number": "+1234567890"
  }
}
```

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
**GET** `/debug/whatsapp`

Check WhatsApp service configuration.

**GET** `/debug/test-request`

Show the exact request format being sent to Gupshup.

## API Documentation

Once the server is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Usage Examples

### Using curl

1. **Send OTP:**
   ```bash
   curl -X POST "http://localhost:8000/send-otp" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+1234567890"}'
   ```

2. **Resend OTP:**
   ```bash
   curl -X POST "http://localhost:8000/resend-otp" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+1234567890"}'
   ```

3. **Verify OTP:**
   ```bash
   curl -X POST "http://localhost:8000/verify-otp" \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+1234567890", "otp": "123456"}'
   ```

### Using Python requests

```python
import requests

# Send OTP
response = requests.post("http://localhost:8000/send-otp", 
                        json={"phone_number": "+1234567890"})
print(response.json())

# Verify OTP
response = requests.post("http://localhost:8000/verify-otp", 
                        json={"phone_number": "+1234567890", "otp": "123456"})
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
├── .gitignore           # Git ignore rules
├── .cursorrules         # Cursor editor rules
└── README.md           # Project documentation
```

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

The API includes comprehensive error handling:

- **Invalid phone number format**: Returns 400 Bad Request
- **OTP not found/expired**: Returns appropriate error message
- **Invalid OTP**: Returns error message
- **API failures**: Returns detailed error information
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

### Quick Debug Steps
1. **Check configuration**: `curl http://localhost:8000/debug/whatsapp`
2. **Check request format**: `curl http://localhost:8000/debug/test-request`
3. **Run test script**: `python test_api.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 