"""Build prompts for metadata generation."""

from ..core.schema import FileInfo


class PromptBuilder:
    """Build prompts for metadata generation."""

    @staticmethod
    def build_metadata_prompt(file_info: FileInfo, schema: dict) -> str:
        """
        Build a prompt for Bedrock based on file info and JSON Schema.

        Args:
            file_info: File information
            schema: JSON Schema for metadata

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
        content_preview = file_info.content[:3000]
        if len(file_info.content) > 3000:
            content_preview += "\n... (truncated)"

        return f"""Please generate metadata for the following file according to the \
specified JSON Schema.

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
