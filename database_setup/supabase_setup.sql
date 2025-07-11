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

-- IMPORTANT: Grant permissions to service role
-- This is required for the service role to access the table
GRANT ALL ON otp_storage TO service_role;
GRANT USAGE, SELECT ON SEQUENCE otp_storage_id_seq TO service_role;

-- Row Level Security (RLS) - Enable if needed
-- ALTER TABLE otp_storage ENABLE ROW LEVEL SECURITY;

-- Create policy for service role (uncomment if RLS is enabled)
-- CREATE POLICY "Service role can manage all OTPs" ON otp_storage
--     FOR ALL USING (auth.role() = 'service_role');

-- Alternative: Disable RLS for this table (recommended for OTP storage)
-- This allows the service role to access the table without complex policies
ALTER TABLE otp_storage DISABLE ROW LEVEL SECURITY; 



-- For Lead Creation and Lead Status Check

-- Supabase Database Schema for Lead Management
-- Run this SQL in your Supabase SQL Editor

-- Create leads table
CREATE TABLE IF NOT EXISTS leads (
    id BIGSERIAL PRIMARY KEY,
    basic_application_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255),
    relation_id VARCHAR(255),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(15) NOT NULL,
    email VARCHAR(255),
    pan_number VARCHAR(10),
    loan_type VARCHAR(50) NOT NULL,
    loan_amount DECIMAL(15,2) NOT NULL,
    loan_tenure INTEGER NOT NULL,
    gender VARCHAR(10),
    dob VARCHAR(10), -- Store as YYYY-MM-DD format
    pin_code VARCHAR(10),
    basic_api_response JSONB, -- Store full Basic API response
    status VARCHAR(50) DEFAULT 'created',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_leads_basic_application_id ON leads(basic_application_id);
CREATE INDEX IF NOT EXISTS idx_leads_mobile_number ON leads(mobile_number);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_leads_updated_at 
    BEFORE UPDATE ON leads 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- -- Enable Row Level Security (RLS)
-- ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- -- Create policy for authenticated users (adjust based on your auth requirements)
-- CREATE POLICY "Allow authenticated users to read leads" ON leads
--     FOR SELECT USING (auth.role() = 'authenticated');

-- CREATE POLICY "Allow authenticated users to insert leads" ON leads
--     FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- CREATE POLICY "Allow authenticated users to update leads" ON leads
--     FOR UPDATE USING (auth.role() = 'authenticated');

-- Optional: Create a view for lead statistics
CREATE OR REPLACE VIEW lead_statistics AS
SELECT 
    COUNT(*) as total_leads,
    COUNT(CASE WHEN status = 'created' THEN 1 END) as created_leads,
    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_leads,
    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_leads,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as leads_last_24h,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as leads_last_7d
FROM leads; 