"""Extract JSON from text responses."""
import json
import re
from typing import Dict, Any


class JsonExtractor:
    """Extract and parse JSON from generated text."""
    
    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """
        Extract JSON from generated text.
        
        This method tries multiple strategies to find valid JSON:
        1. Parse the entire text as JSON
        2. Find JSON in markdown code blocks
        3. Find JSON object patterns in text
        
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
        
        # Try to find JSON in markdown code blocks
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
