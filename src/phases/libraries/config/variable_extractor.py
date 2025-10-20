#!/usr/bin/env python3
"""
VariableExtractor Unit

Extract template variables from config
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import logging
import re

logger = logging.getLogger(__name__)


class VariableExtractor:
    """
    Extract template variables from config
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize VariableExtractor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def extract(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract template variables from configuration.

        Flattens nested configuration into template-ready variables.

        Args:
            config: Configuration dictionary (can be nested)

        Returns:
            Flattened dictionary with template variables

        Example:
            Input:  {'db': {'host': 'localhost', 'port': 5432}}
            Output: {'db_host': 'localhost', 'db_port': 5432}
        """
        logger.info("Extracting template variables from configuration")

        variables = {}
        self._flatten_dict(config, variables)

        logger.info(f"Extracted {len(variables)} template variables")
        return variables

    def _flatten_dict(
        self, data: Dict[str, Any], result: Dict[str, Any], prefix: str = ""
    ) -> None:
        """
        Recursively flatten nested dictionary.

        Args:
            data: Dictionary to flatten
            result: Dictionary to store results
            prefix: Current key prefix
        """
        for key, value in data.items():
            # Create flattened key
            new_key = f"{prefix}_{key}" if prefix else key

            if isinstance(value, dict):
                # Recursively flatten nested dict
                self._flatten_dict(value, result, new_key)
            else:
                # Add to results (convert to template-friendly format)
                result[new_key] = self._convert_value(value)

    def _convert_value(self, value: Any) -> Any:
        """
        Convert value to template-friendly format.

        Args:
            value: Value to convert

        Returns:
            Converted value
        """
        if isinstance(value, bool):
            # Keep as boolean for Jinja2
            return value
        elif isinstance(value, (int, float)):
            # Keep numbers as-is
            return value
        elif isinstance(value, list):
            # Keep lists as-is for Jinja2 loops
            return value
        elif value is None:
            # Convert None to empty string
            return ""
        else:
            # String or other - convert to string
            return str(value)

    def extract_from_template(self, template: str) -> Set[str]:
        """
        Extract variable names from a Jinja2 template.

        Args:
            template: Jinja2 template string

        Returns:
            Set of variable names found in template

        Example:
            Input:  "Hello {{ name }}! Port: {{ port }}"
            Output: {'name', 'port'}
        """
        logger.debug("Extracting variables from template")

        # Match {{ variable }} and {% if variable %}
        patterns = [
            r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\}",  # {{ var }}
            r"\{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s*%\}",  # {% if var %}
            r"\{%\s*for\s+\w+\s+in\s+([a-zA-Z_][a-zA-Z0-9_\.]*)\s*%\}",  # {% for x in var %}
        ]

        variables = set()
        for pattern in patterns:
            matches = re.findall(pattern, template)
            variables.update(matches)

        # Remove common Jinja2 keywords
        keywords = {"true", "false", "none", "True", "False", "None"}
        variables = variables - keywords

        logger.debug(f"Found {len(variables)} variables in template")
        return variables


def main():
    """Test the unit."""
    unit = VariableExtractor()

    # Test 1: Extract from nested config
    print("Test 1: Extract from nested configuration")
    config = {
        "project_name": "openproject",
        "database": {
            "host": "localhost",
            "port": 5432,
            "credentials": {"user": "postgres", "password": "secret"},
        },
        "features": {"ssl_enabled": True, "debug": False},
        "services": ["web", "db"],
    }

    variables = unit.extract(config)
    print(f"  Extracted {len(variables)} variables:")
    for key, value in sorted(variables.items()):
        print(f"    {key}: {value}")

    # Test 2: Extract from template
    print("\nTest 2: Extract variables from template")
    template = """
server {
    listen {{ port }};
    server_name {{ domain }};

    {% if ssl_enabled %}
    ssl on;
    ssl_certificate {{ ssl_cert }};
    {% endif %}

    {% for service in services %}
    upstream {{ service }};
    {% endfor %}
}
"""

    template_vars = unit.extract_from_template(template)
    print(f"  Found variables in template: {sorted(template_vars)}")

    # Verify
    assert "project_name" in variables
    assert "database_host" in variables
    assert "database_credentials_user" in variables
    assert "port" in template_vars
    assert "ssl_enabled" in template_vars

    print("\n✅ All tests passed!")
    print(f"\n{unit.__class__.__name__} tests complete")


if __name__ == "__main__":
    main()
