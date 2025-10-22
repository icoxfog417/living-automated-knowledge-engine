"""Core metadata generation logic."""

import json

from jsonschema import ValidationError, validate

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
            config: Configuration with rules and settings
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
        # Find matching rule (delegated to RuleMatcher)
        rule = self.rule_matcher.find_matching_rule(file_info.key)
        if not rule:
            raise ValueError(f"No matching rule found for file: {file_info.key}")

        # Calculate max content characters based on input context window
        max_content_chars = PromptBuilder.calculate_max_content_chars(
            input_context_window=self.config.bedrock_input_context_window
        )

        # Build prompt from JSON Schema (delegated to PromptBuilder)
        prompt = PromptBuilder.build_metadata_prompt(
            file_info, rule.schema, max_content_chars=max_content_chars
        )

        # Generate metadata using Bedrock with structured output
        raw_metadata = self.bedrock_client.generate_metadata(prompt, json_schema=rule.schema)

        # Validate against JSON Schema
        validated_metadata = self._validate_metadata(raw_metadata, rule.schema)

        return GeneratedMetadata(metadata=validated_metadata, file_key=file_info.key)

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
            error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            raise ValueError(
                f"Generated metadata validation failed at '{error_path}': {e.message}\n"
                f"Generated metadata: {json.dumps(metadata, ensure_ascii=False, indent=2)}"
            ) from e
