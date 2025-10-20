#!/usr/bin/env python3
"""
Deployment Execution
Sequence: 40
Status: IMPLEMENTED

Execute Docker Compose deployment
"""

from pathlib import Path
from typing import Dict, Any
import logging

from phases.libraries.config.env_generator import EnvGenerator
from phases.libraries.docker.image_puller import ImagePuller
from phases.libraries.docker.compose_executor import ComposeExecutor
from phases.libraries.docker.startup_monitor import StartupMonitor

logger = logging.getLogger(__name__)


class Phase4DeploymentOrchestrator:
    """
    Deployment Execution

    Status: IMPLEMENTED
    Sequence: 40

    Execute Docker Compose deployment
    """

    PHASE_ID = "phase_4_deployment"
    PHASE_SEQUENCE = 40
    PHASE_NAME = "Deployment Execution"

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        Initialize Deployment Execution.

        Args:
            project_root: Root directory of the project
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config
        self.phase_dir = project_root / "runtime" / "phase_4_deployment"
        self.outputs_dir = self.phase_dir / "outputs"

        # Ensure outputs directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Deployment Execution.

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

        try:
            # Step 10: Generate Environment File
            step_result = self._step_10_generate_environment_file(context)
            if step_result["status"] == "error":
                result["status"] = "error"
                result["messages"].extend(step_result.get("messages", []))
                return result
            result["artifacts"].update(step_result.get("artifacts", {}))
            context.update(step_result.get("artifacts", {}))

            # Step 20: Pull Docker Images
            step_result = self._step_20_pull_docker_images(context)
            if step_result["status"] == "error":
                result["status"] = "error"
                result["messages"].extend(step_result.get("messages", []))
                return result
            result["artifacts"].update(step_result.get("artifacts", {}))
            context.update(step_result.get("artifacts", {}))

            # Step 30: Execute Compose Up
            step_result = self._step_30_execute_compose_up(context)
            if step_result["status"] == "error":
                result["status"] = "error"
                result["messages"].extend(step_result.get("messages", []))
                return result
            result["artifacts"].update(step_result.get("artifacts", {}))
            context.update(step_result.get("artifacts", {}))

            # Step 40: Monitor Service Startup
            step_result = self._step_40_monitor_service_startup(context)
            if step_result["status"] == "error":
                result["status"] = "error"
                result["messages"].extend(step_result.get("messages", []))
                return result
            result["artifacts"].update(step_result.get("artifacts", {}))

            result["messages"].append("✅ Phase 4: Deployment Execution complete")

        except Exception as e:
            logger.error(f"Phase 4 failed: {e}", exc_info=True)
            result["status"] = "error"
            result["messages"].append(f"Phase 4 failed: {str(e)}")

        return result

    def _step_10_generate_environment_file(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 10: Generate Environment File

        Convert configuration to .env format for Docker Compose
        """
        logger.info(f"  Step 10: Generate Environment File")

        try:
            # Get validated config from context
            validated_config = context.get("validated_config")
            if not validated_config:
                return {
                    "status": "error",
                    "artifacts": {},
                    "messages": ["No validated_config found in context"],
                }

            # Get project name and environment
            project_name = validated_config.get("project_name", "myproject")
            environment = validated_config.get("environment", "production")

            # Determine output path
            env_file_path = self.outputs_dir / f".env.{environment}"

            # Generate environment file
            generator = EnvGenerator()
            generator.generate(validated_config, env_file_path)

            # Check if file was created
            if not env_file_path.exists():
                return {
                    "status": "error",
                    "artifacts": {},
                    "messages": [
                        f"Failed to generate environment file: {env_file_path}"
                    ],
                }

            # Count lines (excluding comments and empty lines)
            with open(env_file_path) as f:
                lines = f.readlines()
            variable_count = sum(
                1 for line in lines if line.strip() and not line.strip().startswith("#")
            )

            logger.info(f"    ✅ Generated environment file: {env_file_path}")
            logger.info(f"       Variables: {variable_count}")

            return {
                "status": "success",
                "artifacts": {
                    "env_file_path": str(env_file_path),
                    "env_variable_count": variable_count,
                },
                "messages": [f"Generated {variable_count} environment variables"],
            }

        except Exception as e:
            logger.error(f"Step 10 failed: {e}", exc_info=True)
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Step 10 failed: {str(e)}"],
            }

    def _step_20_pull_docker_images(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 20: Pull Docker Images

        Pull required Docker images (if requested)
        """
        logger.info(f"  Step 20: Pull Docker Images")

        try:
            # Get validated config from context
            validated_config = context.get("validated_config")
            if not validated_config:
                return {
                    "status": "error",
                    "artifacts": {},
                    "messages": ["No validated_config found in context"],
                }

            # Check if image pulling is enabled (default: True)
            pull_images = validated_config.get("deployment", {}).get(
                "pull_images", True
            )

            if not pull_images:
                logger.info(f"    ⏭️  Image pulling disabled, skipping")
                return {
                    "status": "success",
                    "artifacts": {"images_pulled": False},
                    "messages": ["Image pulling disabled"],
                }

            # Extract image names from services
            images = []
            services = validated_config.get("services", {})
            for service_name, service_config in services.items():
                if "image" in service_config:
                    images.append(service_config["image"])

            if not images:
                logger.info(f"    ⏭️  No images to pull")
                return {
                    "status": "success",
                    "artifacts": {"images_pulled": False},
                    "messages": ["No images to pull"],
                }

            # Pull images
            logger.info(f"    📥 Pulling {len(images)} image(s)...")
            puller = ImagePuller()
            results = puller.pull_multiple(images)

            # Check results
            successful = [img for img, r in results.items() if r.success]
            already_exists = [
                img for img, r in results.items() if r.success and r.already_exists
            ]
            failed = [img for img, r in results.items() if not r.success]

            if failed:
                return {
                    "status": "error",
                    "artifacts": {
                        "images_pulled": True,
                        "pull_results": {
                            img: {"success": r.success, "error": r.error}
                            for img, r in results.items()
                        },
                    },
                    "messages": [
                        f"Failed to pull {len(failed)} image(s): {', '.join(failed)}"
                    ],
                }

            logger.info(f"    ✅ Pulled {len(successful)} image(s)")
            if already_exists:
                logger.info(f"       {len(already_exists)} already up-to-date")

            return {
                "status": "success",
                "artifacts": {
                    "images_pulled": True,
                    "pull_results": {
                        img: {"success": r.success, "already_exists": r.already_exists}
                        for img, r in results.items()
                    },
                },
                "messages": [f"Pulled {len(successful)} image(s)"],
            }

        except Exception as e:
            logger.error(f"Step 20 failed: {e}", exc_info=True)
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Step 20 failed: {str(e)}"],
            }

    def _step_30_execute_compose_up(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 30: Execute Compose Up

        Run docker compose up -d to start services
        """
        logger.info(f"  Step 30: Execute Compose Up")

        try:
            # Get compose file paths from context
            rendered_compose = context.get("rendered_docker_compose")
            if not rendered_compose:
                return {
                    "status": "error",
                    "artifacts": {},
                    "messages": ["No rendered_docker_compose found in context"],
                }

            # Convert to absolute path to avoid path issues
            compose_path = Path(rendered_compose)
            if not compose_path.is_absolute():
                compose_path = self.project_root / compose_path

            # Get validated config for project name
            validated_config = context.get("validated_config")
            project_name = (
                validated_config.get("project_name", "myproject")
                if validated_config
                else "myproject"
            )

            # Get environment file path
            env_file = context.get("env_file_path")

            # Initialize compose executor with config (use absolute paths)
            executor_config = {
                "compose_file": str(compose_path),
                "project_name": project_name,
                "working_dir": str(compose_path.parent),
            }
            executor = ComposeExecutor(executor_config)

            # Build up command with options
            up_command = "up -d"
            if env_file:
                up_command = f"--env-file {env_file} {up_command}"

            # Execute compose up
            logger.info(f"    🚀 Starting services with docker compose up...")
            result = executor.execute(up_command, capture_output=True, timeout=300)

            if not result.success:
                return {
                    "status": "error",
                    "artifacts": {
                        "compose_result": {
                            "success": result.success,
                            "command": result.command,
                            "stderr": result.stderr,
                            "error": result.error,
                        }
                    },
                    "messages": [
                        f"Docker compose up failed: {result.error or result.stderr}"
                    ],
                }

            logger.info(f"    ✅ Services started successfully")
            if result.stdout:
                logger.debug(f"       Output: {result.stdout[:200]}")

            return {
                "status": "success",
                "artifacts": {
                    "compose_result": {
                        "success": result.success,
                        "command": result.command,
                        "stdout": result.stdout,
                    },
                    "project_name": project_name,
                    "compose_file": rendered_compose,
                },
                "messages": ["Services started successfully"],
            }

        except Exception as e:
            logger.error(f"Step 30 failed: {e}", exc_info=True)
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Step 30 failed: {str(e)}"],
            }

    def _step_40_monitor_service_startup(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 40: Monitor Service Startup

        Monitor services starting and capture initial logs
        """
        logger.info(f"  Step 40: Monitor Service Startup")

        try:
            # Get project name and compose file from context
            project_name = context.get("project_name")
            compose_file = context.get("compose_file")

            if not project_name or not compose_file:
                return {
                    "status": "error",
                    "artifacts": {},
                    "messages": ["Missing project_name or compose_file in context"],
                }

            # Get validated config for timeout settings
            validated_config = context.get("validated_config")
            startup_timeout = 120  # Default 2 minutes
            if validated_config:
                startup_timeout = validated_config.get("deployment", {}).get(
                    "startup_timeout", 120
                )

            # Initialize startup monitor with config
            monitor_config = {
                "compose_file": compose_file,
                "project_name": project_name,
            }
            monitor = StartupMonitor(monitor_config)

            # Monitor startup
            logger.info(
                f"    ⏳ Monitoring service startup (timeout: {startup_timeout}s)..."
            )
            result = monitor.monitor(
                timeout=startup_timeout, check_health=True, interval=2
            )

            if not result.success:
                # Log container states for debugging
                logger.error(f"    ❌ Startup monitoring failed: {result.error}")
                for container in result.containers:
                    logger.error(
                        f"       {container.name}: {container.state} (health: {container.health})"
                    )

                return {
                    "status": "error",
                    "artifacts": {
                        "monitor_result": {
                            "success": result.success,
                            "all_running": result.all_running,
                            "all_healthy": result.all_healthy,
                            "elapsed_time": result.elapsed_time,
                            "containers": [
                                {
                                    "name": c.name,
                                    "state": c.state,
                                    "health": c.health,
                                    "uptime": c.uptime,
                                }
                                for c in result.containers
                            ],
                            "error": result.error,
                        }
                    },
                    "messages": [f"Service startup failed: {result.error}"],
                }

            # Log success
            logger.info(
                f"    ✅ All services started successfully ({result.elapsed_time:.1f}s)"
            )
            for container in result.containers:
                status_icon = "✅" if container.state == "running" else "❌"
                health_status = (
                    f" (health: {container.health})"
                    if container.health != "none"
                    else ""
                )
                logger.info(
                    f"       {status_icon} {container.name}: {container.state}{health_status}"
                )

            return {
                "status": "success",
                "artifacts": {
                    "monitor_result": {
                        "success": result.success,
                        "all_running": result.all_running,
                        "all_healthy": result.all_healthy,
                        "elapsed_time": result.elapsed_time,
                        "containers": [
                            {
                                "name": c.name,
                                "state": c.state,
                                "health": c.health,
                                "uptime": c.uptime,
                            }
                            for c in result.containers
                        ],
                    }
                },
                "messages": [f"All services running ({result.elapsed_time:.1f}s)"],
            }

        except Exception as e:
            logger.error(f"Step 40 failed: {e}", exc_info=True)
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Step 40 failed: {str(e)}"],
            }


def main():
    """Test the phase orchestrator."""
    from pathlib import Path
    import yaml

    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    project_root = Path(__file__).parent.parent.parent
    config = {}

    # Create test context with sample data
    context = {
        "validated_config": {
            "project_name": "test-deployment",
            "environment": "development",
            "services": {
                "web": {"image": "nginx:alpine", "ports": ["80:80"]},
                "redis": {"image": "redis:alpine"},
            },
            "deployment": {"pull_images": True, "startup_timeout": 60},
        },
        # Mock rendered compose file path (would come from Phase 2)
        "rendered_docker_compose": str(project_root / "docker-compose.yml"),
    }

    orchestrator = Phase4DeploymentOrchestrator(project_root, config)

    logger.info("\n" + "=" * 70)
    logger.info("Testing Phase 4 Deployment Orchestrator")
    logger.info("=" * 70)
    logger.info(f"Project root: {project_root}")
    logger.info(f"Outputs dir: {orchestrator.outputs_dir}")
    logger.info("")

    # Note: This is a dry-run test - actual deployment would require:
    # - Valid docker-compose.yml file
    # - Docker daemon running
    # - Proper Phase 1 & 2 artifacts in context

    logger.info("✅ Phase 4 orchestrator initialized successfully")
    logger.info("\nTo test full deployment flow:")
    logger.info("  1. Ensure Docker is running")
    logger.info("  2. Run Phases 1 & 2 first to generate artifacts")
    logger.info("  3. Pass their context to Phase 4")
    logger.info("")
    logger.info(f"Phase ID: {orchestrator.PHASE_ID}")
    logger.info(f"Phase Sequence: {orchestrator.PHASE_SEQUENCE}")
    logger.info(f"Phase Name: {orchestrator.PHASE_NAME}")


if __name__ == "__main__":
    main()
