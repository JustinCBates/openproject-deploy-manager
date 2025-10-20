# Deploy Manager CLI

Command-line interface for managing Docker deployments with rollback capability.

## Installation

```bash
# Install Click dependency (if not already installed)
pip install click

# Make CLI executable
chmod +x cli/deploy_cli.py

# Create symlink (optional)
ln -s $(pwd)/cli/deploy_cli.py /usr/local/bin/deploy-cli
```

## Usage

### Deploy Application

Deploy with all 6 phases (preflight, templates, snapshot, deployment, health, post-deployment):

```bash
# Full deployment
python3 cli/deploy_cli.py deploy -c config.yml -f docker-compose.yml

# Validation only (dry-run)
python3 cli/deploy_cli.py deploy -c config.yml --dry-run

# Skip health checks (faster)
python3 cli/deploy_cli.py deploy -c config.yml -f docker-compose.yml --skip-health
```

### Rollback to Snapshot

Rollback to a previous deployment state:

```bash
# Interactive (asks for confirmation)
python3 cli/deploy_cli.py rollback snap_myapp_20251015_123456

# With custom reason
python3 cli/deploy_cli.py rollback snap_myapp_20251015_123456 -r "Bug in v2.0"

# Skip confirmation
python3 cli/deploy_cli.py rollback snap_myapp_20251015_123456 -y

# With config and compose file
python3 cli/deploy_cli.py rollback snap_myapp_20251015_123456 -c config.yml -f docker-compose.yml
```

### Manage Snapshots

List, show, and manage deployment snapshots:

```bash
# List snapshots (default: 10 most recent)
python3 cli/deploy_cli.py snapshot list

# List specific number
python3 cli/deploy_cli.py snapshot list -n 5

# JSON output
python3 cli/deploy_cli.py snapshot list --json-format

# Show detailed snapshot info
python3 cli/deploy_cli.py snapshot show snap_myapp_20251015_123456

# Show in JSON format
python3 cli/deploy_cli.py snapshot show snap_myapp_20251015_123456 --json-format
```

### Health Check

Run health checks on current deployment:

```bash
# Basic health check
python3 cli/deploy_cli.py health

# With configuration
python3 cli/deploy_cli.py health -c config.yml
```

Checks performed:
- Container health status
- HTTP/HTTPS endpoint availability
- Database connectivity
- Service connectivity

### Deployment Status

Show deployment status and history:

```bash
# Show status
python3 cli/deploy_cli.py status

# With configuration
python3 cli/deploy_cli.py status -c config.yml

# JSON output
python3 cli/deploy_cli.py status --json-format
```

Displays:
- Recent deployment history (last 5 events)
- Recent snapshots (last 3)
- Deployment/rollback events

## Commands Reference

### `deploy`

Deploy application with all 6 phases.

**Options:**
- `-c, --config PATH` - Configuration file (YAML)
- `-f, --compose-file PATH` - Docker Compose file
- `--dry-run` - Validate only, do not deploy
- `--skip-health` - Skip health verification

**Phases executed:**
1. Preflight Validation
2. Template Rendering
3. Snapshot Creation
4. Deployment Execution
5. Health Verification
6. Post-Deployment Reporting

### `rollback`

Rollback to a previous snapshot.

**Arguments:**
- `SNAPSHOT_ID` - ID of snapshot to rollback to

**Options:**
- `-c, --config PATH` - Configuration file (YAML)
- `-f, --compose-file PATH` - Docker Compose file
- `-r, --reason TEXT` - Reason for rollback (for audit log)
- `-y, --yes` - Skip confirmation prompt

**Steps executed:**
1. Load snapshot
2. Stop current deployment
3. Restore configuration files
4. Restart services
5. Verify health
6. Log rollback event

### `snapshot list`

List available snapshots.

**Options:**
- `-n, --limit INTEGER` - Number of snapshots to show (default: 10)
- `--json-format` - Output in JSON format

### `snapshot show`

Show detailed snapshot information.

**Arguments:**
- `SNAPSHOT_ID` - ID of snapshot to show

**Options:**
- `--json-format` - Output in JSON format

### `health`

Run health checks on current deployment.

**Options:**
- `-c, --config PATH` - Configuration file (YAML)

### `status`

Show deployment status and recent history.

**Options:**
- `-c, --config PATH` - Configuration file (YAML)
- `--json-format` - Output in JSON format

## Examples

### Complete Deployment Workflow

```bash
# 1. Validate configuration
python3 cli/deploy_cli.py deploy -c config.yml --dry-run

# 2. Deploy application
python3 cli/deploy_cli.py deploy -c config.yml -f docker-compose.yml

# 3. Check health
python3 cli/deploy_cli.py health -c config.yml

# 4. View status
python3 cli/deploy_cli.py status

# 5. If issues occur, rollback
python3 cli/deploy_cli.py rollback snap_myapp_20251015_123456 -r "Performance issues"
```

### Snapshot Management

```bash
# List all snapshots
python3 cli/deploy_cli.py snapshot list

# View specific snapshot details
python3 cli/deploy_cli.py snapshot show snap_myapp_20251015_123456

# Rollback to snapshot
python3 cli/deploy_cli.py rollback snap_myapp_20251015_123456
```

### Automation

```bash
# Deploy with JSON output for parsing
python3 cli/deploy_cli.py deploy -c config.yml -f docker-compose.yml 2>&1 | tee deploy.log

# Check status programmatically
python3 cli/deploy_cli.py status --json-format | jq '.[] | select(.deployment_status == "success")'

# List snapshots for backup
python3 cli/deploy_cli.py snapshot list --json-format > snapshots.json
```

## Exit Codes

- `0` - Success
- `1` - Failure (deployment failed, rollback failed, etc.)

## Output Format

### Standard Output
- Uses emoji icons for visual feedback
- Structured sections with separators
- Color-coded status messages (if terminal supports it)

### JSON Output
- Machine-readable format
- Includes all metadata
- Suitable for automation and parsing

## Logging

All operations are logged to:
- `runtime/phase_6_post_deployment/outputs/deployment_history.log`

This provides a complete audit trail of all deployments and rollbacks.

## Error Handling

The CLI provides clear error messages:
- Configuration file not found
- Snapshot not found
- Deployment failures
- Rollback failures

All errors are logged for debugging.

## Tips

1. **Always validate first**: Use `--dry-run` to validate before deploying
2. **Keep snapshots**: Snapshots enable instant rollback
3. **Monitor health**: Run health checks after deployment
4. **Use rollback reasons**: Document why rollbacks occur for audit trail
5. **Check status**: Review deployment history regularly

## Troubleshooting

**CLI not working:**
```bash
# Ensure Click is installed
pip install click

# Check Python path
python3 -c "import sys; print(sys.path)"

# Run from project root
cd /path/to/deploy-manager
python3 cli/deploy_cli.py --help
```

**Snapshot not found:**
```bash
# Check snapshot directory exists
ls runtime/phase_3_snapshot/outputs/snapshots/

# List available snapshots
python3 cli/deploy_cli.py snapshot list
```

**Rollback fails:**
```bash
# Check compose file path
python3 cli/deploy_cli.py rollback SNAPSHOT_ID -c config.yml -f docker-compose.yml

# Check logs
tail -f runtime/phase_6_post_deployment/outputs/deployment_history.log
```

## Version

Deploy Manager CLI v1.0.0
