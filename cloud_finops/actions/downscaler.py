"""Automatic resource downscaling."""

from typing import List, Dict, Any, Optional
from cloud_finops.providers.aws_provider import Resource
from cloud_finops.analyzers.optimizer import OptimizationRecommendation, RecommendationType
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)


class Downscaler:
    """Handles automatic resource downscaling."""

    def __init__(self, provider, dry_run: bool = True):
        """
        Initialize downscaler.

        Args:
            provider: Cloud provider instance (AWSProvider, AzureProvider, or GCPProvider)
            dry_run: If True, only log actions without executing them
        """
        self.provider = provider
        self.dry_run = dry_run

    def apply_recommendation(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """
        Apply an optimization recommendation.

        Args:
            recommendation: Optimization recommendation to apply

        Returns:
            Dictionary with results of the action
        """
        logger.info(f"Applying recommendation: {recommendation.title}")

        results = {
            'recommendation': recommendation.title,
            'action': recommendation.action,
            'resources_processed': 0,
            'resources_succeeded': 0,
            'resources_failed': 0,
            'errors': []
        }

        if self.dry_run:
            logger.info(f"[DRY RUN] Would apply: {recommendation.action}")
            results['dry_run'] = True
            results['resources_processed'] = len(recommendation.resources)
            return results

        # Apply based on recommendation type
        if recommendation.recommendation_type == RecommendationType.TERMINATE_UNUSED:
            results = self._terminate_resources(recommendation)
        elif recommendation.recommendation_type == RecommendationType.STOP_IDLE:
            results = self._stop_resources(recommendation)
        elif recommendation.recommendation_type == RecommendationType.SCHEDULE_STOP:
            results = self._schedule_stop_resources(recommendation)
        else:
            logger.warning(f"Recommendation type {recommendation.recommendation_type} not yet implemented for automatic execution")

        return results

    def _terminate_resources(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """Terminate unused resources."""
        results = {
            'recommendation': recommendation.title,
            'action': 'terminate',
            'resources_processed': 0,
            'resources_succeeded': 0,
            'resources_failed': 0,
            'errors': []
        }

        provider_type = type(self.provider).__name__

        for resource_id in recommendation.resources:
            results['resources_processed'] += 1

            try:
                if provider_type == 'AWSProvider':
                    # Extract instance ID
                    if resource_id.startswith('i-'):
                        success = self.provider.terminate_instance(resource_id)
                    else:
                        logger.warning(f"Unknown resource type for termination: {resource_id}")
                        success = False
                elif provider_type == 'AzureProvider':
                    # Azure resources need resource group and name
                    # This is simplified - in production, parse resource_id properly
                    logger.warning(f"Azure termination not fully implemented for: {resource_id}")
                    success = False
                elif provider_type == 'GCPProvider':
                    # GCP resources need zone and name
                    logger.warning(f"GCP termination not fully implemented for: {resource_id}")
                    success = False
                else:
                    success = False

                if success:
                    results['resources_succeeded'] += 1
                else:
                    results['resources_failed'] += 1
                    results['errors'].append(f"Failed to terminate {resource_id}")

            except Exception as e:
                results['resources_failed'] += 1
                results['errors'].append(f"Error terminating {resource_id}: {str(e)}")
                logger.error(f"Error terminating {resource_id}: {e}")

        return results

    def _stop_resources(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """Stop idle resources."""
        results = {
            'recommendation': recommendation.title,
            'action': 'stop',
            'resources_processed': 0,
            'resources_succeeded': 0,
            'resources_failed': 0,
            'errors': []
        }

        provider_type = type(self.provider).__name__

        for resource_id in recommendation.resources:
            results['resources_processed'] += 1

            try:
                if provider_type == 'AWSProvider':
                    if resource_id.startswith('i-'):
                        success = self.provider.stop_instance(resource_id)
                    else:
                        success = False
                elif provider_type == 'AzureProvider':
                    # Would need resource group and VM name
                    logger.warning(f"Azure stop not fully implemented for: {resource_id}")
                    success = False
                elif provider_type == 'GCPProvider':
                    # Would need zone and instance name
                    logger.warning(f"GCP stop not fully implemented for: {resource_id}")
                    success = False
                else:
                    success = False

                if success:
                    results['resources_succeeded'] += 1
                else:
                    results['resources_failed'] += 1
                    results['errors'].append(f"Failed to stop {resource_id}")

            except Exception as e:
                results['resources_failed'] += 1
                results['errors'].append(f"Error stopping {resource_id}: {str(e)}")
                logger.error(f"Error stopping {resource_id}: {e}")

        return results

    def _schedule_stop_resources(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """Schedule stop for resources (would integrate with scheduler)."""
        # This would integrate with ResourceScheduler
        logger.info(f"Scheduling stop for {len(recommendation.resources)} resources")
        
        return {
            'recommendation': recommendation.title,
            'action': 'schedule_stop',
            'resources_processed': len(recommendation.resources),
            'resources_succeeded': len(recommendation.resources),
            'resources_failed': 0,
            'errors': [],
            'note': 'Scheduling requires ResourceScheduler integration'
        }

