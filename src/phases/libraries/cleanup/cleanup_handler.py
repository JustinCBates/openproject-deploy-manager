#!/usr/bin/env python3
"""
CleanupHandler Unit

Clean up temporary files and old artifacts safely
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
import shutil
import logging

logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """Result of cleanup operation"""
    success: bool
    files_removed: int
    directories_removed: int
    space_freed_bytes: int
    errors: List[str]


class CleanupHandler:
    """
    Clean up temporary files and old artifacts
    
    Features:
    - Safe file deletion with pattern matching
    - Old artifact cleanup (by age/count)
    - Dry-run mode
    - Size calculation
    - Protected files/directories
    """
    
    # Patterns to never delete (safety)
    PROTECTED_PATTERNS = {
        'src', '.git', '.gitignore', 'README.md', 'LICENSE',
        'pyproject.toml', 'setup.py', 'requirements.txt'
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CleanupHandler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.protected_dirs = set(self.config.get('protected_dirs', self.PROTECTED_PATTERNS))
        self.dry_run = self.config.get('dry_run', False)

    def cleanup(self, target_dir: Path, patterns: Optional[List[str]] = None,
                recursive: bool = False) -> CleanupResult:
        """
        Clean up files matching patterns
        
        Args:
            target_dir: Directory to clean
            patterns: List of glob patterns to match (default: ['*.tmp', '*.log', '__pycache__'])
            recursive: Whether to search recursively
            
        Returns:
            CleanupResult with cleanup statistics
        """
        if patterns is None:
            patterns = ['*.tmp', '*.log', '__pycache__']
        
        files_removed = 0
        dirs_removed = 0
        space_freed = 0
        errors = []
        
        try:
            if not target_dir.exists():
                logger.warning(f"Target directory does not exist: {target_dir}")
                return CleanupResult(
                    success=True,
                    files_removed=0,
                    directories_removed=0,
                    space_freed_bytes=0,
                    errors=[]
                )
            
            # Safety check
            if self._is_protected(target_dir):
                error_msg = f"Refusing to clean protected directory: {target_dir}"
                logger.error(error_msg)
                return CleanupResult(
                    success=False,
                    files_removed=0,
                    directories_removed=0,
                    space_freed_bytes=0,
                    errors=[error_msg]
                )
            
            # Find matching files/dirs
            matches = self._find_matches(target_dir, patterns, recursive)
            
            # Remove matches
            for path in matches:
                try:
                    size = self._get_size(path)
                    
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would remove: {path} ({size} bytes)")
                        continue
                    
                    if path.is_file():
                        path.unlink()
                        files_removed += 1
                        logger.info(f"Removed file: {path}")
                    elif path.is_dir():
                        shutil.rmtree(path)
                        dirs_removed += 1
                        logger.info(f"Removed directory: {path}")
                    
                    space_freed += size
                    
                except Exception as e:
                    error_msg = f"Failed to remove {path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Cleanup complete: {files_removed} files, {dirs_removed} dirs, "
                       f"{space_freed} bytes freed")
            
            return CleanupResult(
                success=len(errors) == 0,
                files_removed=files_removed,
                directories_removed=dirs_removed,
                space_freed_bytes=space_freed,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return CleanupResult(
                success=False,
                files_removed=files_removed,
                directories_removed=dirs_removed,
                space_freed_bytes=space_freed,
                errors=[str(e)]
            )

    def cleanup_old_artifacts(self, artifacts_dir: Path, keep_count: int = 5,
                             pattern: str = '*') -> CleanupResult:
        """
        Clean up old artifacts, keeping only the most recent N
        
        Args:
            artifacts_dir: Directory containing artifacts
            keep_count: Number of most recent artifacts to keep
            pattern: Glob pattern to match artifacts
            
        Returns:
            CleanupResult with cleanup statistics
        """
        try:
            if not artifacts_dir.exists():
                logger.warning(f"Artifacts directory does not exist: {artifacts_dir}")
                return CleanupResult(
                    success=True,
                    files_removed=0,
                    directories_removed=0,
                    space_freed_bytes=0,
                    errors=[]
                )
            
            # Get all matching artifacts sorted by modification time
            artifacts = sorted(
                artifacts_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True  # Newest first
            )
            
            # Keep only the most recent N
            to_remove = artifacts[keep_count:]
            
            if not to_remove:
                logger.info(f"No old artifacts to clean ({len(artifacts)} total, keeping {keep_count})")
                return CleanupResult(
                    success=True,
                    files_removed=0,
                    directories_removed=0,
                    space_freed_bytes=0,
                    errors=[]
                )
            
            logger.info(f"Cleaning {len(to_remove)} old artifacts (keeping {keep_count} newest)")
            
            # Use cleanup() to remove old artifacts
            # Create a temporary list of paths to clean
            files_removed = 0
            dirs_removed = 0
            space_freed = 0
            errors = []
            
            for artifact in to_remove:
                try:
                    size = self._get_size(artifact)
                    
                    if self.dry_run:
                        logger.info(f"[DRY RUN] Would remove old artifact: {artifact}")
                        continue
                    
                    if artifact.is_file():
                        artifact.unlink()
                        files_removed += 1
                    elif artifact.is_dir():
                        shutil.rmtree(artifact)
                        dirs_removed += 1
                    
                    space_freed += size
                    logger.info(f"Removed old artifact: {artifact}")
                    
                except Exception as e:
                    error_msg = f"Failed to remove {artifact}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            return CleanupResult(
                success=len(errors) == 0,
                files_removed=files_removed,
                directories_removed=dirs_removed,
                space_freed_bytes=space_freed,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Artifact cleanup failed: {e}")
            return CleanupResult(
                success=False,
                files_removed=0,
                directories_removed=0,
                space_freed_bytes=0,
                errors=[str(e)]
            )

    def _find_matches(self, directory: Path, patterns: List[str], 
                     recursive: bool) -> Set[Path]:
        """Find all files/dirs matching patterns"""
        matches = set()
        
        for pattern in patterns:
            if recursive:
                matches.update(directory.rglob(pattern))
            else:
                matches.update(directory.glob(pattern))
        
        # Filter out protected items
        return {m for m in matches if not self._is_protected(m)}

    def _is_protected(self, path: Path) -> bool:
        """Check if path is protected from deletion"""
        # Check if path name matches any protected pattern
        for protected in self.protected_dirs:
            if path.name == protected or protected in path.parts:
                return True
        return False

    def _get_size(self, path: Path) -> int:
        """Get total size of file or directory in bytes"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            total = 0
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except:
                        pass
            return total
        return 0


def main():
    """Test the unit."""
    import tempfile
    logging.basicConfig(level=logging.INFO)
    
    handler = CleanupHandler(config={'dry_run': False})
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_cleanup"
        test_dir.mkdir()
        
        # Create some test files
        (test_dir / "file1.tmp").write_text("temp file 1")
        (test_dir / "file2.log").write_text("log file")
        (test_dir / "keep_me.txt").write_text("important file")
        
        pycache_dir = test_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "module.pyc").write_text("compiled")
        
        print(f"Created test files in: {test_dir}")
        print(f"Files before cleanup: {list(test_dir.rglob('*'))}\n")
        
        # Test cleanup
        result = handler.cleanup(test_dir, patterns=['*.tmp', '*.log', '__pycache__'], recursive=True)
        
        print(f"\nCleanup Result:")
        print(f"  Success: {result.success}")
        print(f"  Files removed: {result.files_removed}")
        print(f"  Directories removed: {result.directories_removed}")
        print(f"  Space freed: {result.space_freed_bytes} bytes")
        print(f"  Errors: {result.errors}")
        
        print(f"\nFiles after cleanup: {list(test_dir.rglob('*'))}")


if __name__ == '__main__':
    main()
