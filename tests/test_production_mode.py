"""Tests for production mode operation in deploy-manager"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def sample_config():
    return {
        "domain": "openproject.example.com",
        "postgres_password": "secret123",
    }


def test_production_mode_requires_paths(sample_config):
    """Test that production mode requires templates_dir and output_dir"""
    from openproject_deploy_manager import DeploymentOrchestrator

    with pytest.raises(ValueError, match="templates_dir and output_dir required"):
        DeploymentOrchestrator(config=sample_config, use_local_paths=False)


def test_production_mode_with_paths(sample_config):
    """Test production mode with provided paths"""
    from openproject_deploy_manager import DeploymentOrchestrator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        templates_dir = tmpdir / "templates"
        output_dir = tmpdir / "outputs"
        templates_dir.mkdir()

        deployer = DeploymentOrchestrator(
            config=sample_config,
            templates_dir=templates_dir,
            output_dir=output_dir,
            use_local_paths=False,
        )

        # Should use provided paths
        assert deployer.templates_dir == templates_dir
        assert deployer.output_dir == output_dir
        assert output_dir.exists()


def test_production_mode_snapshot_defaults(sample_config):
    """Test that snapshot_dir defaults to output_dir/snapshots in production"""
    from openproject_deploy_manager import DeploymentOrchestrator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        templates_dir = tmpdir / "templates"
        output_dir = tmpdir / "outputs"
        templates_dir.mkdir()

        deployer = DeploymentOrchestrator(
            config=sample_config,
            templates_dir=templates_dir,
            output_dir=output_dir,
            use_local_paths=False,
        )

        # Snapshot should default to output_dir/snapshots
        assert deployer.snapshot_dir == output_dir / "snapshots"
        assert deployer.snapshot_dir.exists()


def test_production_mode_all_paths_specified(sample_config):
    """Test production mode with all paths explicitly specified"""
    from openproject_deploy_manager import DeploymentOrchestrator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        templates_dir = tmpdir / "templates"
        output_dir = tmpdir / "outputs"
        snapshot_dir = tmpdir / "backups" / "snapshots"
        compose_file = tmpdir / "docker-compose.yml"

        templates_dir.mkdir()
        compose_file.touch()

        deployer = DeploymentOrchestrator(
            config=sample_config,
            templates_dir=templates_dir,
            output_dir=output_dir,
            snapshot_dir=snapshot_dir,
            compose_file=compose_file,
            use_local_paths=False,
        )

        assert deployer.templates_dir == templates_dir
        assert deployer.output_dir == output_dir
        assert deployer.snapshot_dir == snapshot_dir
        assert deployer.compose_file == compose_file
        assert output_dir.exists()
        assert snapshot_dir.exists()


def test_render_templates_in_production(sample_config):
    """Test template rendering in production mode"""
    from openproject_deploy_manager import DeploymentOrchestrator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        templates_dir = tmpdir / "templates"
        output_dir = tmpdir / "outputs"
        templates_dir.mkdir()

        # Create a test template
        template_file = templates_dir / "test.conf.j2"
        template_file.write_text(
            "Domain: {{ domain }}\nPassword: {{ postgres_password }}"
        )

        deployer = DeploymentOrchestrator(
            config=sample_config,
            templates_dir=templates_dir,
            output_dir=output_dir,
            use_local_paths=False,
        )

        # Render templates
        result = deployer.render_templates()

        # Should succeed
        assert result["status"] == "success"
        assert result["files_rendered"] == 1

        # Check output file
        output_file = output_dir / "test.conf"
        assert output_file.exists()
        content = output_file.read_text()
        assert "openproject.example.com" in content
        assert "secret123" in content


def test_create_snapshot_in_production(sample_config):
    """Test snapshot creation in production mode"""
    from openproject_deploy_manager import DeploymentOrchestrator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        templates_dir = tmpdir / "templates"
        output_dir = tmpdir / "outputs"
        templates_dir.mkdir()
        output_dir.mkdir()

        # Create some output files
        (output_dir / "test.conf").write_text("test content")

        deployer = DeploymentOrchestrator(
            config=sample_config,
            templates_dir=templates_dir,
            output_dir=output_dir,
            use_local_paths=False,
        )

        # Create snapshot
        result = deployer.create_snapshot("test_snapshot")

        # Should succeed
        assert result["status"] == "success"
        assert result["snapshot_name"] == "test_snapshot"

        # Check snapshot exists
        snapshot_path = deployer.snapshot_dir / "test_snapshot"
        assert snapshot_path.exists()
        assert (snapshot_path / "test.conf").exists()


def test_config_paths_added_in_production(sample_config):
    """Test that config gets path information in production mode"""
    from openproject_deploy_manager import DeploymentOrchestrator

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        templates_dir = tmpdir / "templates"
        output_dir = tmpdir / "outputs"
        templates_dir.mkdir()

        deployer = DeploymentOrchestrator(
            config=sample_config,
            templates_dir=templates_dir,
            output_dir=output_dir,
            use_local_paths=False,
        )

        # Config should have _paths
        assert "_paths" in deployer.config
        assert deployer.config["_paths"]["templates_dir"] == str(templates_dir)
        assert deployer.config["_paths"]["output_dir"] == str(output_dir)
