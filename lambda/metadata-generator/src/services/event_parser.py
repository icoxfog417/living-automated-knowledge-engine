"""Parse Lambda event to extract file information."""
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EventParser:
    """Parse Lambda event to extract file information."""
    
    @staticmethod
    def extract_file_info(event: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Extract file information from EventBridge S3 event.
        
        Supports two event formats:
        1. EventBridge format (S3 events via EventBridge)
        2. Direct invocation format (for testing)
        
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
