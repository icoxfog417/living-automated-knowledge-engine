"""Email response sender service."""

import boto3
import logging
from ..models import ProcessingResult

logger = logging.getLogger(__name__)


class ResponseSender:
    """Send email responses."""

    def __init__(self):
        self.ses_client = boto3.client("ses")

    def send_upload_confirmation(self, recipient: str, result: ProcessingResult) -> None:
        """Send upload confirmation email."""
        try:
            if result.success:
                subject = "Document Upload Successful"
                body = f"""Your document upload was successful.

{result.message}

Files processed: {', '.join(result.details.get('files', []))}

The documents are now being processed for metadata generation and will be available in your Knowledge Base shortly."""
            else:
                subject = "Document Upload Failed"
                body = f"""Your document upload failed.

Error: {result.message}

Please check your attachments and try again. Supported file types: PDF, DOCX, TXT, XLSX, CSV (max 25MB each)."""

            self._send_email(recipient, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send upload confirmation: {e}")

    def send_command_response(self, recipient: str, result: ProcessingResult) -> None:
        """Send command response email."""
        try:
            if result.success:
                if result.details:
                    # Format statistics response
                    stats = result.details
                    body = f"""LAKE Statistics Report

Total Documents: {stats.get('total_documents', 0)}

Departments:"""
                    for dept, count in stats.get('departments', {}).items():
                        body += f"\n- {dept}: {count} documents"
                    
                    body += f"\n\nDocument Types:"
                    for doc_type, count in stats.get('document_types', {}).items():
                        body += f"\n- {doc_type}: {count} documents"
                    
                    if 'filtered_by' in stats:
                        body = f"Statistics for Department: {stats['filtered_by']}\n\n" + body
                else:
                    body = result.message
                    
                subject = "LAKE Command Response"
            else:
                subject = "LAKE Command Error"
                body = f"Command failed: {result.message}"

            self._send_email(recipient, subject, body)
            
        except Exception as e:
            logger.error(f"Failed to send command response: {e}")

    def _send_email(self, recipient: str, subject: str, body: str) -> None:
        """Send email via SES."""
        try:
            self.ses_client.send_email(
                Source="noreply@lake.example.com",  # Configure in environment
                Destination={"ToAddresses": [recipient]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Text": {"Data": body}}
                }
            )
            logger.info(f"Email sent to {recipient}: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            raise
