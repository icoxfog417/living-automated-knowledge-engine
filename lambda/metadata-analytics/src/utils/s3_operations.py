"""S3 operations utilities."""

import json
import logging
from datetime import datetime
from typing import Iterator, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def upload_to_s3(bucket: str, key: str, file_path: str) -> str:
    """Upload a file to S3.

    Args:
        bucket: S3 bucket name
        key: S3 object key (path in bucket)
        file_path: Local file path to upload

    Returns:
        S3 URL of the uploaded file (s3://bucket/key format)

    Raises:
        ClientError: If upload fails
    """
    s3_client = boto3.client("s3")

    try:
        logger.info(f"Uploading {file_path} to s3://{bucket}/{key}")
        s3_client.upload_file(file_path, bucket, key)
        s3_url = f"s3://{bucket}/{key}"
        logger.info(f"Successfully uploaded to {s3_url}")
        return s3_url

    except ClientError as e:
        logger.error(f"Failed to upload {file_path} to s3://{bucket}/{key}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading {file_path}: {e}")
        raise


class S3Operations:
    """Utility class for S3 operations."""

    def __init__(self, s3_client: Optional[boto3.client] = None):
        """Initialize S3 operations.

        Args:
            s3_client: boto3 S3 client (injectable for testing)
        """
        self.s3_client = s3_client or boto3.client("s3")

    def list_metadata_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Iterator[dict]:
        """List .metadata.json files from S3 with pagination support.

        Args:
            bucket: S3 bucket name
            prefix: S3 prefix to filter files
            start_date: Filter files modified after this date
            end_date: Filter files modified before this date

        Yields:
            File information dict (Key, LastModified, Size)
        """
        paginator = self.s3_client.get_paginator("list_objects_v2")

        page_config = {"Bucket": bucket}

        if prefix:
            page_config["Prefix"] = prefix

        try:
            for page in paginator.paginate(**page_config):
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]

                    # Only .metadata.json files
                    if not key.endswith(".metadata.json"):
                        continue

                    last_modified = obj["LastModified"]

                    # Date filtering
                    if start_date and last_modified < start_date:
                        continue
                    if end_date and last_modified > end_date:
                        continue

                    yield {"Key": key, "LastModified": last_modified, "Size": obj["Size"]}

        except ClientError as e:
            logger.error(f"Failed to list objects from s3://{bucket}/{prefix or ''}: {e}")
            raise

    def download_metadata_content(self, bucket: str, key: str) -> Optional[dict]:
        """Download and parse metadata file from S3.

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            Parsed metadata dictionary, or None if error occurs
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8")

            metadata = json.loads(content)
            return metadata

        except ClientError as e:
            logger.error(f"Failed to download s3://{bucket}/{key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON s3://{bucket}/{key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading s3://{bucket}/{key}: {e}")
            return None
