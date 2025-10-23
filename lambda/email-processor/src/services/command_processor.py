"""Command processing service."""

import os
import logging
from ..models import EmailData, ProcessingResult
from ..clients.s3_operations import S3Operations

logger = logging.getLogger(__name__)


class CommandProcessor:
    """Process email commands."""

    def __init__(self, s3_ops: S3Operations):
        self.s3_ops = s3_ops
        self.data_bucket = os.environ.get("DATA_BUCKET_NAME")

    def process_command(self, email_data: EmailData) -> ProcessingResult:
        """Process command from email body."""
        try:
            command = email_data.body.strip().lower()
            
            if command == "get stats":
                return self._get_stats()
            elif command.startswith("get stats "):
                department = command.replace("get stats ", "").strip()
                return self._get_stats(department)
            elif command == "help":
                return self._get_help()
            elif command.startswith("status "):
                filename = command.replace("status ", "").strip()
                return self._get_status(filename)
            else:
                return ProcessingResult(
                    success=False,
                    message=f"Unknown command: {command}. Send 'help' for available commands."
                )
                
        except Exception as e:
            logger.error(f"Failed to process command: {e}")
            return ProcessingResult(
                success=False,
                message=f"Command processing failed: {str(e)}"
            )

    def _get_stats(self, department: str = None) -> ProcessingResult:
        """Get metadata statistics."""
        try:
            metadata_files = self.s3_ops.list_metadata_files(
                self.data_bucket, 
                "uploads/"
            )
            
            total_docs = 0
            departments = {}
            doc_types = {}
            
            for file_obj in metadata_files:
                if file_obj["Key"].endswith(".metadata.json"):
                    try:
                        metadata = self.s3_ops.get_metadata_content(
                            self.data_bucket, 
                            file_obj["Key"]
                        )
                        
                        dept = metadata.get("department", "Unknown")
                        doc_type = metadata.get("document_type", "Unknown")
                        
                        if department and dept.lower() != department.lower():
                            continue
                            
                        total_docs += 1
                        departments[dept] = departments.get(dept, 0) + 1
                        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to read metadata {file_obj['Key']}: {e}")
                        continue
            
            stats = {
                "total_documents": total_docs,
                "departments": departments,
                "document_types": doc_types
            }
            
            if department:
                stats["filtered_by"] = department
            
            return ProcessingResult(
                success=True,
                message="Statistics generated successfully",
                details=stats
            )
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return ProcessingResult(
                success=False,
                message=f"Failed to generate statistics: {str(e)}"
            )

    def _get_help(self) -> ProcessingResult:
        """Get help information."""
        help_text = """
Available Commands:
- get stats: Get overall document statistics
- get stats [department]: Get statistics for specific department
- status [filename]: Check processing status of a file
- help: Show this help message
        """.strip()
        
        return ProcessingResult(
            success=True,
            message=help_text
        )

    def _get_status(self, filename: str) -> ProcessingResult:
        """Get status of specific file."""
        try:
            # Check if file exists
            metadata_key = f"uploads/{filename}.metadata.json"
            try:
                metadata = self.s3_ops.get_metadata_content(self.data_bucket, metadata_key)
                return ProcessingResult(
                    success=True,
                    message=f"File '{filename}' has been processed successfully",
                    details=metadata
                )
            except:
                return ProcessingResult(
                    success=True,
                    message=f"File '{filename}' not found or not yet processed"
                )
                
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return ProcessingResult(
                success=False,
                message=f"Failed to check status: {str(e)}"
            )
