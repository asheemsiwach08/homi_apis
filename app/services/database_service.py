import time
import logging
from threading import Lock
from typing import Dict, Tuple, Optional
from typing import Dict, Optional, List

from fastapi import HTTPException
from app.config.settings import settings
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone


logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for handling Supabase database operations with multi-environment support"""
    
    def __init__(self):
        # Environment configurations
        self.supabase_orbit_url = settings.SUPABASE_ORBIT_URL
        self.supabase_orbit_service_role_key = settings.SUPABASE_ORBIT_SERVICE_ROLE_KEY

        self.supabase_homfinity_url = settings.SUPABASE_HOMFINITY_URL
        self.supabase_homfinity_service_role_key = settings.SUPABASE_HOMFINITY_SERVICE_ROLE_KEY 
        
        # Initialize clients
        self.client_orbit = None
        self.client_homfinity = None
        self.client = None  # Default client for backward compatibility
        
        # Environment determination flag
        self.environment = self._determine_environment()
        
        # Initialize Orbit client
        if self.supabase_orbit_url and self.supabase_orbit_service_role_key:
            try:
                self.client_orbit = create_client(self.supabase_orbit_url, self.supabase_orbit_service_role_key)
                logger.info("Successfully initialized Orbit Supabase client")
            except Exception as e:
                logger.error(f"Error initializing Orbit Supabase client: {e}")
                self.client_orbit = None
        else:
            logger.warning("Orbit Supabase credentials not configured")
        
        # Initialize Homfinity client
        if self.supabase_homfinity_url and self.supabase_homfinity_service_role_key:
            try:
                self.client_homfinity = create_client(self.supabase_homfinity_url, self.supabase_homfinity_service_role_key)
                logger.info("Successfully initialized Homfinity Supabase client")
            except Exception as e:
                logger.error(f"Error initializing Homfinity Supabase client: {e}")
                self.client_homfinity = None
        else:
            logger.warning("Homfinity Supabase credentials not configured")
        
        # Set default client for backward compatibility
        self.client = self._get_default_client()
        
        # Validate at least one client is available
        if not self.client_orbit and not self.client_homfinity:
            logger.error("WARNING: No Supabase clients initialized successfully.")
            logger.error("Please check your environment variables and network connectivity.")
    
    def _determine_environment(self) -> str:
        """
        Determine which environment to use as default based on configuration
        
        Returns:
            str: Environment name ('orbit', 'homfinity', or 'unknown')
        """
        # Priority logic: Use Orbit as primary if available, fallback to Homfinity
        if self.supabase_orbit_url and self.supabase_orbit_service_role_key:
            return "orbit"
        elif self.supabase_homfinity_url and self.supabase_homfinity_service_role_key:
            return "homfinity"
        else:
            return "unknown"
    
    def _get_default_client(self):
        """Get the default client based on environment determination"""
        if self.environment == "orbit" and self.client_orbit:
            return self.client_orbit
        elif self.environment == "homfinity" and self.client_homfinity:
            return self.client_homfinity
        elif self.client_orbit:
            return self.client_orbit
        elif self.client_homfinity:
            return self.client_homfinity
        else:
            return None
    
    def get_client(self, environment: str = None):
        """
        Get the appropriate Supabase client for the specified environment
        
        Args:
            environment (str, optional): Environment name ('orbit' or 'homfinity'). 
                                       If None, uses default environment.
                                       
        Returns:
            Client: Supabase client for the specified environment
            
        Raises:
            HTTPException: If the specified environment client is not available
        """
        if environment is None:
            environment = self.environment
        
        if environment.lower() == "orbit":
            if not self.client_orbit:
                raise HTTPException(
                    status_code=500,
                    detail="Orbit Supabase client not initialized. Check SUPABASE_ORBIT_URL and SUPABASE_ORBIT_SERVICE_ROLE_KEY."
                )
            return self.client_orbit
        elif environment.lower() == "homfinity":
            if not self.client_homfinity:
                raise HTTPException(
                    status_code=500,
                    detail="Homfinity Supabase client not initialized. Check SUPABASE_HOMFINITY_URL and SUPABASE_HOMFINITY_SERVICE_ROLE_KEY."
                )
            return self.client_homfinity
        else:
            # Fallback to default client
            if not self.client:
                raise HTTPException(
                    status_code=500,
                    detail="No Supabase client available. Check database configuration."
                )
            return self.client
    
    def get_client_for_table(self, table_name: str):
        """
        Get the appropriate client based on table name or data type
        
        This method implements business logic to determine which environment
        should be used for specific tables or operations.
        
        Args:
            table_name (str): Name of the table being accessed
            
        Returns:
            Client: Appropriate Supabase client for the table
        """
        # Define table-to-environment mapping
        table_environment_mapping = {
            # Orbit tables (main business operations)
            "leads": "orbit",
            "appointments": "orbit", 
            "disbursements": "orbit",
            "whatsapp_campaigns": "orbit",   # Use this for all campaign related data
            # "whatsapp_messages": "orbit",
            # Homfinity tables (if you have specific homfinity operations)
            "otp_storage": "homfinity",  # You can choose which env for OTP
            # Add more table mappings as needed
        }
        
        target_environment = table_environment_mapping.get(table_name, self.environment)
        return self.get_client(target_environment)

    def save_record_to_supabase(self, table_name: str, record: Dict, environment: str = None) -> Dict:
        """
        Save record to Supabase database
        
        Args:
            table_name: Name of the table
            record: Dictionary containing the record to save
            environment: Optional environment override
        """
        # Get appropriate client for this operation
        client = self.get_client_for_table(table_name) if environment is None else self.get_client(environment)

        if not record or not isinstance(record, dict):
            raise HTTPException(status_code=400, detail="Record is required and must be a dictionary")

        try:
            result = client.table(table_name).insert(record).execute()
            return result.data
        except Exception as e:
            logger.warning(f"Error saving record to Supabase: {str(e)}")
            return None

    # Generic method to get records from any table
    def get_records_from_table(self, table_environment: str, table_name: str, col_name: str, col_value: str, 
                             environment: str = None, where_clauses: Optional[List[Dict[str, str]]] = None,
                             order_by: Optional[str] = None, ascending: bool = True, limit: Optional[int] = None) -> List:
        """
        Get records from table with optional additional where clauses, ordering, and limit
        
        Args:
            table_environment: Environment of the table
            table_name: Name of the table
            col_name: Name of the column
            col_value: Value of the column
            environment: Optional environment override
            where_clauses: Optional list of additional where conditions
                          Format: [{"column": "col_name", "operator": "eq", "value": "col_value"}]
                          Supported operators: eq, neq, gt, gte, lt, lte, like, ilike, is_, in_, contains
            order_by: Optional column name to order by
            ascending: Whether to sort in ascending order (True) or descending (False). Default: True
            limit: Optional limit on number of records to return
            
        Returns:
            List: Records from table
        """
        # Get appropriate client for this operation
        client = self.get_client_for_table(table_environment) if environment is None else self.get_client(environment)
        try:
            # Build query starting with the base condition
            query = client.table(table_name).select("*").eq(col_name, col_value)
            
            # Add additional where clauses if provided
            if where_clauses:
                for clause in where_clauses:
                    column = clause.get("column")
                    operator = clause.get("operator", "eq")
                    value = clause.get("value")
                    
                    if not column or value is None:
                        continue
                        
                    # Apply the appropriate operator
                    if operator == "eq":
                        query = query.eq(column, value)
                    elif operator == "neq":
                        query = query.neq(column, value)
                    elif operator == "gt":
                        query = query.gt(column, value)
                    elif operator == "gte":
                        query = query.gte(column, value)
                    elif operator == "lt":
                        query = query.lt(column, value)
                    elif operator == "lte":
                        query = query.lte(column, value)
                    elif operator == "like":
                        query = query.like(column, value)
                    elif operator == "ilike":
                        query = query.ilike(column, value)
                    elif operator == "is_":
                        query = query.is_(column, value)
                    elif operator == "in_":
                        query = query.in_(column, value)
                    elif operator == "contains":
                        query = query.contains(column, value)
                    else:
                        logger.warning(f"Unsupported operator: {operator}")
            
            # Add ordering if specified
            if order_by:
                if ascending:
                    query = query.order(order_by)
                else:
                    query = query.order(order_by, desc=True)
            
            # Add limit if specified
            if limit and limit > 0:
                query = query.limit(limit)
            
            result = query.execute()  # Execute the query and get the result

            if result.data:
                return result.data if result.data else None
            else:
                return None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error getting records from table {table_name}: {str(e)}"
            )

    def update_record(self, table_environment: str, table_name: str, record_col_name: str, record_id: str, update_data: Dict, environment: str = None) -> bool:
        """
        Update the application status for a lead record
        
        Args:
            table_environment: Environment of the table
            table_name: Name of the table to update
            record_col_name: Name of the column to update
            record_id: ID of the record to update
            update_data: Dictionary containing the data to update
            environment (str, optional): Target environment ('orbit' or 'homfinity')
            
        Returns:
            Dict: Updated record
        """
        try:
            # Get appropriate client for this operation
            client = self.get_client_for_table(table_environment) if environment is None else self.get_client(environment)
            
            result = client.table(table_name).update(update_data).eq(record_col_name, record_id).execute()
            
            if result.data:
                logger.info(f"Successfully updated record in table {table_name} with record ID: {record_id}")
                return result.data
            else:
                logger.warning(f"No record found in table {table_name} with record ID: {record_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating record in table {table_name}: {e}")
            return None


    def save_whatsapp_message(self, message_data: Dict, environment: str = None) -> Dict:
        """
        Save WhatsApp message to database (simplified)
        
        Args:
            message_data: Dictionary containing message details
                - mobile: Sender's mobile number
                - message: Message content
                - payload: Full webhook payload (optional)
            environment (str, optional): Target environment ('orbit' or 'homfinity')
                
        Returns:
            Dict: Database operation result
        """
        # Get appropriate client for this operation
        client = self.get_client_for_table("whatsapp_campaigns") if environment is None else self.get_client(environment)
        
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

            # Insert data into whatsapp_messages table using appropriate client
            result = client.table("whatsapp_messages").insert(db_data).execute()
            
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

    def save_whatsapp_conversation(self, table_name: str,message_data: Dict, environment: str = None) -> Dict:
        """
        Save WhatsApp conversation to database (simplified) from different apps along with their response
        
        Args:
            message_data: Dictionary containing message details
                - will include all the details from the webhook payload need to save in the database
            environment (str, optional): Target environment ('orbit' or 'homfinity')
                
        Returns:
            Dict: Database operation result
        """
        # Get appropriate client for this operation
        client = self.get_client_for_table("whatsapp_campaigns") if environment is None else self.get_client(environment)
        try:
            # Validate mobile number before saving
            phone = message_data.get("phone")
            if not phone or phone is None or str(phone).strip() == "":
                raise HTTPException(
                        status_code=400,
                        detail=f"❌Cannot save message: phone number is required for saving the conversation, {message_data}"
                    )
                
            # Prepare data for database with proper field mapping
            db_data = message_data
        
            # Insert data into whatsapp_conversation table using appropriate client
            result = client.table(table_name).insert(db_data).execute()
            
            if result.data:
                logger.info(f"✅ WhatsApp conversation saved to database with ID: {result.data[0].get('id')}")
                return {
                    "success": True,
                    "message_id": result.data[0].get("id"),
                    "message": "✅ WhatsApp conversation saved to database"
                }
            else:
                logger.warning(f"❌ Failed to save WhatsApp conversation to database")
                raise HTTPException(
                    status_code=500,
                    detail="❌ Failed to save WhatsApp conversation to database"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Database error saving WhatsApp conversation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"❌ Database error saving WhatsApp conversation: {str(e)}"
            )
    
    def save_book_appointment_data(self, appointment_data: Dict, basic_api_response: Dict, environment: str = None) -> Dict:
        """
        Save appointment booking data to Supabase database
        
        Args:
            appointment_data: Original appointment data from request (date, time, reference_id)
            basic_api_response: Response from Basic Application API CreateTaskOrComment
            environment (str, optional): Target environment ('orbit' or 'homfinity')
            
        Returns:
            Dict: Database operation result
        """
        # Get appropriate client for this operation
        client = self.get_client_for_table("appointments") if environment is None else self.get_client(environment)
        
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
            
            logger.info(f"Book Appointment API Success Check - Has Result: {bool(result)}, Message: {message}, APP ID: {result.get('id') if result else 'None'}, Success: {is_success}")
            
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
            
            # Insert into appointments table using appropriate client
            db_result = client.table("appointments").insert(appointment_record).execute()
            
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

    def save_lead_data(self, request_data: Dict, fbb_response: Dict, self_fullfilment_response: Dict, environment: str = None) -> Dict:
        """
        Save lead data to Supabase database
        
        This method processes and stores comprehensive lead information from multiple API responses.
        It handles both successful and failed API responses, storing complete audit trails.
        Supports upsert functionality - updates existing records or creates new ones based on application ID.
        
        Args:
            request_data (Dict): Original request data from API call containing user input
            fbb_response (Dict): Response from CreateFBBByBasicUser API call
            self_fullfilment_response (Dict): Response from SelfFullfilment API call
            environment (str, optional): Target environment ('orbit' or 'homfinity')
            
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
        # Get appropriate client for this operation
        client = self.get_client_for_table("leads") if environment is None else self.get_client(environment)
        
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

            if is_success:
                logger.info(f"[{request_id}] Processing successful API response")
                # Extract data from successful API response
                result = self_fullfilment_response.get("result", {})
                primary_borrower = result.get("primaryBorrower", {})
                credit_report = result.get("primaryBorrowerCreditReportDetails", {})
                
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
                existing_check = client.table("leads").select("id, internal_status, processing_stage").eq("api_id", api_id).execute()
                if existing_check.data:
                    existing_record = existing_check.data[0]
            elif basic_app_id:
                logger.info(f"[{request_id}] Checking for existing record with Basic App ID: {basic_app_id}")
                existing_check = client.table("leads").select("id, internal_status, processing_stage").eq("basic_app_id", basic_app_id).execute()
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
                db_result = client.table("leads").update(lead_record).eq("id", existing_id).execute()
                lead_id = existing_id
                operation_type = "updated"
            else:
                # INSERT new record
                logger.info(f"[{request_id}] Inserting new lead record into database")
                db_result = client.table("leads").insert(lead_record).execute()
                
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

    def get_leads_by_mobile(self, mobile: str, environment: str = None) -> List[Dict]:
        """
        Get leads by mobile number
        
        Args:
            mobile: Mobile number to search for
            environment (str, optional): Target environment ('orbit' or 'homfinity')
            
        Returns:
            List[Dict]: List of leads
        """
        # Get appropriate client for this operation
        client = self.get_client_for_table("leads") if environment is None else self.get_client(environment)
        
        try:
            result = client.table("leads").select("*").eq("customer_mobile", mobile).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving leads by mobile: {e}")
            return []

    def get_leads_by_basic_app_id(self, basic_app_id: str, environment: str = None) -> List[Dict]:
        """
        Get leads by Basic Application ID
        
        Args:
            basic_app_id: Basic Application ID to search for
            environment (str, optional): Target environment ('orbit' or 'homfinity')
            
        Returns:
            List[Dict]: List of leads
        """
        # Get appropriate client for this operation
        client = self.get_client_for_table("leads") if environment is None else self.get_client(environment)
        
        try:
            result = client.table("leads").select("*").eq("basic_app_id", basic_app_id).order("created_at", desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving leads by Basic App ID: {e}")
            return []

    def update_lead_status(self, basic_app_id: str, new_status: str, environment: str = None) -> bool:
        """
        Update the application status for a lead record
        
        Args:
            basic_app_id: Basic Application ID to update
            new_status: New status to set
            environment (str, optional): Target environment ('orbit' or 'homfinity')
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Get appropriate client for this operation
            client = self.get_client_for_table("leads") if environment is None else self.get_client(environment)
            
            # Update the application_status and updated_at timestamp
            update_data = {
                "application_status": new_status,
                "updated_at": "now()"
            }
            
            result = client.table("leads").update(update_data).eq("basic_app_id", basic_app_id).execute()
            
            if result.data:
                logger.info(f"Successfully updated lead status for Basic App ID: {basic_app_id} to: {new_status}")
                return True
            else:
                logger.warning(f"No lead found with Basic App ID: {basic_app_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating lead status: {e}")
            return False


    def update_basic_verify_status(self, verification_id: str, verification_status: str, comments: str) -> bool:
        """
        Update the application status for a lead record
        
        Args:
            verification_id: Verification ID to update
            verification_status: Verification status to set
            comments: Comments to set
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not self.client:
            logger.error("Supabase client not initialized for lead status update")
            return False
        
        try:
            # Update the application_status and updated_at timestamp
            update_data = {
                "disbursement_status": verification_status,
                "comments": comments,
                "updated_at": "now()"
            }
            
            result = self.client.table("leads").update(update_data).eq("verification_id", verification_id).execute()
            
            if result.data:
                logger.info(f"Successfully updated lead status for Verification ID: {verification_id} to: {verification_status}")
                return True
            else:
                logger.warning(f"No lead found with Verification ID: {verification_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating lead status: {e}")
            return False

    ################################# Appointment Methods ##############################################
    # def get_appointments_by_reference_id(self, reference_id: str) -> List[Dict]:
    #     """
    #     Get appointments by reference ID
        
    #     Args:
    #         reference_id: Reference ID to search for
            
    #     Returns:
    #         List[Dict]: List of appointments
    #     """
    #     if not self.client:
    #         raise HTTPException(
    #             status_code=500,
    #             detail="Supabase client not initialized. Check database configuration."
    #         )
        
    #     try:
    #         result = self.client.table("appointments").select("*").eq("reference_id", reference_id).order("created_at", desc=True).execute()
    #         return result.data if result.data else []
    #     except Exception as e:
    #         logger.error(f"Error retrieving appointments by reference ID: {str(e)}")
    #         return []

    # def get_appointments_by_basic_app_id(self, basic_app_id: str) -> List[Dict]:
    #     """
    #     Get appointments by Basic Application ID
        
    #     Args:
    #         basic_app_id: Basic Application ID to search for
            
    #     Returns:
    #         List[Dict]: List of appointments
    #     """
    #     if not self.client:
    #         raise HTTPException(
    #             status_code=500,
    #             detail="Supabase client not initialized. Check database configuration."
    #         )
        
    #     try:
    #         result = self.client.table("appointments").select("*").eq("basic_app_id", basic_app_id).order("created_at", desc=True).execute()
    #         return result.data if result.data else []
    #     except Exception as e:
    #         logger.error(f"Error retrieving appointments by Basic App ID: {str(e)}")
    #         return []

    # def get_appointment_statistics(self) -> Dict:
    #     """
    #     Get appointment statistics
        
    #     Returns:
    #         Dict: Appointment statistics
    #     """
    #     appointment_statistics = {
    #             "total_appointments": 0,
    #             "successful_appointments": 0,
    #             "failed_appointments": 0,
    #             "open_appointments": 0,
    #             "upcoming_appointments": 0
    #         }
    #     if not self.client:
    #         return appointment_statistics
        
    #     try:
    #         result = self.client.table("appointment_statistics").select("*").execute()
    #         if result.data and len(result.data) > 0:
    #             return result.data[0]
    #         else:
    #             return appointment_statistics
    #     except Exception as e:
    #         logger.error(f"Error retrieving appointment statistics: {str(e)}")
    #         return appointment_statistics

    ################################# Disbursement Methods ##############################################
    
    def save_disbursement_data(self, disbursement_records: List[Dict], environment: str = None) -> Dict:
        """
        Save disbursement records to Supabase database.
        
        Args:
            disbursement_records: List of disbursement dictionaries from AI analysis
            environment (str, optional): Target environment ('orbit' or 'homfinity')
            
        Returns:
            Dict: Save operation statistics
        """
        # Get appropriate client for this operation
        client = self.get_client_for_table("ai_disbursements") if environment is None else self.get_client(environment)
        
        stats = {
            'total_processed': 0,
            'new_records': 0,
            'records_updated': 0,
            'validation_failed': 0,
            'errors': 0,
            'error_details': [],
            'validation_failures': [],
            'new_disbursements': []
        }
        
        try:
            for record in disbursement_records:
                stats['total_processed'] += 1
                
                try:
                    # Validate essential data before processing
                    validation_result = self._validate_disbursement_record(record)
                    if not validation_result['is_valid']:
                        stats['validation_failed'] += 1
                        validation_msg = f"Validation failed: {validation_result['reason']} for record: {record.get('loanAccountNumber') or record.get('bankAppId', 'N/A')}"
                        stats['validation_failures'].append(validation_msg)
                        logger.warning(validation_msg)
                        continue
                    else:
                        # Check for duplicates based on loan_account_number and bank_app_id
                        is_duplicate, ai_disbursement_id = self._check_disbursement_duplicate(record, client)

                        # Prepare record for database insertion
                        db_record = self._prepare_disbursement_record(record, is_duplicate)
                        
                        if is_duplicate and ai_disbursement_id != "":  #record.get('force_save', False)
                            logger.info(f"✅ Duplicate disbursement found, updating the record with ID: {ai_disbursement_id}")
                            
                            # Update the record for update query
                            update_data = {
                                "updated_at": datetime.now().isoformat(), 
                                "record_updated": True, 
                                "disbursement_status": record.get('disbursementStatus', ''), 
                                "pdd": record.get('pdd', ''), 
                                "otc": record.get('otc', ''), 
                                "ai_disbursement_id":ai_disbursement_id
                            }
                            # Update the record with the duplicate status
                            result = client.table("ai_disbursements").update(update_data).eq("ai_disbursement_id", ai_disbursement_id).execute()
                            if result.data:
                                stats['records_updated'] += 1
                                logger.info(f"✅ Disbursement record updated successfully with ID: {ai_disbursement_id}")
                                continue
                            else:
                                stats['errors'] += 1
                                error_msg = f"❌ Failed to update disbursement record with ID: {ai_disbursement_id}"
                                stats['error_details'].append(error_msg)
                                logger.error(error_msg)
                                continue
                        
                        # Insert into database
                        try:
                            # Debug: Log the record being inserted
                            logger.debug(f"Inserting disbursement record: {db_record}")
                            
                            # Validate record structure before insertion
                            clean_record = self._clean_record_for_supabase(db_record)
                            
                            result = client.table("ai_disbursements").insert(clean_record).execute()
                            
                            if result.data:
                                stats['new_records'] += 1
                                stats['new_disbursements'].append(clean_record)
                                logger.info(f"✅ Saved disbursement record with ID: {clean_record.get('ai_disbursement_id')}")
                            else:
                                stats['errors'] += 1
                                error_msg = f"❌ No data returned for record with ID: {clean_record.get('ai_disbursement_id')}"
                                stats['error_details'].append(error_msg)
                                logger.warning(error_msg)
                                
                        except Exception as insert_error:
                            stats['errors'] += 1
                            error_msg = f"❌ Database insertion failed for record with ID: {clean_record.get('ai_disbursement_id')}: {str(insert_error)}"
                            stats['error_details'].append(error_msg)
                            logger.error(error_msg)
                            # Log the problematic record for debugging
                            logger.error(f"Problematic record data with ID: {clean_record.get('ai_disbursement_id')}: {db_record}")
                            
                except Exception as e:
                    stats['errors'] += 1
                    error_msg = f"❌ Error saving disbursement record: {str(e)}"
                    stats['error_details'].append(error_msg)
                    logger.error(error_msg)
                    continue
            
            logger.info(f"✅ Disbursement save completed: {stats['new_records']} new, {stats['records_updated']} records updated, {stats['validation_failed']} validation failures, {stats['errors']} errors")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error in save_disbursement_data: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # def get_disbursements(self, filters: Dict = None, limit: int = 100, offset: int = 0) -> Dict:
    #     """
    #     Get disbursement records with filtering and pagination.
        
    #     Args:
    #         filters: Dictionary of filter criteria
    #         limit: Maximum number of records to return
    #         offset: Number of records to skip
            
    #     Returns:
    #         Dict: Paginated disbursement data
    #     """
    #     if not self.client:
    #         raise HTTPException(
    #             status_code=500,
    #             detail="Supabase client not initialized. Check database configuration."
    #         )
        
    #     try:
    #         # Start with base query on the frontend view
    #         query = self.client.table("disbursements_frontend").select("*")
            
    #         # Apply filters if provided
    #         if filters:
    #             query = self._apply_disbursement_filters(query, filters)
            
    #         # Get total count for pagination (before limit/offset)
    #         count_result = query.execute()
    #         total_count = len(count_result.data) if count_result.data else 0
            
    #         # Apply pagination
    #         query = query.range(offset, offset + limit - 1).order('processed_at', desc=True)
            
    #         # Execute query
    #         result = query.execute()
            
    #         return {
    #             'success': True,
    #             'data': result.data or [],
    #             'total_count': total_count,
    #             'limit': limit,
    #             'offset': offset,
    #             'has_more': offset + limit < total_count
    #         }
            
    #     except Exception as e:
    #         logger.error(f"Error getting disbursements: {str(e)}")
    #         raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    
    def _validate_disbursement_record(self, record: Dict) -> Dict:
        """
        Validate disbursement record before saving to database.
        
        Validation Rules:
        1. Either loanAccountNumber OR bankAppId must be present
        2. disbursementAmount must be present and not 0
        
        Args:
            record: Raw disbursement record from AI analysis
            
        Returns:
            Dict: Validation result with is_valid and reason
        """
        # Check condition 1: TODO: Recorrect this
        # Either loanAccountNumber OR bankAppId must be present
        bank_app_id = record.get('bankAppId', '').strip()
        basic_app_id = record.get('basicAppId', '').strip()
        loan_account_number = record.get('loanAccountNumber', '').strip()
        basic_disbursement_id = record.get('disbursementId', '').strip()

        if not loan_account_number and not bank_app_id and not basic_disbursement_id:
            return {
                'is_valid': False,
                'reason': 'Neither loanAccountNumber nor bankAppId nor disbursementId present in the record'
            }
        
        # Check condition 2: disbursementAmount must be present and not 0
        disbursement_amount = record.get('disbursementAmount')
        
        # Handle different data types for disbursement amount
        if disbursement_amount is None:
            return {
                'is_valid': False,
                'reason': 'disbursementAmount is missing'
            }
        
        # Convert to float for validation if it's a string
        try:
            if isinstance(disbursement_amount, str):
                # Remove any currency symbols, commas, and whitespace
                cleaned_amount = disbursement_amount.replace(',', '').replace('₹', '').replace('$', '').strip()
                if not cleaned_amount:
                    return {
                        'is_valid': False,
                        'reason': 'disbursementAmount is empty'
                    }
                disbursement_amount = float(cleaned_amount)
            else:
                disbursement_amount = float(disbursement_amount)
        except (ValueError, TypeError):
            return {
                'is_valid': False,
                'reason': 'disbursementAmount is not a valid number'
            }
        
        # Check if amount is greater than 0
        if disbursement_amount <= 0:
            return {
                'is_valid': False,
                'reason': f'disbursementAmount must be greater than 0, got: {disbursement_amount}'
            }
        
        return {
            'is_valid': True,
            'reason': 'All validation checks passed'
        }

    def _check_disbursement_duplicate(self, record: Dict, client) -> tuple[bool, str]:
        """Check if a disbursement record already exists."""
        try:
            basic_disbursement_id = record.get('disbursementId', '').strip()

            if not basic_disbursement_id or basic_disbursement_id in ['Not found', '']:
                return False, ""
            
            query = client.table("ai_disbursements").select("ai_disbursement_id")

            # Check by basic disbursement ID if loan account not found
            if basic_disbursement_id and basic_disbursement_id != 'Not found':
                result = query.eq("basic_disbursement_id", basic_disbursement_id).execute()
                if result.data:
                    ai_disbursement_id = result.data[0].get("ai_disbursement_id")
                    return True, ai_disbursement_id
            
            return False, ""
            
        except Exception as e:
            logger.warning(f"❌ Error checking disbursement duplicate: {str(e)}")
            return False, ""

    def _generate_ai_disbursement_id(self) -> str:
        """Generate a unique ID using UUID."""
        import uuid
        return str(uuid.uuid4())

    def _prepare_disbursement_record(self, record: Dict, is_duplicate: bool = False) -> Dict:
        """Prepare disbursement record for database insertion."""
        from datetime import datetime
        import re
        
        def parse_date_safely(date_str):
            """Parse date string safely to PostgreSQL-compatible format."""
            if not date_str or date_str.strip() == "":
                return None
            
            date_str = str(date_str).strip()

            try:
                from dateutil import parser
                parsed_date = parser.parse(date_str).strftime('%Y-%m-%d')
                return parsed_date
            except Exception as e:
                try:
                    # Handle various date formats
                    # DD-MM-YYYY or DD/MM/YYYY
                    if re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', date_str):
                        # Parse DD-MM-YYYY or DD/MM/YYYY
                        date_str = date_str.replace('/', '-')
                        day, month, year = date_str.split('-')
                        parsed_date = datetime(int(year), int(month), int(day))
                        return parsed_date.strftime('%Y-%m-%d')
                    
                    # YYYY-MM-DD (already correct format)
                    elif re.match(r'\d{4}-\d{1,2}-\d{1,2}', date_str):
                        # Validate and reformat for consistency
                        parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        return parsed_date.strftime('%Y-%m-%d')
                    
                    # MM/DD/YYYY
                    elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                        parsed_date = datetime.strptime(date_str, '%m/%d/%Y')
                        return parsed_date.strftime('%Y-%m-%d')

                    # DD/MM/YYYY
                    elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                        parsed_date = datetime.strptime(date_str, '%d/%m/%Y')
                        return parsed_date.strftime('%Y-%m-%d')
                    
                    # Try ISO format parsing as fallback
                    else:
                        parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        return parsed_date.strftime('%Y-%m-%d')
                        
                except (ValueError, AttributeError) as e:
                    logger.warning(f"❌ Could not parse date '{date_str}': {e}. Setting to None.")
                    return None
            
        def safe_numeric_conversion(value, default=None):
            """Safely convert numeric values to proper types."""
            if value is None or value == "":
                return default
            
            try:
                if isinstance(value, str):
                    # Remove currency symbols and commas
                    cleaned_value = value.replace(',', '').replace('₹', '').replace('$', '').strip()
                    if not cleaned_value:
                        return default
                    return float(cleaned_value)
                return float(value)
            except (ValueError, TypeError):
                logger.warning(f"❌ Could not convert '{value}' to number. Using {default}")
                return default

        return {
            "ai_disbursement_id": self._generate_ai_disbursement_id(),
            "banker_email": record.get("bankerEmail", "").strip() or None,
            "first_name": record.get("firstName", "").strip() or None,
            "last_name": record.get("lastName", "").strip() or None,
            "loan_account_number": record.get("loanAccountNumber", "").strip() or None,
            "disbursed_on": parse_date_safely(record.get("disbursedOn")),
            # "disbursed_created_on": parse_date_safely(record.get("disbursedCreatedOn")),
            "sanction_date": parse_date_safely(record.get("sanctionDate")),
            "disbursement_amount": safe_numeric_conversion(record.get("disbursementAmount")),
            "loan_sanction_amount": safe_numeric_conversion(record.get("loanSanctionAmount")),
            "bank_app_id": record.get("bankAppId", "").strip() or None,
            "basic_app_id": record.get("basicAppId", "").strip() or None,
            "basic_disbursement_id": record.get("disbursementId", "").strip() or None,
            "app_bank_name": record.get("appBankName", "").strip() or None,
            "disbursement_stage": record.get("disbursementStage", "").strip() or "VerifiedByAI",
            "disbursement_status": record.get("disbursementStatus", "").strip() or None,
            "primary_borrower_mobile": record.get("primaryBorrowerMobile", "").strip() or None,
            "pdd": record.get("pdd", "").strip() or None,
            "otc": record.get("otc", "").strip() or None,
            "sourcing_channel": record.get("sourcingChannel", "").strip() or None,
            "sourcing_code": record.get("sourcingCode", "").strip() or None,
            "application_product_type": record.get("applicationProductType", "").strip() or None,
            "comments": record.get("comments", "").strip() or None,
            "data_found": record.get("dataFound", True),
            "confidence_score": safe_numeric_conversion(record.get("confidenceScore"), 0.0),
            "extraction_method": record.get("extractionMethod", "AI"),
            "email_subject": record.get("emailSubject", "").strip() or None,
            "email_date": parse_date_safely(record.get("emailDate")),
            "source_email_id": record.get("sourceEmailId", "").strip() or None,
            # "is_duplicate": is_duplicate,
            "record_updated": True if is_duplicate else False,
            "manual_review_required": True,
            # "processed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "created_by": "system"
        }

    def _clean_record_for_supabase(self, record: Dict) -> Dict:
        """
        Clean and validate record data types for Supabase insertion.
        
        Args:
            record: Prepared disbursement record
            
        Returns:
            Dict: Cleaned record safe for Supabase insertion
        """
        cleaned_record = {}
        
        for key, value in record.items():
            # Handle None values
            if value is None:
                cleaned_record[key] = None
                continue
            
            # Handle boolean values
            if isinstance(value, bool):
                cleaned_record[key] = value
                continue
            
            # Handle numeric values
            if key in ['disbursement_amount', 'loan_sanction_amount', 'confidence_score']:
                if isinstance(value, (int, float)):
                    cleaned_record[key] = value
                elif isinstance(value, str) and value.strip():
                    try:
                        cleaned_record[key] = float(value.replace(',', '').replace('₹', '').replace('$', '').strip())
                    except ValueError:
                        logger.warning(f"❌ Could not convert {key} '{value}' to float. Setting to None.")
                        cleaned_record[key] = None
                else:
                    cleaned_record[key] = None
                continue
            
            # Handle string values - ensure they're not empty strings
            if isinstance(value, str):
                cleaned_value = value.strip()
                cleaned_record[key] = cleaned_value if cleaned_value else None
            else:
                # Convert other types to string
                cleaned_record[key] = str(value)
        
        # Remove any completely empty records
        if all(v is None or v == "" for v in cleaned_record.values()):
            raise ValueError("Record contains no valid data")
        
        return cleaned_record

    def update_basic_verify_status(self, verification_id: str, verification_status: str, comments: str = None, environment: str = None) -> bool:
        """Update the verification status of a disbursement record."""
        try:
            if not verification_id:
                logger.error("Verification ID is required")
                return False
            
            # Prepare the update data
            update_data = {
                "disbursement_status": verification_status,
                "updated_at": datetime.now().isoformat()
            }
            
            if comments:
                update_data["comments"] = comments
            
            # Get appropriate client for this operation
            client = self.get_client_for_table("disbursements") if environment is None else self.get_client(environment)
            
            # Update in Supabase
            result = client.table("disbursements").update(update_data).eq("ai_disbursement_id", verification_id).execute()
            
            if result.data:
                logger.info(f"Successfully updated disbursement status to {verification_status} for ai_disbursement_id: {verification_id}")
                return True
            else:
                logger.error(f"No record found with ai_disbursement_id: {verification_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating disbursement status: {str(e)}")
            return False

    # def _apply_disbursement_filters(self, query, filters: Dict):
    #     """Apply filters to disbursement query."""
    #     if filters.get('bank_name'):
    #         query = query.ilike('app_bank_name', f"%{filters['bank_name']}%")
        
    #     if filters.get('disbursement_stage'):
    #         query = query.eq('disbursement_stage', filters['disbursement_stage'])
        
    #     if filters.get('date_from'):
    #         query = query.gte('disbursed_on', filters['date_from'])
        
    #     if filters.get('date_to'):
    #         query = query.lte('disbursed_on', filters['date_to'])
        
    #     if filters.get('amount_min') is not None:
    #         query = query.gte('disbursement_amount', filters['amount_min'])
        
    #     if filters.get('amount_max') is not None:
    #         query = query.lte('disbursement_amount', filters['amount_max'])
        
    #     if filters.get('customer_name'):
    #         customer_filter = f"%{filters['customer_name']}%"
    #         query = query.or_(f"first_name.ilike.{customer_filter},last_name.ilike.{customer_filter}")
        
    #     return query

######################################## Supabase OTP Storage ########################################

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
    #         # Table doesn't exist
    
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

######################################## Local OTP Storage ########################################
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


# Global instance with fallback mechanism - OTP Storage
try:
    otp_storage = SupabaseOTPStorage()
    logger.info("Successfully initialized Supabase OTP storage")
except Exception as e:
    logger.error(f"Warning: Could not initialize Supabase storage: {e}")
    logger.error(f"Error type: {type(e).__name__}")
    logger.error("Falling back to local storage...")
    otp_storage = LocalOTPStorage()
    logger.info("Successfully initialized Local OTP storage as fallback")

# Other database services
database_service = DatabaseService() 
