-- Detailed Leads Table Setup for Supabase
-- Based on the CreateFBBByBasicUser and SelfFullfilment API response structure
-- Run this in your Supabase SQL Editor

-- Create the detailed_leads table
CREATE TABLE IF NOT EXISTS detailed_leads (
    id BIGSERIAL PRIMARY KEY,
    
    -- Core Application Fields
    api_id UUID, -- id from API response
    basic_app_id VARCHAR(20), -- basicAppId
    loan_type VARCHAR(10), -- loanType (HL, PL, etc.)
    loan_amount_req DECIMAL(15,2), -- loanAmountReq
    loan_tenure INTEGER, -- loanTenure
    
    -- Application Status & Dates
    application_date TIMESTAMP WITH TIME ZONE, -- applicationDate
    application_status VARCHAR(50), -- applicationStatus
    application_stage VARCHAR(50), -- applicationStage
    fbb_date TIMESTAMP WITH TIME ZONE, -- fbbDate
    fbb_outcome VARCHAR(50), -- fbbOutcome
    fbb_rejection_reason TEXT, -- fbbRejectionReason
    
    -- Verification Status
    tele_verification_status VARCHAR(50), -- teleVerificationStatus
    tele_verification_failed_reason TEXT, -- teleVerificationFailedReason
    
    -- Assignment Fields
    assigned_to UUID, -- assignedTo
    application_assigned_to_rm UUID, -- applicationAssignedToRm
    
    -- Flags & Permissions
    is_qualified_by_ref_agent BOOLEAN DEFAULT false, -- isQualifiedByRefAgent
    include_credit_score BOOLEAN DEFAULT true, -- includeCreditScore
    is_lead_prefilled BOOLEAN DEFAULT true, -- isLeadPrefilled
    can_activate_bank_referral BOOLEAN DEFAULT false, -- canActivateBankReferral
    is_basic_fullfilment BOOLEAN DEFAULT true, -- isBasicFullfilment
    is_cancellable_withdrawable BOOLEAN DEFAULT false, -- isCancellableWithdrawable
    can_cancel_bank_login BOOLEAN DEFAULT false, -- canCancelBankLogin
    can_skip_osv BOOLEAN DEFAULT false, -- canSkipOsv
    has_disbursements BOOLEAN DEFAULT false, -- hasDisbursements
    
    -- Source & Origin
    source VARCHAR(50), -- source
    originated_by_dsa_org_id UUID, -- originatedByDsaOrgId
    originated_by_dsa_user_id UUID, -- originatedByDsaUserId
    dsa_org_id UUID, -- dsaOrgId
    
    -- Customer Information
    customer_id UUID, -- primaryBorrower.customerId
    customer_pan VARCHAR(10), -- primaryBorrower.pan
    customer_first_name VARCHAR(100), -- primaryBorrower.firstName
    customer_last_name VARCHAR(100), -- primaryBorrower.lastName
    customer_gender VARCHAR(20), -- primaryBorrower.gender
    customer_mobile VARCHAR(15), -- primaryBorrower.mobile
    customer_email VARCHAR(255), -- primaryBorrower.email
    customer_date_of_birth DATE, -- primaryBorrower.dateOfBirth
    customer_pincode VARCHAR(10), -- primaryBorrower.pincode
    customer_city VARCHAR(100), -- primaryBorrower.city
    customer_district VARCHAR(100), -- primaryBorrower.district
    customer_state VARCHAR(100), -- primaryBorrower.state
    customer_annual_income DECIMAL(15,2), -- primaryBorrower.annualIncome
    customer_company_name VARCHAR(255), -- primaryBorrower.companyName
    customer_profession_id UUID, -- primaryBorrower.professionId
    customer_profession_name VARCHAR(100), -- primaryBorrower.professionName
    customer_consent_status VARCHAR(50), -- primaryBorrower.customerConsentStatus
    
    -- Financial Information
    co_borrower_income DECIMAL(15,2) DEFAULT 0, -- coBorrowerIncome
    existing_emis DECIMAL(15,2) DEFAULT 0, -- existingEmis
    
    -- Credit Information
    credit_score INTEGER DEFAULT 0, -- creditScore
    credit_score_type_id VARCHAR(255), -- creditScoreTypeId
    customer_credit_score INTEGER DEFAULT 0, -- primaryBorrowerCreditReportDetails.customerCreditScore
    credit_report_status VARCHAR(50), -- primaryBorrowerCreditReportDetails.creditReportStatus
    
    -- Scores & Badges
    demo_score INTEGER DEFAULT 0, -- demoScore
    product_score INTEGER DEFAULT 0, -- productScore
    fin_score INTEGER DEFAULT 0, -- finScore
    prop_score INTEGER DEFAULT 0, -- propScore
    total_score INTEGER DEFAULT 0, -- totalScore
    lead_badge VARCHAR(50) DEFAULT 'None', -- leadBadge
    
    -- Property Information
    is_property_identified BOOLEAN DEFAULT false, -- isPropertyIdentified
    property_type_id VARCHAR(255), -- propertyTypeId
    property_project_name VARCHAR(255), -- propertyProjectName
    property_pincode VARCHAR(10), -- propertyPincode
    property_district VARCHAR(100), -- propertyDistrict
    builder_id VARCHAR(255), -- builderId
    builder_name VARCHAR(255), -- builderName
    project_id VARCHAR(255), -- projectId
    tower_id VARCHAR(255), -- towerId
    tower_name VARCHAR(255), -- towerName
    
    -- Loan Usage & Agreement
    loan_usage_type_id VARCHAR(255), -- loanUsageTypeId
    aggreement_type_id VARCHAR(255), -- aggrementTypeId
    
    -- Additional Flags
    is_referral_lead BOOLEAN DEFAULT false, -- isReferralLead
    referred_to_banks INTEGER DEFAULT 0, -- referredTobanks
    can_customer_upload_documents BOOLEAN DEFAULT false, -- canCustomerUploadDocuments
    is_pbb_lead BOOLEAN DEFAULT false, -- isPbbLead
    is_osv_by_consultant_available BOOLEAN DEFAULT true, -- isOsvByConsultantAvailable
    online_login_type VARCHAR(50) DEFAULT 'None', -- onlineLoginType
    
    -- Latest References
    application_latest_comment_or_task_id UUID, -- applicationLatestCommentOrTaskId
    
    -- Qualification & Agents
    qualified_by_agent_user_id UUID, -- qualifiedByAgentUserId
    qualified_by_agent_type VARCHAR(50), -- qualifiedByAgentType
    auto_referral_attempt_count INTEGER DEFAULT 0, -- autoReferralAttemptCount
    
    -- JSONB Storage Fields
    application_comments JSONB, -- applicationComments array
    documents JSONB, -- documents array
    primary_borrower_documents JSONB, -- primaryBorrower.documents array
    co_borrowers JSONB, -- coBorrowers array
    sanctions JSONB, -- sanctions array
    disbursements JSONB, -- disbursements array
    has_application_tags JSONB, -- hasApplicationTags array
    
    -- Original Request Data
    original_request_data JSONB, -- Store original API request
    fbb_api_response JSONB, -- Store FBB API response
    self_fullfilment_api_response JSONB, -- Store Self Fullfilment API response
    
    -- Internal Status & Error Handling
    internal_status VARCHAR(50) DEFAULT 'created', -- Our internal status
    error_message TEXT, -- Store any error messages
    processing_stage VARCHAR(50) DEFAULT 'fbb', -- Track which stage: fbb, self_fullfilment, completed
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_detailed_leads_api_id ON detailed_leads(api_id);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_basic_app_id ON detailed_leads(basic_app_id);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_customer_id ON detailed_leads(customer_id);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_customer_mobile ON detailed_leads(customer_mobile);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_customer_pan ON detailed_leads(customer_pan);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_customer_email ON detailed_leads(customer_email);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_application_status ON detailed_leads(application_status);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_application_stage ON detailed_leads(application_stage);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_loan_type ON detailed_leads(loan_type);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_internal_status ON detailed_leads(internal_status);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_processing_stage ON detailed_leads(processing_stage);
CREATE INDEX IF NOT EXISTS idx_detailed_leads_created_at ON detailed_leads(created_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_detailed_leads_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_detailed_leads_updated_at ON detailed_leads;
CREATE TRIGGER update_detailed_leads_updated_at 
    BEFORE UPDATE ON detailed_leads 
    FOR EACH ROW 
    EXECUTE FUNCTION update_detailed_leads_updated_at_column();

-- Grant permissions to service role
GRANT ALL ON detailed_leads TO service_role;
GRANT USAGE, SELECT ON SEQUENCE detailed_leads_id_seq TO service_role;

-- Disable Row Level Security for this table
ALTER TABLE detailed_leads DISABLE ROW LEVEL SECURITY;

-- Create a view for detailed leads statistics
CREATE OR REPLACE VIEW detailed_leads_statistics AS
SELECT 
    COUNT(*) as total_detailed_leads,
    COUNT(CASE WHEN internal_status = 'created' THEN 1 END) as created_leads,
    COUNT(CASE WHEN internal_status = 'fbb_completed' THEN 1 END) as fbb_completed_leads,
    COUNT(CASE WHEN internal_status = 'self_fullfilment_completed' THEN 1 END) as self_fullfilment_completed_leads,
    COUNT(CASE WHEN internal_status = 'completed' THEN 1 END) as completed_leads,
    COUNT(CASE WHEN internal_status = 'failed' THEN 1 END) as failed_leads,
    COUNT(CASE WHEN application_status = 'Lead' THEN 1 END) as lead_status_leads,
    COUNT(CASE WHEN application_stage = 'Lead' THEN 1 END) as lead_stage_leads,
    COUNT(CASE WHEN loan_type = 'HL' THEN 1 END) as home_loans,
    COUNT(CASE WHEN loan_type = 'PL' THEN 1 END) as personal_loans,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as leads_last_24h,
    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as leads_last_7d,
    AVG(loan_amount_req) as avg_loan_amount,
    AVG(loan_tenure) as avg_loan_tenure
FROM detailed_leads;

-- Grant permissions on the view
GRANT SELECT ON detailed_leads_statistics TO service_role;

-- Create functions for common queries
CREATE OR REPLACE FUNCTION get_detailed_leads_by_mobile(mobile VARCHAR)
RETURNS TABLE (
    id BIGINT,
    api_id UUID,
    basic_app_id VARCHAR(20),
    customer_mobile VARCHAR(15),
    customer_first_name VARCHAR(100),
    customer_last_name VARCHAR(100),
    application_status VARCHAR(50),
    internal_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dl.id,
        dl.api_id,
        dl.basic_app_id,
        dl.customer_mobile,
        dl.customer_first_name,
        dl.customer_last_name,
        dl.application_status,
        dl.internal_status,
        dl.created_at
    FROM detailed_leads dl
    WHERE dl.customer_mobile = mobile
    ORDER BY dl.created_at DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_detailed_leads_by_basic_app_id(app_id VARCHAR)
RETURNS TABLE (
    id BIGINT,
    api_id UUID,
    basic_app_id VARCHAR(20),
    customer_mobile VARCHAR(15),
    customer_first_name VARCHAR(100),
    customer_last_name VARCHAR(100),
    application_status VARCHAR(50),
    internal_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dl.id,
        dl.api_id,
        dl.basic_app_id,
        dl.customer_mobile,
        dl.customer_first_name,
        dl.customer_last_name,
        dl.application_status,
        dl.internal_status,
        dl.created_at
    FROM detailed_leads dl
    WHERE dl.basic_app_id = app_id
    ORDER BY dl.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION get_detailed_leads_by_mobile(VARCHAR) TO service_role;
GRANT EXECUTE ON FUNCTION get_detailed_leads_by_basic_app_id(VARCHAR) TO service_role; 