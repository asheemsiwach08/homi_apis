-- Updated Appointments Table Setup for Supabase
-- Based on actual Basic Application API response structure
-- Run this in your Supabase SQL Editor

-- Drop existing table if you need to recreate it (CAUTION: This will delete existing data)
-- DROP TABLE IF EXISTS appointments CASCADE;

-- Create the updated appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id BIGSERIAL PRIMARY KEY,
    
    -- API Response Fields
    api_id UUID, -- id from API response
    wa_message_status VARCHAR(50), -- waMesageStatus
    comment_ref VARCHAR(20), -- commentRef
    comment TEXT, -- comment
    ref_type VARCHAR(50) DEFAULT 'Application', -- refType
    basic_app_id VARCHAR(20), -- basicAppId
    ref_id UUID, -- refId
    
    -- Tenant Information
    created_by_tenant_name VARCHAR(255), -- createdByTenantName
    created_by_tenant_id UUID, -- createdByTenantId
    created_by_tenant_type VARCHAR(50), -- createdByTenantType
    created_by_user_name VARCHAR(255), -- createdByUserName
    visible_to TEXT, -- visibleTo
    
    -- Task Information
    task_type VARCHAR(50) DEFAULT 'Task', -- type
    due_date TIMESTAMP WITH TIME ZONE, -- dueDate (parsed)
    task_assigned_to_tenant_type VARCHAR(50), -- taskAssignedToTenantType
    status VARCHAR(50) DEFAULT 'Open', -- status
    
    -- Audit Fields
    created_by UUID, -- createdBy
    created_date TIMESTAMP WITH TIME ZONE, -- createdDate
    updated_by UUID, -- updatedBy
    updated_date TIMESTAMP WITH TIME ZONE, -- updatedDate
    is_active BOOLEAN DEFAULT true, -- isActive
    
    -- Assigned User Information
    assigned_to_user_id UUID, -- assignedToUserId
    assigned_to_user_name VARCHAR(255), -- assignedToUserName
    
    -- Customer Information
    primary_borrower_name VARCHAR(255), -- primaryBorrowerName
    primary_borrower_consent_status VARCHAR(50), -- primaryBorrowerConsentStatus
    
    -- Additional Fields
    can_logged_in_user_delete BOOLEAN DEFAULT false, -- canLoggedInUserDelete
    can_logged_in_user_close BOOLEAN DEFAULT true, -- canLoggedInUserClose
    customer_wa_notification_direction VARCHAR(50), -- customerWAnotificationDirection
    logged_in_user_lost_access BOOLEAN DEFAULT false, -- loggedInUserLostAccess
    
    -- Counts
    extended_count INTEGER DEFAULT 0, -- extendedCount
    call_log_count INTEGER DEFAULT 0, -- callLogCount
    
    -- Original Input Data
    original_appointment_date VARCHAR(20), -- Original date input from user
    original_appointment_time VARCHAR(20), -- Original time input from user
    reference_id VARCHAR(255), -- Reference ID for the appointment
    
    -- Storage Fields
    tags JSONB, -- Store tags array
    uploaded_docs JSONB, -- Store uploadedDocs array
    basic_api_request JSONB, -- Store the request payload sent to Basic API
    basic_api_response JSONB, -- Store the full Basic API response
    
    -- Internal Status
    internal_status VARCHAR(50) DEFAULT 'created', -- Our internal status (created, success, failed)
    error_message TEXT, -- Store any error messages
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_appointments_api_id ON appointments(api_id);
CREATE INDEX IF NOT EXISTS idx_appointments_basic_app_id ON appointments(basic_app_id);
CREATE INDEX IF NOT EXISTS idx_appointments_ref_id ON appointments(ref_id);
CREATE INDEX IF NOT EXISTS idx_appointments_reference_id ON appointments(reference_id);
CREATE INDEX IF NOT EXISTS idx_appointments_comment_ref ON appointments(comment_ref);
CREATE INDEX IF NOT EXISTS idx_appointments_due_date ON appointments(due_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_internal_status ON appointments(internal_status);
CREATE INDEX IF NOT EXISTS idx_appointments_created_by ON appointments(created_by);
CREATE INDEX IF NOT EXISTS idx_appointments_assigned_to_user_id ON appointments(assigned_to_user_id);
CREATE INDEX IF NOT EXISTS idx_appointments_created_at ON appointments(created_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_appointments_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_appointments_updated_at ON appointments;
CREATE TRIGGER update_appointments_updated_at 
    BEFORE UPDATE ON appointments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_appointments_updated_at_column();

-- Grant permissions to service role
GRANT ALL ON appointments TO service_role;
GRANT USAGE, SELECT ON SEQUENCE appointments_id_seq TO service_role;

-- Disable Row Level Security for this table
ALTER TABLE appointments DISABLE ROW LEVEL SECURITY;

-- Create a view for appointment statistics
CREATE OR REPLACE VIEW appointment_statistics AS
SELECT 
    COUNT(*) as total_appointments,
    COUNT(CASE WHEN internal_status = 'created' THEN 1 END) as created_appointments,
    COUNT(CASE WHEN internal_status = 'success' THEN 1 END) as successful_appointments,
    COUNT(CASE WHEN internal_status = 'failed' THEN 1 END) as failed_appointments,
    COUNT(CASE WHEN status = 'Open' THEN 1 END) as open_appointments,
    COUNT(CASE WHEN status = 'Closed' THEN 1 END) as closed_appointments,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as appointments_last_24h,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as appointments_last_7d,
    COUNT(CASE WHEN due_date >= NOW() THEN 1 END) as upcoming_appointments
FROM appointments;

-- Grant permissions on the view
GRANT SELECT ON appointment_statistics TO service_role;

-- Create functions for common queries
CREATE OR REPLACE FUNCTION get_appointments_by_basic_app_id(app_id VARCHAR)
RETURNS TABLE (
    id BIGINT,
    api_id UUID,
    comment_ref VARCHAR(20),
    comment TEXT,
    basic_app_id VARCHAR(20),
    due_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50),
    internal_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.api_id,
        a.comment_ref,
        a.comment,
        a.basic_app_id,
        a.due_date,
        a.status,
        a.internal_status,
        a.created_at
    FROM appointments a
    WHERE a.basic_app_id = app_id
    ORDER BY a.created_at DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_appointments_by_reference_id(ref_id VARCHAR)
RETURNS TABLE (
    id BIGINT,
    api_id UUID,
    comment_ref VARCHAR(20),
    comment TEXT,
    basic_app_id VARCHAR(20),
    due_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50),
    internal_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.id,
        a.api_id,
        a.comment_ref,
        a.comment,
        a.basic_app_id,
        a.due_date,
        a.status,
        a.internal_status,
        a.created_at
    FROM appointments a
    WHERE a.reference_id = ref_id
    ORDER BY a.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION get_appointments_by_basic_app_id(VARCHAR) TO service_role;
GRANT EXECUTE ON FUNCTION get_appointments_by_reference_id(VARCHAR) TO service_role; 