-- WhatsApp Messages Table Setup
-- Run this in your Supabase SQL Editor

-- Create the WhatsApp messages table (simplified)
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id BIGSERIAL PRIMARY KEY,
    mobile VARCHAR(15) NOT NULL,
    message TEXT NOT NULL,
    payload JSONB -- Store full webhook payload
);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_mobile ON whatsapp_messages(mobile);

-- Create a function to get message statistics
CREATE OR REPLACE FUNCTION get_whatsapp_message_stats()
RETURNS TABLE (
    total_messages BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT COUNT(*) as total_messages
    FROM whatsapp_messages;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get messages by mobile number
CREATE OR REPLACE FUNCTION get_messages_by_mobile(phone_number VARCHAR)
RETURNS TABLE (
    id BIGINT,
    mobile VARCHAR(15),
    message TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        wm.id,
        wm.mobile,
        wm.message
    FROM whatsapp_messages wm
    WHERE wm.mobile = phone_number
    ORDER BY wm.id DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to service role
GRANT ALL ON whatsapp_messages TO service_role;
GRANT USAGE, SELECT ON SEQUENCE whatsapp_messages_id_seq TO service_role;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION get_whatsapp_message_stats() TO service_role;
GRANT EXECUTE ON FUNCTION get_messages_by_mobile(VARCHAR) TO service_role;

-- Disable Row Level Security for this table (recommended for message storage)
ALTER TABLE whatsapp_messages DISABLE ROW LEVEL SECURITY;

-- Create a view for recent messages
CREATE OR REPLACE VIEW recent_whatsapp_messages AS
SELECT 
    id,
    mobile,
    message
FROM whatsapp_messages
ORDER BY id DESC
LIMIT 100; 