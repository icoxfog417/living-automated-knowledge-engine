"""Build prompts for metadata generation."""

from ..core.schema import FileInfo


class PromptBuilder:
    """Build prompts for metadata generation."""

    @staticmethod
    def calculate_max_content_chars(
        input_context_window: int,
        prompt_overhead_tokens: int = 3000,
        safety_margin: float = 0.8,
        chars_per_token: int = 3,
    ) -> int:
        """
        Calculate maximum content characters based on input context window.

        Args:
            input_context_window: Model's input context window size in tokens
            prompt_overhead_tokens: Estimated tokens for prompt structure (schema, instructions, etc.)
            safety_margin: Safety factor (0.0-1.0) to use of available tokens
            chars_per_token: Character to token conversion ratio

        Returns:
            Maximum number of characters to include from file content
        """
        # ファイル内容に使用可能なトークン数
        available_tokens = input_context_window - prompt_overhead_tokens

        # 安全マージンを適用
        safe_available_tokens = int(available_tokens * safety_margin)

        # トークン数を文字数に変換
        max_chars = safe_available_tokens * chars_per_token

        # 最小値の保証（3000文字）
        return max(max_chars, 3000)

    @staticmethod
    def build_metadata_prompt(file_info: FileInfo, schema: dict, max_content_chars: int = 3000) -> str:
        """
        Build a prompt for Bedrock based on file info and JSON Schema.

        Args:
            file_info: File information
            schema: JSON Schema for metadata
            max_content_chars: Maximum characters to include from file content

        Returns:
            Formatted prompt string
        """
        # Extract schema information for prompt
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        # Build field descriptions
        field_descriptions = []
        for field_name, field_schema in properties.items():
            desc = field_schema.get("description", "")
            field_type = field_schema.get("type", "string")

            field_info = f"- {field_name} ({field_type})"
            if field_name in required_fields:
                field_info += " [Required]"
            if desc:
                field_info += f": {desc}"

            # Add enum values if present
            if "enum" in field_schema:
                enum_values = ", ".join(str(v) for v in field_schema["enum"])
                field_info += f"\n  Options: {enum_values}"

            # Add const value if present
            if "const" in field_schema:
                field_info += f"\n  Fixed value: {field_schema['const']}"

            # Add array item info if present
            if field_type == "array" and "items" in field_schema:
                items_type = field_schema["items"].get("type", "string")
                field_info += f"\n  Array items: {items_type}"
                if "minItems" in field_schema:
                    field_info += f", minimum {field_schema['minItems']} items"
                if "maxItems" in field_schema:
                    field_info += f", maximum {field_schema['maxItems']} items"

            field_descriptions.append(field_info)

        # Limit content length for prompt
        content_preview = file_info.content[:max_content_chars]
        if len(file_info.content) > max_content_chars:
            content_preview += "\n... (truncated)"

        return f"""Analyze the following file and generate appropriate metadata based on its content, filename, and path.

## File Information
- File name: {file_info.file_name}
- File path: {file_info.key}

## File Content
{content_preview}

## Metadata Field Guidelines
{chr(10).join(field_descriptions)}

## Analysis Instructions
1. Analyze the file content to understand its purpose and context
2. Use the file path and name as additional context clues
3. For Japanese content, provide metadata values in English
4. If specific values cannot be determined from content, make reasonable inferences from the filename or path
5. Ensure all required fields are populated with appropriate values

Generate metadata that accurately reflects the file's content and purpose."""
