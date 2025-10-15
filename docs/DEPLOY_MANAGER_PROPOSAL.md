# Deploy-Manager Structure Proposal

**Created**: October 15, 2025  
**Purpose**: Define the deploy-manager component structure using control-flow system from scratch

---

## 🎯 Component Overview

**Deploy-Manager** is a deployment orchestration system that:
1. Consumes configuration from config-manager
2. Renders deployment templates (Caddyfile, docker-compose overrides, etc.)
3. Orchestrates Docker Compose deployments
4. Performs health checking and validation
5. Supports rollback on failure

---

## 📋 Main Components (Based on README Analysis)

### 1. **Deployment Orchestrator** (Core Controller)
**Purpose**: Main controller coordinating the entire deployment lifecycle

**Responsibilities**:
- Load configuration from config-manager output
- Coordinate all deployment phases
- Handle errors and trigger rollback
- Report deployment status

**Key Methods**:
- `deploy(dry_run: bool, prober_enabled: bool) -> DeploymentResult`
- `rollback() -> RollbackResult`
- `get_status() -> DeploymentStatus`
- `validate_deployment() -> ValidationResult`

---

### 2. **Configuration Loader**
**Purpose**: Load and parse configuration from config-manager

**Responsibilities**:
- Load `.cfg` file from config-manager
- Parse bash-style `key="value"` pairs
- Convert to `.env` format for Docker Compose
- Extract template variables for Jinja2
- Validate required configuration keys

**Input Sources**:
- Primary: `collected_configuration.yml` from config-manager Phase 5 export
- Alternative: `.env` file
- Fallback: Environment variables

**Key Methods**:
- `load_config(path: Path) -> Dict[str, str]`
- `convert_to_env() -> Dict[str, str]`
- `extract_template_vars() -> Dict[str, Any]`
- `validate_required_keys() -> ValidationResult`

---

### 3. **Template Renderer**
**Purpose**: Render Jinja2 templates with configuration values

**Responsibilities**:
- Load Jinja2 templates (Caddyfile, nginx.conf, compose overrides)
- Render with configuration context
- Validate rendered output syntax
- Support custom filters (to_bool, to_port, to_domain)
- Handle template errors gracefully

**Templates to Support**:
- `Caddyfile.j2` - Caddy reverse proxy config
- `nginx.conf.j2` - Nginx configuration
- `docker-compose.override.yml.j2` - Dynamic compose settings
- Custom user templates

**Key Methods**:
- `render(template_name: str, context: dict) -> str`
- `render_to_file(template_name: str, output_path: Path, context: dict)`
- `validate_rendered(content: str, validator: Callable) -> ValidationResult`

---

### 4. **Docker Client Wrapper**
**Purpose**: Simplified interface to Docker SDK for Python

**Responsibilities**:
- Wrap Docker SDK with error handling
- Execute docker-compose operations
- Monitor container status and logs
- Handle Docker API errors gracefully
- Check Docker daemon availability

**Key Methods**:
- `compose_up(compose_file: Path, services: List[str]) -> ComposeResult`
- `compose_down(remove_volumes: bool) -> ComposeResult`
- `get_service_status(service_name: str) -> ServiceStatus`
- `get_container_logs(container_id: str, tail: int) -> str`
- `pull_image(image_name: str) -> PullResult`
- `is_daemon_running() -> bool`

---

### 5. **Health Checker**
**Purpose**: Validate service health after deployment

**Responsibilities**:
- Check Docker container health via Docker API
- Probe HTTP/HTTPS endpoints
- Verify database connectivity (optional)
- Wait for services with timeout and retry
- Report detailed health status

**Health Check Strategies**:
1. Docker Health Checks (container built-in healthcheck)
2. HTTP Probes (GET requests to health endpoints)
3. Database Checks (pg_isready, redis-cli)
4. Custom service-specific checks

**Key Methods**:
- `check_service(service_name: str) -> HealthStatus`
- `check_endpoint(url: str, timeout: int) -> EndpointStatus`
- `wait_for_healthy(services: List[str], timeout: int) -> HealthCheckResult`

---

### 6. **Prober Integration**
**Purpose**: Interface to docker-prober-utility for preflight validation

**Responsibilities**:
- Run preflight checks before deployment
- Test HTTP/HTTPS endpoints
- Validate TLS configuration
- Test URL rewriting and headers
- Return actionable recommendations

**Modes**:
- **Preflight**: Comprehensive pre-deployment validation
- **Post-deployment**: Verify deployed services (delegates to HealthChecker)

**Key Methods**:
- `run_preflight_check(config: dict) -> ProberResult`
- `cleanup()`

---

### 7. **Snapshot Manager**
**Purpose**: Create and manage deployment snapshots for rollback

**Responsibilities**:
- Create pre-deployment snapshots
- Store container state, volumes, configs
- Restore from snapshots on rollback
- Manage snapshot lifecycle (retention, cleanup)

**Snapshot Contents**:
- Docker container states
- Volume data (optional - can be large)
- Configuration files
- Template outputs
- Deployment metadata

**Key Methods**:
- `create_snapshot() -> Snapshot`
- `restore_snapshot(snapshot_id: str) -> RestoreResult`
- `list_snapshots() -> List[Snapshot]`
- `delete_snapshot(snapshot_id: str)`

---

## 🔄 Proposed Control Flow Phases

Based on README analysis, here's the recommended phase structure:

### **Phase 1: Preflight Validation**
**Purpose**: Validate environment before deployment

**Steps**:
1. Load configuration from config-manager
2. Validate configuration completeness
3. Check Docker daemon accessibility
4. Check port availability
5. Run prober preflight check (optional)
6. Validate system resources (memory, disk)

**Outputs**:
- `preflight_validation.yml` - Validation results
- `deployment_config.yml` - Processed configuration

---

### **Phase 2: Template Rendering**
**Purpose**: Render all deployment templates

**Steps**:
1. Extract template variables from config
2. Load Jinja2 templates
3. Render Caddyfile template
4. Render docker-compose override template
5. Render any custom templates
6. Validate rendered outputs

**Outputs**:
- `Caddyfile` - Rendered proxy configuration
- `docker-compose.override.yml` - Dynamic compose settings
- `rendered_templates/` - All rendered templates

---

### **Phase 3: Snapshot Creation**
**Purpose**: Create pre-deployment snapshot for rollback

**Steps**:
1. Capture current container states
2. Backup configuration files
3. Record deployment metadata
4. Store snapshot with timestamp

**Outputs**:
- `snapshots/<timestamp>/` - Snapshot directory
- `snapshot_metadata.json` - Snapshot info

---

### **Phase 4: Deployment Execution**
**Purpose**: Execute Docker Compose deployment

**Steps**:
1. Convert config to `.env` format
2. Pull Docker images (if requested)
3. Execute `docker-compose up -d`
4. Monitor service startup
5. Capture deployment logs

**Outputs**:
- `.env` - Environment file for Docker Compose
- `deployment_logs.txt` - Deployment execution logs
- Running containers

---

### **Phase 5: Health Verification**
**Purpose**: Verify deployment success

**Steps**:
1. Wait for container health checks
2. Probe HTTP/HTTPS endpoints
3. Verify database connectivity
4. Test service connectivity
5. Generate health report

**Outputs**:
- `health_report.json` - Comprehensive health status
- `service_status.yml` - Per-service health

---

### **Phase 6: Post-Deployment**
**Purpose**: Finalize deployment and cleanup

**Steps**:
1. Report deployment status
2. Log deployment metadata
3. Clean up temporary files
4. Send notifications (if configured)

**Outputs**:
- `deployment_result.json` - Final deployment status
- `deployment_manifest.yml` - Deployment record

---

## 📂 Proposed Directory Structure

Using control-flow scaffolding system:

```
deploy-manager/
├── design_specs/
│   └── control_flows.yml          # UPDATED with detailed phase structure
│
├── phases/
│   ├── phase_1_preflight/
│   │   ├── orchestrator_preflight.py
│   │   ├── step_1_load_config/
│   │   │   └── config_loader.py
│   │   ├── step_2_validate_config/
│   │   │   └── config_validator.py
│   │   ├── step_3_check_docker/
│   │   │   └── docker_checker.py
│   │   ├── step_4_check_ports/
│   │   │   └── port_checker.py
│   │   ├── step_5_run_prober/
│   │   │   └── prober_runner.py
│   │   └── outputs/preflight/
│   │       ├── preflight_validation.yml
│   │       └── deployment_config.yml
│   │
│   ├── phase_2_template_rendering/
│   │   ├── orchestrator_template_rendering.py
│   │   ├── step_1_extract_variables/
│   │   │   └── variable_extractor.py
│   │   ├── step_2_render_caddyfile/
│   │   │   └── caddyfile_renderer.py
│   │   ├── step_3_render_compose/
│   │   │   └── compose_renderer.py
│   │   ├── step_4_validate_templates/
│   │   │   └── template_validator.py
│   │   └── outputs/templates/
│   │       ├── Caddyfile
│   │       ├── docker-compose.override.yml
│   │       └── rendered_templates/
│   │
│   ├── phase_3_snapshot/
│   │   ├── orchestrator_snapshot.py
│   │   ├── step_1_capture_state/
│   │   │   └── state_capturer.py
│   │   ├── step_2_backup_configs/
│   │   │   └── config_backupper.py
│   │   ├── step_3_store_snapshot/
│   │   │   └── snapshot_storer.py
│   │   └── outputs/snapshots/
│   │       └── <timestamp>/
│   │
│   ├── phase_4_deployment/
│   │   ├── orchestrator_deployment.py
│   │   ├── step_1_generate_env/
│   │   │   └── env_generator.py
│   │   ├── step_2_pull_images/
│   │   │   └── image_puller.py
│   │   ├── step_3_compose_up/
│   │   │   └── compose_executor.py
│   │   ├── step_4_monitor_startup/
│   │   │   └── startup_monitor.py
│   │   └── outputs/deployment/
│   │       ├── .env
│   │       └── deployment_logs.txt
│   │
│   ├── phase_5_health_verification/
│   │   ├── orchestrator_health_verification.py
│   │   ├── step_1_container_health/
│   │   │   └── container_health_checker.py
│   │   ├── step_2_endpoint_probing/
│   │   │   └── endpoint_prober.py
│   │   ├── step_3_database_check/
│   │   │   └── database_checker.py
│   │   ├── step_4_connectivity_test/
│   │   │   └── connectivity_tester.py
│   │   └── outputs/health/
│   │       ├── health_report.json
│   │       └── service_status.yml
│   │
│   ├── phase_6_post_deployment/
│   │   ├── orchestrator_post_deployment.py
│   │   ├── step_1_report_status/
│   │   │   └── status_reporter.py
│   │   ├── step_2_log_metadata/
│   │   │   └── metadata_logger.py
│   │   ├── step_3_cleanup/
│   │   │   └── cleanup_handler.py
│   │   └── outputs/final/
│   │       ├── deployment_result.json
│   │       └── deployment_manifest.yml
│   │
│   ├── libraries/
│   │   ├── docker/
│   │   │   ├── __init__.py
│   │   │   ├── client_wrapper.py
│   │   │   └── compose_manager.py
│   │   ├── templates/
│   │   │   ├── __init__.py
│   │   │   ├── jinja_renderer.py
│   │   │   └── template_filters.py
│   │   ├── health/
│   │   │   ├── __init__.py
│   │   │   ├── health_checker.py
│   │   │   └── endpoint_prober.py
│   │   └── config/
│   │       ├── __init__.py
│   │       ├── config_loader.py
│   │       └── config_converter.py
│   │
│   └── phases_orchestrator.py         # Global orchestrator
│
├── templates/
│   ├── Caddyfile.j2
│   ├── nginx.conf.j2
│   ├── docker-compose.override.yml.j2
│   └── custom/
│
├── src/
│   └── openproject_deploy_manager/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py
│       └── core/
│           ├── __init__.py
│           ├── orchestrator.py        # Wraps phases_orchestrator
│           └── result_types.py
│
├── tests/
│   ├── unit/
│   │   ├── test_config_loader.py
│   │   ├── test_template_renderer.py
│   │   ├── test_docker_client.py
│   │   ├── test_health_checker.py
│   │   └── test_snapshot_manager.py
│   ├── integration/
│   │   ├── test_deployment_flow.py
│   │   └── test_rollback_flow.py
│   └── fixtures/
│       ├── sample_config.yml
│       ├── sample_templates/
│       └── mock_docker_responses/
│
├── docs/
│   ├── DEPLOYMENT_FLOW.md
│   ├── TEMPLATE_GUIDE.md
│   ├── HEALTH_CHECKING.md
│   └── ROLLBACK_GUIDE.md
│
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## 🎯 Key Design Decisions

### 1. **Configuration Input**
- **Primary**: `collected_configuration.yml` from config-manager Phase 5
- **Format**: YAML with metadata + user_responses
- **Conversion**: Convert to `.env` for Docker Compose compatibility

### 2. **Template Strategy**
- **Engine**: Jinja2 for flexibility
- **Location**: `templates/` directory
- **Custom Filters**: Add domain-specific helpers (to_bool, to_port, etc.)
- **Validation**: Syntax check rendered outputs

### 3. **Health Checking**
- **Multi-level**: Docker health, HTTP probes, database connectivity
- **Timeout Strategy**: Exponential backoff with configurable max timeout
- **Failure Handling**: Detailed error reporting with rollback option

### 4. **Rollback Strategy**
- **Snapshot Before Deploy**: Always create snapshot before changes
- **Snapshot Contents**: Container states, configs (not volumes by default)
- **Restore Process**: Stop current, restore snapshot, verify
- **Manual vs Auto**: Configurable (default: manual for safety)

### 5. **Phase Communication**
- **Outputs Directory**: Each phase writes to `outputs/` subdirectory
- **Next Phase Input**: Next phase reads previous phase outputs
- **Metadata**: YAML format for structured data
- **Logs**: Separate log files for debugging

---

## 📊 Comparison with Config-Manager

| Aspect | Config-Manager | Deploy-Manager |
|--------|---------------|----------------|
| **Purpose** | Collect user configuration | Deploy with configuration |
| **Input** | User interaction / auto-detection | Config-manager output |
| **Output** | `collected_configuration.yml` | Running deployment |
| **Phases** | 5 (Discovery, TUI Map, Collection, Validation, Export) | 6 (Preflight, Templates, Snapshot, Deploy, Health, Post) |
| **Interactivity** | High (TUI forms) | Low (automated with flags) |
| **External Deps** | questionary, tui-form-designer | docker, docker-compose, prober |
| **Rollback** | N/A | Critical feature |

---

## 🚀 Implementation Strategy

### Using Control-Flow System

1. **Update `control_flows.yml`** with detailed phase/step structure
2. **Run scaffolder** to generate directory structure:
   ```bash
   cd /opt/openproject/external/deploy-manager
   flow-engine scaffold design_specs/control_flows.yml --output phases/
   ```
3. **Implement units** in `phases/libraries/`
4. **Implement step logic** using units
5. **Implement phase orchestrators**
6. **Implement global orchestrator**
7. **Wrap in CLI** (`src/openproject_deploy_manager/cli/main.py`)

### Development Phases

**Phase 1: Core Infrastructure** (Week 1)
- Docker client wrapper
- Configuration loader
- Template renderer
- Basic orchestrator

**Phase 2: Deployment Flow** (Week 2)
- Preflight validation
- Template rendering phase
- Deployment execution phase
- Basic health checking

**Phase 3: Advanced Features** (Week 3)
- Snapshot management
- Full health verification
- Rollback capability
- Prober integration

**Phase 4: Polish & Testing** (Week 4)
- Comprehensive tests
- CLI refinement
- Documentation
- Examples

---

## 📝 Next Steps

1. **Review this proposal** and provide feedback
2. **Update control_flows.yml** with detailed phase structure
3. **Run control-flow scaffolder** to generate skeleton
4. **Start implementing Phase 1** components (Docker client, config loader)
5. **Create backlog** for deploy-manager features

---

## ❓ Questions for Resolution

1. **Snapshot Strategy**: Should we snapshot Docker volumes by default? (Can be large)
2. **Prober Integration**: Required or optional dependency?
3. **Template Location**: Should templates be in deploy-manager or consuming project?
4. **Health Check Timeout**: What's a reasonable default? (Current proposal: 300s)
5. **Rollback Automation**: Auto-rollback on failure or always manual?
6. **Configuration Format**: Prefer YAML from config-manager or support .cfg/.env too?

---

**This proposal is ready for scaffolding using the control-flow system!**
