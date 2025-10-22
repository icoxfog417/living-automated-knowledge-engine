"""Configuration loader for metadata generation rules."""

from pathlib import Path

import yaml

from .schema import Config, MetadataRule


class ConfigLoader:
    """Load configuration from YAML file."""

    @staticmethod
    def load(config_path: str) -> Config:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to the configuration YAML file

        Returns:
            Config object with loaded rules and settings

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with config_file.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError("Config file is empty")

        # Parse rules
        rules_data = data.get("rules", {})
        file_patterns = rules_data.get("file_patterns", [])

        if not file_patterns:
            raise ValueError("No file patterns defined in config")

        rules = [
            MetadataRule(pattern=rule.get("pattern", ""), schema=rule.get("schema", {}))
            for rule in file_patterns
        ]

        # Parse Bedrock configuration
        bedrock_config = data.get("bedrock", {})

        return Config(
            rules=rules,
            bedrock_model_id=bedrock_config.get(
                "model_id", "global.anthropic.claude-haiku-4-5-20251001-v1:0"
            ),
            bedrock_max_tokens=bedrock_config.get("max_tokens", 2000),
            bedrock_input_context_window=bedrock_config.get("input_context_window", 100000),
            bedrock_temperature=bedrock_config.get("temperature", 0.1),
        )

    @staticmethod
    def load_from_module(module_path: str = "src/config/config.yaml") -> Config:
        """
        Load configuration from module-relative path.

        Args:
            module_path: Relative path from the Lambda function root

        Returns:
            Config object
        """
        # Get the directory where this module is located
        current_dir = Path(__file__).parent.parent
        config_path = current_dir / module_path.replace("src/", "")

        return ConfigLoader.load(str(config_path))
