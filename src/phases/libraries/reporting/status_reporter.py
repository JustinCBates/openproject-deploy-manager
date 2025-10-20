#!/usr/bin/env python3
"""
StatusReporter Unit

Generate comprehensive deployment status reports in multiple formats
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class DeploymentResult:
    """Deployment result summary"""

    success: bool
    project_name: str
    environment: str
    timestamp: str
    duration_seconds: float
    phases_completed: List[str]
    phases_failed: List[str]
    services_deployed: int
    services_healthy: int
    snapshot_created: Optional[str]
    errors: List[str]
    warnings: List[str]


class StatusReporter:
    """
    Generate deployment status reports

    Features:
    - JSON format reports
    - Human-readable text reports
    - Summary statistics
    - Health status overview
    - Error and warning aggregation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize StatusReporter.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def generate_report(
        self, context: Dict[str, Any], output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Generate deployment status report from context

        Args:
            context: Full deployment context from all phases
            output_path: Optional path to save report

        Returns:
            Dict with report data
        """
        try:
            # Extract key information from context
            config = context.get("validated_config", context.get("config", {}))

            # Determine success/failure
            all_phases = [
                context.get("phase_1_result", {}),
                context.get("phase_2_result", {}),
                context.get("phase_3_result", {}),
                context.get("phase_4_result", {}),
                context.get("phase_5_result", {}),
                context.get("phase_6_result", {}),
            ]

            phases_completed = [
                p.get("phase_id") for p in all_phases if p.get("status") == "success"
            ]
            phases_failed = [
                p.get("phase_id")
                for p in all_phases
                if p.get("status") in ["error", "failed"]
            ]

            success = len(phases_failed) == 0

            # Collect health status
            health_data = context.get("phase_5_result", {}).get("health_checks", {})
            containers_data = health_data.get("containers", {})

            services_deployed = containers_data.get("total", 0)
            services_healthy = containers_data.get("healthy", 0)

            # Collect errors and warnings
            errors = []
            warnings = []
            for phase in all_phases:
                if "error" in phase:
                    errors.append(f"{phase.get('phase_id')}: {phase['error']}")
                if "warnings" in phase:
                    warnings.extend(phase["warnings"])

            # Build report
            report = {
                "deployment_status": {
                    "success": success,
                    "project_name": config.get("project_name", "unknown"),
                    "environment": config.get("environment", "development"),
                    "timestamp": datetime.now().isoformat(),
                    "duration_seconds": context.get("total_duration", 0),
                },
                "phases": {
                    "completed": phases_completed,
                    "failed": phases_failed,
                    "total": len([p for p in all_phases if p]),
                },
                "services": {
                    "deployed": services_deployed,
                    "healthy": services_healthy,
                    "unhealthy": services_deployed - services_healthy,
                },
                "snapshot": {
                    "created": context.get("snapshot_id"),
                    "path": context.get("snapshot_path"),
                },
                "health_checks": health_data,
                "errors": errors,
                "warnings": warnings,
                "artifacts": {
                    "env_file": context.get("env_file"),
                    "caddyfile": context.get("rendered_caddyfile"),
                    "compose_override": context.get("rendered_compose_override"),
                    "health_report": context.get("health_report"),
                },
            }

            # Save to file if path provided
            if output_path:
                with open(output_path, "w") as f:
                    json.dump(report, f, indent=2)
                logger.info(f"Report saved to: {output_path}")

            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {"deployment_status": {"success": False, "error": str(e)}}

    def generate_text_report(self, context: Dict[str, Any]) -> str:
        """
        Generate human-readable text report

        Args:
            context: Full deployment context

        Returns:
            Formatted text report
        """
        report = self.generate_report(context)

        status = report["deployment_status"]
        phases = report["phases"]
        services = report["services"]

        status_icon = "✅" if status["success"] else "❌"

        lines = [
            "=" * 70,
            "DEPLOYMENT STATUS REPORT",
            "=" * 70,
            "",
            f"{status_icon} Status: {'SUCCESS' if status['success'] else 'FAILED'}",
            f"Project: {status['project_name']}",
            f"Environment: {status['environment']}",
            f"Timestamp: {status['timestamp']}",
            f"Duration: {status.get('duration_seconds', 0):.2f}s",
            "",
            "PHASES:",
            f"  Completed: {len(phases['completed'])}/{phases['total']}",
        ]

        if phases["completed"]:
            for phase in phases["completed"]:
                lines.append(f"    ✅ {phase}")

        if phases["failed"]:
            lines.append("  Failed:")
            for phase in phases["failed"]:
                lines.append(f"    ❌ {phase}")

        lines.extend(
            [
                "",
                "SERVICES:",
                f"  Deployed: {services['deployed']}",
                f"  Healthy: {services['healthy']}",
                f"  Unhealthy: {services['unhealthy']}",
            ]
        )

        if report.get("snapshot", {}).get("created"):
            lines.extend(
                [
                    "",
                    "SNAPSHOT:",
                    f"  ID: {report['snapshot']['created']}",
                    f"  Path: {report['snapshot'].get('path', 'N/A')}",
                ]
            )

        if report["errors"]:
            lines.extend(
                [
                    "",
                    "ERRORS:",
                ]
            )
            for error in report["errors"]:
                lines.append(f"  ❌ {error}")

        if report["warnings"]:
            lines.extend(
                [
                    "",
                    "WARNINGS:",
                ]
            )
            for warning in report["warnings"]:
                lines.append(f"  ⚠️  {warning}")

        lines.extend(
            [
                "",
                "=" * 70,
            ]
        )

        return "\n".join(lines)

    def print_summary(self, context: Dict[str, Any]) -> None:
        """
        Print deployment summary to console

        Args:
            context: Full deployment context
        """
        text_report = self.generate_text_report(context)
        print(text_report)


def main():
    """Test the unit."""
    logging.basicConfig(level=logging.INFO)

    reporter = StatusReporter()

    # Test with sample context
    test_context = {
        "validated_config": {"project_name": "test-app", "environment": "production"},
        "phase_1_result": {"phase_id": "phase_1_preflight", "status": "success"},
        "phase_2_result": {
            "phase_id": "phase_2_template_rendering",
            "status": "success",
        },
        "phase_3_result": {"phase_id": "phase_3_snapshot", "status": "success"},
        "phase_4_result": {"phase_id": "phase_4_deployment", "status": "success"},
        "phase_5_result": {
            "phase_id": "phase_5_health_verification",
            "status": "success",
            "health_checks": {"containers": {"total": 3, "healthy": 3, "unhealthy": 0}},
        },
        "snapshot_id": "snap_test-app_20251015",
        "total_duration": 45.5,
    }

    print("Generating deployment report...\n")

    # Generate JSON report
    report = reporter.generate_report(test_context)
    print("JSON Report generated:")
    print(json.dumps(report, indent=2))

    print("\n" + "=" * 70 + "\n")

    # Generate text report
    reporter.print_summary(test_context)


if __name__ == "__main__":
    main()
