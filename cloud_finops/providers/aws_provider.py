"""AWS provider integration for cost and resource analysis."""

import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class Resource:
    """Represents a cloud resource."""
    resource_id: str
    resource_type: str
    region: str
    cost: float
    tags: Dict[str, str]
    utilization: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CostData:
    """Represents cost data for a time period."""
    start_date: datetime
    end_date: datetime
    total_cost: float
    costs_by_service: Dict[str, float]
    costs_by_region: Dict[str, float]
    resources: List[Resource]


class AWSProvider:
    """AWS cloud provider integration."""

    def __init__(self, region: str = "us-east-1", access_key_id: Optional[str] = None,
                 secret_access_key: Optional[str] = None):
        """
        Initialize AWS provider.

        Args:
            region: AWS region
            access_key_id: AWS access key ID (optional, uses credentials chain if not provided)
            secret_access_key: AWS secret access key (optional)
        """
        self.region = region
        self.session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
        
        # Initialize clients
        self.ce_client = self.session.client('ce')  # Cost Explorer
        self.ec2_client = self.session.client('ec2')
        self.rds_client = self.session.client('rds')
        self.s3_client = self.session.client('s3')
        self.lambda_client = self.session.client('lambda')
        self.cloudwatch = self.session.client('cloudwatch')

    def get_cost_data(self, start_date: datetime, end_date: datetime) -> CostData:
        """
        Get cost data for a time period.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            CostData object with cost information
        """
        logger.info(f"Fetching AWS cost data from {start_date} to {end_date}")

        # Get cost and usage data
        response = self.ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost', 'UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'DIMENSION', 'Key': 'REGION'}
            ]
        )

        # Parse cost data
        costs_by_service: Dict[str, float] = {}
        costs_by_region: Dict[str, float] = {}
        total_cost = 0.0

        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service = group['Keys'][0]
                region = group['Keys'][1] if len(group['Keys']) > 1 else 'N/A'
                cost = float(group['Metrics']['BlendedCost']['Amount'])

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

    def _get_resources(self) -> List[Resource]:
        """Get detailed resource information."""
        resources: List[Resource] = []

        # Get EC2 instances
        resources.extend(self._get_ec2_instances())

        # Get RDS instances
        resources.extend(self._get_rds_instances())

        # Get S3 buckets
        resources.extend(self._get_s3_buckets())

        # Get Lambda functions
        resources.extend(self._get_lambda_functions())

        return resources

    def _get_ec2_instances(self) -> List[Resource]:
        """Get EC2 instance information."""
        instances = []
        
        try:
            response = self.ec2_client.describe_instances()
            
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    state = instance['State']['Name']
                    
                    # Skip terminated instances
                    if state == 'terminated':
                        continue
                    
                    # Get tags
                    tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    
                    # Get utilization metrics
                    utilization = self._get_instance_utilization(instance_id)
                    
                    # Estimate cost (simplified - in production, use Cost Explorer API)
                    cost = self._estimate_ec2_cost(instance)
                    
                    instances.append(Resource(
                        resource_id=instance_id,
                        resource_type='EC2',
                        region=instance.get('Placement', {}).get('AvailabilityZone', self.region),
                        cost=cost,
                        tags=tags,
                        utilization=utilization,
                        metadata={
                            'instance_type': instance.get('InstanceType'),
                            'state': state,
                            'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else None
                        }
                    ))
        except Exception as e:
            logger.warning(f"Error fetching EC2 instances: {e}")

        return instances

    def _get_rds_instances(self) -> List[Resource]:
        """Get RDS instance information."""
        instances = []
        
        try:
            response = self.rds_client.describe_db_instances()
            
            for db_instance in response.get('DBInstances', []):
                db_id = db_instance['DBInstanceIdentifier']
                status = db_instance['DBInstanceStatus']
                
                # Get tags
                tags_response = self.rds_client.list_tags_for_resource(
                    ResourceName=db_instance['DBInstanceArn']
                )
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}
                
                # Get utilization
                utilization = self._get_rds_utilization(db_id)
                
                # Estimate cost
                cost = self._estimate_rds_cost(db_instance)
                
                instances.append(Resource(
                    resource_id=db_id,
                    resource_type='RDS',
                    region=db_instance.get('AvailabilityZone', self.region),
                    cost=cost,
                    tags=tags,
                    utilization=utilization,
                    metadata={
                        'engine': db_instance.get('Engine'),
                        'instance_class': db_instance.get('DBInstanceClass'),
                        'status': status,
                        'allocated_storage': db_instance.get('AllocatedStorage')
                    }
                ))
        except Exception as e:
            logger.warning(f"Error fetching RDS instances: {e}")

        return instances

    def _get_s3_buckets(self) -> List[Resource]:
        """Get S3 bucket information."""
        buckets = []
        
        try:
            response = self.s3_client.list_buckets()
            
            for bucket in response.get('Buckets', []):
                bucket_name = bucket['Name']
                
                # Get bucket size and cost
                size, cost = self._get_s3_bucket_cost(bucket_name)
                
                # Get tags
                try:
                    tags_response = self.s3_client.get_bucket_tagging(Bucket=bucket_name)
                    tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
                except:
                    tags = {}
                
                buckets.append(Resource(
                    resource_id=bucket_name,
                    resource_type='S3',
                    region=self.region,
                    cost=cost,
                    tags=tags,
                    metadata={
                        'size_gb': size,
                        'creation_date': bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None
                    }
                ))
        except Exception as e:
            logger.warning(f"Error fetching S3 buckets: {e}")

        return buckets

    def _get_lambda_functions(self) -> List[Resource]:
        """Get Lambda function information."""
        functions = []
        
        try:
            response = self.lambda_client.list_functions()
            
            for func in response.get('Functions', []):
                func_name = func['FunctionName']
                
                # Get tags
                try:
                    tags_response = self.lambda_client.list_tags(Resource=func['FunctionArn'])
                    tags = tags_response.get('Tags', {})
                except:
                    tags = {}
                
                # Get utilization
                utilization = self._get_lambda_utilization(func_name)
                
                # Estimate cost
                cost = self._estimate_lambda_cost(func, utilization)
                
                functions.append(Resource(
                    resource_id=func_name,
                    resource_type='Lambda',
                    region=func.get('FunctionArn', '').split(':')[3],
                    cost=cost,
                    tags=tags,
                    utilization=utilization,
                    metadata={
                        'runtime': func.get('Runtime'),
                        'memory_size': func.get('MemorySize'),
                        'timeout': func.get('Timeout')
                    }
                ))
        except Exception as e:
            logger.warning(f"Error fetching Lambda functions: {e}")

        return functions

    def _get_instance_utilization(self, instance_id: str, days: int = 7) -> Dict[str, float]:
        """Get EC2 instance CPU utilization."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                return {'cpu_percent': avg_cpu}
        except Exception as e:
            logger.debug(f"Could not get utilization for {instance_id}: {e}")
        
        return {'cpu_percent': 0.0}

    def _get_rds_utilization(self, db_id: str, days: int = 7) -> Dict[str, float]:
        """Get RDS instance CPU utilization."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if datapoints:
                avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
                return {'cpu_percent': avg_cpu}
        except Exception as e:
            logger.debug(f"Could not get RDS utilization for {db_id}: {e}")
        
        return {'cpu_percent': 0.0}

    def _get_lambda_utilization(self, function_name: str, days: int = 7) -> Dict[str, float]:
        """Get Lambda function invocation metrics."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            # Get invocations
            invocations_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            total_invocations = sum(dp['Sum'] for dp in invocations_response.get('Datapoints', []))
            
            return {'invocations': total_invocations}
        except Exception as e:
            logger.debug(f"Could not get Lambda utilization for {function_name}: {e}")
        
        return {'invocations': 0}

    def _estimate_ec2_cost(self, instance: Dict[str, Any]) -> float:
        """Estimate EC2 instance monthly cost (simplified)."""
        # This is a simplified estimation. In production, use AWS Pricing API
        # or Cost Explorer for accurate costs.
        instance_type = instance.get('InstanceType', 't3.micro')
        
        # Rough monthly cost estimates (on-demand pricing, varies by region)
        pricing_map = {
            't3.micro': 7.5,
            't3.small': 15.0,
            't3.medium': 30.0,
            't3.large': 60.0,
            't3.xlarge': 120.0,
            'm5.large': 96.0,
            'm5.xlarge': 192.0,
            'm5.2xlarge': 384.0,
            'c5.large': 85.0,
            'c5.xlarge': 170.0,
        }
        
        return pricing_map.get(instance_type, 50.0)  # Default estimate

    def _estimate_rds_cost(self, db_instance: Dict[str, Any]) -> float:
        """Estimate RDS instance monthly cost (simplified)."""
        instance_class = db_instance.get('DBInstanceClass', 'db.t3.micro')
        
        # Rough monthly cost estimates
        pricing_map = {
            'db.t3.micro': 15.0,
            'db.t3.small': 30.0,
            'db.t3.medium': 60.0,
            'db.r5.large': 200.0,
            'db.r5.xlarge': 400.0,
            'db.r5.2xlarge': 800.0,
        }
        
        base_cost = pricing_map.get(instance_class, 100.0)
        
        # Add storage cost (simplified: $0.10/GB/month)
        storage_gb = db_instance.get('AllocatedStorage', 20)
        storage_cost = storage_gb * 0.10
        
        return base_cost + storage_cost

    def _get_s3_bucket_cost(self, bucket_name: str) -> tuple:
        """Get S3 bucket size and estimated cost."""
        try:
            # Get bucket size
            paginator = self.s3_client.get_paginator('list_objects_v2')
            total_size = 0
            
            for page in paginator.paginate(Bucket=bucket_name):
                for obj in page.get('Contents', []):
                    total_size += obj.get('Size', 0)
            
            size_gb = total_size / (1024 ** 3)
            
            # Estimate cost: $0.023/GB/month for standard storage
            cost = size_gb * 0.023
            
            return size_gb, cost
        except Exception as e:
            logger.debug(f"Could not get S3 bucket cost for {bucket_name}: {e}")
            return 0.0, 0.0

    def _estimate_lambda_cost(self, func: Dict[str, Any], utilization: Dict[str, float]) -> float:
        """Estimate Lambda function monthly cost."""
        # Lambda pricing: $0.20 per 1M requests, $0.0000166667 per GB-second
        invocations = utilization.get('invocations', 0)
        memory_mb = func.get('MemorySize', 128)
        
        # Simplified: assume average 1 second execution time
        gb_seconds = (invocations * memory_mb) / 1024
        
        request_cost = (invocations / 1_000_000) * 0.20
        compute_cost = gb_seconds * 0.0000166667
        
        return request_cost + compute_cost

    def stop_instance(self, instance_id: str) -> bool:
        """Stop an EC2 instance."""
        try:
            self.ec2_client.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Stopped EC2 instance: {instance_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping instance {instance_id}: {e}")
            return False

    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an EC2 instance."""
        try:
            self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            logger.info(f"Terminated EC2 instance: {instance_id}")
            return True
        except Exception as e:
            logger.error(f"Error terminating instance {instance_id}: {e}")
            return False

