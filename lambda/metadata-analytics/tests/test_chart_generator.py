"""Tests for chart generator."""

import os
from unittest.mock import MagicMock, patch

import pytest

from src.utils.chart_generator import ChartGenerator, ChartResult, TableData


class TestChartGenerator:
    """Test chart generator functionality."""

    @pytest.fixture
    def chart_generator(self):
        """Create chart generator instance."""
        return ChartGenerator()

    @pytest.fixture
    def sample_aggregation(self):
        """Create sample aggregation data."""
        return {
            "total_collected": 100,
            "total_scanned": 120,
            "execution_time_seconds": 5.5,
            "data_transfer_mb": 10.5,
            "schema": {
                "department": {
                    "occurrence_rate": 95.0,
                    "types": ["str"],
                    "is_numeric": False,
                    "non_null_count": 95,
                    "null_count": 5,
                    "sample_values": ["Engineering", "Sales", "Marketing"],
                },
                "document_type": {
                    "occurrence_rate": 100.0,
                    "types": ["str"],
                    "is_numeric": False,
                    "non_null_count": 100,
                    "null_count": 0,
                    "sample_values": ["report", "proposal", "memo"],
                },
                "page_count": {
                    "occurrence_rate": 80.0,
                    "types": ["int"],
                    "is_numeric": True,
                    "non_null_count": 80,
                    "null_count": 20,
                    "sample_values": ["5", "10", "15"],
                },
            },
            "aggregations": {
                "department": {
                    "Engineering": 45,
                    "Sales": 30,
                    "Marketing": 20,
                    "_others": 5,
                },
                "document_type": {"report": 60, "proposal": 25, "memo": 15},
                "page_count": {
                    "count": 80,
                    "min": 1,
                    "max": 50,
                    "avg": 12.5,
                    "sum": 1000,
                },
            },
            "by_file_type": {"pdf": 70, "docx": 25, "txt": 5},
        }

    def test_generate_charts_returns_tuple(self, chart_generator, sample_aggregation):
        """Test that generate_charts returns tuple of charts and tables."""
        with patch("matplotlib.pyplot.savefig"), patch("matplotlib.pyplot.close"):
            charts, tables = chart_generator.generate_charts(sample_aggregation)
            assert isinstance(charts, list)
            assert isinstance(tables, list)
            assert len(charts) > 0 or len(tables) > 0

    def test_generate_file_type_chart(self, chart_generator, sample_aggregation):
        """Test file type chart generation."""
        with patch("matplotlib.pyplot.savefig"), patch("matplotlib.pyplot.close"):
            charts, tables = chart_generator.generate_charts(sample_aggregation)
            file_type_charts = [c for c in charts if c.metadata_key == "file_type"]
            assert len(file_type_charts) == 1
            chart = file_type_charts[0]
            assert chart.chart_type == "bar"
            assert chart.title == "File Type Distribution"

    def test_generate_categorical_charts(self, chart_generator, sample_aggregation):
        """Test categorical field chart generation."""
        with patch("matplotlib.pyplot.savefig"), patch("matplotlib.pyplot.close"):
            charts, tables = chart_generator.generate_charts(sample_aggregation)

            # Should have charts or tables for categorical fields
            all_keys = [c.metadata_key for c in charts] + [t.metadata_key for t in tables]
            assert "department" in all_keys
            assert "document_type" in all_keys

    def test_chart_result_has_required_fields(self, chart_generator, sample_aggregation):
        """Test that ChartResult has all required fields."""
        with patch("matplotlib.pyplot.savefig"), patch("matplotlib.pyplot.close"):
            charts, tables = chart_generator.generate_charts(sample_aggregation)
            for chart in charts:
                assert hasattr(chart, "chart_type")
                assert hasattr(chart, "title")
                assert hasattr(chart, "file_path")
                assert hasattr(chart, "metadata_key")
                assert hasattr(chart, "description")
                assert chart.chart_type == "bar"

    def test_table_data_has_required_fields(self, chart_generator, sample_aggregation):
        """Test that TableData has all required fields."""
        with patch("matplotlib.pyplot.savefig"), patch("matplotlib.pyplot.close"):
            charts, tables = chart_generator.generate_charts(sample_aggregation)
            for table in tables:
                assert hasattr(table, "metadata_key")
                assert hasattr(table, "title")
                assert hasattr(table, "data")
                assert hasattr(table, "reason")
                assert isinstance(table.data, dict)

    def test_handle_empty_aggregation(self, chart_generator):
        """Test handling of empty aggregation data."""
        empty_aggregation = {
            "schema": {},
            "aggregations": {},
            "by_file_type": {},
        }
        charts, tables = chart_generator.generate_charts(empty_aggregation)
        assert isinstance(charts, list)
        assert isinstance(tables, list)
        assert len(charts) == 0
        assert len(tables) == 0

    def test_long_text_creates_table(self, chart_generator):
        """Test that long text fields create tables instead of charts."""
        long_text_data = {
            "schema": {
                "long_field": {
                    "occurrence_rate": 100.0,
                    "types": ["str"],
                    "is_numeric": False,
                    "non_null_count": 100,
                    "null_count": 0,
                    "sample_values": ["a" * 100, "b" * 100],
                }
            },
            "aggregations": {
                "long_field": {
                    "a" * 100: 50,
                    "b" * 100: 50,
                }
            },
            "by_file_type": {},
        }

        with patch("matplotlib.pyplot.savefig"), patch("matplotlib.pyplot.close"):
            charts, tables = chart_generator.generate_charts(long_text_data)
            # Long text should create table
            long_field_tables = [t for t in tables if t.metadata_key == "long_field"]
            assert len(long_field_tables) == 1
            assert "Long text" in long_field_tables[0].reason

    def test_many_categories_creates_table(self, chart_generator):
        """Test that fields with many categories create tables."""
        many_categories = {
            "schema": {
                "many_cats": {
                    "occurrence_rate": 100.0,
                    "types": ["str"],
                    "is_numeric": False,
                    "non_null_count": 100,
                    "null_count": 0,
                    "sample_values": ["cat1", "cat2", "cat3"],
                }
            },
            "aggregations": {
                "many_cats": {f"category_{i}": 5 for i in range(20)}
            },
            "by_file_type": {},
        }

        with patch("matplotlib.pyplot.savefig"), patch("matplotlib.pyplot.close"):
            charts, tables = chart_generator.generate_charts(many_categories)
            # Many categories should create table
            many_cat_tables = [t for t in tables if t.metadata_key == "many_cats"]
            assert len(many_cat_tables) == 1
            assert "Many categories" in many_cat_tables[0].reason

    def test_numeric_fields_skipped(self, chart_generator, sample_aggregation):
        """Test that numeric fields are skipped (no raw data for histogram)."""
        with patch("matplotlib.pyplot.savefig"), patch("matplotlib.pyplot.close"):
            charts, tables = chart_generator.generate_charts(sample_aggregation)
            # Numeric fields should be skipped entirely
            all_keys = [c.metadata_key for c in charts] + [t.metadata_key for t in tables]
            assert "page_count" not in all_keys

    def test_chart_file_paths_are_temporary(self, chart_generator, sample_aggregation):
        """Test that generated charts use temporary file paths."""
        with patch("matplotlib.pyplot.savefig") as mock_savefig, patch(
            "matplotlib.pyplot.close"
        ):
            charts, tables = chart_generator.generate_charts(sample_aggregation)
            for chart in charts:
                assert chart.file_path.endswith(".png")
                # Should be in temp directory
                assert "tmp" in chart.file_path.lower() or chart.file_path.startswith(
                    "/var/folders"
                )

    def test_error_handling_in_chart_generation(self, chart_generator):
        """Test error handling when chart generation fails."""
        malformed_data = {
            "schema": {"test": {"is_numeric": False}},
            "aggregations": {"test": None},  # This should cause an error
            "by_file_type": {},
        }

        # Should not raise exception, just return empty or partial results
        charts, tables = chart_generator.generate_charts(malformed_data)
        assert isinstance(charts, list)
        assert isinstance(tables, list)
