#!/usr/bin/env python3
"""
Deploy Manager CLI

Command-line interface for deployment management with rollback capability.
"""

import click
import sys
import yaml
import json
from pathlib import Path
from typing import Optional
import logging

# Add src to path
cli_dir = Path(__file__).parent
project_root = cli_dir.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from phases.phases_orchestrator import PhasesOrchestrator
from phases.libraries.snapshot.snapshot_storer import SnapshotStorer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_file: Optional[Path]) -> dict:
    """Load configuration from YAML file."""
    if not config_file:
        click.echo("⚠️  No configuration file specified, using defaults")
        return {}
    
    if not config_file.exists():
        click.echo(f"❌ Configuration file not found: {config_file}", err=True)
        sys.exit(1)
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        click.echo(f"✅ Loaded configuration from: {config_file}")
        return config
    except Exception as e:
        click.echo(f"❌ Failed to load configuration: {e}", err=True)
        sys.exit(1)


@click.group()
@click.version_option(version='1.0.0', prog_name='deploy-manager')
def cli():
    """
    Deploy Manager - Deployment orchestration with rollback capability.
    
    Manages Docker deployments with comprehensive health checking,
    snapshotting, and rollback functionality.
    """
    pass


@cli.command()
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Configuration file (YAML)'
)
@click.option(
    '--compose-file', '-f',
    type=click.Path(exists=True, path_type=Path),
    help='Docker Compose file'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Validate only, do not deploy'
)
@click.option(
    '--skip-health',
    is_flag=True,
    help='Skip health verification (faster, less safe)'
)
def deploy(config: Optional[Path], compose_file: Optional[Path], dry_run: bool, skip_health: bool):
    """
    Deploy application with all 6 phases.
    
    Executes complete deployment lifecycle:
    - Preflight validation
    - Template rendering
    - Snapshot creation
    - Deployment execution
    - Health verification
    - Post-deployment reporting
    
    Example:
        deploy-cli deploy -c config.yml -f docker-compose.yml
    """
    click.echo("\n" + "=" * 70)
    click.echo("🚀 DEPLOY MANAGER - Full Deployment")
    click.echo("=" * 70 + "\n")
    
    # Load configuration
    config_data = load_config(config)
    
    # Add compose file to config if provided
    if compose_file:
        config_data['compose_file'] = str(compose_file)
        click.echo(f"📄 Compose file: {compose_file}")
    
    # Initialize orchestrator
    orchestrator = PhasesOrchestrator(project_root, config_data)
    
    if dry_run:
        click.echo("🔍 Running validation only (dry-run mode)\n")
        result = orchestrator.execute_validation_only_flow()
    else:
        click.echo("🚀 Starting full deployment\n")
        
        # Prepare initial context
        initial_context = {}
        if config:
            initial_context['config_file'] = str(config)
        if compose_file:
            initial_context['compose_file'] = str(compose_file)
        if 'compose_file' in config_data:
            initial_context['rendered_docker_compose'] = config_data['compose_file']
        
        result = orchestrator.execute_main_deployment_flow(initial_context)
    
    # Display results
    click.echo("\n" + "=" * 70)
    
    status = result.get('status', 'unknown')
    if status == 'success':
        click.echo("✅ DEPLOYMENT SUCCESSFUL")
        
        # Show snapshot info
        phases = result.get('phases', {})
        phase_3 = phases.get('phase_3_snapshot', {})
        snapshot_id = phase_3.get('artifacts', {}).get('snapshot_id')
        
        if snapshot_id:
            click.echo(f"\n📸 Snapshot created: {snapshot_id}")
            click.echo(f"   To rollback: deploy-cli rollback {snapshot_id}")
        
        # Show health info
        phase_5 = phases.get('phase_5_health_verification', {})
        health_status = phase_5.get('status', 'unknown')
        click.echo(f"\n🏥 Health status: {health_status}")
        
    elif status == 'failed':
        click.echo("❌ DEPLOYMENT FAILED")
        failed_phase = result.get('failed_phase', 'unknown')
        click.echo(f"\n   Failed at: {failed_phase}")
        sys.exit(1)
    else:
        click.echo(f"⚠️  Deployment completed with status: {status}")
    
    click.echo("=" * 70 + "\n")


@cli.command()
@click.argument('snapshot_id')
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Configuration file (YAML)'
)
@click.option(
    '--compose-file', '-f',
    type=click.Path(exists=True, path_type=Path),
    help='Docker Compose file'
)
@click.option(
    '--reason', '-r',
    default='Manual rollback via CLI',
    help='Reason for rollback (for audit log)'
)
@click.option(
    '--yes', '-y',
    is_flag=True,
    help='Skip confirmation prompt'
)
def rollback(snapshot_id: str, config: Optional[Path], compose_file: Optional[Path], 
             reason: str, yes: bool):
    """
    Rollback to a previous snapshot.
    
    Restores configuration and services to a previous state:
    - Loads snapshot
    - Stops current deployment
    - Restores configuration files
    - Restarts services
    - Verifies health
    - Logs rollback event
    
    Example:
        deploy-cli rollback snap_myapp_20251015_123456
    """
    click.echo("\n" + "=" * 70)
    click.echo("🔄 DEPLOY MANAGER - Rollback")
    click.echo("=" * 70 + "\n")
    
    click.echo(f"📸 Snapshot: {snapshot_id}")
    click.echo(f"📝 Reason: {reason}\n")
    
    # Confirm rollback
    if not yes:
        if not click.confirm("⚠️  This will stop the current deployment and rollback. Continue?"):
            click.echo("❌ Rollback cancelled")
            return
    
    # Load configuration
    config_data = load_config(config)
    
    # Add compose file to config if provided
    if compose_file:
        config_data['compose_file'] = str(compose_file)
    
    # Initialize orchestrator
    orchestrator = PhasesOrchestrator(project_root, config_data)
    
    # Execute rollback
    click.echo("🔄 Executing rollback...\n")
    result = orchestrator.execute_rollback_flow(snapshot_id, reason)
    
    # Display results
    click.echo("\n" + "=" * 70)
    
    status = result.get('status', 'unknown')
    if status == 'success':
        click.echo("✅ ROLLBACK SUCCESSFUL")
        
        health_status = result.get('health_status', 'unknown')
        click.echo(f"\n🏥 Health status: {health_status}")
        
        files_restored = result.get('files_restored', 0)
        if files_restored:
            click.echo(f"📄 Files restored: {files_restored}")
        
    elif status == 'partial':
        click.echo("⚠️  ROLLBACK PARTIALLY SUCCESSFUL")
        click.echo("\n   Some steps failed, but deployment may be functional")
        
        errors = result.get('errors', [])
        if errors:
            click.echo("\n   Errors:")
            for error in errors:
                click.echo(f"     - {error}")
    else:
        click.echo("❌ ROLLBACK FAILED")
        
        errors = result.get('errors', [])
        if errors:
            click.echo("\n   Errors:")
            for error in errors:
                click.echo(f"     - {error}")
        sys.exit(1)
    
    click.echo("=" * 70 + "\n")


@cli.group()
def snapshot():
    """Manage deployment snapshots."""
    pass


@snapshot.command('list')
@click.option(
    '--limit', '-n',
    type=int,
    default=10,
    help='Number of snapshots to show'
)
@click.option(
    '--json-format',
    is_flag=True,
    help='Output in JSON format'
)
def snapshot_list(limit: int, json_format: bool):
    """
    List available snapshots.
    
    Shows all available snapshots sorted by timestamp (newest first).
    
    Example:
        deploy-cli snapshot list -n 5
    """
    snapshot_dir = project_root / "runtime" / "phase_3_snapshot" / "outputs" / "snapshots"
    
    if not snapshot_dir.exists():
        click.echo("⚠️  No snapshots directory found")
        return
    
    storer = SnapshotStorer(config={'snapshot_dir': str(snapshot_dir)})
    snapshots = storer.list()
    
    if not snapshots:
        click.echo("📸 No snapshots found")
        return
    
    # Limit results
    snapshots = snapshots[:limit]
    
    if json_format:
        # JSON output
        output = [
            {
                'id': s.id,
                'timestamp': s.timestamp,
                'project_name': s.project_name,
                'containers': len(s.containers),
                'networks': len(s.networks),
                'volumes': len(s.volumes),
                'config_files': len(s.config_files)
            }
            for s in snapshots
        ]
        click.echo(json.dumps(output, indent=2))
    else:
        # Human-readable output
        click.echo(f"\n📸 Available Snapshots ({len(snapshots)} shown):\n")
        click.echo("=" * 70)
        
        for snapshot in snapshots:
            click.echo(f"\n🔹 {snapshot.id}")
            click.echo(f"   Time: {snapshot.timestamp}")
            click.echo(f"   Project: {snapshot.project_name}")
            click.echo(f"   Containers: {len(snapshot.containers)}, "
                      f"Networks: {len(snapshot.networks)}, "
                      f"Volumes: {len(snapshot.volumes)}")
            click.echo(f"   Config files: {len(snapshot.config_files)}")
        
        click.echo("\n" + "=" * 70 + "\n")


@snapshot.command('show')
@click.argument('snapshot_id')
@click.option(
    '--json-format',
    is_flag=True,
    help='Output in JSON format'
)
def snapshot_show(snapshot_id: str, json_format: bool):
    """
    Show detailed snapshot information.
    
    Example:
        deploy-cli snapshot show snap_myapp_20251015_123456
    """
    snapshot_dir = project_root / "runtime" / "phase_3_snapshot" / "outputs" / "snapshots"
    storer = SnapshotStorer(config={'snapshot_dir': str(snapshot_dir)})
    
    result = storer.load(snapshot_id)
    
    if not result.success:
        click.echo(f"❌ Failed to load snapshot: {result.error}", err=True)
        sys.exit(1)
    
    snapshot = result.snapshot
    
    if json_format:
        click.echo(json.dumps(snapshot.to_dict(), indent=2))
    else:
        click.echo(f"\n📸 Snapshot: {snapshot.id}\n")
        click.echo("=" * 70)
        click.echo(f"Timestamp: {snapshot.timestamp}")
        click.echo(f"Project: {snapshot.project_name}")
        
        if snapshot.containers:
            click.echo(f"\nContainers ({len(snapshot.containers)}):")
            for container in snapshot.containers:
                click.echo(f"  - {container.get('name', 'unknown')}: {container.get('status', 'unknown')}")
        
        if snapshot.networks:
            click.echo(f"\nNetworks ({len(snapshot.networks)}):")
            for network in snapshot.networks:
                click.echo(f"  - {network.get('name', 'unknown')}")
        
        if snapshot.volumes:
            click.echo(f"\nVolumes ({len(snapshot.volumes)}):")
            for volume in snapshot.volumes:
                click.echo(f"  - {volume.get('name', 'unknown')}")
        
        if snapshot.config_files:
            click.echo(f"\nConfig Files ({len(snapshot.config_files)}):")
            for config_file in snapshot.config_files:
                click.echo(f"  - {config_file}")
        
        if snapshot.backup_dir:
            click.echo(f"\nBackup Directory: {snapshot.backup_dir}")
        
        click.echo("=" * 70 + "\n")


@cli.command()
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Configuration file (YAML)'
)
def health(config: Optional[Path]):
    """
    Run health checks on current deployment.
    
    Checks:
    - Container health status
    - HTTP/HTTPS endpoint availability
    - Database connectivity
    - Service connectivity
    
    Example:
        deploy-cli health -c config.yml
    """
    click.echo("\n" + "=" * 70)
    click.echo("🏥 DEPLOY MANAGER - Health Check")
    click.echo("=" * 70 + "\n")
    
    # Load configuration
    config_data = load_config(config)
    
    # Initialize orchestrator
    orchestrator = PhasesOrchestrator(project_root, config_data)
    
    # Run health verification
    context = {"config": config_data}
    result = orchestrator.phase_5_health_verification.execute(context)
    
    # Display results
    click.echo("\n" + "=" * 70)
    
    status = result.get('status', 'unknown')
    artifacts = result.get('artifacts', {})
    
    if status in ['success', 'degraded']:
        status_icon = "✅" if status == 'success' else "⚠️"
        click.echo(f"{status_icon} Health Status: {status.upper()}")
        
        click.echo("\n📊 Health Metrics:")
        
        containers_checked = artifacts.get('containers_checked', 0)
        containers_healthy = artifacts.get('containers_healthy', 0)
        click.echo(f"   Containers: {containers_healthy}/{containers_checked} healthy")
        
        endpoints_checked = artifacts.get('endpoints_checked', 0)
        endpoints_healthy = artifacts.get('endpoints_healthy', 0)
        click.echo(f"   Endpoints: {endpoints_healthy}/{endpoints_checked} responding")
        
        avg_response_time = artifacts.get('average_response_time_ms', 0)
        if avg_response_time > 0:
            click.echo(f"   Avg Response Time: {avg_response_time:.2f}ms")
        
    else:
        click.echo(f"❌ Health Status: {status.upper()}")
        sys.exit(1)
    
    click.echo("=" * 70 + "\n")


@cli.command()
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Configuration file (YAML)'
)
@click.option(
    '--json-format',
    is_flag=True,
    help='Output in JSON format'
)
def status(config: Optional[Path], json_format: bool):
    """
    Show deployment status and recent history.
    
    Displays:
    - Current deployment information
    - Recent deployment history
    - Available snapshots
    
    Example:
        deploy-cli status -c config.yml
    """
    click.echo("\n" + "=" * 70)
    click.echo("📊 DEPLOY MANAGER - Status")
    click.echo("=" * 70 + "\n")
    
    # Check for deployment history
    history_file = project_root / "runtime" / "phase_6_post_deployment" / "outputs" / "deployment_history.log"
    
    if history_file.exists():
        from phases.libraries.reporting.metadata_logger import MetadataLogger
        
        logger_obj = MetadataLogger(config={'log_format': 'json'})
        entries = logger_obj.read_log(history_file, limit=5)
        
        if json_format:
            click.echo(json.dumps(entries, indent=2))
        else:
            click.echo(f"📜 Recent History ({len(entries)} entries):\n")
            
            for entry in entries:
                event_type = entry.get('event_type', 'deployment')
                timestamp = entry.get('timestamp', 'unknown')
                project = entry.get('project_name', 'unknown')
                status = entry.get('deployment_status') or entry.get('status', 'unknown')
                
                icon = "🚀" if event_type == "deployment" else "🔄"
                click.echo(f"{icon} {timestamp}")
                click.echo(f"   Type: {event_type}")
                click.echo(f"   Project: {project}")
                click.echo(f"   Status: {status}")
                
                if event_type == "rollback":
                    snapshot_id = entry.get('snapshot_id', 'unknown')
                    click.echo(f"   Snapshot: {snapshot_id}")
                
                click.echo()
    else:
        click.echo("📜 No deployment history found\n")
    
    # Show available snapshots
    snapshot_dir = project_root / "runtime" / "phase_3_snapshot" / "outputs" / "snapshots"
    if snapshot_dir.exists():
        storer = SnapshotStorer(config={'snapshot_dir': str(snapshot_dir)})
        snapshots = storer.list()[:3]  # Show 3 most recent
        
        if snapshots:
            click.echo(f"📸 Recent Snapshots ({len(snapshots)} shown):\n")
            for s in snapshots:
                click.echo(f"   - {s.id} ({s.timestamp})")
            click.echo()
    
    click.echo("=" * 70 + "\n")


if __name__ == '__main__':
    cli()
