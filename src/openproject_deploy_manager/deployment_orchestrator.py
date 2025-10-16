"""
Deployment Orchestrator with dual-mode support

This is a wrapper around PhasesOrchestrator that provides dual-mode capability:
- Development Mode: Uses local directory structure
- Production Mode: Uses paths provided by main orchestrator
"""

from pathlib import Path
from typing import Dict, Any, Optional
import logging
import os
import sys

logger = logging.getLogger(__name__)


class DeploymentOrchestrator:
    """
    Deployment Orchestrator with dual-mode support.
    
    Supports both development (git submodule) and production (pip package) modes.
    
    Examples:
        # Development mode (auto-detected)
        deployer = DeploymentOrchestrator(config=cfg)
        
        # Production mode (explicit paths)
        deployer = DeploymentOrchestrator(
            config=cfg,
            templates_dir=Path("/opt/openproject/templates"),
            output_dir=Path("/opt/openproject/outputs"),
            compose_file=Path("/opt/openproject/docker-compose.yml")
        )
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        project_root: Optional[Path] = None,
        templates_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        compose_file: Optional[Path] = None,
        snapshot_dir: Optional[Path] = None,
        config_file: Optional[Path] = None,
        use_local_paths: Optional[bool] = None,
    ):
        """
        Initialize deployment orchestrator.
        
        Args:
            config: Configuration dictionary
            project_root: Root directory (legacy, will be deprecated)
            templates_dir: Where to find Jinja2 templates
            output_dir: Where to write rendered files
            compose_file: Path to docker-compose.yml
            snapshot_dir: Where to store deployment snapshots
            config_file: Path to config file (.env or .cfg)
            use_local_paths: Force development mode (None = auto-detect)
        """
        self.config = config
        self.config_file = config_file
        
        # Auto-detect mode if not specified
        if use_local_paths is None:
            use_local_paths = self._is_development_mode()
        
        if use_local_paths:
            # Development mode: Use local directories
            base_dir = Path(__file__).parent.parent.parent
            self.project_root = project_root or base_dir
            self.templates_dir = templates_dir or base_dir / 'templates'
            self.output_dir = output_dir or base_dir / 'outputs'
            self.compose_file = compose_file or base_dir / 'docker-compose.yml'
            self.snapshot_dir = snapshot_dir or base_dir / 'backups' / 'snapshots'
        else:
            # Production mode: Paths must be provided
            if templates_dir is None or output_dir is None:
                raise ValueError(
                    "templates_dir and output_dir required in production mode. "
                    "For development, set use_local_paths=True or "
                    "set environment variable OPENPROJECT_DEV_MODE=1"
                )
            self.project_root = project_root or output_dir.parent
            self.templates_dir = Path(templates_dir)
            self.output_dir = Path(output_dir)
            self.compose_file = Path(compose_file) if compose_file else self.project_root / 'docker-compose.yml'
            self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else self.output_dir / 'snapshots'
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify templates directory exists
        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
        
        # Store configuration for phase orchestrators
        self._update_config_paths()
    
    def _update_config_paths(self):
        """Update config with path information for phases"""
        # Add path information to config so phases can find resources
        self.config['_paths'] = {
            'project_root': str(self.project_root),
            'templates_dir': str(self.templates_dir),
            'output_dir': str(self.output_dir),
            'compose_file': str(self.compose_file),
            'snapshot_dir': str(self.snapshot_dir),
        }
    
    @staticmethod
    def _is_development_mode() -> bool:
        """
        Auto-detect if running in development mode.
        
        Checks for:
        1. Environment variable OPENPROJECT_DEV_MODE
        2. Presence of .git directory (running from source)
        3. Not in site-packages (packaged installation)
        
        Returns:
            True if in development mode, False if in production mode
        """
        # Check environment variable
        if os.getenv('OPENPROJECT_DEV_MODE', '').lower() in ('1', 'true', 'yes'):
            logger.debug("Development mode: OPENPROJECT_DEV_MODE environment variable set")
            return True
        
        # Check if running from git repository
        current_file = Path(__file__).resolve()
        
        # Walk up the directory tree looking for .git
        for parent in current_file.parents:
            if (parent / '.git').exists():
                logger.debug(f"Development mode: Found .git directory at {parent}")
                return True
            # Stop if we hit site-packages (packaged installation)
            if 'site-packages' in str(parent):
                logger.debug(f"Production mode: Running from site-packages at {parent}")
                return False
        
        # Default to development if no clear indicators
        logger.debug("Development mode: No clear indicators, defaulting to development")
        return True
    
    def deploy(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute deployment (wrapper for execute_main_deployment_flow).
        
        Args:
            dry_run: If True, validate but don't execute
            
        Returns:
            Deployment result dictionary
        """
        # Import here to avoid circular dependencies
        try:
            # Try to import from old location (development)
            sys.path.insert(0, str(self.project_root / 'src'))
            from phases.phases_orchestrator import PhasesOrchestrator
        except ImportError:
            logger.warning("Could not import PhasesOrchestrator - deploy-manager phases not available")
            return {
                'status': 'error',
                'message': 'PhasesOrchestrator not available. This is a wrapper class for dual-mode support.'
            }
        
        # Initialize phases orchestrator with our paths
        orchestrator = PhasesOrchestrator(
            project_root=self.project_root,
            config=self.config
        )
        
        # Execute deployment flow
        result = orchestrator.execute_main_deployment_flow()
        
        return result
    
    def render_templates(self) -> Dict[str, Any]:
        """
        Render Jinja2 templates.
        
        Templates are loaded from self.templates_dir
        Outputs are written to self.output_dir
        
        Returns:
            Dictionary with render results
        """
        from jinja2 import Environment, FileSystemLoader
        import yaml
        
        logger.info(f"Rendering templates from {self.templates_dir} to {self.output_dir}")
        
        # Create Jinja2 environment
        env = Environment(loader=FileSystemLoader(self.templates_dir))
        
        # Discover templates
        templates = list(self.templates_dir.glob('*.j2'))
        
        if not templates:
            logger.warning(f"No templates found in {self.templates_dir}")
            return {'status': 'warning', 'message': 'No templates found', 'files_rendered': 0}
        
        rendered_files = []
        
        for template_file in templates:
            try:
                template = env.get_template(template_file.name)
                rendered = template.render(**self.config)
                
                # Write to output dir
                output_file = self.output_dir / template_file.name.replace('.j2', '')
                output_file.write_text(rendered)
                
                rendered_files.append(str(output_file))
                logger.info(f"Rendered: {template_file.name} -> {output_file.name}")
            except Exception as e:
                logger.error(f"Failed to render {template_file.name}: {e}")
                return {
                    'status': 'error',
                    'message': f"Template rendering failed: {e}",
                    'failed_template': template_file.name
                }
        
        return {
            'status': 'success',
            'files_rendered': len(rendered_files),
            'rendered_files': rendered_files
        }
    
    def create_snapshot(self, snapshot_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a deployment snapshot.
        
        Args:
            snapshot_name: Optional snapshot name (auto-generated if None)
            
        Returns:
            Snapshot creation result
        """
        from datetime import datetime
        import shutil
        
        if snapshot_name is None:
            snapshot_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot_path = self.snapshot_dir / snapshot_name
        snapshot_path.mkdir(parents=True, exist_ok=True)
        
        # Copy configuration
        if self.config_file and Path(self.config_file).exists():
            shutil.copy2(self.config_file, snapshot_path / 'config')
        
        # Copy rendered outputs
        for file in self.output_dir.iterdir():
            if file.is_file():
                shutil.copy2(file, snapshot_path / file.name)
        
        logger.info(f"Created snapshot: {snapshot_path}")
        
        return {
            'status': 'success',
            'snapshot_name': snapshot_name,
            'snapshot_path': str(snapshot_path)
        }


# Alias for backward compatibility
PhasesOrchestrator = DeploymentOrchestrator
