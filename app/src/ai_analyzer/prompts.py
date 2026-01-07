previous_single_email_prompt = """
                    IMPORTANT CONTEXT: You are analyzing emails from Basic Enterprises Pvt Ltd, which is an intermediary/agent firm that processes loan applications between banks and customers. Basic Enterprises is NOT a bank and should NEVER be used as the bank name.

                    Please analyze the following email and extract customer disbursement information:

                    Email Subject: {subject}
                    Email Sender: {sender}
                    Email Content:
                    {content}

                    The above email content must be all content of the email thread, treat this Email Content as a single email thread.

                    EXTRACTION RULES:
                    1. Extract CUSTOMER information only (not banker/agent details from email headers)
                    2. For bank name (appBankName), extract the actual lending bank (like HDFC Bank, ICICI Bank, SBI, etc.)
                    3. DO NOT use "Basic Enterprises" or any intermediary/agent names as bank name
                    4. Convert Indian currency: 1 lakh = 100,000, 1 crore = 10,000,000
                    5. Create separate records for each customer disbursement
                    6. Use 'Disbursed', 'Pending', or 'No Status' for disbursementStage
                    7. **CRITICAL: Use empty string '' or 'Not found' for missing data - NEVER repeat the same default value across multiple records**
                    8. **NAME SPLITTING RULES**: 
                       - For individual customers: Split full names into firstName and lastName
                       - firstName = First/given names, lastName = Family/surname 
                       - Examples: "RAJESH KUMAR" → firstName: "RAJESH", lastName: "KUMAR"
                       - Examples: "PRIYA SHARMA GUPTA" → firstName: "PRIYA SHARMA", lastName: "GUPTA"
                       - Examples: "DR. AMIT SINGH" → firstName: "AMIT", lastName: "SINGH"
                       - For companies: Put full company name in firstName, leave lastName empty
                       - Examples: "ABC Enterprises Pvt Ltd" → firstName: "ABC Enterprises Pvt Ltd", lastName: ""
                    9. **BANK APPLICATION ID (bankAppId) EXTRACTION CRITICAL RULES**:
                       - Look for ALL variations of bank application identifiers:
                       - **Common Terms**: "Bank App ID", "Bank Application ID", "Application ID", "App ID", "Application Number", "Application No", "Application Ref", "Bank Reference", "Bank Ref No", "Ref No", "Reference Number", "Application Code", "App No", "Bank App No"
                       - **Variations**: "App ID:", "Application ID:", "Appl ID:", "Bank App:", "Application No:", "Ref:", "Reference:", "App Ref:", "Bank Ref:", "Application#", "App#"
                       - **Patterns to Look For**:
                         * "Application ID: BHL123456789"
                         * "Bank App ID: HDFC2024001234"
                         * "App ID: APP789456123"
                         * "Application Number: BKA987654321"
                         * "Bank Reference: REF456789123"
                         * "Application Code: AC123456"
                         * "App No: 202400123456"
                         * "Bank App No: BA567890123"
                         * "Reference: BHL/2024/001234"
                       - **In Tables**: Look for columns labeled "Application ID", "App ID", "Bank App ID", "Application Number", "Reference"
                       - **Format Recognition**: Usually alphanumeric codes with 6-20 characters, may include bank/company prefixes
                       - **Context Clues**: Usually appears near customer names, loan amounts, or disbursement details
                       - **CRITICAL**: If no bankAppId found, use empty string "" - DO NOT use repeated default values like "APP001" or "UNKNOWN"
                    10. **LOAN ACCOUNT NUMBER (LAN) EXTRACTION CRITICAL RULES**:
                       - Look for ALL variations of loan account numbers in emails
                       - **Common Terms**: "LAN", "Loan Account Number", "Loan Account No", "Loan A/C No", "Account Number", "Loan Number", "L.A.N", "LAN ID", "LAN Number", "Loan A/C", "Account No"
                       - **Variations**: "LAN:", "LAN-", "LAN #", "LAN No:", "Loan A/C:", "A/C No:", "Account No:", "Loan ID:", "Reference No:", "Loan Ref:", "Account ID:"
                       - **Patterns to Look For**:
                         * "LAN: 0PVL2506000005110837"
                         * "Loan Account Number: ABC123456789"
                         * "LAN ID: XYZ987654321"
                         * "Account No: 1234567890123456"
                         * "Loan A/C No: HDFC0001234567"
                         * "Reference: REF123456789"
                         * "Loan Number: LN789456123"
                         * "Account ID: ACC456789123"
                       - **In Tables**: Look for columns labeled "LAN", "Account No", "Loan Account", "A/C Number", "Loan A/C No"
                       - **Format Recognition**: Usually 10-20 digit alphanumeric codes, may include bank prefixes
                       - **Priority**: Use actual LAN over application numbers when both are present
                       - **CRITICAL**: If no loanAccountNumber found, use empty string "" - DO NOT use repeated default values like "LAN001" or "UNKNOWN"

                    Extract information in this JSON format:
                    {{
                        "bankerEmail": "email@example.com",
                        "firstName": "John",
                        "lastName": "Doe",
                        "loanAccountNumber": "123456789",
                        "disbursedOn": "2024-01-15",
                        "disbursedCreatedOn": "2024-01-15",
                        "sanctionDate": "2024-01-15",
                        "disbursementAmount": 500000,
                        "loanSanctionAmount": 500000,
                        "bankAppId": "234234",
                        "basicAppId": "A123456",
                        "disbursementId": "A123456_D2",
                        "appBankName": "HDFC Bank",
                        "disbursementStatus": "Disbursed",
                        "disbursementStage": "VerifiedByAI",
                        "primaryborrowerMobile": "+919876543210",
                        "pdd": "cleared",
                        "otc": "cleared",
                        "sourcingChannel": "Direct",
                        "sourcingcode": "DIR001",
                        "applicationProductType": "HL",
                        "dataFound": true
                    }}

                    **CRITICAL NOTES**: 
                    1. The bankAppId field is essential - look for Application ID, Bank App ID, App ID, Application Number, Bank Reference, or any application identifier variations!
                    2. The loanAccountNumber field is essential - look for LAN, Account No, A/C No, LAN ID, Reference No, or any loan identifier variations!
                    3. **NEVER use repeated default values** - if bankAppId or loanAccountNumber not found, use empty string "" for each individual record
                    4. **DO NOT use placeholder values** like "APP001", "LAN001", "UNKNOWN", "DEFAULT" across multiple records
                    5. Each record must have unique bankAppId and loanAccountNumber when available, or empty string when not found

                    If no bank application information is found, set all fields to "Not found" and dataFound to false.
            """

latest_single_email_prompt = """
IMPORTANT CONTEXT: You are analyzing emails from Basic Enterprises Pvt Ltd, which is an intermediary/agent firm that processes loan applications between banks and customers. Basic Enterprises is NOT a bank and should NEVER be used as the bank name.

Please analyze the following email and extract customer's recent disbursement information:

Email Subject: {subject}
Email Sender: {sender}
Email Content:
{content}

EXTRACTION RULES:
1. Extract CUSTOMER information only (not banker/agent details from email headers).
2. Convert Indian currency: 1 lakh = 100,000, 1 crore = 10,000,000.
3. Create separate records for each customer disbursement.
4. **STRICTLY** use only 'Disbursement Confirmation Received', 'Disbursement Not Confirmed', 'Disbursement Confirmation Rejected' or 'Awaiting Banker Confirmation' for disbursementStage.
5. **STRICTLY** use only 'PDD Confirmation Received', 'PDD Not Confirmed', 'PDD Confirmation Rejected' or Awaiting Banker Confirmation' for pdd status.
7. **CRITICAL: Use empty string '' or 'Not found' for missing data - NEVER repeat the same default value across multiple records**.
9. **BASIC APPLICATION ID (basicAppId) EXTRACTION CRITICAL RULES**:
   - Look for ALL variations of bank application identifiers:
   - **Common Terms**: "Basic App ID", "Basic Application ID", "Application ID", "App ID", "Application Number", "Application No", "Application Ref", "Bank Reference", "Bank Ref No", "Ref No", "Reference Number", "Application Code", "App No", "Basic App No"
   - **Variations**: "App ID:", "Application ID:", "Appl ID:", "Basic App:", "Application No:", "Ref:", "Reference:", "App Ref:", "Basic Ref:", "Application#", "App#", "Basic App#"
   - **Patterns to Look For**:
      * "Application ID: BHL123456"
      * "Basic App ID: HDFC202400"
      * "App ID: APP78945"
      * "Application Number: BKA98765"
      * "Basic Reference: REF456789123"
      * "Application Code: AC12345"
      * "App No: 202400123"
      * "Basic App No: BA567890"
   - **In Tables**: Look for columns labeled "Application ID", "App ID", "Basic App ID", "Application Number", "Basic Reference".
   - **Format Recognition**: Usually alphanumeric codes with 6-20 characters, may include bank/company prefixes.
   - **Context Clues**: Usually appears near customer names, loan amounts, or disbursement details.
   - **CRITICAL**: If no basicAppId found, use empty string "" - DO NOT use repeated default values like "APP001" or "UNKNOWN".

**CRITICAL NOTES**: 
1. The basicAppId field is essential - look for Application ID, Basic App ID, App ID, Application Number, Basic Reference, or any application identifier variations!
2. The disbursementId field is essential - look for Disbursement ID, Disbursement Number, Disbursement No, Disbursement Reference, or any disbursement identifier variations!
3. **NEVER use repeated default values** - if basicAppId not found, use empty string "" for each individual record.
4. **DO NOT use placeholder values** like "APP001", "UNKNOWN", "DEFAULT" across multiple records.
5. Each record must have unique basicAppId when available, or empty string when not found.

If no basic application information is found, set all fields to "Not found" and **dataFound to false**.

Extract information in this JSON format:
{{
   "basicAppId": "A123456",
   "disbursementId": "A123456_D2",
   "disbursementDate": "2024-01-15",
   "disbursementAmount": 500000,
   "disbursementStatus": "Disbursement Confirmation Received",
   "pdd": "PDD Confirmation Received",
   "applicationProductType": "HL",
   "dataFound": true
}}
            """


latest_single_email_prompt2 = """ROLE:
You are an information extraction engine. Your task is to analyze emails sent by **Basic Enterprises Pvt Ltd**, which is an intermediary/agent firm that processes loan applications between banks and customers.

IMPORTANT CONTEXT:
- Basic Enterprises Pvt Ltd is **NOT a bank**.
- NEVER use “Basic Enterprises” as the bank name.
- Extract **only customer-related disbursement information**.

---

INPUT EMAIL DETAILS:
Email Subject: {subject}  
Email Sender: {sender}  
Email Content:
{content}

---

OBJECTIVE:
Extract the **most recent customer disbursement information** from the email.

Create **one JSON record per customer disbursement**.

---

EXTRACTION RULES (STRICT):

1. Extract **CUSTOMER information only**  
   - Ignore banker names, agent names, internal staff, or email headers.

2. Currency Conversion (India):
   - 1 lakh = 100,000  
   - 1 crore = 10,000,000  
   - Convert all disbursement amounts to absolute INR numbers.

3. Records:
   - Create a **separate record for each customer disbursement**.

4. Disbursement Status (STRICT ENUM):
   Use **ONLY ONE** of the following values:
   - "Disbursement Confirmation Received"
   - "Disbursement Not Confirmed"
   - "Disbursement Confirmation Rejected"
   - "Awaiting Banker Confirmation"

5. PDD Status (STRICT ENUM):
   Use **ONLY ONE** of the following values:
   - "PDD Confirmation Received"
   - "PDD Not Confirmed"
   - "PDD Confirmation Rejected"
   - "Awaiting Banker Confirmation"

6. Missing Data Handling:
   - Use **empty string ""** or **"Not found"** for missing values.
   - **NEVER reuse the same default value across multiple records**.

---

CRITICAL IDENTIFIER EXTRACTION RULES

### BASIC APPLICATION ID (basicAppId) — MANDATORY SEARCH

Search aggressively for **any application identifier** using the following:

#### Common Terms:
- Basic App ID
- Basic Application ID
- Application ID
- App ID
- Application Number
- Application No
- App No
- Application Ref
- Bank Reference
- Bank Ref No
- Ref No
- Reference Number
- Application Code
- Basic App No
- Basic Reference

#### Variations:
- "App ID:"
- "Application ID:"
- "Appl ID:"
- "Basic App:"
- "Application No:"
- "Ref:"
- "Reference:"
- "App Ref:"
- "Basic Ref:"
- "Application#"
- "App#"
- "Basic App#"

#### Example Patterns:
- Application ID: BHL123456
- Basic App ID: HDFC202400
- App ID: APP78945
- Application Number: BKA98765
- Basic Reference: REF456789123
- Application Code: AC12345
- App No: 202400123
- Basic App No: BA567890

#### Tables:
- Look for columns such as:
  - Application ID
  - App ID
  - Basic App ID
  - Application Number
  - Basic Reference

#### Format Clues:
- Typically alphanumeric
- Length: 6–20 characters
- May include bank or company prefixes
- Usually near customer name, loan amount, or disbursement details

⚠️ CRITICAL:
- If **basicAppId is NOT found**, use **empty string ""**
- DO NOT invent or reuse placeholder values
- DO NOT use "APP001", "UNKNOWN", or similar defaults

---

DISBURSEMENT ID (disbursementId) — MANDATORY SEARCH

Look for:
- Disbursement ID
- Disbursement Number
- Disbursement No
- Disbursement Reference
- Disbursement Ref No

Apply the same strict rules as basicAppId:
- Use empty string "" if not found
- Do NOT reuse default values across records

---

FAILURE CONDITION:
If **no basic application information is found at all**:
- Set **all fields** to "Not found"
- Set `"dataFound": false`

---

OUTPUT FORMAT (JSON — ONE OBJECT PER DISBURSEMENT):

{{
  "basicAppId": "A123456",
  "disbursementId": "A123456_D2",
  "disbursementDate": "2024-01-15",
  "disbursementAmount": 500000,
  "disbursementStatus": "Disbursement Confirmation Received",
  "pdd": "PDD Confirmation Received",
  "applicationProductType": "HL",
  "dataFound": true
}}
"""