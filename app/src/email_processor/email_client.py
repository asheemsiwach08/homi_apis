import email
import imaplib2
import logging
import re
import html
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import Message
from app.config.config import config   # TODO: Rename this import

logger = logging.getLogger(__name__)


class MailClient:
    """Client for connecting to mail server via IMAP."""

    def __init__(self):
        """Initialize Mail client."""
        self.gmail_config = config.get_gmail_config()
        self.zoho_config = config.get_zoho_config()
        self.connection: Optional[imaplib2.IMAP4_SSL] = None

    def connect(self, mail_client: str = 'zoho') -> bool:  # Default to Zoho
        """Connect to Mail IMAP server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if mail_client == 'gmail':
                self.connection = imaplib2.IMAP4_SSL(
                    self.gmail_config['imap_server'],
                    self.gmail_config['imap_port']
                )

                # Login
                self.connection.login(
                    self.gmail_config['email'],
                    self.gmail_config['password']
                )
                logger.info("Successfully connected to Gmail.")

            elif mail_client == 'zoho':
                self.connection = imaplib2.IMAP4_SSL(
                    self.zoho_config['imap_server'],
                    self.zoho_config['imap_port']
                )

                # Login
                self.connection.login(
                    self.zoho_config['email'],
                    self.zoho_config['password']
                )
                logger.info("Successfully connected to Zoho.")

            else:
                logger.error(f"Invalid mail client: {mail_client}")
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to connect to mail server: {str(e)}")
            return False

    def disconnect(self) -> None:
        """Disconnect from mail server."""    
        if self.connection:
            try:
                self.connection.logout()
                logger.info("Disconnected from mail server.")
            except Exception as e:
                logger.error(f"Error disconnecting from mail server: {str(e)}")
            finally:
                self.connection = None

    def check_connection(self) -> bool:
        """Check if the mail server connection is established."""
        try:
            test_success = self.connect()
            if test_success:
                self.disconnect()
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking mail server connection: {str(e)}")
            return False

    def find_emails(
        self,
        folder: str = 'INBOX',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        subject_filter: Optional[str] = None,
        sender_filter: Optional[str] = None,
        max_emails: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get emails by date range.
        
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
            logger.error("Not connected to Gmail")
            return []

        try:
            # Set default dates if not provided
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=1)

            # Select the folder
            self.connection.select(folder)

            # Format dates for IMAP search
            start_date_str = start_date.strftime("%d-%b-%Y")
            end_date_str = end_date.strftime("%d-%b-%Y")

            # Build search criteria
            search_parts = [] 
            search_parts.append(f"SINCE {start_date_str}")  # DAte range
            # Only aDD BEFORE if end_date is actually in the past
            today = datetime.now().date()
            end_date_only = end_date.date() if isinstance(end_date, datetime) else end_date

            if end_date_only < today:
                search_parts.append(f"BEFORE {end_date_str}")

            # Subject filter
            if subject_filter:
                search_parts.append(f"SUBJECT '{subject_filter}'")

            # Sender filter
            if sender_filter:
                search_parts.append(f"FROM '{sender_filter}'")

            # Combine search criteria
            search_criteria = " ".join(search_parts)
            logger.info(f"Searching emails in '{folder}' with criteria: {search_criteria}")

            _, message_numbers = self.connection.search(None, search_criteria)

            if not message_numbers[0]:
                logger.info(f"No emails found matching criteria in '{folder}'")
                return []

            email_list = message_numbers[0].decode('utf-8').split()  # .split()
            logger.info(f"Found {len(email_list)} emails matching criteria")

            # Limit the number of eamils if specified
            if max_emails and len(email_list) > max_emails:
                email_list = email_list[-max_emails:]     # You can change this to get more or less emails
                logger.info(f"Limited to {max_emails} most recent emails")

            # fetch email data
            emails = []
            for num in email_list:
                try:
                    email_data = self.get_email_data(num)
                    if email_data:
                        emails.append(email_data)
                        # print(f"🪧 Email {num} fetched successfully")   
                except Exception as e:
                    logger.warning(f"Error fetching email {num}: {str(e)}")
                    continue

            if len(emails) == 0:
                logger.info("No emails fetched successfully")
                return []
            else:
                logger.info(f"Successfully fetched {len(emails)} emails from {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')}. Unable to fetch {len(email_list) - len(emails)} emails.")
                return emails
            
        except Exception as e:
            logger.warning(f"Error fetching emails from date range: {str(e)}")
            return []

    def get_email_data(self, email_num: int) -> Optional[Dict[str, Any]]:
        """
        Get email data for a specific email.

        Args:
            email_num: Email message number

        Returns:
            Email data dictionary or None if error
        """
        if not self.connection:
            logger.warning("Not connected to Gmail while getting particular email data(get_email_data)")
            return None

        try:
            _, msg_data = self.connection.fetch(str(email_num), '(BODY.PEEK[])')
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

            # from app.src.email_processor.email_parser import EmailParser
            # email_parser = EmailParser()
            # new_content = email_parser._clean_content(text=content)
            from app.src.data_processing.text_extractor import clean_email_content
            new_content = clean_email_content(text=content)
            # print("----------------------------------------------------------------------")
            # print("Subject: ", subject)
            # print(f"🔹🔹🔹 New Content: {new_content} 🔹🔹")
            # print("----🔹 Raw Content 🔹------->>>",content)
            # print(f"🚩 Raw Content Length: {len(content)}, New length: {len(new_content)} 🚩")
            # print("----------------------------------------------------------------------")

            # # Extract attachments
            # attachments = self._extract_attachments(email_message)

            email_data = {
                "message_id": message_id,
                "subject": subject,
                "sender": sender,
                "date": date,
                "content": new_content,
                # "attachments": attachments,  # TODO: Check this later
                "raw_message": email_message,
                "email_num": email_num
            }
            # print("----------------------------------------------------------------------")
            # print("Sender: ", sender)
            # print("Sender Name:", sender.split('<')[0].strip())
            # print("Sender Email:", sender.split('<')[1].strip())
            # print("Subject: ", subject)
            # print("Date: ", date)
            # print("Content: ", content)
            # # print("Raw Message: ", email_message)
            # print("Email Num: ", email_num)
            # print("----------------------------------------------------------------------")
            return email_data

        except Exception as e:
            logger.warning(f"Error getting email data for email {email_num}: {str(e)}")
            return None

    def _decode_header(self, header: Optional[str]) -> str:
        """
        Decode email header.

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
            logger.warning(f"Error decoding header {header}: {str(e)}")
            return str(header) if header else ""

    def _extract_email_content(self, email_message: Message) -> str:
        """
        Extract email content from email message.

        Args:
            email_message: Email message object

        Returns:
            Extracted email content
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
                        logger.warning(f"Error extracting multipart content {str(e)}")

        else:
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    charset = email_message.get_content_charset() or 'utf-8'
                    content = payload.decode(charset, errors='ignore')

                    # Check if content is HTML and strip HTML tags
                    content_type = email_message.get_content_type()
                    if isinstance(content, str) and (content_type == 'text/html' or self._is_html_content(content)):
                        content = self._strip_html(content)
            except Exception as e:
                logger.warning(f"Error extracting single part content {str(e)}")
        
        return content

    def _is_html_content(self, content: str) -> bool:
        """
        Check if content contains HTML tags.
        
        Args:
            content: Content string to check
            
        Returns:
            True if content appears to be HTML, False otherwise
        """
        if not isinstance(content, str):
            return False
        
        # Check for common HTML tags
        html_pattern = re.compile(r'<[^>]+>', re.IGNORECASE)
        return bool(html_pattern.search(content))

    def _strip_html(self, html_content: str) -> str:
        """
        Strip HTML tags from content and decode HTML entities.
        
        Args:
            html_content: HTML content string
            
        Returns:
            Plain text content with HTML tags removed
        """
        if not isinstance(html_content, str):
            return html_content
        
        # Remove script and style tags with their content
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # Remove all HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities (e.g., &nbsp; -> space, &amp; -> &)
        html_content = html.unescape(html_content)
        
        # Clean up whitespace - replace multiple spaces/newlines with single space
        html_content = re.sub(r'\s+', ' ', html_content)
        
        # Strip leading/trailing whitespace
        html_content = html_content.strip()
        
        return html_content

    def _extract_attachments(self, email_message: Message) -> List[Dict[str, Any]]:
        """
        Extract attachments from email message.

        Args:
            email_message: Email message object

        Returns:
            List of attachment dictionaries with filename, content_type, size and data
        """
        attachments = []
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    # Skip if this is the main text part
                    if part.get_content_maintype() == "multipart":
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
                                "filename": filename,
                                "content_type": part.get_content_type(),
                                "size": len(attachment_data),
                                "data": attachment_data,
                                "content_disposition": part.get("Content-Disposition", ""),
                                "content_id": part.get("Content-ID", "")
                            }
                            attachments.append(attachment_info)
                            print(f"Extracted attachment: {filename} ({len(attachment_data)} bytes)")

            # Handle single part mesages that might be attachments
            elif email_message.get_filename():
                filename = self._decode_header(email_message.get_filename())
                attachment_data = email_message.get_payload(decode=True)
                if attachment_data:
                    attachment_info = {
                        "filename": filename,
                        "content_type": email_message.get_content_type(),
                        "size": len(attachment_data),
                        "data": attachment_data,
                        "content_disposition": email_message.get("Content-Disposition", ""),
                        "content_id": email_message.get("Content-ID", "")
                    }
                    attachments.append(attachment_info)
                    print(f"Extracted attachment(elif part): {filename} ({len(attachment_data)} bytes)")

        except Exception as e:
            logger.warning(f"Error extracting attachments: {str(e)}")

        return attachments

    # def save_attachment(self, attachment_data: Dict[str, Any], save_dir: str = "attachments") -> str:
    #     """
    #     Save an attachment to disk.

    #     Args:
    #         attachment_data: Attachment dictionary with filename, data, etc.
    #         save_dir: Directory to save attachments (default: "attachments")

    #     Returns:
    #         Path to save file or empty string if failed
    #     """


############################################################################################################
                           #     Email Thread Fetching Methods     #
############################################################################################################

    def _extract_references(self, email_data: Dict[str, Any]) -> List[str]:
        """Extract References from email headers.
        
        Args:
            email_data: Email data dictionary
            
        Returns:
            List of Message-IDs from References header
        """
        references = []

        # Get references header
        ref_header = email_data.get("headers", {}).get("references", None)
        if ref_header:
            # Parse references header (space-separated Message-IDs)
            ref_ids = ref_header.strip().split()
            references.extend(ref_ids)

        # Also check In-Reply-To header
        in_reply_to = email_data.get("headers", {}).get("in-reply-to", None)
        if in_reply_to:
            references.append(in_reply_to.strip())

        return references

    def _find_root_message_id(self, email_data: Dict[str, Any], all_emails: List[Dict[str, Any]]) -> str:
        """Find the root Message-ID for an email thread.
        
        Args:
            email_data: Email data dictionary
            all_emails: All emails in the mailbox
            
        Returns:
            Root Message-ID for the thread
        """
        message_id = email_data.get("message_id", None)
        if not message_id:
            return f"no_id_{hash(email_data.get("subject", ""))}"

        # Check References to find the root
        references = self._extract_references(email_data)

        # If no references, this is the root
        if not references:
            return message_id

        # Find the earliest referenced message
        root_id = references[0]

        # Verify this root exists in our email list
        for email in all_emails:
            if email.get("message_id") == root_id:
                print(f"✅ Found root message ID: {root_id}")
                return root_id
            else:
                return message_id  # If root not found, use current message as root

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
            message_id = email_data.get("message_id", None)
            references = self._extract_references(email_data)
            print(f"🟠➡️ REFERENCES: {references}, Message ID: {message_id}")

            if message_id:
                # Find the root message ID
                root_id = self._find_root_message_id(email_data, emails)
                print(f"✅ Root message ID: {root_id}")
                threads[root_id].append(email_data)
            elif references:
                # Use first reference as thread ID
                root_id = references[0]
                print(f"✅ ReferenceRoot message ID: {root_id}")
                threads[root_id].append(email_data)
            else:
                # No message-ID or references, use subject
                subject = email_data.get("subject", None)
                if subject:
                    thread_id = f"subject_{hash(subject)}"
                    print(f"❌ Subject: {subject} Root message ID: {thread_id}")
                    threads[thread_id].append(email_data)
        
        return dict(threads)


############################################################################################################