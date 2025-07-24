"""
Email monitoring service for real-time email processing.
"""

import time
import threading
import logging
from typing import Callable, Optional, List, Dict, Any
from datetime import datetime, timedelta
from dateutil import parser

from .zoho_mail_client import ZohoMailClient
from app.config.config import config

logger = logging.getLogger(__name__)


class EmailMonitor:
    """Monitors emails for new arrivals and triggers processing."""
    
    def __init__(self, on_new_email_callback: Callable[[List[Dict[str, Any]]], None]):
        """
        Initialize email monitor.
        
        Args:
            on_new_email_callback: Callback function to handle new emails
        """
        self.zoho_client = ZohoMailClient()
        self.on_new_email_callback = on_new_email_callback
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Configuration
        app_config = config.get_app_config()
        self.polling_interval = int(app_config.get('email_polling_interval', 30))  # seconds
        self.folders_to_monitor = app_config.get('email_folders_to_monitor', 'INBOX').split(',')
        
        # Configure how far back to look on startup (in minutes)
        startup_lookback_minutes = int(app_config.get('email_startup_lookback_minutes', 60))  # 1 hour default
        self.last_check_time = datetime.now() - timedelta(minutes=startup_lookback_minutes)
        
        logger.info(f"Email monitor initialized with {self.polling_interval}s polling interval")
        logger.info(f"Monitoring folders: {self.folders_to_monitor}")
        logger.info(f"Initial check will look back {startup_lookback_minutes} minutes to {self.last_check_time}")
    
    def start_monitoring(self):
        """Start monitoring for new emails."""
        if self.is_monitoring:
            logger.warning("Email monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Email monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring for new emails."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("Email monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that checks for new emails."""
        logger.info("Starting email monitoring loop")
        
        while self.is_monitoring:
            try:
                # Check for new emails in each monitored folder
                for folder in self.folders_to_monitor:
                    folder = folder.strip()
                    new_emails = self._check_for_new_emails(folder)
                    
                    if new_emails:
                        logger.info(f"Found {len(new_emails)} new emails in folder '{folder}'")
                        try:
                            # Trigger the callback for processing
                            self.on_new_email_callback(new_emails)
                        except Exception as e:
                            logger.error(f"Error in email processing callback: {str(e)}")
                
                # Update last check time
                self.last_check_time = datetime.now()
                
                # Wait for next polling cycle
                time.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(self.polling_interval)  # Continue monitoring even after errors
    
    def _check_for_new_emails(self, folder: str = 'INBOX') -> List[Dict[str, Any]]:
        """
        Check for new emails since last check.
        
        Args:
            folder: Email folder to check
            
        Returns:
            List of new email data
        """
        try:
            # Connect to Zoho Mail
            if not self.zoho_client.connect():
                logger.error(f"Failed to connect to Zoho Mail for folder '{folder}'")
                return []
            
            # Use the last check time, but ensure it's not too recent to avoid missing emails
            # Add a small buffer to handle timing issues
            buffer_seconds = 30  # 30-second buffer
            start_date = self.last_check_time - timedelta(seconds=buffer_seconds)
            end_date = datetime.now()
            
            logger.debug(f"Checking for emails in '{folder}' from {start_date} to {end_date} (with {buffer_seconds}s buffer)")
            
            # Fetch new emails since last check using the dedicated monitoring method
            # This method already filters by time, so we don't need additional filtering
            new_emails = self.zoho_client.fetch_new_emails_since(
                since_datetime=start_date,
                folder=folder,
                max_emails=100  # Increased limit for monitoring to catch more emails
            )
            
            # Additional filtering to remove any emails we might have already processed
            # This prevents duplicate processing due to the buffer
            filtered_emails = []
            actual_new_count = 0
            
            for email in new_emails:
                email_date_str = email.get('date', '')
                if email_date_str:
                    try:
                        email_datetime = parser.parse(email_date_str).replace(tzinfo=None)
                        # Only include emails that are actually newer than our last check (without buffer)
                        if email_datetime > self.last_check_time:
                            filtered_emails.append(email)
                            actual_new_count += 1
                        else:
                            logger.debug(f"Filtering out email from {email_datetime} (before last check {self.last_check_time})")
                    except Exception as e:
                        # If we can't parse the date, include it to be safe
                        filtered_emails.append(email)
                        actual_new_count += 1
                        logger.debug(f"Including email with unparseable date: {email_date_str}")
                else:
                    # No date, include to be safe
                    filtered_emails.append(email)
                    actual_new_count += 1
            
            logger.info(f"Found {len(new_emails)} emails since {start_date}, {actual_new_count} are actually new since {self.last_check_time}")
            
            return filtered_emails
            
        except Exception as e:
            logger.error(f"Error checking for new emails in folder '{folder}': {str(e)}")
            return []
        finally:
            try:
                self.zoho_client.disconnect()
            except:
                pass
    
    def check_connection(self) -> bool:
        """
        Check if email connection is working.
        
        Returns:
            True if connection is successful
        """
        try:
            self.zoho_client.connect()
            self.zoho_client.disconnect()
            return True
        except Exception as e:
            logger.error(f"Email connection check failed: {str(e)}")
            return False
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status.
        
        Returns:
            Status information dictionary
        """
        return {
            'is_monitoring': self.is_monitoring,
            'last_check_time': self.last_check_time.isoformat(),
            'polling_interval': self.polling_interval,
            'folders_monitored': self.folders_to_monitor,
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False
        } 