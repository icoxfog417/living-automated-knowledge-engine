"""S3 operations for reading files and writing metadata."""

from __future__ import annotations

import json

import boto3

from ..core.schema import FileInfo, GeneratedMetadata


class S3Operations:
    """Handle S3 read and write operations."""

    def __init__(self, s3_client: boto3.client | None = None):
        """
        Initialize S3 operations.

        Args:
            s3_client: Optional boto3 S3 client. If not provided, creates a new one.
        """
        self.s3_client = s3_client or boto3.client("s3")

    def read_file(self, bucket: str, key: str, max_bytes: int = 50 * 1024 * 1024) -> FileInfo:
        """
        Read a file from S3.

        Args:
            bucket: S3 bucket name
            key: Object key
            max_bytes: Maximum bytes to read (default: 50MB for Bedrock KB compatibility)

        Returns:
            FileInfo object with file content

        Raises:
            Exception: If file cannot be read from S3
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)

            # Read content with size limit
            content_bytes = response["Body"].read(max_bytes)

            # Get appropriate parser and parse content
            from ..services.file_parser import FileParser

            parser = FileParser.get_parser(key)
            content = parser.parse(content_bytes)

            return FileInfo(bucket=bucket, key=key, content=content)
        except Exception as e:
            raise Exception(
                f"Failed to read file from S3 (bucket={bucket}, key={key}): {str(e)}"
            ) from e

    def write_metadata(self, bucket: str, metadata: GeneratedMetadata) -> None:
        """
        Write metadata JSON to S3.

        Args:
            bucket: S3 bucket name
            metadata: Generated metadata to write

        Raises:
            Exception: If metadata cannot be written to S3
        """
        try:
            # Wrap metadata with metadataAttributes field
            wrapped_metadata = {"metadataAttributes": metadata.metadata}

            metadata_json = json.dumps(wrapped_metadata, ensure_ascii=False, indent=2)

            self.s3_client.put_object(
                Bucket=bucket,
                Key=metadata.s3_key,
                Body=metadata_json.encode("utf-8"),
                ContentType="application/json",
                Metadata={
                    "generated-by": "lake-metadata-generator",
                },
            )
        except Exception as e:
            raise Exception(
                f"Failed to write metadata to S3 (bucket={bucket}, key={metadata.s3_key}): {str(e)}"
            ) from e

    def metadata_exists(self, bucket: str, file_key: str) -> bool:
        """
        Check if metadata file already exists for a given file.

        Args:
            bucket: S3 bucket name
            file_key: Original file key

        Returns:
            True if metadata file exists, False otherwise
        """
        metadata_key = f"{file_key}.metadata.json"

        try:
            self.s3_client.head_object(Bucket=bucket, Key=metadata_key)
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception:
            # If there's an error checking, assume it doesn't exist
            return False
