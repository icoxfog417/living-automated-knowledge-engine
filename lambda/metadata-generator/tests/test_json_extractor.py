"""Unit tests for JsonExtractor."""
import pytest

from src.services.json_extractor import JsonExtractor


def test_extract_simple_json():
    """Test extracting simple JSON from text."""
    text = '{"name": "test", "value": 123}'
    result = JsonExtractor.extract_json(text)
    
    assert result == {"name": "test", "value": 123}


def test_extract_json_with_whitespace():
    """Test extracting JSON with leading/trailing whitespace."""
    text = '  \n  {"name": "test", "value": 123}  \n  '
    result = JsonExtractor.extract_json(text)
    
    assert result == {"name": "test", "value": 123}


def test_extract_json_from_markdown_code_block():
    """Test extracting JSON from markdown code block."""
    text = """Here's the result:
```json
{
  "name": "test",
  "value": 123
}
```
"""
    result = JsonExtractor.extract_json(text)
    
    assert result == {"name": "test", "value": 123}


def test_extract_json_from_markdown_code_block_no_language():
    """Test extracting JSON from markdown code block without language specifier."""
    text = """Here's the result:
```
{
  "name": "test",
  "value": 123
}
```
"""
    result = JsonExtractor.extract_json(text)
    
    assert result == {"name": "test", "value": 123}


def test_extract_json_from_mixed_text():
    """Test extracting JSON from text with surrounding content."""
    text = """
    Some text before
    
    {"name": "test", "value": 123}
    
    Some text after
    """
    result = JsonExtractor.extract_json(text)
    
    assert result == {"name": "test", "value": 123}


def test_extract_nested_json():
    """Test extracting nested JSON objects."""
    text = '{"outer": {"inner": {"name": "test", "value": 123}}}'
    result = JsonExtractor.extract_json(text)
    
    assert result == {"outer": {"inner": {"name": "test", "value": 123}}}


def test_extract_json_with_arrays():
    """Test extracting JSON with arrays."""
    text = '{"items": [1, 2, 3], "tags": ["a", "b", "c"]}'
    result = JsonExtractor.extract_json(text)
    
    assert result == {"items": [1, 2, 3], "tags": ["a", "b", "c"]}


def test_extract_longest_json_when_multiple():
    """Test extracting the longest JSON when multiple JSON objects exist."""
    text = """
    {"short": "json"}
    
    Some text
    
    {"longer": "json", "with": "more", "fields": true, "nested": {"data": 123}}
    
    More text
    """
    result = JsonExtractor.extract_json(text)
    
    # Should extract the longer JSON
    assert "longer" in result
    assert "nested" in result
    assert result["nested"]["data"] == 123


def test_extract_json_with_unicode():
    """Test extracting JSON with unicode characters."""
    text = '{"message": "こんにちは", "emoji": "🎉"}'
    result = JsonExtractor.extract_json(text)
    
    assert result == {"message": "こんにちは", "emoji": "🎉"}


def test_no_json_raises_error():
    """Test that ValueError is raised when no JSON is found."""
    text = "This is just plain text without any JSON"
    
    with pytest.raises(ValueError) as exc_info:
        JsonExtractor.extract_json(text)
    
    assert "No valid JSON found" in str(exc_info.value)


def test_invalid_json_raises_error():
    """Test that ValueError is raised when JSON is malformed."""
    text = '{"invalid": json}'
    
    with pytest.raises(ValueError) as exc_info:
        JsonExtractor.extract_json(text)
    
    assert "No valid JSON found" in str(exc_info.value)


def test_empty_string_raises_error():
    """Test that ValueError is raised for empty string."""
    with pytest.raises(ValueError) as exc_info:
        JsonExtractor.extract_json("")
    
    assert "No valid JSON found" in str(exc_info.value)
