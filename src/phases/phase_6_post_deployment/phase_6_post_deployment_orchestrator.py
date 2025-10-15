#!/usr/bin/env python3
"""
Post-Deployment
Sequence: 60
Status: IMPLEMENTED

Finalize deployment and cleanup
"""

from pathlib import Path
from typing import Dict, Any
import logging
import sys

# Import library units
sys.path.insert(0, str(Path(__file__).parent.parent / "libraries"))
from reporting.status_reporter import StatusReporter
from reporting.metadata_logger import MetadataLogger
from cleanup.cleanup_handler import CleanupHandler

logger = logging.getLogger(__name__)


class Phase6PostDeploymentOrchestrator:
    """
    Post-Deployment
    
    Status: PLANNED
    Sequence: 60
    
    Finalize deployment and cleanup
    """
    
    PHASE_ID = "phase_6_post_deployment"
    PHASE_SEQUENCE = 60
    PHASE_NAME = "Post-Deployment"
    
    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        Initialize Post-Deployment.
        
        Args:
            project_root: Root directory of the project
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config
        self.phase_dir = project_root / "runtime" / "phase_6_post_deployment"
        self.outputs_dir = self.phase_dir / "outputs"
        
        # Ensure outputs directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Post-Deployment.
        
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
            "messages": []
        }
        
        # Execute steps in sequence:
        # Step 10: Report Deployment Status
        step_result = self._step_10_report_deployment_status(context)
        result['artifacts'].update(step_result.get('artifacts', {}))
        if step_result.get('status') != 'success':
            result['status'] = 'failed'
            result['messages'].extend(step_result.get('messages', []))

        # Step 20: Log Deployment Metadata
        step_result = self._step_20_log_deployment_metadata(context)
        result['artifacts'].update(step_result.get('artifacts', {}))
        if step_result.get('status') != 'success':
            result['status'] = 'failed'
            result['messages'].extend(step_result.get('messages', []))

        # Step 30: Cleanup Temporary Files
        step_result = self._step_30_cleanup_temporary_files(context)
        result['artifacts'].update(step_result.get('artifacts', {}))
        if step_result.get('status') != 'success':
            result['status'] = 'failed'
            result['messages'].extend(step_result.get('messages', []))

        # Final status
        success_icon = "✅" if result['status'] == 'success' else "❌"
        logger.info(f"{success_icon} {self.PHASE_NAME} complete")
        logger.info(f"\nStatus: {result['status']}")
        logger.info(f"Artifacts: {len(result['artifacts'])}")
        for key, value in result['artifacts'].items():
            logger.info(f"  {key}: {value}")
        
        return result
    

    def _step_10_report_deployment_status(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 10: Report Deployment Status
        
        Generate and report final deployment status
        """
        logger.info(f"  Step 10: Report Deployment Status")
        
        try:
            reporter = StatusReporter()
            
            # Generate JSON report
            report = reporter.generate_report(context)
            report_path = self.outputs_dir / "deployment_report.json"
            
            import json
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"    Deployment report: {report_path}")
            
            # Generate text report
            text_report = reporter.generate_text_report(context)
            text_path = self.outputs_dir / "deployment_report.txt"
            
            with open(text_path, 'w') as f:
                f.write(text_report)
            
            logger.info(f"    Text report: {text_path}")
            
            # Print summary to console
            reporter.print_summary(context)
            
            # Extract key metrics
            deployment_status = report.get('deployment_status', {})
            phases = report.get('phases', {})
            services = report.get('services', {})
            
            success_icon = "✅" if deployment_status.get('success') else "❌"
            logger.info(f"    {success_icon} Status: {deployment_status.get('success', False)}")
            logger.info(f"    Phases: {phases.get('completed', [])} completed")
            logger.info(f"    Services: {services.get('deployed', 0)} deployed, "
                       f"{services.get('healthy', 0)} healthy")
            
            return {
                "status": "success",
                "artifacts": {
                    "deployment_report_json": str(report_path),
                    "deployment_report_text": str(text_path),
                    "deployment_success": deployment_status.get('success', False),
                    "phases_completed": len(phases.get('completed', [])),
                    "services_deployed": services.get('deployed', 0)
                },
                "messages": []
            }
            
        except Exception as e:
            logger.error(f"Failed to report deployment status: {e}")
            return {
                "status": "failed",
                "artifacts": {},
                "messages": [str(e)]
            }

    def _step_20_log_deployment_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 20: Log Deployment Metadata
        
        Log deployment metadata for audit trail
        """
        logger.info(f"  Step 20: Log Deployment Metadata")
        
        try:
            metadata_logger = MetadataLogger(config={'log_format': 'json'})
            
            # Log deployment metadata
            log_path = self.outputs_dir / "deployment_history.log"
            success = metadata_logger.log_deployment(context, log_path)
            
            if success:
                logger.info(f"    Metadata logged to: {log_path}")
                
                # Read recent entries for verification
                recent_entries = metadata_logger.read_log(log_path, limit=1)
                if recent_entries:
                    last_entry = recent_entries[0]
                    logger.info(f"    Last entry: project={last_entry.get('project_name')}, "
                               f"status={last_entry.get('deployment_status')}")
            else:
                logger.warning("    Failed to log metadata")
            
            return {
                "status": "success",
                "artifacts": {
                    "deployment_log": str(log_path),
                    "metadata_logged": success
                },
                "messages": []
            }
            
        except Exception as e:
            logger.error(f"Failed to log deployment metadata: {e}")
            return {
                "status": "failed",
                "artifacts": {},
                "messages": [str(e)]
            }

    def _step_30_cleanup_temporary_files(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 30: Cleanup Temporary Files
        
        Clean up temporary files and resources
        """
        logger.info(f"  Step 30: Cleanup Temporary Files")
        
        try:
            cleanup_handler = CleanupHandler(config={'dry_run': False})
            
            # Clean up temporary files from template rendering
            template_temp_dir = self.project_root / "runtime" / "phase_2_template_rendering" / "temp"
            if template_temp_dir.exists():
                result = cleanup_handler.cleanup(
                    template_temp_dir,
                    patterns=['*.tmp', '*.backup', '*.bak'],
                    recursive=True
                )
                logger.info(f"    Template cleanup: {result.files_removed} files, "
                           f"{result.space_freed_bytes} bytes freed")
            
            # Clean up old snapshots (keep 5 most recent)
            snapshots_dir = self.project_root / "runtime" / "phase_3_snapshot" / "outputs"
            if snapshots_dir.exists():
                result = cleanup_handler.cleanup_old_artifacts(
                    snapshots_dir,
                    keep_count=5,
                    pattern='snapshot_*'
                )
                logger.info(f"    Snapshot cleanup: kept 5 newest, removed {result.files_removed + result.directories_removed}")
            
            # Clean up old health reports (keep 5 most recent)
            health_dir = self.project_root / "runtime" / "phase_5_health_verification" / "outputs"
            if health_dir.exists():
                result = cleanup_handler.cleanup_old_artifacts(
                    health_dir,
                    keep_count=5,
                    pattern='health_report_*'
                )
                logger.info(f"    Health report cleanup: kept 5 newest, removed {result.files_removed + result.directories_removed}")
            
            logger.info(f"    Cleanup complete")
            
            return {
                "status": "success",
                "artifacts": {
                    "cleanup_completed": True
                },
                "messages": []
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup temporary files: {e}")
            return {
                "status": "failed",
                "artifacts": {},
                "messages": [str(e)]
            }


def main():
    """Test the phase orchestrator."""
    from pathlib import Path
    import json
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    project_root = Path(__file__).parent.parent.parent
    config = {
        "project_name": "test-app",
        "environment": "staging",
        "domain": "test.example.com",
        "port": 8080
    }
    
    # Create context with sample data from previous phases
    context = {
        "config": config,
        "phase_results": {
            "phase_1_preflight": {"status": "success"},
            "phase_2_template_rendering": {"status": "success"},
            "phase_3_snapshot": {
                "status": "success",
                "artifacts": {"snapshot_id": "snap_test_20251015"}
            },
            "phase_4_deployment": {
                "status": "success",
                "artifacts": {"services_deployed": 3}
            },
            "phase_5_health_verification": {
                "status": "success",
                "artifacts": {
                    "containers_healthy": 3,
                    "endpoints_healthy": 2
                }
            }
        },
        "errors": [],
        "warnings": ["Test warning"],
        "deployment_start_time": "2025-10-15T22:00:00"
    }
    
    orchestrator = Phase6PostDeploymentOrchestrator(project_root, config)
    result = orchestrator.execute(context)
    
    print(f"\n\nPhase 6 Result:")
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
