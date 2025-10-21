"""Core metadata generation logic."""
import json
from pathlib import PurePosixPath
from typing import Optional
from jsonschema import validate, ValidationError

from .schema import FileInfo, MetadataRule, Config, GeneratedMetadata
from ..clients.bedrock_client import BedrockClient


class MetadataGenerator:
    """Generate metadata for files based on configured rules."""
    
    def __init__(self, config: Config, bedrock_client: BedrockClient):
        """
        Initialize metadata generator.
        
        Args:
            config: Configuration with rules and settings
            bedrock_client: Bedrock client for AI generation
        """
        self.config = config
        self.bedrock_client = bedrock_client
    
    def generate_metadata(self, file_info: FileInfo) -> GeneratedMetadata:
        """
        Generate metadata for a file.
        
        Args:
            file_info: Information about the file to process
            
        Returns:
            Generated metadata
            
        Raises:
            ValueError: If no matching rule found or generation fails
        """
        # Find matching rule
        rule = self._find_matching_rule(file_info.key)
        if not rule:
            raise ValueError(f"No matching rule found for file: {file_info.key}")
        
        # Build prompt from JSON Schema
        prompt = self._build_prompt(file_info, rule.schema)
        
        # Generate metadata using Bedrock with structured output
        raw_metadata = self.bedrock_client.generate_metadata(prompt, json_schema=rule.schema)
        
        # Validate against JSON Schema
        validated_metadata = self._validate_metadata(raw_metadata, rule.schema)
        
        return GeneratedMetadata(
            metadata=validated_metadata,
            file_key=file_info.key
        )
    
    def _find_matching_rule(self, file_key: str) -> Optional[MetadataRule]:
        """
        Find the first rule that matches the file key.
        
        Args:
            file_key: S3 object key to match
            
        Returns:
            Matching MetadataRule or None
        """
        for rule in self.config.rules:
            if self._match_pattern(file_key, rule.pattern):
                return rule
        
        return None
    
    def _match_pattern(self, file_key: str, pattern: str) -> bool:
        """
        Match a file key against a glob pattern.
        
        This method handles both root-level and nested files correctly,
        including patterns with ** (globstar).
        
        Args:
            file_key: S3 object key to match
            pattern: Glob pattern (e.g., "**/*.md", "reports/**/*.csv")
            
        Returns:
            True if the file key matches the pattern, False otherwise
        """
        # Use PurePosixPath for consistent path handling (S3 uses forward slashes)
        path = PurePosixPath(file_key)
        
        # Try direct match first
        if path.match(pattern):
            return True
        
        # For patterns starting with **, also try without the **/ prefix
        # This handles root-level files like "file.md" matching "**/*.md"
        if pattern.startswith('**/'):
            simple_pattern = pattern[3:]  # Remove "**/" prefix
            if path.match(simple_pattern):
                return True
        
        # For patterns with **/ in the middle (e.g., "reports/**/*.csv")
        # Try removing **/ entirely to match direct children
        if '/**/' in pattern:
            simple_pattern = pattern.replace('/**/', '/')
            if path.match(simple_pattern):
                return True
        
        return False
    
    def _build_prompt(self, file_info: FileInfo, schema: dict) -> str:
        """
        Build a prompt for Bedrock based on file info and JSON Schema.
        
        Args:
            file_info: File information
            schema: JSON Schema for metadata
            
        Returns:
            Formatted prompt string
        """
        # Extract schema information for prompt
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        
        # Build field descriptions
        field_descriptions = []
        for field_name, field_schema in properties.items():
            desc = field_schema.get('description', '')
            field_type = field_schema.get('type', 'string')
            
            field_info = f"- {field_name} ({field_type})"
            if field_name in required_fields:
                field_info += " [Required]"
            if desc:
                field_info += f": {desc}"
            
            # Add enum values if present
            if 'enum' in field_schema:
                enum_values = ', '.join(str(v) for v in field_schema['enum'])
                field_info += f"\n  Options: {enum_values}"
            
            # Add const value if present
            if 'const' in field_schema:
                field_info += f"\n  Fixed value: {field_schema['const']}"
            
            # Add array item info if present
            if field_type == 'array' and 'items' in field_schema:
                items_type = field_schema['items'].get('type', 'string')
                field_info += f"\n  Array items: {items_type}"
                if 'minItems' in field_schema:
                    field_info += f", minimum {field_schema['minItems']} items"
                if 'maxItems' in field_schema:
                    field_info += f", maximum {field_schema['maxItems']} items"
            
            field_descriptions.append(field_info)
        
        # Limit content length for prompt
        content_preview = file_info.content[:3000]
        if len(file_info.content) > 3000:
            content_preview += "\n... (truncated)"
        
        prompt = f"""Please generate metadata for the following file according to the specified JSON Schema.

## File Information
- File name: {file_info.file_name}
- File path: {file_info.key}

## File Content
{content_preview}

## Metadata Field Definitions
{chr(10).join(field_descriptions)}

## Generation Rules
1. All [Required] fields must be included
2. If enum or const (fixed value) is specified, use those values
3. Infer appropriate values from the file content
4. For Japanese files, generate values in English
5. If values are unknown, infer them from the file name or path

## Output Format
Output in valid JSON format. No explanatory text or additional text is needed.

Example:
```json
{{
  "field1": "value1",
  "field2": "value2"
}}
```

Please output in JSON format:"""
        
        return prompt
    
    def _validate_metadata(self, metadata: dict, schema: dict) -> dict:
        """
        Validate generated metadata against JSON Schema.
        
        Args:
            metadata: Generated metadata dictionary
            schema: JSON Schema to validate against
            
        Returns:
            Validated metadata (same as input if valid)
            
        Raises:
            ValueError: If metadata doesn't match schema
        """
        try:
            validate(instance=metadata, schema=schema)
            return metadata
        except ValidationError as e:
            # Provide detailed error message
            error_path = ' -> '.join(str(p) for p in e.path) if e.path else 'root'
            raise ValueError(
                f"Generated metadata validation failed at '{error_path}': {e.message}\n"
                f"Generated metadata: {json.dumps(metadata, ensure_ascii=False, indent=2)}"
            )
