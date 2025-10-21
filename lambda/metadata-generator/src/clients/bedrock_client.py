"""Bedrock client for metadata generation using AI models."""
import json
import boto3
from typing import Optional, Dict, Any, List

from ..services.json_extractor import JsonExtractor


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
    
    def generate_structured_json(
        self, 
        prompt: str, 
        json_schema: Dict[str, Any],
        tool_name: str = "generate_structured_data",
        tool_description: str = "Generate structured data according to the provided schema"
    ) -> Dict[str, Any]:
        """
        Generate structured JSON using Bedrock Converse API with tool use.
        
        This method uses the Converse API's tool use feature to ensure the model
        returns data strictly conforming to the provided JSON Schema.
        
        Args:
            prompt: Prompt describing what data to generate
            json_schema: JSON Schema defining the structure of the output
            tool_name: Name of the tool (default: "generate_structured_data")
            tool_description: Description of what the tool does
            
        Returns:
            Generated data as dictionary conforming to the schema
            
        Raises:
            Exception: If generation fails or no tool use is returned
        """
        try:
            # Prepare tool configuration
            tool_config = {
                "tools": [
                    {
                        "toolSpec": {
                            "name": tool_name,
                            "description": tool_description,
                            "inputSchema": {
                                "json": json_schema
                            }
                        }
                    }
                ],
                "toolChoice": {
                    "tool": {
                        "name": tool_name
                    }
                }
            }
            
            # Call Converse API
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                toolConfig=tool_config,
                inferenceConfig={
                    "maxTokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )
            
            # Extract tool use from response
            if 'output' not in response:
                raise ValueError("No output in Bedrock response")
            
            output = response['output']
            if 'message' not in output:
                raise ValueError("No message in Bedrock output")
            
            message = output['message']
            if 'content' not in message:
                raise ValueError("No content in Bedrock message")
            
            # Find tool use in content
            tool_use = None
            for content_block in message['content']:
                if 'toolUse' in content_block:
                    tool_use = content_block['toolUse']
                    break
            
            if not tool_use:
                raise ValueError("No tool use found in response")
            
            # Extract the structured input from tool use
            if 'input' not in tool_use:
                raise ValueError("No input in tool use")
            
            return tool_use['input']
            
        except Exception as e:
            raise Exception(f"Failed to generate structured JSON with Bedrock: {str(e)}")
    
    def generate_metadata(self, prompt: str, json_schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate metadata using Bedrock model.
        
        If json_schema is provided, uses Converse API with tool use for structured output.
        Otherwise, falls back to the legacy invoke_model approach.
        
        Args:
            prompt: Prompt for metadata generation
            json_schema: Optional JSON Schema for structured output
            
        Returns:
            Generated metadata as dictionary
            
        Raises:
            Exception: If generation fails or response is invalid
        """
        # Use structured generation if schema is provided
        if json_schema:
            return self.generate_structured_json(
                prompt=prompt,
                json_schema=json_schema,
                tool_name="generate_metadata",
                tool_description="Generate metadata for a file according to the specified schema"
            )
        
        # Legacy approach using invoke_model
        try:
            # Prepare request body for Claude 3
            request_body = {
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
            metadata = JsonExtractor.extract_json(generated_text)
            
            return metadata
            
        except Exception as e:
            raise Exception(f"Failed to generate metadata with Bedrock: {str(e)}")
