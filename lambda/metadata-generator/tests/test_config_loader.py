"""Tests for ConfigLoader."""

import tempfile
from pathlib import Path

import pytest

from src.core.config_loader import ConfigLoader
from src.core.schema import Config


def test_config_loader_valid_yaml():
    """Test loading valid config YAML."""
    yaml_content = """
metadata_fields:
  department:
    type: "STRING"
    options: ["sales", "engineering"]
    description: "Department name"

path_rules:
  - pattern: "{department}/**"
    extractions:
      department: "{department}"

file_type_rules:
  table_data:
    - extensions: [".csv"]
      use_columns_for_metadata: true

bedrock:
  model_id: "test-model"
  max_tokens: 1000
  input_context_window: 2000
  temperature: 0.1
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        f.flush()
        
        config = ConfigLoader.load(f.name)
        
        assert isinstance(config, Config)
        assert len(config.metadata_fields) == 1
        assert len(config.path_rules) == 1
        assert "table_data" in config.file_type_rules
        assert config.bedrock_model_id == "test-model"


def test_config_loader_invalid_file_type_rules():
    """Test that invalid file_type_rules structure raises error."""
    yaml_content = """
metadata_fields:
  department:
    type: "STRING"
    description: "Department"

path_rules: []

file_type_rules:
  - table_data:
    - extensions: [".csv"]

bedrock:
  model_id: "test-model"
  max_tokens: 1000
  input_context_window: 2000
  temperature: 0.1
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        f.flush()
        
        with pytest.raises(AttributeError, match="'list' object has no attribute 'items'"):
            ConfigLoader.load(f.name)


def test_config_loader_from_module():
    """Test loading config from module."""
    config = ConfigLoader.load_from_module()
    
    assert isinstance(config, Config)
    assert len(config.metadata_fields) > 0
    assert len(config.path_rules) > 0
    assert len(config.file_type_rules) > 0
