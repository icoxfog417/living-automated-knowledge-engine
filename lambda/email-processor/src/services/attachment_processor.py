"""Attachment processing service."""

import os
import logging
from ..models import EmailData, ProcessingResult
from ..clients.s3_operations import S3Operations

logger = logging.getLogger(__name__)


class AttachmentProcessor:
    """Process email attachments."""

    def __init__(self, s3_ops: S3Operations):
        self.s3_ops = s3_ops
        self.data_bucket = os.environ.get("DATA_BUCKET_NAME")
        self.allowed_types = {".pdf", ".docx", ".txt", ".xlsx", ".csv"}
        self.max_size = 25 * 1024 * 1024  # 25MB

    def process_attachments(self, email_data: EmailData) -> ProcessingResult:
        """Process attachments from email."""
        try:
            if not email_data.attachments:
                return ProcessingResult(
                    success=False,
                    message="No attachments found in email"
                )

            processed_files = []
            
            for attachment in email_data.attachments:
                filename = attachment["filename"]
                content = attachment["content"]
                
                # Validate file
                if not self._validate_attachment(filename, content):
                    continue
                
                # Upload to S3 data bucket
                s3_key = f"uploads/{filename}"
                self.s3_ops.upload_attachment(self.data_bucket, s3_key, content)
                processed_files.append(filename)
                
            if processed_files:
                return ProcessingResult(
                    success=True,
                    message=f"Successfully processed {len(processed_files)} files",
                    details={"files": processed_files}
                )
            else:
                return ProcessingResult(
                    success=False,
                    message="No valid attachments to process"
                )
                
        except Exception as e:
            logger.error(f"Failed to process attachments: {e}")
            return ProcessingResult(
                success=False,
                message=f"Processing failed: {str(e)}"
            )

    def _validate_attachment(self, filename: str, content: bytes) -> bool:
        """Validate attachment file."""
        # Check file extension
        _, ext = os.path.splitext(filename.lower())
        if ext not in self.allowed_types:
            logger.warning(f"Invalid file type: {filename}")
            return False
            
        # Check file size
        if len(content) > self.max_size:
            logger.warning(f"File too large: {filename}")
            return False
            
        return True
