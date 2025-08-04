"""
Live Disbursements API

Simple endpoints for real-time monitoring and processing of disbursement emails.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import threading
import time
import logging
import os

from pydantic import BaseModel, Field
from app.src.email_processor.zoho_mail_client import ZohoMailClient
from app.src.ai_analyzer.openai_analyzer import OpenAIAnalyzer
from app.services.database_service import database_service
from app.models.schemas import DisbursementFilters, DisbursementResponse, DisbursementStatsResponse, DisbursementRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["live-disbursements"])

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
    "processed_email_ids": set()  # Track processed email message IDs
}


class LiveMonitoringConfig(BaseModel):
    """Configuration for live monitoring."""
    polling_interval: int = Field(default=60, ge=10, le=3600, description="Polling interval in seconds")
    email_folders: List[str] = Field(default=["INBOX"], description="Email folders to monitor")
    subject_filter: Optional[str] = Field(default=None, description="Filter emails by subject")
    sender_filter: Optional[str] = Field(default=None, description="Filter emails by sender")
    check_period_minutes: int = Field(default=5, ge=1, le=60, description="Check emails from last N minutes")

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
        zoho_client = ZohoMailClient()
        if not zoho_client.connect():
            raise HTTPException(status_code=500, detail="Failed to connect to Zoho Mail")
        zoho_client.disconnect()
        
        # Update monitoring state
        monitoring_state.update({
            "is_running": True,
            "started_at": datetime.now(),
            "last_check": None,
            "emails_processed": 0,
            "disbursements_found": 0,
            "errors": [],
            "config": config.dict(),
            "processed_email_ids": set()  # Reset processed emails tracking
        })
        
        # Reset stop event
        monitoring_state["stop_event"].clear()
        
        # Start monitoring thread
        monitoring_thread = threading.Thread(
            target=live_monitoring_loop,
            args=(config,),
            daemon=True
        )
        print("<<<------------- Monitoring thread started", monitoring_thread,"-------------->>>")
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
        raise
    except Exception as e:
        logger.error(f"Failed to start live monitoring: {str(e)}")
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
        zoho_client = ZohoMailClient()
        ai_analyzer = OpenAIAnalyzer()
        
        # Connect to Zoho Mail
        if not zoho_client.connect():
            raise Exception("Failed to connect to Zoho Mail")
        
       
        # Calculate time range for new emails
        check_start = datetime.now()
        since_time = check_start - timedelta(minutes=config.check_period_minutes)
        
        logger.info(f"Checking for emails since {since_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Current time: {check_start.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Fetch new emails from all folders using time-based filtering
        all_emails = []
        for folder in config.email_folders:
            try:
                # Use a broader time range for IMAP search and then filter more precisely
                broader_since = since_time - timedelta(hours=1)  # Search 1 hour back to catch timing issues
                
                emails = zoho_client.fetch_new_emails_since(
                    since_datetime=broader_since,
                    folder=folder,
                    max_emails=100  # Increase limit but we'll filter out duplicates
                )
                
                # Apply more precise time filtering
                time_filtered_emails = []
                for email in emails:
                    email_date_str = email.get('date', '')
                    
                    if email_date_str:
                        try:
                            # Parse email date and check if it's actually newer than since_time
                            from dateutil import parser
                            email_date = parser.parse(email_date_str)
                            if email_date.replace(tzinfo=None) >= since_time:
                                time_filtered_emails.append(email)
                            else:
                                logger.debug(f"Email too old: {email.get('subject', '')[:30]} from {email_date_str}")
                        except Exception as e:
                            # If we can't parse the date, include the email to be safe
                            logger.warning(f"Could not parse email date '{email_date_str}': {e}")
                            time_filtered_emails.append(email)
                    else:
                        # If no date, include the email
                        time_filtered_emails.append(email)
                
                # Apply additional filters if specified
                if config.subject_filter or config.sender_filter:
                    filtered_emails = []
                    for email in time_filtered_emails:
                        subject_match = True
                        sender_match = True
                        
                        if config.subject_filter:
                            subject = email.get('subject', '').lower()
                            subject_match = config.subject_filter.lower() in subject
                        
                        if config.sender_filter:
                            sender = email.get('sender', '').lower()
                            sender_match = config.sender_filter.lower() in sender
                        
                        if subject_match and sender_match:
                            filtered_emails.append(email)
                    
                    time_filtered_emails = filtered_emails
                
                all_emails.extend(time_filtered_emails)
                logger.info(f"Found {len(time_filtered_emails)} time-filtered emails in folder '{folder}' (from {len(emails)} total)")
                
            except Exception as e:
                error_msg = f"Error fetching emails from folder {folder}: {str(e)}"
                monitoring_state["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error_msg
                })
                logger.error(error_msg)
        
        logger.info(f"Total emails found from IMAP: {len(all_emails)}")
        
        # Filter out already processed emails
        unprocessed_emails = []
        for email in all_emails:
            email_id = email.get('message_id') or email.get('email_num')
            if email_id and email_id not in monitoring_state["processed_email_ids"]:
                unprocessed_emails.append(email)
                monitoring_state["processed_email_ids"].add(email_id)
            else:
                logger.debug(f"Skipping already processed email: {email.get('subject', 'No Subject')[:50]}")
        
        logger.info(f"New emails to process: {len(unprocessed_emails)} (filtered from {len(all_emails)} total)")
        
        # Process emails with AI only if we have new emails
        new_disbursements = []
        if unprocessed_emails:
            for i, email_data in enumerate(unprocessed_emails):
                try:
                    subject = email_data.get('subject', 'No Subject')[:50]
                    logger.info(f"Processing email {i+1}/{len(unprocessed_emails)}: {subject}...")
                    
                    disbursements = ai_analyzer.analyze_email(email_data)
                    if disbursements:
                        # Add processing timestamp and live metadata
                        for disbursement in disbursements:
                            disbursement["processed_at"] = datetime.now()
                            disbursement["processing_type"] = "live"
                            disbursement["monitoring_session"] = monitoring_state["started_at"]
                            disbursement["email_subject"] = email_data.get('subject', '')
                            disbursement["email_sender"] = email_data.get('sender', '')
                            disbursement["email_date"] = email_data.get('date', '')
                        
                        new_disbursements.extend(disbursements)
                        logger.info(f"Found {len(disbursements)} disbursements in email")
                    else:
                        logger.debug(f"No disbursements found in email")
                        
                except Exception as e:
                    error_msg = f"Error analyzing email {i+1}: {str(e)}"
                    monitoring_state["errors"].append({
                        "timestamp": datetime.now().isoformat(),
                        "error": error_msg
                    })
                    logger.error(error_msg)
        else:
            logger.info("No new emails to process")
        
        logger.info(f"Total disbursements extracted: {len(new_disbursements)}")
        
        # Update Supabase database
        if new_disbursements:
            try:
                logger.info(f"Updating Supabase database with {len(new_disbursements)} disbursements")
                database_service.save_disbursement_data(new_disbursements)
            except Exception as e:
                error_msg = f"Error updating Supabase database: {str(e)}"
                monitoring_state["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error_msg
                })
                logger.error(error_msg)
        
        # Update monitoring state
        monitoring_state["last_check"] = check_start
        monitoring_state["emails_processed"] += len(unprocessed_emails)  # Only count newly processed emails
        monitoring_state["disbursements_found"] += len(new_disbursements)
        
        # Clean up
        zoho_client.disconnect()
        
        result = {
            "emails_checked": len(all_emails),
            "new_emails_processed": len(unprocessed_emails),
            "disbursements_found": len(new_disbursements),
            "check_duration": (datetime.now() - check_start).total_seconds(),
            "total_processed_emails": len(monitoring_state["processed_email_ids"])
        }
        
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