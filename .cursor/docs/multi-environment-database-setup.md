# Multi-Environment Database Setup Guide

## Overview

The `database_service.py` now supports multiple Supabase environments to handle different types of data and operations. This setup allows you to:

- Separate concerns between different environments (e.g., production vs staging data)
- Scale operations across multiple databases
- Implement environment-specific configurations

## Environment Configuration

### Supported Environments

1. **Orbit Environment** - Primary business operations
   - Handles: leads, appointments, disbursements, WhatsApp messages
   - Environment variables: `SUPABASE_ORBIT_URL`, `SUPABASE_ORBIT_SERVICE_ROLE_KEY`

2. **Homfinity Environment** - OTP and utility operations
   - Handles: OTP storage, auxiliary services
   - Environment variables: `SUPABASE_HOMFINITY_URL`, `SUPABASE_HOMFINITY_SERVICE_ROLE_KEY`

### Environment Variables Setup

Add these environment variables to your `.env` file:

```bash
# Orbit Environment (Primary)
SUPABASE_ORBIT_URL=https://your-orbit-project.supabase.co
SUPABASE_ORBIT_SERVICE_ROLE_KEY=your-orbit-service-role-key

# Homfinity Environment (Secondary)
SUPABASE_HOMFINITY_URL=https://your-homfinity-project.supabase.co
SUPABASE_HOMFINITY_SERVICE_ROLE_KEY=your-homfinity-service-role-key

# Default Environment Configuration
DEFAULT_DATABASE_ENVIRONMENT=orbit

# Legacy OTP Support (optional)
SUPABASE_URL=https://your-homfinity-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-homfinity-service-role-key
```

## How Environment Selection Works

### 1. Automatic Table-Based Selection

The system automatically selects the appropriate environment based on the table being accessed:

```python
# Table-to-environment mapping (defined in database_service.py)
table_environment_mapping = {
    "leads": "orbit",
    "appointments": "orbit", 
    "disbursements": "orbit",
    "whatsapp_messages": "orbit",
    "otp_storage": "homfinity"
}
```

### 2. Manual Environment Selection

You can explicitly specify the environment for any operation:

```python
# Using specific environment
database_service.save_lead_data(
    request_data, 
    fbb_response, 
    self_fullfilment_response, 
    environment="orbit"  # Explicit environment
)

# Using automatic selection (recommended)
database_service.save_lead_data(
    request_data, 
    fbb_response, 
    self_fullfilment_response
    # Will automatically use 'orbit' environment for leads table
)
```

### 3. Default Environment Fallback

If no specific environment is provided and no table mapping exists, the system uses the default environment (configurable via `DEFAULT_DATABASE_ENVIRONMENT`).

## Usage Examples

### Basic Usage (Automatic Environment Selection)

```python
from app.services.database_service import database_service

# These calls automatically use the appropriate environment
result = database_service.save_lead_data(request_data, fbb_response, self_fullfilment_response)
leads = database_service.get_leads_by_mobile("9876543210")
database_service.save_whatsapp_message(message_data)
```

### Explicit Environment Usage

```python
# Force specific environment
result = database_service.save_lead_data(
    request_data, 
    fbb_response, 
    self_fullfilment_response, 
    environment="homfinity"
)

# Get leads from specific environment
leads = database_service.get_leads_by_mobile("9876543210", environment="orbit")
```

### Environment Validation

```python
# Check environment status
status = database_service.validate_environments()
print(status)
# Output:
# {
#     "orbit": {"available": True, "error": None},
#     "homfinity": {"available": True, "error": None}
# }

# Get environment configuration info
info = database_service.get_environment_info()
print(info)
```

## API Method Updates

All major database methods now support environment selection:

- `save_whatsapp_message(message_data, environment=None)`
- `save_book_appointment_data(appointment_data, basic_api_response, environment=None)`
- `save_lead_data(request_data, fbb_response, self_fullfilment_response, environment=None)`
- `get_leads_by_mobile(mobile, environment=None)`
- `get_leads_by_basic_app_id(basic_app_id, environment=None)`
- `update_lead_status(basic_app_id, new_status, environment=None)`
- `save_disbursement_data(disbursement_records, environment=None)`
- `update_basic_verify_status(verification_id, verification_status, comments=None, environment=None)`

## Error Handling

The system provides detailed error handling for environment-related issues:

1. **Missing Configuration**: Clear error messages when environment variables are not set
2. **Connection Failures**: Graceful fallback and detailed logging
3. **Environment Unavailability**: Automatic detection and reporting of environment status

## Health Check Integration

You can add environment validation to your health check endpoint:

```python
@router.get("/health")
async def health_check():
    env_status = database_service.validate_environments()
    env_info = database_service.get_environment_info()
    
    return {
        "status": "healthy",
        "database_environments": env_status,
        "environment_config": env_info
    }
```

## Migration from Single Environment

If you're migrating from a single-environment setup:

1. **No Breaking Changes**: All existing code continues to work without modification
2. **Gradual Migration**: You can gradually add environment parameters to method calls
3. **Backward Compatibility**: The system maintains the `self.client` property for legacy code

## Best Practices

1. **Use Automatic Selection**: Let the system choose the environment based on table mapping
2. **Explicit for Special Cases**: Only specify environment explicitly when you need to override defaults
3. **Environment Validation**: Regularly check environment status in production
4. **Configuration Management**: Use environment variables for all sensitive configuration
5. **Logging**: Monitor the logs for environment-related messages and errors

## Troubleshooting

### Common Issues

1. **Environment Not Available**
   - Check environment variables are set correctly
   - Verify Supabase project URLs and keys
   - Test network connectivity to Supabase

2. **Permission Errors**
   - Ensure service role keys have appropriate permissions
   - Check RLS (Row Level Security) policies
   - Verify table access permissions

3. **Table Not Found**
   - Ensure tables exist in the target environment
   - Check table naming consistency across environments
   - Verify database schema is up to date

### Debug Commands

```python
# Check environment configuration
print(database_service.get_environment_info())

# Validate environment connectivity
print(database_service.validate_environments())

# Check specific client initialization
print(f"Orbit client: {database_service.client_orbit}")
print(f"Homfinity client: {database_service.client_homfinity}")
```
