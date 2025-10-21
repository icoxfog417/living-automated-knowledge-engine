"""Lambda handler for metadata generation."""
import json
import logging
from typing import Any, Dict

from .core.config_loader import ConfigLoader
from .core.metadata_generator import MetadataGenerator
from .clients.bedrock_client import BedrockClient
from .clients.s3_operations import S3Operations

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
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
        
        # Extract file information from EventBridge event
        file_info = extract_file_info_from_event(event)
        
        if not file_info:
            logger.warning("No file information found in event")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid event format'})
            }
        
        bucket = file_info['bucket']
        key = file_info['key']
        
        logger.info(f"Processing file: s3://{bucket}/{key}")
        
        # Initialize S3 operations
        s3_ops = S3Operations()
        
        # Check if metadata already exists
        if s3_ops.metadata_exists(bucket, key):
            logger.info(f"Metadata already exists for {key}, skipping generation")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Metadata already exists',
                    'file': key,
                    'skipped': True
                })
            }
        
        # Read file content from S3
        file_data = s3_ops.read_file(bucket, key)
        
        # Load configuration
        config = ConfigLoader.load_from_module()
        
        # Initialize Bedrock client
        bedrock_client = BedrockClient(
            model_id=config.bedrock_model_id,
            max_tokens=config.bedrock_max_tokens,
            temperature=config.bedrock_temperature
        )
        
        # Initialize metadata generator
        generator = MetadataGenerator(config, bedrock_client)
        
        # Generate metadata
        logger.info(f"Generating metadata for {key}")
        metadata = generator.generate_metadata(file_data)
        
        # Save metadata to S3
        s3_ops.write_metadata(bucket, metadata)
        
        logger.info(f"Successfully generated and saved metadata for {key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Metadata generated successfully',
                'file': key,
                'metadata_key': metadata.s3_key,
                'metadata': metadata.metadata
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to generate metadata'
            })
        }


def extract_file_info_from_event(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract file information from EventBridge S3 event.
    
    Args:
        event: EventBridge event dictionary
        
    Returns:
        Dictionary with 'bucket' and 'key' or None if invalid
    """
    try:
        # EventBridge format for S3 events
        if 'detail' in event:
            detail = event['detail']
            
            # Extract bucket name
            bucket_info = detail.get('bucket', {})
            bucket = bucket_info.get('name')
            
            # Extract object key
            object_info = detail.get('object', {})
            key = object_info.get('key')
            
            if bucket and key:
                return {
                    'bucket': bucket,
                    'key': key
                }
        
        # Direct invocation format (for testing)
        if 'bucket' in event and 'key' in event:
            return {
                'bucket': event['bucket'],
                'key': event['key']
            }
        
        logger.warning(f"Could not extract file info from event: {json.dumps(event)}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting file info: {str(e)}")
        return None
