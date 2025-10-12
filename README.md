# Deploy Manager

Deployment orchestration for Docker Compose stacks with health checking, rollback capabilities, and live validation.

## Features

- **Deployment Orchestration**: Coordinate complete docker-compose lifecycle
- **Template Rendering**: Jinja2 template support for dynamic configuration (Caddyfile, nginx.conf, etc.)
- **Health Checking**: Verify services are healthy after deployment
- **Preflight Validation**: Integrate with docker-prober-utility for pre-deployment checks
- **Automatic Rollback**: Rollback on deployment failure with state snapshots
- **Progress Monitoring**: Real-time deployment progress and logging

## Purpose

This is a generic, reusable deployment orchestration tool designed to work with any Docker Compose stack. It provides intelligent deployment with validation, health checking, and automatic recovery.

## Installation

```bash
pip install openproject-deploy-manager
```

Or install from source:

```bash
git clone https://github.com/JustinCBates/openproject-deploy-manager.git
cd openproject-deploy-manager
pip install -e .
```

## Usage

### Basic Usage

```python
from openproject_deploy_manager import DeploymentOrchestrator

# Deploy Docker Compose stack
orchestrator = DeploymentOrchestrator(
    config={"domain": "example.com", "port": "8080"},
    compose_file="docker-compose.yml",
    template_dir="templates/",
    prober_enabled=True
)

# Execute deployment
result = orchestrator.deploy(dry_run=False)

if result.success:
    print(f"Deployed {len(result.services_started)} services successfully")
else:
    print(f"Deployment failed: {result.error_message}")
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

### Required Dependencies

```toml
dependencies = [
    "docker>=7.0.0",        # Docker SDK
    "jinja2>=3.1.0",        # Template rendering
    "pyyaml>=6.0",          # Configuration parsing
    "click>=8.1.0",         # CLI framework
    "rich>=13.0.0",         # Terminal output
]
```

### External Dependencies

- **docker-prober-utility**: Pre-deployment validation of HTTP/HTTPS endpoints
  ```toml
  docker-prober-utility @ git+https://github.com/JustinCBates/docker_prober_utility.git@main
  ```

### Development Dependencies

```toml
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-docker>=1.0.0",  # Docker fixtures for testing
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
]
```

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

```bash
# Run tests (requires Docker)
pytest

# Run tests with coverage
pytest --cov=openproject_deploy_manager --cov-report=term-missing

# Run specific test
pytest tests/test_orchestrator.py

# Skip Docker-dependent tests
pytest -m "not docker"
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

## License

MIT

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass and code is formatted
5. Submit a pull request

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
