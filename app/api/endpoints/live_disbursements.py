"""
Live Disbursements API

Simple endpoints for real-time monitoring and processing of disbursement emails.
"""

from fastapi import APIRouter, HTTPException, Query
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
    "processed_email_ids": set(),  # Track processed email message IDs
    "latest_disbursements": [],  # Store latest extracted disbursements
    "last_disbursement_check": None,  # Track when disbursements were last extracted
    "session_disbursements": []  # All disbursements in current monitoring session
}


class LiveMonitoringConfig(BaseModel):
    """Configuration for live monitoring."""
    polling_interval: int = Field(default=60, ge=10, le=3600, description="Polling interval in seconds")
    email_folders: List[str] = Field(default=["INBOX"], description="Email folders to monitor")
    subject_filter: Optional[str] = Field(default=None, description="Filter emails by subject")
    sender_filter: Optional[str] = Field(default=None, description="Filter emails by sender")
    check_period_minutes: int = Field(default=5, ge=1, le=60, description="Check emails from last N minutes")


# Google Sheets integration removed - now using Supabase database only


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
        
        # Save to Supabase database
        supabase_saved = 0
        if new_disbursements and database_service.client:
            try:
                logger.info(f"Saving {len(new_disbursements)} disbursements to Supabase database")
                
                # Save disbursements to database
                save_stats = database_service.save_disbursement_data(new_disbursements)
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
        if new_disbursements:
            monitoring_state["latest_disbursements"] = new_disbursements
            monitoring_state["last_disbursement_check"] = check_start
            monitoring_state["session_disbursements"].extend(new_disbursements)
        
        # Clean up
        zoho_client.disconnect()
        
        result = {
            "emails_checked": len(all_emails),
            "new_emails_processed": len(unprocessed_emails),
            "disbursements_found": len(new_disbursements),
            "new_disbursements": new_disbursements,
            "supabase_saved": supabase_saved if 'supabase_saved' in locals() else 0,
            "supabase_duplicates": supabase_duplicates if 'supabase_duplicates' in locals() else 0,
            "supabase_errors": supabase_errors if 'supabase_errors' in locals() else 0,
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


@router.get("/disbursements", response_model=DisbursementResponse)
async def get_disbursements_from_db(
    bank_name: Optional[str] = Query(None, description="Filter by bank name"),
    disbursement_stage: Optional[str] = Query(None, description="Filter by disbursement stage"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    amount_min: Optional[float] = Query(None, description="Minimum disbursement amount"),
    amount_max: Optional[float] = Query(None, description="Maximum disbursement amount"),
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Records to skip for pagination")
):
    """
    Get disbursement data from Supabase database with filtering and pagination support.
    
    This endpoint retrieves disbursement data from Supabase database and provides
    comprehensive filtering capabilities for frontend consumption.
    """
    try:
        # Prepare filters dictionary
        filters = {}
        if bank_name:
            filters['bank_name'] = bank_name
        if disbursement_stage:
            filters['disbursement_stage'] = disbursement_stage
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        if amount_min is not None:
            filters['amount_min'] = amount_min
        if amount_max is not None:
            filters['amount_max'] = amount_max
        if customer_name:
            filters['customer_name'] = customer_name
        
        # Get data from database service
        result = database_service.get_disbursements(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail="Failed to retrieve disbursement data")
        
        # Convert database records to DisbursementRecord objects
        disbursement_records = []
        for record in result['data']:
            try:
                disbursement_record = DisbursementRecord(
                    banker_email=record.get("banker_email"),
                    first_name=record.get("first_name"),
                    last_name=record.get("last_name"),
                    loan_account_number=record.get("loan_account_number"),
                    disbursed_on=record.get("disbursed_on"),
                    disbursed_created_on=record.get("disbursed_created_on"),
                    sanction_date=record.get("sanction_date"),
                    disbursement_amount=record.get("disbursement_amount"),
                    loan_sanction_amount=record.get("loan_sanction_amount"),
                    bank_app_id=record.get("bank_app_id"),
                    basic_app_id=record.get("basic_app_id"),
                    basic_disb_id=record.get("basic_disb_id"),
                    app_bank_name=record.get("app_bank_name"),
                    disbursement_stage=record.get("disbursement_stage"),
                    disbursement_status=record.get("disbursement_status"),
                    primary_borrower_mobile=record.get("primary_borrower_mobile"),
                    pdd=record.get("pdd"),
                    otc=record.get("otc"),
                    sourcing_channel=record.get("sourcing_channel"),
                    sourcing_code=record.get("sourcing_code"),
                    application_product_type=record.get("application_product_type"),
                    data_found=record.get("data_found"),
                    processed_at=record.get("processed_at"),
                    email_date=record.get("email_date")
                )
                disbursement_records.append(disbursement_record)
            except Exception as e:
                logger.warning(f"Error converting database record to DisbursementRecord: {str(e)}")
                continue
        
        # Prepare page info
        has_more = result.get('has_more', False)
        filtered_count = result.get('total_count', len(disbursement_records))
        
        page_info = {
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "current_page": (offset // limit) + 1,
            "total_pages": (filtered_count + limit - 1) // limit
        }
        
        return DisbursementResponse(
            success=True,
            message=f"Retrieved {len(disbursement_records)} disbursement records from Supabase",
            data=disbursement_records,
            total_count=filtered_count,
            filtered_count=filtered_count,
            page_info=page_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_disbursements_from_db: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/disbursements/stats", response_model=DisbursementStatsResponse)
async def get_disbursement_stats():
    """
    Get disbursement statistics from Supabase for dashboard display.
    """
    try:
        # Get statistics from database service
        stats = database_service.get_disbursement_stats()
        
        # Add live monitoring status to stats
        stats['data_freshness'] = {
            "live_monitoring_active": monitoring_state["is_running"],
            "last_check": monitoring_state["last_check"].isoformat() if monitoring_state["last_check"] else None,
            "emails_processed": monitoring_state["emails_processed"],
            "disbursements_found": monitoring_state["disbursements_found"],
            "session_disbursements": len(monitoring_state.get("session_disbursements", []))
        }
        
        return DisbursementStatsResponse(
            success=True,
            message="Disbursement statistics calculated successfully from Supabase",
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Error in get_disbursement_stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/disbursements/manual-check")
async def manual_disbursement_check():
    """
    Manually trigger a disbursement check cycle and return results immediately.
    
    This endpoint allows you to manually trigger an email check and get the 
    disbursement results without waiting for the monitoring cycle.
    """
    try:
        if not monitoring_state["is_running"]:
            raise HTTPException(
                status_code=400, 
                detail="Live monitoring is not running. Start monitoring first."
            )
        
        # Get current config
        config_dict = monitoring_state.get("config", {})
        config = LiveMonitoringConfig(**config_dict)
        
        # Perform email check
        check_result = await perform_email_check(config)
        
        return {
            "success": True,
            "message": "Manual disbursement check completed",
            "data": {
                "check_result": check_result,
                "new_disbursements": check_result.get("new_disbursements", []),
                "disbursements_count": check_result.get("disbursements_found", 0),
                "emails_processed": check_result.get("new_emails_processed", 0),
                "supabase_saved": check_result.get("supabase_saved", 0),
                "check_duration": check_result.get("check_duration", 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual_disbursement_check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        ) 