"""Lambda handler for email processing."""

import json
import logging
from typing import Any

from .services.email_parser import EmailParser
from .services.attachment_processor import AttachmentProcessor
from .services.command_processor import CommandProcessor
from .services.response_sender import ResponseSender
from .clients.s3_operations import S3Operations

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize services
s3_ops = S3Operations()
email_parser = EmailParser()
attachment_processor = AttachmentProcessor(s3_ops)
command_processor = CommandProcessor(s3_ops)
response_sender = ResponseSender()


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler for email processing events.

    Args:
        event: EventBridge event containing S3 email object details
        context: Lambda context

    Returns:
        Response dictionary with status and details
    """
    try:
        logger.info(f"Processing email event: {json.dumps(event)}")

        # Extract email information from EventBridge event
        detail = event.get("detail", {})
        bucket = detail.get("bucket", {}).get("name")
        key = detail.get("object", {}).get("key")

        if not bucket or not key:
            logger.warning("No email information found in event")
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid event format"})}

        logger.info(f"Processing email: s3://{bucket}/{key}")

        # Parse email from S3
        email_data = email_parser.parse_email_from_s3(bucket, key)
        
        # Determine email type based on S3 key prefix
        if key.startswith("inbound/upload/"):
            # Process upload email with attachments
            result = attachment_processor.process_attachments(email_data)
            response_sender.send_upload_confirmation(email_data.sender, result)
            
        elif key.startswith("inbound/reports/"):
            # Process command email
            result = command_processor.process_command(email_data)
            response_sender.send_command_response(email_data.sender, result)
            
        else:
            logger.warning(f"Unknown email type for key: {key}")
            return {"statusCode": 400, "body": json.dumps({"error": "Unknown email type"})}

        logger.info(f"Successfully processed email: {key}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Email processed successfully",
                "email_key": key,
                "result": {
                    "success": result.success,
                    "message": result.message
                }
            }),
        }

    except Exception as e:
        logger.error(f"Error processing email: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e), "message": "Failed to process email"}),
        }
