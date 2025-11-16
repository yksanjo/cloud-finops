"""Configuration management for Cloud FinOps."""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
load_dotenv()


class Config:
    """Manages configuration for Cloud FinOps optimizer."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to YAML configuration file
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}

    @property
    def aws_access_key_id(self) -> Optional[str]:
        """AWS access key ID."""
        return os.getenv("AWS_ACCESS_KEY_ID") or self.config.get("aws", {}).get("access_key_id")

    @property
    def aws_secret_access_key(self) -> Optional[str]:
        """AWS secret access key."""
        return os.getenv("AWS_SECRET_ACCESS_KEY") or self.config.get("aws", {}).get("secret_access_key")

    @property
    def aws_region(self) -> str:
        """AWS region."""
        return os.getenv("AWS_REGION") or self.config.get("aws", {}).get("region", "us-east-1")

    @property
    def azure_subscription_id(self) -> Optional[str]:
        """Azure subscription ID."""
        return os.getenv("AZURE_SUBSCRIPTION_ID") or self.config.get("azure", {}).get("subscription_id")

    @property
    def azure_client_id(self) -> Optional[str]:
        """Azure client ID."""
        return os.getenv("AZURE_CLIENT_ID") or self.config.get("azure", {}).get("client_id")

    @property
    def azure_client_secret(self) -> Optional[str]:
        """Azure client secret."""
        return os.getenv("AZURE_CLIENT_SECRET") or self.config.get("azure", {}).get("client_secret")

    @property
    def azure_tenant_id(self) -> Optional[str]:
        """Azure tenant ID."""
        return os.getenv("AZURE_TENANT_ID") or self.config.get("azure", {}).get("tenant_id")

    @property
    def gcp_project_id(self) -> Optional[str]:
        """GCP project ID."""
        return os.getenv("GCP_PROJECT_ID") or self.config.get("gcp", {}).get("project_id")

    @property
    def gcp_credentials_path(self) -> Optional[str]:
        """Path to GCP service account credentials."""
        return os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or self.config.get("gcp", {}).get("credentials_path")

    @property
    def auto_downscale_enabled(self) -> bool:
        """Whether automatic downscaling is enabled."""
        value = os.getenv("AUTO_DOWNSCALE_ENABLED", "false").lower()
        return value == "true" or self.config.get("optimization", {}).get("auto_downscale_enabled", False)

    @property
    def non_critical_env_tag(self) -> str:
        """Tag key:value for non-critical environments."""
        return os.getenv("NON_CRITICAL_ENV_TAG", "environment:dev") or \
               self.config.get("optimization", {}).get("non_critical_env_tag", "environment:dev")

    @property
    def dry_run(self) -> bool:
        """Whether to run in dry-run mode (no actual changes)."""
        value = os.getenv("DRY_RUN", "true").lower()
        return value == "true" or self.config.get("optimization", {}).get("dry_run", True)

    @property
    def cost_threshold(self) -> float:
        """Minimum cost threshold for reporting (in dollars)."""
        return float(os.getenv("COST_THRESHOLD", "10.0")) or \
               self.config.get("optimization", {}).get("cost_threshold", 10.0)

    @property
    def savings_threshold(self) -> float:
        """Minimum savings threshold for recommendations (in dollars)."""
        return float(os.getenv("SAVINGS_THRESHOLD", "50.0")) or \
               self.config.get("optimization", {}).get("savings_threshold", 50.0)

