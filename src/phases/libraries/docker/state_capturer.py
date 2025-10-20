#!/usr/bin/env python3
"""
StateCapturer Unit

Capture container states for snapshots
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging
import subprocess
import json
import shlex

logger = logging.getLogger(__name__)


@dataclass
class ContainerState:
    """Container state information."""

    id: str
    name: str
    image: str
    status: str
    created: str
    ports: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    command: Optional[str] = None
    entrypoint: Optional[str] = None


@dataclass
class CaptureResult:
    """Result of state capture operation."""

    success: bool
    containers: List[ContainerState] = field(default_factory=list)
    networks: List[Dict[str, Any]] = field(default_factory=list)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: Optional[str] = None
    error: Optional[str] = None


class StateCapturer:
    """
    Capture container states for snapshots
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize StateCapturer.

        Args:
            config: Optional configuration dictionary with:
                - project_name: Filter containers by project name
                - compose_file: Docker Compose file path
                - include_stopped: Include stopped containers (default: True)
        """
        self.config = config or {}
        self.project_name = self.config.get("project_name")
        self.compose_file = self.config.get("compose_file")
        self.include_stopped = self.config.get("include_stopped", True)

    def capture(self, project_name: Optional[str] = None) -> CaptureResult:
        """
        Capture current state of containers, networks, and volumes.

        Args:
            project_name: Optional project name to filter containers

        Returns:
            CaptureResult with captured state information

        Example:
            capturer = StateCapturer({'project_name': 'myapp'})
            result = capturer.capture()
            if result.success:
                print(f"Captured {len(result.containers)} containers")
        """
        try:
            # Use provided project_name or fall back to config
            project_name = project_name or self.project_name

            # Capture containers
            containers = self._capture_containers(project_name)

            # Capture networks
            networks = self._capture_networks(project_name)

            # Capture volumes
            volumes = self._capture_volumes(project_name)

            # Get timestamp
            import datetime

            timestamp = datetime.datetime.now().isoformat()

            logger.info(
                f"✅ Captured state: {len(containers)} containers, "
                f"{len(networks)} networks, {len(volumes)} volumes"
            )

            return CaptureResult(
                success=True,
                containers=containers,
                networks=networks,
                volumes=volumes,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(f"Failed to capture state: {e}", exc_info=True)
            return CaptureResult(success=False, error=str(e))

    def _capture_containers(self, project_name: Optional[str]) -> List[ContainerState]:
        """Capture container states."""
        containers = []

        try:
            # Build docker ps command
            cmd = ["docker", "ps", "--format", "{{json .}}"]

            # Include stopped containers if configured
            if self.include_stopped:
                cmd.append("--all")

            # Filter by project name if provided
            if project_name:
                cmd.extend(
                    ["--filter", f"label=com.docker.compose.project={project_name}"]
                )

            # Execute command
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
            )

            if result.returncode != 0:
                logger.warning(f"docker ps returned non-zero: {result.stderr}")
                return containers

            # Parse JSON output (one JSON object per line)
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                try:
                    container_info = json.loads(line)

                    # Get detailed container info
                    detailed_info = self._get_container_details(container_info["ID"])

                    # Create ContainerState
                    state = ContainerState(
                        id=container_info.get("ID", ""),
                        name=container_info.get("Names", ""),
                        image=container_info.get("Image", ""),
                        status=container_info.get("Status", ""),
                        created=container_info.get("CreatedAt", ""),
                        ports=self._parse_ports(container_info.get("Ports", "")),
                        networks=detailed_info.get("networks", []),
                        volumes=detailed_info.get("volumes", []),
                        environment=detailed_info.get("environment", {}),
                        labels=detailed_info.get("labels", {}),
                        command=detailed_info.get("command"),
                        entrypoint=detailed_info.get("entrypoint"),
                    )

                    containers.append(state)

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse container JSON: {e}")
                    continue

            logger.info(f"Captured {len(containers)} container(s)")

        except subprocess.TimeoutExpired:
            logger.error("docker ps command timed out")
        except Exception as e:
            logger.error(f"Failed to capture containers: {e}")

        return containers

    def _get_container_details(self, container_id: str) -> Dict[str, Any]:
        """Get detailed container information."""
        details = {
            "networks": [],
            "volumes": [],
            "environment": {},
            "labels": {},
            "command": None,
            "entrypoint": None,
        }

        try:
            # Use docker inspect to get full details
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            if result.returncode != 0:
                return details

            inspect_data = json.loads(result.stdout)
            if not inspect_data:
                return details

            container = inspect_data[0]

            # Extract networks
            networks = container.get("NetworkSettings", {}).get("Networks", {})
            details["networks"] = list(networks.keys())

            # Extract volumes
            mounts = container.get("Mounts", [])
            details["volumes"] = [
                f"{m.get('Source', '')}:{m.get('Destination', '')}"
                for m in mounts
                if m.get("Source") and m.get("Destination")
            ]

            # Extract environment variables
            env_list = container.get("Config", {}).get("Env", [])
            details["environment"] = dict(
                item.split("=", 1) for item in env_list if "=" in item
            )

            # Extract labels
            details["labels"] = container.get("Config", {}).get("Labels", {})

            # Extract command and entrypoint
            details["command"] = " ".join(
                container.get("Config", {}).get("Cmd", []) or []
            )
            details["entrypoint"] = " ".join(
                container.get("Config", {}).get("Entrypoint", []) or []
            )

        except Exception as e:
            logger.debug(f"Failed to get container details for {container_id}: {e}")

        return details

    def _capture_networks(self, project_name: Optional[str]) -> List[Dict[str, Any]]:
        """Capture Docker networks."""
        networks = []

        try:
            # Build command
            cmd = ["docker", "network", "ls", "--format", "{{json .}}"]

            # Filter by project name if provided
            if project_name:
                cmd.extend(
                    ["--filter", f"label=com.docker.compose.project={project_name}"]
                )

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=False
            )

            if result.returncode != 0:
                logger.warning(f"docker network ls returned non-zero: {result.stderr}")
                return networks

            # Parse output
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    network_info = json.loads(line)
                    networks.append(network_info)
                except json.JSONDecodeError:
                    continue

            logger.info(f"Captured {len(networks)} network(s)")

        except Exception as e:
            logger.error(f"Failed to capture networks: {e}")

        return networks

    def _capture_volumes(self, project_name: Optional[str]) -> List[Dict[str, Any]]:
        """Capture Docker volumes."""
        volumes = []

        try:
            # Build command
            cmd = ["docker", "volume", "ls", "--format", "{{json .}}"]

            # Filter by project name if provided
            if project_name:
                cmd.extend(
                    ["--filter", f"label=com.docker.compose.project={project_name}"]
                )

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10, check=False
            )

            if result.returncode != 0:
                logger.warning(f"docker volume ls returned non-zero: {result.stderr}")
                return networks

            # Parse output
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    volume_info = json.loads(line)
                    volumes.append(volume_info)
                except json.JSONDecodeError:
                    continue

            logger.info(f"Captured {len(volumes)} volume(s)")

        except Exception as e:
            logger.error(f"Failed to capture volumes: {e}")

        return volumes

    def _parse_ports(self, ports_str: str) -> List[str]:
        """Parse ports string into list."""
        if not ports_str:
            return []

        # Ports format: "0.0.0.0:8080->80/tcp, 0.0.0.0:6379->6379/tcp"
        return [p.strip() for p in ports_str.split(",") if p.strip()]


def main():
    """Test the unit."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("\nTesting StateCapturer")
    print("=" * 50)

    # Test 1: Capture all containers
    print("\n1. Testing capture of all containers:")
    capturer = StateCapturer({"include_stopped": True})
    result = capturer.capture()

    if result.success:
        print(f"   ✅ Captured {len(result.containers)} containers")
        print(f"   ✅ Captured {len(result.networks)} networks")
        print(f"   ✅ Captured {len(result.volumes)} volumes")
        print(f"   Timestamp: {result.timestamp}")

        # Show first container details if any
        if result.containers:
            container = result.containers[0]
            print(f"\n   First container:")
            print(f"     Name: {container.name}")
            print(f"     Image: {container.image}")
            print(f"     Status: {container.status}")
            print(f"     Networks: {', '.join(container.networks)}")
            print(f"     Volumes: {len(container.volumes)}")
    else:
        print(f"   ❌ Failed to capture state: {result.error}")

    # Test 2: Capture specific project
    print("\n2. Testing capture with project filter:")
    capturer = StateCapturer({"project_name": "test-deployment"})
    result = capturer.capture()

    if result.success:
        print(
            f"   ✅ Captured {len(result.containers)} containers for project 'test-deployment'"
        )
        for container in result.containers:
            print(f"     - {container.name} ({container.image})")
    else:
        print(f"   ⏭️  No containers found (might not exist)")

    print("\n✅ StateCapturer tests complete")


if __name__ == "__main__":
    main()
