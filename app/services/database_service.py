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
