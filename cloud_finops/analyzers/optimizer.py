"""Optimization recommendation engine."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
from cloud_finops.providers.aws_provider import Resource
from cloud_finops.analyzers.cost_analyzer import CostAnalysis
from cloud_finops.analyzers.resource_analyzer import ResourceAnalysis
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)


class RecommendationType(Enum):
    """Types of optimization recommendations."""
    TERMINATE_UNUSED = "terminate_unused"
    STOP_IDLE = "stop_idle"
    DOWNSIZE = "downsize"
    SCHEDULE_STOP = "schedule_stop"
    MOVE_STORAGE = "move_storage"
    DELETE_UNUSED = "delete_unused"
    RESERVED_INSTANCE = "reserved_instance"


class RecommendationPriority(Enum):
    """Priority levels for recommendations."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OptimizationRecommendation:
    """An optimization recommendation."""
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    estimated_savings: float  # Monthly savings in dollars
    action: str
    resources: List[str]  # Resource IDs
    details: Dict[str, Any]
    risk_level: str  # "low", "medium", "high"


class Optimizer:
    """Generates optimization recommendations based on analysis."""

    def __init__(self, savings_threshold: float = 50.0):
        """
        Initialize optimizer.

        Args:
            savings_threshold: Minimum estimated savings to include a recommendation (dollars/month)
        """
        self.savings_threshold = savings_threshold

    def get_recommendations(self, cost_analysis: CostAnalysis, 
                           resource_analysis: ResourceAnalysis,
                           resources: List[Resource]) -> List[OptimizationRecommendation]:
        """
        Generate optimization recommendations.

        Args:
            cost_analysis: Cost analysis results
            resource_analysis: Resource analysis results
            resources: List of all resources

        Returns:
            List of optimization recommendations
        """
        logger.info("Generating optimization recommendations...")

        recommendations = []

        # Terminate unused resources
        recommendations.extend(
            self._recommend_terminate_unused(resource_analysis.unused_resources)
        )

        # Stop idle resources
        recommendations.extend(
            self._recommend_stop_idle(resource_analysis.idle_resources)
        )

        # Downsize overprovisioned resources
        recommendations.extend(
            self._recommend_downsize(resource_analysis.overprovisioned_resources)
        )

        # Schedule stop for non-critical environments
        recommendations.extend(
            self._recommend_schedule_stop(resources)
        )

        # Move storage to cheaper tiers
        recommendations.extend(
            self._recommend_move_storage(resources)
        )

        # Filter by savings threshold
        recommendations = [
            rec for rec in recommendations 
            if rec.estimated_savings >= self.savings_threshold
        ]

        # Sort by estimated savings (descending)
        recommendations.sort(key=lambda x: x.estimated_savings, reverse=True)

        return recommendations

    def _recommend_terminate_unused(self, unused_resources: List[Resource]) -> List[OptimizationRecommendation]:
        """Recommend terminating unused resources."""
        recommendations = []

        if not unused_resources:
            return recommendations

        # Group by type
        by_type: Dict[str, List[Resource]] = {}
        for resource in unused_resources:
            resource_type = resource.resource_type
            if resource_type not in by_type:
                by_type[resource_type] = []
            by_type[resource_type].append(resource)

        for resource_type, resources in by_type.items():
            total_savings = sum(r.cost for r in resources)
            
            if total_savings >= self.savings_threshold:
                recommendations.append(OptimizationRecommendation(
                    title=f"Terminate Unused {resource_type} Resources",
                    description=f"Found {len(resources)} unused {resource_type} resources that can be terminated",
                    recommendation_type=RecommendationType.TERMINATE_UNUSED,
                    priority=RecommendationPriority.HIGH if total_savings > 500 else RecommendationPriority.MEDIUM,
                    estimated_savings=total_savings,
                    action=f"Terminate {len(resources)} unused {resource_type} resources",
                    resources=[r.resource_id for r in resources],
                    details={
                        'resource_type': resource_type,
                        'count': len(resources),
                        'resources': [
                            {
                                'id': r.resource_id,
                                'cost': r.cost,
                                'region': r.region
                            }
                            for r in resources
                        ]
                    },
                    risk_level="low" if resource_type in ['EC2', 'VirtualMachine', 'ComputeEngine'] else "medium"
                ))

        return recommendations

    def _recommend_stop_idle(self, idle_resources: List[Resource]) -> List[OptimizationRecommendation]:
        """Recommend stopping idle resources."""
        recommendations = []

        if not idle_resources:
            return recommendations

        # Filter for non-production resources (check tags)
        non_prod_resources = [
            r for r in idle_resources
            if self._is_non_production(r)
        ]

        if non_prod_resources:
            total_savings = sum(r.cost * 0.7 for r in non_prod_resources)  # 70% savings if stopped
            
            if total_savings >= self.savings_threshold:
                recommendations.append(OptimizationRecommendation(
                    title="Stop Idle Development/Test Resources",
                    description=f"Found {len(non_prod_resources)} idle non-production resources",
                    recommendation_type=RecommendationType.STOP_IDLE,
                    priority=RecommendationPriority.MEDIUM,
                    estimated_savings=total_savings,
                    action=f"Stop {len(non_prod_resources)} idle resources",
                    resources=[r.resource_id for r in non_prod_resources],
                    details={
                        'count': len(non_prod_resources),
                        'resources': [r.resource_id for r in non_prod_resources]
                    },
                    risk_level="low"
                ))

        return recommendations

    def _recommend_downsize(self, overprovisioned_resources: List[Resource]) -> List[OptimizationRecommendation]:
        """Recommend downsizing overprovisioned resources."""
        recommendations = []

        if not overprovisioned_resources:
            return recommendations

        # Group by current instance type
        by_type: Dict[str, List[Resource]] = {}
        for resource in overprovisioned_resources:
            instance_type = (
                resource.metadata.get('instance_type') or 
                resource.metadata.get('vm_size') or 
                resource.metadata.get('machine_type') or 
                'unknown'
            )
            if instance_type not in by_type:
                by_type[instance_type] = []
            by_type[instance_type].append(resource)

        for instance_type, resources in by_type.items():
            # Estimate savings from downsizing (simplified: assume 30-50% cost reduction)
            total_current_cost = sum(r.cost for r in resources)
            estimated_savings = total_current_cost * 0.4  # 40% savings

            if estimated_savings >= self.savings_threshold:
                recommendations.append(OptimizationRecommendation(
                    title=f"Downsize Over-provisioned Resources ({instance_type})",
                    description=f"Found {len(resources)} resources that can be downsized",
                    recommendation_type=RecommendationType.DOWNSIZE,
                    priority=RecommendationPriority.MEDIUM,
                    estimated_savings=estimated_savings,
                    action=f"Downsize {len(resources)} resources from {instance_type} to smaller instance types",
                    resources=[r.resource_id for r in resources],
                    details={
                        'current_instance_type': instance_type,
                        'count': len(resources),
                        'resources': [r.resource_id for r in resources]
                    },
                    risk_level="medium"
                ))

        return recommendations

    def _recommend_schedule_stop(self, resources: List[Resource]) -> List[OptimizationRecommendation]:
        """Recommend scheduling stop for non-critical environments."""
        recommendations = []

        # Find non-production resources
        non_prod_resources = [r for r in resources if self._is_non_production(r)]

        if non_prod_resources:
            # Estimate savings from stopping on weekends/off-hours (assume 30% of time)
            total_cost = sum(r.cost for r in non_prod_resources)
            estimated_savings = total_cost * 0.3

            if estimated_savings >= self.savings_threshold:
                recommendations.append(OptimizationRecommendation(
                    title="Schedule Stop for Non-Critical Environments",
                    description=f"Schedule automatic stop for {len(non_prod_resources)} non-production resources during off-hours",
                    recommendation_type=RecommendationType.SCHEDULE_STOP,
                    priority=RecommendationPriority.LOW,
                    estimated_savings=estimated_savings,
                    action=f"Schedule stop for {len(non_prod_resources)} resources during weekends/off-hours",
                    resources=[r.resource_id for r in non_prod_resources],
                    details={
                        'count': len(non_prod_resources),
                        'schedule': 'weekends and off-hours',
                        'resources': [r.resource_id for r in non_prod_resources]
                    },
                    risk_level="low"
                ))

        return recommendations

    def _recommend_move_storage(self, resources: List[Resource]) -> List[OptimizationRecommendation]:
        """Recommend moving storage to cheaper tiers."""
        recommendations = []

        # Find storage resources
        storage_resources = [
            r for r in resources 
            if r.resource_type in ['S3', 'StorageAccount', 'CloudStorage']
        ]

        # Find old/unused storage
        old_storage = [
            r for r in storage_resources
            if r.metadata and r.metadata.get('size_gb', 0) > 100  # Large buckets
        ]

        if old_storage:
            total_cost = sum(r.cost for r in old_storage)
            # Estimate 50% savings by moving to cheaper tier
            estimated_savings = total_cost * 0.5

            if estimated_savings >= self.savings_threshold:
                recommendations.append(OptimizationRecommendation(
                    title="Move Storage to Cheaper Tiers",
                    description=f"Move {len(old_storage)} storage buckets to cheaper storage classes",
                    recommendation_type=RecommendationType.MOVE_STORAGE,
                    priority=RecommendationPriority.LOW,
                    estimated_savings=estimated_savings,
                    action=f"Move {len(old_storage)} storage buckets to Glacier/Archive tier",
                    resources=[r.resource_id for r in old_storage],
                    details={
                        'count': len(old_storage),
                        'resources': [r.resource_id for r in old_storage]
                    },
                    risk_level="low"
                ))

        return recommendations

    def _is_non_production(self, resource: Resource) -> bool:
        """Check if a resource is non-production based on tags."""
        tags = resource.tags or {}
        
        # Check common environment tags
        env = tags.get('environment', '').lower()
        env_tag = tags.get('Environment', '').lower()
        env_type = tags.get('env', '').lower()
        
        return env in ['dev', 'development', 'test', 'staging', 'qa'] or \
               env_tag in ['dev', 'development', 'test', 'staging', 'qa'] or \
               env_type in ['dev', 'development', 'test', 'staging', 'qa']

