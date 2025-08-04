-- Disbursements Table Setup for Supabase
-- This table stores all disbursement records processed from emails
-- Run this in your Supabase SQL Editor

-- Create the disbursements table
CREATE TABLE IF NOT EXISTS disbursements (
    id BIGSERIAL PRIMARY KEY,
    
    -- Email Context
    banker_email VARCHAR(255), -- Email of the banker/sender
    email_subject TEXT, -- Subject of the email
    email_date TIMESTAMP WITH TIME ZONE, -- Date of the email
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- When we processed this record
    
    -- Customer Information
    first_name VARCHAR(255), -- Customer first name
    last_name VARCHAR(255), -- Customer last name
    primary_borrower_mobile VARCHAR(20), -- Customer mobile number
    
    -- Loan Account Information
    loan_account_number VARCHAR(255), -- LAN or account number
    bank_app_id VARCHAR(255), -- Bank application ID
    basic_app_id VARCHAR(255), -- Basic application ID
    basic_disb_id VARCHAR(255), -- Basic disbursement ID
    
    -- Bank Information
    app_bank_name VARCHAR(255), -- Name of the lending bank
    
    -- Disbursement Details
    disbursement_amount DECIMAL(15,2), -- Amount disbursed
    loan_sanction_amount DECIMAL(15,2), -- Total sanctioned amount
    disbursed_on DATE, -- Date of disbursement
    disbursed_created_on DATE, -- Date when disbursement was created
    sanction_date DATE, -- Date of loan sanction
    
    -- Status Information
    disbursement_stage VARCHAR(50), -- Disbursed, Pending, No Status
    disbursement_status VARCHAR(50), -- VerifiedByAI, Manual, etc.
    
    -- Additional Fields
    pdd VARCHAR(50), -- PDD status
    otc VARCHAR(50), -- OTC status
    sourcing_channel VARCHAR(100), -- How the loan was sourced
    sourcing_code VARCHAR(100), -- Sourcing code
    application_product_type VARCHAR(10), -- HL, PL, LAP, etc.
    
    -- Data Quality
    data_found BOOLEAN DEFAULT false, -- Whether valid data was found
    confidence_score DECIMAL(3,2), -- AI confidence score (0.00 to 1.00)
    extraction_method VARCHAR(50) DEFAULT 'AI', -- AI, Manual, Import
    
    -- Source Information
    source_email_id VARCHAR(255), -- Original email message ID
    source_thread_id VARCHAR(255), -- Email thread ID if applicable
    attachment_count INTEGER DEFAULT 0, -- Number of attachments processed
    
    -- Internal Fields
    is_duplicate BOOLEAN DEFAULT false, -- Marked if this is a duplicate
    duplicate_of_id BIGINT REFERENCES disbursements(id), -- References original record if duplicate
    manual_review_required BOOLEAN DEFAULT true, -- Needs manual review
    manual_review_notes TEXT, -- Notes from manual review
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) DEFAULT 'system', -- system, user_email, etc.
    updated_by VARCHAR(100) DEFAULT 'system'
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_disbursements_loan_account_number ON disbursements(loan_account_number);
CREATE INDEX IF NOT EXISTS idx_disbursements_bank_app_id ON disbursements(bank_app_id);
CREATE INDEX IF NOT EXISTS idx_disbursements_basic_app_id ON disbursements(basic_app_id);
CREATE INDEX IF NOT EXISTS idx_disbursements_banker_email ON disbursements(banker_email);
CREATE INDEX IF NOT EXISTS idx_disbursements_disbursed_on ON disbursements(disbursed_on);
CREATE INDEX IF NOT EXISTS idx_disbursements_disbursement_stage ON disbursements(disbursement_stage);
CREATE INDEX IF NOT EXISTS idx_disbursements_app_bank_name ON disbursements(app_bank_name);
CREATE INDEX IF NOT EXISTS idx_disbursements_processed_at ON disbursements(processed_at);
CREATE INDEX IF NOT EXISTS idx_disbursements_email_date ON disbursements(email_date);
CREATE INDEX IF NOT EXISTS idx_disbursements_data_found ON disbursements(data_found);
CREATE INDEX IF NOT EXISTS idx_disbursements_is_duplicate ON disbursements(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_disbursements_manual_review_required ON disbursements(manual_review_required);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_disbursements_customer_name ON disbursements(first_name, last_name);
CREATE INDEX IF NOT EXISTS idx_disbursements_date_range ON disbursements(disbursed_on, processed_at);
CREATE INDEX IF NOT EXISTS idx_disbursements_bank_stage ON disbursements(app_bank_name, disbursement_stage);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_disbursements_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_disbursements_updated_at ON disbursements;
CREATE TRIGGER update_disbursements_updated_at 
    BEFORE UPDATE ON disbursements 
    FOR EACH ROW 
    EXECUTE FUNCTION update_disbursements_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE disbursements IS 'Stores all disbursement records extracted from banker emails';
COMMENT ON COLUMN disbursements.loan_account_number IS 'Loan Account Number (LAN) or Account Number';
COMMENT ON COLUMN disbursements.bank_app_id IS 'Bank Application ID from the lending bank';
COMMENT ON COLUMN disbursements.disbursement_stage IS 'Status: Disbursed, Pending, or No Status';
COMMENT ON COLUMN disbursements.data_found IS 'True if valid disbursement data was extracted';
COMMENT ON COLUMN disbursements.confidence_score IS 'AI extraction confidence (0.00-1.00)';
COMMENT ON COLUMN disbursements.is_duplicate IS 'True if this record is identified as duplicate';
COMMENT ON COLUMN disbursements.manual_review_required IS 'True if record needs manual verification';

-- Create a view for frontend consumption (only non-duplicate, valid records)
CREATE OR REPLACE VIEW disbursements_frontend AS
SELECT 
    id,
    banker_email,
    first_name,
    last_name,
    loan_account_number,
    disbursed_on,
    disbursed_created_on,
    sanction_date,
    disbursement_amount,
    loan_sanction_amount,
    bank_app_id,
    basic_app_id,
    basic_disb_id,
    app_bank_name,
    disbursement_stage,
    disbursement_status,
    primary_borrower_mobile,
    pdd,
    otc,
    sourcing_channel,
    sourcing_code,
    application_product_type,
    data_found,
    confidence_score,
    processed_at,
    email_date,
    created_at
FROM disbursements 
WHERE 
    is_duplicate = false 
    AND data_found = true
ORDER BY processed_at DESC;

COMMENT ON VIEW disbursements_frontend IS 'Clean view of disbursement records for frontend display';

-- Sample data for testing (optional - remove in production)
/*
INSERT INTO disbursements (
    banker_email, first_name, last_name, loan_account_number, 
    disbursed_on, disbursement_amount, loan_sanction_amount,
    bank_app_id, app_bank_name, disbursement_stage,
    disbursement_status, primary_borrower_mobile, 
    application_product_type, data_found, confidence_score
) VALUES 
(
    'banker@hdfcbank.com', 'John', 'Doe', 'LAN123456789',
    '2024-01-15', 2500000, 2500000,
    'HDFC2024001', 'HDFC Bank', 'Disbursed',
    'VerifiedByAI', '+919876543210',
    'HL', true, 0.95
),
(
    'banker@icicibank.com', 'Jane', 'Smith', 'ICICI987654321', 
    '2024-01-16', 1800000, 2000000,
    'ICICI2024002', 'ICICI Bank', 'Disbursed',
    'VerifiedByAI', '+919876543211',
    'HL', true, 0.92
);
*/