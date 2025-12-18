# API Wireframes Documentation

## 1A. 📋 CREATE LEAD API (`leads.py` - `/create_lead`)

### Overview
The Create Lead API handles comprehensive lead creation through FBB (First Bank Branch) processing with multi-stage workflow and flexible field support.

### API Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    CREATE LEAD API WIREFRAME                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/create_lead                                      │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION & SCHEMA                               │   │
│  │                                                         │   │
│  │ REQUIRED FIELDS:                                        │   │
│  │ ├── environment: "orbit" | "homfinity"                  │   │
│  │ ├── firstName: string (2-50 chars)                      │   │
│  │ ├── lastName: string (2-50 chars)                       │   │
│  │ ├── mobile: string (10 digits, auto-normalized)         │   │
│  │ ├── email: string (valid email format)                  │   │
│  │ ├── pan: string (ABCDE1234F format)                     │   │
│  │ ├── loanType: "HL"|"LAP"|"PL"|"BL"|"CL"|"EL"            │   │
│  │ ├── loanAmountReq: number (min: 100000, max: 50000000)  │   │
│  │ ├── loanTenure: number (months: 12-360)                 │   │
│  │ ├── creditScore: number (300-900)                       │   │
│  │ ├── pincode: string (6 digits)                          │   │
│  │ └── dateOfBirth: string (YYYY-MM-DD)                    │   │
│  │                                                         │   │
│  │ OPTIONAL FIELDS:                                        │   │
│  │ ├── gender: "Male"|"Female"|"Other"                     │   │
│  │ ├── annualIncome: number (0-100000000)                  │   │
│  │ ├── applicationAssignedToRm: string                     │   │
│  │ ├── remarks: string (max 500 chars)                     │   │
│  │ ├── state: string                                       │   │
│  │ ├── customerId: string                                  │   │
│  │ ├── qrShortCode: string                                 │   │
│  │ ├── includeCreditScore: boolean (default: true)         │   │
│  │ └── isLeadPrefilled: boolean (default: false)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ COMPREHENSIVE VALIDATION PIPELINE                       │   │
│  │                                                         │   │
│  │ STEP 1: ENVIRONMENT VALIDATION                          │   │
│  │ ├── Check environment is provided                       │   │
│  │ ├── Validate environment is "orbit" or "homfinity"      │   │
│  │ └── Set processing context based on environment         │   │
│  │                                                         │   │
│  │ STEP 2: PERSONAL DATA VALIDATION                        │   │
│  │ ├── firstName: validate_first_name()                    │   │
│  │ ├── lastName: validate_last_name()                      │   │
│  │ ├── mobile: validate_mobile_number() + normalize        │   │
│  │ ├── email: validate_email() format check                │   │
│  │ ├── pan: validate_pan_number() format + checksum        │   │
│  │ ├── gender: validate_gender() if provided               │   │
│  │ └── dateOfBirth: age validation (18-65 years)           │   │
│  │                                                         │   │
│  │ STEP 3: FINANCIAL DATA VALIDATION                       │   │
│  │ ├── loanType: validate_loan_type() mapping              │   │
│  │ ├── loanAmountReq: validate_loan_amount() range         │   │
│  │ ├── loanTenure: validate_loan_tenure() limits           │   │
│  │ ├── creditScore: validate_credit_score() range          │   │
│  │ └── annualIncome: range validation if provided          │   │
│  │                                                         │   │
│  │ STEP 4: LOCATION DATA VALIDATION                        │   │
│  │ ├── pincode: validate_pin_code() format + existence     │   │
│  │ └── state: cross-reference with pincode if provided     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ FBB CREATION WORKFLOW                                   │   │
│  │                                                         │   │
│  │ STEP 1: API PAYLOAD PREPARATION                         │   │
│  │ ├── Map internal fields to Basic Application format     │   │
│  │ ├── Apply loan type mapping (HL, LAP, PL, etc.)         │   │
│  │ ├── Format dates and numbers per API requirements       │   │
│  │ └── Add environment-specific configurations             │   │
│  │                                                         │   │
│  │ STEP 2: BASIC APPLICATION API CALL                      │   │
│  │ ├── Endpoint: CreateFBBByBasicUser                      │   │
│  │ ├── Authentication: API key + user ID                   │   │
│  │ ├── Request timeout: 30 seconds                         │   │
│  │ ├── Retry logic: 3 attempts with exponential backoff    │   │
│  │ └── Response validation: check for basic_application_id │   │
│  │                                                         │   │
│  │ STEP 3: RESPONSE PROCESSING                             │   │
│  │ ├── Extract basic_application_id (e.g., "B002BJF")      │   │
│  │ ├── Extract applicationId (UUID)                        │   │
│  │ ├── Generate reference_id (UUID for tracking)           │   │
│  │ └── Validate API response completeness                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DATABASE STORAGE & AUDIT TRAIL                          │   │
│  │                                                         │   │
│  │ STEP 1: LEAD DATA PREPARATION                           │   │
│  │ ├── Combine request data + API response                 │   │
│  │ ├── Add timestamps (created_at, updated_at)             │   │
│  │ ├── Add processing metadata (request_id, user_agent)    │   │
│  │ └── Prepare audit trail information                     │   │
│  │                                                         │   │
│  │ STEP 2: DATABASE OPERATIONS                             │   │
│  │ ├── Environment-specific table selection                │   │
│  │ ├── Upsert logic (update if exists, insert if new)      │   │
│  │ ├── Transaction management (rollback on failure)        │   │
│  │ └── Index optimization for quick lookups                │   │
│  │                                                         │   │
│  │ STEP 3: AUDIT & COMPLIANCE                              │   │
│  │ ├── Log all field changes                               │   │
│  │ ├── Store operation type (created/updated)              │   │
│  │ ├── Record processing duration                          │   │
│  │ └── Maintain data lineage                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ WHATSAPP NOTIFICATION SYSTEM                            │   │
│  │                                                         │   │
│  │ STEP 1: NOTIFICATION DECISION                           │   │
│  │ ├── Check if WhatsApp notification is enabled           │   │
│  │ ├── Validate customer phone number                      │   │
│  │ ├── Check notification preferences                      │   │
│  │ └── Determine appropriate template                      │   │
│  │                                                         │   │
│  │ STEP 2: MESSAGE PREPARATION                             │   │
│  │ ├── Template: Lead Confirmation Template                │   │
│  │ ├── Parameters: [customerName, applicationId, loanType] │   │
│  │ ├── Personalization: Include specific details           │   │
│  │ └── Compliance: Add opt-out instructions                │   │
│  │                                                         │   │
│  │ STEP 3: DELIVERY & TRACKING                             │   │
│  │ ├── Send via WhatsApp Service                           │   │
│  │ ├── Track delivery status                               │   │
│  │ ├── Log notification attempt                            │   │
│  │ └── Handle delivery failures gracefully                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ RESPONSE GENERATION                                     │   │
│  │                                                         │   │
│  │ SUCCESS RESPONSE (HTTP 200):                            │   │
│  │ {                                                       │   │
│  │   "success": true,                                      │   │
│  │   "basic_application_id": "B002BJF",                    │   │
│  │   "applicationId": "uuid-string",                       │   │
│  │   "reference_id": "uuid-string",                        │   │
│  │   "message": "Lead created successfully"                │   │
│  │ }                                                       │   │
│  │                                                         │   │
│  │ ERROR RESPONSES:                                        │   │
│  │ ├── 422: Validation errors with field details           │   │
│  │ ├── 400: Basic Application API failures                 │   │
│  │ ├── 409: Duplicate lead (if exists)                     │   │
│  │ └── 500: Internal server errors                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  Create Lead   │───▶│ Basic App API   │
│   (Frontend)    │    │      API        │    │ (CreateFBB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Database      │    │   WhatsApp      │
                       │  (Supabase)     │    │   Service       │
                       └─────────────────┘    └─────────────────┘
```

### Validation Matrix

|----------------|--------------------------------------|------------------------------------------|
|      Field     |            Validation Rules          |               Error Message              |
|----------------|--------------------------------------|------------------------------------------|
| environment    | Required, "orbit" or "homfinity"     | "Environment must be orbit or homfinity" |
| firstName      | Required, 2-50 chars, alphabetic     | "First name must be 2-50 characters"     |
| mobile         | Required, 10 digits, auto-normalized | "Invalid mobile number format"           |
| email          | Required, valid email format         | "Invalid email address format"           |
| pan            | Required, ABCDE1234F format          | "Invalid PAN number format"              |
| loanA mountReq | Required, 100000-50000000            | "Loan amount must be between 1L-5Cr"     |
| creditScore    | Required, 300-900                    | "Credit score must be between 300-900"   |

---

## 1B. ⚡ LEAD FLASH API (`leads.py` - `/lead_flash`)

### Overview
The Lead Flash API processes complete lead flash workflow with comprehensive application details, handling self-fulfillment creation and property processing.

### API Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    LEAD FLASH API WIREFRAME                    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/lead_flash                                       │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION & SCHEMA                               │   │
│  │                                                         │   │
│  │ REQUIRED FIELDS:                                        │   │
│  │ ├── applicationId: string (existing UUID)               │   │
│  │ ├── professionId: number (valid profession ID)          │   │
│  │ ├── professionName: string (e.g., "Software Engineer")  │   │
│  │                                                         │   │
│  │ CORE PERSONAL DATA (inherited from create_lead):        │   │
│  │ ├── firstName, lastName, mobile, email, pan             │   │
│  │ ├── loanType, loanAmountReq, loanTenure, creditScore    │   │
│  │ ├── pincode, dateOfBirth, gender                        │   │
│  │                                                         │   │
│  │ PROPERTY INFORMATION (optional with smart defaults):    │   │
│  │ ├── propertyIdentified: boolean (default: false)        │   │
│  │ ├── propertyName: string (e.g., "Dream Home")           │   │
│  │ ├── propertyType: string (e.g., "Apartment")            │   │
│  │ ├── agreementType: string (e.g., "Sale Deed")           │   │
│  │ ├── location: string (property location)                │   │
│  │ ├── usageType: string (residential/commercial)          │   │
│  │ ├── propertyValue: number (market valuation)            │   │
│  │                                                         │   │
│  │ EMPLOYMENT DETAILS (optional):                          │   │
│  │ ├── salaryCreditModeId: number                          │   │
│  │ ├── salaryCreditModeName: string                        │   │
│  │ ├── selfCompanyTypeId: number                           │   │
│  │ ├── companyName: string                                 │   │
│  │ └── coBorrowerIncome: number                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ APPLICATION VALIDATION PIPELINE                         │   │
│  │                                                         │   │
│  │ STEP 1: EXISTING APPLICATION VERIFICATION               │   │
│  │ ├── Validate applicationId format (UUID)                │   │
│  │ ├── Database lookup to confirm application exists       │   │
│  │ ├── Check application status (must be "created")        │   │
│  │ ├── Verify application belongs to correct environment   │   │
│  │ └── Load existing application data for processing       │   │
│  │                                                         │   │
│  │ STEP 2: PROFESSION DATA VALIDATION                      │   │
│  │ ├── professionId: must be valid profession ID           │   │
│  │ ├── professionName: cross-reference with ID             │   │
│  │ ├── Employment type validation (salaried/self-employed) │   │
│  │ └── Income consistency checks                           │   │
│  │                                                         │   │
│  │ STEP 3: PROPERTY DATA VALIDATION                        │   │
│  │ ├── propertyValue: reasonable range for location        │   │
│  │ ├── agreementType: valid legal document type            │   │
│  │ ├── propertyType: standard property categories          │   │
│  │ └── Location consistency with pincode                   │   │
│  │                                                         │   │
│  │ STEP 4: FINANCIAL CONSISTENCY CHECKS                    │   │
│  │ ├── Loan amount vs property value ratio                 │   │
│  │ ├── Income vs loan amount feasibility                   │   │
│  │ ├── Credit score vs loan terms alignment                │   │
│  │ └── Co-borrower income validation if provided           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ SELF-FULFILLMENT CREATION WORKFLOW                      │   │
│  │                                                         │   │
│  │ STEP 1: COMPREHENSIVE DATA PREPARATION                  │   │
│  │ ├── Merge existing application data with new details    │   │
│  │ ├── Apply business rules and defaults                   │   │
│  │ ├── Format data for CreateSelfFullfilmentLead API       │   │
│  │ ├── Add compliance and regulatory fields                │   │
│  │ └── Prepare property and profession mappings            │   │
│  │                                                         │   │
│  │ STEP 2: SELF-FULFILLMENT API INTEGRATION                │   │
│  │ ├── Endpoint: CreateSelfFullfilmentLead                 │   │
│  │ ├── Authentication: Environment-specific credentials    │   │
│  │ ├── Payload: Complete application + flash data          │   │
│  │ ├── Timeout: 45 seconds (complex processing)            │   │
│  │ ├── Retry logic: 2 attempts with 5-second delay         │   │
│  │ └── Response validation: confirm successful creation    │   │
│  │                                                         │   │
│  │ STEP 3: PROPERTY PROCESSING PIPELINE                    │   │
│  │ ├── Property identification verification                │   │
│  │ ├── Market valuation cross-check                        │   │
│  │ ├── Legal document type validation                      │   │
│  │ ├── Location and usage type verification                │   │
│  │ └── Property-loan alignment assessment                  │   │
│  │                                                         │   │
│  │ STEP 4: PROFESSION & EMPLOYMENT PROCESSING              │   │
│  │ ├── Profession category mapping                         │   │
│  │ ├── Salary credit mode validation                       │   │
│  │ ├── Company type and name verification                  │   │
│  │ ├── Income source documentation requirements            │   │
│  │ └── Employment stability assessment                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DATABASE UPDATE & STATUS MANAGEMENT                     │   │
│  │                                                         │   │
│  │ STEP 1: APPLICATION STATUS UPDATE                       │   │
│  │ ├── Change status from "created" to "completed"         │   │
│  │ ├── Add flash processing timestamp                      │   │
│  │ ├── Update application with complete details            │   │
│  │ ├── Create audit trail for status change                │   │
│  │ └── Link property and profession data                   │   │
│  │                                                         │   │
│  │ STEP 2: COMPREHENSIVE DATA STORAGE                      │   │
│  │ ├── Store complete application workflow data            │   │
│  │ ├── Property details with valuation information         │   │
│  │ ├── Profession and employment complete records          │   │
│  │ ├── Processing metadata and timing information          │   │
│  │ └── Cross-reference with original lead creation         │   │
│  │                                                         │   │
│  │ STEP 3: WORKFLOW COMPLETION TRACKING                    │   │
│  │ ├── Mark all required steps as completed                │   │
│  │ ├── Generate completion certificate/reference           │   │
│  │ ├── Update processing metrics and analytics             │   │
│  │ └── Prepare for next workflow stage (if applicable)     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ WHATSAPP STATUS NOTIFICATION                            │   │
│  │                                                         │   │
│  │ STEP 1: NOTIFICATION PREPARATION                        │   │
│  │ ├── Template: Application Status Update Template        │   │
│  │ ├── Parameters: [customerName, applicationId, status]   │   │
│  │ ├── Personalized message with next steps                │   │
│  │ └── Include timeline and contact information            │   │
│  │                                                         │   │
│  │ STEP 2: DELIVERY & CONFIRMATION                         │   │
│  │ ├── Send WhatsApp notification to customer              │   │
│  │ ├── Track delivery and read receipts                    │   │
│  │ ├── Log notification in conversation history            │   │
│  │ └── Handle delivery failures with retry logic           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ RESPONSE GENERATION                                     │   │
│  │                                                         │   │
│  │ SUCCESS RESPONSE (HTTP 200):                            │   │
│  │ {                                                       │   │
│  │   "success": true,                                      │   │
│  │   "basic_application_id": "B002BJF",                    │   │
│  │   "reference_id": "uuid-string",                        │   │
│  │   "message": "Lead Flash processed successfully",       │   │
│  │   "status": "completed",                                │   │
│  │   "next_steps": [                                       │   │
│  │     "Document verification",                            │   │
│  │     "Property valuation",                               │   │
│  │     "Final approval"                                    │   │
│  │   ]                                                     │   │
│  │ }                                                       │   │
│  │                                                         │   │
│  │ ERROR RESPONSES:                                        │   │
│  │ ├── 422: Missing required fields (applicationId, etc.)  │   │
│  │ ├── 400: Invalid application ID or API failures         │   │
│  │ ├── 404: Application not found                          │   │
│  │ └── 500: Internal processing errors                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Flash Processing Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Existing      │───▶│   Lead Flash   │───▶│ Self-Fulfillment│
│  Application    │    │      API        │    │      API        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Property      │    │   WhatsApp      │
│   (Status       │    │  Processing     │    │  Notification   │
│   Update)       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Required vs Optional Fields Matrix

|----------------|-----------------|-----------------|
| Field Category | Required Fields | Optional Fields |
|----------------|-----------------|-----------------|
| Application | applicationId, professionId, professionName | - |
| Property | - | propertyIdentified, propertyName, propertyType, agreementType, propertyValue |
| Employment | - | salaryCreditModeId, companyName, selfCompanyTypeId |
| Financial | - | coBorrowerIncome |

### Processing Stages

1. **Validation Stage**: Verify existing application and new data
2. **Integration Stage**: Merge data and call Self-Fulfillment API
3. **Processing Stage**: Handle property and profession details
4. **Completion Stage**: Update status and send notifications
5. **Audit Stage**: Log all changes and maintain compliance

---

## 2. 🔐 OTP API (`otp.py`)

### Overview
The OTP API manages WhatsApp-based OTP operations with consent request functionality and multi-environment support.

### Endpoints Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         OTP API WIREFRAME                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/otp_send                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION                                        │   │
│  │ ├── phone_number (various formats supported)            │   │
│  │ ├── user_check (consent request flag)                   │   │
│  │ └── environment (orbit/homfinity)                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ PROCESSING LOGIC                                        │   │
│  │ ├── 1. Phone Number Normalization                       │   │
│  │ ├── 2. OTP Generation (6-digit random)                  │   │
│  │ ├── 3. Consent Request (if user_check = false)          │   │
│  │ │   ├── Template: consent_template_id                   │   │
│  │ │   └── Link Generation: random 12-char string          │   │
│  │ ├── 4. WhatsApp OTP Delivery                            │   │
│  │ └── 5. Database Storage (3-minute expiry)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ OUTPUT RESPONSE                                         │   │
│  │ ├── success: true                                       │   │
│  │ ├── message: "OTP sent + consent message"               │   │
│  │ └── data: { phone_number: "normalized" }                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/otp_resend                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT: phone_number                                     │   │
│  │ LOGIC: Same as send_otp but checks existing OTP         │   │
│  │ OUTPUT: New OTP with updated expiry                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/otp_verify                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION                                        │   │
│  │ ├── phone_number (normalized)                           │   │
│  │ └── otp (6-digit code)                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ VERIFICATION LOGIC                                      │   │
│  │ ├── 1. Database Lookup (by phone number)                │   │
│  │ ├── 2. OTP Match Validation                             │   │
│  │ ├── 3. Expiry Check (3-minute window)                   │   │
│  │ ├── 4. Usage Status Check (not already used)            │   │
│  │ └── 5. Mark as Used (is_used = true)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ OUTPUT RESPONSE                                         │   │
│  │ ├── success: true/false                                 │   │
│  │ ├── message: verification status                        │   │
│  │ └── data: { phone_number, verified: boolean }           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### OTP Lifecycle Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Generate  │──▶│    Send     │───▶│   Verify    |──▶│  Mark Used  │
│     OTP     │    │  WhatsApp   │    │     OTP     │    │  (Audit)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Database   │    │  Gupshup    │    │  Database   │    │  Database   │
│   Storage   │    │   API       │    │   Lookup    │    │   Update    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 3. 📊 TRACK LEADS API (`track_leads.py`)

### Overview
The Track Leads API provides comprehensive lead tracking, application status monitoring, and appointment booking capabilities.

### Endpoints Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    TRACK LEADS API WIREFRAME                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/lead_status                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION                                        │   │
│  │ ├── environment (orbit/homfinity)                       │   │
│  │ ├── mobile_number OR basic_application_id               │   │
│  │ └── At least one identifier required                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STATUS LOOKUP WORKFLOW                                  │   │
│  │ ├── 1. Database Query (leads table by identifier)       │   │
│  │ ├── 2. Basic Application API Call (external status)     │   │
│  │ ├── 3. Data Aggregation (combine internal + external)   │   │
│  │ └── 4. WhatsApp Notification (optional status update)   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ OUTPUT RESPONSE                                         │   │
│  │ ├── success: true                                       │   │
│  │ ├── message: "Lead status retrieved successfully"       │   │
│  │ ├── data: {                                             │   │
│  │ │   ├── basic_application_id: "B002BJF"                 │   │
│  │ │   ├── status: "Under Review"                          │   │
│  │ │   ├── mobile_number: "9876543210"                     │   │
│  │ │   └── additional_details: {...}                       │   │
│  │ │ }                                                     │   │
│  │ └───────────────────────────────────────────────────────│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/track_application                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION                                        │   │
│  │ ├── environment (orbit/homfinity)                       │   │
│  │ ├── mobile_number (required)                            │   │
│  │ └── application_id (optional for filtering)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ TRACKING WORKFLOW                                       │   │
│  │ ├── 1. Multi-Source Data Retrieval                      │   │
│  │ │   ├── Database leads table                            │   │
│  │ │   ├── Basic Application API                           │   │
│  │ │   └── WhatsApp conversation history                   │   │
│  │ ├── 2. Data Correlation & Enrichment                    │   │
│  │ ├── 3. Timeline Construction                            │   │
│  │ └── 4. Status Summary Generation                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ COMPREHENSIVE TRACKING RESPONSE                         │   │
│  │ ├── application_timeline: [...]                         │   │
│  │ ├── current_status: "detailed_status"                   │   │
│  │ ├── next_steps: [...]                                   │   │
│  │ └── contact_information: {...}                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/book_appointment                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION                                        │   │
│  │ ├── environment (orbit/homfinity)                       │   │
│  │ ├── reference_id (UUID from lead creation)              │   │
│  │ ├── date (DD-MM-YYYY format)                            │   │
│  │ ├── time (HH:MM AM/PM format)                           │   │
│  │ └── rm_name (optional)                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ APPOINTMENT BOOKING WORKFLOW                            │   │
│  │ ├── 1. Reference ID Validation (lead exists)            │   │
│  │ ├── 2. Calendar Integration (availability check)        │   │
│  │ ├── 3. RM Assignment (automatic or manual)              │   │
│  │ ├── 4. Database Update (appointment record)             │   │
│  │ ├── 5. Customer Notification (WhatsApp confirmation)    │   │
│  │ └── 6. RM Notification (internal system)                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ APPOINTMENT CONFIRMATION                                │   │
│  │ ├── success: true                                       │   │
│  │ ├── message: "Appointment booked successfully"          │   │
│  │ ├── basic_app_id: "B0027J8"                             │   │
│  │ ├── appointment_details: {                              │   │
│  │ │   ├── date: "30-07-2025"                              │   │
│  │ │   ├── time: "6:00 PM"                                 │   │
│  │ │   ├── rm_name: "John Smith"                           │   │
│  │ │   └── location: "Branch Address"                      │   │
│  │ │ }                                                     │   │
│  │ └───────────────────────────────────────────────────────│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Multi-Source Data Integration

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │ Basic App API   │    │   WhatsApp      │
│   (Internal)    │    │   (External)    │    │   History       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   Data Aggregation      │
                    │   & Correlation         │
                    └─────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Unified Response      │
                    │   Generation            │
                    └─────────────────────────┘
```

---

## 4. 📱 WHATSAPP WEBHOOK API (`whatsapp_webhook.py`)

### Overview
The WhatsApp Webhook API handles incoming WhatsApp messages, processes status requests, and provides intelligent automated responses.

### Endpoints Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                  WHATSAPP WEBHOOK API WIREFRAME                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  GET /api_v1/whatsapp/webhook (Webhook Verification)           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT PARAMETERS                                        │   │
│  │ ├── hub_mode (subscription verification)                │   │
│  │ ├── hub_verify_token (security token)                   │   │
│  │ └── hub_challenge (verification challenge)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ VERIFICATION LOGIC                                      │   │
│  │ ├── 1. Token Validation (security check)                │   │
│  │ ├── 2. Mode Verification (subscription setup)           │   │
│  │ └── 3. Challenge Response (WhatsApp handshake)          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ OUTPUT: hub_challenge (echo back to WhatsApp)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  POST /api_v1/whatsapp/webhook (Message Processing)            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INCOMING MESSAGE STRUCTURE                              │   │
│  │ ├── sender: { phone, name, country_code }               │   │
│  │ ├── message: { type, text, timestamp }                  │   │
│  │ ├── context: { conversation_id, app_name }              │   │
│  │ └── metadata: { webhook_signature, delivery_info }      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ MESSAGE PROCESSING PIPELINE                             │   │
│  │                                                         │   │
│  │ 1. MESSAGE VALIDATION & PARSING                         │   │
│  │    ├── Webhook signature verification                   │   │
│  │    ├── JSON structure validation                        │   │
│  │    ├── Phone number normalization                       │   │
│  │    └── Message type identification                      │   │
│  │                                                         │   │
│  │ 2. INTELLIGENT MESSAGE CLASSIFICATION                   │   │
│  │    ├── Status Check Detection                           │   │
│  │    │   ├── Keywords: "status", "check", "application"   │   │
│  │    │   ├── "loan status", "track application"           │   │
│  │    │   └── "my application", "loan details"             │   │
│  │    ├── General Inquiry Detection                        │   │
│  │    └── Spam/Invalid Message Filtering                   │   │
│  │                                                         │   │
│  │ 3. CONTEXT-AWARE PROCESSING                             │   │
│  │    ├── Customer History Lookup                          │   │
│  │    ├── Previous Conversation Analysis                   │   │
│  │    ├── Application Status Retrieval                     │   │
│  │    └── Personalization Data Gathering                   │   │
│  │                                                         │   │
│  │ 4. RESPONSE GENERATION ENGINE                           │   │
│  │    ├── Status Response Generation                       │   │
│  │    │   ├── Database Query (internal records)            │   │
│  │    │   ├── Basic Application API Call                   │   │
│  │    │   ├── Data Formatting & Personalization            │   │
│  │    │   └── Template Message Construction                │   │
│  │    ├── Error Response Generation                        │   │
│  │    │   ├── "Application not found" messages             │   │
│  │    │   ├── "Invalid phone number" responses             │   │
│  │    │   └── "Try again later" fallbacks                  │   │
│  │    └── Fallback Response Generation                     │   │
│  │        ├── General help messages                        │   │
│  │        ├── Contact information provision                │   │
│  │        └── Service menu options                         │   │
│  │                                                         │   │
│  │ 5. AUTOMATED RESPONSE DELIVERY                          │   │
│  │    ├── WhatsApp Service Integration                     │   │
│  │    ├── Template Message Sending                         │   │
│  │    ├── Delivery Status Tracking                         │   │
│  │    └── Response Logging & Analytics                     │   │
│  │                                                         │   │
│  │ 6. AUDIT & COMPLIANCE                                   │   │
│  │    ├── Conversation Logging                             │   │
│  │    ├── Response Time Tracking                           │   │
│  │    ├── Success/Failure Metrics                          │   │
│  │    └── Customer Interaction History                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ RESPONSE TYPES & EXAMPLES                               │   │
│  │                                                         │   │
│  │ STATUS RESPONSE:                                        │   │
│  │ "Hi John! Your home loan application B002BJF is         │   │
│  │  currently under review. Expected completion: 3-5       │   │
│  │  business days. Need help? Reply 'help'"                │   │
│  │                                                         │   │
│  │ ERROR RESPONSE:                                         │   │
│  │ "We couldn't find your application details. Please      │   │
│  │  check your mobile number or contact our support."      │   │
│  │                                                         │   │
│  │ FALLBACK RESPONSE:                                      │   │
│  │ "Thanks for your message! For application status,       │   │
│  │  type 'status'. For support, type 'help'."              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Intelligent Message Processing Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │───▶│   Webhook      │───▶│   Message       │
│   Platform      │    │   Receiver      │    │   Classifier    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Response      │◀───│   Response     │◀───│   Context       │
│   Delivery      │    │   Generator     │    │   Analyzer      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   Database      │    │ Basic App API   │
│   Service       │    │   Storage       │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Message Classification Matrix

|----------------|----------------------------------|-----------------------------------------|
| Message Type   |             Keywords             |          Response Action                |
|----------------|----------------------------------|-----------------------------------------|
| Status Check   | "status", "check", "application" | Database + API lookup → Status response |
| General Help   | "help", "support", "contact"     | Help menu → Service options             |
| Invalid/Spam   | Unrecognized patterns            | Fallback response → Contact info        |
| Application ID | "B002BJF", application codes     | Direct lookup → Detailed status         |

### Error Handling & Fallbacks

```
┌─────────────────┐
│ Message Received│
└─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐
│ Parse & Validate│──▶│ Classification  │
└─────────────────┘    │ Failed?         │
         │             └─────────────────┘
         ▼                       │ YES
┌─────────────────┐              ▼
│ Processing      │    ┌─────────────────┐
│ Failed?         │    │ Send Fallback   │
└─────────────────┘    │ Response        │
         │ YES         └─────────────────┘
         ▼
┌─────────────────┐
│ Send Error      │
│ Response        │
└─────────────────┘
```

---

## Cross-API Integration Architecture

### Unified Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    INTEGRATED API ECOSYSTEM                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│  │    OTP      │───▶│   LEADS    │───▶│   TRACK     │       │
│  │    API      │    │    API      │    │   LEADS     │       │
│  └─────────────┘    └─────────────┘    └─────────────┘       │
│         │                   │                   │            │
│         └───────────────────┼───────────────────┘            │
│                             ▼                                │
│                    ┌─────────────────┐                       │
│                    │   WHATSAPP      │                       │
│                    │   WEBHOOK       │                       │
│                    └─────────────────┘                       │
│                             │                                │
│                             ▼                                │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              SHARED INFRASTRUCTURE                    │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │   │
│  │  │  Database   │ │  WhatsApp   │ │ Basic App   │      │   │
│  │  │  Service    │ │  Service    │ │    API      │      │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Security & Validation Layer

```
┌────────────────────────────────────────────────────────────────┐
│                      SECURITY ARCHITECTURE                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ INPUT VALIDATION (All APIs)                             │   │
│  │ ├── Phone Number Normalization                          │   │
│  │ ├── Environment Validation (orbit/homfinity)            │   │
│  │ ├── Request Schema Validation                           │   │
│  │ ├── Rate Limiting & Throttling                          │   │
│  │ └── Authentication & Authorization                      |   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DATA PROTECTION                                         │   │
│  │ ├── OTP Security (no logging of OTP values)             │   │
│  │ ├── PII Encryption (personal data protection)           │   │
│  │ ├── Audit Trails (comprehensive logging)                │   │
│  │ └── HTTPS Enforcement (secure transmission)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ERROR HANDLING                                          │   │
│  │ ├── Consistent HTTP Status Codes                        │   │
│  │ ├── Structured Error Responses                          │   │
│  │ ├── Graceful Degradation                                │   │
│  │ └── Fallback Mechanisms                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Performance & Monitoring

### Response Time Targets

|   API Endpoint   | Target Response Time | SLA   |
|------------------|----------------------|-------|
| OTP Send/Verify  | < 2 seconds          | 99.5% |
| Lead Creation    | < 5 seconds          | 99.0% |
| Status Lookup    | < 3 seconds          | 99.5% |
| WhatsApp Webhook | < 1 second           | 99.9% |

### Monitoring Dashboard Metrics

```
┌───────────────────────────────────────────────────────────────┐
│                      MONITORING WIREFRAME                     │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  API HEALTH METRICS                                           │
│  ├── Request Volume (per minute/hour/day)                     │
│  ├── Response Times (P50, P95, P99)                           │
│  ├── Error Rates (by endpoint and error type)                 │
│  ├── Success Rates (percentage by API)                        │
│  └── Database Connection Health                               │
│                                                               │
│  BUSINESS METRICS                                             │
│  ├── OTP Success Rate (sent vs verified)                      │
│  ├── Lead Conversion Rate (created vs completed)              │
│  ├── WhatsApp Response Accuracy                               │
│  ├── Customer Satisfaction Scores                             │
│  └── Average Processing Time per Lead                         │
│                                                               │
│  INFRASTRUCTURE METRICS                                       │
│  ├── Server Resource Utilization                              │
│  ├── Database Query Performance                               │
│  ├── External API Dependency Health                           │
│  ├── WhatsApp Service Availability                            │
│  └── Storage Usage & Growth Trends                            │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

This comprehensive wireframe documentation provides detailed architectural views of all four APIs, their interactions, data flows, error handling, and monitoring capabilities. Each API is designed with scalability, security, and user experience in mind.
