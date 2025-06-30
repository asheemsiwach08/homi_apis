-- Supabase OTP Storage Table Setup
-- Run this in your Supabase SQL Editor

-- Create the OTP storage table
CREATE TABLE IF NOT EXISTS otp_storage (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    otp VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_otp_phone_number ON otp_storage(phone_number);
CREATE INDEX IF NOT EXISTS idx_otp_expires_at ON otp_storage(expires_at);
CREATE INDEX IF NOT EXISTS idx_otp_is_used ON otp_storage(is_used);

-- Create a function to clean up expired OTPs
CREATE OR REPLACE FUNCTION cleanup_expired_otps()
RETURNS void AS $$
BEGIN
    UPDATE otp_storage 
    SET is_used = TRUE 
    WHERE expires_at < NOW() AND is_used = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to clean up expired OTPs (optional)
-- This requires pg_cron extension to be enabled
-- SELECT cron.schedule('cleanup-expired-otps', '*/5 * * * *', 'SELECT cleanup_expired_otps();');

-- Row Level Security (RLS) - Enable if needed
-- ALTER TABLE otp_storage ENABLE ROW LEVEL SECURITY;

-- Create policy for service role (adjust as needed)
-- CREATE POLICY "Service role can manage all OTPs" ON otp_storage
--     FOR ALL USING (auth.role() = 'service_role');

-- Grant permissions (adjust as needed)
-- GRANT ALL ON otp_storage TO service_role;
-- GRANT USAGE, SELECT ON SEQUENCE otp_storage_id_seq TO service_role; 