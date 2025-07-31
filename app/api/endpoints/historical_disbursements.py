"""
Historical Disbursements API

Simple endpoints for processing historical emails and extracting disbursement data.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import logging
import os

from pydantic import BaseModel, Field
from app.src.email_processor.zoho_mail_client import ZohoMailClient
from app.src.ai_analyzer.openai_analyzer import OpenAIAnalyzer
from app.src.sheets_integration.google_sheets_client import GoogleSheetsClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["historical-disbursements"])

# In-memory storage for jobs
jobs_storage = {}


class HistoricalProcessRequest(BaseModel):
    """Request model for historical processing."""
    days_back: int = Field(default=7, ge=0, le=365, description="Number of days to look back")
    email_folders: List[str] = Field(default=["INBOX"], description="Email folders to process")
    subject_filter: Optional[str] = Field(default=None, description="Filter emails by subject")
    sender_filter: Optional[str] = Field(default=None, description="Filter emails by sender")


def get_historical_sheets_client() -> Optional[GoogleSheetsClient]:
    """Get Google Sheets client configured for historical data."""
    try:
        sheets_client = GoogleSheetsClient()
        
        # Override configuration for historical sheet
        historical_spreadsheet_id = os.getenv('GOOGLE_HISTORICAL_SPREADSHEET_ID') or os.getenv('GOOGLE_SPREADSHEET_ID')
        historical_worksheet_name = os.getenv('GOOGLE_HISTORICAL_WORKSHEET_NAME', 'Historical_Disbursements')
        
        if historical_spreadsheet_id:
            sheets_client.spreadsheet_id = historical_spreadsheet_id
            sheets_client.range_name = historical_worksheet_name
            return sheets_client
        else:
            logger.warning("No historical spreadsheet ID configured")
            return None
            
    except Exception as e:
        logger.error(f"Failed to configure historical sheets client: {str(e)}")
        return None


############################################################################################
                                # Historical Disbursements Start API
############################################################################################

@router.post("/historical_disbursements_start")
async def start_historical_processing(
    request: HistoricalProcessRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Start historical email processing job."""
    
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job record
        jobs_storage[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "message": "Job queued for processing",
            "emails_processed": 0,
            "disbursements_found": 0,
            "started_at": datetime.now(),
            "completed_at": None,
            "errors": [],
            "request": request.dict()
        }
        
        # Start background processing
        background_tasks.add_task(
            process_historical_emails,
            job_id,
            request
        )
        
        logger.info(f"Started historical processing job: {job_id}")
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Historical processing job started",
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Failed to start historical processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


############################################################################################
                                # Historical Disbursements Cancel API
############################################################################################

@router.post("/historical_disbursements_cancel/{job_id}")
async def cancel_job(job_id: str) -> Dict[str, Any]:
    """Cancel a running historical processing job."""
    
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    
    if job["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job['status']}"
        )
    
    # Update job status
    jobs_storage[job_id]["status"] = "cancelled"
    jobs_storage[job_id]["message"] = "Job cancelled by user"
    jobs_storage[job_id]["completed_at"] = datetime.now()
    
    logger.info(f"Cancelled historical job: {job_id}")
    
    return {
        "success": True,
        "message": "Historical job cancelled successfully",
        "job_id": job_id
    }


############################################################################################
                                # Historical Disbursements Status API
############################################################################################

@router.get("/historical_disbursements_status/{job_id}")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get status of a historical processing job."""
    
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = jobs_storage[job_id]
    return {
        "job_id": job_data["job_id"],
        "status": job_data["status"],
        "progress": job_data["progress"],
        "message": job_data["message"],
        "emails_processed": job_data["emails_processed"],
        "disbursements_found": job_data["disbursements_found"],
        "started_at": job_data["started_at"],
        "completed_at": job_data["completed_at"],
        "errors": job_data["errors"]
    }


async def process_historical_emails(job_id: str, request: HistoricalProcessRequest):
    """Background task to process historical emails."""
    
    try:
        # Update job status
        jobs_storage[job_id]["status"] = "processing"
        jobs_storage[job_id]["message"] = "Initializing email processing"
        
        # Initialize services
        zoho_client = ZohoMailClient()
        ai_analyzer = OpenAIAnalyzer()
        sheets_client = get_historical_sheets_client()
        
        # Connect to Zoho Mail
        jobs_storage[job_id]["message"] = "Connecting to Zoho Mail"
        if not zoho_client.connect():
            raise Exception("Failed to connect to Zoho Mail")
        
        # Authenticate with Historical Google Sheets if needed
        if sheets_client and not sheets_client.authenticate():
            logger.warning("Failed to authenticate with Historical Google Sheets")
            sheets_client = None
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.days_back)
        
        # Update progress
        jobs_storage[job_id]["progress"] = 10.0
        jobs_storage[job_id]["message"] = f"Fetching emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        # Fetch emails from each folder
        all_emails = []
        for folder in request.email_folders:
            try:
                emails = zoho_client.fetch_emails_from_date_range(
                    folder=folder,
                    start_date=start_date,
                    end_date=end_date,
                    subject_filter=request.subject_filter,
                    sender_filter=request.sender_filter
                )
                all_emails.extend(emails)
                logger.info(f"Fetched {len(emails)} emails from folder: {folder}")
                
            except Exception as e:
                error_msg = f"Error fetching emails from folder {folder}: {str(e)}"
                jobs_storage[job_id]["errors"].append(error_msg)
                logger.error(error_msg)
        
        total_emails = len(all_emails)
        jobs_storage[job_id]["message"] = f"Processing {total_emails} emails"
        jobs_storage[job_id]["progress"] = 20.0
        
        # Process emails with AI
        all_disbursements = []
        for i, email_data in enumerate(all_emails):
            try:
                # Check if job was cancelled
                if jobs_storage[job_id]["status"] == "cancelled":
                    return
                
                # Analyze email with AI
                disbursements = ai_analyzer.analyze_email(email_data)
                
                if disbursements:
                    # Add metadata for historical tracking
                    for disbursement in disbursements:
                        disbursement["processing_type"] = "historical"
                        disbursement["job_id"] = job_id
                        disbursement["processed_at"] = datetime.now()
                    
                    all_disbursements.extend(disbursements)
                    logger.info(f"Found {len(disbursements)} disbursements in email {i+1}")
                
                # Update progress
                progress = 20.0 + (60.0 * (i + 1) / total_emails)
                jobs_storage[job_id]["progress"] = progress
                jobs_storage[job_id]["emails_processed"] = i + 1
                jobs_storage[job_id]["disbursements_found"] = len(all_disbursements)
                jobs_storage[job_id]["message"] = f"Processed {i+1}/{total_emails} emails, found {len(all_disbursements)} disbursements"
                
            except Exception as e:
                error_msg = f"Error processing email {i+1}: {str(e)}"
                jobs_storage[job_id]["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Update Historical Google Sheets if enabled
        if sheets_client and all_disbursements:
            try:
                jobs_storage[job_id]["progress"] = 85.0
                jobs_storage[job_id]["message"] = "Updating Historical Google Sheets"
                
                # Use the correct method to append bank application data
                stats = sheets_client.append_bank_application_data(all_disbursements)
                success_count = stats.get('new_records', 0)
                updated_count = stats.get('updated_records', 0)
                filtered_count = stats.get('filtered_out', 0)
                
                logger.info(f"Historical Google Sheets update: {success_count} new, {updated_count} updated, {filtered_count} filtered out (non-disbursed)")
                logger.info(f"Sheets update stats: {stats}")
                
                # Update job message with more detailed stats
                if filtered_count > 0:
                    if updated_count > 0:
                        jobs_storage[job_id]["message"] = f"Completed: {len(all_disbursements)} total ({success_count} new, {updated_count} updated, {filtered_count} filtered out)"
                    else:
                        jobs_storage[job_id]["message"] = f"Completed: {len(all_disbursements)} total ({success_count} new, {filtered_count} filtered out)"
                else:
                    if updated_count > 0:
                        jobs_storage[job_id]["message"] = f"Completed: {len(all_disbursements)} disbursements ({success_count} new, {updated_count} updated)"
                    else:
                        jobs_storage[job_id]["message"] = f"Completed: {len(all_disbursements)} disbursements ({success_count} new records)"
                
            except Exception as e:
                error_msg = f"Error updating Historical Google Sheets: {str(e)}"
                jobs_storage[job_id]["errors"].append(error_msg)
                logger.error(error_msg)
        
        # Complete job
        jobs_storage[job_id]["status"] = "completed"
        jobs_storage[job_id]["progress"] = 100.0
        
        # Use detailed message if sheets were updated, otherwise use default message
        if not jobs_storage[job_id]["message"].startswith("Completed:"):
            jobs_storage[job_id]["message"] = f"Historical processing completed. Found {len(all_disbursements)} disbursements from {total_emails} emails"
        
        jobs_storage[job_id]["completed_at"] = datetime.now()
        
        # Disconnect from services
        zoho_client.disconnect()
        
        logger.info(f"Historical processing job {job_id} completed successfully")
        
    except Exception as e:
        # Handle job failure
        jobs_storage[job_id]["status"] = "failed"
        jobs_storage[job_id]["message"] = f"Job failed: {str(e)}"
        jobs_storage[job_id]["completed_at"] = datetime.now()
        jobs_storage[job_id]["errors"].append(str(e))
        
        logger.error(f"Historical processing job {job_id} failed: {str(e)}")
        
        # Clean up connections
        try:
            if 'zoho_client' in locals():
                zoho_client.disconnect()
        except:
            pass 