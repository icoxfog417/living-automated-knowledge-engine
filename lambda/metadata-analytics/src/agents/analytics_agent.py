"""Metadata analytics agent using Strands Agents SDK."""

import json
import logging
from typing import Any, Dict, List

from strands import Agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert data analyst specializing in metadata analytics and reporting.

Given metadata statistics and information about pre-generated charts, you will:
1. Analyze trends and patterns in the collected metadata
2. Interpret the visualizations that have been created
3. Generate comprehensive analysis in structured text format

ANALYSIS REQUIREMENTS:
- Review the provided statistics and chart descriptions
- Identify the most significant patterns and trends
- Analyze distributions and relationships between different metadata fields
- Calculate and explain key metrics (totals, averages, percentages, growth rates)
- Highlight any unusual patterns or outliers
- Provide actionable insights based on the data

RESPONSE FORMAT:
Return your analysis as a JSON object with the following structure:
{
  "executive_summary": "Brief overview of the key findings (2-3 sentences)",
  "key_findings": [
    "Finding 1: Specific, data-driven insight",
    "Finding 2: Another specific insight",
    ...
  ],
  "detailed_statistics": {
    "summary": "Detailed explanation of statistics",
    "notable_patterns": ["Pattern 1", "Pattern 2", ...],
    "recommendations": ["Recommendation 1", "Recommendation 2", ...]
  }
}

IMPORTANT:
- Base your analysis ONLY on the provided data
- Be specific with numbers and percentages
- Provide actionable insights
- Keep findings concise and data-driven
- Do not make assumptions beyond what the data shows
"""


class MetadataAnalyticsAgent:
    """AI agent for metadata analytics using Strands Agents SDK."""

    def __init__(self, region: str = "us-west-2"):
        """Initialize the analytics agent.

        Args:
            region: AWS region for Bedrock (not used anymore but kept for compatibility)
        """
        logger.info(f"Initializing MetadataAnalyticsAgent in region: {region}")

        # Create agent without tools - focusing on interpretation only
        self.agent = Agent(
            model="global.anthropic.claude-sonnet-4-5-20250929-v1:0",
            system_prompt=SYSTEM_PROMPT,
        )
        logger.info("Strands Agent created successfully (interpretation mode)")

    def analyze(
        self,
        statistics: Dict[str, Any],
        chart_info: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Analyze metadata statistics with pre-generated charts.

        Args:
            statistics: Aggregated metadata statistics from collector
            chart_info: List of chart information (title, description, file_path)

        Returns:
            Analysis result with insights and chart information
        """
        logger.info("Starting AI-powered metadata analysis (interpretation mode)...")
        import time

        start_time = time.time()

        try:
            # Format statistics and chart info for the agent
            prompt = self._format_analysis_prompt(statistics, chart_info)

            # Execute agent with statistics
            logger.info("Executing Strands Agent for interpretation...")
            response = self.agent(prompt)

            logger.info("Agent execution completed")

            # Parse agent response
            result = self._parse_agent_response(response, statistics, chart_info)

            # Add execution time
            result["execution_time"] = time.time() - start_time

            return result

        except Exception as e:
            logger.error(f"Error during analysis: {e}", exc_info=True)
            # Return fallback analysis if agent fails
            return self._create_fallback_analysis(statistics, chart_info)

    def _format_analysis_prompt(
        self, statistics: Dict[str, Any], chart_info: List[Dict[str, str]] = None
    ) -> str:
        """Format statistics and chart info into a prompt for the agent.

        Args:
            statistics: Raw statistics
            chart_info: List of chart information dictionaries

        Returns:
            Formatted prompt string
        """
        # Format chart information
        chart_descriptions = []
        if chart_info:
            for i, chart in enumerate(chart_info, 1):
                chart_descriptions.append(
                    f"{i}. {chart['title']}\n"
                    f"   Type: {chart['chart_type']}\n"
                    f"   Field: {chart['metadata_key']}\n"
                    f"   Description: {chart['description']}"
                )

        chart_section = (
            "\n\nPRE-GENERATED VISUALIZATIONS:\n"
            + "\n\n".join(chart_descriptions)
            if chart_descriptions
            else "\n\nNo visualizations were generated."
        )

        prompt = f"""Please analyze the following metadata statistics and provide comprehensive insights.

METADATA STATISTICS:
```json
{json.dumps(statistics, indent=2, ensure_ascii=False)}
```
{chart_section}

Please analyze this data and provide:
1. An executive summary highlighting the most important findings
2. A list of key findings with specific data points
3. Detailed statistical insights including notable patterns and recommendations

Return your analysis as a JSON object following the specified format.
"""
        return prompt

    def _parse_agent_response(
        self,
        response: str,
        original_stats: Dict[str, Any],
        chart_info: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Parse the agent's response.

        Args:
            response: Raw response from agent
            original_stats: Original statistics for fallback
            chart_info: Chart information

        Returns:
            Structured analysis result
        """
        try:
            # Try to extract JSON from response
            response_str = str(response)

            # Look for JSON content
            if "```json" in response_str:
                json_start = response_str.find("```json") + 7
                json_end = response_str.find("```", json_start)
                json_content = response_str[json_start:json_end].strip()
                analysis = json.loads(json_content)
            elif "```" in response_str:
                # Try without json marker
                json_start = response_str.find("```") + 3
                json_end = response_str.find("```", json_start)
                json_content = response_str[json_start:json_end].strip()
                analysis = json.loads(json_content)
            else:
                # Try parsing the entire response as JSON
                analysis = json.loads(response_str)

            # Ensure required fields exist
            result = {
                "executive_summary": analysis.get(
                    "executive_summary", "Analysis completed successfully."
                ),
                "key_findings": analysis.get("key_findings", []),
                "detailed_statistics": analysis.get("detailed_statistics", {}),
                "charts": [
                    chart["file_path"] for chart in (chart_info or [])
                ],  # Use actual chart paths
                "raw_response": response_str,
                "execution_time": 0.0,  # Will be set by analyze() method
            }

            return result

        except Exception as e:
            logger.warning(f"Failed to parse agent response as JSON: {e}")
            # Return response as-is with original stats
            return {
                "executive_summary": "Analysis completed. See raw response for details.",
                "key_findings": self._extract_findings_from_text(str(response)),
                "detailed_statistics": original_stats,
                "charts": [chart["file_path"] for chart in (chart_info or [])],
                "raw_response": str(response),
                "execution_time": 0.0,  # Will be set by analyze() method
            }

    def _extract_findings_from_text(self, text: str) -> List[str]:
        """Extract findings from unstructured text response.

        Args:
            text: Response text

        Returns:
            List of findings
        """
        findings = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered items
            if line.startswith("-") or line.startswith("•"):
                findings.append(line[1:].strip())
            elif len(line) > 10 and any(
                line.startswith(f"{i}.") for i in range(1, 20)
            ):
                findings.append(line.split(".", 1)[1].strip())

        return findings[:10]  # Limit to 10 findings

    def _create_fallback_analysis(
        self, statistics: Dict[str, Any], chart_info: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a basic analysis if agent fails.

        Args:
            statistics: Original statistics
            chart_info: Chart information

        Returns:
            Basic analysis result
        """
        logger.info("Creating fallback analysis...")

        total = statistics.get("total_collected", 0)
        aggs = statistics.get("aggregations", {})

        findings = []
        if "department" in aggs:
            top_dept = max(
                aggs["department"].items(), key=lambda x: x[1], default=(None, 0)
            )
            if top_dept[0]:
                findings.append(
                    f"Top department: {top_dept[0]} with {top_dept[1]} files"
                )

        if "document_type" in aggs:
            top_type = max(
                aggs["document_type"].items(), key=lambda x: x[1], default=(None, 0)
            )
            if top_type[0]:
                findings.append(
                    f"Most common document type: {top_type[0]} ({top_type[1]} files)"
                )

        by_file_type = statistics.get("by_file_type", {})
        if by_file_type:
            top_ext = max(by_file_type.items(), key=lambda x: x[1], default=(None, 0))
            if top_ext[0]:
                findings.append(
                    f"Most common file extension: {top_ext[0]} ({top_ext[1]} files)"
                )

        chart_count = len(chart_info) if chart_info else 0

        return {
            "executive_summary": (
                f"Collected and analyzed {total} metadata files. "
                f"Generated {chart_count} visualization(s). "
                "Basic statistical analysis completed."
            ),
            "key_findings": findings
            if findings
            else ["No significant patterns detected."],
            "detailed_statistics": {
                "summary": f"Analyzed {total} files across various categories.",
                "notable_patterns": findings,
                "recommendations": [
                    "Review the generated charts for detailed distribution patterns"
                ],
            },
            "charts": [chart["file_path"] for chart in (chart_info or [])],
            "raw_response": "Fallback analysis (agent execution failed)",
            "execution_time": 0.0,
        }
