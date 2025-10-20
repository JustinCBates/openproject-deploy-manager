#!/usr/bin/env python3
"""
ConfigLoader Unit

Load configuration from YAML/env files
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Load configuration from YAML/env files
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ConfigLoader.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def load(self, path: Path) -> Dict[str, Any]:
        """
        Load configuration from file (YAML or .env).

        Args:
            path: Path to configuration file

        Returns:
            Dict containing configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If file format is unsupported
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        logger.info(f"Loading configuration from: {path}")

        # Read file content
        content = path.read_text()

        # Parse based on file extension
        if path.suffix in [".yml", ".yaml"]:
            return self.parse_yaml(content)
        elif path.suffix == ".env":
            return self._parse_env(content)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

    def parse_yaml(self, content: str) -> Dict[str, Any]:
        """
        Parse YAML content into dictionary.

        Args:
            content: YAML content as string

        Returns:
            Dict containing parsed YAML

        Raises:
            yaml.YAMLError: If YAML is invalid
        """
        try:
            data = yaml.safe_load(content)
            if data is None:
                return {}
            if not isinstance(data, dict):
                raise ValueError(
                    f"YAML must contain a dictionary, got {type(data).__name__}"
                )
            logger.debug(f"Parsed YAML with {len(data)} top-level keys")
            return data
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML: {e}")
            raise

    def _parse_env(self, content: str) -> Dict[str, str]:
        """
        Parse .env file content into dictionary.

        Args:
            content: .env file content

        Returns:
            Dict with environment variables
        """
        result = {}
        for line in content.splitlines():
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE format
            if "=" in line:
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip().strip("\"'")

        logger.debug(f"Parsed .env with {len(result)} variables")
        return result


def main():
    """Test the unit."""
    import tempfile

    # Test YAML loading
    unit = ConfigLoader()

    # Create temp YAML file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(
            """
project_name: openproject
services:
  - web
  - db
config:
  port: 8080
"""
        )
        temp_path = Path(f.name)

    try:
        config = unit.load(temp_path)
        print(f"✅ Loaded YAML config: {config}")
        print(f"   Project: {config.get('project_name')}")
        print(f"   Services: {config.get('services')}")
    finally:
        temp_path.unlink()

    # Test YAML parsing
    yaml_content = "key: value\nlist:\n  - item1\n  - item2"
    parsed = unit.parse_yaml(yaml_content)
    print(f"✅ Parsed YAML: {parsed}")

    print(f"\n{unit.__class__.__name__} tests complete")


if __name__ == "__main__":
    main()
