#!/usr/bin/env python3
"""
Health Verification
Sequence: 50
Status: IMPLEMENTED

Verify deployment health and service availability
"""

from pathlib import Path
from typing import Dict, Any
import logging
import json

from phases.libraries.health.container_health_checker import (
    ContainerHealthChecker,
    HealthCheckResult,
)
from phases.libraries.health.endpoint_prober import EndpointProber, ProbeReport
from phases.libraries.health.database_checker import DatabaseChecker, DbCheckResult
from phases.libraries.health.connectivity_tester import (
    ConnectivityTester,
    ConnectivityTest,
    ConnectivityReport,
)

logger = logging.getLogger(__name__)


class Phase5HealthVerificationOrchestrator:
    """
    Health Verification

    Status: IMPLEMENTED
    Sequence: 50

    Verify deployment health and service availability

    Steps:
    1. Check Container Health - Verify all containers are healthy via Docker health checks
    2. Probe HTTP/HTTPS Endpoints - Test HTTP/HTTPS endpoints are responding
    3. Check Database Connectivity - Verify database is accessible and responding
    4. Test Service Connectivity - Test inter-service connectivity and networking
    """

    PHASE_ID = "phase_5_health_verification"
    PHASE_SEQUENCE = 50
    PHASE_NAME = "Health Verification"

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        """
        Initialize Health Verification.

        Args:
            project_root: Root directory of the project
            config: Configuration dictionary
        """
        self.project_root = project_root
        self.config = config
        self.phase_dir = project_root / "runtime" / "phase_5_health_verification"
        self.outputs_dir = self.phase_dir / "outputs"

        # Ensure outputs directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Health Verification.

        Args:
            context: Execution context from previous phases

        Returns:
            Dict with phase results and artifacts
        """
        logger.info("=" * 70)
        logger.info(f"{self.PHASE_NAME}")
        logger.info("=" * 70)

        result = {
            "phase_id": self.PHASE_ID,
            "status": "success",
            "artifacts": {},
            "messages": [],
            "health_checks": {},
        }

        try:
            # Step 10: Check Container Health
            step_result = self._step_10_check_container_health(context)
            result["artifacts"].update(step_result.get("artifacts", {}))
            result["health_checks"]["containers"] = step_result.get("summary", {})

            # Step 20: Probe HTTP/HTTPS Endpoints
            step_result = self._step_20_probe_http_https_endpoints(context)
            result["artifacts"].update(step_result.get("artifacts", {}))
            result["health_checks"]["endpoints"] = step_result.get("summary", {})

            # Step 30: Check Database Connectivity
            step_result = self._step_30_check_database_connectivity(context)
            result["artifacts"].update(step_result.get("artifacts", {}))
            result["health_checks"]["database"] = step_result.get("summary", {})

            # Step 40: Test Service Connectivity
            step_result = self._step_40_test_service_connectivity(context)
            result["artifacts"].update(step_result.get("artifacts", {}))
            result["health_checks"]["connectivity"] = step_result.get("summary", {})

            # Overall health status
            all_checks_passed = all(
                check.get("all_healthy", True)
                for check in result["health_checks"].values()
            )

            result["all_healthy"] = all_checks_passed
            result["status"] = "success" if all_checks_passed else "degraded"

            # Save health report
            health_report_path = self.outputs_dir / "health_report.json"
            with open(health_report_path, "w") as f:
                json.dump(result["health_checks"], f, indent=2)

            result["artifacts"]["health_report"] = str(health_report_path)

            logger.info(f"✅ {self.PHASE_NAME} complete (status: {result['status']})")

        except Exception as e:
            logger.error(f"Health verification failed: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def _step_10_check_container_health(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 10: Check Container Health

        Verify all containers are healthy via Docker health checks
        """
        logger.info(f"  Step 10: Check Container Health")

        try:
            # Get project name from context
            project_name = context.get("validated_config", {}).get(
                "project_name", context.get("config", {}).get("project_name")
            )

            if not project_name:
                logger.warning("No project name in context, checking all containers")

            # Initialize checker
            checker = ContainerHealthChecker(self.config)

            # Check container health
            result = checker.check(project_name=project_name)

            # Log results
            logger.info(
                f"    Container health: {result.healthy_count}/{result.total_count} healthy"
            )
            for container in result.containers:
                status_icon = "✅" if container.is_healthy() else "❌"
                logger.info(
                    f"    {status_icon} {container.container_name}: {container.status.value}"
                )
                if not container.is_healthy():
                    logger.warning(
                        f"       Unhealthy: {container.last_health_output or 'No health output'}"
                    )

            # Return summary
            return {
                "status": "success",
                "artifacts": {
                    "containers_checked": result.total_count,
                    "containers_healthy": result.healthy_count,
                    "containers_unhealthy": result.unhealthy_count,
                },
                "summary": {
                    "total": result.total_count,
                    "healthy": result.healthy_count,
                    "unhealthy": result.unhealthy_count,
                    "all_healthy": result.all_healthy,
                },
            }

        except Exception as e:
            logger.error(f"Container health check failed: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "summary": {"error": str(e), "all_healthy": False},
            }

    def _step_20_probe_http_https_endpoints(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 20: Probe HTTP/HTTPS Endpoints

        Test HTTP/HTTPS endpoints are responding
        """
        logger.info(f"  Step 20: Probe HTTP/HTTPS Endpoints")

        try:
            # Get endpoints from config
            config = context.get("validated_config", context.get("config", {}))
            endpoints = config.get("health_check_endpoints", [])

            if not endpoints:
                # Build default endpoints from config
                domain = config.get("domain", "localhost")
                port = config.get("port", "80")
                protocol = "https" if config.get("https_enabled", False) else "http"

                endpoints = [
                    {"url": f"{protocol}://{domain}:{port}", "expected_status": 200}
                ]

            # Initialize prober
            prober = EndpointProber(self.config)

            # Probe endpoints
            report = prober.probe_multiple(endpoints)

            # Log results
            logger.info(
                f"    Endpoint health: {report.successful_probes}/{report.total_endpoints} responding"
            )
            for probe in report.probes:
                status_icon = "✅" if probe.success else "❌"
                logger.info(
                    f"    {status_icon} {probe.url}: {probe.status.value} "
                    f"(HTTP {probe.http_code}, {probe.response_time_ms:.2f}ms)"
                )

            return {
                "status": "success",
                "artifacts": {
                    "endpoints_checked": report.total_endpoints,
                    "endpoints_healthy": report.successful_probes,
                    "average_response_time_ms": report.average_response_time_ms,
                },
                "summary": {
                    "total": report.total_endpoints,
                    "successful": report.successful_probes,
                    "failed": report.failed_probes,
                    "all_healthy": report.all_endpoints_healthy,
                },
            }

        except Exception as e:
            logger.error(f"Endpoint probing failed: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "summary": {"error": str(e), "all_healthy": False},
            }

    def _step_30_check_database_connectivity(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 30: Check Database Connectivity

        Verify database is accessible and responding
        """
        logger.info(f"  Step 30: Check Database Connectivity")

        try:
            # Get database config from context
            config = context.get("validated_config", context.get("config", {}))
            db_config = config.get("database", {})

            if not db_config:
                logger.info("    No database configuration found, skipping")
                return {
                    "status": "skipped",
                    "artifacts": {},
                    "summary": {"all_healthy": True},  # No DB = no problem
                }

            # Initialize checker
            checker = DatabaseChecker(self.config)

            # Check database
            db_type = db_config.get("type", "postgres")
            db_host = db_config.get("host", "localhost")
            db_port = db_config.get("port")

            result = checker.check(db_host, db_port, db_type)

            # Log result
            status_icon = "✅" if result.success else "❌"
            logger.info(
                f"    {status_icon} {db_type}@{db_host}:{db_port}: {result.status.value} "
                f"({result.response_time_ms:.2f}ms)"
            )

            return {
                "status": "success",
                "artifacts": {
                    "database_type": db_type,
                    "database_host": db_host,
                    "database_port": db_port,
                    "database_reachable": result.success,
                    "response_time_ms": result.response_time_ms,
                },
                "summary": {"reachable": result.success, "all_healthy": result.success},
            }

        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "summary": {"error": str(e), "all_healthy": False},
            }

    def _step_40_test_service_connectivity(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Step 40: Test Service Connectivity

        Test inter-service connectivity and networking
        """
        logger.info(f"  Step 40: Test Service Connectivity")

        try:
            # Get connectivity tests from config
            config = context.get("validated_config", context.get("config", {}))
            connectivity_config = config.get("connectivity_tests", {})

            if not connectivity_config:
                logger.info("    No connectivity tests configured, skipping")
                return {
                    "status": "skipped",
                    "artifacts": {},
                    "summary": {"all_healthy": True},  # No tests = no problem
                }

            # Initialize tester
            tester = ConnectivityTester(self.config)

            # Run connectivity tests
            report = tester.test_from_config(connectivity_config)

            # Log results
            logger.info(
                f"    Connectivity: {report.successful_tests}/{report.total_tests} connections successful"
            )
            for test_result in report.tests:
                status_icon = "✅" if test_result.success else "❌"
                logger.info(
                    f"    {status_icon} {test_result.test.source} → "
                    f"{test_result.test.target_host}:{test_result.test.target_port}: "
                    f"{test_result.status.value}"
                )

            return {
                "status": "success",
                "artifacts": {
                    "tests_run": report.total_tests,
                    "tests_passed": report.successful_tests,
                    "tests_failed": report.failed_tests,
                },
                "summary": {
                    "total": report.total_tests,
                    "successful": report.successful_tests,
                    "failed": report.failed_tests,
                    "all_healthy": report.all_connections_healthy,
                },
            }

        except Exception as e:
            logger.error(f"Connectivity testing failed: {e}")
            return {
                "status": "error",
                "artifacts": {},
                "summary": {"error": str(e), "all_healthy": False},
            }


def main():
    """Test the phase orchestrator."""
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    project_root = Path(__file__).parent.parent.parent

    # Test config
    config = {
        "project_name": "test-deployment",
        "domain": "localhost",
        "port": "8080",
        "https_enabled": False,
    }

    # Test context (simulate Phase 4 output)
    context = {"validated_config": config, "config": config}

    orchestrator = Phase5HealthVerificationOrchestrator(project_root, config)
    result = orchestrator.execute(context)

    logger.info("\n" + "=" * 70)
    logger.info("PHASE 5 TEST RESULT")
    logger.info("=" * 70)
    logger.info(f"Status: {result['status']}")
    logger.info(f"All Healthy: {result.get('all_healthy', 'N/A')}")
    logger.info(f"\nArtifacts: {len(result['artifacts'])}")
    for key, value in result["artifacts"].items():
        logger.info(f"  {key}: {value}")


if __name__ == "__main__":
    main()
