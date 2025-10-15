#!/usr/bin/env python3
"""
ResourceChecker Unit

Check system resources
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
import psutil

logger = logging.getLogger(__name__)


@dataclass
class MemoryStatus:
    """Memory status information"""
    total_gb: float
    available_gb: float
    used_gb: float
    percent_used: float
    sufficient: bool
    
    def __str__(self):
        status = "✅" if self.sufficient else "⚠️"
        return f"{status} Memory: {self.used_gb:.1f}GB/{self.total_gb:.1f}GB ({self.percent_used:.1f}% used)"


@dataclass
class DiskStatus:
    """Disk status information"""
    total_gb: float
    available_gb: float
    used_gb: float
    percent_used: float
    sufficient: bool
    path: str = "/"
    
    def __str__(self):
        status = "✅" if self.sufficient else "⚠️"
        return f"{status} Disk ({self.path}): {self.used_gb:.1f}GB/{self.total_gb:.1f}GB ({self.percent_used:.1f}% used)"


@dataclass
class CpuStatus:
    """CPU status information"""
    cores: int
    percent_used: float
    load_average: tuple
    sufficient: bool
    
    def __str__(self):
        status = "✅" if self.sufficient else "⚠️"
        return f"{status} CPU: {self.cores} cores, {self.percent_used:.1f}% used, load: {self.load_average}"


class ResourceChecker:
    """
    Check system resources
    """
    
    # Resource thresholds
    MEMORY_THRESHOLD_PERCENT = 90  # Warn if >90% used
    DISK_THRESHOLD_PERCENT = 85    # Warn if >85% used
    CPU_THRESHOLD_PERCENT = 80     # Warn if >80% used
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ResourceChecker.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Allow custom thresholds
        if config:
            self.memory_threshold = config.get('memory_threshold', self.MEMORY_THRESHOLD_PERCENT)
            self.disk_threshold = config.get('disk_threshold', self.DISK_THRESHOLD_PERCENT)
            self.cpu_threshold = config.get('cpu_threshold', self.CPU_THRESHOLD_PERCENT)
        else:
            self.memory_threshold = self.MEMORY_THRESHOLD_PERCENT
            self.disk_threshold = self.DISK_THRESHOLD_PERCENT
            self.cpu_threshold = self.CPU_THRESHOLD_PERCENT

    def check_memory(self) -> MemoryStatus:
        """
        Check memory availability.
        
        Returns:
            MemoryStatus with memory information
        """
        logger.debug("Checking memory status")
        
        mem = psutil.virtual_memory()
        
        total_gb = mem.total / (1024**3)
        available_gb = mem.available / (1024**3)
        used_gb = mem.used / (1024**3)
        percent_used = mem.percent
        
        sufficient = percent_used < self.memory_threshold
        
        status = MemoryStatus(
            total_gb=total_gb,
            available_gb=available_gb,
            used_gb=used_gb,
            percent_used=percent_used,
            sufficient=sufficient
        )
        
        if sufficient:
            logger.info(f"✅ Memory check passed: {available_gb:.1f}GB available")
        else:
            logger.warning(f"⚠️  Memory usage high: {percent_used:.1f}% used")
        
        return status

    def check_disk(self, path: str = "/") -> DiskStatus:
        """
        Check disk space availability.
        
        Args:
            path: Path to check disk space for (default: root)
            
        Returns:
            DiskStatus with disk information
        """
        logger.debug(f"Checking disk status for: {path}")
        
        disk = psutil.disk_usage(path)
        
        total_gb = disk.total / (1024**3)
        available_gb = disk.free / (1024**3)
        used_gb = disk.used / (1024**3)
        percent_used = disk.percent
        
        sufficient = percent_used < self.disk_threshold
        
        status = DiskStatus(
            total_gb=total_gb,
            available_gb=available_gb,
            used_gb=used_gb,
            percent_used=percent_used,
            sufficient=sufficient,
            path=path
        )
        
        if sufficient:
            logger.info(f"✅ Disk check passed: {available_gb:.1f}GB available")
        else:
            logger.warning(f"⚠️  Disk usage high: {percent_used:.1f}% used")
        
        return status

    def check_cpu(self) -> CpuStatus:
        """
        Check CPU availability.
        
        Returns:
            CpuStatus with CPU information
        """
        logger.debug("Checking CPU status")
        
        cores = psutil.cpu_count()
        percent_used = psutil.cpu_percent(interval=1)
        load_average = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
        
        sufficient = percent_used < self.cpu_threshold
        
        status = CpuStatus(
            cores=cores,
            percent_used=percent_used,
            load_average=load_average,
            sufficient=sufficient
        )
        
        if sufficient:
            logger.info(f"✅ CPU check passed: {percent_used:.1f}% used")
        else:
            logger.warning(f"⚠️  CPU usage high: {percent_used:.1f}% used")
        
        return status


def main():
    """Test the unit."""
    unit = ResourceChecker()
    
    print("Testing ResourceChecker...")
    
    # Test 1: Check memory
    print("\nTest 1: Check memory")
    mem_status = unit.check_memory()
    print(f"  {mem_status}")
    print(f"  Total: {mem_status.total_gb:.1f} GB")
    print(f"  Available: {mem_status.available_gb:.1f} GB")
    print(f"  Used: {mem_status.used_gb:.1f} GB ({mem_status.percent_used:.1f}%)")
    
    # Test 2: Check disk
    print("\nTest 2: Check disk space")
    disk_status = unit.check_disk("/")
    print(f"  {disk_status}")
    print(f"  Total: {disk_status.total_gb:.1f} GB")
    print(f"  Available: {disk_status.available_gb:.1f} GB")
    print(f"  Used: {disk_status.used_gb:.1f} GB ({disk_status.percent_used:.1f}%)")
    
    # Test 3: Check CPU
    print("\nTest 3: Check CPU")
    cpu_status = unit.check_cpu()
    print(f"  {cpu_status}")
    print(f"  Cores: {cpu_status.cores}")
    print(f"  Usage: {cpu_status.percent_used:.1f}%")
    print(f"  Load average: {cpu_status.load_average}")
    
    # Summary
    print("\nSummary:")
    all_sufficient = mem_status.sufficient and disk_status.sufficient and cpu_status.sufficient
    if all_sufficient:
        print("  ✅ All system resources are sufficient")
    else:
        print("  ⚠️  Some system resources are constrained")
    
    print(f"\n{unit.__class__.__name__} tests complete")


if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()
