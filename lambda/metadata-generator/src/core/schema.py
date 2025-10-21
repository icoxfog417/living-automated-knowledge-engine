"""Data models for metadata generation."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FileInfo:
    """Information about a file to process."""
    bucket: str
    key: str
    content: str
    
    @property
    def file_name(self) -> str:
        """Get the file name from the key."""
        return Path(self.key).name
    
    @property
    def extension(self) -> str:
        """Get the file extension from the key."""
        return Path(self.key).suffix


@dataclass
class MetadataRule:
    """A rule for generating metadata based on file patterns."""
    pattern: str
    schema: dict[str, Any]


@dataclass
class Config:
    """Application configuration."""
    rules: list[MetadataRule]
    bedrock_model_id: str
    bedrock_max_tokens: int
    bedrock_temperature: float


@dataclass
class GeneratedMetadata:
    """Generated metadata result."""
    metadata: dict[str, Any]
    file_key: str
    
    @property
    def s3_key(self) -> str:
        """Get the S3 key for the metadata file."""
        return f"{self.file_key}.metadata.json"
