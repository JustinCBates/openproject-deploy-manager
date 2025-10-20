#!/usr/bin/env python3
"""
ConnectivityTester Unit

Test network connectivity between services using TCP/UDP port checking
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import socket
import time
import logging

logger = logging.getLogger(__name__)


class ConnectivityStatus(Enum):
    """Network connectivity status"""

    CONNECTED = "connected"
    REFUSED = "refused"
    TIMEOUT = "timeout"
    UNREACHABLE = "unreachable"
    UNKNOWN_ERROR = "unknown"


@dataclass
class ConnectivityTest:
    """Single connectivity test configuration"""

    source: str  # Description of source (e.g., "web-service")
    target_host: str
    target_port: int
    protocol: str = "tcp"  # 'tcp' or 'udp'
    timeout: int = 5


@dataclass
class ConnectivityTestResult:
    """Result of a single connectivity test"""

    test: ConnectivityTest
    status: ConnectivityStatus
    success: bool
    response_time_ms: float
    error_message: Optional[str] = None


@dataclass
class ConnectivityReport:
    """Report for multiple connectivity tests"""

    success: bool
    tests: List[ConnectivityTestResult]
    total_tests: int
    successful_tests: int
    failed_tests: int
    all_connections_healthy: bool


class ConnectivityTester:
    """
    Test network connectivity between services

    Features:
    - TCP port connectivity testing
    - UDP port testing (basic)
    - Response time measurement
    - Batch testing support
    - Inter-service connectivity verification
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ConnectivityTester.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.default_timeout = self.config.get("timeout", 5)

    def test_connection(
        self, host: str, port: int, protocol: str = "tcp", timeout: Optional[int] = None
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Test a single network connection

        Args:
            host: Target host
            port: Target port
            protocol: 'tcp' or 'udp'
            timeout: Connection timeout in seconds

        Returns:
            Tuple of (success, response_time_ms, error_message)
        """
        timeout_seconds = timeout or self.default_timeout
        start_time = time.time()

        try:
            if protocol.lower() == "tcp":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            elif protocol.lower() == "udp":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            else:
                return False, 0, f"Unsupported protocol: {protocol}"

            sock.settimeout(timeout_seconds)

            # Attempt connection
            if protocol.lower() == "tcp":
                result = sock.connect_ex((host, port))
                response_time = (time.time() - start_time) * 1000

                if result == 0:
                    sock.close()
                    return True, response_time, None
                else:
                    sock.close()
                    return (
                        False,
                        response_time,
                        f"Connection refused (error code: {result})",
                    )
            else:
                # UDP is connectionless, so we just send a packet and see if we get a response
                sock.sendto(b"", (host, port))
                try:
                    sock.recvfrom(1024)
                    response_time = (time.time() - start_time) * 1000
                    sock.close()
                    return True, response_time, None
                except socket.timeout:
                    response_time = (time.time() - start_time) * 1000
                    sock.close()
                    # For UDP, timeout doesn't necessarily mean failure
                    return (
                        True,
                        response_time,
                        "UDP (no response, but sent successfully)",
                    )

        except socket.timeout:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"Timeout after {timeout_seconds}s"

        except socket.gaierror as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, f"Host unreachable: {e}"

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return False, response_time, str(e)

        finally:
            try:
                sock.close()
            except Exception:
                # Ignore close errors, socket may already be closed
                pass

    def test(self, tests: List[ConnectivityTest]) -> ConnectivityReport:
        """
        Run multiple connectivity tests

        Args:
            tests: List of ConnectivityTest configurations

        Returns:
            ConnectivityReport with results for all tests
        """
        results = []

        for test in tests:
            success, response_time, error_msg = self.test_connection(
                test.target_host, test.target_port, test.protocol, test.timeout
            )

            # Determine status
            if success:
                status = ConnectivityStatus.CONNECTED
            elif error_msg and "timeout" in error_msg.lower():
                status = ConnectivityStatus.TIMEOUT
            elif error_msg and "unreachable" in error_msg.lower():
                status = ConnectivityStatus.UNREACHABLE
            elif error_msg and "refused" in error_msg.lower():
                status = ConnectivityStatus.REFUSED
            else:
                status = ConnectivityStatus.UNKNOWN_ERROR

            result = ConnectivityTestResult(
                test=test,
                status=status,
                success=success,
                response_time_ms=response_time,
                error_message=error_msg,
            )
            results.append(result)

            # Log result
            status_icon = "✅" if success else "❌"
            logger.info(
                f"{status_icon} {test.source} → {test.target_host}:{test.target_port} "
                f"({status.value}, {response_time:.2f}ms)"
            )

        # Calculate stats
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        all_healthy = failed == 0

        logger.info(
            f"Connectivity test complete: {successful}/{len(results)} connections successful"
        )

        return ConnectivityReport(
            success=True,
            tests=results,
            total_tests=len(results),
            successful_tests=successful,
            failed_tests=failed,
            all_connections_healthy=all_healthy,
        )

    def test_from_config(self, service_config: Dict[str, Any]) -> ConnectivityReport:
        """
        Create and run connectivity tests from service configuration

        Args:
            service_config: Dictionary with service connectivity requirements

        Returns:
            ConnectivityReport with results
        """
        tests = []

        # Parse service_config to create ConnectivityTest objects
        for service_name, config in service_config.items():
            for dependency in config.get("dependencies", []):
                test = ConnectivityTest(
                    source=service_name,
                    target_host=dependency.get("host", "localhost"),
                    target_port=dependency["port"],
                    protocol=dependency.get("protocol", "tcp"),
                    timeout=dependency.get("timeout", self.default_timeout),
                )
                tests.append(test)

        return self.test(tests)


def main():
    """Test the unit."""
    logging.basicConfig(level=logging.INFO)

    tester = ConnectivityTester()

    # Test with some common services
    logger.info("Testing connectivity...")

    tests = [
        ConnectivityTest(
            source="web-app",
            target_host="localhost",
            target_port=80,
            protocol="tcp",
            timeout=2,
        ),
        ConnectivityTest(
            source="web-app",
            target_host="8.8.8.8",
            target_port=53,
            protocol="tcp",
            timeout=2,
        ),
        ConnectivityTest(
            source="api",
            target_host="localhost",
            target_port=5432,
            protocol="tcp",
            timeout=2,
        ),
    ]

    report = tester.test(tests)

    logger.info(f"\nConnectivity Report:")
    logger.info(f"Total tests: {report.total_tests}")
    logger.info(f"Successful: {report.successful_tests}")
    logger.info(f"Failed: {report.failed_tests}")
    logger.info(f"All healthy: {report.all_connections_healthy}")

    for result in report.tests:
        status_icon = "✅" if result.success else "❌"
        logger.info(
            f"{status_icon} {result.test.source} → {result.test.target_host}:{result.test.target_port}: "
            f"{result.status.value} ({result.response_time_ms:.2f}ms)"
        )
        if result.error_message:
            logger.info(f"   Error: {result.error_message}")


if __name__ == "__main__":
    main()
