"""Azure provider integration for cost and resource analysis."""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from cloud_finops.providers.aws_provider import Resource, CostData
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    from azure.mgmt.costmanagement import CostManagementClient
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.resource import ResourceManagementClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("Azure SDK not available. Install with: pip install azure-identity azure-mgmt-costmanagement azure-mgmt-compute azure-mgmt-resource")


class AzureProvider:
    """Azure cloud provider integration."""

    def __init__(self, subscription_id: str, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None, tenant_id: Optional[str] = None):
        """
        Initialize Azure provider.

        Args:
            subscription_id: Azure subscription ID
            client_id: Azure client ID (optional, uses DefaultAzureCredential if not provided)
            client_secret: Azure client secret (optional)
            tenant_id: Azure tenant ID (optional)
        """
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK not installed. Install with: pip install azure-identity azure-mgmt-costmanagement azure-mgmt-compute azure-mgmt-resource")

        self.subscription_id = subscription_id

        # Setup credentials
        if client_id and client_secret and tenant_id:
            self.credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            self.credential = DefaultAzureCredential()

        # Initialize clients
        self.cost_client = CostManagementClient(self.credential)
        self.compute_client = ComputeManagementClient(self.credential, subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, subscription_id)

    def get_cost_data(self, start_date: datetime, end_date: datetime) -> CostData:
        """
        Get cost data for a time period.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            CostData object with cost information
        """
        logger.info(f"Fetching Azure cost data from {start_date} to {end_date}")

        # Azure Cost Management API query
        scope = f"/subscriptions/{self.subscription_id}"
        
        # Build query
        query_definition = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": start_date.isoformat(),
                "to": end_date.isoformat()
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {"name": "PreTaxCost", "function": "Sum"}
                },
                "grouping": [
                    {"type": "Dimension", "name": "ServiceName"},
                    {"type": "Dimension", "name": "ResourceLocation"}
                ]
            }
        }

        try:
            query_result = self.cost_client.query.usage(
                scope=scope,
                parameters=query_definition
            )

            # Parse cost data
            costs_by_service: Dict[str, float] = {}
            costs_by_region: Dict[str, float] = {}
            total_cost = 0.0

            if query_result.rows:
                for row in query_result.rows:
                    service = row[1] if len(row) > 1 else "Unknown"
                    region = row[2] if len(row) > 2 else "Unknown"
                    cost = float(row[0]) if row[0] else 0.0

                    costs_by_service[service] = costs_by_service.get(service, 0) + cost
                    costs_by_region[region] = costs_by_region.get(region, 0) + cost
                    total_cost += cost

            # Get resource details
            resources = self._get_resources()

            return CostData(
                start_date=start_date,
                end_date=end_date,
                total_cost=total_cost,
                costs_by_service=costs_by_service,
                costs_by_region=costs_by_region,
                resources=resources
            )
        except Exception as e:
            logger.error(f"Error fetching Azure cost data: {e}")
            # Return empty cost data on error
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

        # Get VMs
        resources.extend(self._get_virtual_machines())

        # Get storage accounts
        resources.extend(self._get_storage_accounts())

        return resources

    def _get_virtual_machines(self) -> List[Resource]:
        """Get Azure Virtual Machine information."""
        instances = []

        try:
            vms = self.compute_client.virtual_machines.list_all()

            for vm in vms:
                vm_id = vm.id
                vm_name = vm.name
                resource_group = vm.id.split('/')[4]

                # Get tags
                tags = vm.tags or {}

                # Get utilization (simplified - would need metrics API)
                utilization = {'cpu_percent': 0.0}  # Placeholder

                # Estimate cost (simplified)
                vm_size = vm.hardware_profile.vm_size if vm.hardware_profile else "Standard_B1s"
                cost = self._estimate_vm_cost(vm_size)

                instances.append(Resource(
                    resource_id=vm_id,
                    resource_type='VirtualMachine',
                    region=vm.location or "Unknown",
                    cost=cost,
                    tags=tags,
                    utilization=utilization,
                    metadata={
                        'vm_size': vm_size,
                        'resource_group': resource_group,
                        'name': vm_name,
                        'power_state': 'Unknown'  # Would need additional API call
                    }
                ))
        except Exception as e:
            logger.warning(f"Error fetching Azure VMs: {e}")

        return instances

    def _get_storage_accounts(self) -> List[Resource]:
        """Get Azure Storage Account information."""
        accounts = []

        try:
            storage_accounts = self.resource_client.resources.list(
                filter="resourceType eq 'Microsoft.Storage/storageAccounts'"
            )

            for account in storage_accounts:
                account_id = account.id
                account_name = account.name

                # Get tags
                tags = account.tags or {}

                # Estimate cost (simplified)
                cost = 50.0  # Placeholder - would need actual usage data

                accounts.append(Resource(
                    resource_id=account_id,
                    resource_type='StorageAccount',
                    region=account.location or "Unknown",
                    cost=cost,
                    tags=tags,
                    metadata={
                        'name': account_name
                    }
                ))
        except Exception as e:
            logger.warning(f"Error fetching Azure storage accounts: {e}")

        return accounts

    def _estimate_vm_cost(self, vm_size: str) -> float:
        """Estimate Azure VM monthly cost (simplified)."""
        # Rough monthly cost estimates (varies by region and OS)
        pricing_map = {
            'Standard_B1s': 10.0,
            'Standard_B2s': 20.0,
            'Standard_D2s_v3': 70.0,
            'Standard_D4s_v3': 140.0,
            'Standard_D8s_v3': 280.0,
        }

        return pricing_map.get(vm_size, 50.0)  # Default estimate

    def stop_vm(self, resource_group: str, vm_name: str) -> bool:
        """Stop an Azure Virtual Machine."""
        try:
            self.compute_client.virtual_machines.begin_power_off(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            logger.info(f"Stopped Azure VM: {vm_name} in {resource_group}")
            return True
        except Exception as e:
            logger.error(f"Error stopping VM {vm_name}: {e}")
            return False

