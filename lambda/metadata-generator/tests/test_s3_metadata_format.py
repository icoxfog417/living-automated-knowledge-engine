"""Test to verify the metadata output format."""

import json
from unittest.mock import MagicMock

from src.clients.s3_operations import S3Operations
from src.core.schema import GeneratedMetadata


def test_metadata_wrapped_with_metadata_attributes():
    """Test that metadata is correctly wrapped with metadataAttributes field."""

    # Mock S3 client
    mock_s3_client = MagicMock()
    s3_ops = S3Operations(s3_client=mock_s3_client)

    # Create test metadata
    test_metadata = GeneratedMetadata(
        metadata={
            "id": 123,
            "genres": "Action",
            "year": 2024,
            "publisher": "Test Publisher",
            "score": 85,
        },
        file_key="test/movie.txt",
    )

    # Call write_metadata
    s3_ops.write_metadata("test-bucket", test_metadata)

    # Verify put_object was called
    assert mock_s3_client.put_object.called, "put_object should be called"

    # Get the actual call arguments
    call_args = mock_s3_client.put_object.call_args
    body_bytes = call_args.kwargs["Body"]

    # Parse the JSON that would be written to S3
    written_json = json.loads(body_bytes.decode("utf-8"))

    # Verify the structure
    assert "metadataAttributes" in written_json, "Should have metadataAttributes field"
    assert written_json["metadataAttributes"]["id"] == 123, "Should contain correct id"
    assert written_json["metadataAttributes"]["genres"] == "Action", "Should contain correct genres"
    assert written_json["metadataAttributes"]["year"] == 2024, "Should contain correct year"
    assert written_json["metadataAttributes"]["publisher"] == "Test Publisher", (
        "Should contain correct publisher"
    )
    assert written_json["metadataAttributes"]["score"] == 85, "Should contain correct score"

    # Verify that metadata is not at the top level
    assert "id" not in written_json, "id should not be at top level"
    assert "genres" not in written_json, "genres should not be at top level"

    print("\n[Format Test] Generated JSON structure:")
    print(json.dumps(written_json, ensure_ascii=False, indent=2))
