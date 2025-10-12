# Control Flow Specification - Deploy Manager

> **Design-first specification for iterative development**  
> Use this to communicate deployment flow changes before implementation exists

## Entry Points
```yaml
cli:
  status: IMPLEMENTED
  description: "Main deployment CLI entry point"
  calls: [deploy, rollback, health, validate, template, status]
  
deploy:
  status: IMPLEMENTED  
  description: "Run complete deployment orchestration process"
  flow_id: "main_deployment_flow"

rollback:
  status: PLANNED
  description: "Rollback to previous deployment snapshot"
  flow_id: "rollback_flow"
```

## Flow Implementations
```yaml
main_deployment_flow:
  description: "Primary Deployment Process"
  flow_steps:
    - step_id: "init"
      name: "Initialize Orchestrator"
      status: IMPLEMENTED
      description: "Create DeploymentOrchestrator instance"
      
    - step_id: "preflight"
      name: "Preflight Validation"
      status: IMPLEMENTED
      description: "Run environment, system, and Docker discovery"
      sub_flows: ["discovery_flow"]
      
    - step_id: "collection"
      name: "Interactive Collection"
      status: IMPLEMENTED
      description: "Collect user configuration via UI"
      
    - step_id: "validation"
      name: "Validation Phase"
      status: IMPLEMENTED
      description: "Validate collected configuration"
      sub_flows: ["validation_flow"]
      decision_point: "continue_on_validation_failure"
      
    - step_id: "export"
      name: "Export Phase"
      status: IMPLEMENTED
      description: "Export configuration to file"
      sub_flows: ["export_flow"]
      
  planned_insertions:
    - insert_after: "collection"
      step_id: "pre_validation_cleanup"
      name: "Pre-validation Cleanup"
      status: PLANNED
      description: "Clean up configuration before validation"
      
    - insert_before: "export"
      step_id: "final_review"
      name: "Final Review"
      status: PLANNED
      description: "Show summary for user approval before export"

discovery_flow:
  description: "Environment Discovery"
  flow_steps:
    - step_id: "env_discovery"
      name: "Environment Variables"
      status: IMPLEMENTED
      description: "Discover relevant environment variables"
      
    - step_id: "system_discovery"
      name: "System Information"
      status: IMPLEMENTED
      description: "Detect system resources and platform"
      
    - step_id: "docker_discovery"
      name: "Docker Environment"
      status: IMPLEMENTED
      description: "Discover Docker containers and networks"
      
  planned_insertions:
    - insert_after: "docker_discovery"
      step_id: "network_discovery"
      name: "Network Discovery"
      status: TODO
      description: "Discover network topology and conflicts"
```

## Decision Points
```yaml
continue_on_validation_failure:
  type: "user_confirmation"
  prompt: "Validation failed. Continue anyway?"
  default: false
  implemented: true
  
use_custom_output_path:
  type: "parameter_check"
  condition: "output parameter provided"
  implemented: true

confirm_destructive_changes:
  type: "user_confirmation"
  prompt: "This will overwrite existing configuration. Continue?"
  default: false
  implemented: false
  insert_before_step: "export.write_file"
```