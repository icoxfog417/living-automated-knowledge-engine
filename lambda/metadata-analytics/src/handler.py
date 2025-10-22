"""Lambda handler for metadata analytics."""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

from .agents.analytics_agent import MetadataAnalyticsAgent
from .collector.metadata_collector import MetadataCollector
from .collector.models import CollectionParams
from .utils.chart_generator import ChartGenerator
from .utils.pdf_generator import PDFReportGenerator
from .utils.s3_operations import upload_to_s3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize reusable components outside handler for Lambda container reuse
collector = MetadataCollector()
chart_generator = ChartGenerator()
pdf_generator = PDFReportGenerator()
region = os.environ.get("AWS_REGION", "us-east-1")
analytics_agent = MetadataAnalyticsAgent(region=region)


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
        # Get bucket name from environment variable
        bucket_name = os.environ.get("BUCKET_NAME")
        if not bucket_name:
            raise ValueError("BUCKET_NAME environment variable is required")

        # Set date range: previous 24 hours
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)

        logger.info(f"Target: {bucket_name}, Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        # Configure collection parameters
        params = CollectionParams(
            bucket_name=bucket_name,
            start_date=start_date,
            end_date=end_date,
            parallel_downloads=20,
        )

        # Collect metadata
        result = collector.collect(params)

        logger.info(f"Collected {result.total_collected} files ({result.total_scanned} scanned) in {result.execution_time_seconds:.2f}s, {result.data_transfer_bytes / 1024 / 1024:.2f} MB")

        # Get aggregation
        aggregation = result.aggregate()

        # Generate charts and tables deterministically
        chart_results, table_data = chart_generator.generate_charts(aggregation)
        logger.info(f"Generated {len(chart_results)} charts, {len(table_data)} metadata detail tables")

        # Prepare chart information for AI agent
        chart_info = [
            {
                "title": chart.title,
                "chart_type": chart.chart_type,
                "metadata_key": chart.metadata_key,
                "description": chart.description,
                "file_path": chart.file_path,
            }
            for chart in chart_results
        ]

        # Perform AI analysis with pre-generated charts
        analysis_result = analytics_agent.analyze(
            statistics=aggregation, chart_info=chart_info
        )
        logger.info(f"AI analysis completed in {analysis_result['execution_time']:.2f}s")

        # Generate PDF report
        chart_paths_for_pdf = [chart.file_path for chart in chart_results]
        pdf_path = pdf_generator.generate_report(
            aggregation=aggregation,
            analysis=analysis_result,
            start_date=start_date,
            end_date=end_date,
            chart_paths=chart_paths_for_pdf,
            table_data=table_data,
        )

        # Upload PDF to S3
        report_date = end_date.strftime("%Y-%m-%d")
        s3_key = f"analytics-reports/{report_date}/metadata-analytics-report.pdf"
        s3_url = upload_to_s3(bucket_name, s3_key, pdf_path)
        logger.info(f"PDF uploaded: {s3_url}")

        # Upload charts to S3
        chart_urls = []
        if chart_results:
            for i, chart_result in enumerate(chart_results, 1):
                if os.path.exists(chart_result.file_path):
                    chart_filename = f"{i:02d}_{chart_result.metadata_key}_{chart_result.chart_type}.png"
                    chart_s3_key = f"analytics-reports/{report_date}/charts/{chart_filename}"
                    chart_url = upload_to_s3(bucket_name, chart_s3_key, chart_result.file_path)
                    chart_urls.append(chart_url)
                    os.remove(chart_result.file_path)

        os.remove(pdf_path)
        
        logger.info(f"Charts uploaded: {len(chart_urls)} files")
        logger.info("Analytics completed successfully")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Metadata analytics completed successfully",
                    "summary": {
                        "total_scanned": result.total_scanned,
                        "total_collected": result.total_collected,
                        "execution_time_seconds": result.execution_time_seconds,
                        "data_transfer_mb": round(result.data_transfer_bytes / 1024 / 1024, 2),
                    },
                    "analysis": {
                        "executive_summary": analysis_result["executive_summary"],
                        "key_findings_count": len(analysis_result["key_findings"]),
                        "charts_generated": len(analysis_result["charts"]),
                    },
                    "outputs": {
                        "report_url": s3_url,
                        "chart_urls": chart_urls,
                    },
                },
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        logger.error(f"Error in metadata analytics: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "message": "Metadata analytics failed"}),
        }
