"""Tests for development mode operation in deploy-manager"""

import pytest
import os
import tempfile
from pathlib import Path


# Force development mode for these tests
@pytest.fixture(autouse=True)
def setup_dev_mode():
    """Force development mode for tests"""
    os.environ["OPENPROJECT_DEV_MODE"] = "1"
    yield
    if "OPENPROJECT_DEV_MODE" in os.environ:
        del os.environ["OPENPROJECT_DEV_MODE"]


@pytest.fixture
def sample_config():
    return {
        "domain": "openproject.example.com",
        "postgres_password": "secret123",
    }


def test_auto_detect_development(sample_config):
    """Test that development mode is auto-detected"""
    from openproject_deploy_manager import DeploymentOrchestrator

    assert DeploymentOrchestrator._is_development_mode() is True


def test_uses_local_directories(sample_config):
    """Test that local directories are used in development mode"""
    from openproject_deploy_manager import DeploymentOrchestrator

    deployer = DeploymentOrchestrator(config=sample_config)

    # Should use local directories (not site-packages)
    assert "site-packages" not in str(deployer.output_dir)
    assert deployer.output_dir.exists()
    assert deployer.snapshot_dir.exists()

    # Directories should be created relative to package
    assert "deploy-manager" in str(deployer.output_dir) or "outputs" in str(
        deployer.output_dir
    )


def test_explicit_development_mode(sample_config):
    """Test explicitly setting development mode"""
    from openproject_deploy_manager import DeploymentOrchestrator

    deployer = DeploymentOrchestrator(config=sample_config, use_local_paths=True)

    assert deployer.output_dir.exists()
    assert deployer.snapshot_dir.exists()
    assert "site-packages" not in str(deployer.output_dir)


def test_custom_paths_in_development(sample_config):
    """Test that custom paths can override defaults even in dev mode"""
    from openproject_deploy_manager import DeploymentOrchestrator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        custom_templates = tmpdir / "custom_templates"
        custom_output = tmpdir / "custom_output"
        custom_templates.mkdir()

        deployer = DeploymentOrchestrator(
            config=sample_config,
            templates_dir=custom_templates,
            output_dir=custom_output,
            use_local_paths=True,  # Still in dev mode
        )

        # Should use custom paths even in dev mode
        assert deployer.templates_dir == custom_templates
        assert deployer.output_dir == custom_output
        assert custom_output.exists()


def test_config_paths_updated(sample_config):
    """Test that config gets updated with path information"""
    from openproject_deploy_manager import DeploymentOrchestrator

    deployer = DeploymentOrchestrator(config=sample_config)

    # Config should have _paths added
    assert "_paths" in deployer.config
    assert "project_root" in deployer.config["_paths"]
    assert "templates_dir" in deployer.config["_paths"]
    assert "output_dir" in deployer.config["_paths"]
