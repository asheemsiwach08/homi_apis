"""
Email parser for extracting and processing email content.
"""

import re
from typing import Dict, Any, List, Optional
from email import message_from_string
from email.header import decode_header
import logging

logger = logging.getLogger(__name__)


class EmailParser:
    """Parser for email content and metadata."""
    
    def __init__(self):
        """Initialize email parser."""
        # Common patterns for bank application information
        self.application_patterns = [
            r'application[:\s]*id[:\s]*([A-Z0-9-]+)',
            r'app[:\s]*id[:\s]*([A-Z0-9-]+)',
            r'reference[:\s]*([A-Z0-9-]+)',
            r'case[:\s]*([A-Z0-9-]+)',
            r'tracking[:\s]*([A-Z0-9-]+)'
        ]
        
        # Patterns for applicant names
        self.name_patterns = [
            r'name[:\s]*([A-Za-z\s]+)',
            r'applicant[:\s]*([A-Za-z\s]+)',
            r'customer[:\s]*([A-Za-z\s]+)'
        ]
        
        # Patterns for dates
        self.date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\w+\s+\d{1,2},?\s+\d{4}'
        ]
    
    def parse_email(self, email_content: str, email_headers: Dict[str, str]) -> Dict[str, Any]:
        """Parse email content and extract structured information.
        
        Args:
            email_content: Raw email content
            email_headers: Email headers dictionary
            
        Returns:
            Parsed email information dictionary
        """
        try:
            parsed_info = {
                'subject': email_headers.get('subject', ''),
                'sender': email_headers.get('from', ''),
                'date': email_headers.get('date', ''),
                'message_id': email_headers.get('message-id', ''),
                'content': email_content,
                'extracted_data': {}
            }
            
            # Extract structured data
            parsed_info['extracted_data'] = self._extract_structured_data(email_content)
            
            # Clean and normalize content
            parsed_info['clean_content'] = self._clean_content(email_content)
            
            logger.debug(f"Email parsed successfully - Message ID: {parsed_info['message_id']}, Subject: {parsed_info['subject']}")
            
            return parsed_info
            
        except Exception as e:
            logger.error(f"Error parsing email: {str(e)}")
            return {
                'subject': email_headers.get('subject', ''),
                'sender': email_headers.get('from', ''),
                'date': email_headers.get('date', ''),
                'message_id': email_headers.get('message-id', ''),
                'content': email_content,
                'extracted_data': {},
                'clean_content': '',
                'error': str(e)
            }
    
    def _extract_structured_data(self, content: str) -> Dict[str, Any]:
        """Extract structured data from email content.
        
        Args:
            content: Email content string
            
        Returns:
            Dictionary of extracted data
        """
        extracted_data = {
            'application_ids': [],
            'applicant_names': [],
            'dates': [],
            'phone_numbers': [],
            'email_addresses': [],
            'amounts': []
        }
        
        # Extract application IDs
        for pattern in self.application_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            extracted_data['application_ids'].extend(matches)
        
        # Extract applicant names
        for pattern in self.name_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            # Clean up names
            cleaned_names = [name.strip() for name in matches if len(name.strip()) > 2]
            extracted_data['applicant_names'].extend(cleaned_names)
        
        # Extract dates
        for pattern in self.date_patterns:
            matches = re.findall(pattern, content)
            extracted_data['dates'].extend(matches)
        
        # Extract phone numbers
        phone_pattern = r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
        phone_matches = re.findall(phone_pattern, content)
        extracted_data['phone_numbers'].extend(phone_matches)
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, content)
        extracted_data['email_addresses'].extend(email_matches)
        
        # Extract monetary amounts
        amount_pattern = r'\$[\d,]+\.?\d*'
        amount_matches = re.findall(amount_pattern, content)
        extracted_data['amounts'].extend(amount_matches)
        
        # Remove duplicates
        for key in extracted_data:
            if isinstance(extracted_data[key], list):
                extracted_data[key] = list(set(extracted_data[key]))
        
        return extracted_data
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize email content.
        
        Args:
            content: Raw email content
            
        Returns:
            Cleaned content string
        """
        if not content:
            return ""
        
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common email signatures
        signature_patterns = [
            r'--\s*\n.*',
            r'Best regards,.*',
            r'Sincerely,.*',
            r'Thank you,.*'
        ]
        
        for pattern in signature_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Strip leading/trailing whitespace
        content = content.strip()
        
        return content
    
    def extract_application_id(self, content: str) -> Optional[str]:
        """Extract the most likely application ID from content.
        
        Args:
            content: Email content
            
        Returns:
            Application ID if found, None otherwise
        """
        for pattern in self.application_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                app_id = match.group(1).strip()
                if app_id and len(app_id) >= 3:  # Minimum length validation
                    return app_id
        
        return None
    
    def extract_applicant_name(self, content: str) -> Optional[str]:
        """Extract the most likely applicant name from content.
        
        Args:
            content: Email content
            
        Returns:
            Applicant name if found, None otherwise
        """
        for pattern in self.name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name and len(name) >= 3:  # Minimum length validation
                    return name
        
        return None
    
    def is_bank_application_email(self, content: str, subject: str) -> bool:
        """Determine if an email is related to bank applications.
        
        Args:
            content: Email content
            subject: Email subject
            
        Returns:
            True if likely a bank application email, False otherwise
        """
        # Keywords that indicate bank application emails
        bank_keywords = [
            'application', 'apply', 'loan', 'credit', 'mortgage',
            'banking', 'account', 'approval', 'status', 'verification',
            'document', 'form', 'submission', 'review'
        ]
        
        # Check subject and content for keywords
        combined_text = f"{subject} {content}".lower()
        
        keyword_count = sum(1 for keyword in bank_keywords if keyword in combined_text)
        
        # If we find multiple keywords, it's likely a bank application email
        return keyword_count >= 2
    
    def get_email_priority(self, content: str, subject: str) -> str:
        """Determine the priority of an email based on content analysis.
        
        Args:
            content: Email content
            subject: Email subject
            
        Returns:
            Priority level ('high', 'medium', 'low')
        """
        # High priority keywords
        high_priority = ['urgent', 'immediate', 'critical', 'emergency', 'rejected', 'denied']
        
        # Medium priority keywords
        medium_priority = ['pending', 'review', 'approval', 'status', 'update']
        
        combined_text = f"{subject} {content}".lower()
        
        # Check for high priority keywords
        for keyword in high_priority:
            if keyword in combined_text:
                return 'high'
        
        # Check for medium priority keywords
        for keyword in medium_priority:
            if keyword in combined_text:
                return 'medium'
        
        return 'low' 