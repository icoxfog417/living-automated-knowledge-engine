"""S3 operations client."""

import boto3
import logging
from typing import Any

logger = logging.getLogger(__name__)


class S3Operations:
    """Handle S3 operations for email processing."""

    def __init__(self):
        self.s3_client = boto3.client("s3")

    def get_email_object(self, bucket: str, key: str) -> bytes:
        """Get email object from S3."""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Failed to get email object {bucket}/{key}: {e}")
            raise

    def upload_attachment(self, bucket: str, key: str, content: bytes) -> None:
        """Upload attachment to S3."""
        try:
            self.s3_client.put_object(Bucket=bucket, Key=key, Body=content)
            logger.info(f"Uploaded attachment to {bucket}/{key}")
        except Exception as e:
            logger.error(f"Failed to upload attachment {bucket}/{key}: {e}")
            raise

    def list_metadata_files(self, bucket: str, prefix: str = "") -> list[dict]:
        """List metadata files in S3."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            return response.get("Contents", [])
        except Exception as e:
            logger.error(f"Failed to list metadata files: {e}")
            raise

    def get_metadata_content(self, bucket: str, key: str) -> dict:
        """Get metadata file content."""
        import json
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return json.loads(response["Body"].read().decode())
        except Exception as e:
            logger.error(f"Failed to get metadata {bucket}/{key}: {e}")
            raise
