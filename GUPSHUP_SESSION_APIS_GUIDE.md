# Gupshup Session Message APIs Guide

## Overview

This document provides a comprehensive guide to all the session-bound message APIs available in the HOM-i WhatsApp integration. Session messages are sent during an active conversation window (24 hours after user interaction) and don't require templates.

## Available Session Message APIs

### 1. Text Messages
**Endpoint:** `POST /api_v1/gupshup/session/text`

Send simple text messages during an active session.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "message": "Hello! How can I help you today?"
}
```

### 2. Image Messages
**Endpoint:** `POST /api_v1/gupshup/session/image`

Send image messages with optional captions.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "image_url": "https://example.com/image.jpg",
  "caption": "Here's your loan approval document"
}
```

### 3. Document Messages
**Endpoint:** `POST /api_v1/gupshup/session/document`

Send document files (PDF, DOC, etc.) with filename and optional caption.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "document_url": "https://example.com/loan-agreement.pdf",
  "filename": "Loan_Agreement.pdf",
  "caption": "Please review and sign this document"
}
```

### 4. Audio Messages
**Endpoint:** `POST /api_v1/gupshup/session/audio`

Send audio files in various formats.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "audio_url": "https://example.com/voice-message.mp3"
}
```

### 5. Video Messages
**Endpoint:** `POST /api_v1/gupshup/session/video`

Send video files with optional captions.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "video_url": "https://example.com/tutorial.mp4",
  "caption": "Watch this tutorial for loan application process"
}
```

### 6. Sticker Messages
**Endpoint:** `POST /api_v1/gupshup/session/sticker`

Send sticker files (WebP format recommended).

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "sticker_url": "https://example.com/celebration.webp"
}
```

### 7. Reaction Messages
**Endpoint:** `POST /api_v1/gupshup/session/reaction`

React to a specific message with an emoji.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "message_id": "wamid.HBgNOTE1NTc5MTc2ODQ=",
  "emoji": "👍"
}
```

### 8. Location Messages
**Endpoint:** `POST /api_v1/gupshup/session/location`

Share location with coordinates and optional details.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "name": "Our Office",
  "address": "New Delhi, India"
}
```

### 9. List Messages
**Endpoint:** `POST /api_v1/gupshup/session/list`

Send interactive list messages with multiple sections and options.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "header": "Loan Options",
  "body": "Choose from our available loan products:",
  "footer": "Select an option to continue",
  "button_text": "View Options",
  "sections": [
    {
      "title": "Home Loans",
      "rows": [
        {
          "id": "home_loan_basic",
          "title": "Basic Home Loan",
          "description": "Up to ₹50 Lakhs at 8.5% interest"
        },
        {
          "id": "home_loan_premium",
          "title": "Premium Home Loan",
          "description": "Up to ₹1 Crore at 8.0% interest"
        }
      ]
    },
    {
      "title": "Personal Loans",
      "rows": [
        {
          "id": "personal_loan",
          "title": "Personal Loan",
          "description": "Up to ₹10 Lakhs at 12% interest"
        }
      ]
    }
  ]
}
```

### 10. Quick Replies
**Endpoint:** `POST /api_v1/gupshup/session/quick-replies`

Send messages with quick reply buttons (max 3 buttons).

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "header": "Application Status",
  "body": "Your loan application is under review. What would you like to do?",
  "footer": "Choose an option",
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
        "id": "upload_docs",
        "title": "Upload Documents"
      }
    },
    {
      "type": "reply",
      "reply": {
        "id": "contact_agent",
        "title": "Contact Agent"
      }
    }
  ]
}
```

### 11. Catalog Messages
**Endpoint:** `POST /api_v1/gupshup/session/catalog`

Display product catalogs for browsing.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "header": "Our Loan Products",
  "body": "Browse our complete loan catalog",
  "footer": "Find the perfect loan for you",
  "action": {
    "name": "catalog_message",
    "parameters": {
      "thumbnail_product_retailer_id": "loan_catalog_001"
    }
  }
}
```

### 12. Single Product Messages
**Endpoint:** `POST /api_v1/gupshup/session/single-product`

Display a single product from your catalog.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "header": "Featured Loan",
  "body": "Check out our most popular home loan product",
  "footer": "Apply now for instant approval",
  "product_retailer_id": "home_loan_premium_001"
}
```

### 13. Multi Product Messages
**Endpoint:** `POST /api_v1/gupshup/session/multi-product`

Display multiple products from your catalog.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "header": "Recommended Loans",
  "body": "Based on your profile, here are our recommendations",
  "footer": "Choose the best option for you",
  "catalog_id": "loan_catalog_main",
  "product_sections": [
    {
      "title": "Best Match",
      "product_items": [
        {"product_retailer_id": "home_loan_001"},
        {"product_retailer_id": "home_loan_002"}
      ]
    },
    {
      "title": "Alternative Options",
      "product_items": [
        {"product_retailer_id": "personal_loan_001"}
      ]
    }
  ]
}
```

### 14. CTA (Call-to-Action) Messages
**Endpoint:** `POST /api_v1/gupshup/session/cta`

Send messages with CTA buttons for URLs or phone numbers (max 2 buttons).

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "header": "Complete Your Application",
  "body": "You're almost done! Complete your loan application or call us for assistance.",
  "footer": "We're here to help",
  "buttons": [
    {
      "type": "url",
      "title": "Complete Application",
      "url": "https://basichomeloan.com/complete-application"
    },
    {
      "type": "phone_number",
      "title": "Call Support",
      "phone_number": "+911234567890"
    }
  ]
}
```

## Response Format

All session message APIs return a consistent response format:

```json
{
  "success": true,
  "message": "Message sent successfully",
  "message_id": "wamid.HBgNOTE1NTc5MTc2ODQ=",
  "data": {
    "app_name": "basichomeloan",
    // ... specific message data
  },
  "gupshup_response": {
    // Raw Gupshup API response
  }
}
```

## Error Handling

All APIs include comprehensive error handling:

- **400**: Bad Request (validation errors, limits exceeded)
- **404**: App configuration not found
- **500**: Internal server errors, Gupshup API failures

Example error response:
```json
{
  "detail": "Failed to send message: HTTP 400: Invalid phone number format"
}
```

## App Configuration

All session message APIs require the `app_name` parameter to identify which Gupshup app configuration to use. Make sure you have configured the following environment variables:

```env
# For basichomeloan app
BASICHOMELOAN_GUPSHUP_API_KEY=your_api_key
BASICHOMELOAN_GUPSHUP_APP_ID=your_app_id
BASICHOMELOAN_GUPSHUP_APP_NAME=your_app_name
BASICHOMELOAN_GUPSHUP_SOURCE=your_source_number

# For irabybasic app
IRABYBASIC_GUPSHUP_API_KEY=your_api_key
IRABYBASIC_GUPSHUP_APP_ID=your_app_id
IRABYBASIC_GUPSHUP_APP_NAME=your_app_name
IRABYBASIC_GUPSHUP_SOURCE=your_source_number
```

## Usage Guidelines

1. **Session Window**: Messages can only be sent within 24 hours of the last user interaction
2. **Phone Number Format**: Automatically normalized to include country code (+91)
3. **Media URLs**: Must be publicly accessible HTTPS URLs
4. **File Formats**: 
   - Images: JPG, PNG, GIF
   - Documents: PDF, DOC, DOCX, TXT
   - Audio: MP3, AAC, OGG
   - Video: MP4, 3GP
   - Stickers: WebP (recommended)
5. **Button Limits**: 
   - Quick Replies: Max 3 buttons
   - CTA Messages: Max 2 buttons
6. **List Sections**: Up to 10 sections with 10 rows each

## Testing

You can test these APIs using tools like Postman, curl, or the FastAPI automatic documentation at `/docs` when your server is running.

Example curl command:
```bash
curl -X POST "http://localhost:5000/api_v1/gupshup/session/text" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "basichomeloan",
    "phone_number": "917888888888",
    "message": "Hello from session API!"
  }'
```

## Next Steps

1. Configure your Gupshup app credentials in environment variables
2. Test the APIs with your WhatsApp Business number
3. Integrate the APIs into your application workflow
4. Monitor message delivery using the returned message IDs

For more information about Gupshup WhatsApp Business API, refer to their official documentation.


# Gupshup Template Message APIs Guide

## Overview

This document provides a comprehensive guide to all the template-based message APIs available in the HOM-i WhatsApp integration. Template messages are used for business-initiated conversations and require pre-approved templates from WhatsApp.

## Key Differences: Template vs Session Messages

| Feature | Template Messages | Session Messages |
|---------|-------------------|------------------|
| **Usage** | Business-initiated conversations | Within active conversation window (24h) |
| **Approval** | Requires WhatsApp template approval | No approval needed |
| **Cost** | Usually charged per message | Usually free within session |
| **Flexibility** | Fixed template structure with parameters | Full customization |
| **Use Cases** | Notifications, OTP, Promotions, Updates | Customer service, responses |

## Available Template Message APIs

### 1. Template Text Messages
**Endpoint:** `POST /api_v1/gupshup/template/text`

Send text-based template messages for notifications, updates, or general business communication.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "loan_approval_notification",
  "template_params": ["John Doe", "Home Loan", "₹50,00,000"],
  "source_name": "BasicHomeLoan"
}
```

### 2. Template Image Messages
**Endpoint:** `POST /api_v1/gupshup/template/image`

Send template messages with image headers for visual notifications.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "loan_document_template",
  "template_params": ["John Doe", "Loan Agreement"],
  "image_url": "https://example.com/loan-document-header.jpg",
  "source_name": "BasicHomeLoan"
}
```

### 3. Template Video Messages
**Endpoint:** `POST /api_v1/gupshup/template/video`

Send template messages with video headers for engaging content.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "loan_process_tutorial",
  "template_params": ["John Doe"],
  "video_url": "https://example.com/loan-tutorial.mp4",
  "source_name": "BasicHomeLoan"
}
```

### 4. Template Document Messages
**Endpoint:** `POST /api_v1/gupshup/template/document`

Send template messages with document attachments.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "document_delivery_template",
  "template_params": ["John Doe", "Loan Agreement"],
  "document_url": "https://example.com/loan-agreement.pdf",
  "filename": "Loan_Agreement_JohnDoe.pdf",
  "source_name": "BasicHomeLoan"
}
```

### 5. Template Location Messages
**Endpoint:** `POST /api_v1/gupshup/template/location`

Send template messages with location information.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "branch_location_template",
  "template_params": ["John Doe", "Delhi Branch"],
  "latitude": 28.6139,
  "longitude": 77.2090,
  "name": "BasicHomeLoan Delhi Branch",
  "address": "Connaught Place, New Delhi, India",
  "source_name": "BasicHomeLoan"
}
```

### 6. Template Coupon Messages
**Endpoint:** `POST /api_v1/gupshup/template/coupon`

Send promotional template messages with coupon codes.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "special_offer_coupon",
  "template_params": ["John Doe", "0.5% interest rate reduction"],
  "coupon_code": "SAVE2024",
  "source_name": "BasicHomeLoan"
}
```

### 7. Template Carousel Messages
**Endpoint:** `POST /api_v1/gupshup/template/carousel`

Send template messages with multiple cards in carousel format.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "loan_options_carousel",
  "template_params": ["John Doe"],
  "cards": [
    {
      "card_index": 0,
      "components": [
        {
          "type": "header",
          "parameters": [
            {
              "type": "image",
              "image": {"link": "https://example.com/home-loan.jpg"}
            }
          ]
        },
        {
          "type": "body",
          "parameters": [
            {"type": "text", "text": "Home Loan"},
            {"type": "text", "text": "8.5%"},
            {"type": "text", "text": "₹50 Lakhs"}
          ]
        },
        {
          "type": "button",
          "sub_type": "url",
          "index": "0",
          "parameters": [
            {"type": "text", "text": "Apply Now"}
          ]
        }
      ]
    },
    {
      "card_index": 1,
      "components": [
        {
          "type": "header",
          "parameters": [
            {
              "type": "image",
              "image": {"link": "https://example.com/personal-loan.jpg"}
            }
          ]
        },
        {
          "type": "body",
          "parameters": [
            {"type": "text", "text": "Personal Loan"},
            {"type": "text", "text": "12%"},
            {"type": "text", "text": "₹10 Lakhs"}
          ]
        }
      ]
    }
  ],
  "source_name": "BasicHomeLoan"
}
```

### 8. Template Limited Time Offer (LTO) Messages
**Endpoint:** `POST /api_v1/gupshup/template/lto`

Send time-sensitive promotional template messages.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "limited_time_offer",
  "template_params": ["John Doe", "Special Home Loan Rate", "7.5%"],
  "offer_expiry": "2024-12-31",
  "source_name": "BasicHomeLoan"
}
```

### 9. Template Multi Product Message (MPM)
**Endpoint:** `POST /api_v1/gupshup/template/mpm`

Send template messages showcasing multiple products from your catalog.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "product_showcase_template",
  "template_params": ["John Doe", "Recommended Loans"],
  "catalog_id": "loan_catalog_2024",
  "product_sections": [
    {
      "title": "Best Match",
      "product_retailer_ids": ["home_loan_premium", "home_loan_basic"]
    },
    {
      "title": "Alternative Options",
      "product_retailer_ids": ["personal_loan", "business_loan"]
    }
  ],
  "source_name": "BasicHomeLoan"
}
```

### 10. Template Catalog Messages
**Endpoint:** `POST /api_v1/gupshup/template/catalog`

Send template messages displaying your product catalog.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "catalog_display_template",
  "template_params": ["John Doe", "Our Loan Products"],
  "catalog_id": "main_loan_catalog",
  "source_name": "BasicHomeLoan"
}
```

### 11. Template Authentication Messages
**Endpoint:** `POST /api_v1/gupshup/template/authentication`

Send authentication template messages (OTP, verification codes, etc.).

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "otp_verification_template",
  "template_params": ["123456", "5"],
  "auth_type": "OTP",
  "source_name": "BasicHomeLoan"
}
```

**Note:** Template parameters are not included in the response for security reasons.

### 12. Template Postback Text Support
**Endpoint:** `POST /api_v1/gupshup/template/postback`

Send template messages with postback functionality for user interactions.

```json
{
  "app_name": "basichomeloan",
  "phone_number": "917888888888",
  "template_id": "interactive_survey_template",
  "template_params": ["John Doe", "Customer Satisfaction Survey"],
  "postback_text": "SURVEY_RESPONSE_2024",
  "source_name": "BasicHomeLoan"
}
```

## Response Format

All template message APIs return a consistent response format:

```json
{
  "success": true,
  "message": "Template message sent successfully",
  "message_id": "wamid.HBgNOTE1NTc5MTc2ODQ=",
  "template_id": "loan_approval_notification",
  "data": {
    "template_id": "loan_approval_notification",
    "template_params": ["John Doe", "Home Loan", "₹50,00,000"],
    "app_name": "basichomeloan"
  },
  "gupshup_response": {
    // Raw Gupshup API response
  }
}
```

## Error Handling

All APIs include comprehensive error handling:

- **400**: Bad Request (validation errors, limits exceeded)
- **404**: App configuration not found, template not found
- **422**: Template parameter mismatch
- **500**: Internal server errors, Gupshup API failures

Example error response:
```json
{
  "detail": "Failed to send template message: Template not found or not approved"
}
```

## Template Requirements

### Template Approval Process
1. **Create Template**: Design template in Gupshup dashboard or via API
2. **Submit for Approval**: WhatsApp reviews template content
3. **Approval Status**: Templates must be APPROVED before use
4. **Parameter Mapping**: Ensure parameters match template placeholders

### Template Categories
- **AUTHENTICATION**: OTP, verification codes
- **MARKETING**: Promotions, offers, announcements
- **UTILITY**: Notifications, updates, confirmations

### Template Components
- **Header**: Optional (text, image, video, document)
- **Body**: Required (text with parameters)
- **Footer**: Optional (text)
- **Buttons**: Optional (call-to-action, quick reply, URL)

## Best Practices

### 1. Parameter Management
- Ensure parameter order matches template definition
- Use meaningful parameter names in templates
- Validate parameter count before sending
- Handle special characters properly

### 2. Template Design
- Keep templates concise and clear
- Use parameters for dynamic content
- Follow WhatsApp template guidelines
- Test templates thoroughly before approval

### 3. Error Handling
- Implement retry logic for failed sends
- Monitor template approval status
- Handle parameter validation errors
- Log template usage for analytics

### 4. Performance Optimization
- Cache approved templates
- Batch similar template messages
- Monitor delivery rates
- Use appropriate message timing

## Template Parameter Examples

### Simple Text Template
```
Template: "Hello {{1}}, your {{2}} application has been {{3}}."
Parameters: ["John Doe", "Home Loan", "approved"]
Result: "Hello John Doe, your Home Loan application has been approved."
```

### Complex Template with Header
```
Template Header: Image/Video
Template Body: "Hi {{1}}, your {{2}} of {{3}} is ready for pickup at {{4}}."
Parameters: ["John", "Loan Documents", "₹50L Home Loan", "Delhi Branch"]
```

## Integration Examples

### Using with Existing OTP System
```python
# Send OTP using template
response = await send_template_authentication_message({
    "app_name": "basichomeloan",
    "phone_number": "917888888888",
    "template_id": "otp_verification",
    "template_params": [otp_code, "5"],  # OTP and expiry minutes
    "auth_type": "OTP"
})
```

### Marketing Campaign
```python
# Send promotional offer
response = await send_template_coupon_message({
    "app_name": "basichomeloan", 
    "phone_number": customer_phone,
    "template_id": "festive_offer",
    "template_params": [customer_name, "Diwali Special"],
    "coupon_code": "DIWALI2024"
})
```

## Monitoring and Analytics

### Message Tracking
- Use returned `message_id` for delivery tracking
- Monitor template performance metrics
- Track user engagement with interactive templates
- Analyze conversion rates by template type

### Template Management
- Regular audit of template approval status
- Monitor template usage limits
- Update templates based on performance
- A/B test different template variations

## Troubleshooting

### Common Issues
1. **Template Not Found**: Verify template ID and approval status
2. **Parameter Mismatch**: Check parameter count and order
3. **Rate Limiting**: Implement proper throttling
4. **Invalid Media URLs**: Ensure URLs are accessible and in correct format

### Debug Steps
1. Verify app configuration
2. Check template approval status via `/templates/by-app` endpoint
3. Validate phone number format
4. Test with minimal parameters first
5. Check Gupshup dashboard for detailed error logs

## Next Steps

1. **Create Templates**: Design and submit templates for approval
2. **Configure Apps**: Set up environment variables for your Gupshup apps
3. **Test APIs**: Start with simple text templates
4. **Monitor Performance**: Track delivery and engagement metrics
5. **Scale Usage**: Implement batch processing for high-volume scenarios

For more information about WhatsApp Business templates and Gupshup API, refer to their official documentation.

