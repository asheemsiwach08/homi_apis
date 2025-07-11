-- Quick Fix for Supabase OTP Storage Permissions
-- Run this in your Supabase SQL Editor to fix the permission denied error

-- Grant all permissions to service role on the otp_storage table
GRANT ALL ON otp_storage TO service_role;

-- Grant permissions on the sequence (for auto-incrementing ID)
GRANT USAGE, SELECT ON SEQUENCE otp_storage_id_seq TO service_role;

-- Disable Row Level Security for this table (recommended for OTP storage)
-- This allows the service role to access the table without complex policies
ALTER TABLE otp_storage DISABLE ROW LEVEL SECURITY;

-- Verify the table exists and has correct structure
SELECT 
    table_name, 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'otp_storage'
ORDER BY ordinal_position; 