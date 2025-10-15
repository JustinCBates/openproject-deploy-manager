#!/usr/bin/env python3
"""
TemplateValidator Unit

Validate rendered template syntax
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
import yaml

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of template validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    
    def __str__(self):
        if self.valid:
            return "✅ Template valid"
        return f"❌ Template invalid: {len(self.errors)} errors"


class TemplateValidator:
    """
    Validate rendered template syntax
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize TemplateValidator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def validate(self, content: str, type: str) -> ValidationResult:
        """
        Validate rendered template content based on type.
        
        Args:
            content: Rendered template content
            type: Type of content ('yaml', 'docker-compose', 'env', 'json')
            
        Returns:
            ValidationResult with validation status
        """
        logger.debug(f"Validating template as type: {type}")
        
        errors = []
        warnings = []
        
        try:
            if type in ['yaml', 'docker-compose']:
                self._validate_yaml(content, errors, warnings)
            elif type == 'env':
                self._validate_env(content, errors, warnings)
            elif type == 'json':
                self._validate_json(content, errors, warnings)
            else:
                warnings.append(f"Unknown template type '{type}', skipping validation")
        except Exception as e:
            errors.append(f"Validation exception: {e}")
        
        valid = len(errors) == 0
        
        if valid:
            logger.info(f"✅ Template validation passed ({type})")
        else:
            logger.error(f"❌ Template validation failed ({type}): {len(errors)} errors")
        
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
    
    def _validate_yaml(self, content: str, errors: List[str], warnings: List[str]) -> None:
        """Validate YAML content"""
        try:
            data = yaml.safe_load(content)
            if data is None:
                warnings.append("YAML content is empty")
            elif not isinstance(data, dict):
                warnings.append(f"YAML root is {type(data).__name__}, expected dict")
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {e}")
    
    def _validate_env(self, content: str, errors: List[str], warnings: List[str]) -> None:
        """Validate .env file content"""
        line_num = 0
        for line in content.splitlines():
            line_num += 1
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for KEY=VALUE format
            if '=' not in line:
                errors.append(f"Line {line_num}: Missing '=' in variable assignment")
            else:
                key, value = line.split('=', 1)
                key = key.strip()
                
                # Validate key format
                if not key:
                    errors.append(f"Line {line_num}: Empty variable name")
                elif not key.replace('_', '').replace('-', '').isalnum():
                    warnings.append(f"Line {line_num}: Unusual variable name: {key}")
    
    def _validate_json(self, content: str, errors: List[str], warnings: List[str]) -> None:
        """Validate JSON content"""
        import json
        try:
            data = json.loads(content)
            if not isinstance(data, (dict, list)):
                warnings.append(f"JSON root is {type(data).__name__}")
        except json.JSONDecodeError as e:
            errors.append(f"JSON syntax error: {e}")


def main():
    """Test the unit."""
    unit = TemplateValidator()
    
    # Test 1: Valid YAML
    print("Test 1: Valid YAML")
    yaml_content = """
project: openproject
services:
  - web
  - db
"""
    result = unit.validate(yaml_content, 'yaml')
    print(f"  {result}")
    
    # Test 2: Invalid YAML
    print("\nTest 2: Invalid YAML")
    invalid_yaml = """
project: test
  - invalid syntax
    - nested wrong
"""
    result = unit.validate(invalid_yaml, 'yaml')
    print(f"  {result}")
    print(f"  Errors: {result.errors}")
    
    # Test 3: Valid .env
    print("\nTest 3: Valid .env")
    env_content = """
# Database config
DB_HOST=localhost
DB_PORT=5432
DB_NAME=openproject
"""
    result = unit.validate(env_content, 'env')
    print(f"  {result}")
    
    # Test 4: Invalid .env
    print("\nTest 4: Invalid .env")
    invalid_env = """
DB_HOST=localhost
INVALID LINE WITHOUT EQUALS
DB_PORT=5432
"""
    result = unit.validate(invalid_env, 'env')
    print(f"  {result}")
    print(f"  Errors: {result.errors}")
    
    print(f"\n{unit.__class__.__name__} tests complete")
