"""
Zoho Mail client for connecting to and fetching emails.
"""

import imaplib
import email
from email.header import decode_header
from email.message import Message
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import re
import logging

from app.config.config import config

logger = logging.getLogger(__name__)


class ZohoMailClient:
    """Client for connecting to Zoho Mail via IMAP."""
    
    def __init__(self):
        """Initialize Zoho Mail client."""
        self.zoho_config = config.get_zoho_config()
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        
    def connect(self) -> bool:
        """Connect to Zoho Mail IMAP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            
            self.connection = imaplib.IMAP4_SSL(
                self.zoho_config['imap_server'],
                self.zoho_config['imap_port']
            )
            
            # Login
            self.connection.login(
                self.zoho_config['email'],
                self.zoho_config['password']
            )
            
            logger.info("Successfully connected to Zoho Mail")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Zoho Mail: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Zoho Mail."""
        if self.connection:
            try:
                self.connection.logout()
                logger.info("Disconnected from Zoho Mail")
            except Exception as e:
                logger.error(f"Error disconnecting from Zoho Mail: {str(e)}")
            finally:
                self.connection = None

    def fetch_emails_from_date_range(
        self, 
        folder: str = 'INBOX',
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        subject_filter: Optional[str] = None,
        sender_filter: Optional[str] = None,
        max_emails: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch emails from a specific date range with optional filters.
        
        Args:
            folder: Email folder to search in (default: 'INBOX')
            start_date: Start date for search (default: 7 days ago)
            end_date: End date for search (default: now)
            subject_filter: Optional subject filter
            sender_filter: Optional sender filter
            max_emails: Maximum number of emails to fetch
            
        Returns:
            List of email data dictionaries
        """
        if not self.connection:
            logger.error("Not connected to Zoho Mail")
            return []
        
        try:
            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=7)
            
            # Select the folder
            self.connection.select(folder)
            
            # Format dates for IMAP search  
            start_date_str = start_date.strftime("%d-%b-%Y")
            end_date_str = end_date.strftime("%d-%b-%Y")
            
            # Build search criteria
            search_parts = []
            
            # Date range
            search_parts.append(f'SINCE {start_date_str}')
            
            # Only add BEFORE if end_date is actually in the past
            # Convert end_date to date for comparison
            today = datetime.now().date()
            end_date_only = end_date.date() if isinstance(end_date, datetime) else end_date
            
            if end_date_only < today:
                search_parts.append(f'BEFORE {end_date_str}')
            
            # Subject filter
            if subject_filter:
                search_parts.append(f'SUBJECT "{subject_filter}"')
            
            # Sender filter
            if sender_filter:
                search_parts.append(f'FROM "{sender_filter}"')
            
            # Combine search criteria
            search_criteria = ' '.join(search_parts)
            logger.info(f"Searching emails in '{folder}' with criteria: {search_criteria}")
            
            _, message_numbers = self.connection.search(None, search_criteria)
            
            if not message_numbers[0]:
                logger.info(f"No emails found matching criteria in '{folder}'")
                return []
            
            email_list = message_numbers[0].split()
            logger.info(f"Found {len(email_list)} emails matching criteria")
            
            # Limit the number of emails if specified
            if max_emails and len(email_list) > max_emails:
                email_list = email_list[-max_emails:]
                logger.info(f"Limited to {max_emails} most recent emails")
            
            # Fetch email data
            emails = []
            for num in email_list:
                try:
                    email_data = self._fetch_email_data(num)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error fetching email {num}: {str(e)}")
                    continue
            
            logger.info(f"Successfully fetched {len(emails)} emails from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails from date range: {str(e)}")
            return []
    
    def fetch_unread_emails(self, max_emails: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch unread emails from Zoho Mail.
        
        Args:
            max_emails: Maximum number of emails to fetch
            
        Returns:
            List of email data dictionaries
            
        Note:
            This method uses RFC822.PEEK to fetch email content without marking emails as read.
            The original read/unread status of emails in the mail account is preserved.
        """
        if not self.connection:
            logger.error("Not connected to Zoho Mail")
            return []
        
        try:
            # Select the folder
            folder = self.zoho_config['folder']
            self.connection.select(folder)
            
            # Search for unread emails
            search_criteria = self.zoho_config['search_criteria']
            _, message_numbers = self.connection.search(None, search_criteria)
            
            if not message_numbers[0]:
                logger.info("No unread emails found")
                return []
            
            email_list = message_numbers[0].split()
            
            # Limit the number of emails if specified
            if max_emails:
                email_list = email_list[-max_emails:]
            
            emails = []
            for num in email_list:
                try:
                    email_data = self._fetch_email_data(num)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error fetching email {num}: {str(e)}")
                    continue
            
            logger.info(f"Fetched emails successfully: {len(emails)}")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching unread emails: {str(e)}")
            return []

    def fetch_recent_emails(self, months_back: int = 3, max_emails: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch emails from the last N months.
        
        Args:
            months_back: Number of months back to fetch emails from (default: 3)
            max_emails: Maximum number of emails to fetch
            
        Returns:
            List of email data dictionaries
            
        Note:
            This method uses RFC822.PEEK to fetch email content without marking emails as read.
            The original read/unread status of emails in the mail account is preserved.
        """
        if not self.connection:
            logger.error("Not connected to Zoho Mail")
            return []
        
        try:
            # Select the folder
            folder = self.zoho_config['folder']
            self.connection.select(folder)
            
            # Calculate the date 3 months ago
            three_months_ago = datetime.now() - timedelta(days=months_back * 30)
            date_str = three_months_ago.strftime("%d-%b-%Y")
            
            # Search for emails since the calculated date
            search_criteria = f'SINCE {date_str}'
            logger.info(f"Searching for emails since: {date_str}")
            
            _, message_numbers = self.connection.search(None, search_criteria)
            
            if not message_numbers[0]:
                logger.info(f"No emails found since {date_str}")  
                return []
            
            email_list = message_numbers[0].split()
            
            # Limit the number of emails if specified
            if max_emails:
                email_list = email_list[-max_emails:]
            
            emails = []
            for num in email_list:
                try:
                    email_data = self._fetch_email_data(num)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error fetching email {num}: {str(e)}")
                    continue
            
            logger.info(f"Fetched {len(emails)} emails from the last {months_back} months")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching recent emails: {str(e)}")
            return []

    def fetch_emails_by_date_range(self, start_months_back: int, end_months_back: int, max_emails: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch emails within a specific date range.
        
        Args:
            start_months_back: Number of months back for the start date (older date)
            end_months_back: Number of months back for the end date (newer date)
            max_emails: Maximum number of emails to fetch
            
        Returns:
            List of email data dictionaries
            
        Note:
            This method uses RFC822.PEEK to fetch email content without marking emails as read.
            The original read/unread status of emails in the mail account is preserved.
        """
        if not self.connection:
            logger.error("Not connected to Zoho Mail")
            return []
        
        try:
            # Select the folder
            folder = self.zoho_config['folder']
            self.connection.select(folder)
            
            # Calculate the date range
            now = datetime.now()
            start_date = now - timedelta(days=start_months_back * 30)
            end_date = now - timedelta(days=end_months_back * 30)
            
            # Format dates for IMAP search
            start_date_str = start_date.strftime("%d-%b-%Y")
            end_date_str = end_date.strftime("%d-%b-%Y")
            
            # Search for emails within the date range
            # IMAP uses SINCE and BEFORE for date ranges
            search_criteria = f'SINCE {start_date_str} BEFORE {end_date_str}'
            logger.info(f"Searching for emails from {start_date_str} to {end_date_str}")
            
            _, message_numbers = self.connection.search(None, search_criteria)
            
            if not message_numbers[0]:
                logger.info(f"No emails found in the specified date range")       
                return []
            
            email_list = message_numbers[0].split()
            
            # Limit the number of emails if specified
            if max_emails:
                email_list = email_list[-max_emails:]
            
            emails = []
            for num in email_list:
                try:
                    email_data = self._fetch_email_data(num)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error fetching email {num}: {str(e)}")
                    continue
            
            logger.info(f"Fetched {len(emails)} emails from {start_months_back} to {end_months_back} months back")
            logger.info("Note: Email read/unread status has been preserved in the original mail account")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails by date range: {str(e)}")
            return []

    def get_email_flags(self, email_num: bytes) -> List[str]:
        """Get the flags for a specific email without modifying them.
        
        Args:
            email_num: Email message number
            
        Returns:
            List of email flags
        """
        if not self.connection:
            return []
            
        try:
            email_num_str = email_num.decode('utf-8') if isinstance(email_num, bytes) else str(email_num)
            _, flag_data = self.connection.fetch(email_num_str, '(FLAGS)')
            
            if flag_data and flag_data[0]:
                # Extract flags from the response
                flag_response = flag_data[0].decode('utf-8')
                # Parse flags from response like: "1 (FLAGS (\\Seen \\Flagged))"
                if 'FLAGS' in flag_response:
                    flags_start = flag_response.find('FLAGS') + 6
                    flags_end = flag_response.rfind(')')
                    if flags_start < flags_end:
                        flags_str = flag_response[flags_start:flags_end]
                        return [flag.strip('\\') for flag in flags_str.split() if flag.strip('\\')]
            return []
            
        except Exception as e:
            logger.error(f"Error getting flags for email {email_num}: {str(e)}")
            return []
    
    def _fetch_email_data(self, email_num: bytes) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific email.
        
        Args:
            email_num: Email message number
            
        Returns:
            Email data dictionary or None if error
        """
        if not self.connection:
            return None
            
        try:
            # Convert bytes to string for fetch
            email_num_str = email_num.decode('utf-8') if isinstance(email_num, bytes) else str(email_num)
            # Use BODY.PEEK[] to fetch email content without marking as read
            _, msg_data = self.connection.fetch(email_num_str, '(BODY.PEEK[])')
            if not msg_data or not msg_data[0]:
                return None
                
            email_body = msg_data[0][1]
            if not isinstance(email_body, bytes):
                return None
                
            email_message = email.message_from_bytes(email_body)
            
            # Extract email information
            subject = self._decode_header(email_message['subject'])
            sender = self._decode_header(email_message['from'])
            date = email_message['date']
            message_id = email_message['message-id']
            
            # Extract email content
            content = self._extract_email_content(email_message)
            
            # Extract attachments
            attachments = self._extract_attachments(email_message)
            
            email_data = {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'content': content,
                'attachments': attachments,
                'raw_message': email_message,
                'email_num': email_num
            }
            
            return email_data
            
        except Exception as e:
            logger.error(f"Error processing email {email_num}: {str(e)}")
            return None
    
    def _decode_header(self, header: Optional[str]) -> str:
        """Decode email header.
        
        Args:
            header: Email header string
            
        Returns:
            Decoded header string
        """
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            
            return decoded_string
        except Exception as e:
            logger.error(f"Error decoding header {header}: {str(e)}")
            return str(header) if header else ""
    
    def _extract_email_content(self, email_message: Message) -> str:
        """Extract text content from email message.
        
        Args:
            email_message: Email message object
            
        Returns:
            Extracted text content
        """
        content = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            content += payload.decode(charset, errors='ignore')
                    except Exception as e:
                        logger.error(f"Error extracting multipart content {str(e)}")
        else:
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or 'utf-8'
                    content = payload.decode(charset, errors='ignore')
            except Exception as e:
                logger.error(f"Error extracting single part content {str(e)}")
        
        return content

    def _extract_attachments(self, email_message: Message) -> List[Dict[str, Any]]:
        """Extract attachments from email message.
        
        Args:
            email_message: Email message object
            
        Returns:
            List of attachment dictionaries with filename, content_type, size, and data
        """
        attachments = []
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    # Skip if this is the main text part
                    if part.get_content_maintype() == 'multipart':
                        continue
                    
                    # Check if this part is an attachment
                    filename = part.get_filename()
                    if filename:
                        # Decode filename if needed
                        filename = self._decode_header(filename)
                        
                        # Get attachment data
                        attachment_data = part.get_payload(decode=True)
                        if attachment_data:
                            attachment_info = {
                                'filename': filename,
                                'content_type': part.get_content_type(),
                                'size': len(attachment_data),
                                'data': attachment_data,
                                'content_disposition': part.get('Content-Disposition', ''),
                                'content_id': part.get('Content-ID', '')
                            }
                            attachments.append(attachment_info)
                            # print(f"Extracted attachment: {filename} ({len(attachment_data)} bytes)")
            
            # Handle single part messages that might be attachments
            elif email_message.get_filename():
                filename = self._decode_header(email_message.get_filename())
                attachment_data = email_message.get_payload(decode=True)
                if attachment_data:
                    attachment_info = {
                        'filename': filename,
                        'content_type': email_message.get_content_type(),
                        'size': len(attachment_data),
                        'data': attachment_data,
                        'content_disposition': email_message.get('Content-Disposition', ''),
                        'content_id': email_message.get('Content-ID', '')
                    }
                    attachments.append(attachment_info)
                    # print(f"Extracted attachment: {filename} ({len(attachment_data)} bytes)")
        
        except Exception as e:
            logger.error(f"Error extracting attachments: {str(e)}")
        
        return attachments

    def save_attachment(self, attachment_data: Dict[str, Any], save_dir: str = "attachments") -> str:
        """Save an attachment to disk.
        
        Args:
            attachment_data: Attachment dictionary with filename, data, etc.
            save_dir: Directory to save attachments (default: "attachments")
            
        Returns:
            Path to saved file or empty string if failed
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(save_dir, exist_ok=True)
            
            # Get filename and sanitize it
            filename = attachment_data['filename']
            if not filename:
                filename = f"attachment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Sanitize filename for filesystem
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            # Create unique filename if file already exists
            base_name, ext = os.path.splitext(filename)
            counter = 1
            final_filename = filename
            while os.path.exists(os.path.join(save_dir, final_filename)):
                final_filename = f"{base_name}_{counter}{ext}"
                counter += 1
            
            # Save file
            file_path = os.path.join(save_dir, final_filename)
            with open(file_path, 'wb') as f:
                f.write(attachment_data['data'])
            
            logger.info(f"Saved attachment: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving attachment {filename}: {str(e)}")
            return ""

    def save_all_attachments(self, email_data: Dict[str, Any], save_dir: str = "attachments") -> List[str]:
        """Save all attachments from an email to disk.
        
        Args:
            email_data: Email data dictionary with attachments
            save_dir: Directory to save attachments (default: "attachments")
            
        Returns:
            List of saved file paths
        """
        saved_files = []
        attachments = email_data.get('attachments', [])
        
        for attachment in attachments:
            file_path = self.save_attachment(attachment, save_dir)
            if file_path:
                saved_files.append(file_path)
        
        return saved_files

    ######################################################################################
    #                              Email Thread Fetching Methods                         #
    ######################################################################################
    
    # def fetch_thread_by_subject(self, subject: str, max_emails: int = 20) -> List[Dict[str, Any]]:
    #     """Fetch all emails in a thread by subject.
        
    #     Args:
    #         subject: Email subject to search for
    #         max_emails: Maximum number of emails to return
            
    #     Returns:
    #         List of email data dictionaries, sorted by date
    #     """
    #     if not self.connection:
    #         print("Not connected to email server")
    #         return []
        
    #     try:
    #         # Select the folder
    #         folder = self.zoho_config['folder']
    #         self.connection.select(folder)
            
    #         # Clean subject for search
    #         clean_subject = self._clean_subject_for_search(subject)
            
    #         # Search for emails with this subject
    #         search_criteria = f'SUBJECT "{clean_subject}"'
    #         _, message_numbers = self.connection.search(None, search_criteria)
            
    #         if not message_numbers[0]:
    #             print(f"No emails found with subject: {clean_subject}")
    #             return []
            
    #         # Fetch emails
    #         thread_emails = []
    #         email_list = message_numbers[0].split()
            
    #         # Limit results
    #         if len(email_list) > max_emails:
    #             email_list = email_list[-max_emails:]
            
    #         for num in email_list:
    #             try:
    #                 email_data = self._fetch_email_data(num)
    #                 if email_data and self._is_same_thread_subject(email_data['subject'], subject):
    #                     thread_emails.append(email_data)
    #             except Exception as e:
    #                 print(f"Error fetching email {num}: {str(e)}")
    #                 continue
            
    #         # Sort by date
    #         thread_emails.sort(key=lambda x: x.get('date', ''))
            
    #         print(f"Found {len(thread_emails)} emails in thread for subject: {clean_subject}")
    #         return thread_emails
            
    #     except Exception as e:
    #         print(f"Error fetching thread by subject: {str(e)}")
    #         return []
    
    # def fetch_thread_by_message_id(self, message_id: str, max_emails: int = 20) -> List[Dict[str, Any]]:
    #     """Fetch all emails in a thread by Message-ID.
        
    #     Args:
    #         message_id: Message-ID to search for
    #         max_emails: Maximum number of emails to return
            
    #     Returns:
    #         List of email data dictionaries, sorted by date
    #     """
    #     if not self.connection:
    #         print("Not connected to email server")
    #         return []
        
    #     try:
    #         # Select the folder
    #         folder = self.zoho_config['folder']
    #         self.connection.select(folder)
            
    #         # Search for emails with this Message-ID or that reference it
    #         search_criteria = f'OR HEADER Message-ID "{message_id}" HEADER References "{message_id}"'
    #         _, message_numbers = self.connection.search(None, search_criteria)
            
    #         if not message_numbers[0]:
    #             print(f"No emails found with Message-ID: {message_id}")
    #             return []
            
    #         # Fetch emails
    #         thread_emails = []
    #         email_list = message_numbers[0].split()
            
    #         # Limit results
    #         if len(email_list) > max_emails:
    #             email_list = email_list[-max_emails:]
            
    #         for num in email_list:
    #             try:
    #                 email_data = self._fetch_email_data(num)
    #                 if email_data:
    #                     thread_emails.append(email_data)
    #             except Exception as e:
    #                 print(f"Error fetching email {num}: {str(e)}")
    #                 continue
            
    #         # Sort by date
    #         thread_emails.sort(key=lambda x: x.get('date', ''))
            
    #         print(f"Found {len(thread_emails)} emails in thread for Message-ID: {message_id}")
    #         return thread_emails
            
    #     except Exception as e:
    #         print(f"Error fetching thread by Message-ID: {str(e)}")
    #         return []
    
    # def fetch_thread_by_references(self, message_id: str, max_thread_size: int = 50) -> List[Dict[str, Any]]:
    #     """Fetch an email thread by following References headers.
        
    #     Args:
    #         message_id: The Message-ID to start the thread from
    #         max_thread_size: Maximum number of emails in the thread
            
    #     Returns:
    #         List of emails in the thread, ordered by date
    #     """
    #     if not self.connection:
    #         print("Not connected to email server")
    #         return []
        
    #     try:
    #         # Select the folder
    #         folder = self.zoho_config['folder']
    #         self.connection.select(folder)
            
    #         # Get the initial email
    #         search_criteria = f'HEADER Message-ID "{message_id}"'
    #         _, message_numbers = self.connection.search(None, search_criteria)
            
    #         if not message_numbers[0]:
    #             print(f"Initial email not found with Message-ID: {message_id}")
    #             return []
            
    #         # Fetch the initial email
    #         initial_email_num = message_numbers[0].split()[0]
    #         initial_email = self._fetch_email_data(initial_email_num)
            
    #         if not initial_email:
    #             return []
            
    #         # Build the thread by following References
    #         thread_emails = [initial_email]
    #         processed_ids = {message_id}
            
    #         # Get References from the initial email
    #         references = self._extract_references(initial_email)
            
    #         # Follow each reference
    #         for ref_id in references:
    #             if ref_id not in processed_ids and len(thread_emails) < max_thread_size:
    #                 ref_emails = self._fetch_emails_by_message_id(ref_id)
    #                 for ref_email in ref_emails:
    #                     if ref_email['message_id'] not in processed_ids:
    #                         thread_emails.append(ref_email)
    #                         processed_ids.add(ref_email['message_id'])
                            
    #                         # Add new references to follow
    #                         new_refs = self._extract_references(ref_email)
    #                         references.extend([r for r in new_refs if r not in processed_ids])
            
    #         # Sort by date
    #         thread_emails.sort(key=lambda x: x.get('date', ''))
            
    #         print(f"Found {len(thread_emails)} emails in thread using References")
    #         return thread_emails
            
    #     except Exception as e:
    #         print(f"Error fetching thread by References: {str(e)}")
    #         return []
    
    def fetch_recent_threads(self,start_months_back: int = 3, end_months_back: int = 0, max_threads: int = 5, max_emails_per_thread: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Get recent email threads from the mailbox.
        
        Args:
            max_threads: Maximum number of threads to return
            max_emails_per_thread: Maximum emails per thread
            
        Returns:
            Dictionary mapping thread IDs to lists of emails
        """
        if not self.connection:
            logger.warning("Not connected to email server")
            return {}
        
        try:
            # Select the folder
            folder = self.zoho_config['folder']
            self.connection.select(folder)
            
            # # Get recent emails (last 30 days)
            # from datetime import datetime, timedelta
            # thirty_days_ago = datetime.now() - timedelta(days=30)
            # date_str = thirty_days_ago.strftime("%d-%b-%Y")
            # search_criteria = f'SINCE {date_str}'

            # Calculate the date range
            from datetime import datetime, timedelta
            now = datetime.now()
            start_date = now - timedelta(days=start_months_back)
            end_date = now - timedelta(days=end_months_back)
            
            # Format dates for IMAP search
            start_date_str = start_date.strftime("%d-%b-%Y")
            end_date_str = end_date.strftime("%d-%b-%Y")
            
            # Search for emails within the date range
            # IMAP uses SINCE and BEFORE for date ranges
            search_criteria = f'SINCE {start_date_str} BEFORE {end_date_str}'
            logger.info(f"Searching for emails from {start_date_str} to {end_date_str}")
            
            _, message_numbers = self.connection.search(None, search_criteria)
            
            if not message_numbers[0]:
                logger.info("No recent emails found")
                return {}

            
            # Fetch emails
            all_emails = []
            email_list = message_numbers[0].split()

            # TODO: Remove the limits
            email_list = email_list[-max_threads:]
            
            for num in email_list:
                try:
                    email_data = self._fetch_email_data(num)
                    if email_data:
                        all_emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error fetching email {num}: {str(e)}")
                    continue
            
            # Group into threads
            threads = self._group_emails_into_threads(all_emails)
            
            # Limit results
            limited_threads = {}
            thread_count = 0
            
            for thread_id, thread_emails in threads.items():
                if thread_count >= max_threads:
                    break
                
                # Sort emails in thread by date
                thread_emails.sort(key=lambda x: x.get('date', ''))
                
                # Limit emails per thread
                if len(thread_emails) > max_emails_per_thread:
                    thread_emails = thread_emails[-max_emails_per_thread:]
                
                limited_threads[thread_id] = thread_emails
                thread_count += 1
            
            logger.info(f"Found {len(limited_threads)} recent threads")
            return limited_threads
            
        except Exception as e:
            logger.error(f"Error fetching recent threads: {str(e)}")
            return {}
    
    # def fetch_bank_application_threads(self, max_threads: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    #     """Get email threads that appear to be bank applications.
        
    #     Args:
    #         max_threads: Maximum number of threads to return
            
    #     Returns:
    #         Dictionary mapping thread IDs to lists of bank application emails
    #     """
    #     if not self.connection:
    #         print("Not connected to email server")
    #         return {}
        
    #     try:
    #         # Select the folder
    #         folder = self.zoho_config['folder']
    #         self.connection.select(folder)
            
    #         # Get all emails
    #         _, message_numbers = self.connection.search(None, 'ALL')
            
    #         if not message_numbers[0]:
    #             print("No emails found")
    #             return {}
            
    #         # Fetch emails
    #         all_emails = []
    #         email_list = message_numbers[0].split()
            
    #         for num in email_list:
    #             try:
    #                 email_data = self._fetch_email_data(num)
    #                 if email_data:
    #                     all_emails.append(email_data)
    #             except Exception as e:
    #                 print(f"Error fetching email {num}: {str(e)}")
    #                 continue
            
    #         # Filter for bank application emails
    #         bank_emails = []
    #         for email_data in all_emails:
    #             subject = email_data.get('subject', '').lower()
    #             content = email_data.get('content', '').lower()
                
    #             # Check for bank application keywords
    #             bank_keywords = [
    #                 'application', 'loan', 'credit', 'mortgage', 'bank', 'financial',
    #                 'approval', 'status', 'review', 'document', 'verification'
    #             ]
                
    #             if any(keyword in subject or keyword in content for keyword in bank_keywords):
    #                 bank_emails.append(email_data)
            
    #         # Group into threads
    #         threads = self._group_emails_into_threads(bank_emails)
            
    #         # Limit results
    #         limited_threads = {}
    #         thread_count = 0
            
    #         for thread_id, thread_emails in threads.items():
    #             if thread_count >= max_threads:
    #                 break
                
    #             # Sort emails in thread by date
    #             thread_emails.sort(key=lambda x: x.get('date', ''))
    #             limited_threads[thread_id] = thread_emails
    #             thread_count += 1
            
    #         print(f"Found {len(limited_threads)} bank application threads")
    #         return limited_threads
            
    #     except Exception as e:
    #         print(f"Error fetching bank application threads: {str(e)}")
    #         return {}
    
    # def fetch_all_threads(self, max_threads: int = 10, max_emails_per_thread: int = 20) -> Dict[str, List[Dict[str, Any]]]:
    #     """Fetch all email threads in the mailbox.
        
    #     Args:
    #         max_threads: Maximum number of threads to fetch
    #         max_emails_per_thread: Maximum emails per thread
            
    #     Returns:
    #         Dictionary mapping thread IDs to lists of emails
    #     """
    #     if not self.connection:
    #         print("Not connected to email server")
    #         return {}
        
    #     try:
    #         # Select the folder
    #         folder = self.zoho_config['folder']
    #         self.connection.select(folder)
            
    #         # Get all emails
    #         _, message_numbers = self.connection.search(None, 'ALL')
            
    #         if not message_numbers[0]:
    #             print("No emails found")
    #             return {}
            
    #         # Fetch all emails
    #         all_emails = []
    #         email_list = message_numbers[0].split()
            
    #         for num in email_list:
    #             try:
    #                 email_data = self._fetch_email_data(num)
    #                 if email_data:
    #                     all_emails.append(email_data)
    #             except Exception as e:
    #                 print(f"Error fetching email {num}: {str(e)}")
    #                 continue
            
    #         # Group emails into threads
    #         threads = self._group_emails_into_threads(all_emails)
            
    #         # Limit threads and emails per thread
    #         limited_threads = {}
    #         thread_count = 0
            
    #         for thread_id, thread_emails in threads.items():
    #             if thread_count >= max_threads:
    #                 break
                
    #             # Sort emails in thread by date
    #             thread_emails.sort(key=lambda x: x.get('date', ''))
                
    #             # Limit emails per thread
    #             if len(thread_emails) > max_emails_per_thread:
    #                 thread_emails = thread_emails[-max_emails_per_thread:]
                
    #             limited_threads[thread_id] = thread_emails
    #             thread_count += 1
            
    #         print(f"Found {len(limited_threads)} threads")
    #         return limited_threads
            
    #     except Exception as e:
    #         print(f"Error fetching all threads: {str(e)}")
    #         return {}
    
    # Helper methods for thread processing
    
    # def _clean_subject_for_search(self, subject: str) -> str:
    #     """Clean subject for IMAP search.
        
    #     Args:
    #         subject: Original subject
            
    #     Returns:
    #         Cleaned subject for search
    #     """
    #     # Remove common prefixes
    #     prefixes_to_remove = ['Re:', 'Fwd:', 'FW:', 'RE:', 'FW:', 'FWD:']
    #     clean_subject = subject
        
    #     for prefix in prefixes_to_remove:
    #         if clean_subject.startswith(prefix):
    #             clean_subject = clean_subject[len(prefix):].strip()
        
    #     # Remove extra whitespace
    #     clean_subject = re.sub(r'\s+', ' ', clean_subject).strip()
        
    #     return clean_subject
    
    # def _is_same_thread_subject(self, email_subject: str, thread_subject: str) -> bool:
    #     """Check if two subjects belong to the same thread.
        
    #     Args:
    #         email_subject: Subject of email to check
    #         thread_subject: Subject of the thread
            
    #     Returns:
    #         True if subjects belong to same thread
    #     """
    #     clean_email_subject = self._clean_subject_for_search(email_subject)
    #     clean_thread_subject = self._clean_subject_for_search(thread_subject)
        
    #     return clean_email_subject.lower() == clean_thread_subject.lower()
    
    def _extract_references(self, email_data: Dict[str, Any]) -> List[str]:
        """Extract References from email headers.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            List of Message-IDs from References header
        """
        references = []
        
        # Get References header
        ref_header = email_data.get('headers', {}).get('references', '')
        if ref_header:
            # Parse References header (space-separated Message-IDs)
            ref_ids = ref_header.strip().split()
            references.extend(ref_ids)
        
        # Also check In-Reply-To header
        in_reply_to = email_data.get('headers', {}).get('in-reply-to', '')
        if in_reply_to:
            references.append(in_reply_to.strip())
        
        return references
    
    # def _fetch_emails_by_message_id(self, message_id: str) -> List[Dict[str, Any]]:
    #     """Fetch emails by Message-ID.
        
    #     Args:
    #         message_id: Message-ID to search for
            
    #     Returns:
    #         List of matching emails
    #     """
    #     if not self.connection:
    #         return []
        
    #     try:
    #         search_criteria = f'HEADER Message-ID "{message_id}"'
    #         _, message_numbers = self.connection.search(None, search_criteria)
            
    #         if not message_numbers[0]:
    #             return []
            
    #         emails = []
    #         for num in message_numbers[0].split():
    #             try:
    #                 email_data = self._fetch_email_data(num)
    #                 if email_data:
    #                     emails.append(email_data)
    #             except Exception as e:
    #                 print(f"Error fetching email {num}: {str(e)}")
    #                 continue
            
    #         return emails
            
    #     except Exception as e:
    #         print(f"Error fetching emails by Message-ID: {str(e)}")
    #         return []
    
    def _group_emails_into_threads(self, emails: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group emails into threads based on Message-ID and References.
        
        Args:
            emails: List of email data dictionaries
            
        Returns:
            Dictionary mapping thread IDs to lists of emails
        """
        from collections import defaultdict
        
        threads = defaultdict(list)
        
        # First pass: create threads based on Message-ID and References
        for email_data in emails:
            message_id = email_data.get('message_id', '')
            references = self._extract_references(email_data)
            
            if message_id:
                # Find the root message ID
                root_id = self._find_root_message_id(email_data, emails)
                threads[root_id].append(email_data)
            elif references:
                # Use first reference as thread ID
                root_id = references[0]
                threads[root_id].append(email_data)
            else:
                # No Message-ID or References, use subject
                subject = email_data.get('subject', '')
                if subject:
                    thread_id = f"subject_{hash(subject)}"
                    threads[thread_id].append(email_data)
        
        return dict(threads)
    
    def format_thread_for_analysis(self, thread_id: str, thread_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format a complete email thread for AI analysis.
        
        Args:
            thread_id: Unique identifier for the thread
            thread_emails: List of emails in the thread
            
        Returns:
            Formatted thread data ready for AI analysis
        """
        if not thread_emails:
            return {}
        
        # Sort emails by date to maintain conversation flow
        sorted_emails = sorted(thread_emails, key=lambda x: x.get('date', ''))
        
        # Extract thread metadata
        first_email = sorted_emails[0]
        last_email = sorted_emails[-1]
        
        # Collect all participants
        participants = set()
        senders = []
        recipients = []
        
        # Collect all subjects to track conversation evolution
        subjects = []
        
        # Collect all content and attachments
        combined_content = ""
        all_attachments = []
        attachment_summary = []
        
        # Track conversation flow
        conversation_flow = []
        
        for i, email_data in enumerate(sorted_emails):
            # Add sender to participants
            sender = email_data.get('sender', 'Unknown')
            participants.add(sender)
            senders.append(sender)
            
            # Add recipient if available
            recipient = email_data.get('to', 'Unknown')
            recipients.append(recipient)
            
            # Collect subject
            subject = email_data.get('subject', 'No Subject')
            subjects.append(subject)
            
            # Collect content
            content = email_data.get('content', '')
            date = email_data.get('date', 'Unknown Date')
            
            # Format conversation entry
            conversation_entry = f"""
=== Email {i+1} of {len(sorted_emails)} ===
Date: {date}
From: {sender}
To: {recipient}
Subject: {subject}
Content:
{content}
"""
            conversation_flow.append(conversation_entry)
            combined_content += f"\n--- Email {i+1} ---\n{content}\n"
            
            # Collect attachments
            attachments = email_data.get('attachments', [])
            if attachments:
                all_attachments.extend(attachments)
                for attachment in attachments:
                    attachment_info = {
                        'email_index': i + 1,
                        'sender': sender,
                        'date': date,
                        'filename': attachment.get('filename', 'Unknown'),
                        'content_type': attachment.get('content_type', 'Unknown'),
                        'size': attachment.get('size', 0),
                        'content_disposition': attachment.get('content_disposition', '')
                    }
                    attachment_summary.append(attachment_info)
        
        # # Extract application-related information
        # application_info = self._extract_application_info_from_thread(combined_content, subjects)
        
        # Create comprehensive thread summary
        thread_summary = {
            'thread_id': thread_id,
            'thread_metadata': {
                'total_emails': len(sorted_emails),
                'participants': list(participants),
                'date_range': {
                    'start_date': first_email.get('date', 'Unknown'),
                    'end_date': last_email.get('date', 'Unknown')
                },
                'conversation_duration': self._calculate_conversation_duration(
                    first_email.get('date', ''), 
                    last_email.get('date', '')
                ),
                'has_attachments': len(all_attachments) > 0,
                'total_attachments': len(all_attachments)
            },
            'conversation_details': {
                'subjects': subjects,
                'senders': senders,
                'recipients': recipients,
                'conversation_flow': conversation_flow
            },
            'content_analysis': {
                'combined_content': combined_content,
                'content_length': len(combined_content),
                'word_count': len(combined_content.split()),
                # 'application_info': application_info
            },
            'attachments': {
                'total_count': len(all_attachments),
                'summary': attachment_summary,
                'types': list(set([att.get('content_type', 'Unknown') for att in all_attachments]))
            },
            # 'thread_analysis': {
            #     'conversation_type': self._determine_conversation_type(subjects, combined_content),
            #     'priority_level': self._determine_priority_level(subjects, combined_content),
            #     'key_topics': self._extract_key_topics(combined_content, subjects),
            #     'action_items': self._extract_action_items(combined_content)
            # },
            'raw_emails': sorted_emails  # Keep original data for reference
        }
        
        return thread_summary
    
    def _extract_application_info_from_thread(self, content: str, subjects: List[str]) -> Dict[str, Any]:
        """Extract bank application information from thread content.
        
        Args:
            content: Combined content from all emails in thread
            subjects: List of subjects from all emails
            
        Returns:
            Dictionary of extracted application information
        """
        import re
        
        application_info = {
            'application_ids': [],
            'applicant_names': [],
            'loan_amounts': [],
            'status_updates': [],
            'dates': [],
            'phone_numbers': [],
            'email_addresses': [],
            'bank_names': [],
            'product_types': []
        }
        
        # Combine content and subjects for analysis
        full_text = content + " " + " ".join(subjects)
        full_text_lower = full_text.lower()
        
        # Extract application IDs
        app_id_patterns = [
            r'application[:\s]*id[:\s]*([A-Z0-9-]+)',
            r'app[:\s]*id[:\s]*([A-Z0-9-]+)',
            r'reference[:\s]*([A-Z0-9-]+)',
            r'case[:\s]*([A-Z0-9-]+)',
            r'tracking[:\s]*([A-Z0-9-]+)',
            r'loan[:\s]*id[:\s]*([A-Z0-9-]+)'
        ]
        
        for pattern in app_id_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            application_info['application_ids'].extend(matches)
        
        # Extract applicant names
        name_patterns = [
            r'name[:\s]*([A-Za-z\s]+)',
            r'applicant[:\s]*([A-Za-z\s]+)',
            r'customer[:\s]*([A-Za-z\s]+)',
            r'borrower[:\s]*([A-Za-z\s]+)'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            # Clean up names
            cleaned_names = [name.strip() for name in matches if len(name.strip()) > 2]
            application_info['applicant_names'].extend(cleaned_names)
        
        # Extract loan amounts
        amount_patterns = [
            r'loan[:\s]*amount[:\s]*([₹$]?[\d,]+\.?\d*)',
            r'amount[:\s]*([₹$]?[\d,]+\.?\d*)',
            r'([₹$]?[\d,]+\.?\d*)[:\s]*(?:lakh|lac|thousand|k)',
            r'rs[.\s]*([\d,]+\.?\d*)',
            r'rupees[:\s]*([\d,]+\.?\d*)'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, full_text, re.IGNORECASE)
            application_info['loan_amounts'].extend(matches)
        
        # Extract status updates
        status_keywords = [
            'approved', 'rejected', 'pending', 'under review', 'processing',
            'disbursed', 'sanctioned', 'completed', 'cancelled', 'on hold'
        ]
        
        for keyword in status_keywords:
            if keyword in full_text_lower:
                application_info['status_updates'].append(keyword)
        
        # Extract dates
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\w+\s+\d{1,2},?\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, full_text)
            application_info['dates'].extend(matches)
        
        # Extract phone numbers
        phone_pattern = r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
        phone_matches = re.findall(phone_pattern, full_text)
        application_info['phone_numbers'].extend(phone_matches)
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, full_text)
        application_info['email_addresses'].extend(email_matches)
        
        # Extract bank names
        bank_keywords = [
            'hdfc', 'sbi', 'icici', 'axis', 'kotak', 'yes bank', 'pnb', 'canara',
            'union bank', 'bank of baroda', 'idbi', 'central bank'
        ]
        
        for keyword in bank_keywords:
            if keyword in full_text_lower:
                application_info['bank_names'].append(keyword)
        
        # Extract product types
        product_keywords = [
            'home loan', 'personal loan', 'business loan', 'car loan', 'education loan',
            'gold loan', 'mortgage', 'credit card', 'overdraft'
        ]
        
        for keyword in product_keywords:
            if keyword in full_text_lower:
                application_info['product_types'].append(keyword)
        
        # Remove duplicates and ensure all values are strings
        for key in application_info:
            # Remove duplicates while preserving order
            seen = set()
            unique_items = []
            for item in application_info[key]:
                item_str = str(item)
                if item_str not in seen:
                    seen.add(item_str)
                    unique_items.append(item_str)
            application_info[key] = unique_items
        
        return application_info
    
    def _calculate_conversation_duration(self, start_date: str, end_date: str) -> str:
        """Calculate the duration of a conversation.
        
        Args:
            start_date: Start date string
            end_date: End date string
            
        Returns:
            Duration string
        """
        try:
            from datetime import datetime
            from dateutil import parser
            
            start = parser.parse(start_date)
            end = parser.parse(end_date)
            duration = end - start
            
            days = duration.days
            if days == 0:
                return "Same day"
            elif days == 1:
                return "1 day"
            elif days < 7:
                return f"{days} days"
            elif days < 30:
                weeks = days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''}"
            else:
                months = days // 30
                return f"{months} month{'s' if months > 1 else ''}"
        except:
            return "Unknown"
    
    def _determine_conversation_type(self, subjects: List[str], content: str) -> str:
        """Determine the type of conversation.
        
        Args:
            subjects: List of email subjects
            content: Combined email content
            
        Returns:
            Conversation type string
        """
        content_lower = content.lower()
        subjects_lower = " ".join(subjects).lower()
        
        # Check for bank application keywords
        bank_keywords = ['application', 'loan', 'credit', 'mortgage', 'approval', 'status']
        if any(keyword in content_lower or keyword in subjects_lower for keyword in bank_keywords):
            return "Bank Application"
        
        # Check for customer service
        service_keywords = ['support', 'help', 'issue', 'problem', 'complaint']
        if any(keyword in content_lower or keyword in subjects_lower for keyword in service_keywords):
            return "Customer Service"
        
        # Check for general inquiry
        inquiry_keywords = ['inquiry', 'question', 'information', 'details']
        if any(keyword in content_lower or keyword in subjects_lower for keyword in inquiry_keywords):
            return "General Inquiry"
        
        return "General Communication"
    
    def _determine_priority_level(self, subjects: List[str], content: str) -> str:
        """Determine the priority level of the conversation.
        
        Args:
            subjects: List of email subjects
            content: Combined email content
            
        Returns:
            Priority level string
        """
        content_lower = content.lower()
        subjects_lower = " ".join(subjects).lower()
        
        # High priority keywords
        high_priority = ['urgent', 'emergency', 'critical', 'immediate', 'asap']
        if any(keyword in content_lower or keyword in subjects_lower for keyword in high_priority):
            return "High"
        
        # Medium priority keywords
        medium_priority = ['important', 'priority', 'attention', 'review']
        if any(keyword in content_lower or keyword in subjects_lower for keyword in medium_priority):
            return "Medium"
        
        return "Normal"
    
    def _extract_key_topics(self, content: str, subjects: List[str]) -> List[str]:
        """Extract key topics from the conversation.
        
        Args:
            content: Combined email content
            subjects: List of email subjects
            
        Returns:
            List of key topics
        """
        import re
        
        # Common topics in bank applications
        topics = []
        full_text = content + " " + " ".join(subjects)
        full_text_lower = full_text.lower()
        
        topic_keywords = {
            'Documentation': ['document', 'paperwork', 'form', 'certificate', 'statement'],
            'Verification': ['verify', 'verification', 'confirm', 'check', 'validate'],
            'Approval Process': ['approval', 'approve', 'sanction', 'authorize'],
            'Disbursement': ['disburse', 'disbursement', 'payment', 'transfer'],
            'Status Update': ['status', 'update', 'progress', 'stage'],
            'Requirements': ['requirement', 'need', 'must', 'should', 'required'],
            'Timeline': ['timeline', 'deadline', 'schedule', 'time', 'date'],
            'Amount': ['amount', 'loan', 'money', 'sum', 'figure'],
            'Interest Rate': ['interest', 'rate', 'percentage', 'roi'],
            'EMI': ['emi', 'installment', 'monthly', 'payment']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in full_text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _extract_action_items(self, content: str) -> List[str]:
        """Extract action items from the conversation.
        
        Args:
            content: Combined email content
            
        Returns:
            List of action items
        """
        import re
        
        action_items = []
        content_lower = content.lower()
        
        # Action item patterns
        action_patterns = [
            r'please\s+([^.!?]+)',
            r'kindly\s+([^.!?]+)',
            r'need\s+to\s+([^.!?]+)',
            r'must\s+([^.!?]+)',
            r'should\s+([^.!?]+)',
            r'required\s+to\s+([^.!?]+)'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                action_items.append(match.strip())
        
        return action_items[:5]  # Limit to top 5 action items
    
    def get_formatted_threads_for_analysis(self, start_months_back: int = 3, end_months_back: int = 0, 
                                         max_threads: int = 5) -> List[Dict[str, Any]]:
        """Get formatted email threads ready for AI analysis.
        
        Args:
            start_months_back: Number of months back for start date
            end_months_back: Number of months back for end date
            max_threads: Maximum number of threads to process
            
        Returns:
            List of formatted thread data ready for AI analysis
        """
        # Fetch threads
        threads = self.fetch_recent_threads(
            start_months_back=start_months_back,
            end_months_back=end_months_back,
            max_threads=max_threads,
            max_emails_per_thread=20
        )
        
        # Format each thread for analysis
        formatted_threads = []
        
        for thread_id, thread_emails in threads.items():
            formatted_thread = self.format_thread_for_analysis(thread_id, thread_emails)
            if formatted_thread:
                formatted_threads.append(formatted_thread)
        
        return formatted_threads
    
    def _find_root_message_id(self, email_data: Dict[str, Any], all_emails: List[Dict[str, Any]]) -> str:
        """Find the root Message-ID for an email thread.
        
        Args:
            email_data: Email data dictionary
            all_emails: All emails in the mailbox
            
        Returns:
            Root Message-ID for the thread
        """
        message_id = email_data.get('message_id', '')
        if not message_id:
            return f"no_id_{hash(email_data.get('subject', ''))}"
        
        # Check References to find the root
        references = self._extract_references(email_data)
        
        # If no references, this is the root
        if not references:
            return message_id
        
        # Find the earliest referenced message
        root_id = references[0]  # First reference is usually the root
        
        # Verify this root exists in our email list
        for email in all_emails:
            if email.get('message_id') == root_id:
                return root_id
        
        # If root not found, use current message as root
        return message_id 

    def fetch_new_emails_since(self, since_datetime: datetime, folder: str = 'INBOX', max_emails: Optional[int] = 50) -> List[Dict[str, Any]]:
        """Fetch emails that arrived since a specific datetime.
        
        This method is specifically designed for email monitoring to get new emails
        since the last check, unlike fetch_emails_by_date_range which is for historical data.
        
        Args:
            since_datetime: Datetime to search from
            folder: Email folder to search in (default: 'INBOX')
            max_emails: Maximum number of emails to fetch (default: 50)
            
        Returns:
            List of new email data dictionaries
            
        Note:
            This method uses RFC822.PEEK to fetch email content without marking emails as read.
        """
        if not self.connection:
            logger.error("Not connected to Zoho Mail")
            return []
        
        try:
            # Select the specified folder
            self.connection.select(folder)
            
            # IMAP SINCE searches by date only, not time. To capture emails from today,
            # we need to search from the day before the since_datetime to ensure we don't miss any
            search_date_obj = since_datetime.date() - timedelta(days=1)
            search_date = search_date_obj.strftime("%d-%b-%Y")
            
            # Search for emails since the calculated date (broader search)
            search_criteria = f'SINCE {search_date}'
            logger.debug(f"Searching for emails in '{folder}' since: {search_date} (to filter for datetime: {since_datetime})")
            
            _, message_numbers = self.connection.search(None, search_criteria)
            
            if not message_numbers[0]:
                logger.debug(f"No emails found since {search_date} in folder '{folder}'")
                return []
            
            email_list = message_numbers[0].split()
            logger.debug(f"IMAP found {len(email_list)} emails since {search_date}")
            
            # Don't limit emails yet - we need to filter by time first
            # Then limit the final results after time filtering
            
            # Fetch emails and filter by actual datetime
            new_emails = []
            processed_count = 0
            skipped_old = 0
            skipped_errors = 0
            
            for num in email_list:
                try:
                    processed_count += 1
                    email_data = self._fetch_email_data(num)
                    if email_data:
                        email_date_str = email_data.get('date', '')
                        subject = email_data.get('subject', 'No Subject')
                        
                        # Parse email date and check if it's actually after since_datetime
                        if email_date_str:
                            if self._is_email_newer_than(email_date_str, since_datetime):
                                new_emails.append(email_data)
                                logger.debug(f"Including email: '{subject[:50]}...' from {email_date_str}")
                            else:
                                skipped_old += 1
                                logger.debug(f"Skipping old email: '{subject[:50]}...' from {email_date_str}")
                        else:
                            # If no date, include it to be safe (might be a new email)
                            new_emails.append(email_data)
                            logger.debug(f"Including email with no date: '{subject[:50]}...'")
                    else:
                        skipped_errors += 1
                except Exception as e:
                    skipped_errors += 1
                    logger.warning(f"Error fetching email {num}: {str(e)}")
                    continue
            
            # Now limit the results after filtering
            if max_emails and len(new_emails) > max_emails:
                # Sort by date to get the most recent emails
                new_emails.sort(key=lambda x: self._get_email_timestamp(x), reverse=True)
                new_emails = new_emails[:max_emails]
                logger.debug(f"Limited to {max_emails} most recent emails after filtering")
            
            logger.info(f"Email extraction summary: Processed {processed_count} emails, "
                       f"found {len(new_emails)} new emails since {since_datetime}, "
                       f"skipped {skipped_old} old emails, {skipped_errors} errors")
            return new_emails
            
        except Exception as e:
            logger.error(f"Error fetching new emails since {since_datetime}: {str(e)}")
            return []

    def _is_email_newer_than(self, email_date_str: str, since_datetime: datetime) -> bool:
        """Check if an email date is newer than the specified datetime.
        
        Args:
            email_date_str: Email date string from email headers
            since_datetime: Reference datetime to compare against
            
        Returns:
            True if email is newer than since_datetime
        """
        try:
            from dateutil import parser
            
            # Parse the email date string - handle common email date formats
            email_datetime = parser.parse(email_date_str)
            
            # Normalize timezone handling
            if email_datetime.tzinfo is not None and since_datetime.tzinfo is None:
                # Convert email datetime to local time (remove timezone)
                email_datetime = email_datetime.replace(tzinfo=None)
            elif email_datetime.tzinfo is None and since_datetime.tzinfo is not None:
                # Convert since_datetime to naive (remove timezone) 
                since_datetime = since_datetime.replace(tzinfo=None)
            
            # Compare with slight tolerance for same-minute emails
            # This helps handle rounding issues with email timestamps
            tolerance = timedelta(seconds=30)
            is_newer = email_datetime > (since_datetime - tolerance)
            
            logger.debug(f"Email date {email_datetime} vs since {since_datetime} (with {tolerance} tolerance): newer = {is_newer}")
            return is_newer
            
        except Exception as e:
            logger.warning(f"Error parsing email date '{email_date_str}': {str(e)}. Assuming email is new.")
            # If we can't parse the date, assume it's new to be safe
            return True

    def _get_email_timestamp(self, email_data: Dict[str, Any]) -> datetime:
        """Get email timestamp for sorting.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            Email datetime or current time if parsing fails
        """
        try:
            from dateutil import parser
            from datetime import timezone, timedelta
            email_date_str = email_data.get('date', '')
            if email_date_str:
                # Parse email date and ensure it's timezone-aware
                parsed_date = parser.parse(email_date_str)
                if parsed_date.tzinfo is None:
                    # If no timezone info, assume IST
                    ist_timezone = timezone(timedelta(hours=5, minutes=30))
                    parsed_date = parsed_date.replace(tzinfo=ist_timezone)
                return parsed_date
            # Return current time in IST if no date found
            ist_timezone = timezone(timedelta(hours=5, minutes=30))
            return datetime.now(ist_timezone)
        except:
            # Return current time in IST if parsing fails
            from datetime import timezone, timedelta
            ist_timezone = timezone(timedelta(hours=5, minutes=30))
            return datetime.now(ist_timezone)

    def check_connection(self) -> bool:
        """
        Check if email connection is working.
        
        Returns:
            True if connection is successful
        """
        try:
            # Try to connect and disconnect to test the connection
            test_success = self.connect()
            if test_success:
                self.disconnect()
                return True
            return False
        except Exception as e:
            logger.error(f"Email connection check failed: {str(e)}")
            return False 

                                    