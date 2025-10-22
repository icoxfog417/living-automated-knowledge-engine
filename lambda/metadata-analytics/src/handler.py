"""Lambda handler for metadata analytics."""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

from .collector.metadata_collector import MetadataCollector
from .collector.models import CollectionParams

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Lambda handler for metadata analytics.

    Triggered by CloudWatch Events (scheduled execution).
    Analyzes metadata files from the previous 24 hours.

    Args:
        event: CloudWatch Events scheduled event
        context: Lambda context

    Returns:
        Response dictionary with status and summary
    """
    try:
        logger.info("Starting metadata analytics...")
        logger.info(f"Event: {json.dumps(event)}")

        # Get bucket name from environment variable
        bucket_name = os.environ.get("BUCKET_NAME")
        if not bucket_name:
            raise ValueError("BUCKET_NAME environment variable is required")

        # Set date range: previous 24 hours
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)

        logger.info(f"Target bucket: {bucket_name}")
        logger.info(f"Analysis period: {start_date} to {end_date}")

        # Configure collection parameters
        params = CollectionParams(
            bucket_name=bucket_name,
            start_date=start_date,
            end_date=end_date,
            parallel_downloads=20,
        )

        # Collect metadata
        collector = MetadataCollector()
        result = collector.collect(params)

        logger.info("=" * 80)
        logger.info("METADATA ANALYTICS RESULTS")
        logger.info("=" * 80)
        logger.info(f"Total scanned: {result.total_scanned} files")
        logger.info(f"Total collected: {result.total_collected} files")
        logger.info(f"Execution time: {result.execution_time_seconds:.2f}s")
        logger.info(f"Data transfer: {result.data_transfer_bytes / 1024 / 1024:.2f} MB")

        # Get aggregation
        aggregation = result.aggregate()

        # Log discovered schema
        logger.info("\n" + "=" * 80)
        logger.info("DISCOVERED SCHEMA")
        logger.info("=" * 80)
        for key, info in aggregation["schema"].items():
            logger.info(f"\n{key}:")
            logger.info(f"  Occurrence rate: {info['occurrence_rate']}%")
            logger.info(f"  Types: {', '.join(info['types'])}")
            logger.info(f"  Non-null count: {info['non_null_count']}")
            logger.info(f"  Sample values: {', '.join(info['sample_values'][:3])}")

        # Log aggregations
        logger.info("\n" + "=" * 80)
        logger.info("AGGREGATIONS")
        logger.info("=" * 80)
        for key, stats in aggregation["aggregations"].items():
            logger.info(f"\n{key}:")
            if isinstance(stats, dict) and "count" in stats and "avg" in stats:
                # Numeric aggregation
                logger.info(f"  Count: {stats['count']}")
                logger.info(f"  Min: {stats['min']}")
                logger.info(f"  Max: {stats['max']}")
                logger.info(f"  Average: {stats['avg']}")
                logger.info(f"  Sum: {stats['sum']}")
            else:
                # Categorical aggregation
                for value, count in list(stats.items())[:5]:
                    logger.info(f"  {value}: {count}")
                if len(stats) > 5:
                    logger.info(f"  ... and {len(stats) - 5} more")

        # Log file types
        logger.info("\n" + "=" * 80)
        logger.info("BY FILE TYPE")
        logger.info("=" * 80)
        for ext, count in aggregation["by_file_type"].items():
            logger.info(f"{ext}: {count} files")

        logger.info("\n" + "=" * 80)
        logger.info("ANALYTICS COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Metadata analytics completed successfully",
                    "summary": {
                        "total_scanned": result.total_scanned,
                        "total_collected": result.total_collected,
                        "execution_time_seconds": result.execution_time_seconds,
                        "data_transfer_mb": round(
                            result.data_transfer_bytes / 1024 / 1024, 2
                        ),
                    },
                },
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        logger.error(f"Error in metadata analytics: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": str(e), "message": "Metadata analytics failed"}
            ),
        }
