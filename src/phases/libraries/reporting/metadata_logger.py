#!/usr/bin/env python3
"""
MetadataLogger Unit

Log deployment metadata for audit trail and historical tracking
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class MetadataLogger:
    """
    Log deployment metadata for audit trail
    
    Features:
    - Append-only log format
    - JSON structured logging
    - Timestamped entries
    - Metadata extraction from context
    - Historical tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize MetadataLogger.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.log_format = self.config.get('log_format', 'json')  # 'json' or 'text'

    def log(self, metadata: Dict[str, Any], output_path: Path) -> bool:
        """
        Log metadata to file
        
        Args:
            metadata: Deployment metadata to log
            output_path: Path to log file
            
        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add timestamp if not present
            if 'timestamp' not in metadata:
                metadata['timestamp'] = datetime.now().isoformat()
            
            # Append to log file
            mode = 'a'  # Append mode
            
            if self.log_format == 'json':
                # JSON format - one entry per line
                with open(output_path, mode) as f:
                    f.write(json.dumps(metadata) + '\n')
            else:
                # Text format
                with open(output_path, mode) as f:
                    f.write(self._format_text_entry(metadata) + '\n')
            
            logger.info(f"Metadata logged to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log metadata: {e}")
            return False

    def log_deployment(self, context: Dict[str, Any], output_path: Path) -> bool:
        """
        Log deployment metadata extracted from context
        
        Args:
            context: Full deployment context
            output_path: Path to log file
            
        Returns:
            True if successful
        """
        try:
            # Extract relevant metadata from context
            config = context.get('validated_config', context.get('config', {}))
            
            metadata = {
                'event_type': 'deployment',
                'timestamp': datetime.now().isoformat(),
                'project_name': config.get('project_name', 'unknown'),
                'environment': config.get('environment', 'development'),
                'domain': config.get('domain'),
                'port': config.get('port'),
                'https_enabled': config.get('https_enabled', False),
                'snapshot_id': context.get('snapshot_id'),
                'duration_seconds': context.get('total_duration', 0),
                'phases_completed': self._get_completed_phases(context),
                'services_deployed': context.get('services_deployed', 0),
                'deployment_status': 'success' if self._is_successful(context) else 'failed',
                'deployer': context.get('deployer', 'unknown'),
                'git_commit': context.get('git_commit'),
                'git_branch': context.get('git_branch'),
            }
            
            return self.log(metadata, output_path)
            
        except Exception as e:
            logger.error(f"Failed to log deployment metadata: {e}")
            return False

    def log_rollback(self, snapshot_id: str, reason: str, output_path: Path) -> bool:
        """
        Log rollback event
        
        Args:
            snapshot_id: Snapshot being restored
            reason: Reason for rollback
            output_path: Path to log file
            
        Returns:
            True if successful
        """
        metadata = {
            'event_type': 'rollback',
            'timestamp': datetime.now().isoformat(),
            'snapshot_id': snapshot_id,
            'reason': reason,
            'status': 'initiated'
        }
        
        return self.log(metadata, output_path)

    def read_log(self, log_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Read log entries from file
        
        Args:
            log_path: Path to log file
            limit: Maximum number of entries to return (most recent)
            
        Returns:
            List of log entries
        """
        if not log_path.exists():
            logger.warning(f"Log file does not exist: {log_path}")
            return []
        
        try:
            entries = []
            
            if self.log_format == 'json':
                with open(log_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
            else:
                # Text format - basic parsing
                with open(log_path, 'r') as f:
                    content = f.read()
                    # Simple text parsing (not as structured)
                    entries.append({'raw': content})
            
            # Return most recent entries if limit specified
            if limit and len(entries) > limit:
                entries = entries[-limit:]
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to read log: {e}")
            return []

    def _get_completed_phases(self, context: Dict[str, Any]) -> List[str]:
        """Extract list of completed phases from context"""
        completed = []
        for phase_num in range(1, 7):
            phase_result = context.get(f'phase_{phase_num}_result', {})
            if phase_result.get('status') == 'success':
                completed.append(phase_result.get('phase_id', f'phase_{phase_num}'))
        return completed

    def _is_successful(self, context: Dict[str, Any]) -> bool:
        """Determine if deployment was successful"""
        # Check if any phase failed
        for phase_num in range(1, 7):
            phase_result = context.get(f'phase_{phase_num}_result', {})
            if phase_result.get('status') in ['error', 'failed']:
                return False
        return True

    def _format_text_entry(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as text entry"""
        lines = [
            f"[{metadata.get('timestamp')}] {metadata.get('event_type', 'unknown').upper()}"
        ]
        
        for key, value in metadata.items():
            if key not in ['timestamp', 'event_type']:
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)


def main():
    """Test the unit."""
    import tempfile
    logging.basicConfig(level=logging.INFO)
    
    logger_unit = MetadataLogger()
    
    # Create temporary log file
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "deployment.log"
        
        # Test logging metadata
        print("Testing metadata logging...\n")
        
        test_metadata = {
            'project_name': 'test-app',
            'environment': 'staging',
            'snapshot_id': 'snap_test_20251015',
            'duration_seconds': 42.5,
            'deployment_status': 'success'
        }
        
        success = logger_unit.log(test_metadata, log_path)
        print(f"Log entry written: {success}")
        
        # Log another entry
        logger_unit.log_rollback('snap_test_20251015', 'Testing rollback', log_path)
        
        # Read log
        print("\nReading log entries:")
        entries = logger_unit.read_log(log_path)
        for i, entry in enumerate(entries, 1):
            print(f"\nEntry {i}:")
            print(json.dumps(entry, indent=2))


if __name__ == '__main__':
    main()
