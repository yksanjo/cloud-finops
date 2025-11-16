"""Resource utilization analysis engine."""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from cloud_finops.providers.aws_provider import Resource
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ResourceAnalysis:
    """Results of resource analysis."""
    total_resources: int
    unused_resources: List[Resource]
    underutilized_resources: List[Resource]
    overprovisioned_resources: List[Resource]
    idle_resources: List[Resource]
    resources_by_type: Dict[str, int]
    average_utilization: Dict[str, float]


class ResourceAnalyzer:
    """Analyzes resource utilization and identifies optimization opportunities."""

    def __init__(self, cpu_threshold: float = 10.0, idle_days: int = 7):
        """
        Initialize resource analyzer.

        Args:
            cpu_threshold: CPU utilization threshold below which a resource is considered underutilized (%)
            idle_days: Number of days of inactivity to consider a resource idle
        """
        self.cpu_threshold = cpu_threshold
        self.idle_days = idle_days

    def analyze(self, resources: List[Resource]) -> ResourceAnalysis:
        """
        Analyze resources and identify optimization opportunities.

        Args:
            resources: List of resources to analyze

        Returns:
            ResourceAnalysis object with findings
        """
        logger.info(f"Analyzing {len(resources)} resources...")

        # Categorize resources
        unused = self._find_unused_resources(resources)
        underutilized = self._find_underutilized_resources(resources)
        overprovisioned = self._find_overprovisioned_resources(resources)
        idle = self._find_idle_resources(resources)

        # Count by type
        resources_by_type = self._count_by_type(resources)

        # Calculate average utilization
        avg_utilization = self._calculate_average_utilization(resources)

        return ResourceAnalysis(
            total_resources=len(resources),
            unused_resources=unused,
            underutilized_resources=underutilized,
            overprovisioned_resources=overprovisioned,
            idle_resources=idle,
            resources_by_type=resources_by_type,
            average_utilization=avg_utilization
        )

    def _find_unused_resources(self, resources: List[Resource]) -> List[Resource]:
        """Find resources that appear to be unused."""
        unused = []

        for resource in resources:
            # Check for stopped/terminated instances
            if resource.metadata:
                state = resource.metadata.get('state', '').lower()
                status = resource.metadata.get('status', '').lower()
                
                if state in ['stopped', 'terminated'] or status in ['stopped', 'deallocated']:
                    unused.append(resource)
                    continue

            # Check for zero utilization
            if resource.utilization:
                cpu = resource.utilization.get('cpu_percent', 0)
                invocations = resource.utilization.get('invocations', 0)
                
                if cpu == 0 and invocations == 0:
                    # Additional check: resource might be new
                    unused.append(resource)

        return unused

    def _find_underutilized_resources(self, resources: List[Resource]) -> List[Resource]:
        """Find resources with low utilization."""
        underutilized = []

        for resource in resources:
            if resource.utilization:
                cpu = resource.utilization.get('cpu_percent', 0)
                
                # Check if CPU is below threshold
                if 0 < cpu < self.cpu_threshold:
                    underutilized.append(resource)

        return underutilized

    def _find_overprovisioned_resources(self, resources: List[Resource]) -> List[Resource]:
        """Find resources that might be overprovisioned."""
        overprovisioned = []

        for resource in resources:
            if resource.utilization and resource.metadata:
                cpu = resource.utilization.get('cpu_percent', 0)
                instance_type = resource.metadata.get('instance_type') or resource.metadata.get('vm_size') or resource.metadata.get('machine_type')
                
                # Check if resource is consistently underutilized and is a large instance
                if cpu < 30 and instance_type:
                    # Check if it's a large instance type (simplified check)
                    if any(size in instance_type.lower() for size in ['xlarge', '2xlarge', '4xlarge', '8xlarge']):
                        overprovisioned.append(resource)

        return overprovisioned

    def _find_idle_resources(self, resources: List[Resource]) -> List[Resource]:
        """Find resources that have been idle for extended periods."""
        idle = []

        for resource in resources:
            if resource.utilization:
                cpu = resource.utilization.get('cpu_percent', 0)
                invocations = resource.utilization.get('invocations', 0)
                
                # Consider idle if no activity
                if cpu == 0 and invocations == 0:
                    idle.append(resource)

        return idle

    def _count_by_type(self, resources: List[Resource]) -> Dict[str, int]:
        """Count resources by type."""
        counts: Dict[str, int] = {}
        
        for resource in resources:
            resource_type = resource.resource_type
            counts[resource_type] = counts.get(resource_type, 0) + 1

        return counts

    def _calculate_average_utilization(self, resources: List[Resource]) -> Dict[str, float]:
        """Calculate average utilization by resource type."""
        utilization_by_type: Dict[str, List[float]] = {}

        for resource in resources:
            if resource.utilization:
                cpu = resource.utilization.get('cpu_percent', 0)
                resource_type = resource.resource_type
                
                if resource_type not in utilization_by_type:
                    utilization_by_type[resource_type] = []
                
                utilization_by_type[resource_type].append(cpu)

        # Calculate averages
        avg_utilization: Dict[str, float] = {}
        for resource_type, values in utilization_by_type.items():
            if values:
                avg_utilization[resource_type] = sum(values) / len(values)

        return avg_utilization

