# Dependencies - Deploy Manager

This directory contains dependency tracking for the Deploy Manager component.

## Files

### Documentation
- **`DEPENDENCIES.md`** - Deployment tool dependencies and requirements

## Purpose

The Deploy Manager handles OpenProject deployment operations:
- Docker container orchestration
- Configuration validation and deployment
- Environment-specific deployments
- Health checking and monitoring setup

## Dependency Categories

### Production Dependencies
- **Absolute**: Required for all deployments
  - Docker runtime and Docker Compose
  - Shell utilities (bash, curl, etc.)

- **Ad-Hoc**: Context-dependent
  - SSL certificate tools (for HTTPS setups)
  - Cloud provider CLIs (for cloud deployments)
  - Backup utilities (for data protection)

### Developer Dependencies
- **Absolute**: Required for development
  - Git for version control
  - Text editors for configuration editing

- **Ad-Hoc**: Optional development tools
  - Linting tools for shell scripts
  - Testing frameworks for deployment validation

## Usage

The Deploy Manager is called by other components and rarely invoked directly by users. It focuses on:
1. Receiving validated configurations from config-manager
2. Deploying containers according to specifications
3. Setting up networking and storage
4. Configuring monitoring and health checks

## Integration Points

- **Input**: Configuration files from config-manager
- **Output**: Running OpenProject deployment
- **Dependencies**: System-level Docker and networking tools
- **Monitoring**: Integration with prober component for health checks
