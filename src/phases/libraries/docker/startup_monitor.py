#!/usr/bin/env python3
"""
StartupMonitor Unit

Monitor Docker container startup with timeout and health checking
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging
import subprocess
import time
import json

logger = logging.getLogger(__name__)


@dataclass
class ContainerStatus:
    """Status of a Docker container"""

    name: str
    state: str  # running, exited, created, etc.
    health: str  # healthy, unhealthy, starting, none
    uptime: str

    def __str__(self) -> str:
        if self.state == "running":
            if self.health == "healthy":
                return f"✅ {self.name}: running ({self.health})"
            elif self.health == "starting":
                return f"🔄 {self.name}: running ({self.health})"
            else:
                return f"✅ {self.name}: running"
        return f"⚠️  {self.name}: {self.state}"


@dataclass
class MonitorResult:
    """Result of startup monitoring"""

    success: bool
    containers: List[ContainerStatus] = field(default_factory=list)
    all_running: bool = False
    all_healthy: bool = False
    elapsed_time: float = 0.0
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.success:
            return f"✅ All containers started ({len(self.containers)} containers, {self.elapsed_time:.1f}s)"
        return f"❌ Startup failed: {self.error}"


class StartupMonitor:
    """
    Monitor Docker container startup with health checking
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize StartupMonitor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.project_name = config.get("project_name") if config else None

    def monitor(
        self, timeout: int = 120, check_health: bool = True, interval: int = 2
    ) -> MonitorResult:
        """
        Monitor container startup until all are running or timeout.

        Args:
            timeout: Maximum time to wait in seconds (default 120)
            check_health: Wait for health checks to pass (default True)
            interval: Check interval in seconds (default 2)

        Returns:
            MonitorResult with container statuses
        """
        logger.info(f"Monitoring container startup (timeout: {timeout}s)")

        start_time = time.time()
        last_status = {}

        try:
            while True:
                elapsed = time.time() - start_time

                # Check if timed out
                if elapsed > timeout:
                    error_msg = f"Startup timeout ({timeout}s exceeded)"
                    logger.error(f"❌ {error_msg}")

                    # Get final status
                    containers = self._get_container_status()
                    return MonitorResult(
                        success=False,
                        containers=containers,
                        elapsed_time=elapsed,
                        error=error_msg,
                    )

                # Get current container status
                containers = self._get_container_status()

                if not containers:
                    logger.warning("No containers found - waiting...")
                    time.sleep(interval)
                    continue

                # Check status changes
                for container in containers:
                    prev_state = last_status.get(container.name, {}).get("state")
                    if prev_state != container.state:
                        logger.info(f"  {container}")
                        last_status[container.name] = {
                            "state": container.state,
                            "health": container.health,
                        }

                # Check if all running
                all_running = all(c.state == "running" for c in containers)

                if not all_running:
                    logger.debug(f"Waiting for containers... ({elapsed:.1f}s elapsed)")
                    time.sleep(interval)
                    continue

                # If health checks disabled, we're done
                if not check_health:
                    logger.info(
                        f"✅ All {len(containers)} containers running (health checks disabled)"
                    )
                    return MonitorResult(
                        success=True,
                        containers=containers,
                        all_running=True,
                        all_healthy=False,
                        elapsed_time=elapsed,
                    )

                # Check health status
                containers_with_health = [c for c in containers if c.health != "none"]

                if not containers_with_health:
                    logger.info(
                        f"✅ All {len(containers)} containers running (no health checks)"
                    )
                    return MonitorResult(
                        success=True,
                        containers=containers,
                        all_running=True,
                        all_healthy=True,
                        elapsed_time=elapsed,
                    )

                # Wait for all health checks
                all_healthy = all(c.health in ["healthy", "none"] for c in containers)
                any_unhealthy = any(c.health == "unhealthy" for c in containers)

                if any_unhealthy:
                    unhealthy = [c.name for c in containers if c.health == "unhealthy"]
                    error_msg = f"Unhealthy containers: {', '.join(unhealthy)}"
                    logger.error(f"❌ {error_msg}")
                    return MonitorResult(
                        success=False,
                        containers=containers,
                        elapsed_time=elapsed,
                        error=error_msg,
                    )

                if all_healthy:
                    logger.info(f"✅ All {len(containers)} healthy ({elapsed:.1f}s)")
                    return MonitorResult(
                        success=True,
                        containers=containers,
                        all_running=True,
                        all_healthy=True,
                        elapsed_time=elapsed,
                    )

                # Still starting
                time.sleep(interval)

        except Exception as e:
            error_msg = f"Monitoring error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return MonitorResult(
                success=False,
                containers=[],
                elapsed_time=time.time() - start_time,
                error=error_msg,
            )

    def _get_container_status(self) -> List[ContainerStatus]:
        """Get status of all containers for the project."""
        try:
            cmd = ["docker", "ps", "-a", "--format", "json"]

            if self.project_name:
                cmd.extend(
                    [
                        "--filter",
                        f"label=com.docker.compose.project={self.project_name}",
                    ]
                )

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=False
            )

            if result.returncode != 0:
                return []

            containers = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    status_text = data.get("Status", "")

                    if "(healthy)" in status_text:
                        health = "healthy"
                    elif "(unhealthy)" in status_text:
                        health = "unhealthy"
                    elif "health: starting" in status_text:
                        health = "starting"
                    else:
                        health = "none"

                    container = ContainerStatus(
                        name=data.get("Names", "unknown"),
                        state=data.get("State", "unknown"),
                        health=health,
                        uptime=status_text,
                    )
                    containers.append(container)
                except json.JSONDecodeError:
                    # Skip lines that aren't valid JSON
                    continue

            return containers
        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            return []


def main():
    """Test the unit."""
    import logging

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("Testing StartupMonitor")
    print("=" * 50)

    monitor = StartupMonitor()

    print("\n1. Testing container status retrieval:")
    containers = monitor._get_container_status()
    print(f"   Found {len(containers)} containers")
    for container in containers[:5]:
        print(f"   {container}")

    print("\n✅ StartupMonitor tests complete")


if __name__ == "__main__":
    main()
