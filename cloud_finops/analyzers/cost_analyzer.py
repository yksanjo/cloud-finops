"""Cost analysis engine."""

from dataclasses import dataclass
from typing import Dict, List, Any
from datetime import datetime
from cloud_finops.providers.aws_provider import CostData
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class CostAnalysis:
    """Results of cost analysis."""
    total_cost: float
    costs_by_service: Dict[str, float]
    costs_by_region: Dict[str, float]
    top_cost_drivers: List[tuple[str, float, float]]  # (service, cost, percentage)
    cost_trend: str  # "increasing", "decreasing", "stable"
    anomalies: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime


class CostAnalyzer:
    """Analyzes cloud costs and identifies patterns."""

    def __init__(self):
        """Initialize cost analyzer."""
        pass

    def analyze(self, cost_data: CostData) -> CostAnalysis:
        """
        Analyze cost data and generate insights.

        Args:
            cost_data: Cost data to analyze

        Returns:
            CostAnalysis object with insights
        """
        logger.info("Analyzing cost data...")

        # Calculate top cost drivers
        total_cost = cost_data.total_cost
        top_drivers = self._get_top_cost_drivers(cost_data.costs_by_service, total_cost)

        # Detect cost trend (simplified - would need historical data for real trend)
        cost_trend = "stable"  # Placeholder

        # Detect anomalies
        anomalies = self._detect_anomalies(cost_data)

        return CostAnalysis(
            total_cost=total_cost,
            costs_by_service=cost_data.costs_by_service,
            costs_by_region=cost_data.costs_by_region,
            top_cost_drivers=top_drivers,
            cost_trend=cost_trend,
            anomalies=anomalies,
            period_start=cost_data.start_date,
            period_end=cost_data.end_date
        )

    def _get_top_cost_drivers(self, costs_by_service: Dict[str, float], 
                              total_cost: float, top_n: int = 10) -> List[tuple[str, float, float]]:
        """Get top N cost drivers with percentages."""
        if total_cost == 0:
            return []

        # Sort services by cost
        sorted_services = sorted(
            costs_by_service.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_drivers = []
        for service, cost in sorted_services[:top_n]:
            percentage = (cost / total_cost) * 100
            top_drivers.append((service, cost, percentage))

        return top_drivers

    def _detect_anomalies(self, cost_data: CostData) -> List[Dict[str, Any]]:
        """Detect cost anomalies."""
        anomalies = []

        # Check for unusually high costs
        if cost_data.total_cost > 10000:  # Threshold
            anomalies.append({
                'type': 'high_total_cost',
                'severity': 'warning',
                'message': f'Total cost is unusually high: ${cost_data.total_cost:,.2f}',
                'value': cost_data.total_cost
            })

        # Check for services with unexpectedly high costs
        avg_service_cost = cost_data.total_cost / len(cost_data.costs_by_service) if cost_data.costs_by_service else 0
        for service, cost in cost_data.costs_by_service.items():
            if cost > avg_service_cost * 3:  # 3x average
                anomalies.append({
                    'type': 'high_service_cost',
                    'severity': 'info',
                    'message': f'{service} has unusually high cost: ${cost:,.2f}',
                    'service': service,
                    'value': cost
                })

        return anomalies

