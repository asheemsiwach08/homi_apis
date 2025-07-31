import os
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from fastapi import HTTPException
from app.config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for handling Supabase database operations"""
    
    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY 
        
        if not self.supabase_url or not self.supabase_service_role_key:
            logger.error("WARNING: Supabase credentials not configured.")
            logger.error("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.")
            self.client = None
        else:
            try:
                self.client = create_client(self.supabase_url, self.supabase_service_role_key)
            except Exception as e:
                logger.error(f"Error initializing Supabase client: {e}")
                self.client = None
    
    def save_lead_data(self, lead_data: Dict, basic_api_response: Dict) -> Dict:
        """
        Save lead data to Supabase database
        
        Args:
            lead_data: Original lead data from request
            basic_api_response: Response from Basic Application API
            
        Returns:
            Dict: Database operation result
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Supabase client not initialized. Check database configuration."
            )
        
        try:            
            # Extract basic application ID from Basic API response
            basic_application_id = (
                basic_api_response.get("result", {})
                .get("basicAppId")
            )
            
            if not basic_application_id:
                raise HTTPException(
                    status_code=400,
                    detail="Basic Application ID not found in Basic API response"
                )
            
            # Format date for database (convert DD/MM/YYYY to YYYY-MM-DD)
            dob = lead_data.get("dob", "")
            if dob:
                try:
                    if '/' in dob:
                        # Convert DD/MM/YYYY to YYYY-MM-DD
                        day, month, year = dob.split('/')
                        dob = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif 'T' in dob:
                        # If it's already in ISO format, extract just the date part
                        dob = dob.split('T')[0]
                except Exception as e:
                    dob = None
            
            # Prepare data for database with proper type handling
            relation_id = basic_api_response.get("result", {}).get("id")
            customer_id = basic_api_response.get("result", {}).get("primaryBorrower", {}).get("customerId")
            
            # Ensure string values for VARCHAR fields
            if relation_id is not None:
                relation_id = str(relation_id)
            if customer_id is not None:
                customer_id = str(customer_id)
            
            db_data = {
                "basic_application_id": str(basic_application_id),
                "customer_id": customer_id,
                "relation_id": relation_id,
                "first_name": str(lead_data.get("first_name", "")),
                "last_name": str(lead_data.get("last_name", "")),
                "mobile_number": str(lead_data.get("mobile_number", "")),
                "email": str(lead_data.get("email", "")),
                "pan_number": str(lead_data.get("pan_number", "")),
                "loan_type": str(lead_data.get("loan_type", "")),
                "loan_amount": float(lead_data.get("loan_amount", 0)),
                "loan_tenure": int(lead_data.get("loan_tenure", 0)),
                "gender": str(lead_data.get("gender", "")),
                "dob": str(dob) if dob else None,
                "pin_code": str(lead_data.get("pin_code", "")),
                "basic_api_response": basic_api_response,  # Store full response for reference
                "status": "created",
                "created_at": "now()"
            }
            
            
            # Insert data into leads table
            result = self.client.table("leads").insert(db_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "database_id": result.data[0].get("id"),
                    "basic_application_id": basic_application_id,
                    "message": "Lead data saved to database"
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to save lead data to database"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(e)}"
            )
    
    def get_lead_by_application_id(self, basic_application_id: str) -> Optional[Dict]:
        """
        Get lead data by basic application ID
        
        Args:
            basic_application_id: Basicpplication ID from Basic API
            
        Returns:
            Optional[Dict]: Lead data or None if not found
        """
        if not self.client:
            return None
        
        try:
            result = self.client.table("leads").select("*").eq("basic_application_id", basic_application_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            return None
    
    def get_lead_by_mobile(self, mobile_number: str) -> Optional[Dict]:
        """
        Get lead data by mobile number
        
        Args:
            mobile_number: Mobile number
            
        Returns:
            Optional[Dict]: Lead data or None if not found
        """
        if not self.client:
            return None
        
        try:
            result = self.client.table("leads").select("*").eq("mobile_number", mobile_number).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            return None
    
    
    def update_lead_status(self, basic_application_id: str, status: str) -> bool:
        """
        Update lead status
        
        Args:
            basic_application_id: Basic Application ID
            status: New status
            
        Returns:
            bool: Success status
        """
        if not self.client:
            return False
        
        try:
            # Update the status in leads table
            result = self.client.table("leads").update({
                "leadStatus": status,
                "updated_at": "now()"
            }).eq("basic_application_id", basic_application_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            return False
    

    

    

    
    def save_whatsapp_message(self, message_data: Dict) -> Dict:
        """
        Save WhatsApp message to database (simplified)
        
        Args:
            message_data: Dictionary containing message details
                - mobile: Sender's mobile number
                - message: Message content
                - payload: Full webhook payload (optional)
                
        Returns:
            Dict: Database operation result
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Supabase client not initialized. Check database configuration."
            )
        
        try:
            # Validate mobile number before saving
            mobile = message_data.get("mobile")
            if not mobile or mobile is None or str(mobile).strip() == "":
                raise HTTPException(
                    status_code=400,
                    detail="Cannot save message: mobile number is required"
                )
            
            # Prepare data for database (simplified)
            db_data = {
                "mobile": str(mobile),
                "message": str(message_data.get("message", "")),
                "payload": message_data.get("payload")
            }
            
            # Insert data into whatsapp_messages table
            result = self.client.table("whatsapp_messages").insert(db_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "message_id": result.data[0].get("id"),
                    "message": "WhatsApp message saved to database"
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to save WhatsApp message to database"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error saving WhatsApp message: {str(e)}"
            )
    
    def save_book_appointment_data(self, appointment_data: Dict, basic_api_response: Dict) -> Dict:
        """
        Save appointment booking data to Supabase database
        
        Args:
            appointment_data: Original appointment data from request (date, time, reference_id)
            basic_api_response: Response from Basic Application API CreateTaskOrComment
            
        Returns:
            Dict: Database operation result
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Supabase client not initialized. Check database configuration."
            )
        
        try:
            from datetime import datetime
            
            # Get original input data
            original_date = appointment_data.get("date", "")
            original_time = appointment_data.get("time", "")
            reference_id = appointment_data.get("reference_id", "")
            
            # Check if API call was successful
            # For Book Appointment API, success is indicated by presence of result and success message
            result = basic_api_response.get("result", {})
            message = basic_api_response.get("message", "")
            is_success = bool(result and result.get("id") and "success" in message.lower())
            
            logger.info(f"Book Appointment API Success Check - Has Result: {bool(result)}, Message: {message}, API ID: {result.get('id') if result else 'None'}, Success: {is_success}")
            
            if is_success:
                # Extract data from successful API response (already extracted above)
                
                # Parse due_date
                due_date_str = result.get("dueDate")
                due_date = None
                if due_date_str:
                    try:
                        # Parse ISO format: "2025-07-29T18:21:00"
                        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"Could not parse due_date '{due_date_str}': {e}")
                        due_date = datetime.now()
                else:
                    due_date = datetime.now()
                
                # Parse created_date and updated_date
                created_date = None
                updated_date = None
                try:
                    created_date_str = result.get("createdDate")
                    if created_date_str:
                        created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                    
                    updated_date_str = result.get("updatedDate") 
                    if updated_date_str:
                        updated_date = datetime.fromisoformat(updated_date_str.replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"Could not parse audit dates: {e}")
                
                # Prepare appointment record for database
                appointment_record = {
                    # API Response Fields
                    "api_id": result.get("id"),
                    "wa_message_status": result.get("waMesageStatus"),
                    "comment_ref": result.get("commentRef"),
                    "comment": result.get("comment"),
                    "ref_type": result.get("refType"),
                    "basic_app_id": result.get("basicAppId"),
                    "ref_id": result.get("refId"),
                    
                    # Tenant Information
                    "created_by_tenant_name": result.get("createdByTenantName"),
                    "created_by_tenant_id": result.get("createdByTenantId"),
                    "created_by_tenant_type": result.get("createdByTenantType"),
                    "created_by_user_name": result.get("createdByUserName"),
                    "visible_to": result.get("visibleTo"),
                    
                    # Task Information
                    "task_type": result.get("type"),
                    "due_date": due_date.isoformat() if due_date else None,
                    "task_assigned_to_tenant_type": result.get("taskAssignedToTenantType"),
                    "status": result.get("status"),
                    
                    # Audit Fields
                    "created_by": result.get("createdBy"),
                    "created_date": created_date.isoformat() if created_date else None,
                    "updated_by": result.get("updatedBy"),
                    "updated_date": updated_date.isoformat() if updated_date else None,
                    "is_active": result.get("isActive"),
                    
                    # Assigned User Information
                    "assigned_to_user_id": result.get("assignedToUserId"),
                    "assigned_to_user_name": result.get("assignedToUserName"),
                    
                    # Customer Information
                    "primary_borrower_name": result.get("primaryBorrowerName"),
                    "primary_borrower_consent_status": result.get("primaryBorrowerConsentStatus"),
                    
                    # Additional Fields
                    "can_logged_in_user_delete": result.get("canLoggedInUserDelete"),
                    "can_logged_in_user_close": result.get("canLoggedInUserClose"),
                    "customer_wa_notification_direction": result.get("customerWAnotificationDirection"),
                    "logged_in_user_lost_access": result.get("loggedInUserLostAccess"),
                    
                    # Counts
                    "extended_count": result.get("extendedCount"),
                    "call_log_count": result.get("callLogCount"),
                    
                    # Original Input Data
                    "original_appointment_date": original_date,
                    "original_appointment_time": original_time,
                    "reference_id": reference_id,
                    
                    # Storage Fields
                    "tags": result.get("tags"),
                    "uploaded_docs": result.get("uploadedDocs"),
                    "basic_api_request": appointment_data,
                    "basic_api_response": basic_api_response,
                    
                    # Internal Status
                    "internal_status": "success",
                    "error_message": None
                }
                
                internal_status = "success"
                
                # Log what's being saved to database
                logger.info(f"Database Record - API ID: {appointment_record.get('api_id')}, Basic App ID: {appointment_record.get('basic_app_id')}, Status: {appointment_record.get('status')}")
                logger.info(f"Database Record - Comment: {appointment_record.get('comment')}, Comment Ref: {appointment_record.get('comment_ref')}")
                logger.info(f"Database Record Fields Count: {len(appointment_record)}")
                
            else:
                # Handle failed API response
                exception_info = basic_api_response.get("responseException", {})
                error_message = exception_info.get("exceptionMessage", "Unknown error")
                validation_errors = exception_info.get("validationErrors", [])
                
                if validation_errors:
                    error_details = ", ".join([
                        f"{err.get('name', 'field')}: {err.get('reason', 'error')}" 
                        for err in validation_errors
                    ])
                    error_message = f"{error_message}. Validation errors: {error_details}"
                
                # Prepare minimal record for failed appointment
                appointment_record = {
                    # Original Input Data
                    "original_appointment_date": original_date,
                    "original_appointment_time": original_time,
                    "reference_id": reference_id,
                    
                    # Storage Fields
                    "basic_api_request": appointment_data,
                    "basic_api_response": basic_api_response,
                    
                    # Internal Status
                    "internal_status": "failed",
                    "error_message": error_message,
                    
                    # Set minimal required fields
                    "comment": f"Failed appointment booking: {error_message}",
                    "ref_type": "Application",
                    "task_type": "Task",
                    "status": "Failed"
                }
                
                internal_status = "failed"
            
            # Insert into appointments table
            db_result = self.client.table("appointments").insert(appointment_record).execute()
            
            if db_result.data:
                appointment_id = db_result.data[0]["id"]
                basic_app_id = appointment_record.get("basic_app_id")
                
                logger.info(f"Appointment saved successfully with ID: {appointment_id}")
                
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "internal_status": internal_status,
                    "basic_app_id": basic_app_id,
                    "api_id": appointment_record.get("api_id"),
                    "comment_ref": appointment_record.get("comment_ref"),
                    "message": f"Appointment data saved successfully in database"
                }
            else:
                raise Exception("No data returned from insert operation")
                
        except Exception as e:
            logger.error(f"Error saving appointment to database: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save appointment to database: {str(e)}"
            )

    def save_lead_data(self, request_data: Dict, fbb_response: Dict, self_fullfilment_response: Dict) -> Dict:
        """
        Save lead data to Supabase database
        
        This method processes and stores comprehensive lead information from multiple API responses.
        It handles both successful and failed API responses, storing complete audit trails.
        Supports upsert functionality - updates existing records or creates new ones based on application ID.
        
        Args:
            request_data (Dict): Original request data from API call containing user input
            fbb_response (Dict): Response from CreateFBBByBasicUser API call
            self_fullfilment_response (Dict): Response from SelfFullfilment API call
            
        Returns:
            Dict: Database operation result containing:
                - success (bool): Whether the save operation succeeded
                - operation_type (str): Type of operation performed (created/updated)
                - lead_id (int): Database ID of the saved lead record
                - internal_status (str): Internal processing status (completed/failed)
                - basic_app_id (str): Basic Application ID from API response
                - api_id (str): API ID from response
                - customer_mobile (str): Customer mobile number
                - message (str): Success/failure message
                
        Raises:
            HTTPException: If Supabase client is not initialized or database operation fails
            
        Processing Flow:
            1. Validates Supabase client initialization
            2. Checks API response success status
            3. For successful responses: Maps all 60+ API fields to database columns
            4. For failed responses: Stores minimal data with error details
            5. Performs upsert operation (insert new or update existing record)
            6. Returns operation result with relevant IDs and status
        """
        if not self.client:
            logger.error("Supabase client not initialized for lead saving")
            raise HTTPException(
                status_code=500,
                detail="Supabase client not initialized. Check database configuration."
            )
        
        # Generate request identifier for logging
        customer_mobile = request_data.get("mobile", "unknown")
        customer_pan = request_data.get("pan", "unknown")
        request_id = f"{customer_mobile}_{customer_pan}"
        
        # logger.info(f"[{request_id}] Starting lead data save to database")
        
        try:
            from datetime import datetime
            
            # Check if self_fullfilment API call was successful
            # API is successful if isError is explicitly False or not present
            is_error = self_fullfilment_response.get("isError", False)
            is_success = not is_error
            # logger.info(f"[{request_id}] API response status - isError: {is_error}, Success: {is_success}")
            # logger.info(f"[{request_id}] API response keys: {list(self_fullfilment_response.keys()) if self_fullfilment_response else 'No response'}")
            
            if is_success:
                logger.info(f"[{request_id}] Processing successful API response")
                # Extract data from successful API response
                result = self_fullfilment_response.get("result", {})
                primary_borrower = result.get("primaryBorrower", {})
                credit_report = result.get("primaryBorrowerCreditReportDetails", {})
                
                # Log key information about the API response
                # logger.info(f"[{request_id}] Extracted API ID: {result.get('id')}")
                # logger.info(f"[{request_id}] Extracted Basic App ID: {result.get('basicAppId')}")
                # logger.info(f"[{request_id}] Status field values - applicationStatus: {result.get('applicationStatus')}, latestStatus: {result.get('latestStatus')}, status: {result.get('status')}")
                # logger.info(f"[{request_id}] Available result keys: {list(result.keys()) if result else 'No result object'}")
                
                # Parse dates
                application_date = None
                fbb_date = None
                customer_dob = None
                
                try:
                    app_date_str = result.get("applicationDate")
                    if app_date_str:
                        application_date = datetime.fromisoformat(app_date_str.replace('Z', '+00:00'))
                        
                    fbb_date_str = result.get("fbbDate")
                    if fbb_date_str:
                        fbb_date = datetime.fromisoformat(fbb_date_str.replace('Z', '+00:00'))
                        
                    dob_str = primary_borrower.get("dateOfBirth")
                    if dob_str:
                        customer_dob = datetime.fromisoformat(dob_str.replace('Z', '+00:00')).date()
                        
                    logger.debug(f"[{request_id}] Date parsing completed - App Date: {application_date}, FBB Date: {fbb_date}, DOB: {customer_dob}")
                except Exception as e:
                    logger.warning(f"[{request_id}] Date parsing warning: {str(e)}")
                
                # Helper function to safely convert to integer
                def safe_int(value):
                    if value is None or value == "":
                        return None
                    try:
                        return int(float(str(value)))  # Convert to float first to handle "0.0" cases
                    except (ValueError, TypeError):
                        return None
                
                # Prepare lead record for database
                lead_record = {
                    # Core Application Fields
                    "api_id": result.get("id"),
                    "basic_app_id": result.get("basicAppId"),
                    "loan_type": result.get("loanType"),
                    "loan_amount_req": result.get("loanAmountReq"),
                    "loan_tenure": safe_int(result.get("loanTenure")),
                    
                    # Application Status & Dates
                    "application_date": application_date.isoformat() if application_date else None,
                    "application_status": (result.get("applicationStatus") or 
                                      result.get("latestStatus") or 
                                      result.get("status")),
                    "application_stage": result.get("applicationStage"),
                    "fbb_date": fbb_date.isoformat() if fbb_date else None,
                    "fbb_outcome": result.get("fbbOutcome"),
                    "fbb_rejection_reason": result.get("fbbRejectionReason"),
                    
                    # Verification Status
                    "tele_verification_status": result.get("teleVerificationStatus"),
                    "tele_verification_failed_reason": result.get("teleVerificationFailedReason"),
                    
                    # Assignment Fields
                    "assigned_to": result.get("assignedTo"),
                    "application_assigned_to_rm": result.get("applicationAssignedToRm"),
                    
                    # Flags & Permissions
                    "is_qualified_by_ref_agent": result.get("isQualifiedByRefAgent"),
                    "include_credit_score": result.get("includeCreditScore"),
                    "is_lead_prefilled": result.get("isLeadPrefilled"),
                    "can_activate_bank_referral": result.get("canActivateBankReferral"),
                    "is_basic_fullfilment": result.get("isBasicFullfilment"),
                    "is_cancellable_withdrawable": result.get("isCancellableWithdrawable"),
                    "can_cancel_bank_login": result.get("canCancelBankLogin"),
                    "can_skip_osv": result.get("canSkipOsv"),
                    "has_disbursements": result.get("hasDisbursements"),
                    
                    # Source & Origin
                    "source": result.get("source"),
                    "originated_by_dsa_org_id": result.get("originatedByDsaOrgId"),
                    "originated_by_dsa_user_id": result.get("originatedByDsaUserId"),
                    "dsa_org_id": result.get("dsaOrgId"),
                    
                    # Customer Information
                    "customer_id": primary_borrower.get("customerId"),
                    "customer_pan": primary_borrower.get("pan"),
                    "customer_first_name": primary_borrower.get("firstName"),
                    "customer_last_name": primary_borrower.get("lastName"),
                    "customer_gender": primary_borrower.get("gender"),
                    "customer_mobile": primary_borrower.get("mobile"),
                    "customer_email": primary_borrower.get("email"),
                    "customer_date_of_birth": customer_dob.isoformat() if customer_dob else None,
                    "customer_pincode": primary_borrower.get("pincode"),
                    "customer_city": primary_borrower.get("city"),
                    "customer_district": primary_borrower.get("district"),
                    "customer_state": primary_borrower.get("state"),
                    "customer_annual_income": primary_borrower.get("annualIncome"),
                    "customer_company_name": primary_borrower.get("companyName"),
                    "customer_profession_id": primary_borrower.get("professionId"),
                    "customer_profession_name": primary_borrower.get("professionName"),
                    "customer_consent_status": primary_borrower.get("customerConsentStatus"),
                    
                    # Financial Information
                    "co_borrower_income": result.get("coBorrowerIncome"),
                    "existing_emis": result.get("existingEmis"),
                    
                    # Credit Information
                    "credit_score": safe_int(result.get("creditScore")),
                    "credit_score_type_id": result.get("creditScoreTypeId"),
                    "customer_credit_score": safe_int(credit_report.get("customerCreditScore")),
                    "credit_report_status": credit_report.get("creditReportStatus"),
                    
                    # Scores & Badges
                    "demo_score": safe_int(result.get("demoScore")),
                    "product_score": safe_int(result.get("productScore")),
                    "fin_score": safe_int(result.get("finScore")),
                    "prop_score": safe_int(result.get("propScore")),
                    "total_score": safe_int(result.get("totalScore")),
                    "lead_badge": result.get("leadBadge"),
                    
                    # Property Information
                    "is_property_identified": result.get("isPropertyIdentified"),
                    "property_type_id": result.get("propertyTypeId"),
                    "property_project_name": result.get("propertyProjectName"),
                    "property_pincode": result.get("propertyPincode"),
                    "property_district": result.get("propertyDistrict"),
                    "builder_id": result.get("builderId"),
                    "builder_name": result.get("builderName"),
                    "project_id": result.get("projectId"),
                    "tower_id": result.get("towerId"),
                    "tower_name": result.get("towerName"),
                    
                    # Loan Usage & Agreement
                    "loan_usage_type_id": result.get("loanUsageTypeId"),
                    "aggreement_type_id": result.get("aggrementTypeId"),
                    
                    # Additional Flags
                    "is_referral_lead": result.get("isReferralLead"),
                    "referred_to_banks": safe_int(result.get("referredTobanks")),
                    "can_customer_upload_documents": result.get("canCustomerUploadDocuments"),
                    "is_pbb_lead": result.get("isPbbLead"),
                    "is_osv_by_consultant_available": result.get("isOsvByConsultantAvailable"),
                    "online_login_type": result.get("onlineLoginType"),
                    
                    # Latest References
                    "application_latest_comment_or_task_id": result.get("applicationLatestCommentOrTaskId"),
                    
                    # Qualification & Agents
                    "qualified_by_agent_user_id": result.get("qualifiedByAgentUserId"),
                    "qualified_by_agent_type": result.get("qualifiedByAgentType"),
                    "auto_referral_attempt_count": safe_int(result.get("autoReferralAttemptCount")),
                    
                    # JSONB Storage Fields
                    "application_comments": result.get("applicationComments"),
                    "documents": result.get("documents"),
                    "primary_borrower_documents": primary_borrower.get("documents"),
                    "co_borrowers": result.get("coBorrowers"),
                    "sanctions": result.get("sanctions"),
                    "disbursements": result.get("disbursements"),
                    "has_application_tags": result.get("hasApplicationTags"),
                    
                    # Original Request Data
                    "original_request_data": request_data,
                    "fbb_api_response": fbb_response,
                    "self_fullfilment_api_response": self_fullfilment_response,
                    
                    # Internal Status & Error Handling (will be set based on source endpoint below)
                    "internal_status": "completed",
                    "processing_stage": "completed",
                    "error_message": None
                }
                
                internal_status = "completed"
                logger.info(f"[{request_id}] Lead record prepared with {len(lead_record)} fields")
                
                # Log key field population status
                non_null_fields = {k: v for k, v in lead_record.items() if v is not None and v != ""}
                logger.info(f"[{request_id}] Populated {len(non_null_fields)} non-null fields in database record")
                logger.info(f"[{request_id}] Database record application_status: {lead_record.get('application_status')}")
                logger.info(f"[{request_id}] Database record internal_status: {lead_record.get('internal_status')}")
                
            else:
                logger.warning(f"[{request_id}] Processing failed API response")
                # Handle failed API response
                exception_info = self_fullfilment_response.get("responseException", {})
                error_message = exception_info.get("exceptionMessage", "Unknown error")
                validation_errors = exception_info.get("validationErrors", [])
                
                if validation_errors:
                    error_details = ", ".join([
                        f"{err.get('name', 'field')}: {err.get('reason', 'error')}" 
                        for err in validation_errors
                    ])
                    error_message = f"{error_message}. Validation errors: {error_details}"
                
                logger.error(f"[{request_id}] API failure details: {error_message}")
                
                # Prepare minimal record for failed lead
                lead_record = {
                    # Original Request Data
                    "original_request_data": request_data,
                    "fbb_api_response": fbb_response,
                    "self_fullfilment_api_response": self_fullfilment_response,
                    
                    # Internal Status & Error Handling
                    "internal_status": "failed",
                    "processing_stage": "self_fullfilment_failed",
                    "error_message": error_message,
                    
                    # Set minimal required fields from request
                    "customer_first_name": request_data.get("firstName"),
                    "customer_last_name": request_data.get("lastName"),
                    "customer_mobile": request_data.get("mobile"),
                    "customer_email": request_data.get("email"),
                    "customer_pan": request_data.get("pan"),
                    "loan_type": request_data.get("loanType"),
                    "loan_amount_req": request_data.get("loanAmountReq"),
                    "loan_tenure": safe_int(request_data.get("loanTenure"))
                }
                
                internal_status = "failed"
            
            # Set processing stage based on source endpoint for new records
            source_endpoint = request_data.get("source_endpoint", "")
            if source_endpoint == "create_lead":
                lead_record["processing_stage"] = "fbb"
                lead_record["internal_status"] = "fbb_completed"
                internal_status = "fbb_completed"
            elif source_endpoint == "lead_flash":
                lead_record["processing_stage"] = "completed"
                lead_record["internal_status"] = "completed"
                internal_status = "completed"
            
            # Check if record already exists based on API ID or Basic App ID
            existing_record = None
            api_id = lead_record.get("api_id")
            basic_app_id = lead_record.get("basic_app_id")
            
            if api_id:
                logger.info(f"[{request_id}] Checking for existing record with API ID: {api_id}")
                existing_check = self.client.table("leads").select("id, internal_status, processing_stage").eq("api_id", api_id).execute()
                if existing_check.data:
                    existing_record = existing_check.data[0]
            elif basic_app_id:
                logger.info(f"[{request_id}] Checking for existing record with Basic App ID: {basic_app_id}")
                existing_check = self.client.table("leads").select("id, internal_status, processing_stage").eq("basic_app_id", basic_app_id).execute()
                if existing_check.data:
                    existing_record = existing_check.data[0]
            
            if existing_record:
                # UPDATE existing record
                existing_id = existing_record["id"]
                existing_stage = existing_record.get("processing_stage", "")
                logger.info(f"[{request_id}] Updating existing record with ID: {existing_id}, current stage: {existing_stage}")
                
                # Determine the new processing stage based on source endpoint
                source_endpoint = request_data.get("source_endpoint", "")
                if source_endpoint == "create_lead" and existing_stage in ["", "fbb"]:
                    # If create_lead is called on existing record, update with FBB data
                    lead_record["processing_stage"] = "fbb"
                elif source_endpoint == "lead_flash":
                    # If lead_flash is called, mark as completed (full process)
                    lead_record["processing_stage"] = "completed"
                    lead_record["internal_status"] = "completed"
                
                # Update the record with new data
                db_result = self.client.table("leads").update(lead_record).eq("id", existing_id).execute()
                lead_id = existing_id
                operation_type = "updated"
            else:
                # INSERT new record
                logger.info(f"[{request_id}] Inserting new lead record into database")
                db_result = self.client.table("leads").insert(lead_record).execute()
                
                if db_result.data:
                    lead_id = db_result.data[0]["id"]
                    operation_type = "created"
                else:
                    raise Exception("No data returned from insert operation")
            
            # Return success response
            basic_app_id = lead_record.get("basic_app_id")
            logger.info(f"[{request_id}] Lead {operation_type} successfully - Database ID: {lead_id}, Basic App ID: {basic_app_id}")
            
            return {
                "success": True,
                "lead_id": lead_id,
                "internal_status": internal_status,
                "basic_app_id": basic_app_id,
                "api_id": lead_record.get("api_id"),
                "customer_mobile": lead_record.get("customer_mobile"),
                "operation_type": operation_type,
                "message": f"Lead data {operation_type} successfully in database"
            }
                
        except Exception as e:
            logger.error(f"[{request_id}] Database save error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save lead to database: {str(e)}"
            )

    def get_leads_by_mobile(self, mobile: str) -> List[Dict]:
        """
        Get leads by mobile number
        
        Args:
            mobile: Mobile number to search for
            
        Returns:
            List[Dict]: List of leads
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Supabase client not initialized. Check database configuration."
            )
        
        try:
            result = self.client.table("leads").select("*").eq("customer_mobile", mobile).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving leads by mobile: {e}")
            return []

    def get_leads_by_basic_app_id(self, basic_app_id: str) -> List[Dict]:
        """
        Get leads by Basic Application ID
        
        Args:
            basic_app_id: Basic Application ID to search for
            
        Returns:
            List[Dict]: List of leads
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Supabase client not initialized. Check database configuration."
            )
        
        try:
            result = self.client.table("leads").select("*").eq("basic_app_id", basic_app_id).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving leads by Basic App ID: {e}")
            return []

    def update_lead_status(self, basic_app_id: str, new_status: str) -> bool:
        """
        Update the application status for a lead record
        
        Args:
            basic_app_id: Basic Application ID to update
            new_status: New status to set
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self.client:
            logger.error("Supabase client not initialized for lead status update")
            return False
        
        try:
            # Update the application_status and updated_at timestamp
            update_data = {
                "application_status": new_status,
                "updated_at": "now()"
            }
            
            result = self.client.table("leads").update(update_data).eq("basic_app_id", basic_app_id).execute()
            
            if result.data:
                logger.info(f"Successfully updated lead status for Basic App ID: {basic_app_id} to: {new_status}")
                return True
            else:
                logger.warning(f"No lead found with Basic App ID: {basic_app_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating lead status: {e}")
            return False

    def get_leads_statistics(self) -> Dict:
        """
        Get leads statistics
        
        Returns:
            Dict: Leads statistics
        """
        if not self.client:
            return {
                "total_leads": 0,
                "completed_leads": 0,
                "failed_leads": 0,
                "leads_last_24h": 0,
                "avg_loan_amount": 0
            }
        
        try:
            result = self.client.table("leads_statistics").select("*").execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                return {
                    "total_leads": 0,
                    "completed_leads": 0,
                    "failed_leads": 0,
                    "leads_last_24h": 0,
                    "avg_loan_amount": 0
                }
        except Exception as e:
            logger.error(f"Error retrieving leads statistics: {e}")
            return {
                "total_leads": 0,
                "completed_leads": 0,
                "failed_leads": 0,
                "leads_last_24h": 0,
                "avg_loan_amount": 0
            }

    def get_appointments_by_reference_id(self, reference_id: str) -> List[Dict]:
        """
        Get appointments by reference ID
        
        Args:
            reference_id: Reference ID to search for
            
        Returns:
            List[Dict]: List of appointments
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Supabase client not initialized. Check database configuration."
            )
        
        try:
            result = self.client.table("appointments").select("*").eq("reference_id", reference_id).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving appointments by reference ID: {str(e)}")
            return []

    def get_appointments_by_basic_app_id(self, basic_app_id: str) -> List[Dict]:
        """
        Get appointments by Basic Application ID
        
        Args:
            basic_app_id: Basic Application ID to search for
            
        Returns:
            List[Dict]: List of appointments
        """
        if not self.client:
            raise HTTPException(
                status_code=500,
                detail="Supabase client not initialized. Check database configuration."
            )
        
        try:
            result = self.client.table("appointments").select("*").eq("basic_app_id", basic_app_id).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving appointments by Basic App ID: {str(e)}")
            return []

    def get_appointment_statistics(self) -> Dict:
        """
        Get appointment statistics
        
        Returns:
            Dict: Appointment statistics
        """
        if not self.client:
            return {
                "total_appointments": 0,
                "successful_appointments": 0,
                "failed_appointments": 0,
                "open_appointments": 0,
                "upcoming_appointments": 0
            }
        
        try:
            result = self.client.table("appointment_statistics").select("*").execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                return {
                    "total_appointments": 0,
                    "successful_appointments": 0,
                    "failed_appointments": 0,
                    "open_appointments": 0,
                    "upcoming_appointments": 0
                }
        except Exception as e:
            logger.error(f"Error retrieving appointment statistics: {str(e)}")
            return {
                "total_appointments": 0,
                "successful_appointments": 0,
                "failed_appointments": 0,
                "open_appointments": 0,
                "upcoming_appointments": 0
            }


## OTP Storage in Supabase
class SupabaseOTPStorage:
    def __init__(self):
        # Check if environment variables are set and not empty
        if not settings.SUPABASE_URL or settings.SUPABASE_URL.strip() == "":
            raise ValueError("SUPABASE_URL environment variable is required")
        
        if not settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY.strip() == "":
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")

        try:
            self.supabase: Client = create_client(
                settings.SUPABASE_URL, 
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            raise
        self.table_name = "otp_storage"
        # self._ensure_table_exists()
    
    # def _ensure_table_exists(self):
    #     """Ensure the OTP storage table exists"""
    #     try:
    #         # Check if table exists by trying to select from it
    #         self.supabase.table(self.table_name).select("id").limit(1).execute()
    #         print(f"Table {self.table_name} exists and is accessible")
    #     except Exception as e:
    #         print(f"Error accessing table {self.table_name}: {e}")
    #         print("This might be due to:")
    #         print("1. Table doesn't exist - run the SQL setup script")
    #         print("2. Permission issues - check service role permissions")
    #         print("3. RLS policies blocking access")
    #         # Table doesn't exist, create it
    #         self._create_table()
    
    # def _create_table(self):
    #     """Create the OTP storage table"""
    #     # Note: In Supabase, you typically create tables via SQL editor or migrations
    #     # This is a fallback method
    #     create_table_sql = f"""
    #     CREATE TABLE IF NOT EXISTS {self.table_name} (
    #         id SERIAL PRIMARY KEY,
    #         phone_number VARCHAR(20) NOT NULL,
    #         otp VARCHAR(10) NOT NULL,
    #         created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    #         expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    #         is_used BOOLEAN DEFAULT FALSE
    #     );
        
    #     CREATE INDEX IF NOT EXISTS idx_otp_phone_number ON {self.table_name}(phone_number);
    #     CREATE INDEX IF NOT EXISTS idx_otp_expires_at ON {self.table_name}(expires_at);
    #     """
        
    #     try:
    #         self.supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
    #     except Exception as e:
    #         print(f"Warning: Could not create table automatically: {e}")
    #         print("Please create the table manually in Supabase SQL editor:")
    #         print(create_table_sql)
    
    def set_otp(self, phone_number: str, otp: str, expiry_seconds: int):
        """Store OTP with expiry time"""
        # Use timezone-aware datetime
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)
        
        # Delete any existing OTP for this phone number
        self.supabase.table(self.table_name).delete().eq("phone_number", phone_number).execute()
        
        # Insert new OTP
        data = {
            "phone_number": phone_number,
            "otp": otp,
            "expires_at": expires_at.isoformat(),
            "is_used": False
        }
        
        self.supabase.table(self.table_name).insert(data).execute()
    
    def get_otp(self, phone_number: str) -> Optional[str]:
        """Get OTP for phone number if not expired"""
        try:
            response = self.supabase.table(self.table_name).select(
                "otp, expires_at, is_used"
            ).eq("phone_number", phone_number).eq("is_used", False).execute()
            
            if not response.data:
                return None
            
            otp_record = response.data[0]
            
            # Parse the expires_at string to timezone-aware datetime
            if isinstance(otp_record["expires_at"], str):
                # Handle ISO format string
                expires_at = datetime.fromisoformat(otp_record["expires_at"].replace("Z", "+00:00"))
            else:
                # Handle datetime object
                expires_at = otp_record["expires_at"]
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            # Compare with current UTC time
            current_time = datetime.now(timezone.utc)
            
            # Check if OTP has expired
            if current_time > expires_at:
                # Mark as expired
                self.supabase.table(self.table_name).update(
                    {"is_used": True}
                ).eq("phone_number", phone_number).execute()
                return None
            
            return otp_record["otp"]
            
        except Exception as e:
            logger.error(f"Error getting OTP: {e}")
            return None
    
    def mark_otp_as_used(self, phone_number: str):
        """Mark OTP as used after successful verification"""
        try:
            self.supabase.table(self.table_name).update(
                {"is_used": True}
            ).eq("phone_number", phone_number).execute()
        except Exception as e:
            logger.error(f"Error marking OTP as used: {e}")
    

    

    


# Global instance
try:
    otp_storage = SupabaseOTPStorage()
except Exception as e:
    logger.error(f"Warning: Could not initialize Supabase storage: {e}")
    logger.error("Error type:", type(e).__name__)
    logger.error("Falling back to local storage...")
    
    # Fallback to local storage
    import time
    from threading import Lock
    from typing import Dict, Tuple, Optional
    
    class LocalOTPStorage:
        def __init__(self):
            self._storage: Dict[str, Tuple[str, float]] = {}
            self._used_otps: Dict[str, Tuple[str, float]] = {}  # Track used OTPs
            self._lock = Lock()
        
        def set_otp(self, phone_number: str, otp: str, expiry_seconds: int):
            with self._lock:
                expiry_time = time.time() + expiry_seconds
                self._storage[phone_number] = (otp, expiry_time)
        
        def get_otp(self, phone_number: str) -> Optional[str]:
            with self._lock:
                if phone_number not in self._storage:
                    return None
                
                otp, expiry_time = self._storage[phone_number]
                
                if time.time() > expiry_time:
                    del self._storage[phone_number]
                    return None
                
                return otp
        
        def mark_otp_as_used(self, phone_number: str):
            """Mark OTP as used after successful verification"""
            with self._lock:
                if phone_number in self._storage:
                    otp, expiry_time = self._storage[phone_number]
                    self._used_otps[phone_number] = (otp, expiry_time)
                    del self._storage[phone_number]
        

    otp_storage = LocalOTPStorage() 
    
# Global database service instance
database_service = DatabaseService() 
