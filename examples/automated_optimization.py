"""Automated optimization example."""

from cloud_finops.optimizer import CloudFinOpsOptimizer
from cloud_finops.utils.config import Config
from cloud_finops.actions.downscaler import Downscaler

# Initialize configuration
config = Config()

# Check if auto-optimization is enabled
if not config.auto_downscale_enabled:
    print("Auto-downscaling is disabled. Set AUTO_DOWNSCALE_ENABLED=true to enable.")
    exit(1)

# Create optimizer
optimizer = CloudFinOpsOptimizer(config=config)

# Analyze AWS
print("Analyzing AWS resources...")
result = optimizer.analyze_provider('aws', days=7)

if not result['success']:
    print(f"Error: {result.get('error', 'Unknown error')}")
    exit(1)

recommendations = result['recommendations']

if not recommendations:
    print("No optimization opportunities found.")
    exit(0)

print(f"\nFound {len(recommendations)} optimization recommendations:")
for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec.title}: ${rec.estimated_savings:,.2f}/month savings")

# Apply optimizations (dry-run by default)
print("\nApplying optimizations (dry-run mode)...")
optimize_results = optimizer.apply_optimizations('aws', recommendations, dry_run=True)

print(f"\nResults:")
print(f"  Recommendations Applied: {optimize_results['recommendations_applied']}")
print(f"  Succeeded: {optimize_results['recommendations_succeeded']}")
print(f"  Failed: {optimize_results['recommendations_failed']}")

# To apply for real, set dry_run=False (use with caution!)
# optimize_results = optimizer.apply_optimizations('aws', recommendations, dry_run=False)

