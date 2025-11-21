"""
OpenAI analyzer for email content analysis and bank application information extraction.
"""


from typing import Dict, Any, List
import logging
from openai import OpenAI

from app.config.config import config
from app.utils.timezone_utils import get_ist_timestamp
from app.utils.validators import BankThreadApplications
from ..data_processing.text_extractor import extract_all_attachment_texts

logger = logging.getLogger(__name__)


class OpenAIAnalyzer:
    """OpenAI-based analyzer for email content."""
    
    def __init__(self):
        """Initialize OpenAI analyzer."""
        self.openai_config = config.get_openai_config()
        self.client = OpenAI(api_key=self.openai_config['api_key'])

    def analyze_anything(self, prompt: str) -> str:

        try:
            response = self.client.chat.completions.create(
                model=self.openai_config['model'],
                messages=[
                    {"role": "system", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in analyzing anything: {str(e)}")
            return None

    def analyze_email(self, email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze email content using OpenAI.
        
        Args:
            email_data: Email data dictionary containing content and metadata
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Check if this is thread data or individual email data
            if 'raw_emails' in email_data or 'thread_metadata' in email_data:
                # This is thread data, use thread analysis
                prompt = self._prepare_thread_analysis_prompt(email_data)
                logger.info("Using thread analysis for complex email thread data")
            else:
                # This is individual email data, use individual email analysis
                prompt = self._prepare_analysis_prompt(email_data)
                logger.info("Using individual email analysis for single email")
            
            logger.debug(f"Email analysis prompt length: {len(prompt)} characters")
            
            # Call OpenAI API
            response = self.client.beta.chat.completions.parse(
                model=self.openai_config['model'],
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email analyzer specializing in bank application processing. Your task is to extract customer disbursement information from emails between bankers and loan processing agents. CRITICAL RULES: 1) COMPANY CONTEXT: Basic Enterprises Pvt Ltd is the intermediary/agent firm that processes loan applications between banks and customers - it is NOT a bank and should NEVER be used as bank name. 2) Distinguish between email participants (bankers/agents) and actual loan customers. Only extract customer information from loan application content, NOT from email greetings, signatures, or sender/receiver details. 3) EXTRACT ALL DISBURSEMENTS: Each email may contain multiple separate disbursements for different customers. Create a SEPARATE record for each customer's disbursement - do NOT merge multiple customers into one record. For joint applications (same loan), extract the primary applicant. 4) For institutions/companies, use full company name as firstName and leave lastName empty. 5) Convert Indian currency formats correctly: 1 lakh = 100,000, 1 crore = 10,000,000. Convert amounts like '23 lakh' to 2300000, '2.3 cr' to 23000000. 6) For disbursementStage use ONLY: 'Disbursed', 'Pending', or 'No Status'. 7) For missing data use empty string '' or 'Not found' - NEVER use 'Not specified', 'N/A', 'Unknown'. 8) BANK NAME: Extract the actual lending bank/financial institution name (like HDFC Bank, ICICI Bank, SBI, etc.), NOT Basic Enterprises or any agent/intermediary names. 9) **LOAN ACCOUNT NUMBER (LAN) EXTRACTION IS CRITICAL**: Look for ALL variations including LAN, Loan Account Number, Account No, A/C No, LAN ID, Reference Number, etc. This field is essential for tracking and must not be missed."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format=BankThreadApplications,
                # max_tokens=self.openai_config['max_tokens'],
                temperature=self.openai_config['temperature']
            )

            # Initialize analysis result with disbursements data
            analysis_result = {
                "disbursementStatus": "VerifiedByAI",
                'email_thread_id': email_data.get('thread_id', ''),
                'email_subject': str(email_data.get('conversation_details', {}).get('subjects', '')),
                'email_sender': str(email_data.get('conversation_details', {}).get('senders', '')),
                'email_date': str(email_data.get('thread_metadata', {}).get('date_range','')),
                'analysis_timestamp': self._get_current_timestamp()
            }
            
            # Disbursements list
            disbursements = []

            # Parse the response
            response_content = response.choices[0].message.content
            if isinstance(response_content, str):
                import json
                response_content = json.loads(response_content)
            
            if isinstance(response_content, dict):
                disbursements = response_content.get('disbursements', None)

                if isinstance(disbursements, list):
                    # Convert each disbursement to dictionary format
                    disbursements_dict = []
                    for disbursement in disbursements:
                        disbursement.update(analysis_result)
                        disbursements_dict.append(self._convert_to_dict(disbursement))
                    
                    disbursements = disbursements_dict
                else:
                    # Handle case where disbursements is not a list - try to create BankThreadApplications object
                    try:
                        disbursement_response = BankThreadApplications(**response_content)
                        if disbursement_response.disbursements:
                            disbursements = []
                            for disb in disbursement_response.disbursements:
                                disb_dict = disb.model_dump()
                                disb_dict.update(analysis_result)
                                disbursements.append(disb_dict)
                        else:
                            disbursements = []
                    except:
                        # Handle case where disbursements is not a list
                        disbursements = []

            return disbursements
            
        except Exception as e:
            logger.error(f"Error analyzing email {str(e)}")
            # return self._create_error_result(email_data, str(e))
            return []
    
    def _prepare_analysis_prompt(self, email_data: Dict[str, Any]) -> str:
        """Prepare the analysis prompt for OpenAI.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Formatted prompt string
        """
        subject = email_data.get('subject', '')
        content = email_data.get('content', '')
        sender = email_data.get('sender', '')
        attachments = email_data.get('attachments', [])
        attachments_text = ""
        if attachments:
            # Extract text from all attachments using the comprehensive text extractor
            attachments_text = extract_all_attachment_texts(attachments)
        
        # Prepare attachment section
        attachment_section = ""
        if attachments_text:
            attachment_section = f"Attachment Content:\n{attachments_text}"
                   
        prompt = f"""
                    IMPORTANT CONTEXT: You are analyzing emails from Basic Enterprises Pvt Ltd, which is an intermediary/agent firm that processes loan applications between banks and customers. Basic Enterprises is NOT a bank and should NEVER be used as the bank name.

                    Please analyze the following email and extract customer disbursement information:

                    Email Subject: {subject}
                    Email Sender: {sender}
                    Email Content:
                    {content}

                    {attachment_section}

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
                        "basicDisbId": "123123",
                        "appBankName": "HDFC Bank",
                        "disbursementStage": "Disbursed",
                        "disbursementStatus": "VerifiedByAI",
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
        return prompt
    

    
    def _prepare_thread_analysis_prompt(self, email_data: Dict[str, Any]) -> str:
        """Prepare the analysis prompt for OpenAI.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Formatted prompt string
        """
        thread_id = email_data.get('thread_id', '')
        thread_metadata = email_data.get('thread_metadata', {})
        date_range = str(thread_metadata.get('date_range', ''))
        conversation_duration = str(thread_metadata.get('conversation_duration', ''))
        subjects = str(email_data.get('conversation_details', {}).get('subjects', ''))
        senders = str(email_data.get('conversation_details', {}).get('senders', ''))
        recepients = str(email_data.get('conversation_details', {}).get('recepients', ''))
        conversation_flow = str(email_data.get('conversation_details', {}).get('conversation_flow', ''))
        # Conversation Summary
        newline = '\n'
        conversation_summary = f"""Subjects: {subjects}{newline}Senders : {senders}{newline}Recepients : {recepients} {newline}Conversation Flow : {conversation_flow}"""
        # Combined Content
        # combined_content = str(email_data.get('content_analysis', {}).get('combined_content', ''))

        # Get the email data for the thread
        raw_emails = email_data.get('raw_emails', [])

        # Get all attachments from all raw emails
        all_attachments = []
        for raw_email in raw_emails:
            attachments = raw_email.get("attachments", [])
            all_attachments.extend(attachments)

        attachments_text = ""
        if all_attachments: 
            # Extract text from all attachments using the comprehensive text extractor
            attachments_text = extract_all_attachment_texts(all_attachments)
                   
    
        prompt = f"""
                You are an AI assistant. Analyze the following email thread data to extract all possible disbursement-related information.

                ### Thread Metadata
                Thread ID: {thread_id}
                Date Range: {date_range}
                Conversation Duration: {conversation_duration}

                ### Conversation Summary
                {conversation_summary}

                ### Attachment Content
                {attachments_text if attachments_text else "No attachments"}

                ### Instructions:
                1. **Company Context**: Basic Enterprises Pvt Ltd is the intermediary/agent firm that processes loan applications between banks and customers. Basic Enterprises is NOT a bank and should NEVER be used as bank name (appBankName). Extract the actual lending bank/financial institution name (like HDFC Bank, ICICI Bank, SBI, etc.).
                
                2. **Email Context**: These conversations are between the banker and the Basic Enterprise agents who are processing customer loan applications. You need to extract the disbursement details of the CUSTOMERS they are discussing, not the banker or agent details.
                
                3. **Customer vs Email Participants**: 
                   - IGNORE names in email greetings like "Dear Ram", "Hi John" - these are banker/agent names
                   - IGNORE sender and receiver names - these are banker/agent names
                   - ONLY extract customer names that are mentioned in the email CONTENT as loan applicants or borrowers
                   - Look for phrases like "customer name", "borrower", "applicant", "loan for Mr./Ms.", etc.
                
                4. **Data Sources**: The customer information may be unstructured and scattered across:
                   - Email body content discussing specific loan cases
                   - Attachments with loan documents, statements, or forms
                   - Tables or lists within emails showing loan details
                
                5. **Multiple Disbursement Records**: Each email may contain multiple separate disbursements for different customers. Extract **ALL disbursement records** - create a separate record for each customer/disbursement. Each record must be uniquely identified by **loanAccountNumber** and **bankAppId**. Do NOT merge multiple customers into one record.
                
                6. **Data Mapping Guidelines**:
                   - **BANK APPLICATION ID (bankAppId) EXTRACTION - CRITICAL FOR SUCCESS**:
                     * **Primary Terms**: "Bank App ID", "Bank Application ID", "Application ID", "App ID", "Application Number", "Application No", "Application Ref", "Bank Reference", "Bank Ref No", "Reference Number", "Application Code", "App No", "Bank App No"
                     * **Secondary Terms**: "Ref No", "Reference", "App Ref", "Bank Ref", "Application#", "App#", "Appl ID", "Application Code"
                     * **Variations in Text**:
                       - "Application ID: BHL123456789"
                       - "Bank App ID: HDFC2024001234"
                       - "App ID: APP789456123"
                       - "Application Number: BKA987654321"
                       - "Bank Reference: REF456789123"
                       - "Application Code: AC123456"
                       - "App No: 202400123456"
                       - "Bank App No: BA567890123"
                       - "Reference: BHL/2024/001234"
                       - "Application Ref: AR456789"
                     * **In Email Subject Lines**: "Application ID 123456789 disbursed", "App ID 987654321 approved"
                     * **Context Clues**: Usually appears near customer names, loan amounts, or disbursement details
                     * **Format Patterns**: Usually 6-20 character alphanumeric codes, may include bank/company prefixes
                     * **CRITICAL**: If no bankAppId found, use empty string "" - DO NOT use repeated defaults
                   - **LOAN ACCOUNT NUMBER (LAN) EXTRACTION - CRITICAL FOR SUCCESS**:
                     * **Primary Terms**: "LAN", "Loan Account Number", "Loan Account No", "Loan A/C No", "Account Number", "Loan Number", "L.A.N", "LAN ID", "LAN Number"
                     * **Secondary Terms**: "Account No", "A/C No", "A/C Number", "Acct No", "Reference Number", "Loan ID", "Customer ID", "Account ID", "Loan Ref"
                     * **Variations in Text**:
                       - "LAN: 0PVL2506000005110837" 
                       - "Loan Account Number: ABC123456789"
                       - "LAN ID: XYZ987654321"
                       - "Account No: 1234567890123456"
                       - "Loan A/C No: HDFC0001234567"
                       - "A/C No.: 9876543210987654"
                       - "Reference: REF123456789"
                       - "Loan Number: LN789456123"
                       - "Customer Account: CUST456789123"
                       - "Loan Reference: LR987654321"
                       - "Account ID: ACC456789123"
                     * **In Email Subject Lines**: "Disbursement for LAN 123456789", "Account 987654321 disbursed"
                     * **In Tables/Structured Data**: Look for columns with headers like:
                       - "LAN" | "Loan Account No" | "Application Number" | "Sanction Amount" | "Disbursed Amount"
                       - "Customer Name" | "Account Number" | "Amount" | "Status"
                       - "Borrower" | "LAN ID" | "Disbursement" | "Date"
                       - "Application ID" | "Bank App ID" | "App No" | "Reference"
                     * **Context Clues**: Numbers mentioned near customer names, amounts, or disbursement details
                     * **Format Patterns**: Usually 10-20 digit alphanumeric codes, may contain letters and numbers
                     * **Priority Rules**: 
                       - Use dedicated LAN/Account Number over Application Number when both present
                       - If only Application Number available, use as loanAccountNumber
                       - Bank-specific formats (e.g., HDFC, ICICI prefixes)
                     * **CRITICAL**: If no loanAccountNumber found, use empty string "" - DO NOT use repeated defaults
                   - Disbursement amount may be mentioned as "loan amount", "disbursed amount", "payout", etc.
                   - Look for context clues about disbursement status (pending, completed, in-progress)
                   - Some emails may show pending status followed by confirmation in subsequent emails
                
                7. **Currency Amount Conversion (CRITICAL)**:
                   - Convert all Indian currency formats to actual numbers (without commas)
                   - 1 lakh = 100,000 (1,00,000)
                   - 1 crore = 10,000,000 (1,00,0,000)
                   
                   **Conversion Examples:**
                   - "5 lakh" or "5L" → 500000
                   - "23 lakh" or "23L" → 2300000
                   - "2.5 lakh" or "2.5L" → 250000
                   - "1 crore" or "1 cr" or "1C" → 10000000
                   - "2.3 crore" or "2.3 cr" or "2.3C" → 23000000
                   - "1.5 crore" or "1.5 cr" → 15000000
                   - "50 thousand" → 50000
                   - "Rs. 5,00,000" → 500000
                   - "INR 23,00,000" → 2300000
                   
                   **Handle variations**: lakh/lac/L, crore/cr/C, thousand/K
                
                8. **Customer Name Extraction Rules**:
                   - Look for customer names in loan application details, not email headers/greetings
                   - Check for names associated with loan account numbers or bank application IDs
                   - Names mentioned in context of "borrower", "applicant", "customer", "loan holder"
                   - Names in attached documents or loan statements
                   - **Look for various name formats**: "Applicant name", "Customer name", "Borrower name", "Primary applicant", etc.
                   - **Extract from contexts like**: "Applicant: John Doe", "Customer Name: Jane Smith", "Primary Borrower: Ram Kumar"
                   
                   **NAME SPLITTING CRITICAL RULES**:
                   - **Individual Customers**: Always split full names into firstName and lastName
                   - firstName = First/given names, lastName = Family/surname 
                   - Examples: "RAJESH KUMAR" → firstName: "RAJESH", lastName: "KUMAR"
                   - Examples: "PRIYA SHARMA GUPTA" → firstName: "PRIYA SHARMA", lastName: "GUPTA" 
                   - Examples: "DR. AMIT SINGH" → firstName: "AMIT", lastName: "SINGH"
                   - Examples: "MR. VIKASH PANDEY" → firstName: "VIKASH", lastName: "PANDEY"
                   - **Companies/Institutions**: Put full company name in firstName, leave lastName empty
                   - Examples: "ABC Enterprises Pvt Ltd" → firstName: "ABC Enterprises Pvt Ltd", lastName: ""
                   - Examples: "XYZ Corporation" → firstName: "XYZ Corporation", lastName: ""
                   
                   **MULTIPLE DISBURSEMENTS & CUSTOMER TYPES HANDLING**:
                   - **Separate Disbursements**: When an email contains multiple disbursement rows/entries for different customers, create a SEPARATE record for each customer's disbursement
                   - **Table/List Format**: Look for tabular data, lists, or structured formats showing multiple customer disbursements
                   - **Individual Customer Names**: For individual customers, extract full name into firstName and lastName
                   - **Institution Names**: If the customer is an institution/company, extract the institution name as firstName and leave lastName empty
                   - **Joint Applications**: For joint applications (same loan with multiple applicants), extract the primary applicant name
                   - **Institution Indicators**: Look for suffixes like "Pvt Ltd", "LLC", "Inc", "Corporation", "Company", "Enterprises", "Trust", "Foundation", "Society"
                   
                   **Disbursement Extraction Examples**:
                   - **Multiple Individual Disbursements**: 
                     * "AKSHAY YUVRAJ DESHMUKH | LAN: 123 | Amount: 25L" → Record 1: firstName: "AKSHAY YUVRAJ", lastName: "DESHMUKH"
                     * "VIVEK ANGAD PANDEY | LAN: 456 | Amount: 17L" → Record 2: firstName: "VIVEK ANGAD", lastName: "PANDEY"
                   - **Joint Application**: "Primary: Rajesh Kumar, Co-applicant: Priya Kumar | LAN: 789" → One Record: firstName: "RAJESH", lastName: "KUMAR"
                   - **Institution**: "ABC Enterprises Pvt Ltd | LAN: 101" → Record: firstName: "ABC Enterprises Pvt Ltd", lastName: ""
                   - **Mixed Types**: Handle both individual and institutional customers in the same email
                
                9. **Data Formatting Rules**:
                   - **For missing/unknown values**: Use empty string "" or "Not found" - NEVER use "Not specified", "N/A", "Unknown", etc.
                   - **CRITICAL - NO REPEATED DEFAULTS**: Never use the same default value across multiple records
                     * DO NOT use: "APP001", "LAN001", "UNKNOWN", "DEFAULT", "NOT_FOUND" for multiple records
                     * DO use: Empty string "" for each record individually when data not found
                   - **For disbursementStage**: Use ONLY these exact values: "Disbursed", "Pending", "No Status" - do not create new status values
                   - **For dates**: Use YYYY-MM-DD format or leave empty if not found
                   - **For amounts**: Always use numbers without commas (e.g., 2300000, not 23,00,000)
                   - **For bankAppId**: Extract actual application IDs or use "" - never repeat placeholder values
                   - **For loanAccountNumber**: Extract actual LAN/account numbers or use "" - never repeat placeholder values
                
                10. **What to IGNORE**:
                   - Email sender/receiver names (these are banker/agent names)
                   - Names in email signatures
                   - Greetings like "Dear [Name]", "Hi [Name]", "Hello [Name]"
                   - Names followed by email domains (@basichomeloan.com, @bank.com, etc.)
                
                11. Return the extracted data in the following JSON format:

                [
                    {{
                        "bankerEmail": "email@example.com",
                        "firstName": "John",
                        "lastName": "Doe",
                        "loanAccountNumber": "LAN123456",
                        "disbursedOn": "YYYY-MM-DD",
                        "disbursedCreatedOn": "YYYY-MM-DD",
                        "sanctionDate": "YYYY-MM-DD",
                        "disbursementAmount": 500000,
                        "loanSanctionAmount": 500000,
                        "bankAppId": "BANK001",
                        "basicAppId": "BASIC001",
                        "basicDisbId": "DISB001",
                        "appBankName": "Example Bank",
                        "disbursementStage": "Disbursed",
                        "primaryborrowerMobile": "+919876543210",
                        "pdd": "cleared",
                        "otc": "cleared",
                        "sourcingChannel": "Direct",
                        "sourcingcode": "DIR001",
                        "applicationProductType": "HL",
                        "dataFound": true
                    }},
                    ...
                ]

                5. If no disbursement or bank application details are found, return a single record with all fields as "Not found" and **"dataFound": false**.
                6. **IMPORTANT**: Use only "Disbursed", "Pending", or "No Status" for disbursementStage field.
                7. **IMPORTANT**: For any missing information, use empty string "" or "Not found" - never use "Not specified", "N/A", "Unknown".
                8. **CRITICAL**: Never use repeated placeholder values like "APP001", "LAN001", "UNKNOWN" across multiple records - use empty string "" for missing data.
                9. **CRITICAL**: Each record must have unique bankAppId and loanAccountNumber when available, or empty string "" when not found.

                Respond strictly with the JSON array format as specified.

                ### Example Scenarios for Customer Name Extraction:
                
                **CORRECT Examples - Individual Customers (Name Splitting):**
                - "Loan for Mr. Rajesh Kumar has been disbursed" → firstName: "RAJESH", lastName: "KUMAR"
                - "Borrower: Priya Sharma, LAN: 12345" → firstName: "PRIYA", lastName: "SHARMA"
                - "Application ID 67890 for customer Amit Singh" → firstName: "AMIT", lastName: "SINGH"
                - "Disbursement completed for Ms. Neha Patel" → firstName: "NEHA", lastName: "PATEL"
                - "Applicant Name: Vikash Gupta" → firstName: "VIKASH", lastName: "GUPTA"
                - "Primary Applicant: Sunita Shah" → firstName: "SUNITA", lastName: "SHAH"
                - "Customer Name: Dr. Ravi Kumar" → firstName: "RAVI", lastName: "KUMAR"
                - "AKSHAY YUVRAJ DESHMUKH" → firstName: "AKSHAY YUVRAJ", lastName: "DESHMUKH"
                - "PRIYA SHARMA GUPTA" → firstName: "PRIYA SHARMA", lastName: "GUPTA"
                
                **CORRECT Examples - Multiple Separate Disbursements (Name Splitting):**
                - Table with multiple rows:
                  * Row 1: "AKSHAY YUVRAJ DESHMUKH | LAN: 123 | 25L" → Record 1: firstName: "AKSHAY YUVRAJ", lastName: "DESHMUKH"
                  * Row 2: "VIVEK ANGAD PANDEY | LAN: 456 | 17L" → Record 2: firstName: "VIVEK ANGAD", lastName: "PANDEY"
                  * Row 3: "ATUL PRAKASH BIRJE | LAN: 789 | 19L" → Record 3: firstName: "ATUL PRAKASH", lastName: "BIRJE"
                - List format: Each bullet point or numbered item represents a separate disbursement
                - Structured data: Each complete set of loan details represents one disbursement record
                
                **CORRECT Examples - Joint Applications (Single Disbursement, Name Splitting):**
                - "Primary Applicant: Rajesh Kumar, Co-applicant: Priya Kumar | LAN: 123" → One Record: firstName: "RAJESH", lastName: "KUMAR"
                - "Main Borrower: Amit Sharma & Co-borrower: Sita Sharma | LAN: 456" → One Record: firstName: "AMIT", lastName: "SHARMA"
                - "Joint applicants: Mr. Vikash Gupta and Mrs. Sunita Gupta | LAN: 789" → One Record: firstName: "VIKASH", lastName: "GUPTA"
                
                **CORRECT Examples - Institution/Company Customers (Name Handling):**
                - "Company: ABC Enterprises Pvt Ltd" → firstName: "ABC Enterprises Pvt Ltd", lastName: ""
                - "Business: XYZ Corporation, Contact: John Smith" → firstName: "XYZ Corporation", lastName: ""
                - "Firm: Kumar & Associates LLC" → firstName: "Kumar & Associates LLC", lastName: ""
                - "Institution: Shree Ram Trust" → firstName: "Shree Ram Trust", lastName: ""
                - "Organization: Tech Solutions Inc" → firstName: "Tech Solutions Inc", lastName: ""
                - "Company Name: Green Energy Foundation" → firstName: "Green Energy Foundation", lastName: ""
                - "Business entity: Modern Textiles Pvt Ltd" → firstName: "Modern Textiles Pvt Ltd", lastName: ""
                
                **INCORRECT Examples (DO NOT EXTRACT):**
                - "Dear Ram," → This is greeting to banker/agent, NOT customer
                - "Hi Suresh, please check..." → This is email communication, NOT customer
                - Email from: "poulomi.ghosh@basichomeloan.com" → This is agent/banker, NOT customer
                - "Thanks, Vikash" in signature → This is email participant, NOT customer
                
                **Data Formatting Examples:**
                - disbursementStage: "Disbursed" (if completed), "Pending" (if waiting), "No Status" (if unclear)
                - Missing data: "" or "Not found" (NEVER "Not specified", "N/A", "Unknown")
                - Dates: "2024-01-15" or "" (if not found)
                - Phone: "+919876543210" or "" (if not found)
                
                **CORRECT bankAppId/loanAccountNumber Examples:**
                - Customer 1: bankAppId: "BHL123456", loanAccountNumber: "LAN987654321"
                - Customer 2: bankAppId: "APP789456", loanAccountNumber: "HDFC0001234567"
                - Customer 3 (no data found): bankAppId: "", loanAccountNumber: ""
                - Customer 4 (partial data): bankAppId: "REF456789", loanAccountNumber: ""
                
                **WRONG Examples (DO NOT DO THIS):**
                - Customer 1: bankAppId: "UNKNOWN", loanAccountNumber: "UNKNOWN"
                - Customer 2: bankAppId: "UNKNOWN", loanAccountNumber: "UNKNOWN"  ← WRONG: Same repeated value
                - Customer 3: bankAppId: "APP001", loanAccountNumber: "LAN001"
                - Customer 4: bankAppId: "APP001", loanAccountNumber: "LAN001"  ← WRONG: Same repeated value
                
                **Currency Conversion Examples:**
                - "Loan of 25 lakh approved" → disbursementAmount: 2500000
                - "Amount: 2.3 cr" → disbursementAmount: 23000000
                - "Disbursed Rs. 15L" → disbursementAmount: 1500000
                - "Sanction: 1.5 crore" → loanSanctionAmount: 15000000
                - "Payout of 50 thousand" → disbursementAmount: 50000
                - "Amount: INR 5,50,000" → disbursementAmount: 550000

                **IMPORTANT Example - Multiple Disbursements in Table Format:**
                
                For an email containing a table like this:
                ```
                Customer Name | Loan Account No | Application Number | Sanction Amount | Disbursed Amount
                AKSHAY YUVRAJ DESHMUKH | 0PVL2506000005110837 | APPL05432522 | 2889705 | 2889705
                VIVEK ANGAD PANDEY | 0PVL2506000005111254 | APPL05433928 | 1700000 | 1700000  
                ATUL PRAKASH BIRJE | 0PVL2506000005111375 | APPL05423810 | 1981860 | 792192
                ```
                
                Extract THREE separate records:
                1. firstName: "AKSHAY YUVRAJ", lastName: "DESHMUKH", loanAccountNumber: "0PVL2506000005110837", disbursementAmount: 2889705
                2. firstName: "VIVEK ANGAD", lastName: "PANDEY", loanAccountNumber: "0PVL2506000005111254", disbursementAmount: 1700000
                3. firstName: "ATUL PRAKASH", lastName: "BIRJE", loanAccountNumber: "0PVL2506000005111375", disbursementAmount: 792192

                **CRITICAL LAN Extraction Examples:**
                
                **Scenario 1 - Direct LAN Mention:**
                "Disbursement completed for Mr. Rajesh Kumar, LAN: HL123456789, Amount: 25 lakh"
                → firstName: "RAJESH", lastName: "KUMAR", loanAccountNumber: "HL123456789"
                
                **Scenario 2 - Account Number Variation:**
                "Customer: Priya Sharma, Account No: 0HDFC2024000123456, Disbursed: Rs. 15L"
                → firstName: "PRIYA", lastName: "SHARMA", loanAccountNumber: "0HDFC2024000123456"
                
                **Scenario 3 - Multiple Variations in Same Email:**
                "LAN ID: ABC123456 - Customer: Amit Singh - A/C No: DEF789012 - Amount: 30L"
                → firstName: "AMIT", lastName: "SINGH", loanAccountNumber: "ABC123456" (use LAN ID as priority)
                
                **Scenario 4 - Table Column Headers:**
                "LAN | Customer | Amount
                XYZ456789 | NEHA PATEL | 2000000"
                → firstName: "NEHA", lastName: "PATEL", loanAccountNumber: "XYZ456789"
                
                **Scenario 5 - Subject Line LAN:**
                Subject: "Disbursement Alert - Account 9876543210 - Customer: Vikash Gupta"
                → firstName: "VIKASH", lastName: "GUPTA", loanAccountNumber: "9876543210"
                
                **Scenario 6 - Reference Number as LAN:**
                "Reference Number: REF987654321 for borrower Sunita Shah has been disbursed"
                → firstName: "SUNITA", lastName: "SHAH", loanAccountNumber: "REF987654321"
                
                **Scenario 7 - Unstructured Format:**
                "Amit (LAN: HL789456123) disbursed amount 1800000 on 2024-01-15"
                → firstName: "AMIT", lastName: "", loanAccountNumber: "HL789456123"

                ### Start your analysis now:
                """
        return prompt
    
    
    def _create_error_result(self, email_data: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Create error result when analysis fails.
        
        Args:
            email_data: Original email data
            error_message: Error message
            
        Returns:
            Error result dictionary
        """
        return {
            'bankAppId': None,
            'applicant_name': '',
            'application_status': '',
            'important_dates': [],
            'verification_points': [],
            'confidence_score': 0,
            'notes': f'Analysis failed: {error_message}',
            'requires_verification': False,
            'email_message_id': email_data.get('message_id'),
            'email_subject': email_data.get('subject'),
            'email_sender': email_data.get('sender'),
            'email_date': email_data.get('date'),
            'analysis_timestamp': self._get_current_timestamp(),
            'error': True
        }
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in IST timezone.
        
        Returns:
            Current timestamp string in IST
        """
        return get_ist_timestamp()
    
    def _convert_to_dict(self, obj) -> Dict[str, Any]:
        """Convert Pydantic model or object to dictionary.
        
        Args:
            obj: Object to convert (Pydantic model, dict, or other object)
            
        Returns:
            Dictionary representation of the object
        """
        if hasattr(obj, 'model_dump'):
            # Pydantic v2 method
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            # Pydantic v1 method
            return obj.dict()
        elif isinstance(obj, dict):
            # Already a dictionary
            return obj
        elif hasattr(obj, '__dict__'):
            # Regular object with __dict__
            return vars(obj)
        else:
            # Fallback: return empty dict for unconvertible objects
            return {}
    
    def batch_analyze_emails(self, email_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple emails in batch.
        
        Args:
            email_list: List of email data dictionaries
            
        Returns:
            List of analysis results
        """
        results = []

        for email_data in email_list:
            try:
                result = self.analyze_email(email_data)
                results.extend(result)
            except Exception as e:
                logger.error(f"Error in batch analysis {str(e)}")
        logger.info(f"Batch analysis completed {len(email_list)}")
        
        return results 