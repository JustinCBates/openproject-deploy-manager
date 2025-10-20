#!/usr/bin/env python3
"""
ConfigValidator Unit

Validate configuration completeness
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation"""

    valid: bool
    errors: List[str]
    warnings: List[str]
    missing_keys: List[str]

    def __str__(self):
        if self.valid:
            return "✅ Configuration valid"
        return f"❌ Configuration invalid: {len(self.errors)} errors, {len(self.missing_keys)} missing keys"


class ConfigValidator:
    """
    Validate configuration completeness
    """

    # Required keys for deploy-manager configuration
    REQUIRED_KEYS = ["project_name", "environment", "services"]

    # Optional but recommended keys
    RECOMMENDED_KEYS = ["version", "description"]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ConfigValidator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate configuration completeness and correctness.

        Args:
            config: Configuration dictionary to validate

        Returns:
            ValidationResult with validation status and issues
        """
        errors = []
        warnings = []
        missing_keys = []

        logger.info("Validating configuration...")

        # Check required keys
        missing = self.check_required_keys(config)
        if missing:
            missing_keys.extend(missing)
            errors.append(f"Missing required keys: {', '.join(missing)}")

        # Check recommended keys
        for key in self.RECOMMENDED_KEYS:
            if key not in config:
                warnings.append(f"Recommended key missing: {key}")

        # Validate specific fields
        if "services" in config:
            if not isinstance(config["services"], (list, dict)):
                errors.append("'services' must be a list or dictionary")
            elif isinstance(config["services"], list) and len(config["services"]) == 0:
                warnings.append("'services' list is empty")

        if "environment" in config:
            if config["environment"] not in [
                "production",
                "staging",
                "development",
                "test",
            ]:
                warnings.append(f"Unusual environment value: {config['environment']}")

        # Determine if valid
        valid = len(errors) == 0 and len(missing_keys) == 0

        result = ValidationResult(
            valid=valid, errors=errors, warnings=warnings, missing_keys=missing_keys
        )

        if valid:
            logger.info("✅ Configuration validation passed")
        else:
            logger.error(f"❌ Configuration validation failed: {len(errors)} errors")

        return result

    def check_required_keys(self, config: Dict[str, Any]) -> List[str]:
        """
        Check for required keys in configuration.

        Args:
            config: Configuration dictionary

        Returns:
            List of missing required keys (empty if all present)
        """
        missing = []
        for key in self.REQUIRED_KEYS:
            if key not in config:
                missing.append(key)

        if missing:
            logger.warning(f"Missing required keys: {missing}")

        return missing


def main():
    """Test the unit."""
    unit = ConfigValidator()

    # Test 1: Valid configuration
    print("Test 1: Valid configuration")
    valid_config = {
        "project_name": "openproject",
        "environment": "production",
        "services": ["web", "db"],
        "version": "1.0.0",
    }
    result = unit.validate(valid_config)
    print(f"  {result}")
    print(f"  Errors: {result.errors}")
    print(f"  Warnings: {result.warnings}")

    # Test 2: Invalid configuration (missing keys)
    print("\nTest 2: Invalid configuration (missing keys)")
    invalid_config = {"project_name": "openproject"}
    result = unit.validate(invalid_config)
    print(f"  {result}")
    print(f"  Missing keys: {result.missing_keys}")

    # Test 3: Configuration with warnings
    print("\nTest 3: Configuration with warnings")
    warning_config = {
        "project_name": "openproject",
        "environment": "custom",
        "services": [],
    }
    result = unit.validate(warning_config)
    print(f"  {result}")
    print(f"  Warnings: {result.warnings}")

    print(f"\n{unit.__class__.__name__} tests complete")
