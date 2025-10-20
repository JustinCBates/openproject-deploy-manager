"""OpenProject Deployment Manager

Multi-phase deployment orchestration for OpenProject Docker Compose with
validation, health checks, and rollback capabilities.

Supports dual-mode operation:
- Development Mode: Auto-detected via .git directory, uses local paths
- Production Mode: Receives paths from orchestrator, works as pip package
"""

__version__ = "2.0.0"
__author__ = "OpenProject Contributors"

from .deployment_orchestrator import DeploymentOrchestrator, PhasesOrchestrator

__all__ = ["DeploymentOrchestrator", "PhasesOrchestrator", "__version__"]
