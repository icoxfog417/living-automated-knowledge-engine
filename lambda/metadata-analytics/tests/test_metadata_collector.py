"""Tests for metadata collector."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.collector.metadata_collector import MetadataCollector
from src.collector.models import CollectionParams, MetadataEntry
from src.utils.s3_operations import S3Operations


class TestMetadataCollector:
    """Test cases for MetadataCollector."""

    @pytest.fixture
    def sample_metadata(self):
        """Load sample metadata fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_metadata.json"
        with open(fixture_path, "r") as f:
            return json.load(f)

    @pytest.fixture
    def mock_s3_operations(self, sample_metadata):
        """Create mock S3Operations."""
        mock_s3 = Mock(spec=S3Operations)

        # Mock list_metadata_files
        now = datetime.now(timezone.utc)
        mock_s3.list_metadata_files.return_value = iter(
            [
                {
                    "Key": "reports/sales-report.pdf.metadata.json",
                    "LastModified": now,
                    "Size": 1024,
                },
                {
                    "Key": "reports/engineering-doc.md.metadata.json",
                    "LastModified": now - timedelta(hours=1),
                    "Size": 512,
                },
            ]
        )

        # Mock download_metadata_content
        mock_s3.download_metadata_content.return_value = sample_metadata

        return mock_s3

    def test_collect_basic(self, mock_s3_operations):
        """Test basic metadata collection."""
        collector = MetadataCollector(s3_operations=mock_s3_operations)

        params = CollectionParams(
            bucket_name="test-bucket",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
        )

        result = collector.collect(params)

        assert result.total_scanned == 2
        assert result.total_collected == 2
        assert len(result.entries) == 2
        assert result.execution_time_seconds > 0

    def test_collect_with_filters(self, mock_s3_operations):
        """Test collection with metadata filters."""
        collector = MetadataCollector(s3_operations=mock_s3_operations)

        params = CollectionParams(
            bucket_name="test-bucket",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
            metadata_filters={"department": ["Sales"], "document_type": ["report"]},
        )

        result = collector.collect(params)

        assert result.total_collected == 2  # Both match the filter
        for entry in result.entries:
            assert entry.metadata.get("department") == "Sales"
            assert entry.metadata.get("document_type") == "report"

    def test_collect_with_max_results(self, mock_s3_operations):
        """Test collection with max_results limit."""
        collector = MetadataCollector(s3_operations=mock_s3_operations)

        params = CollectionParams(
            bucket_name="test-bucket",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
            max_results=1,
        )

        result = collector.collect(params)

        assert result.total_scanned == 2
        assert result.total_collected == 1
        assert len(result.entries) == 1

    def test_aggregation(self, mock_s3_operations, sample_metadata):
        """Test result aggregation."""
        collector = MetadataCollector(s3_operations=mock_s3_operations)

        params = CollectionParams(
            bucket_name="test-bucket",
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc),
        )

        result = collector.collect(params)
        aggregation = result.aggregate()

        assert "schema" in aggregation
        assert "aggregations" in aggregation
        assert "by_file_type" in aggregation

        # Check schema discovery
        schema = aggregation["schema"]
        assert "department" in schema
        assert "document_type" in schema
        assert schema["department"]["occurrence_rate"] == 100.0

        # Check aggregations
        aggs = aggregation["aggregations"]
        assert "department" in aggs
        assert aggs["department"]["Sales"] == 2


class TestMetadataEntry:
    """Test cases for MetadataEntry."""

    def test_from_s3_metadata(self):
        """Test MetadataEntry construction from S3 metadata."""
        file_info = {
            "Key": "reports/test.pdf.metadata.json",
            "LastModified": datetime.now(timezone.utc),
            "Size": 1024,
        }

        metadata_content = {
            "department": "Engineering",
            "document_type": "manual",
            "author": "Bob",
        }

        entry = MetadataEntry.from_s3_metadata(
            bucket="test-bucket",
            metadata_file_key=file_info["Key"],
            file_info=file_info,
            metadata_content=metadata_content,
        )

        assert entry.bucket == "test-bucket"
        assert entry.original_file_key == "reports/test.pdf"
        assert entry.metadata_file_key == "reports/test.pdf.metadata.json"
        assert entry.file_extension == "pdf"
        assert entry.metadata == metadata_content

    def test_get_metadata(self):
        """Test metadata value retrieval."""
        entry = MetadataEntry(
            bucket="test-bucket",
            original_file_key="test.pdf",
            metadata_file_key="test.pdf.metadata.json",
            last_modified=datetime.now(timezone.utc),
            file_size=1024,
            metadata={"department": "Sales", "author": "Alice"},
        )

        assert entry.get_metadata("department") == "Sales"
        assert entry.get_metadata("author") == "Alice"
        assert entry.get_metadata("nonexistent", "default") == "default"

    def test_to_dict(self):
        """Test dictionary conversion."""
        now = datetime.now(timezone.utc)
        entry = MetadataEntry(
            bucket="test-bucket",
            original_file_key="test.pdf",
            metadata_file_key="test.pdf.metadata.json",
            last_modified=now,
            file_size=1024,
            metadata={"department": "Sales"},
        )

        result = entry.to_dict()

        assert result["s3_info"]["bucket"] == "test-bucket"
        assert result["s3_info"]["file_extension"] == "pdf"
        assert result["metadata"]["department"] == "Sales"
