#!/usr/bin/env python3
"""
SnapshotStorer Unit

Store and manage snapshots
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
import logging
import json
import datetime

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    """Snapshot data structure."""
    id: str
    timestamp: str
    project_name: str
    containers: List[Dict[str, Any]] = field(default_factory=list)
    networks: List[Dict[str, Any]] = field(default_factory=list)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    backup_dir: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class StoreResult:
    """Result of store operation."""
    success: bool
    snapshot_id: Optional[str] = None
    snapshot_path: Optional[Path] = None
    error: Optional[str] = None


@dataclass
class LoadResult:
    """Result of load operation."""
    success: bool
    snapshot: Optional[Snapshot] = None
    error: Optional[str] = None


class SnapshotStorer:
    """
    Store and manage snapshots
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize SnapshotStorer.
        
        Args:
            config: Optional configuration dictionary with:
                - snapshot_dir: Directory for storing snapshots
                - max_snapshots: Maximum number of snapshots to keep
                - compression: Enable compression (not implemented yet)
        """
        self.config = config or {}
        self.snapshot_dir = Path(self.config.get('snapshot_dir', './snapshots'))
        self.max_snapshots = self.config.get('max_snapshots', 10)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def store(self, snapshot: Snapshot) -> StoreResult:
        """
        Store snapshot to disk.
        
        Args:
            snapshot: Snapshot object to store
            
        Returns:
            StoreResult with success status and snapshot path
            
        Example:
            storer = SnapshotStorer()
            snapshot = Snapshot(
                id='snap_123',
                timestamp='2025-10-15T12:00:00',
                project_name='myapp',
                containers=[...]
            )
            result = storer.store(snapshot)
            if result.success:
                print(f"Stored at: {result.snapshot_path}")
        """
        try:
            # Create snapshot file path
            snapshot_file = self.snapshot_dir / f"{snapshot.id}.json"
            
            # Convert to dict
            snapshot_dict = snapshot.to_dict()
            
            # Write to file
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_dict, f, indent=2)
            
            logger.info(f"✅ Stored snapshot: {snapshot_file}")
            
            # Cleanup old snapshots if needed
            self._cleanup_old_snapshots()
            
            return StoreResult(
                success=True,
                snapshot_id=snapshot.id,
                snapshot_path=snapshot_file
            )
            
        except Exception as e:
            logger.error(f"Failed to store snapshot: {e}", exc_info=True)
            return StoreResult(
                success=False,
                error=str(e)
            )

    def load(self, snapshot_id: str) -> LoadResult:
        """
        Load snapshot from disk.
        
        Args:
            snapshot_id: ID of snapshot to load
            
        Returns:
            LoadResult with snapshot data
            
        Example:
            storer = SnapshotStorer()
            result = storer.load('snap_123')
            if result.success:
                print(f"Loaded {len(result.snapshot.containers)} containers")
        """
        try:
            # Find snapshot file
            snapshot_file = self.snapshot_dir / f"{snapshot_id}.json"
            
            if not snapshot_file.exists():
                return LoadResult(
                    success=False,
                    error=f"Snapshot not found: {snapshot_id}"
                )
            
            # Read from file
            with open(snapshot_file, 'r') as f:
                snapshot_dict = json.load(f)
            
            # Convert to Snapshot object
            snapshot = Snapshot.from_dict(snapshot_dict)
            
            logger.info(f"✅ Loaded snapshot: {snapshot_id}")
            
            return LoadResult(
                success=True,
                snapshot=snapshot
            )
            
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}", exc_info=True)
            return LoadResult(
                success=False,
                error=str(e)
            )

    def list(self) -> List[Snapshot]:
        """
        List all available snapshots.
        
        Returns:
            List of Snapshot objects (metadata only, containers/networks/volumes not loaded)
            
        Example:
            storer = SnapshotStorer()
            snapshots = storer.list()
            for snapshot in snapshots:
                print(f"{snapshot.id}: {snapshot.timestamp} ({snapshot.project_name})")
        """
        snapshots = []
        
        try:
            # Find all snapshot files
            snapshot_files = sorted(
                self.snapshot_dir.glob('*.json'),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # Newest first
            )
            
            for snapshot_file in snapshot_files:
                try:
                    with open(snapshot_file, 'r') as f:
                        snapshot_dict = json.load(f)
                    
                    # Create snapshot with minimal data for listing
                    snapshot = Snapshot(
                        id=snapshot_dict['id'],
                        timestamp=snapshot_dict['timestamp'],
                        project_name=snapshot_dict['project_name'],
                        metadata=snapshot_dict.get('metadata', {})
                    )
                    
                    # Add counts for display
                    snapshot.metadata['container_count'] = len(snapshot_dict.get('containers', []))
                    snapshot.metadata['network_count'] = len(snapshot_dict.get('networks', []))
                    snapshot.metadata['volume_count'] = len(snapshot_dict.get('volumes', []))
                    
                    snapshots.append(snapshot)
                    
                except Exception as e:
                    logger.warning(f"Failed to load snapshot {snapshot_file}: {e}")
                    continue
            
            logger.info(f"Found {len(snapshots)} snapshot(s)")
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}")
        
        return snapshots

    def delete(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: ID of snapshot to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            snapshot_file = self.snapshot_dir / f"{snapshot_id}.json"
            
            if not snapshot_file.exists():
                logger.warning(f"Snapshot not found: {snapshot_id}")
                return False
            
            snapshot_file.unlink()
            logger.info(f"✅ Deleted snapshot: {snapshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete snapshot: {e}")
            return False

    def get_latest(self, project_name: Optional[str] = None) -> LoadResult:
        """
        Get the latest snapshot, optionally filtered by project name.
        
        Args:
            project_name: Optional project name filter
            
        Returns:
            LoadResult with latest snapshot
        """
        snapshots = self.list()
        
        # Filter by project name if provided
        if project_name:
            snapshots = [s for s in snapshots if s.project_name == project_name]
        
        if not snapshots:
            return LoadResult(
                success=False,
                error="No snapshots found"
            )
        
        # Load full snapshot data for the latest one
        latest_snapshot = snapshots[0]
        return self.load(latest_snapshot.id)

    def _cleanup_old_snapshots(self):
        """Remove old snapshots if exceeding max_snapshots limit."""
        try:
            snapshots = self.list()
            
            if len(snapshots) > self.max_snapshots:
                # Delete oldest snapshots
                to_delete = snapshots[self.max_snapshots:]
                
                for snapshot in to_delete:
                    self.delete(snapshot.id)
                    logger.info(f"Cleaned up old snapshot: {snapshot.id}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old snapshots: {e}")



def main():
    """Test the unit."""
    import tempfile
    
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\nTesting SnapshotStorer")
    print("=" * 50)
    
    # Create temporary snapshot directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        storer = SnapshotStorer({'snapshot_dir': temp_path / 'snapshots'})
        
        # Test 1: Create and store snapshot
        print("\n1. Testing store snapshot:")
        snapshot = Snapshot(
            id='snap_20251015_120000',
            timestamp='2025-10-15T12:00:00',
            project_name='test-app',
            containers=[
                {'name': 'web', 'image': 'nginx:alpine', 'status': 'running'},
                {'name': 'redis', 'image': 'redis:alpine', 'status': 'running'}
            ],
            networks=[
                {'name': 'test-network', 'driver': 'bridge'}
            ],
            volumes=[
                {'name': 'test-volume', 'driver': 'local'}
            ],
            config_files=['/path/to/config.yml', '/path/to/docker-compose.yml'],
            metadata={'version': '1.0.0', 'environment': 'production'}
        )
        
        result = storer.store(snapshot)
        
        if result.success:
            print(f"   ✅ Stored snapshot: {result.snapshot_id}")
            print(f"   Snapshot path: {result.snapshot_path}")
        else:
            print(f"   ❌ Failed to store: {result.error}")
        
        # Test 2: Load snapshot
        print("\n2. Testing load snapshot:")
        result = storer.load('snap_20251015_120000')
        
        if result.success:
            loaded = result.snapshot
            print(f"   ✅ Loaded snapshot: {loaded.id}")
            print(f"   Project: {loaded.project_name}")
            print(f"   Containers: {len(loaded.containers)}")
            print(f"   Networks: {len(loaded.networks)}")
            print(f"   Volumes: {len(loaded.volumes)}")
            print(f"   Metadata: {loaded.metadata}")
        else:
            print(f"   ❌ Failed to load: {result.error}")
        
        # Test 3: List snapshots
        print("\n3. Testing list snapshots:")
        
        # Create a few more snapshots
        for i in range(2, 5):
            snap = Snapshot(
                id=f'snap_2025101{i}_120000',
                timestamp=f'2025-10-1{i}T12:00:00',
                project_name='test-app',
                containers=[],
                networks=[],
                volumes=[]
            )
            storer.store(snap)
        
        snapshots = storer.list()
        print(f"   ✅ Found {len(snapshots)} snapshots:")
        for snap in snapshots:
            print(f"     - {snap.id} ({snap.project_name}) - {snap.timestamp}")
        
        # Test 4: Get latest snapshot
        print("\n4. Testing get latest snapshot:")
        result = storer.get_latest('test-app')
        
        if result.success:
            print(f"   ✅ Latest snapshot: {result.snapshot.id}")
        else:
            print(f"   ❌ Failed: {result.error}")
        
        # Test 5: Delete snapshot
        print("\n5. Testing delete snapshot:")
        deleted = storer.delete('snap_20251012_120000')
        
        if deleted:
            print(f"   ✅ Deleted snapshot")
        else:
            print(f"   ❌ Failed to delete")
        
        # Test 6: Load non-existent snapshot
        print("\n6. Testing load non-existent snapshot:")
        result = storer.load('non_existent_snap')
        
        if not result.success:
            print(f"   ✅ Handled correctly: {result.error}")
        else:
            print(f"   ❌ Should have failed")
    
    print("\n✅ SnapshotStorer tests complete")


if __name__ == '__main__':
    main()
