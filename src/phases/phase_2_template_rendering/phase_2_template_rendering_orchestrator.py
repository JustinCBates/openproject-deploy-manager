#!/usr/bin/env python3
"""
Template Rendering
Sequence: 20
Status: IMPLEMENTED

Render deployment templates with configuration values
"""

from pathlib import Path
from typing import Dict, Any
import logging

from phases.libraries.config.variable_extractor import VariableExtractor
from phases.libraries.templates.jinja_renderer import JinjaRenderer
from phases.libraries.templates.template_validator import TemplateValidator

logger = logging.getLogger(__name__)


class Phase2TemplateRenderingOrchestrator:
    """
    Template Rendering

    Status: IMPLEMENTED
    Sequence: 20

    Render deployment templates with configuration values
    """

    PHASE_ID = "phase_2_template_rendering"
    PHASE_SEQUENCE = 20
    PHASE_NAME = "Template Rendering"

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        Initialize Template Rendering.

        Args:
            project_root: Root directory of the project
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config
        self.phase_dir = project_root / "runtime" / "phase_2_template_rendering"
        self.outputs_dir = self.phase_dir / "outputs"

        # Ensure outputs directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Template Rendering.

        Args:
            context: Execution context from previous phases

        Returns:
            Dict with phase results and artifacts
        """
        logger.info("=" * 70)
        logger.info(f"{self.PHASE_NAME}")
        logger.info("=" * 70)

        result = {
            "phase_id": self.PHASE_ID,
            "status": "success",
            "artifacts": {},
            "messages": [],
        }

        # Execute steps in sequence with error handling
        steps = [
            ("Step 10", self._step_10_extract_template_variables),
            ("Step 20", self._step_20_render_caddyfile),
            ("Step 30", self._step_30_render_docker_compose_override),
            ("Step 40", self._step_40_validate_rendered_templates),
        ]

        for step_name, step_func in steps:
            step_result = step_func(context)

            # Update context with artifacts for next steps
            context.update(step_result.get("artifacts", {}))

            # Update result artifacts
            result["artifacts"].update(step_result.get("artifacts", {}))

            # Collect messages
            result["messages"].extend(step_result.get("messages", []))

            # Check step status
            step_status = step_result.get("status", "success")

            if step_status == "error":
                logger.error(f"  ❌ {step_name} failed - aborting phase")
                result["status"] = "error"
                return result
            elif step_status == "warning" and result["status"] == "success":
                # Downgrade to warning but continue
                result["status"] = "warning"

        logger.info(f"✅ {self.PHASE_NAME} complete (status: {result['status']})")
        return result

    def _step_10_extract_template_variables(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 10: Extract Template Variables

        Extract and prepare variables for template rendering
        """
        logger.info(f"  Step 10: Extract Template Variables")

        try:
            # Get validated config from context (from Phase 1)
            config = (
                context.get("validated_config")
                or context.get("loaded_config")
                or self.config
            )

            if not config:
                logger.warning("No configuration available for variable extraction")
                return {
                    "status": "warning",
                    "artifacts": {"template_variables": {}, "config": {}},
                    "messages": ["No configuration available, using empty variables"],
                }

            # Extract and flatten variables
            extractor = VariableExtractor()
            variables = extractor.extract(config)

            # Add any template_vars from config directly
            if "template_vars" in config:
                variables.update(config["template_vars"])

            # ALSO include the full config for templates that need nested structure
            # Templates can use either flattened vars OR access config.services etc.
            variables["config"] = config

            # Add top-level keys directly for convenience
            for key in [
                "project_name",
                "environment",
                "services",
                "network",
                "volumes",
            ]:
                if key in config:
                    variables[key] = config[key]

            logger.info(f"✅ Extracted {len(variables)} template variables")

            return {
                "status": "success",
                "artifacts": {"template_variables": variables, "config": config},
                "messages": [f"Extracted {len(variables)} template variables"],
            }

        except Exception as e:
            logger.error(f"  ❌ Failed to extract template variables: {str(e)}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Failed to extract template variables: {str(e)}"],
            }

    def _step_20_render_caddyfile(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 20: Render Caddyfile

        Render Caddyfile template for reverse proxy
        """
        logger.info(f"  Step 20: Render Caddyfile")

        try:
            # Get template variables from context
            variables = context.get("template_variables", {})

            # Define Caddyfile template path (check multiple locations)
            template_locations = [
                self.project_root.parent / "templates" / "Caddyfile.j2",
                self.project_root / "templates" / "Caddyfile.j2",
                self.phase_dir / "templates" / "Caddyfile.j2",
            ]

            template_path = None
            for location in template_locations:
                if location.exists():
                    template_path = location
                    break

            if not template_path:
                logger.info("  ⚠️  Caddyfile template not found, skipping")
                return {
                    "status": "success",
                    "artifacts": {},
                    "messages": ["Caddyfile template not found, skipped"],
                }

            # Render template
            renderer = JinjaRenderer()
            output_path = self.outputs_dir / "Caddyfile"
            renderer.render_to_file(str(template_path), output_path, variables)

            # Read rendered content
            rendered_content = output_path.read_text()

            logger.info(f"  ✅ Rendered Caddyfile to {output_path}")

            return {
                "status": "success",
                "artifacts": {
                    "caddyfile_path": str(output_path),
                    "caddyfile_content": rendered_content,
                },
                "messages": [f"Rendered Caddyfile ({len(rendered_content)} bytes)"],
            }

        except Exception as e:
            logger.error(f"  ❌ Failed to render Caddyfile: {str(e)}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Failed to render Caddyfile: {str(e)}"],
            }

    def _step_30_render_docker_compose_override(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 30: Render Docker Compose Override

        Render docker-compose.override.yml with dynamic settings
        """
        logger.info(f"  Step 30: Render Docker Compose Override")

        try:
            # Get template variables from context
            variables = context.get("template_variables", {})

            # Define docker-compose override template path
            template_locations = [
                self.project_root.parent
                / "templates"
                / "docker-compose.override.yml.j2",
                self.project_root / "templates" / "docker-compose.override.yml.j2",
                self.phase_dir / "templates" / "docker-compose.override.yml.j2",
            ]

            template_path = None
            for location in template_locations:
                if location.exists():
                    template_path = location
                    break

            if not template_path:
                logger.info("  ⚠️  Docker Compose override template not found, skipping")
                return {
                    "status": "success",
                    "artifacts": {},
                    "messages": ["Docker Compose override template not found, skipped"],
                }

            # Render template
            renderer = JinjaRenderer()
            output_path = self.outputs_dir / "docker-compose.override.yml"
            renderer.render_to_file(str(template_path), output_path, variables)

            # Read rendered content
            rendered_content = output_path.read_text()

            logger.info(f"  ✅ Rendered docker-compose.override.yml to {output_path}")

            return {
                "status": "success",
                "artifacts": {
                    "compose_override_path": str(output_path),
                    "compose_override_content": rendered_content,
                },
                "messages": [
                    f"Rendered docker-compose.override.yml ({len(rendered_content)} bytes)"
                ],
            }

        except Exception as e:
            logger.error(f"  ❌ Failed to render Docker Compose override: {str(e)}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Failed to render Docker Compose override: {str(e)}"],
            }

    def _step_40_validate_rendered_templates(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 40: Validate Rendered Templates

        Validate syntax and completeness of rendered templates
        """
        logger.info(f"  Step 40: Validate Rendered Templates")

        try:
            validator = TemplateValidator()
            validation_results = []
            all_valid = True

            # Validate Caddyfile if rendered
            if "caddyfile_content" in context:
                caddyfile_result = validator.validate(
                    context["caddyfile_content"], type="caddyfile"
                )
                validation_results.append(("Caddyfile", caddyfile_result))
                if not caddyfile_result.valid:
                    all_valid = False
                    logger.warning(
                        f"  ⚠️  Caddyfile validation issues: {caddyfile_result.errors}"
                    )
                else:
                    logger.info(f"  ✅ Caddyfile validated")

            # Validate Docker Compose override if rendered
            if "compose_override_content" in context:
                compose_result = validator.validate(
                    context["compose_override_content"], type="docker-compose"
                )
                validation_results.append(
                    ("docker-compose.override.yml", compose_result)
                )
                if not compose_result.valid:
                    all_valid = False
                    logger.warning(
                        f"  ⚠️  Docker Compose validation issues: {compose_result.errors}"
                    )
                else:
                    logger.info(f"  ✅ docker-compose.override.yml validated")

            if not validation_results:
                logger.info("  ℹ️  No templates to validate")
                return {
                    "status": "success",
                    "artifacts": {},
                    "messages": ["No templates rendered to validate"],
                }

            # Prepare messages
            messages = []
            for name, result in validation_results:
                if result.valid:
                    messages.append(f"{name}: valid")
                else:
                    messages.append(f"{name}: {len(result.errors)} errors")
                    messages.extend([f"  - {err}" for err in result.errors])

            if all_valid:
                logger.info(
                    f"  ✅ All {len(validation_results)} templates validated successfully"
                )
                status = "success"
            else:
                logger.warning(f"  ⚠️  Some templates have validation issues")
                status = "warning"

            return {
                "status": status,
                "artifacts": {
                    "validation_results": validation_results,
                    "all_templates_valid": all_valid,
                },
                "messages": messages,
            }

        except Exception as e:
            logger.error(f"  ❌ Failed to validate templates: {str(e)}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Failed to validate templates: {str(e)}"],
            }


def main():
    """Test the phase orchestrator."""
    from pathlib import Path
    import logging

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    project_root = Path(__file__).parent.parent.parent

    # Test with sample config (simulate Phase 1 context)
    config_path = project_root.parent / "test_config.yaml"

    # Load test config to simulate Phase 1 output
    if config_path.exists():
        from phases.libraries.config.config_loader import ConfigLoader

        loader = ConfigLoader()
        loaded_config = loader.load(config_path)
    else:
        loaded_config = {
            "project_name": "test-deployment",
            "environment": "development",
            "services": {"web": {"port": 8080}},
        }

    config = {}
    context = {"validated_config": loaded_config, "loaded_config": loaded_config}

    logger.info(f"Testing Phase 2 Template Rendering Orchestrator")
    logger.info(f"Config loaded: {len(loaded_config)} keys")
    logger.info("=" * 70)

    orchestrator = Phase2TemplateRenderingOrchestrator(project_root, config)
    result = orchestrator.execute(context)

    logger.info("=" * 70)
    logger.info(f"Phase Status: {result['status']}")
    logger.info(f"Messages: {len(result.get('messages', []))}")
    logger.info(f"Artifacts: {list(result.get('artifacts', {}).keys())}")

    if result["status"] == "error":
        logger.error("\n❌ Phase failed with errors:")
        for msg in result.get("messages", []):
            logger.error(f"  - {msg}")
    elif result["status"] == "warning":
        logger.warning("\n⚠️  Phase completed with warnings:")
        for msg in result.get("messages", []):
            logger.warning(f"  - {msg}")
    else:
        logger.info("\n✅ Phase completed successfully!")
        if result.get("messages"):
            for msg in result.get("messages", []):
                logger.info(f"  - {msg}")


if __name__ == "__main__":
    main()
