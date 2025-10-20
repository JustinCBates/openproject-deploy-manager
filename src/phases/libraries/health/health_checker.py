#!/usr/bin/env python3
"""
HealthChecker Unit

Check service health
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import time
import subprocess

logger = logging.getLogger(__name__)


class HealthState(Enum):
    """Health state enumeration"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    UNKNOWN = "unknown"


@dataclass
class HealthStatus:
    """Health status of a service"""

    name: str
    state: HealthState
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def __str__(self):
        emoji = {
            HealthState.HEALTHY: "✅",
            HealthState.UNHEALTHY: "❌",
            HealthState.STARTING: "🔄",
            HealthState.UNKNOWN: "❓",
        }
        status = f"{emoji[self.state]} {self.name}: {self.state.value}"
        if self.message:
            status += f" - {self.message}"
        return status


@dataclass
class Result:
    """Result of health check operation"""

    success: bool
    services: List[HealthStatus]
    message: str
    elapsed_time: float

    def __str__(self):
        healthy = sum(1 for s in self.services if s.state == HealthState.HEALTHY)
        total = len(self.services)
        if self.success:
            return f"✅ {healthy}/{total} services healthy ({self.elapsed_time:.1f}s)"
        return f"❌ Health check failed: {self.message} ({self.elapsed_time:.1f}s)"


class HealthChecker:
    """
    Check service health
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize HealthChecker.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def check_service(self, name: str) -> HealthStatus:
        """
        Check health of a specific service.

        Args:
            name: Service name (Docker container name)

        Returns:
            HealthStatus with current health state
        """
        logger.debug(f"Checking health of service: {name}")

        try:
            # Use docker inspect to get container health
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", name],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                # Container might not exist or no health check defined
                logger.warning(f"Could not get health status for {name}")
                return HealthStatus(
                    name=name,
                    state=HealthState.UNKNOWN,
                    message="Container not found or no health check defined",
                )

            health_status = result.stdout.strip()

            # Map Docker health status to our HealthState
            state_map = {
                "healthy": HealthState.HEALTHY,
                "unhealthy": HealthState.UNHEALTHY,
                "starting": HealthState.STARTING,
                "": HealthState.UNKNOWN,  # No health check defined
            }

            state = state_map.get(health_status, HealthState.UNKNOWN)

            logger.info(f"Service {name}: {state.value}")

            return HealthStatus(
                name=name,
                state=state,
                message=health_status if health_status else "No health check defined",
            )

        except subprocess.TimeoutExpired:
            logger.error(f"Health check timed out for {name}")
            return HealthStatus(
                name=name, state=HealthState.UNKNOWN, message="Health check timed out"
            )
        except Exception as e:
            logger.error(f"Health check failed for {name}: {e}")
            return HealthStatus(name=name, state=HealthState.UNKNOWN, message=str(e))

    def wait_for_healthy(self, services: List[str], timeout: int = 60) -> Result:
        """
        Wait for services to become healthy.

        Args:
            services: List of service names to check
            timeout: Maximum time to wait in seconds

        Returns:
            Result with success status and service health states
        """
        logger.info(
            f"Waiting for {len(services)} services to become healthy (timeout: {timeout}s)"
        )

        start_time = time.time()
        interval = 2  # Check every 2 seconds

        while True:
            elapsed = time.time() - start_time

            # Check all services
            statuses = [self.check_service(name) for name in services]

            # Count healthy services
            healthy_count = sum(1 for s in statuses if s.state == HealthState.HEALTHY)
            unhealthy = [s for s in statuses if s.state == HealthState.UNHEALTHY]

            logger.debug(
                f"Health check: {healthy_count}/{len(services)} healthy ({elapsed:.1f}s)"
            )

            # Check if all healthy
            if healthy_count == len(services):
                logger.info(f"✅ All services healthy ({elapsed:.1f}s)")
                return Result(
                    success=True,
                    services=statuses,
                    message=f"All {len(services)} services healthy",
                    elapsed_time=elapsed,
                )

            # Check if any unhealthy (not starting)
            if unhealthy:
                logger.error(f"Services unhealthy: {[s.name for s in unhealthy]}")
                return Result(
                    success=False,
                    services=statuses,
                    message=f"{len(unhealthy)} services unhealthy",
                    elapsed_time=elapsed,
                )

            # Check timeout
            if elapsed >= timeout:
                logger.error(f"Health check timed out after {elapsed:.1f}s")
                return Result(
                    success=False,
                    services=statuses,
                    message=f"Timeout waiting for services (only {healthy_count}/{len(services)} healthy)",
                    elapsed_time=elapsed,
                )

            # Wait before next check
            time.sleep(interval)


def main():
    """Test the unit."""
    unit = HealthChecker()

    print("Testing HealthChecker...")
    print("\nNote: This requires Docker containers to be running")
    print("Creating a test container with health check...\n")

    # Try to check a common container (if it exists)
    test_services = ["test-container"]

    print("Test 1: Check single service")
    status = unit.check_service("test-container")
    print(f"  {status}")

    print("\nTest 2: Wait for services (with short timeout)")
    result = unit.wait_for_healthy(test_services, timeout=5)
    print(f"  {result}")

    print(f"\n{unit.__class__.__name__} tests complete")
