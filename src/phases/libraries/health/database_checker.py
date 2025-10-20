#!/usr/bin/env python3
"""
DatabaseChecker Unit

Check database connectivity using TCP port testing
(Avoids dependency on database-specific Python clients)
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import socket
import time
import logging

logger = logging.getLogger(__name__)


class DbStatus(Enum):
    """Database connection status"""

    CONNECTED = "connected"
    REFUSED = "refused"
    TIMEOUT = "timeout"
    HOST_UNREACHABLE = "unreachable"
    UNKNOWN_ERROR = "unknown"


@dataclass
class DbCheckResult:
    """Result of database check"""

    host: str
    port: int
    db_type: str
    status: DbStatus
    success: bool
    response_time_ms: float
    error_message: Optional[str] = None


class DatabaseChecker:
    """
    Check database connectivity using TCP socket connections

    Supports:
    - PostgreSQL (default port 5432)
    - MySQL/MariaDB (default port 3306)
    - MongoDB (default port 27017)
    - Redis (default port 6379)

    Note: This uses TCP port checking, not full database authentication.
    For production, consider using database-specific clients.
    """

    DEFAULT_PORTS = {
        "postgres": 5432,
        "postgresql": 5432,
        "mysql": 3306,
        "mariadb": 3306,
        "mongodb": 27017,
        "mongo": 27017,
        "redis": 6379,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize DatabaseChecker.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.default_timeout = self.config.get("timeout", 5)

    def check(
        self,
        host: str,
        port: Optional[int] = None,
        db_type: str = "postgres",
        timeout: Optional[int] = None,
    ) -> DbCheckResult:
        """
        Check database connectivity

        Args:
            host: Database host
            port: Database port (if None, use default for db_type)
            db_type: Database type ('postgres', 'mysql', 'mongodb', 'redis')
            timeout: Connection timeout in seconds

        Returns:
            DbCheckResult with connection status
        """
        # Determine port
        if port is None:
            port = self.DEFAULT_PORTS.get(db_type.lower(), 5432)

        timeout_seconds = timeout or self.default_timeout
        start_time = time.time()

        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_seconds)

            # Attempt connection
            result = sock.connect_ex((host, port))
            response_time = (time.time() - start_time) * 1000  # ms

            sock.close()

            if result == 0:
                logger.info(
                    f"Database reachable: {db_type} at {host}:{port} ({response_time:.2f}ms)"
                )
                return DbCheckResult(
                    host=host,
                    port=port,
                    db_type=db_type,
                    status=DbStatus.CONNECTED,
                    success=True,
                    response_time_ms=response_time,
                )
            else:
                logger.warning(f"Database connection refused: {host}:{port}")
                return DbCheckResult(
                    host=host,
                    port=port,
                    db_type=db_type,
                    status=DbStatus.REFUSED,
                    success=False,
                    response_time_ms=response_time,
                    error_message=f"Connection refused (error code: {result})",
                )

        except socket.timeout:
            response_time = (time.time() - start_time) * 1000
            logger.warning(
                f"Database connection timeout: {host}:{port} after {timeout_seconds}s"
            )
            return DbCheckResult(
                host=host,
                port=port,
                db_type=db_type,
                status=DbStatus.TIMEOUT,
                success=False,
                response_time_ms=response_time,
                error_message=f"Timeout after {timeout_seconds}s",
            )

        except socket.gaierror as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"Database host unreachable: {host}:{port} - {e}")
            return DbCheckResult(
                host=host,
                port=port,
                db_type=db_type,
                status=DbStatus.HOST_UNREACHABLE,
                success=False,
                response_time_ms=response_time,
                error_message=f"Host unreachable: {e}",
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error checking database {host}:{port} - {e}")
            return DbCheckResult(
                host=host,
                port=port,
                db_type=db_type,
                status=DbStatus.UNKNOWN_ERROR,
                success=False,
                response_time_ms=response_time,
                error_message=str(e),
            )

    def check_postgres(
        self, host: str, port: int = 5432, timeout: Optional[int] = None
    ) -> DbCheckResult:
        """
        Check PostgreSQL connectivity

        Args:
            host: PostgreSQL host
            port: PostgreSQL port (default: 5432)
            timeout: Connection timeout in seconds

        Returns:
            DbCheckResult with connection status
        """
        return self.check(host, port, "postgres", timeout)

    def check_mysql(
        self, host: str, port: int = 3306, timeout: Optional[int] = None
    ) -> DbCheckResult:
        """
        Check MySQL/MariaDB connectivity

        Args:
            host: MySQL host
            port: MySQL port (default: 3306)
            timeout: Connection timeout in seconds

        Returns:
            DbCheckResult with connection status
        """
        return self.check(host, port, "mysql", timeout)

    def check_mongodb(
        self, host: str, port: int = 27017, timeout: Optional[int] = None
    ) -> DbCheckResult:
        """
        Check MongoDB connectivity

        Args:
            host: MongoDB host
            port: MongoDB port (default: 27017)
            timeout: Connection timeout in seconds

        Returns:
            DbCheckResult with connection status
        """
        return self.check(host, port, "mongodb", timeout)


def main():
    """Test the unit."""
    logging.basicConfig(level=logging.INFO)

    checker = DatabaseChecker()

    # Test with localhost (will likely fail since no DB running)
    print("Testing database checker...")

    tests = [
        ("localhost", 5432, "postgres"),
        ("localhost", 3306, "mysql"),
        ("8.8.8.8", 5432, "postgres"),  # Google DNS - will timeout
    ]

    for host, port, db_type in tests:
        result = checker.check(host, port, db_type, timeout=2)
        status_icon = "✅" if result.success else "❌"
        print(
            f"{status_icon} {db_type}@{host}:{port}: {result.status.value} ({result.response_time_ms:.2f}ms)"
        )
        if result.error_message:
            print(f"   Error: {result.error_message}")


if __name__ == "__main__":
    main()
