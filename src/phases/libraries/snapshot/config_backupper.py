#!/usr/bin/env python3
"""
ConfigBackupper Unit

Backup configuration files
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging
import shutil
import hashlib
import datetime

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    """Result of backup operation."""

    success: bool
    backed_up_files: List[Path] = field(default_factory=list)
    backup_dir: Optional[Path] = None
    total_size: int = 0
    file_count: int = 0
    timestamp: Optional[str] = None
    checksums: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None


class ConfigBackupper:
    """
    Backup configuration files
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ConfigBackupper.

        Args:
            config: Optional configuration dictionary with:
                - backup_root: Root directory for backups
                - include_checksums: Calculate MD5 checksums (default: True)
                - preserve_timestamps: Preserve file timestamps (default: True)
        """
        self.config = config or {}
        self.backup_root = Path(self.config.get("backup_root", "./backups"))
        self.include_checksums = self.config.get("include_checksums", True)
        self.preserve_timestamps = self.config.get("preserve_timestamps", True)

    def backup(
        self, files: List[Path], output_dir: Optional[Path] = None
    ) -> BackupResult:
        """
        Backup configuration files to output directory.

        Args:
            files: List of file paths to backup
            output_dir: Optional custom output directory (default: timestamped dir)

        Returns:
            BackupResult with backup information

        Example:
            backupper = ConfigBackupper()
            files = [Path('config.yml'), Path('docker-compose.yml')]
            result = backupper.backup(files)
            if result.success:
                print(f"Backed up {result.file_count} files")
        """
        try:
            # Create timestamped backup directory if not provided
            if output_dir is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = self.backup_root / f"backup_{timestamp}"

            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Creating backup in: {output_dir}")

            backed_up_files = []
            total_size = 0
            checksums = {}

            # Backup each file
            for file_path in files:
                file_path = Path(file_path)

                if not file_path.exists():
                    logger.warning(f"File not found, skipping: {file_path}")
                    continue

                if not file_path.is_file():
                    logger.warning(f"Not a file, skipping: {file_path}")
                    continue

                # Determine backup file path (preserve directory structure)
                if file_path.is_absolute():
                    # For absolute paths, use just the filename
                    backup_path = output_dir / file_path.name
                else:
                    # For relative paths, preserve structure
                    backup_path = output_dir / file_path

                # Create parent directory if needed
                backup_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(file_path, backup_path)

                # Get file size
                file_size = file_path.stat().st_size
                total_size += file_size

                # Calculate checksum if requested
                if self.include_checksums:
                    checksum = self._calculate_checksum(file_path)
                    checksums[str(file_path)] = checksum

                backed_up_files.append(backup_path)
                logger.debug(
                    f"  Backed up: {file_path} -> {backup_path} ({file_size} bytes)"
                )

            # Get timestamp
            timestamp = datetime.datetime.now().isoformat()

            # Create backup manifest
            manifest_path = output_dir / "backup_manifest.txt"
            self._create_manifest(manifest_path, backed_up_files, checksums, timestamp)

            logger.info(
                f"✅ Backed up {len(backed_up_files)} file(s) ({total_size} bytes)"
            )

            return BackupResult(
                success=True,
                backed_up_files=backed_up_files,
                backup_dir=output_dir,
                total_size=total_size,
                file_count=len(backed_up_files),
                timestamp=timestamp,
                checksums=checksums,
            )

        except Exception as e:
            logger.error(f"Failed to backup files: {e}", exc_info=True)
            return BackupResult(success=False, error=str(e))

    def backup_directory(
        self, source_dir: Path, output_dir: Optional[Path] = None
    ) -> BackupResult:
        """
        Backup entire directory structure.

        Args:
            source_dir: Source directory to backup
            output_dir: Optional custom output directory

        Returns:
            BackupResult with backup information
        """
        try:
            source_dir = Path(source_dir)

            if not source_dir.exists():
                return BackupResult(
                    success=False, error=f"Source directory not found: {source_dir}"
                )

            if not source_dir.is_dir():
                return BackupResult(
                    success=False, error=f"Not a directory: {source_dir}"
                )

            # Create timestamped backup directory if not provided
            if output_dir is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = self.backup_root / f"backup_{timestamp}"

            output_dir = Path(output_dir)

            logger.info(f"Backing up directory: {source_dir} -> {output_dir}")

            # Copy entire directory tree
            shutil.copytree(
                source_dir,
                output_dir,
                dirs_exist_ok=True,
                copy_function=shutil.copy2 if self.preserve_timestamps else shutil.copy,
            )

            # Calculate total size and file count
            total_size = 0
            file_count = 0
            backed_up_files = []

            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
                    backed_up_files.append(file_path)

            timestamp = datetime.datetime.now().isoformat()

            logger.info(
                f"✅ Backed up directory: {file_count} files ({total_size} bytes)"
            )

            return BackupResult(
                success=True,
                backed_up_files=backed_up_files,
                backup_dir=output_dir,
                total_size=total_size,
                file_count=file_count,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(f"Failed to backup directory: {e}", exc_info=True)
            return BackupResult(success=False, error=str(e))

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file."""
        md5_hash = hashlib.md5()

        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)

            return md5_hash.hexdigest()

        except Exception as e:
            logger.warning(f"Failed to calculate checksum for {file_path}: {e}")
            return ""

    def _create_manifest(
        self,
        manifest_path: Path,
        backed_up_files: List[Path],
        checksums: Dict[str, str],
        timestamp: str,
    ):
        """Create backup manifest file."""
        try:
            with open(manifest_path, "w") as f:
                f.write(f"# Backup Manifest\n")
                f.write(f"# Created: {timestamp}\n")
                f.write(f"# Files: {len(backed_up_files)}\n")
                f.write(f"\n")

                for file_path in backed_up_files:
                    f.write(f"{file_path}")

                    # Add checksum if available
                    original_path = str(file_path)
                    if original_path in checksums:
                        f.write(f" [MD5: {checksums[original_path]}]")

                    f.write(f"\n")

            logger.debug(f"Created manifest: {manifest_path}")

        except Exception as e:
            logger.warning(f"Failed to create manifest: {e}")


def main():
    """Test the unit."""
    import tempfile

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("\nTesting ConfigBackupper")
    print("=" * 50)

    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files
        file1 = temp_path / "config.yml"
        file2 = temp_path / "docker-compose.yml"
        file3 = temp_path / "subdir" / "settings.json"

        file3.parent.mkdir(parents=True, exist_ok=True)

        file1.write_text("project_name: test\nenvironment: dev\n")
        file2.write_text("version: '3.8'\nservices:\n  web:\n    image: nginx\n")
        file3.write_text('{"debug": true}\n')

        # Test 1: Backup individual files
        print("\n1. Testing backup of individual files:")
        backupper = ConfigBackupper({"backup_root": temp_path / "backups"})
        result = backupper.backup([file1, file2, file3])

        if result.success:
            print(f"   ✅ Backed up {result.file_count} files")
            print(f"   Backup dir: {result.backup_dir}")
            print(f"   Total size: {result.total_size} bytes")
            print(f"   Checksums: {len(result.checksums)}")

            # Verify files exist
            for backed_up_file in result.backed_up_files:
                if backed_up_file.exists():
                    print(f"   ✅ {backed_up_file.name} backed up successfully")
        else:
            print(f"   ❌ Backup failed: {result.error}")

        # Test 2: Backup entire directory
        print("\n2. Testing backup of entire directory:")
        source_dir = temp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("test1")
        (source_dir / "file2.txt").write_text("test2")

        result = backupper.backup_directory(source_dir)

        if result.success:
            print(f"   ✅ Backed up directory: {result.file_count} files")
            print(f"   Total size: {result.total_size} bytes")
        else:
            print(f"   ❌ Backup failed: {result.error}")

        # Test 3: Backup non-existent file
        print("\n3. Testing backup of non-existent file:")
        result = backupper.backup([temp_path / "nonexistent.txt"])

        if result.success:
            print(f"   ✅ Handled gracefully: {result.file_count} files backed up")
        else:
            print(f"   ❌ Failed: {result.error}")

    print("\n✅ ConfigBackupper tests complete")


if __name__ == "__main__":
    main()
