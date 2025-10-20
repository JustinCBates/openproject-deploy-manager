#!/usr/bin/env python3
"""
ContainerHealthChecker Unit

Check Docker container health status using docker inspect
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Container health status"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    NO_HEALTHCHECK = "none"
    UNKNOWN = "unknown"


@dataclass
class ContainerHealth:
    """Container health information"""

    container_id: str
    container_name: str
    status: HealthStatus
    running: bool
    exit_code: Optional[int]
    health_check_defined: bool
    last_health_output: Optional[str]
    failing_streak: int
    test_command: Optional[List[str]]

    def is_healthy(self) -> bool:
        """Check if container is healthy"""
        if not self.running:
            return False
        if not self.health_check_defined:
            # No healthcheck defined - consider healthy if running
            return True
        return self.status == HealthStatus.HEALTHY


@dataclass
class HealthCheckResult:
    """Result of health check operation"""

    success: bool
    containers: List[ContainerHealth]
    healthy_count: int
    unhealthy_count: int
    total_count: int
    all_healthy: bool
    error: Optional[str] = None


class ContainerHealthChecker:
    """
    Check Docker container health using docker inspect

    Checks:
    - Container running status
    - Docker health check status
    - Exit codes
    - Health check output
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ContainerHealthChecker.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def check(
        self,
        project_name: Optional[str] = None,
        container_ids: Optional[List[str]] = None,
    ) -> HealthCheckResult:
        """
        Check container health

        Args:
            project_name: Filter by docker compose project name
            container_ids: Specific container IDs to check (if None, check all)

        Returns:
            HealthCheckResult with health status for all containers
        """
        try:
            # Get list of containers
            if container_ids:
                containers_to_check = container_ids
            elif project_name:
                containers_to_check = self._get_project_containers(project_name)
            else:
                # Check all running containers
                containers_to_check = self._get_all_containers()

            if not containers_to_check:
                logger.warning("No containers found to check")
                return HealthCheckResult(
                    success=True,
                    containers=[],
                    healthy_count=0,
                    unhealthy_count=0,
                    total_count=0,
                    all_healthy=True,
                )

            # Check health of each container
            health_statuses = []
            for container_id in containers_to_check:
                health = self._check_container(container_id)
                if health:
                    health_statuses.append(health)

            # Calculate stats
            healthy_count = sum(1 for h in health_statuses if h.is_healthy())
            unhealthy_count = len(health_statuses) - healthy_count
            all_healthy = unhealthy_count == 0

            logger.info(
                f"Health check complete: {healthy_count}/{len(health_statuses)} healthy"
            )

            return HealthCheckResult(
                success=True,
                containers=health_statuses,
                healthy_count=healthy_count,
                unhealthy_count=unhealthy_count,
                total_count=len(health_statuses),
                all_healthy=all_healthy,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthCheckResult(
                success=False,
                containers=[],
                healthy_count=0,
                unhealthy_count=0,
                total_count=0,
                all_healthy=False,
                error=str(e),
            )

    def _check_container(self, container_id: str) -> Optional[ContainerHealth]:
        """
        Check health of a single container

        Args:
            container_id: Container ID or name

        Returns:
            ContainerHealth object or None if check fails
        """
        try:
            # Run docker inspect
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse JSON
            inspect_data = json.loads(result.stdout)
            if not inspect_data:
                logger.warning(f"No inspect data for container: {container_id}")
                return None

            container_data = inspect_data[0]

            # Extract basic info
            container_name = container_data.get("Name", "").lstrip("/")
            state = container_data.get("State", {})
            running = state.get("Running", False)
            exit_code = state.get("ExitCode")

            # Extract health check info
            health_data = state.get("Health", {})
            health_check_config = container_data.get("Config", {}).get("Healthcheck")

            health_check_defined = health_check_config is not None
            test_command = (
                health_check_config.get("Test") if health_check_config else None
            )

            # Determine health status
            if health_check_defined:
                health_status_str = health_data.get("Status", "unknown")
                try:
                    health_status = HealthStatus(health_status_str)
                except ValueError:
                    health_status = HealthStatus.UNKNOWN

                # Get last health check output
                health_log = health_data.get("Log", [])
                last_output = health_log[-1].get("Output") if health_log else None
                failing_streak = health_data.get("FailingStreak", 0)
            else:
                health_status = HealthStatus.NO_HEALTHCHECK
                last_output = None
                failing_streak = 0

            return ContainerHealth(
                container_id=container_id,
                container_name=container_name,
                status=health_status,
                running=running,
                exit_code=exit_code,
                health_check_defined=health_check_defined,
                last_health_output=last_output,
                failing_streak=failing_streak,
                test_command=test_command,
            )

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to inspect container {container_id}: {e}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse inspect data for {container_id}: {e}")
            return None

    def _get_project_containers(self, project_name: str) -> List[str]:
        """Get all container IDs for a docker compose project"""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "-q",
                    "--filter",
                    f"label=com.docker.compose.project={project_name}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            container_ids = result.stdout.strip().split("\n")
            return [cid for cid in container_ids if cid]
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get containers for project {project_name}: {e}")
            return []

    def _get_all_containers(self) -> List[str]:
        """Get all running container IDs"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-q"], capture_output=True, text=True, check=True
            )
            container_ids = result.stdout.strip().split("\n")
            return [cid for cid in container_ids if cid]
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get all containers: {e}")
            return []


def main():
    """Test the unit."""
    logging.basicConfig(level=logging.INFO)

    checker = ContainerHealthChecker()

    # Test with all containers
    print("Checking all running containers...")
    result = checker.check()

    print(f"\nHealth Check Results:")
    print(f"Total containers: {result.total_count}")
    print(f"Healthy: {result.healthy_count}")
    print(f"Unhealthy: {result.unhealthy_count}")
    print(f"All healthy: {result.all_healthy}")

    for container in result.containers:
        status_icon = "✅" if container.is_healthy() else "❌"
        print(
            f"{status_icon} {container.container_name}: {container.status.value} (running: {container.running})"
        )


if __name__ == "__main__":
    main()
