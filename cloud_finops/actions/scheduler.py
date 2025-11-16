"""Resource scheduling for automatic start/stop."""

from typing import Dict, List, Optional
from datetime import datetime, time
from cloud_finops.utils.logger import setup_logger

logger = setup_logger(__name__)


class ResourceScheduler:
    """Manages scheduled start/stop of cloud resources."""

    def __init__(self, provider):
        """
        Initialize resource scheduler.

        Args:
            provider: Cloud provider instance
        """
        self.provider = provider
        self.schedules: List[Dict] = []

    def schedule_stop(self, tag_filter: Dict[str, str], schedule: str, 
                     timezone: str = "UTC") -> bool:
        """
        Schedule automatic stop for resources matching tag filter.

        Args:
            tag_filter: Dictionary of tag key-value pairs to match
            schedule: Schedule expression (e.g., 'weekends', '0 18 * * 5' for cron)
            timezone: Timezone for schedule

        Returns:
            True if schedule was created successfully
        """
        schedule_config = {
            'action': 'stop',
            'tag_filter': tag_filter,
            'schedule': schedule,
            'timezone': timezone,
            'created_at': datetime.utcnow().isoformat()
        }

        self.schedules.append(schedule_config)
        logger.info(f"Created stop schedule: {schedule} for resources with tags {tag_filter}")

        # In production, this would integrate with AWS EventBridge, Azure Automation, or GCP Cloud Scheduler
        return True

    def schedule_start(self, tag_filter: Dict[str, str], schedule: str,
                      timezone: str = "UTC") -> bool:
        """
        Schedule automatic start for resources matching tag filter.

        Args:
            tag_filter: Dictionary of tag key-value pairs to match
            schedule: Schedule expression
            timezone: Timezone for schedule

        Returns:
            True if schedule was created successfully
        """
        schedule_config = {
            'action': 'start',
            'tag_filter': tag_filter,
            'schedule': schedule,
            'timezone': timezone,
            'created_at': datetime.utcnow().isoformat()
        }

        self.schedules.append(schedule_config)
        logger.info(f"Created start schedule: {schedule} for resources with tags {tag_filter}")

        return True

    def list_schedules(self) -> List[Dict]:
        """List all active schedules."""
        return self.schedules

    def remove_schedule(self, schedule_id: int) -> bool:
        """Remove a schedule by index."""
        if 0 <= schedule_id < len(self.schedules):
            removed = self.schedules.pop(schedule_id)
            logger.info(f"Removed schedule: {removed}")
            return True
        return False

