"""Configuration loader for metadata generation rules."""

from pathlib import Path

import yaml

from .schema import Config, MetadataField, PathRule, FileTypeRule


class ConfigLoader:
    """Load configuration from YAML file."""

    @staticmethod
    def load(config_path: str) -> Config:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to the configuration YAML file

        Returns:
            Config object with loaded metadata fields and rules

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

        # Parse metadata fields
        metadata_fields = {}
        fields_data = data.get("metadata_fields", {})
        for field_name, field_config in fields_data.items():
            metadata_fields[field_name] = MetadataField(
                type=field_config.get("type", "STRING"),
                description=field_config.get("description", ""),
                options=field_config.get("options")
            )

        # Parse path rules
        path_rules = []
        rules_data = data.get("path_rules", [])
        for rule_config in rules_data:
            path_rules.append(PathRule(
                pattern=rule_config.get("pattern", ""),
                extractions=rule_config.get("extractions", {})
            ))

        # Parse file type rules
        file_type_rules = {}
        file_types_data = data.get("file_type_rules", {})
        for category, rules_list in file_types_data.items():
            file_type_rules[category] = [
                FileTypeRule(
                    extensions=rule.get("extensions", []),
                    use_columns_for_metadata=rule.get("use_columns_for_metadata", False)
                )
                for rule in rules_list
            ]

        # Parse Bedrock configuration
        bedrock_config = data.get("bedrock", {})

        return Config(
            metadata_fields=metadata_fields,
            path_rules=path_rules,
            file_type_rules=file_type_rules,
            bedrock_model_id=bedrock_config.get(
                "model_id", "anthropic.claude-3-haiku-20240307-v1:0"
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
