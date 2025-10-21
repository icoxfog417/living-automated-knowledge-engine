"""Unit tests for EventParser."""
from src.services.event_parser import EventParser


def test_parse_eventbridge_format():
    """Test parsing EventBridge S3 event format."""
    event = {
        "version": "0",
        "id": "test-event-id",
        "detail-type": "Object Created",
        "source": "aws.s3",
        "detail": {
            "bucket": {
                "name": "test-bucket"
            },
            "object": {
                "key": "test-file.txt"
            }
        }
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is not None
    assert result["bucket"] == "test-bucket"
    assert result["key"] == "test-file.txt"


def test_parse_eventbridge_format_nested_path():
    """Test parsing EventBridge event with nested file path."""
    event = {
        "detail": {
            "bucket": {
                "name": "my-data-bucket"
            },
            "object": {
                "key": "documents/2024/report.pdf"
            }
        }
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is not None
    assert result["bucket"] == "my-data-bucket"
    assert result["key"] == "documents/2024/report.pdf"


def test_parse_direct_invocation_format():
    """Test parsing direct invocation format (for testing)."""
    event = {
        "bucket": "test-bucket",
        "key": "test-file.txt"
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is not None
    assert result["bucket"] == "test-bucket"
    assert result["key"] == "test-file.txt"


def test_parse_direct_invocation_with_nested_path():
    """Test parsing direct invocation with nested file path."""
    event = {
        "bucket": "my-bucket",
        "key": "path/to/nested/file.csv"
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is not None
    assert result["bucket"] == "my-bucket"
    assert result["key"] == "path/to/nested/file.csv"


def test_missing_detail_returns_none():
    """Test that missing detail field returns None."""
    event = {
        "version": "0",
        "id": "test-event-id"
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is None


def test_missing_bucket_in_detail_returns_none():
    """Test that missing bucket in detail returns None."""
    event = {
        "detail": {
            "object": {
                "key": "test-file.txt"
            }
        }
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is None


def test_missing_bucket_name_returns_none():
    """Test that missing bucket name returns None."""
    event = {
        "detail": {
            "bucket": {},
            "object": {
                "key": "test-file.txt"
            }
        }
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is None


def test_missing_object_in_detail_returns_none():
    """Test that missing object in detail returns None."""
    event = {
        "detail": {
            "bucket": {
                "name": "test-bucket"
            }
        }
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is None


def test_missing_object_key_returns_none():
    """Test that missing object key returns None."""
    event = {
        "detail": {
            "bucket": {
                "name": "test-bucket"
            },
            "object": {}
        }
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is None


def test_missing_bucket_in_direct_format_returns_none():
    """Test that missing bucket in direct format returns None."""
    event = {
        "key": "test-file.txt"
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is None


def test_missing_key_in_direct_format_returns_none():
    """Test that missing key in direct format returns None."""
    event = {
        "bucket": "test-bucket"
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is None


def test_empty_event_returns_none():
    """Test that empty event returns None."""
    event = {}
    
    result = EventParser.extract_file_info(event)
    
    assert result is None


def test_eventbridge_takes_precedence_over_direct():
    """Test that EventBridge format takes precedence when both formats present."""
    event = {
        "bucket": "direct-bucket",
        "key": "direct-key.txt",
        "detail": {
            "bucket": {
                "name": "eventbridge-bucket"
            },
            "object": {
                "key": "eventbridge-key.txt"
            }
        }
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is not None
    assert result["bucket"] == "eventbridge-bucket"
    assert result["key"] == "eventbridge-key.txt"


def test_parse_with_special_characters_in_key():
    """Test parsing file keys with special characters."""
    event = {
        "bucket": "test-bucket",
        "key": "files/test file with spaces.txt"
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is not None
    assert result["key"] == "files/test file with spaces.txt"


def test_parse_with_unicode_in_key():
    """Test parsing file keys with unicode characters."""
    event = {
        "bucket": "test-bucket",
        "key": "documents/レポート.txt"
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is not None
    assert result["key"] == "documents/レポート.txt"


def test_parse_exception_returns_none():
    """Test that exceptions during parsing return None."""
    # Malformed event that might cause exceptions
    event = {
        "detail": None
    }
    
    result = EventParser.extract_file_info(event)
    
    assert result is None
