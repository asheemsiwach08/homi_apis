"""
Email processing package for Zoho Mail integration and email monitoring.
"""

from .zoho_mail_client import ZohoMailClient
from .email_parser import EmailParser
from .email_monitor import EmailMonitor

__all__ = [
    'ZohoMailClient',
    'EmailParser',
    'EmailMonitor'
] 