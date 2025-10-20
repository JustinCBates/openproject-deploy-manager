# Deploy Manager

Deployment orchestration for Docker Compose stacks with health checking, rollback capabilities, and live validation.

**Version**: 2.0.0
**Dual-Mode Support**: Development & Production

## Features

- **Deployment Orchestration**: Coordinate complete docker-compose lifecycle
- **Template Rendering**: Jinja2 template support for dynamic configuration (Caddyfile, nginx.conf, etc.)
- **Health Checking**: Verify services are healthy after deployment
- **Preflight Validation**: Integrate with docker-prober-utility for pre-deployment checks
- **Automatic Rollback**: Rollback on deployment failure with state snapshots
- **Progress Monitoring**: Real-time deployment progress and logging
- **Dual-Mode Operation**: Works in both development (git submodule) and production (pip package) environments

## Purpose

This is a generic, reusable deployment orchestration tool designed to work with any Docker Compose stack. It provides intelligent deployment with validation, health checking, and automatic recovery.

## Installation

### Production Mode (Pip Package)

```bash
pip install openproject-deploy-manager
```

### Development Mode (Git Submodule)

```bash
git clone https://github.com/JustinCBates/openproject-deploy-manager.git
cd openproject-deploy-manager
pip install -e ".[dev]"
```

## Usage

### Production Mode (Explicit Paths)

When installed as a pip package and called by an orchestrator:

```python
from pathlib import Path
from openproject_deploy_manager import DeploymentOrchestrator

# Orchestrator provides paths
deployer = DeploymentOrchestrator(
    config={"domain": "example.com", "postgres_password": "secret123"},
    templates_dir=Path("/opt/openproject/templates"),
    output_dir=Path("/opt/openproject/outputs"),
    compose_file=Path("/opt/openproject/docker-compose.yml"),
    snapshot_dir=Path("/opt/openproject/backups/snapshots")
)

# Render templates
result = deployer.render_templates()
print(f"Rendered {result['files_rendered']} templates")

# Create pre-deployment snapshot
snapshot = deployer.create_snapshot("pre_deploy")

# Execute deployment
result = deployer.deploy()

if result['status'] == 'success':
    print(f"Deployment successful")
else:
    print(f"Deployment failed: {result.get('message')}")
```

### Development Mode (Auto-Detected)

When running from git repository (development):

```python
from openproject_deploy_manager import DeploymentOrchestrator

# Auto-detects development mode (uses local ./templates/ and ./outputs/)
deployer = DeploymentOrchestrator(
    config={"domain": "example.com", "port": "8080"}
)

# Execute deployment
result = deployer.deploy()

if result['status'] == 'success':
    print(f"Deployment successful")
else:
    print(f"Deployment failed: {result.get('message')}")
```

### Force Development Mode

```python
# Explicitly force development mode
deployer = DeploymentOrchestrator(
    config=my_config,
    use_local_paths=True
)
```

Or via environment variable:

```bash
export OPENPROJECT_DEV_MODE=1
```

### Custom Paths in Development

```python
from pathlib import Path

# Override default paths even in development mode
deployer = DeploymentOrchestrator(
    config=my_config,
    templates_dir=Path("/custom/templates"),
    output_dir=Path("/custom/outputs"),
    use_local_paths=True
)
```

### Command Line Interface

```bash
# Deploy stack using .cfg file from Configuration Manager
deploy-manager deploy --config=interactive_config.cfg

# Alternative: Deploy using .env file
deploy-manager deploy --config=.env

# Dry run (validation only)
deploy-manager deploy --dry-run --config=interactive_config.cfg

# Deploy without prober preflight
deploy-manager deploy --no-prober --config=interactive_config.cfg

# Check deployment status
deploy-manager status

# Rollback to previous state
deploy-manager rollback
```

## Architecture

### Control Flow

```
Configuration Input (.cfg file from Configuration Manager)
    ↓
Pre-deployment Validation
    ├─ Load and parse .cfg configuration file
    ├─ Validate configuration completeness
    ├─ Check Docker daemon accessibility
    ├─ Verify port availability
    └─ Run prober preflight check (optional)
    ↓
Template Rendering
    ├─ Extract template variables from .cfg
    ├─ Render Jinja2 templates (Caddyfile, nginx.conf, etc.)
    └─ Validate rendered output syntax
    ↓
Deployment Execution
    ├─ Create deployment snapshot (for rollback)
    ├─ Convert .cfg to .env for Docker Compose
    ├─ Pull images (if requested)
    ├─ docker-compose up -d
    └─ Monitor service startup
    ↓
Health Checking
    ├─ Wait for Docker health checks
    ├─ Probe HTTP/HTTPS endpoints
```
    └─ Verify service connectivity
    ↓
Post-deployment
    ├─ Report deployment status
    ├─ Log deployment metadata
    └─ Clean up temporary files
    ↓
Deployment Result (Success/Failure)
```

## Configuration Integration

### Primary Input: `.cfg` File

The Deploy Manager consumes the `interactive_config.cfg` file produced by the Configuration Manager:

```bash
# Example integration
config-manager configure --interactive
# → Generates: interactive_config.cfg

deploy-manager deploy --config=interactive_config.cfg
# → Reads configuration and deploys stack
```

### Configuration Loading Process

```python
class ConfigurationLoader:
    def load_cfg_file(path: Path) -> Dict[str, str]
    def convert_to_env_format() -> Dict[str, str]
    def extract_template_variables() -> Dict[str, Any]
    def validate_required_keys() -> ValidationResult
```

**Configuration Processing Flow**:
1. **Load .cfg file** → Parse bash-style key="value" pairs
2. **Validate completeness** → Check required deployment variables
3. **Convert formats** → Generate .env and template variables
4. **Template rendering** → Use variables in Jinja2 templates

### Key Configuration Categories

From `interactive_config.cfg`:

- **Core Settings**: `DOMAIN_NAME`, `OPENPROJECT_HTTPS`, `PORT`
- **Database Config**: `DATABASE_URL`, `POSTGRES_PASSWORD`
- **Proxy Settings**: `PROXY_TYPE`, `SSL_EMAIL`, `SECURITY_HEADERS_ENABLED`
- **Deployment Behavior**: `PROBER_ENABLED`, `PULL_IMAGES`, `HEALTH_CHECK_TIMEOUT`

### Components

#### 1. Deployment Orchestrator (`orchestrator.py`)
**Purpose**: Coordinate the complete deployment lifecycle

**Responsibilities**:
- Validate configuration before deployment
- Coordinate template rendering, docker-compose execution, and health checks
- Handle errors and trigger rollback on failure
- Report deployment status and logs

**Methods**:
```python
class DeploymentOrchestrator:
    def validate_deployment() -> ValidationResult
    def deploy(dry_run: bool = False, prober_enabled: bool = True) -> DeploymentResult
    def rollback() -> RollbackResult
    def get_status() -> DeploymentStatus
```

**Workflow**:
1. Pre-deployment validation (config, Docker daemon, ports, prober)
2. Template rendering (via TemplateRenderer)
3. Create deployment snapshot
4. Execute docker-compose up
5. Health checking (via HealthChecker)
6. Report results

#### 2. Template Renderer (`template_renderer.py`)
**Purpose**: Render Jinja2 templates with configuration values

**Responsibilities**:
- Load Jinja2 templates from directory
- Render templates with provided configuration
- Validate rendered output (syntax, required fields)
- Support custom filters and functions
- Handle template errors gracefully

**Methods**:
```python
class TemplateRenderer:
    def render(template_name: str, context: dict) -> str
    def render_to_file(template_name: str, output_path: Path, context: dict) -> None
    def validate_rendered(content: str, validator: Callable) -> ValidationResult
```

**Supported Templates**:
- `Caddyfile.j2`: Caddy reverse proxy configuration
- `nginx.conf.j2`: Nginx configuration
- `docker-compose.override.yml.j2`: Dynamic compose overrides
- Custom templates provided by consuming projects

**Custom Filters**:
- `to_bool`: Convert string to boolean
- `to_port`: Validate and format port numbers
- `to_domain`: Validate domain names

#### 3. Health Checker (`health_checker.py`)
**Purpose**: Validate service health after deployment

**Responsibilities**:
- Check Docker container health via Docker API
- Probe HTTP/HTTPS endpoints
- Verify database connectivity (optional)
- Wait for services to become healthy with timeout
- Report detailed health status

**Methods**:
```python
class HealthChecker:
    def check_service(service_name: str) -> HealthStatus
    def check_endpoint(url: str, timeout: int = 30) -> EndpointStatus
    def wait_for_healthy(services: List[str], timeout: int = 300) -> HealthCheckResult
```

**Health Check Strategies**:
1. **Docker Health Checks**: Use container's built-in healthcheck
2. **HTTP Probes**: GET requests to health endpoints
3. **Database Checks**: Connection tests (via pg_isready, redis-cli, etc.)
4. **Custom Checks**: Service-specific validation

**Timeout Handling**:
- Exponential backoff for retries
- Configurable timeout per service
- Fail fast on critical services

#### 4. Docker Client Wrapper (`docker_client.py`)
**Purpose**: Simplified interface to Docker SDK

**Responsibilities**:
- Wrap Docker SDK for Python with error handling
- Provide simplified interface for common operations
- Support docker-compose operations (up, down, restart)
- Monitor container logs and events
- Handle Docker API errors gracefully

**Methods**:
```python
class DockerClient:
    def compose_up(compose_file: Path, services: List[str] = None) -> ComposeResult
    def compose_down(remove_volumes: bool = False) -> ComposeResult
    def get_service_status(service_name: str) -> ServiceStatus
    def get_container_logs(container_id: str, tail: int = 100) -> str
    def pull_image(image_name: str) -> PullResult
    def is_daemon_running() -> bool
```

**Error Handling**:
- Docker daemon not running → clear error message
- Image not found → suggest pulling or building
- Port conflict → suggest alternative ports
- Volume mount error → suggest checking permissions

#### 5. Prober Integration (`prober_integration.py`)
**Purpose**: Interface to external docker-prober-utility for preflight validation

**Responsibilities**:
- Launch prober for pre-deployment validation
- Test HTTP/HTTPS endpoints with deployment config
- Validate TLS configuration
- Test URL rewriting and header forwarding
- Return actionable recommendations

**Modes**:
- **Preflight Mode**: Comprehensive check before deployment
- **Post-deployment Mode**: Verify deployed services (uses HealthChecker)

**Integration**:
```python
class ProberIntegration:
    def run_preflight_check(config: dict) -> ProberResult
    def cleanup() -> None
```

## Implementation Strategy

### Phase 1: Docker Client Wrapper
- Implement DockerClient with docker-py
- Support basic docker-compose operations
- Add error handling and logging
- Add unit tests with mocked Docker API

### Phase 2: Template Renderer
- Implement Jinja2 template loading
- Add custom filters
- Add template validation
- Add comprehensive tests

### Phase 3: Health Checker
- Implement Docker health check monitoring
- Add HTTP endpoint probing
- Add timeout and retry logic
- Add health check reporting

### Phase 4: Deployment Orchestrator
- Implement deployment workflow
- Add prober integration
- Add rollback capability
- Add deployment snapshots

### Phase 5: Integration & Polish
- Add CLI wrapper
- Add comprehensive tests
- Add documentation
- Add examples

## Dependencies

### Production (End Users)

**Required:**
- `docker` - Container management
- `docker-compose` - Container orchestration
- `python>=3.8` - Python runtime

**Optional Features:**
- `curl` - HTTP requests (if downloading images)
- `openssl` - SSL certificates (if managing certificates)
- `tar` - Archive handling (if backup/restore)

### Development (Contributors)

**Required:**
- `git` - Version control
- `python>=3.8` - Python runtime

**Optional Tools:**
- `pytest` - Testing (if adding tests)
- `black` - Code formatting (if formatting code)
- `shellcheck` - Shell script validation (if using shell scripts)


## Development

### Setup

```bash
# Clone repository
git clone https://github.com/JustinCBates/openproject-deploy-manager.git
cd openproject-deploy-manager

# Install in development mode
pip install -e ".[dev]"

# Ensure Docker is running
docker --version
```

### Testing

Tests are organized by operation mode:

```bash
# Run all tests (requires Docker)
pytest

# Test development mode
pytest tests/test_development_mode.py -v

# Test production mode
pytest tests/test_production_mode.py -v

# Run tests with coverage
pytest --cov=openproject_deploy_manager --cov-report=term-missing

# Run specific test
pytest tests/test_orchestrator.py

# Skip Docker-dependent tests
pytest -m "not docker"
```

## Environment Variables

| Variable | Values | Effect |
|----------|--------|--------|
| `OPENPROJECT_DEV_MODE` | `1`, `true`, `yes` | Force development mode (use local paths) |

**Examples**:

```bash
# Force development mode
export OPENPROJECT_DEV_MODE=1
python -c "from openproject_deploy_manager import DeploymentOrchestrator; d = DeploymentOrchestrator(config={})"
# Uses ./templates/ and ./outputs/

# Production mode (default when installed via pip)
unset OPENPROJECT_DEV_MODE
python -c "from openproject_deploy_manager import DeploymentOrchestrator; d = DeploymentOrchestrator(config={}, templates_dir='/opt/openproject/templates', output_dir='/opt/openproject/outputs')"
# Uses /opt/openproject/templates/ and /opt/openproject/outputs/
```

## Mode Detection

The Deployment Orchestrator auto-detects its operating mode:

1. **Environment Variable Check**: If `OPENPROJECT_DEV_MODE=1`, use development mode
2. **Git Repository Check**: If `.git` directory exists in parent paths, use development mode
3. **Site-Packages Check**: If running from `site-packages/`, use production mode
4. **Default**: Development mode

**Override Detection**:

```python
# Force production mode even in development
deployer = DeploymentOrchestrator(
    config=my_config,
    templates_dir=Path("/opt/openproject/templates"),
    output_dir=Path("/opt/openproject/outputs"),
    use_local_paths=False  # Explicitly disable auto-detection
)

# Force development mode even when installed
deployer = DeploymentOrchestrator(
    config=my_config,
    use_local_paths=True
)
```

## API Reference

### DeploymentOrchestrator

```python
class DeploymentOrchestrator:
    def __init__(
        self,
        config: Dict[str, Any],                      # Configuration dictionary
        project_root: Optional[Path] = None,         # Legacy (deprecated)
        templates_dir: Optional[Path] = None,        # Where to find templates
        output_dir: Optional[Path] = None,           # Where to write rendered files
        compose_file: Optional[Path] = None,         # docker-compose.yml path
        snapshot_dir: Optional[Path] = None,         # Snapshot storage
        config_file: Optional[Path] = None,          # Config file path
        use_local_paths: Optional[bool] = None       # Force dev/prod mode
    ):
        """
        Initialize Deployment Orchestrator.

        Production Mode (paths required):
            deployer = DeploymentOrchestrator(
                config=cfg,
                templates_dir=Path("/opt/openproject/templates"),
                output_dir=Path("/opt/openproject/outputs")
            )

        Development Mode (auto-detected):
            deployer = DeploymentOrchestrator(config=cfg)
        """
```

### Methods

```python
def render_templates(self) -> Dict[str, Any]:
    """
    Render Jinja2 templates.

    Returns:
        Dict with:
        - status: 'success' | 'error' | 'warning'
        - files_rendered: int
        - rendered_files: List[str]
    """

def create_snapshot(self, snapshot_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create deployment snapshot.

    Returns:
        Dict with:
        - status: 'success' | 'error'
        - snapshot_name: str
        - snapshot_path: str
    """

def deploy(self, dry_run: bool = False) -> Dict[str, Any]:
    """
    Execute deployment.

    Returns:
        Dict with:
        - status: 'success' | 'error'
        - message: str (if error)
    """
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
flake8 src tests

# Type checking
mypy src
```

### CI/CD

GitHub Actions workflows are configured for:
- Linting (black, flake8)
- Testing (Python 3.8-3.12, with Docker service)
- Coverage reporting
- Automated releases

## Project Structure

```
openproject-deploy-manager/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── .gitignore
│
├── src/
│   └── openproject_deploy_manager/
│       ├── __init__.py
│       ├── orchestrator.py       # Deployment orchestration
│       ├── template_renderer.py  # Jinja2 template rendering
│       ├── health_checker.py     # Service health validation
│       ├── docker_client.py      # Docker SDK wrapper
│       ├── prober_integration.py # Prober preflight checks
│       ├── cli.py                # CLI interface
│       └── utils/
│           ├── __init__.py
│           ├── logging.py
│           ├── errors.py
│           └── snapshots.py      # Deployment snapshots for rollback
│
├── tests/
│   ├── __init__.py
│   ├── test_orchestrator.py
│   ├── test_template_renderer.py
│   ├── test_health_checker.py
│   ├── test_docker_client.py
│   ├── test_prober_integration.py
│   └── fixtures/
│       ├── docker-compose.yml
│       └── templates/
│
└── .github/
    └── workflows/
        └── ci.yml
```

## Example Templates

### Caddyfile Template (`templates/Caddyfile.j2`)

```caddyfile
{% if tls_enabled %}
{{ domain }}:{{ https_port }} {
    tls {{ tls_cert_path }} {{ tls_key_path }}
    reverse_proxy backend:8080
}
{% else %}
{{ domain }}:{{ http_port }} {
    reverse_proxy backend:8080
}
{% endif %}
```

### Nginx Configuration (`templates/nginx.conf.j2`)

```nginx
server {
    listen {{ port }};
    server_name {{ domain }};

    location / {
        proxy_pass http://backend:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- Docker & Docker Compose (for integration tests)

### Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/JustinCBates/openproject-deploy-manager.git
   cd openproject-deploy-manager
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

   The pre-commit hooks will automatically:
   - Format code with Black (line length 88)
   - Lint with Flake8 (enforce unused import checks)
   - Upgrade Python syntax with pyupgrade
   - Fix trailing whitespace and end-of-file issues
   - Validate YAML and TOML files

### Running Pre-commit Hooks

**Automatically on commit**:
```bash
git commit -m "your message"
# Hooks run automatically before commit
```

**Manually on all files**:
```bash
pre-commit run --all-files
```

**Manually on specific files**:
```bash
pre-commit run --files src/phases/phase_1_preflight/*.py
```

**Skip hooks (emergency only)**:
```bash
git commit --no-verify -m "emergency fix"
```

### Running Tests

**Run all tests**:
```bash
pytest
```

**Run with coverage**:
```bash
pytest --cov=src --cov-report=html
```

**Run specific test file**:
```bash
pytest tests/test_development_mode.py -v
```

### Code Quality Tools

**Format code with Black**:
```bash
black src tests
```

**Lint with Flake8**:
```bash
flake8 src tests
```

**Check types with mypy** (if configured):
```bash
mypy src
```

### Common Issues

**Pre-commit hook fails with "command not found"**:
```bash
# Reinstall pre-commit hooks
pre-commit clean
pre-commit install
```

**Black formatting conflicts**:
```bash
# Run Black manually and commit the changes
black src tests
git add -A
git commit -m "style: apply Black formatting"
```

**Flake8 errors in generated/vendor code**:
The pre-commit config excludes `testing/`, `src/runtime/`, and vendor paths. If you see errors in these paths, update `.pre-commit-config.yaml` to add more exclusions.

## License

MIT

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Install pre-commit hooks (`pre-commit install`)
5. Ensure all tests pass and hooks are green
6. Submit a pull request

**Code Style**:
- Follow Black formatting (automatic via pre-commit)
- Keep line length ≤ 88 characters
- Use type hints where appropriate
- Add docstrings for public APIs

## Support

- **Issues**: https://github.com/JustinCBates/openproject-deploy-manager/issues
- **Discussions**: https://github.com/JustinCBates/openproject-deploy-manager/discussions

## Roadmap

- [ ] Phase 1: Docker Client Wrapper (v0.1.0)
- [ ] Phase 2: Template Renderer (v0.2.0)
- [ ] Phase 3: Health Checker (v0.3.0)
- [ ] Phase 4: Deployment Orchestrator (v0.4.0)
- [ ] Phase 5: Integration & Polish (v1.0.0)
- [ ] Future: Blue-green deployments
- [ ] Future: Canary deployments
- [ ] Future: Multi-environment support
- [ ] Future: Deployment hooks (pre-deploy, post-deploy)
