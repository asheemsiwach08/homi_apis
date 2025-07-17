# WhatsApp Webhook Setup Guide

This guide explains how to set up automatic WhatsApp message processing for application status checks.

## How It Works

1. **User sends WhatsApp message** to your business number
2. **Gupshup receives the message** and forwards it to your webhook
3. **Your API processes the message** automatically
4. **API sends response back** via WhatsApp to the user

## Setup Steps

### 1. Configure Gupshup Webhook

#### A. Log into Gupshup Dashboard
- Go to [Gupshup Dashboard](https://www.gupshup.io/)
- Navigate to your WhatsApp Business API account

#### B. Set Webhook URL
- Go to **Webhook Configuration**
- Set your webhook URL: `https://your-domain.com/api_v1/whatsapp/webhook`
- Set webhook method to **POST**
- Enable webhook for incoming messages

#### C. Configure Webhook Parameters
Gupshup will send the following parameters to your webhook:
- `payload`: Encoded message payload
- `mobile`: Sender's phone number
- `name`: Sender's name (if available)
- `message`: Decoded message text
- `channel`: Channel type (whatsapp)
- `timestamp`: Message timestamp

### 2. Deploy Your API

#### A. Local Development
```bash
# Start your API server
python -m app.main
# or
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

#### B. Production Deployment
```bash
# Using Docker
docker-compose -f docker-compose.prod.yml up --build -d

# Using direct deployment
python -m app.main
```

### 3. Test the Webhook

#### A. Test with ngrok (for local development)
```bash
# Install ngrok
npm install -g ngrok

# Create tunnel to your local server
ngrok http 5000

# Use the ngrok URL in Gupshup webhook configuration
# Example: https://abc123.ngrok.io/api_v1/whatsapp/webhook
```

#### B. Test Message Processing
Send these test messages to your WhatsApp business number:

1. **Status check with phone number:**
   ```
   Check my application status. My mobile number is 9876543210
   ```

2. **Status check with application ID:**
   ```
   Please check my application status. Application ID: APP123456
   ```

3. **Simple status check:**
   ```
   I want to check my application status
   ```

4. **Non-status message:**
   ```
   Hello, how are you?
   ```

## Message Processing Logic

### Status Check Detection
The API detects status check requests using these keywords:
- "check my application status"
- "application status"
- "loan status"
- "status check"
- "track application"
- "application tracking"
- "loan application status"
- "check status"
- "my application"
- "loan details"

### Phone Number Extraction
The API extracts phone numbers from messages using these patterns:
- 10-digit numbers: `9876543210`
- 12-digit numbers with country code: `919876543210`
- Numbers with + prefix: `+919876543210`
- Formatted numbers: `987-654-3210`, `987.654.3210`

### Application ID Extraction
The API looks for application IDs using patterns like:
- "application id: APP123456"
- "app id: APP123456"
- "ID: APP123456"
- Any 6+ character alphanumeric string

## API Endpoints

### 1. Webhook Endpoint (Automatic)
```http
POST /api_v1/whatsapp/webhook
Content-Type: application/x-www-form-urlencoded

payload=encoded_payload&mobile=+919876543210&message=Check my status&channel=whatsapp&timestamp=1234567890
```

### 2. Manual Processing Endpoint (Testing)
```http
POST /api_v1/whatsapp/process_message
Content-Type: application/json

{
    "message": "Check my application status. My mobile number is 9876543210"
}
```

### 3. Webhook Verification (WhatsApp Business API)
```http
GET /api_v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=your_token&hub.challenge=challenge_string
```

## Response Flow

### 1. Status Check Request
```
User: "Check my application status. Mobile: 9876543210"
↓
API: Processes message, extracts phone number
↓
API: Calls Basic Application API
↓
API: Sends response via WhatsApp
↓
User: "Your application status is: Under Review"
```

### 2. Non-Status Message
```
User: "Hello, how are you?"
↓
API: Detects non-status message
↓
API: Sends helpful response
↓
User: "Hi! To check your application status, please send a message like 'Check my application status' along with your mobile number."
```

### 3. Error Handling
```
User: "Check my status"
↓
API: No phone number found in message
↓
API: Sends error message
↓
User: "No mobile number found in the message. Please include your mobile number in the message."
```

## Environment Variables

Add these to your `.env` file:

```env
# WhatsApp Webhook Configuration
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_verify_token_here

# Gupshup Configuration (already configured)
GUPSHUP_API_KEY=your_gupshup_api_key
GUPSHUP_SOURCE=your_source_number
GUPSHUP_API_URL=https://api.gupshup.io/wa/api/v1/template/msg

# Basic Application API (already configured)
BASIC_APPLICATION_API_URL=your_basic_api_url
BASIC_APPLICATION_USER_ID=your_user_id
BASIC_APPLICATION_API_KEY=your_api_key
```

## Troubleshooting

### Common Issues

1. **Webhook not receiving messages**
   - Check if your server is accessible from the internet
   - Verify webhook URL in Gupshup dashboard
   - Check server logs for incoming requests

2. **Messages not being processed**
   - Check if the message contains status check keywords
   - Verify phone number extraction logic
   - Check Basic Application API connectivity

3. **Responses not being sent**
   - Verify Gupshup API credentials
   - Check WhatsApp template configurations
   - Monitor API response logs

### Debug Logs

The API logs important events:
```
Received WhatsApp message from +919876543210: Check my application status
Phone number extracted: 9876543210
Status check request detected
Calling Basic Application API...
Status received: Under Review
Sending WhatsApp response...
```

### Testing Commands

```bash
# Test webhook locally with curl
curl -X POST "http://localhost:5000/api_v1/whatsapp/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "payload=test&mobile=+919876543210&message=Check my application status&channel=whatsapp&timestamp=1234567890"

# Test manual processing
curl -X POST "http://localhost:5000/api_v1/whatsapp/process_message" \
  -H "Content-Type: application/json" \
  -d '{"message": "Check my application status. Mobile: 9876543210"}'
```

## Security Considerations

1. **Webhook Verification**: Implement proper verification tokens
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **Input Validation**: Validate all incoming webhook data
4. **HTTPS**: Use HTTPS in production for secure communication
5. **IP Whitelisting**: Consider whitelisting Gupshup IP addresses

## Monitoring

Monitor these metrics:
- Webhook request volume
- Message processing success rate
- Response time
- Error rates
- User engagement patterns

## Support

For issues with:
- **Gupshup Integration**: Contact Gupshup support
- **API Functionality**: Check server logs and error messages
- **Basic Application API**: Verify API credentials and connectivity 