"""Unit tests for PromptBuilder."""
from src.services.prompt_builder import PromptBuilder
from src.core.schema import FileInfo


def test_build_basic_prompt():
    """Test building a basic prompt with simple schema."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="test-file.txt",
        content="This is a test file content."
    )
    
    schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the document"
            },
            "author": {
                "type": "string",
                "description": "Author name"
            }
        },
        "required": ["title"]
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Check prompt contains key information
    assert "test-file.txt" in prompt
    assert "This is a test file content." in prompt
    assert "title" in prompt
    assert "author" in prompt
    assert "[Required]" in prompt
    assert "Title of the document" in prompt
    assert "Author name" in prompt


def test_build_prompt_with_required_fields():
    """Test that required fields are marked correctly."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="document.md",
        content="Content here"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "required_field": {"type": "string"},
            "optional_field": {"type": "string"}
        },
        "required": ["required_field"]
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Required field should have [Required] marker
    assert "required_field" in prompt
    assert "[Required]" in prompt


def test_build_prompt_with_enum():
    """Test prompt generation with enum values."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="document.txt",
        content="Content"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Document category",
                "enum": ["technical", "business", "personal"]
            }
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Enum options should be listed
    assert "Options:" in prompt
    assert "technical" in prompt
    assert "business" in prompt
    assert "personal" in prompt


def test_build_prompt_with_const():
    """Test prompt generation with const value."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="file.txt",
        content="Content"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "const": "1.0"
            }
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Const value should be shown
    assert "Fixed value:" in prompt
    assert "1.0" in prompt


def test_build_prompt_with_array():
    """Test prompt generation with array fields."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="file.txt",
        content="Content"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "description": "Document tags",
                "items": {
                    "type": "string"
                },
                "minItems": 1,
                "maxItems": 5
            }
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Array info should be present
    assert "tags" in prompt
    assert "array" in prompt.lower()
    assert "Array items: string" in prompt
    assert "minimum 1 items" in prompt
    assert "maximum 5 items" in prompt


def test_truncate_long_content():
    """Test that long content is truncated."""
    # Create content longer than 3000 characters
    long_content = "A" * 4000
    
    file_info = FileInfo(
        bucket="test-bucket",
        key="large-file.txt",
        content=long_content
    )
    
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"}
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Check that content is truncated
    assert "(truncated)" in prompt
    # Prompt shouldn't contain the full 4000 characters
    assert len(prompt) < len(long_content) + 1000


def test_build_prompt_with_multiple_field_types():
    """Test prompt with various field types."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="complex-doc.md",
        content="Complex document content"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Document title"
            },
            "priority": {
                "type": "integer",
                "description": "Priority level"
            },
            "is_published": {
                "type": "boolean",
                "description": "Publication status"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["title", "is_published"]
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # All fields should be present
    assert "title" in prompt
    assert "priority" in prompt
    assert "is_published" in prompt
    assert "tags" in prompt
    
    # Types should be shown
    assert "(string)" in prompt
    assert "(integer)" in prompt
    assert "(boolean)" in prompt
    assert "(array)" in prompt


def test_build_prompt_file_name_extraction():
    """Test that file name is correctly extracted."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="path/to/nested/document.pdf",
        content="Content"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # File name should be extracted correctly
    assert "document.pdf" in prompt
    assert "path/to/nested/document.pdf" in prompt


def test_build_prompt_with_nested_schema():
    """Test prompt generation with nested object schema."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="file.txt",
        content="Content"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "metadata": {
                "type": "object",
                "description": "Nested metadata"
            }
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Nested object should be mentioned
    assert "metadata" in prompt
    assert "(object)" in prompt


def test_build_prompt_with_no_description():
    """Test prompt generation when fields have no description."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="file.txt",
        content="Content"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "field1": {
                "type": "string"
            },
            "field2": {
                "type": "integer"
            }
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Fields should still be present even without descriptions
    assert "field1" in prompt
    assert "field2" in prompt


def test_build_prompt_output_format_instructions():
    """Test that prompt includes output format instructions."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="file.txt",
        content="Content"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"}
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Should contain format instructions
    assert "JSON format" in prompt
    assert "Generation Rules" in prompt
    assert "Output Format" in prompt


def test_build_prompt_with_unicode_content():
    """Test prompt generation with unicode content."""
    file_info = FileInfo(
        bucket="test-bucket",
        key="日本語ファイル.txt",
        content="これは日本語のコンテンツです。\n漢字、ひらがな、カタカナ。"
    )
    
    schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "ドキュメントのタイトル"
            }
        }
    }
    
    prompt = PromptBuilder.build_metadata_prompt(file_info, schema)
    
    # Unicode content should be preserved
    assert "日本語ファイル.txt" in prompt
    assert "これは日本語のコンテンツです" in prompt
    assert "ドキュメントのタイトル" in prompt
