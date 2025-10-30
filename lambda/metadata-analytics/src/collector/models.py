"""Data models for metadata collection with fully dynamic schema support."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MetadataEntry:
    """Collected metadata entry with fully dynamic schema."""

    # S3 metadata (fixed fields)
    bucket: str
    original_file_key: str
    metadata_file_key: str
    last_modified: datetime
    file_size: int

    # Metadata content (completely dynamic)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_s3_metadata(
        cls,
        bucket: str,
        metadata_file_key: str,
        file_info: dict,
        metadata_content: dict,
    ) -> "MetadataEntry":
        """Construct MetadataEntry from S3 metadata file.

        Args:
            bucket: S3 bucket name
            metadata_file_key: Key of the .metadata.json file
            file_info: File information from S3 (Key, LastModified, Size)
            metadata_content: Parsed metadata JSON content

        Returns:
            MetadataEntry instance
        """
        original_key = metadata_file_key.replace(".metadata.json", "")

        return cls(
            bucket=bucket,
            original_file_key=original_key,
            metadata_file_key=metadata_file_key,
            last_modified=file_info["LastModified"],
            file_size=file_info["Size"],
            metadata=metadata_content,
        )

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key.

        Args:
            key: Metadata key
            default: Default value if key doesn't exist

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    @property
    def file_extension(self) -> str:
        """Get file extension."""
        if "." not in self.original_file_key:
            return ""
        return self.original_file_key.split(".")[-1].lower()

    def to_dict(self) -> dict:
        """Convert to dictionary format.

        Returns:
            Dictionary representation
        """
        return {
            "s3_info": {
                "bucket": self.bucket,
                "original_file_key": self.original_file_key,
                "metadata_file_key": self.metadata_file_key,
                "last_modified": self.last_modified.isoformat(),
                "file_size": self.file_size,
                "file_extension": self.file_extension,
            },
            "metadata": self.metadata,
        }


@dataclass
class CollectionParams:
    """Parameters for metadata collection."""

    bucket_name: str
    start_date: datetime
    end_date: datetime
    prefix: Optional[str] = None

    # Metadata filters (completely dynamic)
    # Example: {"department": ["Sales"], "document_type": ["report", "proposal"]}
    metadata_filters: Optional[Dict[str, List[Any]]] = None

    max_results: Optional[int] = None
    parallel_downloads: int = 10


@dataclass
class CollectionResult:
    """Collection result with fully dynamic schema support."""

    entries: List[MetadataEntry]
    total_scanned: int
    total_collected: int
    execution_time_seconds: float
    data_transfer_bytes: int

    def discover_schema(self) -> Dict[str, Dict[str, Any]]:
        """Automatically discover schema from collected metadata.

        Returns:
            Schema information for each key (type, occurrence rate, sample values)
        """
        if not self.entries:
            return {}

        schema = {}
        total_entries = len(self.entries)

        # Collect all keys
        all_keys = set()
        for entry in self.entries:
            all_keys.update(entry.metadata.keys())

        # Analyze each key
        for key in all_keys:
            values = []
            null_count = 0

            for entry in self.entries:
                value = entry.metadata.get(key)
                if value is None:
                    null_count += 1
                else:
                    values.append(value)

            if not values:
                continue

            # Determine types
            value_types = set(type(v).__name__ for v in values)

            # Check if numeric
            is_numeric = all(isinstance(v, (int, float)) for v in values)

            schema[key] = {
                "occurrence_rate": round((len(values) / total_entries) * 100, 1),
                "types": list(value_types),
                "is_numeric": is_numeric,
                "non_null_count": len(values),
                "null_count": null_count,
                "sample_values": list(set(str(v) for v in values[:5])),
            }

        return schema

    def aggregate(self) -> Dict[str, Any]:
        """Aggregate metadata with dynamic key support.

        Returns:
            Fully dynamic aggregation results
        """
        if not self.entries:
            return {
                "total_collected": 0,
                "schema": {},
                "aggregations": {},
            }

        schema = self.discover_schema()
        aggregations = {}

        # Aggregate each key
        for key, key_info in schema.items():
            if key_info["is_numeric"]:
                # Numeric fields: calculate statistics
                aggregations[key] = self._aggregate_numeric(key)
            else:
                # Categorical fields: count frequencies
                aggregations[key] = self._aggregate_categorical(key)

        return {
            "total_collected": self.total_collected,
            "total_scanned": self.total_scanned,
            "execution_time_seconds": self.execution_time_seconds,
            "data_transfer_mb": round(self.data_transfer_bytes / 1024 / 1024, 2),
            "schema": schema,
            "aggregations": aggregations,
            "by_file_type": self._aggregate_by_file_type(),
        }

    def _aggregate_numeric(self, key: str) -> Dict[str, float]:
        """Aggregate numeric field.

        Args:
            key: Metadata key

        Returns:
            Statistical values (count, min, max, avg, sum)
        """
        values = [
            entry.metadata.get(key)
            for entry in self.entries
            if entry.metadata.get(key) is not None
            and isinstance(entry.metadata.get(key), (int, float))
        ]

        if not values:
            return {"count": 0}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": round(sum(values) / len(values), 2),
            "sum": sum(values),
        }

    def _aggregate_categorical(self, key: str) -> Dict[str, int]:
        """Aggregate categorical field.

        Args:
            key: Metadata key

        Returns:
            Frequency counts (top 10 + others)
        """
        counts = defaultdict(int)

        for entry in self.entries:
            value = entry.metadata.get(key)
            if value is not None:
                # Handle list values
                if isinstance(value, list):
                    for item in value:
                        counts[str(item)] += 1
                else:
                    counts[str(value)] += 1

        # Top 10 + others
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)

        if len(sorted_counts) <= 10:
            return dict(sorted_counts)
        else:
            top_10 = dict(sorted_counts[:10])
            others_count = sum(count for _, count in sorted_counts[10:])
            top_10["_others"] = others_count
            return top_10

    def _aggregate_by_file_type(self) -> Dict[str, int]:
        """Aggregate by file type.

        Returns:
            Count by file extension
        """
        counts = defaultdict(int)
        for entry in self.entries:
            counts[entry.file_extension] += 1
        return dict(counts)

    def to_json(self) -> dict:
        """Convert to JSON format.

        Returns:
            JSON-serializable dictionary
        """
        return {
            "summary": self.aggregate(),
            "entries": [entry.to_dict() for entry in self.entries],
        }
