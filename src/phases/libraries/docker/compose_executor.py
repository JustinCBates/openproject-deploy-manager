#!/usr/bin/env python3
"""
ComposeExecutor Unit

Execute docker-compose commands
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging
import subprocess
import shlex

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of docker-compose command execution"""
    success: bool
    command: str
    stdout: str
    stderr: str
    returncode: int
    error: Optional[str] = None
    
    def __str__(self) -> str:
        if self.success:
            return f"✅ Command successful: {self.command}"
        else:
            return f"❌ Command failed (code {self.returncode}): {self.error}"


class ComposeExecutor:
    """
    Execute docker-compose commands with proper error handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ComposeExecutor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.compose_file = config.get('compose_file') if config else None
        self.project_name = config.get('project_name') if config else None
        self.working_dir = Path(config.get('working_dir', '.')) if config else Path('.')

    def execute(self, command: str, capture_output: bool = True, timeout: int = 300) -> ExecutionResult:
        """
        Execute a docker-compose command.
        
        Args:
            command: Compose command (e.g., 'up -d', 'down', 'ps')
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds (default 300)
            
        Returns:
            ExecutionResult with command output and status
            
        Example:
            executor = ComposeExecutor({'compose_file': 'docker-compose.yml'})
            result = executor.execute('up -d')
            if result.success:
                print("Deployment successful!")
        """
        # Build full command - try docker compose (modern) first, fallback to docker-compose
        cmd_parts = ['docker', 'compose']
        
        if self.compose_file:
            cmd_parts.extend(['-f', str(self.compose_file)])
        
        if self.project_name:
            cmd_parts.extend(['-p', self.project_name])
        
        # Add the actual command
        cmd_parts.extend(shlex.split(command))
        
        full_command = ' '.join(cmd_parts)
        logger.info(f"Executing: {full_command}")
        
        try:
            # Execute command
            result = subprocess.run(
                cmd_parts,
                cwd=self.working_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False  # Don't raise on non-zero exit
            )
            
            # Check if successful
            success = result.returncode == 0
            
            if success:
                logger.info(f"✅ Command successful: {command}")
                logger.debug(f"Output: {result.stdout[:200]}")
            else:
                logger.error(f"❌ Command failed with code {result.returncode}: {command}")
                logger.error(f"Error: {result.stderr}")
            
            return ExecutionResult(
                success=success,
                command=full_command,
                stdout=result.stdout if capture_output else "",
                stderr=result.stderr if capture_output else "",
                returncode=result.returncode,
                error=result.stderr if not success else None
            )
            
        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after {timeout}s"
            logger.error(f"❌ {error_msg}: {command}")
            return ExecutionResult(
                success=False,
                command=full_command,
                stdout="",
                stderr=error_msg,
                returncode=-1,
                error=error_msg
            )
        except FileNotFoundError:
            error_msg = "docker compose not found - is Docker installed?"
            logger.error(f"❌ {error_msg}")
            return ExecutionResult(
                success=False,
                command=full_command,
                stdout="",
                stderr=error_msg,
                returncode=-1,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return ExecutionResult(
                success=False,
                command=full_command,
                stdout="",
                stderr=error_msg,
                returncode=-1,
                error=error_msg
            )
    
    def up(self, detached: bool = True, build: bool = False) -> ExecutionResult:
        """
        Run 'docker-compose up'.
        
        Args:
            detached: Run in detached mode (-d)
            build: Build images before starting (--build)
            
        Returns:
            ExecutionResult
        """
        cmd = "up"
        if detached:
            cmd += " -d"
        if build:
            cmd += " --build"
        
        return self.execute(cmd)
    
    def down(self, volumes: bool = False, remove_orphans: bool = True) -> ExecutionResult:
        """
        Run 'docker-compose down'.
        
        Args:
            volumes: Remove volumes (-v)
            remove_orphans: Remove orphan containers (--remove-orphans)
            
        Returns:
            ExecutionResult
        """
        cmd = "down"
        if volumes:
            cmd += " -v"
        if remove_orphans:
            cmd += " --remove-orphans"
        
        return self.execute(cmd)
    
    def ps(self) -> ExecutionResult:
        """
        Run 'docker-compose ps' to list containers.
        
        Returns:
            ExecutionResult with container list
        """
        return self.execute("ps")
    
    def logs(self, service: Optional[str] = None, follow: bool = False, tail: int = 100) -> ExecutionResult:
        """
        Run 'docker-compose logs'.
        
        Args:
            service: Specific service to get logs from (None = all)
            follow: Follow log output (-f)
            tail: Number of lines to show (default 100)
            
        Returns:
            ExecutionResult with logs
        """
        cmd = f"logs --tail {tail}"
        if follow:
            cmd += " -f"
        if service:
            cmd += f" {service}"
        
        return self.execute(cmd, timeout=600 if follow else 60)


def main():
    """Test the unit."""
    import tempfile
    import os
    
    # Create a test compose file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
version: '3.8'
services:
  test:
    image: alpine:latest
    command: echo "Hello from compose"
""")
        compose_file = f.name
    
    try:
        print("Testing ComposeExecutor")
        print("=" * 50)
        
        executor = ComposeExecutor({
            'compose_file': compose_file,
            'project_name': 'test-compose'
        })
        
        # Test ps command
        print("\n1. Testing 'ps' command:")
        result = executor.ps()
        print(f"   {result}")
        print(f"   Output: {result.stdout[:100]}")
        
        # Test validation (dry-run)
        print("\n2. Testing 'config' validation:")
        result = executor.execute('config')
        print(f"   {result}")
        
        print("\n✅ ComposeExecutor tests complete")
        
    finally:
        # Cleanup
        os.unlink(compose_file)


if __name__ == '__main__':
    main()
