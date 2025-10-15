#!/usr/bin/env python3
"""
EnvGenerator Unit

Generate .env file from configuration
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class EnvGenerator:
    """
    Generate .env file from configuration
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize EnvGenerator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def generate(self, config: Dict[str, Any], output_path: Path) -> None:
        """
        Generate .env file from configuration dictionary.
        
        Args:
            config: Configuration dictionary (can be nested)
            output_path: Path where .env file will be written
            
        Raises:
            ValueError: If config contains invalid values for .env format
        """
        output_path = Path(output_path)
        logger.info(f"Generating .env file: {output_path}")
        
        # Flatten nested config and convert to KEY=VALUE format
        env_lines = []
        env_lines.append("# Generated .env file")
        env_lines.append(f"# Generated from configuration")
        env_lines.append("")
        
        # Process config recursively
        self._process_dict(config, env_lines)
        
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        content = '\n'.join(env_lines) + '\n'
        output_path.write_text(content)
        
        logger.info(f"✅ Generated .env file with {len(env_lines)-3} variables: {output_path}")
    
    def _process_dict(self, data: Dict[str, Any], lines: List[str], prefix: str = "") -> None:
        """
        Recursively process dictionary and generate env variables.
        
        Args:
            data: Dictionary to process
            lines: List to append env lines to
            prefix: Current key prefix for nested dicts
        """
        for key, value in data.items():
            # Create env variable name (convert to uppercase, use underscores)
            env_key = self._to_env_key(key, prefix)
            
            if isinstance(value, dict):
                # Recursively process nested dict
                self._process_dict(value, lines, env_key)
            elif isinstance(value, list):
                # Convert list to comma-separated string
                env_value = ','.join(str(v) for v in value)
                lines.append(f"{env_key}={env_value}")
            elif isinstance(value, bool):
                # Convert bool to lowercase string
                lines.append(f"{env_key}={str(value).lower()}")
            elif value is None:
                # Skip None values
                logger.debug(f"Skipping None value for {env_key}")
            else:
                # String, int, float - convert to string
                # Quote if contains spaces
                env_value = str(value)
                if ' ' in env_value or '"' in env_value:
                    env_value = f'"{env_value}"'
                lines.append(f"{env_key}={env_value}")
    
    def _to_env_key(self, key: str, prefix: str = "") -> str:
        """
        Convert a key to environment variable format.
        
        Args:
            key: Original key
            prefix: Prefix from parent keys
            
        Returns:
            Environment variable name (UPPERCASE_WITH_UNDERSCORES)
        """
        # Convert to uppercase and replace hyphens with underscores
        env_key = key.upper().replace('-', '_').replace(' ', '_')
        
        if prefix:
            return f"{prefix}_{env_key}"
        return env_key


def main():
    """Test the unit."""
    import tempfile
    
    unit = EnvGenerator()
    
    # Test configuration
    config = {
        'project_name': 'openproject',
        'environment': 'production',
        'database': {
            'host': 'localhost',
            'port': 5432,
            'name': 'openproject_db',
            'user': 'postgres'
        },
        'services': ['web', 'db', 'cache'],
        'features': {
            'enable_ssl': True,
            'debug_mode': False
        },
        'app_url': 'https://example.com'
    }
    
    # Generate .env file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        output_path = Path(f.name)
    
    try:
        unit.generate(config, output_path)
        
        # Read and display
        content = output_path.read_text()
        print("Generated .env file:")
        print("=" * 60)
        print(content)
        print("=" * 60)
        
        # Verify key variables exist
        assert 'PROJECT_NAME=openproject' in content
        assert 'DATABASE_HOST=localhost' in content
        assert 'SERVICES=web,db,cache' in content
        assert 'FEATURES_ENABLE_SSL=true' in content
        
        print("\n✅ All tests passed!")
        
    finally:
        output_path.unlink()
    
    print(f"\n{unit.__class__.__name__} tests complete")


if __name__ == '__main__':
    main()
