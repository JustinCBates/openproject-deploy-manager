#!/usr/bin/env python3
"""
EndpointProber Unit

Probe HTTP/HTTPS endpoints to verify service availability
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import urllib.request
import urllib.error
import socket
import ssl
import time
import logging

logger = logging.getLogger(__name__)


class ProbeStatus(Enum):
    """Endpoint probe status"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    SSL_ERROR = "ssl_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ProbeResult:
    """Result of endpoint probe"""
    url: str
    status: ProbeStatus
    success: bool
    http_code: Optional[int]
    response_time_ms: float
    error_message: Optional[str] = None
    ssl_valid: bool = True
    redirect_url: Optional[str] = None


@dataclass
class ProbeReport:
    """Report for multiple endpoint probes"""
    success: bool
    probes: List[ProbeResult]
    total_endpoints: int
    successful_probes: int
    failed_probes: int
    average_response_time_ms: float
    all_endpoints_healthy: bool


class EndpointProber:
    """
    Probe HTTP/HTTPS endpoints to verify service availability
    
    Features:
    - HTTP/HTTPS endpoint testing
    - Response time measurement
    - SSL certificate validation
    - Redirect following
    - Timeout handling
    - Status code validation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize EndpointProber.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.default_timeout = self.config.get('timeout', 10)
        self.follow_redirects = self.config.get('follow_redirects', True)
        self.verify_ssl = self.config.get('verify_ssl', True)

    def probe(self, url: str, timeout: Optional[int] = None, expected_status: int = 200) -> ProbeResult:
        """
        Probe a single endpoint
        
        Args:
            url: URL to probe
            timeout: Timeout in seconds (default: from config or 10)
            expected_status: Expected HTTP status code (default: 200)
            
        Returns:
            ProbeResult with probe details
        """
        timeout_seconds = timeout or self.default_timeout
        start_time = time.time()
        
        try:
            # Prepare request
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'DeployManager-HealthProbe/1.0')
            
            # Create SSL context
            if self.verify_ssl:
                context = ssl.create_default_context()
            else:
                context = ssl._create_unverified_context()
            
            # Make request
            with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:
                response_time = (time.time() - start_time) * 1000  # ms
                http_code = response.getcode()
                final_url = response.geturl()
                
                redirect_url = final_url if final_url != url else None
                
                # Check if status code matches expected
                success = http_code == expected_status
                status = ProbeStatus.SUCCESS if success else ProbeStatus.HTTP_ERROR
                
                logger.info(f"Probed {url}: {http_code} ({response_time:.2f}ms)")
                
                return ProbeResult(
                    url=url,
                    status=status,
                    success=success,
                    http_code=http_code,
                    response_time_ms=response_time,
                    redirect_url=redirect_url,
                    ssl_valid=True
                )
                
        except urllib.error.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"HTTP error probing {url}: {e.code} {e.reason}")
            return ProbeResult(
                url=url,
                status=ProbeStatus.HTTP_ERROR,
                success=False,
                http_code=e.code,
                response_time_ms=response_time,
                error_message=f"{e.code} {e.reason}"
            )
            
        except urllib.error.URLError as e:
            response_time = (time.time() - start_time) * 1000
            if isinstance(e.reason, socket.timeout):
                logger.warning(f"Timeout probing {url} after {timeout_seconds}s")
                return ProbeResult(
                    url=url,
                    status=ProbeStatus.TIMEOUT,
                    success=False,
                    http_code=None,
                    response_time_ms=response_time,
                    error_message=f"Timeout after {timeout_seconds}s"
                )
            else:
                logger.warning(f"Connection error probing {url}: {e.reason}")
                return ProbeResult(
                    url=url,
                    status=ProbeStatus.CONNECTION_ERROR,
                    success=False,
                    http_code=None,
                    response_time_ms=response_time,
                    error_message=str(e.reason)
                )
                
        except ssl.SSLError as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"SSL error probing {url}: {e}")
            return ProbeResult(
                url=url,
                status=ProbeStatus.SSL_ERROR,
                success=False,
                http_code=None,
                response_time_ms=response_time,
                error_message=str(e),
                ssl_valid=False
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error probing {url}: {e}")
            return ProbeResult(
                url=url,
                status=ProbeStatus.UNKNOWN_ERROR,
                success=False,
                http_code=None,
                response_time_ms=response_time,
                error_message=str(e)
            )

    def probe_multiple(self, endpoints: List[Dict[str, Any]]) -> ProbeReport:
        """
        Probe multiple endpoints
        
        Args:
            endpoints: List of endpoint configs with 'url', optional 'timeout', 'expected_status'
            
        Returns:
            ProbeReport with results for all endpoints
        """
        results = []
        
        for endpoint in endpoints:
            url = endpoint['url']
            timeout = endpoint.get('timeout')
            expected_status = endpoint.get('expected_status', 200)
            
            result = self.probe(url, timeout=timeout, expected_status=expected_status)
            results.append(result)
        
        # Calculate stats
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        avg_response_time = sum(r.response_time_ms for r in results) / len(results) if results else 0
        all_healthy = failed == 0
        
        logger.info(f"Probe report: {successful}/{len(results)} endpoints healthy")
        
        return ProbeReport(
            success=True,
            probes=results,
            total_endpoints=len(results),
            successful_probes=successful,
            failed_probes=failed,
            average_response_time_ms=avg_response_time,
            all_endpoints_healthy=all_healthy
        )


def main():
    """Test the unit."""
    logging.basicConfig(level=logging.INFO)
    
    prober = EndpointProber()
    
    # Test with some public endpoints
    print("Testing endpoint prober...")
    
    test_endpoints = [
        {'url': 'https://www.google.com', 'expected_status': 200},
        {'url': 'http://localhost:8080', 'timeout': 2},  # Will fail
    ]
    
    report = prober.probe_multiple(test_endpoints)
    
    print(f"\nProbe Report:")
    print(f"Total endpoints: {report.total_endpoints}")
    print(f"Successful: {report.successful_probes}")
    print(f"Failed: {report.failed_probes}")
    print(f"Average response time: {report.average_response_time_ms:.2f}ms")
    print(f"All healthy: {report.all_endpoints_healthy}")
    
    for probe in report.probes:
        status_icon = "✅" if probe.success else "❌"
        print(f"{status_icon} {probe.url}: {probe.status.value} ({probe.response_time_ms:.2f}ms)")
        if probe.error_message:
            print(f"   Error: {probe.error_message}")


if __name__ == '__main__':
    main()
