"""Report generation for cost and optimization analysis."""

import json
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from cloud_finops.analyzers.cost_analyzer import CostAnalysis
from cloud_finops.analyzers.resource_analyzer import ResourceAnalysis
from cloud_finops.analyzers.optimizer import OptimizationRecommendation
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)


class Reporter:
    """Generates reports in various formats."""

    def __init__(self):
        """Initialize reporter."""
        pass

    def generate_text_report(self, cost_analysis: CostAnalysis,
                            resource_analysis: ResourceAnalysis,
                            recommendations: List[OptimizationRecommendation],
                            provider: str = "Unknown") -> str:
        """
        Generate a text report.

        Args:
            cost_analysis: Cost analysis results
            resource_analysis: Resource analysis results
            recommendations: List of optimization recommendations
            provider: Cloud provider name

        Returns:
            Formatted text report
        """
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("Cloud FinOps Analysis Report")
        report_lines.append("=" * 60)
        report_lines.append(f"\nProvider: {provider}")
        report_lines.append(f"Analysis Period: {cost_analysis.period_start.date()} to {cost_analysis.period_end.date()}")
        report_lines.append("\n" + "-" * 60)
        report_lines.append("COST SUMMARY")
        report_lines.append("-" * 60)
        report_lines.append(f"\nTotal Monthly Cost: ${cost_analysis.total_cost:,.2f}")

        # Top cost drivers
        if cost_analysis.top_cost_drivers:
            report_lines.append("\nTop Cost Drivers:")
            for service, cost, percentage in cost_analysis.top_cost_drivers[:10]:
                report_lines.append(f"  - {service}: ${cost:,.2f} ({percentage:.1f}%)")

        # Resource summary
        report_lines.append("\n" + "-" * 60)
        report_lines.append("RESOURCE SUMMARY")
        report_lines.append("-" * 60)
        report_lines.append(f"\nTotal Resources: {resource_analysis.total_resources}")
        report_lines.append(f"Unused Resources: {len(resource_analysis.unused_resources)}")
        report_lines.append(f"Underutilized Resources: {len(resource_analysis.underutilized_resources)}")
        report_lines.append(f"Over-provisioned Resources: {len(resource_analysis.overprovisioned_resources)}")
        report_lines.append(f"Idle Resources: {len(resource_analysis.idle_resources)}")

        # Recommendations
        total_savings = sum(rec.estimated_savings for rec in recommendations)
        report_lines.append("\n" + "-" * 60)
        report_lines.append("OPTIMIZATION OPPORTUNITIES")
        report_lines.append("-" * 60)
        report_lines.append(f"\nTotal Potential Savings: ${total_savings:,.2f}/month")
        report_lines.append(f"Number of Recommendations: {len(recommendations)}\n")

        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec.title}")
            report_lines.append(f"   Estimated Savings: ${rec.estimated_savings:,.2f}/month")
            report_lines.append(f"   Priority: {rec.priority.value.upper()}")
            report_lines.append(f"   Risk Level: {rec.risk_level.upper()}")
            report_lines.append(f"   Action: {rec.action}")
            if rec.resources:
                resource_list = ", ".join(rec.resources[:5])
                if len(rec.resources) > 5:
                    resource_list += f", ... ({len(rec.resources)} total)"
                report_lines.append(f"   Resources: {resource_list}")
            report_lines.append("")

        return "\n".join(report_lines)

    def generate_json_report(self, cost_analysis: CostAnalysis,
                            resource_analysis: ResourceAnalysis,
                            recommendations: List[OptimizationRecommendation],
                            provider: str = "Unknown") -> Dict[str, Any]:
        """
        Generate a JSON report.

        Args:
            cost_analysis: Cost analysis results
            resource_analysis: Resource analysis results
            recommendations: List of optimization recommendations
            provider: Cloud provider name

        Returns:
            Dictionary with report data
        """
        return {
            'provider': provider,
            'generated_at': datetime.utcnow().isoformat(),
            'period': {
                'start': cost_analysis.period_start.isoformat(),
                'end': cost_analysis.period_end.isoformat()
            },
            'cost_summary': {
                'total_cost': cost_analysis.total_cost,
                'costs_by_service': cost_analysis.costs_by_service,
                'costs_by_region': cost_analysis.costs_by_region,
                'top_cost_drivers': [
                    {
                        'service': service,
                        'cost': cost,
                        'percentage': percentage
                    }
                    for service, cost, percentage in cost_analysis.top_cost_drivers
                ]
            },
            'resource_summary': {
                'total_resources': resource_analysis.total_resources,
                'unused_count': len(resource_analysis.unused_resources),
                'underutilized_count': len(resource_analysis.underutilized_resources),
                'overprovisioned_count': len(resource_analysis.overprovisioned_resources),
                'idle_count': len(resource_analysis.idle_resources),
                'resources_by_type': resource_analysis.resources_by_type,
                'average_utilization': resource_analysis.average_utilization
            },
            'recommendations': [
                {
                    'title': rec.title,
                    'description': rec.description,
                    'type': rec.recommendation_type.value,
                    'priority': rec.priority.value,
                    'estimated_savings': rec.estimated_savings,
                    'action': rec.action,
                    'resources': rec.resources,
                    'risk_level': rec.risk_level,
                    'details': rec.details
                }
                for rec in recommendations
            ],
            'total_potential_savings': sum(rec.estimated_savings for rec in recommendations)
        }

    def save_report(self, report_data: Any, output_path: str, format: str = "text") -> bool:
        """
        Save report to file.

        Args:
            report_data: Report data (string for text, dict for JSON/CSV)
            output_path: Path to save report
            format: Report format ('text', 'json', 'csv')

        Returns:
            True if saved successfully
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if format == "text":
                with open(output_file, 'w') as f:
                    f.write(report_data)
            elif format == "json":
                with open(output_file, 'w') as f:
                    json.dump(report_data, f, indent=2)
            elif format == "csv":
                # Convert recommendations to CSV
                if isinstance(report_data, dict) and 'recommendations' in report_data:
                    with open(output_file, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=[
                            'title', 'type', 'priority', 'estimated_savings', 
                            'action', 'risk_level', 'resource_count'
                        ])
                        writer.writeheader()
                        for rec in report_data['recommendations']:
                            writer.writerow({
                                'title': rec['title'],
                                'type': rec['type'],
                                'priority': rec['priority'],
                                'estimated_savings': rec['estimated_savings'],
                                'action': rec['action'],
                                'risk_level': rec['risk_level'],
                                'resource_count': len(rec['resources'])
                            })
            else:
                logger.error(f"Unknown format: {format}")
                return False

            logger.info(f"Report saved to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return False

