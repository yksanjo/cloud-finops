"""HTML report visualization with charts."""

from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from cloud_finops.analyzers.cost_analyzer import CostAnalysis
from cloud_finops.analyzers.resource_analyzer import ResourceAnalysis
from cloud_finops.analyzers.optimizer import OptimizationRecommendation
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)


class Visualizer:
    """Generates HTML reports with visualizations."""

    def __init__(self):
        """Initialize visualizer."""
        pass

    def generate_html_report(self, cost_analysis: CostAnalysis,
                            resource_analysis: ResourceAnalysis,
                            recommendations: List[OptimizationRecommendation],
                            provider: str = "Unknown") -> str:
        """
        Generate an HTML report with charts.

        Args:
            cost_analysis: Cost analysis results
            resource_analysis: Resource analysis results
            recommendations: List of optimization recommendations
            provider: Cloud provider name

        Returns:
            HTML report string
        """
        total_savings = sum(rec.estimated_savings for rec in recommendations)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Cloud FinOps Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            margin: 0;
        }}
        .savings-card {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .priority-high {{
            color: #f44336;
            font-weight: bold;
        }}
        .priority-medium {{
            color: #ff9800;
        }}
        .priority-low {{
            color: #4CAF50;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-high {{
            background-color: #f44336;
            color: white;
        }}
        .badge-medium {{
            background-color: #ff9800;
            color: white;
        }}
        .badge-low {{
            background-color: #4CAF50;
            color: white;
        }}
        .recommendation {{
            background: #f9f9f9;
            border-left: 4px solid #4CAF50;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .recommendation h3 {{
            margin-top: 0;
            color: #333;
        }}
        .resources {{
            font-family: monospace;
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Cloud FinOps Analysis Report</h1>
        <p><strong>Provider:</strong> {provider}</p>
        <p><strong>Analysis Period:</strong> {cost_analysis.period_start.date()} to {cost_analysis.period_end.date()}</p>
        <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>

        <div class="summary">
            <div class="summary-card">
                <h3>Total Monthly Cost</h3>
                <p class="value">${cost_analysis.total_cost:,.0f}</p>
            </div>
            <div class="summary-card savings-card">
                <h3>Potential Savings</h3>
                <p class="value">${total_savings:,.0f}/mo</p>
            </div>
            <div class="summary-card">
                <h3>Total Resources</h3>
                <p class="value">{resource_analysis.total_resources}</p>
            </div>
            <div class="summary-card">
                <h3>Recommendations</h3>
                <p class="value">{len(recommendations)}</p>
            </div>
        </div>

        <h2>Top Cost Drivers</h2>
        <table>
            <thead>
                <tr>
                    <th>Service</th>
                    <th>Cost</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
"""

        for service, cost, percentage in cost_analysis.top_cost_drivers[:10]:
            html += f"""
                <tr>
                    <td>{service}</td>
                    <td>${cost:,.2f}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
"""

        html += """
            </tbody>
        </table>

        <h2>Resource Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Count</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Total Resources</td>
                    <td>{resource_analysis.total_resources}</td>
                </tr>
                <tr>
                    <td>Unused Resources</td>
                    <td>{len(resource_analysis.unused_resources)}</td>
                </tr>
                <tr>
                    <td>Underutilized Resources</td>
                    <td>{len(resource_analysis.underutilized_resources)}</td>
                </tr>
                <tr>
                    <td>Over-provisioned Resources</td>
                    <td>{len(resource_analysis.overprovisioned_resources)}</td>
                </tr>
                <tr>
                    <td>Idle Resources</td>
                    <td>{len(resource_analysis.idle_resources)}</td>
                </tr>
            </tbody>
        </table>

        <h2>Optimization Recommendations</h2>
""".format(
            resource_analysis=resource_analysis
        )

        for i, rec in enumerate(recommendations, 1):
            priority_class = f"priority-{rec.priority.value}"
            badge_class = f"badge-{rec.priority.value}"
            
            html += f"""
        <div class="recommendation">
            <h3>{i}. {rec.title}</h3>
            <p>{rec.description}</p>
            <p><strong>Estimated Savings:</strong> <span style="color: #4CAF50; font-weight: bold;">${rec.estimated_savings:,.2f}/month</span></p>
            <p><strong>Priority:</strong> <span class="badge {badge_class}">{rec.priority.value.upper()}</span></p>
            <p><strong>Risk Level:</strong> <span class="badge badge-{rec.risk_level}">{rec.risk_level.upper()}</span></p>
            <p><strong>Action:</strong> {rec.action}</p>
"""

            if rec.resources:
                resource_list = ", ".join(rec.resources[:10])
                if len(rec.resources) > 10:
                    resource_list += f", ... ({len(rec.resources)} total)"
                html += f'            <div class="resources"><strong>Resources:</strong> {resource_list}</div>'

            html += """
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        return html

    def save_html_report(self, html: str, output_path: str) -> bool:
        """
        Save HTML report to file.

        Args:
            html: HTML content
            output_path: Path to save HTML file

        Returns:
            True if saved successfully
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w') as f:
                f.write(html)

            logger.info(f"HTML report saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}")
            return False

