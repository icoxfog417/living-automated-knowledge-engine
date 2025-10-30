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
class MetadataField:
    """Definition of a metadata field."""
    
    type: str  # "STRING", "STRING_LIST", "NUMBER", "BOOLEAN"
    description: str
    options: list[str] | None = None


@dataclass
class PathRule:
    """Rule for extracting metadata from file paths."""
    
    pattern: str
    extractions: dict[str, str]


@dataclass
class FileTypeRule:
    """Rule for metadata extraction based on file type."""
    
    extensions: list[str] | None = None
    use_columns_for_metadata: bool | None = None


@dataclass
class Config:
    """Application configuration."""

    metadata_fields: dict[str, MetadataField]
    path_rules: list[PathRule]
    file_type_rules: dict[str, list[FileTypeRule]]
    bedrock_model_id: str
    bedrock_max_tokens: int
    bedrock_input_context_window: int
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
