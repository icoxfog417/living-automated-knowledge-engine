"""Lambda handler for metadata generation."""

import json
import logging
from typing import Any

from .clients.bedrock_client import BedrockClient
from .clients.s3_operations import S3Operations
from .core.config_loader import ConfigLoader
from .core.metadata_generator import MetadataGenerator
from .services.event_parser import EventParser
from .services.rule_matcher import RuleMatcher

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    # Load configuration
    config = ConfigLoader.load_from_module()

    # Log loaded configuration
    config_dict = {
        "bedrock_model_id": config.bedrock_model_id,
        "bedrock_max_tokens": config.bedrock_max_tokens,
        "bedrock_temperature": config.bedrock_temperature,
        "rules": [{"pattern": rule.pattern, "schema": rule.schema} for rule in config.rules],
    }
    logger.info(f"Loaded configuration: {json.dumps(config_dict, ensure_ascii=False, indent=2)}")

    # Initialize clients and services
    s3_ops = S3Operations()
    bedrock_client = BedrockClient(
        model_id=config.bedrock_model_id,
        max_tokens=config.bedrock_max_tokens,
        temperature=config.bedrock_temperature,
    )
    rule_matcher = RuleMatcher(config.rules)
    generator = MetadataGenerator(config, bedrock_client, rule_matcher)

except Exception as e:
    logger.error(f"Failed to initialize Lambda components: {str(e)}", exc_info=True)
    raise


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for S3 object created events.

    Args:
        event: EventBridge event containing S3 object details
        context: Lambda context

    Returns:
        Response dictionary with status and details
    """
    try:
        logger.info(f"Processing event: {json.dumps(event)}")

        # Extract file information from EventBridge event (delegated to EventParser)
        file_info = EventParser.extract_file_info(event)

        if not file_info:
            logger.warning("No file information found in event")
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid event format"})}

        bucket = file_info["bucket"]
        key = file_info["key"]

        logger.info(f"Processing file: s3://{bucket}/{key}")

        # Read file content from S3 (using pre-initialized client)
        file_data = s3_ops.read_file(bucket, key)

        # Generate metadata (using pre-initialized generator)
        logger.info(f"Generating metadata for {key}")
        metadata = generator.generate_metadata(file_data)

        # Log generated metadata
        logger.info(
            f"Generated metadata: {json.dumps(metadata.metadata, ensure_ascii=False, indent=2)}"
        )

        # Save metadata to S3
        s3_ops.write_metadata(bucket, metadata)

        logger.info(f"Successfully generated and saved metadata for {key}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Metadata generated successfully",
                    "file": key,
                    "metadata_key": metadata.s3_key,
                    "metadata": metadata.metadata,
                },
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "message": "Failed to generate metadata"}),
        }
