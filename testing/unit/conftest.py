"""
Test fixtures and configuration for deploy-manager unit tests.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing."""
    client = MagicMock()
    client.containers = MagicMock()
    client.images = MagicMock()
    client.networks = MagicMock()
    return client


@pytest.fixture
def sample_compose_file():
    """Sample docker-compose.yml content for testing."""
    return """
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: testdb
"""


@pytest.fixture
def mock_deployment_config():
    """Mock deployment configuration."""
    return {
        "domain": "test.example.com",
        "port": "8080",
        "ssl_enabled": True,
        "backup_enabled": False
    }
