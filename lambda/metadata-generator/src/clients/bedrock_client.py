"""Bedrock client for metadata generation using AI models."""
import json
import boto3
from typing import Optional, Dict, Any


class BedrockClient:
    """Client for Amazon Bedrock API."""
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        max_tokens: int = 2000,
        temperature: float = 0.1,
        bedrock_client: Optional[boto3.client] = None
    ):
        """
        Initialize Bedrock client.
        
        Args:
            model_id: Bedrock model ID to use
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0.0 to 1.0)
            bedrock_client: Optional boto3 Bedrock Runtime client
        """
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.bedrock_client = bedrock_client or boto3.client('bedrock-runtime')
    
    def generate_metadata(self, prompt: str) -> Dict[str, Any]:
        """
        Generate metadata using Bedrock model.
        
        Args:
            prompt: Prompt for metadata generation
            
        Returns:
            Generated metadata as dictionary
            
        Raises:
            Exception: If generation fails or response is invalid
        """
        try:
            # Prepare request body for Claude 3
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            # Call Bedrock API
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Extract generated text
            if 'content' in response_body and len(response_body['content']) > 0:
                generated_text = response_body['content'][0]['text']
            else:
                raise ValueError("No content in Bedrock response")
            
            # Parse JSON from generated text
            metadata = self._extract_json(generated_text)
            
            return metadata
            
        except Exception as e:
            raise Exception(f"Failed to generate metadata with Bedrock: {str(e)}")
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from generated text.
        
        Args:
            text: Generated text that may contain JSON
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            ValueError: If no valid JSON found
        """
        # Try to parse the entire text as JSON first
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in code blocks
        import re
        
        # Look for JSON in markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        # Try to find JSON object directly in text
        json_obj_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_obj_pattern, text, re.DOTALL)
        
        if matches:
            # Try the longest match first (likely to be the complete JSON)
            for match in sorted(matches, key=len, reverse=True):
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        raise ValueError(f"No valid JSON found in generated text: {text[:200]}...")
