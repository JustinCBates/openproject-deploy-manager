#!/usr/bin/env python3
"""
Snapshot Creation
Sequence: 30
Status: IMPLEMENTED

Create pre-deployment snapshot for rollback capability
"""

from pathlib import Path
from typing import Dict, Any
import logging
import datetime

from phases.libraries.docker.state_capturer import StateCapturer
from phases.libraries.snapshot.config_backupper import ConfigBackupper
from phases.libraries.snapshot.snapshot_storer import SnapshotStorer, Snapshot

logger = logging.getLogger(__name__)


class Phase3SnapshotOrchestrator:
    """
    Snapshot Creation

    Status: IMPLEMENTED
    Sequence: 30

    Create pre-deployment snapshot for rollback capability
    """

    PHASE_ID = "phase_3_snapshot"
    PHASE_SEQUENCE = 30
    PHASE_NAME = "Snapshot Creation"

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        Initialize Snapshot Creation.

        Args:
            project_root: Root directory of the project
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config
        self.phase_dir = project_root / "runtime" / "phase_3_snapshot"
        self.outputs_dir = self.phase_dir / "outputs"

        # Ensure outputs directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Snapshot Creation.

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
            # Step 10: Capture Container States
            step_result = self._step_10_capture_container_states(context)
            if step_result["status"] == "error":
                result["status"] = "error"
                result["messages"].extend(step_result.get("messages", []))
                return result
            result["artifacts"].update(step_result.get("artifacts", {}))
            context.update(step_result.get("artifacts", {}))

            # Step 20: Backup Configuration Files
            step_result = self._step_20_backup_configuration_files(context)
            if step_result["status"] == "error":
                result["status"] = "error"
                result["messages"].extend(step_result.get("messages", []))
                return result
            result["artifacts"].update(step_result.get("artifacts", {}))
            context.update(step_result.get("artifacts", {}))

            # Step 30: Store Snapshot
            step_result = self._step_30_store_snapshot(context)
            if step_result["status"] == "error":
                result["status"] = "error"
                result["messages"].extend(step_result.get("messages", []))
                return result
            result["artifacts"].update(step_result.get("artifacts", {}))

            result["messages"].append("✅ Phase 3: Snapshot Creation complete")

        except Exception as e:
            logger.error(f"Phase 3 failed: {e}", exc_info=True)
            result["status"] = "error"
            result["messages"].append(f"Phase 3 failed: {str(e)}")

        return result

    def _step_10_capture_container_states(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 10: Capture Container States

        Capture current container states and configurations
        """
        logger.info(f"  Step 10: Capture Container States")

        try:
            # Get project name from context
            validated_config = context.get("validated_config")
            if not validated_config:
                # If no config, capture all containers
                project_name = None
            else:
                project_name = validated_config.get("project_name")

            # Initialize state capturer
            capturer_config = {}
            if project_name:
                capturer_config["project_name"] = project_name

            capturer = StateCapturer(capturer_config)

            # Capture state
            logger.info(f"    📸 Capturing state for project: {project_name or 'all'}")
            result = capturer.capture(project_name)

            if not result.success:
                return {
                    "status": "error",
                    "artifacts": {},
                    "messages": [f"Failed to capture state: {result.error}"],
                }

            logger.info(
                f"    ✅ Captured {len(result.containers)} containers, "
                f"{len(result.networks)} networks, {len(result.volumes)} volumes"
            )

            # Convert to serializable format
            containers = [
                {
                    "id": c.id,
                    "name": c.name,
                    "image": c.image,
                    "status": c.status,
                    "created": c.created,
                    "ports": c.ports,
                    "networks": c.networks,
                    "volumes": c.volumes,
                    "environment": c.environment,
                    "labels": c.labels,
                    "command": c.command,
                    "entrypoint": c.entrypoint,
                }
                for c in result.containers
            ]

            return {
                "status": "success",
                "artifacts": {
                    "captured_containers": containers,
                    "captured_networks": result.networks,
                    "captured_volumes": result.volumes,
                    "capture_timestamp": result.timestamp,
                },
                "messages": [f"Captured {len(result.containers)} containers"],
            }

        except Exception as e:
            logger.error(f"Step 10 failed: {e}", exc_info=True)
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Step 10 failed: {str(e)}"],
            }

    def _step_20_backup_configuration_files(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 20: Backup Configuration Files

        Backup current configuration files
        """
        logger.info(f"  Step 20: Backup Configuration Files")

        try:
            # Get config files from context
            config_file = context.get("config_file")
            compose_file = context.get("compose_file") or context.get(
                "rendered_docker_compose"
            )
            env_file = context.get("env_file_path")
            rendered_caddyfile = context.get("rendered_caddyfile")

            # Collect files to backup
            files_to_backup = []
            if config_file and Path(config_file).exists():
                files_to_backup.append(Path(config_file))
            if compose_file and Path(compose_file).exists():
                files_to_backup.append(Path(compose_file))
            if env_file and Path(env_file).exists():
                files_to_backup.append(Path(env_file))
            if rendered_caddyfile and Path(rendered_caddyfile).exists():
                files_to_backup.append(Path(rendered_caddyfile))

            if not files_to_backup:
                logger.info(f"    ⏭️  No configuration files to backup")
                return {
                    "status": "success",
                    "artifacts": {"backup_dir": None, "backed_up_files": []},
                    "messages": ["No configuration files to backup"],
                }

            # Create backup directory in phase outputs
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.outputs_dir / f"config_backup_{timestamp}"

            # Initialize backupper
            backupper = ConfigBackupper({"backup_root": self.outputs_dir})

            # Backup files
            logger.info(
                f"    💾 Backing up {len(files_to_backup)} configuration file(s)"
            )
            result = backupper.backup(files_to_backup, backup_dir)

            if not result.success:
                return {
                    "status": "error",
                    "artifacts": {},
                    "messages": [f"Failed to backup files: {result.error}"],
                }

            logger.info(
                f"    ✅ Backed up {result.file_count} files ({result.total_size} bytes)"
            )
            for file in files_to_backup:
                logger.debug(f"       - {file.name}")

            return {
                "status": "success",
                "artifacts": {
                    "backup_dir": str(result.backup_dir),
                    "backed_up_files": [str(f) for f in result.backed_up_files],
                    "backup_size": result.total_size,
                    "backup_checksums": result.checksums,
                },
                "messages": [f"Backed up {result.file_count} configuration files"],
            }

        except Exception as e:
            logger.error(f"Step 20 failed: {e}", exc_info=True)
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Step 20 failed: {str(e)}"],
            }

    def _step_30_store_snapshot(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 30: Store Snapshot

        Store snapshot with metadata and timestamp
        """
        logger.info(f"  Step 30: Store Snapshot")

        try:
            # Get data from previous steps
            containers = context.get("captured_containers", [])
            networks = context.get("captured_networks", [])
            volumes = context.get("captured_volumes", [])
            backup_dir = context.get("backup_dir")
            backed_up_files = context.get("backed_up_files", [])

            # Get project name
            validated_config = context.get("validated_config")
            project_name = (
                validated_config.get("project_name", "unknown")
                if validated_config
                else "unknown"
            )

            # Create snapshot ID
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_id = f"snap_{project_name}_{timestamp}"

            # Create snapshot object
            snapshot = Snapshot(
                id=snapshot_id,
                timestamp=datetime.datetime.now().isoformat(),
                project_name=project_name,
                containers=containers,
                networks=networks,
                volumes=volumes,
                config_files=backed_up_files,
                backup_dir=backup_dir,
                metadata={
                    "phase": "pre-deployment",
                    "container_count": len(containers),
                    "network_count": len(networks),
                    "volume_count": len(volumes),
                    "config_file_count": len(backed_up_files),
                },
            )

            # Initialize storer
            storer_config = {
                "snapshot_dir": self.outputs_dir / "snapshots",
                "max_snapshots": 10,
            }
            storer = SnapshotStorer(storer_config)

            # Store snapshot
            logger.info(f"    💾 Storing snapshot: {snapshot_id}")
            result = storer.store(snapshot)

            if not result.success:
                return {
                    "status": "error",
                    "artifacts": {},
                    "messages": [f"Failed to store snapshot: {result.error}"],
                }

            logger.info(f"    ✅ Snapshot stored: {result.snapshot_path}")
            logger.info(f"       Containers: {len(containers)}")
            logger.info(f"       Networks: {len(networks)}")
            logger.info(f"       Volumes: {len(volumes)}")
            logger.info(f"       Config files: {len(backed_up_files)}")

            return {
                "status": "success",
                "artifacts": {
                    "snapshot_id": result.snapshot_id,
                    "snapshot_path": str(result.snapshot_path),
                    "snapshot_data": snapshot.to_dict(),
                },
                "messages": [f"Snapshot created: {result.snapshot_id}"],
            }

        except Exception as e:
            logger.error(f"Step 30 failed: {e}", exc_info=True)
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Step 30 failed: {str(e)}"],
            }


def main():
    """Test the phase orchestrator."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    project_root = Path(__file__).parent.parent.parent
    config = {}

    # Create test context with sample data
    context = {
        "validated_config": {"project_name": "test-app", "environment": "development"},
        "config_file": str(project_root / "test_data" / "test-config.yml"),
        "compose_file": str(project_root / "test_data" / "test-compose.yml"),
    }

    orchestrator = Phase3SnapshotOrchestrator(project_root, config)

    logger.info("\n" + "=" * 70)
    logger.info("Testing Phase 3 Snapshot Orchestrator")
    logger.info("=" * 70)
    logger.info(f"Project root: {project_root}")
    logger.info(f"Outputs dir: {orchestrator.outputs_dir}")
    logger.info("")

    # Execute phase
    result = orchestrator.execute(context)

    logger.info("\n" + "=" * 70)
    logger.info("Phase 3 Result:")
    logger.info(f"  Status: {result['status']}")
    logger.info(f"  Messages: {result.get('messages', [])}")
    logger.info(f"  Artifacts: {len(result.get('artifacts', {}))}")

    if result.get("snapshot_id"):
        logger.info(f"\n  Snapshot ID: {result['snapshot_id']}")
        logger.info(f"  Snapshot Path: {result.get('snapshot_path')}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
