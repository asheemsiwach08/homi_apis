"""
Email processing orchestration service that coordinates analysis and Google Sheets updates.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from app.config.config import config
from app.src.ai_analyzer import OpenAIAnalyzer
from app.src.email_processor import ZohoMailClient
from app.src.api_client import BasicApplicationService
from app.src.sheets_integration import GoogleSheetsClient

logger = logging.getLogger(__name__)


class EmailProcessingService:
    """Orchestrates the complete email processing pipeline."""
    
    def __init__(self):
        """Initialize the processing service with all required clients."""
        self.zoho_client = ZohoMailClient()
        self.ai_analyzer = OpenAIAnalyzer()
        self.basic_api_client = BasicApplicationService()
        self.sheets_client = GoogleSheetsClient()
        
        # Initialize Google Sheets authentication
        if not self.sheets_client.authenticate():
            logger.error("Failed to authenticate with Google Sheets")
        else:
            logger.info("Google Sheets authentication successful")
        
        # Configuration
        app_config = config.get_app_config()
        self.processing_delay = float(app_config.get('processing_delay', 1.0))
        self.max_retries = int(app_config.get('max_retries', 3))
        self.batch_size = int(app_config.get('batch_size', 10))
        
        logger.info("Email processing service initialized")
    
    def process_new_emails(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of new emails through the complete pipeline.
        
        Args:
            emails: List of email data dictionaries
            
        Returns:
            Processing results summary
        """
        start_time = datetime.now()
        results = {
            'processed_count': 0,
            'successful_count': 0,
            'failed_count': 0,
            'disbursements_found': 0,
            'sheets_updates': 0,
            'errors': [],
            'processing_time': 0
        }
        
        logger.info(f"Starting processing of {len(emails)} new emails")
        
        try:
            # Step 1: Group emails into threads for better analysis
            thread_emails = self._group_emails_into_threads(emails)
            logger.info(f"Grouped {len(emails)} emails into {len(thread_emails)} threads")
            
            # Step 2: Process each thread
            for thread_data in thread_emails:
                try:
                    thread_result = self._process_email_thread(thread_data)
                    
                    # Update results
                    results['processed_count'] += 1
                    if thread_result['success']:
                        results['successful_count'] += 1
                        results['disbursements_found'] += thread_result['disbursements_count']
                        results['sheets_updates'] += thread_result['sheets_updates']
                    else:
                        results['failed_count'] += 1
                        results['errors'].extend(thread_result['errors'])
                        
                except Exception as e:
                    error_msg = f"Error processing thread: {str(e)}"
                    logger.error(error_msg)
                    results['failed_count'] += 1
                    results['errors'].append(error_msg)
            
            # Calculate processing time
            results['processing_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Processing completed: {results['successful_count']}/{results['processed_count']} successful, "
                       f"{results['disbursements_found']} disbursements found, "
                       f"{results['sheets_updates']} sheets updates")
            
            return results
            
        except Exception as e:
            error_msg = f"Critical error in email processing: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['processing_time'] = (datetime.now() - start_time).total_seconds()
            return results
    
    def _group_emails_into_threads(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group individual emails into conversation threads for better analysis.
        
        Args:
            emails: List of individual email data
            
        Returns:
            List of thread data formatted for analysis
        """
        try:
            # Connect to Zoho client for thread processing
            self.zoho_client.connect()
            
            # For now, we'll treat each email as its own thread since the complex thread methods are commented out
            # This is a simplified approach that still works for the monitoring functionality
            all_threads = []
            
            for email in emails:
                try:
                    # Create a simple thread from a single email
                    thread_id = email.get('message_id', '') or f"email_{hash(email.get('subject', ''))}"
                    
                    # Format single email as a thread for analysis
                    formatted_thread = self.zoho_client.format_thread_for_analysis(thread_id, [email])
                    if formatted_thread:
                        all_threads.append(formatted_thread)
                        
                except Exception as e:
                    logger.warning(f"Error processing email as thread '{email.get('subject', 'Unknown')}': {str(e)}")
                    continue
            
            return all_threads
            
        except Exception as e:
            logger.error(f"Error grouping emails into threads: {str(e)}")
            return []
        finally:
            try:
                self.zoho_client.disconnect()
            except:
                pass
    
    def _process_email_thread(self, thread_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single email thread through the complete pipeline.
        
        Args:
            thread_data: Formatted thread data for analysis
            
        Returns:
            Processing result for this thread
        """
        result = {
            'success': False,
            'disbursements_count': 0,
            'sheets_updates': 0,
            'errors': []
        }
        
        thread_id = thread_data.get('thread_id', 'unknown')
        
        try:
            # Step 1: AI Analysis to extract disbursement information
            logger.debug(f"Analyzing thread {thread_id} with AI")
            disbursements = self.ai_analyzer.analyze_email(thread_data)
            
            if not disbursements:
                logger.info(f"No disbursements found in thread {thread_id}")
                result['success'] = True
                return result
            
            result['disbursements_count'] = len(disbursements)
            logger.info(f"Found {len(disbursements)} disbursements in thread {thread_id}")
            
            # Step 2: Process each disbursement
            successful_updates = 0
            for disbursement in disbursements:
                try:
                    # Verify with Basic Application API if bankAppId is available
                    bank_app_id = disbursement.get('bankAppId')
                    if bank_app_id and bank_app_id != 'Not found':
                        api_verification = self._verify_with_basic_api(bank_app_id)
                        if api_verification:
                            disbursement.update(api_verification)
                    
                    # Step 3: Update Google Sheets
                    if self._update_google_sheets(disbursement):
                        successful_updates += 1
                        logger.debug(f"Successfully updated sheets for disbursement: {bank_app_id}")
                    else:
                        result['errors'].append(f"Failed to update sheets for disbursement: {bank_app_id}")
                        
                except Exception as e:
                    error_msg = f"Error processing disbursement {bank_app_id}: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            result['sheets_updates'] = successful_updates
            result['success'] = successful_updates > 0 or len(disbursements) == 0
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing thread {thread_id}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    def _verify_with_basic_api(self, bank_app_id: str) -> Dict[str, Any]:
        """
        Verify disbursement data with Basic Application API.
        
        Args:
            bank_app_id: Bank application ID to verify
            
        Returns:
            API verification data or empty dict if failed
        """
        try:
            for attempt in range(self.max_retries):
                try:
                    api_data = self.basic_api_client.verify_application(bank_app_id)
                    if api_data:
                        logger.debug(f"API verification successful for {bank_app_id}")
                        return api_data
                    else:
                        logger.warning(f"No data returned from API for {bank_app_id}")
                        return {}
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"API verification attempt {attempt + 1} failed for {bank_app_id}: {str(e)}")
                    else:
                        logger.error(f"API verification failed after {self.max_retries} attempts for {bank_app_id}: {str(e)}")
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in API verification for {bank_app_id}: {str(e)}")
            return {}
    
    def _update_google_sheets(self, disbursement_data: Dict[str, Any]) -> bool:
        """
        Update Google Sheets with disbursement data.
        
        Args:
            disbursement_data: Disbursement information to add
            
        Returns:
            True if update was successful
        """
        try:
            # The append_bank_application_data method expects a list of applications
            result = self.sheets_client.append_bank_application_data([disbursement_data])
            
            # Check if the update was successful
            if result.get('new_records', 0) > 0:
                logger.info(f"Successfully added new record to Google Sheets: {disbursement_data.get('bankAppId')}")
                return True
            elif result.get('duplicates_skipped', 0) > 0:
                logger.info(f"Duplicate record skipped in Google Sheets: {disbursement_data.get('bankAppId')}")
                return True  # Consider as successful since data already exists
            else:
                logger.warning(f"No records were added to Google Sheets for: {disbursement_data.get('bankAppId')}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating Google Sheets: {str(e)}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the current status of all service components.
        
        Returns:
            Status information for all components
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'zoho_connection': False,
            'openai_configured': False,
            'basic_api_configured': False,
            'sheets_configured': False
        }
        
        try:
            # Check Zoho connection
            status['zoho_connection'] = self.zoho_client.check_connection()
        except:
            pass
        
        try:
            # Check OpenAI configuration
            status['openai_configured'] = bool(self.ai_analyzer.openai_config.get('api_key'))
        except:
            pass
        
        try:
            # Check Basic API configuration
            basic_config = config.get_basic_application_config()
            status['basic_api_configured'] = bool(basic_config.get('api_token'))
        except:
            pass
        
        try:
            # Check Google Sheets configuration
            sheets_config = config.get_sheets_config()
            status['sheets_configured'] = bool(sheets_config.get('spreadsheet_id'))
        except:
            pass
        
        return status 