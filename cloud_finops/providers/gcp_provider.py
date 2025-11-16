"""GCP provider integration for cost and resource analysis."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from cloud_finops.providers.aws_provider import Resource, CostData
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    from google.cloud import billing_v1
    from google.cloud import compute_v1
    from google.cloud import storage
    from google.oauth2 import service_account
    import google.auth
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False
    logger.warning("GCP SDK not available. Install with: pip install google-cloud-billing google-cloud-compute google-cloud-storage")


class GCPProvider:
    """GCP cloud provider integration."""

    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        """
        Initialize GCP provider.

        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON file (optional, uses default credentials if not provided)
        """
        if not GCP_AVAILABLE:
            raise ImportError("GCP SDK not installed. Install with: pip install google-cloud-billing google-cloud-compute google-cloud-storage")

        self.project_id = project_id

        # Setup credentials
        if credentials_path:
            self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
        else:
            self.credentials, _ = google.auth.default()

        # Initialize clients
        try:
            self.billing_client = billing_v1.CloudBillingClient(credentials=self.credentials)
            self.compute_client = compute_v1.InstancesClient(credentials=self.credentials)
            self.storage_client = storage.Client(project=project_id, credentials=self.credentials)
        except Exception as e:
            logger.warning(f"Error initializing GCP clients: {e}")

    def get_cost_data(self, start_date: datetime, end_date: datetime) -> CostData:
        """
        Get cost data for a time period.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            CostData object with cost information
        """
        logger.info(f"Fetching GCP cost data from {start_date} to {end_date}")

        # GCP Billing API query
        # Note: This is simplified. Full implementation would use Cloud Billing API
        # which requires billing account setup and proper permissions

        costs_by_service: Dict[str, float] = {}
        costs_by_region: Dict[str, float] = {}
        total_cost = 0.0

        try:
            # Get resource details (which include cost estimates)
            resources = self._get_resources()

            # Aggregate costs from resources
            for resource in resources:
                service = resource.resource_type
                region = resource.region

                costs_by_service[service] = costs_by_service.get(service, 0) + resource.cost
                costs_by_region[region] = costs_by_region.get(region, 0) + resource.cost
                total_cost += resource.cost

            return CostData(
                start_date=start_date,
                end_date=end_date,
                total_cost=total_cost,
                costs_by_service=costs_by_service,
                costs_by_region=costs_by_region,
                resources=resources
            )
        except Exception as e:
            logger.error(f"Error fetching GCP cost data: {e}")
            return CostData(
                start_date=start_date,
                end_date=end_date,
                total_cost=0.0,
                costs_by_service={},
                costs_by_region={},
                resources=[]
            )

    def _get_resources(self) -> List[Resource]:
        """Get detailed resource information."""
        resources: List[Resource] = []

        # Get Compute Engine instances
        resources.extend(self._get_compute_instances())

        # Get Cloud Storage buckets
        resources.extend(self._get_storage_buckets())

        return resources

    def _get_compute_instances(self) -> List[Resource]:
        """Get GCP Compute Engine instance information."""
        instances = []

        try:
            # List all zones
            zones_client = compute_v1.ZonesClient(credentials=self.credentials)
            zones = zones_client.list(project=self.project_id)

            for zone in zones:
                zone_name = zone.name

                # List instances in zone
                instances_list = self.compute_client.list(
                    project=self.project_id,
                    zone=zone_name
                )

                for instance in instances_list:
                    instance_id = instance.id
                    instance_name = instance.name

                    # Get labels (tags)
                    labels = instance.labels or {}

                    # Get utilization (simplified)
                    utilization = {'cpu_percent': 0.0}  # Would need Cloud Monitoring API

                    # Estimate cost
                    machine_type = instance.machine_type.split('/')[-1]
                    cost = self._estimate_compute_cost(machine_type, zone_name)

                    instances.append(Resource(
                        resource_id=str(instance_id),
                        resource_type='ComputeEngine',
                        region=zone_name,
                        cost=cost,
                        tags=labels,
                        utilization=utilization,
                        metadata={
                            'machine_type': machine_type,
                            'name': instance_name,
                            'status': instance.status,
                            'zone': zone_name
                        }
                    ))
        except Exception as e:
            logger.warning(f"Error fetching GCP Compute instances: {e}")

        return instances

    def _get_storage_buckets(self) -> List[Resource]:
        """Get GCP Cloud Storage bucket information."""
        buckets = []

        try:
            storage_buckets = self.storage_client.list_buckets()

            for bucket in storage_buckets:
                bucket_name = bucket.name

                # Get labels
                labels = bucket.labels or {}

                # Get size and cost
                size, cost = self._get_bucket_cost(bucket_name)

                buckets.append(Resource(
                    resource_id=bucket_name,
                    resource_type='CloudStorage',
                    region=bucket.location or "Unknown",
                    cost=cost,
                    tags=labels,
                    metadata={
                        'size_gb': size,
                        'location': bucket.location,
                        'storage_class': bucket.storage_class
                    }
                ))
        except Exception as e:
            logger.warning(f"Error fetching GCP storage buckets: {e}")

        return buckets

    def _get_bucket_cost(self, bucket_name: str) -> tuple:
        """Get GCP bucket size and estimated cost."""
        try:
            bucket = self.storage_client.bucket(bucket_name)
            total_size = 0

            for blob in bucket.list_blobs():
                total_size += blob.size

            size_gb = total_size / (1024 ** 3)

            # Estimate cost: $0.020/GB/month for standard storage
            cost = size_gb * 0.020

            return size_gb, cost
        except Exception as e:
            logger.debug(f"Could not get bucket cost for {bucket_name}: {e}")
            return 0.0, 0.0

    def _estimate_compute_cost(self, machine_type: str, zone: str) -> float:
        """Estimate GCP Compute Engine monthly cost (simplified)."""
        # Rough monthly cost estimates (varies by zone)
        pricing_map = {
            'n1-standard-1': 25.0,
            'n1-standard-2': 50.0,
            'n1-standard-4': 100.0,
            'n1-standard-8': 200.0,
            'e2-micro': 7.0,
            'e2-small': 14.0,
            'e2-medium': 28.0,
        }

        return pricing_map.get(machine_type, 30.0)  # Default estimate

    def stop_instance(self, zone: str, instance_name: str) -> bool:
        """Stop a GCP Compute Engine instance."""
        try:
            operation = self.compute_client.stop(
                project=self.project_id,
                zone=zone,
                instance=instance_name
            )
            logger.info(f"Stopped GCP instance: {instance_name} in {zone}")
            return True
        except Exception as e:
            logger.error(f"Error stopping instance {instance_name}: {e}")
            return False

