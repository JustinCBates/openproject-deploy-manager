#!/usr/bin/env python3
"""
PortChecker Unit

Check port availability
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
import socket

logger = logging.getLogger(__name__)


@dataclass
class PortStatus:
    """Status of port checks"""
    available: List[int]
    in_use: List[int]
    errors: Dict[int, str]
    
    @property
    def all_available(self) -> bool:
        """Check if all ports are available"""
        return len(self.in_use) == 0 and len(self.errors) == 0
    
    def __str__(self):
        if self.all_available:
            return f"✅ All {len(self.available)} ports available"
        return f"❌ {len(self.in_use)} ports in use, {len(self.errors)} errors"


class PortChecker:
    """
    Check port availability
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PortChecker.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.host = config.get('host', '0.0.0.0') if config else '0.0.0.0'

    def is_port_available(self, port: int) -> bool:
        """
        Check if a port is available (not in use).
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is available, False if in use
        """
        try:
            # Try to bind to the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(1)
            
            result = sock.connect_ex((self.host, port))
            sock.close()
            
            if result == 0:
                # Port is in use (connection successful)
                logger.debug(f"Port {port} is in use")
                return False
            else:
                # Port is available (connection failed)
                logger.debug(f"Port {port} is available")
                return True
                
        except socket.error as e:
            logger.warning(f"Error checking port {port}: {e}")
            # Assume unavailable if we can't check
            return False

    def check_ports(self, ports: List[int]) -> PortStatus:
        """
        Check availability of multiple ports.
        
        Args:
            ports: List of port numbers to check
            
        Returns:
            PortStatus with available, in_use, and error details
        """
        logger.info(f"Checking {len(ports)} ports for availability")
        
        available = []
        in_use = []
        errors = {}
        
        for port in ports:
            try:
                if self.is_port_available(port):
                    available.append(port)
                else:
                    in_use.append(port)
                    logger.warning(f"Port {port} is already in use")
            except Exception as e:
                errors[port] = str(e)
                logger.error(f"Error checking port {port}: {e}")
        
        status = PortStatus(
            available=available,
            in_use=in_use,
            errors=errors
        )
        
        if status.all_available:
            logger.info(f"✅ All {len(available)} ports are available")
        else:
            logger.warning(f"⚠️  {len(in_use)} ports in use, {len(errors)} errors")
        
        return status


def main():
    """Test the unit."""
    unit = PortChecker()
    
    print("Testing PortChecker...")
    
    # Test 1: Check common ports
    print("\nTest 1: Check if common ports are available")
    test_ports = [8080, 5432, 6379, 3000]
    
    for port in test_ports:
        available = unit.is_port_available(port)
        status = "✅ available" if available else "❌ in use"
        print(f"  Port {port}: {status}")
    
    # Test 2: Check multiple ports at once
    print("\nTest 2: Check multiple ports")
    status = unit.check_ports(test_ports)
    print(f"  {status}")
    print(f"  Available: {status.available}")
    print(f"  In use: {status.in_use}")
    if status.errors:
        print(f"  Errors: {status.errors}")
    
    # Test 3: Check a definitely available port (high number)
    print("\nTest 3: Check high-number port (likely available)")
    high_port = 54321
    available = unit.is_port_available(high_port)
    print(f"  Port {high_port}: {'✅ available' if available else '❌ in use'}")
    
    print(f"\n{unit.__class__.__name__} tests complete")


if __name__ == '__main__':
    main()
