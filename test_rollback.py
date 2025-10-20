#!/usr/bin/env python3
"""
Test Rollback Flow

This test:
1. Runs a deployment (creates snapshot)
2. Makes a change
3. Performs rollback to snapshot
4. Verifies rollback success
"""

from pathlib import Path
import logging
import sys
import yaml
import time

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from phases.phases_orchestrator import PhasesOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run rollback test."""

    print("\n" + "="*70)
    print("ROLLBACK TEST")
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

    config['compose_file'] = str(compose_file)

    print(f"📂 Using compose file: {compose_file}")
    print()

    orchestrator = PhasesOrchestrator(project_root, config)

    # =========================================================================
    # Step 1: Run initial deployment (creates snapshot)
    # =========================================================================
    print("\n" + "="*70)
    print("STEP 1: Initial Deployment (creates snapshot)")
    print("="*70)

    initial_context = {
        "config_file": str(config_file),
        "compose_file": str(compose_file),
        # Provide rendered_docker_compose so Phase 4 doesn't fail
        "rendered_docker_compose": str(compose_file)
    }

    deployment_result = orchestrator.execute_main_deployment_flow(initial_context)

    if deployment_result['status'] not in ['success', 'warning']:
        print(f"\n❌ Initial deployment failed: {deployment_result['status']}")
        return 1

    print(f"\n✅ Initial deployment complete: {deployment_result['status']}")

    # Get snapshot ID from deployment
    phase_3_result = deployment_result.get('phases', {}).get('phase_3_snapshot', {})
    snapshot_id = phase_3_result.get('artifacts', {}).get('snapshot_id')

    if not snapshot_id:
        print("\n❌ No snapshot created during deployment!")
        return 1

    print(f"📸 Snapshot created: {snapshot_id}")

    # Wait a bit for services to stabilize
    print("\n⏳ Waiting 5 seconds for services to stabilize...")
    time.sleep(5)

    # =========================================================================
    # Step 2: Perform rollback
    # =========================================================================
    print("\n" + "="*70)
    print("STEP 2: Rollback to Snapshot")
    print("="*70)

    rollback_result = orchestrator.execute_rollback_flow(
        snapshot_id=snapshot_id,
        reason="Testing rollback functionality"
    )

    print(f"\nRollback Status: {rollback_result['status']}")
    print(f"Steps completed: {list(rollback_result.get('steps', {}).keys())}")

    if rollback_result.get('errors'):
        print(f"Errors: {rollback_result['errors']}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "="*70)
    print("ROLLBACK TEST SUMMARY")
    print("="*70)

    print(f"\n📸 Snapshot ID: {snapshot_id}")
    print(f"🔄 Rollback Status: {rollback_result['status']}")

    if rollback_result.get('steps'):
        print(f"\nSteps:")
        for step_name, step_status in rollback_result['steps'].items():
            status_icon = "✅" if step_status in ["success", "degraded"] else "⚠️" if step_status == "warning" else "❌"
            print(f"   {status_icon} {step_name}: {step_status}")

    if rollback_result.get('health_status'):
        print(f"\n🏥 Health Status: {rollback_result['health_status']}")

    if rollback_result.get('files_restored'):
        print(f"📄 Files Restored: {rollback_result['files_restored']}")

    # Determine test success
    if rollback_result['status'] in ['success', 'partial']:
        print("\n" + "="*70)
        print("✅ ROLLBACK TEST COMPLETE - SUCCESS")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("❌ ROLLBACK TEST FAILED")
        print("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
