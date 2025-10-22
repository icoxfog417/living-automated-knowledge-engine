"""Local test script for Lambda handler with full AI analysis.

This script allows you to test the complete metadata analytics pipeline locally,
including:
- S3 metadata collection
- AI-powered analysis with Strands Agents SDK
- PDF report generation
- S3 upload (optional with DRY_RUN mode)

Usage:
    # Normal execution (with S3 upload)
    uv run python test_handler_local.py
    
    # Dry run mode (skip S3 upload, save locally)
    DRY_RUN=true uv run python test_handler_local.py
"""

import json
import logging
import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

# Set environment variables
os.environ["BUCKET_NAME"] = "lake-data-988417841316-us-east-1"
os.environ["AWS_REGION"] = "us-east-1"

# Optional: Enable dry run mode (skip S3 upload)
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

if DRY_RUN:
    logger.warning("🔴 DRY RUN MODE: S3 uploads will be skipped")
    # Mock S3 upload function
    import src.utils.s3_operations as s3_ops

    def mock_upload(bucket, key, filepath):
        logger.info(f"[DRY RUN] Would upload {filepath} to s3://{bucket}/{key}")
        return f"s3://{bucket}/{key}"

    s3_ops.upload_to_s3 = mock_upload

from src.handler import lambda_handler


def create_mock_context():
    """Create a mock Lambda context object."""
    context = MagicMock()
    context.function_name = "lake-metadata-analytics-local-test"
    context.function_version = "$LATEST"
    context.invoked_function_arn = (
        "arn:aws:lambda:us-east-1:988417841316:function:lake-metadata-analytics-test"
    )
    context.memory_limit_in_mb = 1536
    context.aws_request_id = f"test-request-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    context.log_group_name = "/aws/lambda/lake-metadata-analytics-test"
    context.log_stream_name = f"test/{datetime.utcnow().strftime('%Y/%m/%d')}/[$LATEST]test"
    context.get_remaining_time_in_millis = lambda: 900000  # 15 minutes
    return context


def create_cloudwatch_event():
    """Create a mock CloudWatch Events scheduled event."""
    return {
        "version": "0",
        "id": f"test-event-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "account": "988417841316",
        "time": datetime.utcnow().isoformat() + "Z",
        "region": "us-east-1",
        "resources": [
            "arn:aws:events:us-east-1:988417841316:rule/lake-metadata-analytics-test"
        ],
        "detail": {},
    }


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)


def main():
    """Run local handler test."""
    print_header("LAMBDA HANDLER LOCAL TEST")

    print(f"\n📦 Configuration:")
    print(f"  Bucket: {os.environ['BUCKET_NAME']}")
    print(f"  Region: {os.environ['AWS_REGION']}")
    print(f"  Dry Run: {'✅ Enabled' if DRY_RUN else '❌ Disabled'}")

    # Create mock event and context
    event = create_cloudwatch_event()
    context = create_mock_context()

    print(f"\n📋 Event:")
    print(json.dumps(event, indent=2))

    print_header("EXECUTING HANDLER")

    # Execute handler
    try:
        response = lambda_handler(event, context)

        print_header("EXECUTION RESULT")

        print(f"\n✅ Status Code: {response['statusCode']}")

        # Parse and display response body
        body = json.loads(response["body"])
        print(f"\n📊 Response Body:")
        print(json.dumps(body, indent=2, ensure_ascii=False))

        if response["statusCode"] == 200:
            print_header("✅ SUCCESS")

            # Display summary
            summary = body.get("summary", {})
            print(f"\n📈 Collection Summary:")
            print(f"  Total Scanned: {summary.get('total_scanned', 0)} files")
            print(f"  Total Collected: {summary.get('total_collected', 0)} files")
            print(f"  Execution Time: {summary.get('execution_time_seconds', 0):.2f}s")
            print(f"  Data Transfer: {summary.get('data_transfer_mb', 0):.2f} MB")

            # Display analysis results
            if "analysis" in body:
                analysis = body["analysis"]
                print(f"\n🤖 AI Analysis:")
                print(f"  Key Findings: {analysis.get('key_findings_count', 0)} items")
                print(f"  Charts Generated: {analysis.get('charts_generated', 0)} files")

            # Display output URLs
            if "outputs" in body:
                outputs = body["outputs"]
                print(f"\n📄 Generated Outputs:")
                print(f"  Report: {outputs.get('report_url', 'N/A')}")
                chart_urls = outputs.get("chart_urls", [])
                if chart_urls:
                    print(f"  Charts ({len(chart_urls)}):")
                    for url in chart_urls:
                        print(f"    - {url}")

            print("\n✨ Handler executed successfully!")

        else:
            print_header("❌ ERROR")
            print(f"\nHandler execution failed with status {response['statusCode']}")
            if "error" in body:
                print(f"Error: {body['error']}")
                print(f"Message: {body.get('message', 'N/A')}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)

    except Exception as e:
        print_header("❌ EXCEPTION")
        print(f"\nException occurred: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
