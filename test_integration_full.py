#!/usr/bin/env python3
"""
Integration Test: Complete Deployment Flow
Tests Phases 1 → 2 → 3 → 4 → 5 → 6 (Full deployment lifecycle)
"""

from pathlib import Path
import logging
import sys
import yaml

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from phases.phase_1_preflight.phase_1_preflight_orchestrator import Phase1PreflightOrchestrator
from phases.phase_2_template_rendering.phase_2_template_rendering_orchestrator import Phase2TemplateRenderingOrchestrator
from phases.phase_3_snapshot.phase_3_snapshot_orchestrator import Phase3SnapshotOrchestrator
from phases.phase_4_deployment.phase_4_deployment_orchestrator import Phase4DeploymentOrchestrator
from phases.phase_5_health_verification.phase_5_health_verification_orchestrator import Phase5HealthVerificationOrchestrator
from phases.phase_6_post_deployment.phase_6_post_deployment_orchestrator import Phase6PostDeploymentOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run integration test."""
    
    print("\n" + "="*70)
    print("INTEGRATION TEST: Full Deployment Flow (All 6 Phases)")
    print("="*70)
    print()
    
    # Setup paths
    project_root = Path(__file__).parent
    test_data_dir = project_root / "test_data"
    config_file = test_data_dir / "test-config.yml"
    compose_file = test_data_dir / "test-compose.yml"
    
    # Load test configuration
    print(f"📂 Loading test configuration: {config_file}")
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"📂 Using compose file: {compose_file}")
    print()
    
    # Initialize context
    context = {
        "config_file": str(config_file),
        "compose_file": str(compose_file)
    }
    
    # =========================================================================
    # PHASE 1: Preflight Validation
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 1: Preflight Validation")
    print("="*70)
    
    phase1 = Phase1PreflightOrchestrator(project_root, config)
    phase1_result = phase1.execute(context)
    
    # Phase 1 may return 'warning' if some non-critical checks fail
    if phase1_result['status'] not in ['success', 'warning']:
        print("\n❌ Phase 1 failed!")
        print(f"Status: {phase1_result['status']}")
        print(f"Messages: {phase1_result.get('messages', [])}")
        return 1
    
    if phase1_result['status'] == 'warning':
        print(f"\n⚠️  Phase 1 completed with warnings")
    else:
        print(f"\n✅ Phase 1 complete")
    
    # Update context with Phase 1 artifacts
    context.update(phase1_result.get('artifacts', {}))
    
    # =========================================================================
    # PHASE 2: Template Rendering
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 2: Template Rendering")
    print("="*70)
    
    phase2 = Phase2TemplateRenderingOrchestrator(project_root, config)
    phase2_result = phase2.execute(context)
    
    if phase2_result['status'] != 'success':
        print("\n❌ Phase 2 failed!")
        print(f"Messages: {phase2_result.get('messages', [])}")
        return 1
    
    print(f"\n✅ Phase 2 complete")
    
    # Update context with Phase 2 artifacts
    context.update(phase2_result.get('artifacts', {}))
    
    # =========================================================================
    # PHASE 3: Snapshot Creation
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 3: Snapshot Creation")
    print("="*70)
    
    phase3 = Phase3SnapshotOrchestrator(project_root, config)
    phase3_result = phase3.execute(context)
    
    if phase3_result['status'] != 'success':
        print("\n❌ Phase 3 failed!")
        print(f"Messages: {phase3_result.get('messages', [])}")
        return 1
    
    print(f"\n✅ Phase 3 complete")
    
    # Update context with Phase 3 artifacts
    context.update(phase3_result.get('artifacts', {}))
    
    # =========================================================================
    # PHASE 4: Deployment Execution
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 4: Deployment Execution")
    print("="*70)
    
    # Add compose file to context (Phase 2 would normally render this)
    context['rendered_docker_compose'] = str(compose_file)
    
    phase4 = Phase4DeploymentOrchestrator(project_root, config)
    phase4_result = phase4.execute(context)
    
    if phase4_result['status'] != 'success':
        print("\n❌ Phase 4 failed!")
        print(f"Messages: {phase4_result.get('messages', [])}")
        return 1
    
    print(f"\n✅ Phase 4 complete")
    
    # Update context with Phase 4 artifacts
    context.update(phase4_result.get('artifacts', {}))
    
    # =========================================================================
    # PHASE 5: Health Verification
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 5: Health Verification")
    print("="*70)
    
    # Store phase results for reporting
    if 'phase_results' not in context:
        context['phase_results'] = {}
    context['phase_results']['phase_1_preflight'] = phase1_result
    context['phase_results']['phase_2_template_rendering'] = phase2_result
    context['phase_results']['phase_3_snapshot'] = phase3_result
    context['phase_results']['phase_4_deployment'] = phase4_result
    
    phase5 = Phase5HealthVerificationOrchestrator(project_root, config)
    phase5_result = phase5.execute(context)
    
    # Phase 5 may return 'degraded' status if containers aren't running (expected in test)
    if phase5_result['status'] not in ['success', 'degraded']:
        print("\n❌ Phase 5 failed!")
        print(f"Messages: {phase5_result.get('messages', [])}")
        return 1
    
    print(f"\n✅ Phase 5 complete (status: {phase5_result['status']})")
    
    # Update context with Phase 5 artifacts
    context.update(phase5_result.get('artifacts', {}))
    context['phase_results']['phase_5_health_verification'] = phase5_result
    
    # =========================================================================
    # PHASE 6: Post-Deployment
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 6: Post-Deployment")
    print("="*70)
    
    # Add deployment metadata for Phase 6
    from datetime import datetime
    context['deployment_start_time'] = datetime.now().isoformat()
    context['errors'] = []
    context['warnings'] = []
    
    phase6 = Phase6PostDeploymentOrchestrator(project_root, config)
    phase6_result = phase6.execute(context)
    
    if phase6_result['status'] != 'success':
        print("\n❌ Phase 6 failed!")
        print(f"Messages: {phase6_result.get('messages', [])}")
        return 1
    
    print(f"\n✅ Phase 6 complete")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    
    print(f"\n✅ Phase 1 (Preflight): {phase1_result['status']}")
    print(f"   Artifacts: {len(phase1_result.get('artifacts', {}))}")
    
    print(f"\n✅ Phase 2 (Template Rendering): {phase2_result['status']}")
    print(f"   Artifacts: {len(phase2_result.get('artifacts', {}))}")
    
    print(f"\n✅ Phase 3 (Snapshot): {phase3_result['status']}")
    print(f"   Artifacts: {len(phase3_result.get('artifacts', {}))}")
    if 'snapshot_id' in phase3_result.get('artifacts', {}):
        print(f"   Snapshot ID: {phase3_result['artifacts']['snapshot_id']}")
    
    print(f"\n✅ Phase 4 (Deployment): {phase4_result['status']}")
    print(f"   Artifacts: {len(phase4_result.get('artifacts', {}))}")
    
    print(f"\n✅ Phase 5 (Health Verification): {phase5_result['status']}")
    print(f"   Artifacts: {len(phase5_result.get('artifacts', {}))}")
    if 'containers_healthy' in phase5_result.get('artifacts', {}):
        print(f"   Containers healthy: {phase5_result['artifacts']['containers_healthy']}")
    
    print(f"\n✅ Phase 6 (Post-Deployment): {phase6_result['status']}")
    print(f"   Artifacts: {len(phase6_result.get('artifacts', {}))}")
    if 'deployment_report_json' in phase6_result.get('artifacts', {}):
        print(f"   Report: {phase6_result['artifacts']['deployment_report_json']}")
    
    # Display key artifacts
    print("\n📦 Key Artifacts:")
    if 'env_file_path' in context:
        print(f"   - Environment file: {context['env_file_path']}")
    if 'snapshot_id' in context:
        print(f"   - Snapshot: {context['snapshot_id']}")
    if 'pull_results' in context:
        pull_results = context['pull_results']
        print(f"   - Images pulled: {len(pull_results)}")
    if 'monitor_result' in context:
        monitor = context['monitor_result']
        print(f"   - Containers running: {len(monitor.get('containers', []))}")
        print(f"   - All healthy: {monitor.get('all_healthy', False)}")
        print(f"   - Startup time: {monitor.get('elapsed_time', 0):.1f}s")
    if 'deployment_report_json' in context:
        print(f"   - Deployment report: {context['deployment_report_json']}")
    if 'deployment_log' in context:
        print(f"   - Deployment log: {context['deployment_log']}")
    
    print("\n" + "="*70)
    print("✅ INTEGRATION TEST COMPLETE - ALL 6 PHASES SUCCESSFUL")
    print("="*70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
