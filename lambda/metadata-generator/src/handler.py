import boto3
import json
from typing import Any, Dict

s3_client = boto3.client('s3')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """S3 バケット内のオブジェクト一覧を取得（シンプル版）"""
    bucket_name = event.get('bucket_name')
    
    if not bucket_name:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'bucket_name is required'})
        }
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        objects = [obj['Key'] for obj in response.get('Contents', [])]
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'bucket': bucket_name,
                'objects': objects,
                'count': len(objects)
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
