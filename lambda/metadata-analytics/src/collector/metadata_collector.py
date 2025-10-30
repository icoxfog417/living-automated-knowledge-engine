"""Metadata collector implementation."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from ..utils.s3_operations import S3Operations
from .models import CollectionParams, CollectionResult, MetadataEntry

logger = logging.getLogger(__name__)


class MetadataCollector:
    """Collector for metadata files from S3."""

    def __init__(self, s3_operations: Optional[S3Operations] = None):
        """Initialize metadata collector.

        Args:
            s3_operations: S3 operations instance (injectable for testing)
        """
        self.s3_ops = s3_operations or S3Operations()

    def collect(self, params: CollectionParams) -> CollectionResult:
        """Collect metadata files from S3.

        Args:
            params: Collection parameters

        Returns:
            Collection result with entries and statistics
        """
        start_time = time.time()

        logger.info(f"Starting metadata collection from {params.bucket_name}")
        logger.info(f"Date range: {params.start_date} to {params.end_date}")

        # Step 1: List .metadata.json files from S3
        metadata_files = list(
            self.s3_ops.list_metadata_files(
                bucket=params.bucket_name,
                prefix=params.prefix,
                start_date=params.start_date,
                end_date=params.end_date,
            )
        )

        total_scanned = len(metadata_files)
        logger.info(f"Found {total_scanned} metadata files")

        # Apply max_results limit
        if params.max_results and len(metadata_files) > params.max_results:
            metadata_files = metadata_files[: params.max_results]
            logger.info(f"Limited to {params.max_results} files")

        # Step 2: Download and parse in parallel
        entries = self._download_and_parse_parallel(params.bucket_name, metadata_files, params)

        # Step 3: Apply metadata filters
        filtered_entries = self._apply_filters(entries, params)

        execution_time = time.time() - start_time
        total_bytes = sum(e.file_size for e in filtered_entries)

        logger.info(f"Collected {len(filtered_entries)} entries in {execution_time:.2f}s")

        return CollectionResult(
            entries=filtered_entries,
            total_scanned=total_scanned,
            total_collected=len(filtered_entries),
            execution_time_seconds=execution_time,
            data_transfer_bytes=total_bytes,
        )

    def _download_and_parse_parallel(
        self,
        bucket: str,
        files: List[dict],
        params: CollectionParams,
    ) -> List[MetadataEntry]:
        """Download and parse metadata files in parallel.

        Args:
            bucket: S3 bucket name
            files: List of file info dicts
            params: Collection parameters

        Returns:
            List of metadata entries
        """
        entries = []

        with ThreadPoolExecutor(max_workers=params.parallel_downloads) as executor:
            # Submit download tasks
            future_to_file = {
                executor.submit(self._download_and_parse_single, bucket, file_info): file_info
                for file_info in files
            }

            # Collect results
            for future in as_completed(future_to_file):
                entry = future.result()
                if entry:
                    entries.append(entry)

        return entries

    def _download_and_parse_single(self, bucket: str, file_info: dict) -> Optional[MetadataEntry]:
        """Download and parse a single metadata file.

        Args:
            bucket: S3 bucket name
            file_info: File information dict

        Returns:
            MetadataEntry or None if error occurs
        """
        key = file_info["Key"]

        # Download metadata
        metadata = self.s3_ops.download_metadata_content(bucket, key)
        if not metadata:
            return None

        # Construct MetadataEntry
        entry = MetadataEntry.from_s3_metadata(
            bucket=bucket,
            metadata_file_key=key,
            file_info=file_info,
            metadata_content=metadata,
        )

        return entry

    def _apply_filters(
        self, entries: List[MetadataEntry], params: CollectionParams
    ) -> List[MetadataEntry]:
        """Apply dynamic metadata filters.

        Args:
            entries: List of metadata entries
            params: Collection parameters with filters

        Returns:
            Filtered list of entries
        """
        if not params.metadata_filters:
            return entries

        filtered = []

        for entry in entries:
            # Check all filter conditions
            matches_all = True

            for key, allowed_values in params.metadata_filters.items():
                entry_value = entry.metadata.get(key)

                # None values don't match
                if entry_value is None:
                    matches_all = False
                    break

                # Handle list values
                if isinstance(entry_value, list):
                    if not any(v in allowed_values for v in entry_value):
                        matches_all = False
                        break
                else:
                    # Single value
                    if entry_value not in allowed_values:
                        matches_all = False
                        break

            if matches_all:
                filtered.append(entry)

        logger.info(
            f"Filtered {len(entries)} entries to {len(filtered)} "
            f"based on {len(params.metadata_filters)} filters"
        )

        return filtered
