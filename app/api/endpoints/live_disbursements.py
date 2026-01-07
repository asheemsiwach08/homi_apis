"""
Live Disbursements API

Simple endpoints for real-time monitoring and processing of disbursement emails.
"""

import time
import logging
import threading
from uuid import uuid4
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Response


from app.services.database_service import database_service
from app.src.email_processor.email_client import MailClient
from app.src.ai_analyzer.openai_analyzer import OpenAIAnalyzer
from app.services.email_processing_service import email_processing_service
from app.src.data_processing.text_extractor import match_subject_keywords
from app.services.basic_application_service import BasicApplicationService

# from app.src.email_processor.zoho_mail_client import ZohoMailClient
# from app.models.schemas import DisbursementFilters, DisbursementResponse, DisbursementStatsResponse, DisbursementRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["live-disbursements"])

# Initialize services
basic_app_service = BasicApplicationService()


# Global monitoring state
monitoring_state = {
    "is_running": False,
    "started_at": None,
    "last_check": None,
    "emails_processed": 0,
    "disbursements_found": 0,
    "errors": [],
    "config": {},
    "thread": None,
    "stop_event": threading.Event(),
    "processed_email_ids": set(),  # Track processed email message IDs
    "latest_disbursements": [],  # Store latest extracted disbursements
    "last_disbursement_check": None,  # Track when disbursements were last extracted
    "session_disbursements": []  # All disbursements in current monitoring session
}


class LiveMonitoringConfig(BaseModel):
    """Configuration for live monitoring."""
    polling_interval: int = Field(default=60, ge=10, le=4600, description="Polling interval in seconds")
    mail_client: str = Field(default="zoho", description="Mail client to use for email processing")
    email_folders: List[str] = Field(default=["INBOX"], description="Email folders to monitor")
    subject_filter: Optional[str] = Field(default=None, description="Filter emails by subject")
    sender_filter: Optional[str] = Field(default=None, description="Filter emails by sender")
    check_period_minutes: int = Field(default=5, ge=1, le=93660, description="Check emails from last N minutes")

############################################################################################
                                # Live Disbursements Start API
############################################################################################

@router.post("/live_disbursements_start")
async def start_live_monitoring(config: LiveMonitoringConfig) -> Dict[str, Any]:
    """Start live disbursement monitoring."""
    
    try:
        if monitoring_state["is_running"]:
            raise HTTPException(status_code=400, detail="Live monitoring is already running")
        
        # Validate configuration by testing connections
        email_client = MailClient()
        if not email_client.connect(mail_client=config.mail_client):
            raise HTTPException(status_code=500, detail="Failed to connect to Email Client")
        email_client.disconnect()
        
        # Test Supabase database connection
        if not database_service.client:
            logger.warning("Supabase database not connected, continuing with limited functionality")
        
        # Update monitoring state
        monitoring_state.update({
            "is_running": True,
            "started_at": datetime.now(),
            "last_check": None,
            "emails_processed": 0,
            "disbursements_found": 0,
            "errors": [],
            "config": config.dict(),
            "processed_email_ids": set(),  # Reset processed emails tracking
            "latest_disbursements": [],  # Reset latest disbursements
            "last_disbursement_check": None,
            "session_disbursements": []  # Reset session disbursements
        })
        
        # Reset stop event
        monitoring_state["stop_event"].clear()
        
        # Start monitoring thread
        monitoring_thread = threading.Thread(
            target=live_monitoring_loop,
            args=(config,),
            daemon=True
        )
        monitoring_thread.start()
        monitoring_state["thread"] = monitoring_thread
        
        logger.info("Live disbursement monitoring started")
        
        return {
            "success": True,
            "message": "Live monitoring started successfully",
            "config": config.dict(),
            "started_at": monitoring_state["started_at"].isoformat()
        }
        
    except HTTPException:
        email_processing_service.send_email(
            email_data={
                "subject": f"Live disbursement monitoring failed | Started at:{monitoring_state['started_at'].isoformat()} | Ended at: {datetime.now().isoformat()}", 
                "content": f"Issue in Live Disbursements Service: \nService Started at: {monitoring_state['started_at'].isoformat()} \nService Ended at: {datetime.now().isoformat()} \n\nError: "+str(e)+"\n\nPlease check the logs for more details."
            })
        raise
    except Exception as e:
        email_processing_service.send_email(
            email_data={
                "subject": f"Live disbursement monitoring failed | Started at:{monitoring_state['started_at'].isoformat()} | Ended at: {datetime.now().isoformat()}", 
                "content": f"Issue in Live Disbursements Service: \nService Started at: {monitoring_state['started_at'].isoformat()} \nService Ended at: {datetime.now().isoformat()} \n\nError: "+str(e)+"\n\nPlease check the logs for more details."
            })
        logger.error(f"Issue in Live Disbursements Service: \nService Started at: {monitoring_state['started_at'].isoformat()} \nService Ended at: {datetime.now().isoformat()} \n\nError: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


############################################################################################
                                # Live Disbursements Stop API
############################################################################################

@router.post("/live_disbursements_stop")
async def stop_live_monitoring() -> Dict[str, Any]:
    """Stop live disbursement monitoring."""
    
    try:
        if not monitoring_state["is_running"]:
            raise HTTPException(status_code=400, detail="Live monitoring is not running")
        
        # Signal stop
        monitoring_state["stop_event"].set()
        monitoring_state["is_running"] = False
        
        # Wait for thread to finish (with timeout)
        if monitoring_state["thread"] and monitoring_state["thread"].is_alive():
            monitoring_state["thread"].join(timeout=5.0)
        
        logger.info("Live disbursement monitoring stopped")

        subject = f"Live disbursement monitoring stopped | Started at:{monitoring_state['started_at'].isoformat()} | Ended at: {datetime.now().isoformat()}"
        content = f"Live Disbursements Service: \nService Started at: {monitoring_state['started_at'].isoformat()} \nService Ended at: {datetime.now().isoformat()} \n\nService stopped successfully."

        # Send email to the recipient emails
        email_processing_service.send_email(email_data={"subject": subject, "content": content})
        
        return {
            "success": True,
            "message": "Live monitoring stopped successfully",
            "final_stats": {
                "emails_processed": monitoring_state["emails_processed"],
                "disbursements_found": monitoring_state["disbursements_found"],
                "uptime_seconds": int((datetime.now() - monitoring_state["started_at"]).total_seconds()) if monitoring_state["started_at"] else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop live monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


############################################################################################
                                # Live Disbursements Status API
############################################################################################

@router.get("/live_disbursements_status")
async def get_monitoring_status() -> Dict[str, Any]:
    """Get current live monitoring status."""
    
    uptime_seconds = 0
    next_check = None
    
    if monitoring_state["started_at"]:
        uptime_seconds = int((datetime.now() - monitoring_state["started_at"]).total_seconds())
    
    if monitoring_state["is_running"] and monitoring_state["last_check"]:
        polling_interval = monitoring_state["config"].get("polling_interval", 60)
        next_check = monitoring_state["last_check"] + timedelta(seconds=polling_interval)
    
    return {
        "is_running": monitoring_state["is_running"],
        "started_at": monitoring_state["started_at"],
        "last_check": monitoring_state["last_check"],
        "uptime_seconds": uptime_seconds,
        "emails_processed": monitoring_state["emails_processed"],
        "disbursements_found": monitoring_state["disbursements_found"],
        "next_check": next_check,
        "error_count": len(monitoring_state["errors"]),
        "config": monitoring_state["config"]
    }


async def perform_email_check(config: LiveMonitoringConfig) -> Dict[str, Any]:
    """Perform a single email check cycle."""
    
    try:
        # Initialize services
        # zoho_client = ZohoMailClient()
        email_client = MailClient()
        ai_analyzer = OpenAIAnalyzer()
        
        # Connect to Email Client
        if not email_client.connect(mail_client=config.mail_client):
            raise Exception("Failed to connect to Email Client")
        
        # Calculate time range for new emails
        check_start = datetime.now()
        since_time = check_start - timedelta(minutes=config.check_period_minutes)
        
        logger.info(f"Checking for emails since {since_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Current time: {check_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Fetch new emails from all folders using time-based filtering
        all_emails = []
        for folder in config.email_folders:
            try:
                # # Use a broader time range for IMAP search and then filter more precisely
                # broader_since = since_time - timedelta(hours=1)  # Search 1 hour back to catch timing issues
                
                emails = email_client.find_emails(
                    # start_date=since_time,    # Making these comment, method will take care of date range
                    # end_date=check_start,
                    # subject_filter=config.subject_filter,
                    sender_filter=config.sender_filter,
                    folder=folder,
                    max_emails=20  # Increase limit but we'll filter out duplicates
                )
                
                # Apply more precise time filtering
                time_filtered_emails = []
                for email in emails:
                    email_date_str = email.get('date', '')
                    # print("🔸Email Date String: ", email_date_str)
                    
                    if email_date_str:
                        try:
                            # Parse email date and check if it's actually newer than since_time
                            from dateutil import parser
                            email_date = parser.parse(email_date_str)
                            if email_date.replace(tzinfo=None) >= since_time:
                                print(f"✅ Email Date is newer than since_time({since_time.strftime('%Y-%m-%d %H:%M:%S')})")
                                time_filtered_emails.append(email)
                            # else:
                            #     # print("❌ Email Date is older than since_time")
                            #     logger.warning(f"Email too old: {email.get('subject', '')[:30]} from {email_date_str}")
                        except Exception as e:
                            # If we can't parse the date, include the email to be safe
                            logger.warning(f"Could not parse email date '{email_date_str}': {e}")
                            # print("❌ Could not parse email date")
                            time_filtered_emails.append(email)
                    else:
                        # If no date, include the email
                        # print("❌ No email date")
                        time_filtered_emails.append(email)

                logger.info(f"Time filtered emails: {len(time_filtered_emails)} ({len(time_filtered_emails)/len(emails)*100}%)")
                
                # Apply additional filters if specified
                if config.subject_filter or config.sender_filter:
                    filtered_emails = []
                    matched_subjects = []
                    unmatched_subjects = []
                    for email in time_filtered_emails:
                        subject_match = False
                        sender_match = False
                        
                        if config.subject_filter:
                            subject = email.get('subject', '').lower()
                            # subject_match = config.subject_filter.lower() in subject
                            subject_match = match_subject_keywords(subject, config.subject_filter)
                            
                            # Optional now
                            # from app.src.data_processing.text_extractor import is_valid_subject
                            # subject_match = is_valid_subject(subject)
                            # subject_match = True
                            if subject_match:
                                matched_subjects.append(subject)
                            else:
                                unmatched_subjects.append(subject)
                            print(f"🟠 Subject Match: {subject_match} for {subject}")
                        
                        if config.sender_filter:
                            sender = email.get('sender', '').lower()
                            sender_match = config.sender_filter.lower() in sender
                        
                        if subject_match or sender_match:  # Adding here or condition to allow one of the filters to match
                            filtered_emails.append(email)
                    
                    time_filtered_emails = filtered_emails
                
                all_emails.extend(time_filtered_emails)
                logger.info(f"Found {len(time_filtered_emails)} time-filtered, subject-matched emails in folder '{folder}' (from {len(emails)} total)")
                
            except Exception as e:
                error_msg = f"Error fetching emails from folder {folder}: {str(e)}"
                monitoring_state["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error_msg
                })
                logger.error(error_msg)
            
        # Filter out already processed emails
        unprocessed_emails = []
        for email in all_emails:
            email_id = email.get('message_id') or email.get('email_num')
            if email_id and email_id not in monitoring_state["processed_email_ids"]:
                unprocessed_emails.append(email)
                monitoring_state["processed_email_ids"].add(email_id)
            else:
                logger.debug(f"Skipping already processed email: {email.get('subject', 'No Subject')[:50]}")
        
        logger.info(f"New emails to process: {len(unprocessed_emails)} (total emails found in this batch: {len(emails)})")
        
        # Process emails with AI only if we have new emails
        new_disbursements = []
        unique_basic_app_ids = set()
        upload_and_update_outcome = {
            "pdf_generated": 0, 
            "s3_uploaded": 0, 
            "disbursement_proof_sent": 0
        }
        
        if unprocessed_emails:
            for i, email_data in enumerate(unprocessed_emails):
                try:
                    subject = email_data.get('subject', 'No Subject')[:50]
                    logger.info(f"Processing email {i+1}/{len(unprocessed_emails)}: {subject}...")
                    
                    disbursements = ai_analyzer.analyze_email(email_data)
                    if disbursements:
                        # Add processing timestamp and live metadata
                        for disbursement in disbursements:
                            disbursement = ai_analyzer.confirm_disbursement(disbursement)  # Confirm the disbursement status
                            print("🔹🔹🔹 Disbursement: ", disbursement)
                            print(f"🔹🔹🔹{100*'-'}🔹🔹🔹")
                            disbursement["processed_at"] = datetime.now()
                            disbursement["processing_type"] = "live"
                            disbursement["monitoring_session"] = monitoring_state["started_at"]
                            disbursement["emailSubject"] = email_data.get('subject', '')
                            disbursement["emailSender"] = email_data.get('sender', '')
                            disbursement["emailDate"] = email_data.get('date', '')
                        
                            # Update the disbursements list with only unique disbursements
                            # if disbursement.get('basicAppId') and disbursement.get('dataFound') == True and disbursement.get('basicAppId') not in unique_basic_app_ids:
                            #     unique_basic_app_ids.add(disbursement.get('basicAppId'))
                            if disbursement.get('dataFound') == True:
                                unique_basic_app_ids.add(disbursement.get('basicAppId'))
                                print(f"🔹🔹🔹{100*'-'}🔹🔹🔹")
                                new_disbursements.append(disbursement)
                                logger.info(f"✅ Added the disbursement to the new disbursements list: {disbursement}")

                                # Also generate PDF content for the email which have passed all validations
                                from app.src.data_processing.text_extractor import gather_pdf_content, email_string_to_pdf
                                pdf_to_generate, email_dict = gather_pdf_content(email_data)
                                is_pdf_generated, pdf_bytes = email_string_to_pdf(email_dict)
                                
                                if is_pdf_generated:
                                    upload_and_update_outcome["pdf_generated"] = upload_and_update_outcome["pdf_generated"] + 1
                                    logger.info(f"PDF generated successfully for the disbursement: {disbursement.get('basicAppId')}")
                                    
                                    # Update the pdf, status and record the outcome
                                    pdf_upload_status, pdf_upload_outcome = save_pdf_and_update_disbursement_proof(disbursement=disbursement, pdf_bytes=pdf_bytes)
                                    upload_and_update_outcome["s3_uploaded"] = upload_and_update_outcome["s3_uploaded"] + pdf_upload_outcome["s3_uploaded"]
                                    upload_and_update_outcome["disbursement_proof_sent"] = upload_and_update_outcome["disbursement_proof_sent"] + pdf_upload_outcome["disbursement_proof_sent"]
                                    logger.info(f"PDF upload and update outcome: {upload_and_update_outcome}")
                                    print("🔹🔹🔹 PDF to Generate: ", pdf_to_generate)
                                    print(f"🔹🔹🔹{100*'-'}🔹🔹🔹")
                                else:
                                    logger.error(f"Failed to generate PDF for the disbursement: {disbursement.get('basicAppId')}")
                                    print(f"❌ Failed to generate PDF for the disbursement: {disbursement.get('basicAppId')}")
                                    print(f"🔹🔹🔹{100*'-'}🔹🔹🔹")
       
                except Exception as e:
                    error_msg = f"Error analyzing email {i+1} with AI Analyzer: {str(e)}"
                    monitoring_state["errors"].append({
                        "timestamp": datetime.now().isoformat(),
                        "error": error_msg,
                        "email_subject": email_data.get('subject', ''),
                        "email_sender": email_data.get('sender', ''),
                        "email_date": email_data.get('date', '')
                    })
                    logger.error(error_msg)
                    print(f"❌ Error analyzing email {i+1} with AI Analyzer: {str(e)}")
        # else:
        #     logger.info("No new emails to process")
        
        logger.info(f"Total disbursements extracted: {len(new_disbursements)}")
        
        # Save to Supabase database
        supabase_saved = 0
        if new_disbursements and database_service.client:
            try:
                logger.info(f"Saving {len(new_disbursements)} disbursements to Supabase database")
                print(f"{50*'-'}🔸🔸🔸{50*'-'}")
                print(f"✅ Final New Disbursements: {new_disbursements}")
                print(f"{50*'-'}🔸🔸🔸{50*'-'}")

                # Save disbursements to database
                save_stats = database_service.save_disbursement_data(new_disbursements)
                supabase_new_disbursements = save_stats.get('new_disbursements', [])
                supabase_saved = save_stats.get('new_records', 0)
                supabase_duplicates = save_stats.get('duplicates_skipped', 0)
                supabase_errors = save_stats.get('errors', 0)

                logger.info(f"Supabase save: {supabase_saved} new, {supabase_duplicates} duplicates, {supabase_errors} errors")
                
                if save_stats.get('error_details'):
                    monitoring_state["errors"].extend([
                        {"timestamp": datetime.now().isoformat(), "error": error} 
                        for error in save_stats['error_details'][:5]  # Limit to 5 errors
                    ])
                        
            except Exception as e:
                error_msg = f"Error saving to Supabase database: {str(e)}"
                monitoring_state["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error_msg
                })
                logger.error(error_msg)
        
        # Google Sheets integration removed - all data now saved to Supabase database
        
        # Update monitoring state with new disbursements
        monitoring_state["last_check"] = check_start
        monitoring_state["emails_processed"] += len(unprocessed_emails)  # Only count newly processed emails
        monitoring_state["disbursements_found"] += len(new_disbursements)
        
        # Store latest disbursements and update session disbursements
        if 'supabase_new_disbursements' in locals() and supabase_new_disbursements:
            monitoring_state["latest_disbursements"] = supabase_new_disbursements
            monitoring_state["last_disbursement_check"] = check_start
            monitoring_state["session_disbursements"].extend(supabase_new_disbursements)
        
        # Clean up
        email_client.disconnect()
        
        result = {
            "emails_checked": len(all_emails),
            "new_emails_processed": len(unprocessed_emails),
            "total_disbursements_found": len(new_disbursements) if 'new_disbursements' in locals() else 0,
            "new_disbursements": len(supabase_new_disbursements) if 'supabase_new_disbursements' in locals() else 0,
            "pdf_generated": upload_and_update_outcome["pdf_generated"] if 'upload_and_update_outcome' in locals() else 0,
            "s3_uploaded": upload_and_update_outcome["s3_uploaded"] if 'upload_and_update_outcome' in locals() else 0,
            "disbursement_proof_sent": upload_and_update_outcome["disbursement_proof_sent"] if 'upload_and_update_outcome' in locals() else 0,
            "supabase_saved": supabase_saved if 'supabase_saved' in locals() else 0,
            "supabase_duplicates": supabase_duplicates if 'supabase_duplicates' in locals() else 0,
            "supabase_errors": supabase_errors if 'supabase_errors' in locals() else 0,
            "check_duration": float((datetime.now() - check_start).total_seconds()),
            "total_processed_emails": len(monitoring_state["processed_email_ids"])
        }

        # Save all stats to supabase
        try:
            database_service.save_record_to_supabase(record=result, table_name="live_disbursement_stats", environment="orbit")
        except Exception as e:
            logger.info(f"Error saving stats to supabase: {str(e)}")

        
        logger.info(f"Email check completed: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Email check failed: {str(e)}"
        monitoring_state["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "error": error_msg
        })
        logger.error(error_msg)
        return {
            "emails_checked": 0,
            "disbursements_found": 0,
            "supabase_saved": 0,
            "supabase_errors": 1,
            "error": error_msg
        }


def live_monitoring_loop(config: LiveMonitoringConfig):
    """Main loop for live monitoring (runs in separate thread)."""
    
    logger.info("Live monitoring loop started")
    
    while not monitoring_state["stop_event"].is_set():
        try:
            # Perform email check
            try:
                # We need to run async function in sync context
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                check_result = loop.run_until_complete(perform_email_check(config))
                loop.close()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                monitoring_state["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": f"Monitoring loop error: {str(e)}"
                })
            
            # Wait for next check or stop signal
            if monitoring_state["stop_event"].wait(timeout=config.polling_interval):
                break  # Stop event was set
                
        except Exception as e:
            logger.error(f"Critical error in monitoring loop: {str(e)}")
            monitoring_state["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": f"Critical monitoring error: {str(e)}"
            })
            # Wait a bit before retrying
            time.sleep(30)
    
    logger.info("Live monitoring loop stopped")


############################################################################################
                            # Health Check Endpoint
############################################################################################


def check_live_disbursements_health() -> Dict[str, Any]:
    """
    Check health of live disbursements service and all its dependencies.
    
    Returns:
        Dict containing health status of all live disbursements components
    """
    health_status = {
        "overall_status": "healthy",
        "components": {}
    }
    
    # 1. Check Database Service (Supabase)
    try:
        db_healthy = False
        db_details = {
            "orbit_available": bool(database_service.client_orbit),
            "default_client_available": bool(database_service.client),
            "default_environment": database_service.environment
        }
        
        if database_service.client_orbit or database_service.client:
            try:
                db_healthy = True
            except Exception as e:
                db_details["connection_error"] = str(e)
                db_healthy = False
        else:
            db_healthy = False
            db_details["error"] = "No database client initialized"
        
        health_status["components"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "details": db_details
        }
        
        if not db_healthy:
            health_status["overall_status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["overall_status"] = "unhealthy"
    
    # 2. Check Email Client (MailClient)
    try:
        email_client = MailClient()
        email_health = {
            "zoho_available": False,
            "gmail_available": False
        }
        
        # Test Zoho connection
        try:
            if email_client.connect(mail_client="zoho"):
                email_health["zoho_available"] = True
                email_client.disconnect()
        except Exception as e:
            email_health["zoho_error"] = str(e)

        try:
            if email_client.connect(mail_client="gmail"):
                email_health["gmail_available"] = True
                email_client.disconnect()
        except Exception as e:
            email_health["gmail_error"] = str(e)
        
        email_healthy = email_health["zoho_available"] or email_health["gmail_available"]  # or email_health["gmail_available"]
        
        health_status["components"]["email_client"] = {
            "status": "healthy" if email_healthy else "unhealthy",
            "details": email_health
        }
        
        if not email_healthy:
            health_status["overall_status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["email_client"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["overall_status"] = "unhealthy"
    
    # 3. Check AI Analyzer (OpenAI)
    try:
        ai_analyzer = OpenAIAnalyzer()
        ai_health = {
            "configured": bool(ai_analyzer.openai_config.get('api_key')),
            "model": ai_analyzer.openai_config.get('model', 'unknown')
        }
        
        ai_healthy = ai_health["configured"]
        if ai_healthy:
            try:
                ai_health["client_initialized"] = bool(ai_analyzer.client)
            except Exception as e:
                ai_health["client_error"] = str(e)
                ai_healthy = False
        
        health_status["components"]["ai_analyzer"] = {
            "status": "healthy" if ai_healthy else "unhealthy",
            "details": ai_health
        }
        
        if not ai_healthy:
            health_status["overall_status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["ai_analyzer"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["overall_status"] = "unhealthy"
    
    # 4. Check Basic Application Service
    try:
        basic_app_health = {
            "api_url_configured": bool(basic_app_service.basic_api_url),
            "user_id_configured": bool(basic_app_service.BASIC_APPLICATION_USER_ID),
            "api_key_configured": bool(basic_app_service.BASIC_APPLICATION_API_KEY)
        }
        
        basic_app_healthy = (
            basic_app_health["api_url_configured"] and
            basic_app_health["user_id_configured"] and
            basic_app_health["api_key_configured"]
        )
        
        health_status["components"]["basic_application_service"] = {
            "status": "healthy" if basic_app_healthy else "unhealthy",
            "details": basic_app_health
        }
        
        if not basic_app_healthy:
            health_status["overall_status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["basic_application_service"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["overall_status"] = "unhealthy"
    
    # 5. Check Monitoring State
    try:        
        monitoring_health = {
            "is_running": monitoring_state.get("is_running", False),
            "started_at": monitoring_state.get("started_at").isoformat() if monitoring_state.get("started_at") else None,
            "last_check": monitoring_state.get("last_check").isoformat() if monitoring_state.get("last_check") else None,
            "thread_alive": monitoring_state.get("thread") and monitoring_state.get("thread").is_alive() if monitoring_state.get("thread") else False,
            "emails_processed": monitoring_state.get("emails_processed", 0),
            "disbursements_found": monitoring_state.get("disbursements_found", 0),
            "error_count": len(monitoring_state.get("errors", []))
        }
        
        monitoring_healthy = True
        if monitoring_health["is_running"]:
            if not monitoring_health["thread_alive"]:
                monitoring_healthy = False
                monitoring_health["warning"] = "Monitoring is marked as running but thread is not alive"
        else:
            monitoring_healthy = False
        
        health_status["components"]["monitoring"] = {
            "status": "healthy" if monitoring_healthy else "unhealthy",
            "details": monitoring_health
        }
        
        if not monitoring_healthy:
            health_status["overall_status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["monitoring"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["overall_status"] = "unhealthy"

    
    # If status is unhealthy or degraded, send alert emails to the recipient emails
    if health_status["overall_status"] == "unhealthy" or health_status["overall_status"] == "degraded":
        unhealthy_components = []
        for unhealthy_component in health_status["components"]:
            if health_status["components"][unhealthy_component]["status"] == "unhealthy":
                unhealthy_component = f"{unhealthy_component}: {health_status["components"][unhealthy_component]["details"]}"
                unhealthy_components.append(unhealthy_component)
        
        if unhealthy_components:
            email_processing_service.send_email(email_data={
                "subject": "Issue in Live Disbursements Service",
                "content": "Live disbursements service is unhealthy: \n"+", ".join(unhealthy_components)
            })

    
    return health_status



@router.get("/live_disbursements_health")
async def live_disbursements_health_check(response: Response) -> Dict[str, Any]:
    """
    Comprehensive health check for live disbursements service.
    
    This endpoint uses the shared health check function from the main health API.
    Checks the status of all dependencies:
    - Database service (Supabase)
    - Email client (MailClient - Gmail/Zoho)
    - AI Analyzer (OpenAI)
    - Basic Application Service
    - Monitoring state
    
    Returns:
        Dict containing health status of all components
    """
    health_status = {
        "timestamp": datetime.now().isoformat(),
        **check_live_disbursements_health()
    }
    
    # Set HTTP status code based on overall health
    if health_status["overall_status"] == "unhealthy":
        response.status_code = 503  # Service Unavailable
    elif health_status["overall_status"] == "degraded":
        response.status_code = 200  # Still OK but degraded
    else:
        response.status_code = 200  # Healthy
    
    return health_status


############################################################################################
                        # New Disbursement Data Endpoints
############################################################################################

@router.get("/disbursements/latest")
async def get_latest_disbursements():
    """
    Get the latest disbursements extracted from the most recent email check.
    
    Returns:
        Dict containing the latest disbursements found in the last monitoring cycle
    """
    try:
        latest_disbursements = monitoring_state.get("latest_disbursements", [])
        last_check = monitoring_state.get("last_disbursement_check")
        
        return {
            "success": True,
            "message": f"Retrieved {len(latest_disbursements)} latest disbursements",
            "data": {
                "disbursements": latest_disbursements,
                "count": len(latest_disbursements),
                "last_extracted_at": last_check.isoformat() if last_check else None,
                "monitoring_active": monitoring_state.get("is_running", False),
                "total_session_disbursements": len(monitoring_state.get("session_disbursements", []))
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting latest disbursements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/disbursements/session")
async def get_session_disbursements():
    """
    Get all disbursements found in the current monitoring session.
    
    Returns:
        Dict containing all disbursements extracted since monitoring started
    """
    try:
        session_disbursements = monitoring_state.get("session_disbursements", [])
        started_at = monitoring_state.get("started_at")
        
        return {
            "success": True,
            "message": f"Retrieved {len(session_disbursements)} session disbursements",
            "data": {
                "disbursements": session_disbursements,
                "count": len(session_disbursements),
                "session_started_at": started_at.isoformat() if started_at else None,
                "monitoring_active": monitoring_state.get("is_running", False),
                "emails_processed": monitoring_state.get("emails_processed", 0),
                "last_check": monitoring_state.get("last_check").isoformat() if monitoring_state.get("last_check") else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting session disbursements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


############################################################################################
# Saving the pdf to S3 and getting signed url
def save_pdf_and_update_disbursement_proof(disbursement: Dict, pdf_bytes: bytes) -> bool:
    """
    Save the pdf to S3 and get the presigned s3 url and update the disbursement proof url in the disbursement record
    Args:
        disbursement: Dict containing the disbursement record
        pdf_bytes: bytes containing the pdf data
        pdf_name: str containing the pdf name
    Returns:
        bool: True if the pdf is saved to S3 and the disbursement proof url is updated, False otherwise
        Dict: Dict containing the upload outcome
            - presigned_s3_url: str containing the presigned s3 url
            - s3_uploaded: int containing the status of the upload
            - disbursement_proof_sent: int containing the status of the disbursement proof sent
    """

    upload_outcome = {"presigned_s3_url": 0, "s3_uploaded": 0, "disbursement_proof_sent": 0}

    # Validate the disbursement id
    if disbursement.get('disbursementId').lower() not in ["", None, "none", "not found"]:
        disbursement_id = disbursement.get('disbursementId')
    else:
        disbursement_id = f"default_{str(uuid4())}"

    # Populate the filename and key for the S3 upload 
    filename = f"{disbursement_id}-{str(uuid4())}.pdf"
    key = f"users/vbb-disbursements/{filename}"
    logger.info(f"✅ Filename: {filename}")
    
    # Upload the file to S3 bucket
    from app.services.processing import s3_service
    if isinstance(pdf_bytes, bytes):
        import io
        file_obj = io.BytesIO(pdf_bytes)
        upload_file_response = s3_service.upload_fileObject(file_object=file_obj, key=key)
    else:
        file_obj = pdf_bytes
        upload_file_response = s3_service.upload_fileObject(file_object=pdf_bytes, key=key)

    # Generate the presigned s3 url
    if upload_file_response:
        upload_outcome["s3_uploaded"] = 1
        presigned_s3_url = s3_service.generate_presigned_url(key=key)
        logger.info(f"✅ Signed url generated successfully for the disbursement: {disbursement.get('basicAppId')}: {presigned_s3_url.split('?')[0]}")

        if presigned_s3_url and presigned_s3_url.startswith("https://"):
            upload_outcome["presigned_s3_url"] = 1
            disbursement_proof_url = presigned_s3_url
        else:
            disbursement_proof_url = None
    else:
        disbursement_proof_url = None
        logger.warning("Error in generating signed url for the disbursement proof.`")

    # Send the disbursement proof to Basic Application API
    if disbursement_proof_url:
        try:
            update_disbursement_proof_response = basic_app_service.send_disbursement_proof(data={
                "basicAppId": disbursement.get("basicAppId", ""),
                "basicDisbursementId": disbursement.get("disbursementId", ""),
                "disbursementRemarks": disbursement.get("disbursementStatus", ""),
                "pddRemarks": disbursement.get("pdd", ""),
                "disbursementProofUrl":disbursement_proof_url
            })
            if update_disbursement_proof_response:
                logger.info(f"✅ Disbursement proof sent to Basic Application API")
                upload_outcome["disbursement_proof_sent"] = 1
            
            return True, upload_outcome
        
        except Exception as e:
            logger.warning(f"❌ Error sending disbursement proof to Basic Application API: {str(e)}")
            return False, upload_outcome
        
    else:
        logger.warning(f"❌ Error generating presigned S3 URL")
        return False, upload_outcome
