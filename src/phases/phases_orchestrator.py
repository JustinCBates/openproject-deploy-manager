#!/usr/bin/env python3
"""
Global Phases Orchestrator for deploy-manager

This orchestrator coordinates all deployment phases in sequence.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging

from .phase_1_preflight.phase_1_preflight_orchestrator import Phase1PreflightOrchestrator
from .phase_2_template_rendering.phase_2_template_rendering_orchestrator import Phase2TemplateRenderingOrchestrator
from .phase_3_snapshot.phase_3_snapshot_orchestrator import Phase3SnapshotOrchestrator
from .phase_4_deployment.phase_4_deployment_orchestrator import Phase4DeploymentOrchestrator
from .phase_5_health_verification.phase_5_health_verification_orchestrator import Phase5HealthVerificationOrchestrator
from .phase_6_post_deployment.phase_6_post_deployment_orchestrator import Phase6PostDeploymentOrchestrator

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
        
        if phase_result.get("status") != "success":
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
        
        if phase_result.get("status") != "success":
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
    
    def execute_rollback_flow(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Execute rollback to a previous snapshot.
        
        Args:
            snapshot_id: ID of snapshot to rollback to
            
        Returns:
            Dict with rollback results
        """
        logger.info("=" * 70)
        logger.info(f"ROLLBACK FLOW - Snapshot: {snapshot_id}")
        logger.info("=" * 70)
        
        # TODO: Implement rollback logic
        # 1. Stop current deployment
        # 2. Restore snapshot configuration
        # 3. Restart services with previous config
        # 4. Verify rollback success
        
        return {
            "status": "not_implemented",
            "message": "Rollback flow not yet implemented"
        }
    
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
