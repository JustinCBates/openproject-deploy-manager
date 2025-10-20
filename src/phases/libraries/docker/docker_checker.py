#!/usr/bin/env python3
"""
DockerChecker Unit

Check Docker daemon availability
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
import subprocess
import shutil

logger = logging.getLogger(__name__)


@dataclass
class DockerStatus:
    """Status of Docker daemon"""

    available: bool
    version: Optional[str] = None
    compose_available: bool = False
    compose_version: Optional[str] = None
    error: Optional[str] = None

    def __str__(self):
        if self.available:
            status = f"✅ Docker {self.version} available"
            if self.compose_available:
                status += f", Compose {self.compose_version}"
            return status
        return f"❌ Docker not available: {self.error}"


class DockerChecker:
    """
    Check Docker daemon availability
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DockerChecker.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def check(self) -> DockerStatus:
        """
        Check Docker daemon availability and version.

        Returns:
            DockerStatus with availability and version info
        """
        logger.info("Checking Docker daemon availability...")

        # Check if docker command exists
        if not shutil.which("docker"):
            logger.error("Docker command not found in PATH")
            return DockerStatus(
                available=False, error="Docker command not found in PATH"
            )

        # Check Docker daemon
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Docker daemon not running"
                logger.error(f"Docker daemon check failed: {error_msg}")
                return DockerStatus(available=False, error=error_msg)

            version = result.stdout.strip()
            logger.info(f"✅ Docker daemon available: {version}")

            # Check Docker Compose
            compose_available, compose_version = self._check_compose()

            return DockerStatus(
                available=True,
                version=version,
                compose_available=compose_available,
                compose_version=compose_version,
            )

        except subprocess.TimeoutExpired:
            logger.error("Docker daemon check timed out")
            return DockerStatus(
                available=False,
                error="Docker daemon check timed out (daemon may be unresponsive)",
            )
        except Exception as e:
            logger.error(f"Docker daemon check failed: {e}")
            return DockerStatus(available=False, error=str(e))

    def _check_compose(self) -> tuple[bool, Optional[str]]:
        """
        Check Docker Compose availability.

        Returns:
            Tuple of (available, version)
        """
        # Try docker compose (plugin)
        try:
            result = subprocess.run(
                ["docker", "compose", "version", "--short"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✅ Docker Compose plugin available: {version}")
                return True, version
        except Exception as e:
            logger.debug(f"Docker Compose plugin check failed: {e}")

        # Try docker-compose (standalone)
        if shutil.which("docker-compose"):
            try:
                result = subprocess.run(
                    ["docker-compose", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    # Parse version from output like "docker-compose version 1.29.2"
                    version = result.stdout.strip().split()[-1]
                    logger.info(f"✅ Docker Compose standalone available: {version}")
                    return True, version
            except Exception as e:
                logger.debug(f"Docker Compose standalone check failed: {e}")

        logger.warning("Docker Compose not available")
        return False, None


def main():
    """Test the unit."""
    unit = DockerChecker()

    print("Checking Docker availability...")
    status = unit.check()
    print(f"\n{status}")

    if status.available:
        print(f"\nDetails:")
        print(f"  Docker version: {status.version}")
        print(f"  Compose available: {status.compose_available}")
        if status.compose_available:
            print(f"  Compose version: {status.compose_version}")
    else:
        print(f"\nError: {status.error}")

    print(f"\n{unit.__class__.__name__} test complete")
