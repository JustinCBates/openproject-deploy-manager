#!/usr/bin/env python3
"""
JinjaRenderer Unit

Render Jinja2 templates
"""

from typing import Dict, Any, Optional
import logging
from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateSyntaxError,
    UndefinedError,
)

logger = logging.getLogger(__name__)


class JinjaRenderer:
    """
    Render Jinja2 templates
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize JinjaRenderer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.template_dir = config.get("template_dir") if config else None

        # Create Jinja2 environment
        if self.template_dir:
            self.env = Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=False,  # We're generating config files, not HTML
                keep_trailing_newline=True,
            )
        else:
            self.env = Environment(autoescape=False, keep_trailing_newline=True)

    def render(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template string with context.

        Args:
            template: Template string (Jinja2 syntax)
            context: Dictionary of variables to use in rendering

        Returns:
            Rendered string

        Raises:
            TemplateSyntaxError: If template has syntax errors
            UndefinedError: If template references undefined variables
        """
        logger.debug(f"Rendering template with {len(context)} context variables")

        try:
            tmpl = Template(template, autoescape=False, keep_trailing_newline=True)
            rendered = tmpl.render(**context)
            logger.debug(f"Rendered template: {len(rendered)} characters")
            return rendered
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}")
            raise
        except UndefinedError as e:
            logger.error(f"Undefined variable in template: {e}")
            raise
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise

    def render_to_file(
        self, template: str, output: Path, context: Dict[str, Any]
    ) -> None:
        """
        Render template and write to file.

        Args:
            template: Template string or path to template file
            output: Path where rendered content will be written
            context: Dictionary of variables to use in rendering

        Raises:
            TemplateSyntaxError: If template has syntax errors
        """
        output = Path(output)
        logger.info(f"Rendering template to: {output}")

        # Check if template is a file path
        template_path = Path(template)
        if template_path.exists():
            logger.debug(f"Loading template from file: {template_path}")
            template_str = template_path.read_text()
        else:
            # Assume it's a template string
            template_str = template

        # Render template
        rendered = self.render(template_str, context)

        # Create output directory if needed
        output.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        output.write_text(rendered)
        logger.info(f"✅ Template rendered successfully: {output}")


def main():
    """Test the unit."""
    unit = JinjaRenderer()

    # Test 1: Simple template rendering
    print("Test 1: Simple template rendering")
    template = "Hello {{ name }}! Environment: {{ env }}"
    context = {"name": "OpenProject", "env": "production"}
    result = unit.render(template, context)
    print(f"  Template: {template}")
    print(f"  Result: {result}")

    # Test 2: Template with loops and conditions
    print("\nTest 2: Template with loops")
    template = """
Services:
{% for service in services %}
  - {{ service }}
{% endfor %}
"""
    context = {"services": ["web", "db", "cache"]}
    result = unit.render(template, context)
    print(f"  Result:{result}")

    # Test 3: Render to file
    print("\nTest 3: Render to file")
    import tempfile

    template = "# Generated config\nproject: {{ project }}\nversion: {{ version }}"
    context = {"project": "openproject", "version": "1.0.0"}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        output_path = Path(f.name)

    try:
        unit.render_to_file(template, output_path, context)
        content = output_path.read_text()
        print(f"  File content:\n{content}")
    finally:
        output_path.unlink()

    print(f"\n{unit.__class__.__name__} tests complete")
