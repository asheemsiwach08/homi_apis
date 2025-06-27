# WhatsApp OTP Verification API

A FastAPI-based REST API for sending, resending, and verifying WhatsApp OTP using the Gupshup API. The OTP is valid for 3 minutes and uses local in-memory storage.

## Features

- ✅ Send OTP via WhatsApp
- ✅ Resend OTP functionality
- ✅ Verify OTP with 3-minute expiry
- ✅ Local in-memory OTP storage
- ✅ Phone number validation
- ✅ Comprehensive error handling
- ✅ Async/await support
- ✅ Environment variable configuration

## Prerequisites

- Python 3.8+
- Gupshup WhatsApp API account

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

   # OTP Configuration
   OTP_EXPIRY_MINUTES=3
   ```

4. **Run the application**
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
    "phone_number": "+1234567890"
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
    "phone_number": "+1234567890"
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

## Project Structure

```
otpVerification/
├── main.py              # FastAPI application and endpoints
├── config.py            # Configuration and environment variables
├── database.py          # Local OTP storage implementation
├── whatsapp_service.py  # Gupshup API integration
├── models.py            # Pydantic models for validation
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables template
└── README.md           # Project documentation
```

## Storage Solution

The API uses **local in-memory storage** for OTP management:

- ✅ **Automatic expiry** - OTPs expire after 3 minutes
- ✅ **Thread-safe** - Uses locks for concurrent access
- ✅ **No external dependencies** - No database setup required
- ✅ **Fast performance** - In-memory operations
- ✅ **Automatic cleanup** - Expired OTPs are removed automatically

**Note**: OTPs are stored in memory and will be lost if the server restarts. For production use with multiple server instances, consider using Redis or a database.

## Error Handling

The API includes comprehensive error handling:

- **Invalid phone number format**: Returns 400 Bad Request
- **OTP not found/expired**: Returns appropriate error message
- **Invalid OTP**: Returns error message
- **API failures**: Returns detailed error information
- **Network issues**: Handles timeouts and connection errors

## Security Considerations

- OTPs are stored in memory with automatic expiry
- OTPs are deleted after successful verification
- Phone number validation is implemented
- Environment variables for sensitive configuration
- No OTP logging for security
- Thread-safe operations for concurrent access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 