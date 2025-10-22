"""Example usage of metadata collector."""

import json
import logging
from datetime import datetime, timedelta

from src.collector import CollectionParams, MetadataCollector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():
    """Run example metadata collection."""
    # Configure parameters
    params = CollectionParams(
        bucket_name="your-bucket-name",  # Replace with your S3 bucket
        start_date=datetime.now() - timedelta(days=7),  # Last 7 days
        end_date=datetime.now(),
        prefix="reports/",  # Optional: filter by prefix
        metadata_filters={
            "department": ["Sales", "Engineering"],
            "document_type": ["report", "proposal"],
        },
        max_results=100,  # Optional: limit results
        parallel_downloads=20,  # Parallel download threads
    )

    logger.info("Starting metadata collection...")
    logger.info(f"Bucket: {params.bucket_name}")
    logger.info(f"Date range: {params.start_date} to {params.end_date}")

    # Collect metadata
    collector = MetadataCollector()
    result = collector.collect(params)

    # Display results
    logger.info(f"\nCollection complete!")
    logger.info(f"Scanned: {result.total_scanned} files")
    logger.info(f"Collected: {result.total_collected} files")
    logger.info(f"Execution time: {result.execution_time_seconds:.2f}s")
    logger.info(f"Data transfer: {result.data_transfer_bytes / 1024:.2f} KB")

    # Get aggregation
    aggregation = result.aggregate()

    # Display schema
    logger.info("\n=== Discovered Schema ===")
    for key, info in aggregation["schema"].items():
        logger.info(f"{key}:")
        logger.info(f"  - Occurrence rate: {info['occurrence_rate']}%")
        logger.info(f"  - Types: {info['types']}")
        logger.info(f"  - Sample values: {info['sample_values']}")

    # Display aggregations
    logger.info("\n=== Aggregations ===")
    for key, stats in aggregation["aggregations"].items():
        logger.info(f"{key}: {stats}")

    # Display file types
    logger.info("\n=== By File Type ===")
    for ext, count in aggregation["by_file_type"].items():
        logger.info(f"{ext}: {count} files")

    # Save to file
    output_file = "metadata_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result.to_json(), f, ensure_ascii=False, indent=2)
    logger.info(f"\nFull results saved to: {output_file}")

    # Display sample entries
    logger.info("\n=== Sample Entries ===")
    for i, entry in enumerate(result.entries[:3], 1):
        logger.info(f"\n{i}. {entry.original_file_key}")
        logger.info(f"   Extension: {entry.file_extension}")
        logger.info(f"   Modified: {entry.last_modified}")
        logger.info(f"   Metadata: {json.dumps(entry.metadata, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
