"""Core metadata generation logic."""

import json

from ..clients.bedrock_client import BedrockClient
from ..services.prompt_builder import PromptBuilder
from ..services.rule_matcher import RuleMatcher
from .schema import Config, FileInfo, GeneratedMetadata


class MetadataGenerator:
    """Generate metadata for files based on configured rules."""

    def __init__(self, config: Config, bedrock_client: BedrockClient, rule_matcher: RuleMatcher):
        """
        Initialize metadata generator.

        Args:
            config: Configuration with metadata fields and rules
            bedrock_client: Bedrock client for AI generation
            rule_matcher: Rule matcher for finding matching rules
        """
        self.config = config
        self.bedrock_client = bedrock_client
        self.rule_matcher = rule_matcher

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
        # Find matching path rule
        rule = self.rule_matcher.find_matching_rule(file_info.key)
        if not rule:
            raise ValueError(f"No matching rule found for file: {file_info.key}")

        # Extract path-based metadata (highest priority)
        path_metadata = self.rule_matcher.extract_values(file_info.key, rule)

        # Build JSON schema from metadata fields for AI generation
        json_schema = self._build_json_schema()

        # Calculate max content characters based on input context window
        max_content_chars = PromptBuilder.calculate_max_content_chars(
            input_context_window=self.config.bedrock_input_context_window
        )

        # Build prompt for AI generation
        prompt = PromptBuilder.build_metadata_prompt(
            file_info, json_schema, max_content_chars=max_content_chars
        )

        # Generate metadata using Bedrock
        ai_metadata = self.bedrock_client.generate_metadata(prompt, json_schema=json_schema)

        # Merge metadata: path-based overrides AI-generated
        final_metadata = {**ai_metadata, **path_metadata}

        return GeneratedMetadata(metadata=final_metadata, file_key=file_info.key)

    def _build_json_schema(self) -> dict:
        """
        Build JSON schema from metadata fields configuration.

        Returns:
            JSON schema for metadata validation
        """
        properties = {}
        required = []

        for field_name, field_def in self.config.metadata_fields.items():
            prop = {
                "type": self._convert_field_type(field_def.type),
                "description": field_def.description
            }
            
            if field_def.options:
                prop["enum"] = field_def.options
            
            properties[field_name] = prop
            required.append(field_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def _convert_field_type(self, field_type: str) -> str:
        """Convert metadata field type to JSON schema type."""
        type_mapping = {
            "STRING": "string",
            "STRING_LIST": "array",
            "NUMBER": "number",
            "BOOLEAN": "boolean"
        }
        return type_mapping.get(field_type, "string")
