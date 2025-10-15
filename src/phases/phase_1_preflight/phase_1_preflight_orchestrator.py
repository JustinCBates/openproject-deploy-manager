#!/usr/bin/env python3
"""
Preflight Validation
Sequence: 10
Status: IMPLEMENTED

Validate environment and configuration before deployment
"""

from pathlib import Path
from typing import Dict, Any
import logging
import sys

# Add libraries to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "libraries"))

from config.config_loader import ConfigLoader
from config.config_validator import ConfigValidator
from docker.docker_checker import DockerChecker
from network.port_checker import PortChecker
from system.resource_checker import ResourceChecker
from templates.template_validator import TemplateValidator

logger = logging.getLogger(__name__)


class Phase1PreflightOrchestrator:
    """
    Preflight Validation
    
    Status: PLANNED
    Sequence: 10
    
    Validate environment and configuration before deployment
    """
    
    PHASE_ID = "phase_1_preflight"
    PHASE_SEQUENCE = 10
    PHASE_NAME = "Preflight Validation"
    
    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        Initialize Preflight Validation.
        
        Args:
            project_root: Root directory of the project
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config
        self.phase_dir = project_root / "runtime" / "phase_1_preflight"
        self.outputs_dir = self.phase_dir / "outputs"
        
        # Ensure outputs directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Preflight Validation.
        
        Args:
            context: Execution context from previous phases
            
        Returns:
            Dict with phase results and artifacts
        """
        logger.info("=" * 70)
        logger.info(f"{self.PHASE_NAME}")
        logger.info("=" * 70)
        
        result = {
            "phase_id": self.PHASE_ID,
            "status": "success",
            "artifacts": {},
            "messages": []
        }
        
        # Execute steps in sequence with error handling
        steps = [
            ("Step 10", self._step_10_load_configuration),
            ("Step 20", self._step_20_validate_configuration),
            ("Step 30", self._step_30_check_docker_daemon),
            ("Step 40", self._step_40_check_port_availability),
            ("Step 50", self._step_50_run_prober_preflight),
            ("Step 60", self._step_60_validate_system_resources),
        ]
        
        for step_name, step_func in steps:
            step_result = step_func(context)
            
            # Update context with artifacts for next steps
            context.update(step_result.get('artifacts', {}))
            
            # Update result artifacts
            result['artifacts'].update(step_result.get('artifacts', {}))
            
            # Collect messages
            result['messages'].extend(step_result.get('messages', []))
            
            # Check step status
            step_status = step_result.get('status', 'success')
            
            if step_status == 'error':
                logger.error(f"  ❌ {step_name} failed - aborting phase")
                result['status'] = 'error'
                return result
            elif step_status == 'warning' and result['status'] == 'success':
                # Downgrade to warning but continue
                result['status'] = 'warning'
        
        logger.info(f"✅ {self.PHASE_NAME} complete (status: {result['status']})")
        return result
    

    def _step_10_load_configuration(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 10: Load Configuration
        
        Load deployment configuration from config-manager output
        """
        logger.info(f"  Step 10: Load Configuration")
        
        try:
            # Get config path from context or use default
            config_path = context.get('config_path') or self.config.get('config_path')
            
            if not config_path:
                logger.warning("No config_path provided, using default configuration")
                return {
                    "status": "success",
                    "artifacts": {"loaded_config": self.config},
                    "messages": ["Using provided configuration (no file loaded)"]
                }
            
            # Load configuration file
            loader = ConfigLoader()
            loaded_config = loader.load(Path(config_path))
            
            logger.info(f"✅ Loaded configuration from: {config_path}")
            
            return {
                "status": "success",
                "artifacts": {"loaded_config": loaded_config},
                "messages": [f"Loaded configuration from {config_path}"]
            }
            
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Configuration file not found: {e}"]
            }
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Failed to load configuration: {e}"]
            }

    def _step_20_validate_configuration(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 20: Validate Configuration
        
        Validate configuration completeness and correctness
        """
        logger.info(f"  Step 20: Validate Configuration")
        
        try:
            # Get config from context or use instance config
            config_to_validate = context.get('loaded_config', self.config)
            
            # Validate configuration
            validator = ConfigValidator()
            validation_result = validator.validate(config_to_validate)
            
            if validation_result.valid:
                logger.info(f"✅ Configuration validation passed")
                return {
                    "status": "success",
                    "artifacts": {
                        "validation_result": validation_result,
                        "validated_config": config_to_validate
                    },
                    "messages": ["Configuration validation passed"]
                }
            else:
                logger.error(f"❌ Configuration validation failed: {validation_result.errors}")
                return {
                    "status": "error",
                    "artifacts": {"validation_result": validation_result},
                    "messages": [
                        f"Configuration validation failed: {len(validation_result.errors)} errors"
                    ] + validation_result.errors
                }
                
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Configuration validation error: {e}"]
            }

    def _step_30_check_docker_daemon(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 30: Check Docker Daemon
        
        Verify Docker daemon is accessible and running
        """
        logger.info(f"  Step 30: Check Docker Daemon")
        
        try:
            # Check Docker availability
            checker = DockerChecker()
            docker_status = checker.check()
            
            if docker_status.available:
                logger.info(f"✅ {docker_status}")
                return {
                    "status": "success",
                    "artifacts": {"docker_status": docker_status},
                    "messages": [str(docker_status)]
                }
            else:
                logger.error(f"❌ {docker_status}")
                return {
                    "status": "error",
                    "artifacts": {"docker_status": docker_status},
                    "messages": [f"Docker not available: {docker_status.error}"]
                }
                
        except Exception as e:
            logger.error(f"Docker check failed: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Docker check failed: {e}"]
            }

    def _step_40_check_port_availability(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 40: Check Port Availability
        
        Ensure required ports are available
        """
        logger.info(f"  Step 40: Check Port Availability")
        
        try:
            # Get ports from config
            config_to_check = context.get('validated_config', self.config)
            
            # Extract ports from config (looking for common keys)
            ports = []
            if 'ports' in config_to_check:
                ports = config_to_check['ports'] if isinstance(config_to_check['ports'], list) else [config_to_check['ports']]
            elif 'port' in config_to_check:
                ports = [config_to_check['port']]
            
            # Also check services for port definitions
            if 'services' in config_to_check and isinstance(config_to_check['services'], dict):
                for service_name, service_config in config_to_check['services'].items():
                    if isinstance(service_config, dict) and 'port' in service_config:
                        ports.append(service_config['port'])
            
            if not ports:
                logger.info("No ports specified in configuration, skipping port check")
                return {
                    "status": "success",
                    "artifacts": {},
                    "messages": ["No ports to check"]
                }
            
            # Check port availability
            checker = PortChecker()
            port_status = checker.check_ports(ports)
            
            if port_status.all_available:
                logger.info(f"✅ {port_status}")
                return {
                    "status": "success",
                    "artifacts": {"port_status": port_status},
                    "messages": [str(port_status)]
                }
            else:
                logger.warning(f"⚠️  {port_status}")
                return {
                    "status": "warning",
                    "artifacts": {"port_status": port_status},
                    "messages": [
                        f"Some ports unavailable: {port_status.in_use}",
                        "Ports in use may cause deployment conflicts"
                    ]
                }
                
        except Exception as e:
            logger.error(f"Port check failed: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Port check failed: {e}"]
            }

    def _step_50_run_prober_preflight(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 50: Run Prober Preflight
        
        Execute docker-prober-utility for preflight validation (optional)
        """
        logger.info(f"  Step 50: Run Prober Preflight")
        
        # Prober runner unit not yet implemented - skip for now
        logger.info("Prober preflight skipped (prober_runner unit not implemented)")
        
        return {
            "status": "success",
            "artifacts": {},
            "messages": ["Prober preflight skipped (not yet implemented)"]
        }

    def _step_60_validate_system_resources(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 60: Validate System Resources
        
        Check available memory, disk space, and CPU before deployment
        """
        logger.info(f"  Step 60: Validate System Resources")
        
        try:
            checker = ResourceChecker()
            
            # Check memory
            mem_status = checker.check_memory()
            logger.info(f"    Memory: {mem_status}")
            
            # Check disk space (root partition)
            disk_status = checker.check_disk("/")
            logger.info(f"    Disk: {disk_status}")
            
            # Check CPU
            cpu_status = checker.check_cpu()
            logger.info(f"    CPU: {cpu_status}")
            
            # Determine overall status
            all_sufficient = (
                mem_status.sufficient and 
                disk_status.sufficient and 
                cpu_status.sufficient
            )
            
            if all_sufficient:
                logger.info("  ✅ System resources validated")
                status = "success"
                messages = [
                    "System resources sufficient:",
                    f"  Memory: {mem_status.percent_used:.1f}% used",
                    f"  Disk: {disk_status.percent_used:.1f}% used",
                    f"  CPU: {cpu_status.percent_used:.1f}% used"
                ]
            else:
                logger.warning("  ⚠️  System resources may be insufficient")
                status = "warning"
                messages = [
                    "System resources may be insufficient:",
                    f"  Memory: {mem_status}",
                    f"  Disk: {disk_status}",
                    f"  CPU: {cpu_status}"
                ]
            
            return {
                "status": status,
                "artifacts": {
                    "memory_status": mem_status,
                    "disk_status": disk_status,
                    "cpu_status": cpu_status,
                    "resources_sufficient": all_sufficient
                },
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"  ❌ Error checking system resources: {str(e)}")
            return {
                "status": "error",
                "artifacts": {},
                "messages": [f"Failed to check system resources: {str(e)}"]
            }


def main():
    """Test the phase orchestrator."""
    from pathlib import Path
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    project_root = Path(__file__).parent.parent.parent
    
    # Test with sample config file (in deploy-manager root)
    config_path = project_root.parent / "test_config.yaml"
    
    config = {}
    context = {
        "config_path": str(config_path)
    }
    
    print(f"Testing Phase 1 Preflight Orchestrator")
    print(f"Config path: {config_path}")
    print(f"Config exists: {config_path.exists()}")
    print("=" * 70)
    
    orchestrator = Phase1PreflightOrchestrator(project_root, config)
    result = orchestrator.execute(context)
    
    print("=" * 70)
    print(f"Phase Status: {result['status']}")
    print(f"Messages: {len(result.get('messages', []))}")
    print(f"Artifacts: {list(result.get('artifacts', {}).keys())}")
    
    if result['status'] == 'error':
        print("\n❌ Phase failed with errors:")
        for msg in result.get('messages', []):
            print(f"  - {msg}")
    elif result['status'] == 'warning':
        print("\n⚠️  Phase completed with warnings:")
        for msg in result.get('messages', []):
            print(f"  - {msg}")
    else:
        print("\n✅ Phase completed successfully!")



if __name__ == '__main__':
    main()
