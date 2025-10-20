#!/usr/bin/env python3
"""
Global Phases Orchestrator for deploy-manager

This orchestrator coordinates all deployment phases in sequence.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
import shutil

from phases.phase_1_preflight.phase_1_preflight_orchestrator import Phase1PreflightOrchestrator
from phases.phase_2_template_rendering.phase_2_template_rendering_orchestrator import Phase2TemplateRenderingOrchestrator
from phases.phase_3_snapshot.phase_3_snapshot_orchestrator import Phase3SnapshotOrchestrator
from phases.phase_4_deployment.phase_4_deployment_orchestrator import Phase4DeploymentOrchestrator
from phases.phase_5_health_verification.phase_5_health_verification_orchestrator import Phase5HealthVerificationOrchestrator
from phases.phase_6_post_deployment.phase_6_post_deployment_orchestrator import Phase6PostDeploymentOrchestrator

# Import library units for rollback
from phases.libraries.snapshot.snapshot_storer import SnapshotStorer
from phases.libraries.docker.compose_executor import ComposeExecutor
from phases.libraries.reporting.metadata_logger import MetadataLogger

logger = logging.getLogger(__name__)


class PhasesOrchestrator:
    """
    Global orchestrator for all deployment phases.
    
    Coordinates execution of all phases in the correct sequence,
    handles errors, and manages the deployment context.
    """
    
    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        Initialize global orchestrator.
        
        Args:
            project_root: Root directory of the project
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config
        
        # Initialize all phase orchestrators
        self.phase_1_preflight = Phase1PreflightOrchestrator(project_root, config)
        self.phase_2_template_rendering = Phase2TemplateRenderingOrchestrator(project_root, config)
        self.phase_3_snapshot = Phase3SnapshotOrchestrator(project_root, config)
        self.phase_4_deployment = Phase4DeploymentOrchestrator(project_root, config)
        self.phase_5_health_verification = Phase5HealthVerificationOrchestrator(project_root, config)
        self.phase_6_post_deployment = Phase6PostDeploymentOrchestrator(project_root, config)
    
    def execute_main_deployment_flow(self, initial_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute the main deployment flow (all phases in sequence).
        
        Args:
            initial_context: Initial context/configuration
            
        Returns:
            Dict with deployment results
        """
        logger.info("=" * 70)
        logger.info("MAIN DEPLOYMENT FLOW")
        logger.info("=" * 70)
        
        context = initial_context or {}
        results = {}
        
        try:
            # Phase 10: Preflight Validation
            logger.info(f"Executing Phase 10: Preflight Validation")
            phase_result = self.phase_1_preflight.execute(context)
            
            # Accept 'success' or 'warning' status for preflight
            if phase_result.get("status") not in ["success", "warning"]:
                logger.error(f"Phase 10 failed: {phase_result.get('messages')}")
                return {
                    "status": "failed",
                    "failed_phase": "phase_1_preflight",
                    "result": phase_result
                }
            
            context.update(phase_result.get("artifacts", {}))
            results["phase_1_preflight"] = phase_result

            # Phase 20: Template Rendering
            logger.info(f"Executing Phase 20: Template Rendering")
            phase_result = self.phase_2_template_rendering.execute(context)
            
            if phase_result.get("status") != "success":
                logger.error(f"Phase 20 failed: {phase_result.get('messages')}")
                return {
                    "status": "failed",
                    "failed_phase": "phase_2_template_rendering",
                    "result": phase_result
                }
            
            context.update(phase_result.get("artifacts", {}))
            results["phase_2_template_rendering"] = phase_result

            # Phase 30: Snapshot Creation
            logger.info(f"Executing Phase 30: Snapshot Creation")
            phase_result = self.phase_3_snapshot.execute(context)
            
            if phase_result.get("status") != "success":
                logger.error(f"Phase 30 failed: {phase_result.get('messages')}")
                return {
                    "status": "failed",
                    "failed_phase": "phase_3_snapshot",
                    "result": phase_result
                }
            
            context.update(phase_result.get("artifacts", {}))
            results["phase_3_snapshot"] = phase_result

            # Phase 40: Deployment Execution
            logger.info(f"Executing Phase 40: Deployment Execution")
            phase_result = self.phase_4_deployment.execute(context)
            
            if phase_result.get("status") != "success":
                logger.error(f"Phase 40 failed: {phase_result.get('messages')}")
                return {
                    "status": "failed",
                    "failed_phase": "phase_4_deployment",
                    "result": phase_result
                }
            
            context.update(phase_result.get("artifacts", {}))
            results["phase_4_deployment"] = phase_result

            # Phase 50: Health Verification
            logger.info(f"Executing Phase 50: Health Verification")
            phase_result = self.phase_5_health_verification.execute(context)
            
            # Accept 'success' or 'degraded' status for health verification
            if phase_result.get("status") not in ["success", "degraded"]:
                logger.error(f"Phase 50 failed: {phase_result.get('messages')}")
                return {
                    "status": "failed",
                    "failed_phase": "phase_5_health_verification",
                    "result": phase_result
                }
            
            context.update(phase_result.get("artifacts", {}))
            results["phase_5_health_verification"] = phase_result

            # Phase 60: Post-Deployment
            logger.info(f"Executing Phase 60: Post-Deployment")
            phase_result = self.phase_6_post_deployment.execute(context)
            
            if phase_result.get("status") != "success":
                logger.error(f"Phase 60 failed: {phase_result.get('messages')}")
                return {
                    "status": "failed",
                    "failed_phase": "phase_6_post_deployment",
                    "result": phase_result
                }
            
            context.update(phase_result.get("artifacts", {}))
            results["phase_6_post_deployment"] = phase_result
            
            logger.info("=" * 70)
            logger.info("✅ DEPLOYMENT SUCCESSFUL")
            logger.info("=" * 70)
            
            return {
                "status": "success",
                "phases": results,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Deployment failed with exception: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "error": str(e),
                "phases": results
            }
    
    def execute_rollback_flow(self, snapshot_id: str, reason: str = "Manual rollback") -> Dict[str, Any]:
        """
        Execute rollback to a previous snapshot.
        
        This performs a complete rollback:
        1. Load the snapshot
        2. Stop current deployment
        3. Restore configuration files
        4. Restart services with previous config
        5. Verify health
        6. Log rollback event
        
        Args:
            snapshot_id: ID of snapshot to rollback to
            reason: Reason for rollback (for logging)
            
        Returns:
            Dict with rollback results
        """
        logger.info("=" * 70)
        logger.info(f"ROLLBACK FLOW - Snapshot: {snapshot_id}")
        logger.info(f"Reason: {reason}")
        logger.info("=" * 70)
        
        rollback_result = {
            "status": "in_progress",
            "snapshot_id": snapshot_id,
            "steps": {},
            "errors": []
        }
        
        try:
            # ================================================================
            # Step 1: Load Snapshot
            # ================================================================
            logger.info("\n[Step 1/6] Loading snapshot...")
            
            snapshot_dir = self.project_root / "runtime" / "phase_3_snapshot" / "outputs" / "snapshots"
            storer = SnapshotStorer(config={'snapshot_dir': str(snapshot_dir)})
            
            load_result = storer.load(snapshot_id)
            
            if not load_result.success:
                error_msg = f"Failed to load snapshot: {load_result.error}"
                logger.error(error_msg)
                rollback_result["status"] = "failed"
                rollback_result["errors"].append(error_msg)
                rollback_result["steps"]["load_snapshot"] = "failed"
                return rollback_result
            
            snapshot = load_result.snapshot
            logger.info(f"✅ Loaded snapshot: {snapshot.id}")
            logger.info(f"   Project: {snapshot.project_name}")
            logger.info(f"   Timestamp: {snapshot.timestamp}")
            logger.info(f"   Containers: {len(snapshot.containers)}")
            logger.info(f"   Config files: {len(snapshot.config_files)}")
            
            rollback_result["steps"]["load_snapshot"] = "success"
            
            # ================================================================
            # Step 2: Stop Current Deployment
            # ================================================================
            logger.info("\n[Step 2/6] Stopping current deployment...")
            
            project_name = self.config.get('project_name', snapshot.project_name)
            compose_file = self.config.get('compose_file', '')
            
            if compose_file and Path(compose_file).exists():
                executor = ComposeExecutor(config={
                    'compose_file': compose_file,
                    'project_name': project_name
                })
                
                down_result = executor.down(volumes=False, remove_orphans=True)
                
                if down_result.success:
                    logger.info(f"✅ Stopped current deployment: {project_name}")
                    rollback_result["steps"]["stop_deployment"] = "success"
                else:
                    logger.warning(f"⚠️  Failed to stop deployment: {down_result.error}")
                    rollback_result["steps"]["stop_deployment"] = "warning"
            else:
                logger.warning("⚠️  No compose file found, skipping container stop")
                rollback_result["steps"]["stop_deployment"] = "skipped"
            
            # ================================================================
            # Step 3: Restore Configuration Files
            # ================================================================
            logger.info("\n[Step 3/6] Restoring configuration files...")
            
            if snapshot.backup_dir:
                backup_path = Path(snapshot.backup_dir)
                
                if backup_path.exists():
                    restored_count = 0
                    
                    for config_file_name in snapshot.config_files:
                        source = backup_path / config_file_name
                        dest = self.project_root / config_file_name
                        
                        if source.exists():
                            try:
                                # Create destination directory if needed
                                dest.parent.mkdir(parents=True, exist_ok=True)
                                
                                # Copy file
                                shutil.copy2(source, dest)
                                logger.info(f"   ✅ Restored: {config_file_name}")
                                restored_count += 1
                            except Exception as e:
                                logger.error(f"   ❌ Failed to restore {config_file_name}: {e}")
                                rollback_result["errors"].append(f"Failed to restore {config_file_name}")
                        else:
                            logger.warning(f"   ⚠️  Backup not found: {config_file_name}")
                    
                    logger.info(f"✅ Restored {restored_count}/{len(snapshot.config_files)} configuration files")
                    rollback_result["steps"]["restore_config"] = "success"
                    rollback_result["files_restored"] = restored_count
                else:
                    logger.warning(f"⚠️  Backup directory not found: {backup_path}")
                    rollback_result["steps"]["restore_config"] = "warning"
            else:
                logger.warning("⚠️  No backup directory in snapshot")
                rollback_result["steps"]["restore_config"] = "skipped"
            
            # ================================================================
            # Step 4: Restart Services
            # ================================================================
            logger.info("\n[Step 4/6] Restarting services with previous configuration...")
            
            if compose_file and Path(compose_file).exists():
                executor = ComposeExecutor(config={
                    'compose_file': compose_file,
                    'project_name': project_name
                })
                
                up_result = executor.up(detached=True, build=False)
                
                if up_result.success:
                    logger.info(f"✅ Services restarted: {project_name}")
                    rollback_result["steps"]["restart_services"] = "success"
                else:
                    error_msg = f"Failed to restart services: {up_result.error}"
                    logger.error(f"❌ {error_msg}")
                    rollback_result["errors"].append(error_msg)
                    rollback_result["steps"]["restart_services"] = "failed"
                    # Don't return yet - continue to health check
            else:
                logger.warning("⚠️  No compose file found, skipping service restart")
                rollback_result["steps"]["restart_services"] = "skipped"
            
            # ================================================================
            # Step 5: Verify Health
            # ================================================================
            logger.info("\n[Step 5/6] Verifying deployment health...")
            
            health_context = {
                "config": self.config,
                "project_name": project_name
            }
            
            health_result = self.phase_5_health_verification.execute(health_context)
            
            health_status = health_result.get("status", "unknown")
            if health_status in ["success", "degraded"]:
                logger.info(f"✅ Health verification: {health_status}")
                rollback_result["steps"]["verify_health"] = health_status
                rollback_result["health_status"] = health_status
            else:
                logger.warning(f"⚠️  Health verification: {health_status}")
                rollback_result["steps"]["verify_health"] = "warning"
                rollback_result["health_status"] = health_status
            
            # ================================================================
            # Step 6: Log Rollback Event
            # ================================================================
            logger.info("\n[Step 6/6] Logging rollback event...")
            
            metadata_logger = MetadataLogger(config={'log_format': 'json'})
            log_path = self.project_root / "runtime" / "phase_6_post_deployment" / "outputs" / "deployment_history.log"
            
            rollback_metadata = {
                "event_type": "rollback",
                "snapshot_id": snapshot_id,
                "reason": reason,
                "status": "completed",
                "project_name": project_name,
                "steps_completed": list(rollback_result["steps"].keys()),
                "health_status": rollback_result.get("health_status", "unknown")
            }
            
            if metadata_logger.log(rollback_metadata, log_path):
                logger.info(f"✅ Rollback event logged to: {log_path}")
                rollback_result["steps"]["log_event"] = "success"
            else:
                logger.warning("⚠️  Failed to log rollback event")
                rollback_result["steps"]["log_event"] = "failed"
            
            # ================================================================
            # Final Status
            # ================================================================
            logger.info("\n" + "=" * 70)
            
            # Determine overall status
            failed_steps = [k for k, v in rollback_result["steps"].items() if v == "failed"]
            
            if failed_steps:
                rollback_result["status"] = "partial"
                logger.warning(f"⚠️  ROLLBACK PARTIALLY SUCCESSFUL")
                logger.warning(f"   Failed steps: {failed_steps}")
            else:
                rollback_result["status"] = "success"
                logger.info(f"✅ ROLLBACK SUCCESSFUL")
            
            logger.info(f"   Snapshot: {snapshot_id}")
            logger.info(f"   Health: {rollback_result.get('health_status', 'unknown')}")
            logger.info("=" * 70)
            
            return rollback_result
            
        except Exception as e:
            logger.error(f"Rollback failed with exception: {e}")
            import traceback
            traceback.print_exc()
            
            rollback_result["status"] = "error"
            rollback_result["errors"].append(str(e))
            
            return rollback_result
    
    def execute_validation_only_flow(self) -> Dict[str, Any]:
        """
        Execute validation only (no deployment).
        
        Returns:
            Dict with validation results
        """
        logger.info("=" * 70)
        logger.info("VALIDATION ONLY FLOW")
        logger.info("=" * 70)
        
        context = {}
        results = {}
        
        # Execute Phase 1: Preflight Validation
        logger.info("Executing Phase 1: Preflight Validation")
        phase_result = self.phase_1_preflight.execute(context)
        results["phase_1_preflight"] = phase_result
        
        # Execute Phase 2: Template Rendering
        logger.info("Executing Phase 2: Template Rendering")
        phase_result = self.phase_2_template_rendering.execute(context)
        results["phase_2_template_rendering"] = phase_result
        
        logger.info("=" * 70)
        logger.info("✅ VALIDATION COMPLETE")
        logger.info("=" * 70)
        
        return {
            "status": "success",
            "validation": results
        }


def main():
    """Test the global orchestrator."""
    import sys
    
    project_root = Path(__file__).parent.parent
    config = {}
    
    orchestrator = PhasesOrchestrator(project_root, config)
    
    # Test main deployment flow
    result = orchestrator.execute_main_deployment_flow()
    
    print(f"\nDeployment result: {result['status']}")
    if result['status'] == 'success':
        print(f"Phases executed: {list(result['phases'].keys())}")
    else:
        print(f"Failed at: {result.get('failed_phase', 'unknown')}")


if __name__ == '__main__':
    main()
