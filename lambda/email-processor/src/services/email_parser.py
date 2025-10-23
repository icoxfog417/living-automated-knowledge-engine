"""Email parsing service."""

import email
import logging
from email.message import EmailMessage
from ..models import EmailData
from ..clients.s3_operations import S3Operations

logger = logging.getLogger(__name__)


class EmailParser:
    """Parse emails from S3 objects."""

    def __init__(self):
        self.s3_ops = S3Operations()

    def parse_email_from_s3(self, bucket: str, key: str) -> EmailData:
        """Parse email from S3 object."""
        try:
            email_content = self.s3_ops.get_email_object(bucket, key)
            msg = email.message_from_bytes(email_content)
            
            sender = msg.get("From", "")
            subject = msg.get("Subject", "")
            message_id = msg.get("Message-ID", "")
            
            # Extract body and attachments
            body = ""
            attachments = []
            
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                    elif part.get_content_disposition() == "attachment":
                        attachments.append({
                            "filename": part.get_filename(),
                            "content_type": part.get_content_type(),
                            "content": part.get_payload(decode=True)
                        })
            else:
                body = msg.get_payload(decode=True).decode()
            
            return EmailData(
                sender=sender,
                subject=subject,
                body=body.strip(),
                attachments=attachments,
                message_id=message_id
            )
            
        except Exception as e:
            logger.error(f"Failed to parse email {bucket}/{key}: {e}")
            raise
