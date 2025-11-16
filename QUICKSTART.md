# Cloud FinOps Optimizer - Quick Start Guide

## Installation

```bash
cd cloud-finops
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp env.example .env
```

2. Edit `.env` and add your cloud provider credentials:
   - **AWS**: Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
   - **Azure**: Add subscription ID, client ID, client secret, and tenant ID
   - **GCP**: Add project ID and path to service account JSON

## Basic Usage

### Analyze AWS Costs

```bash
python -m cloud_finops.optimizer --provider aws --analyze
```

### Generate HTML Report

```bash
python -m cloud_finops.optimizer --provider aws --analyze --report output/report.html --format html
```

### Analyze All Providers

```bash
python -m cloud_finops.optimizer --provider all --analyze --report output/reports
```

### Get Optimization Recommendations (Dry Run)

```bash
python -m cloud_finops.optimizer --provider aws --analyze --optimize --dry-run
```

### Apply Optimizations (Use with Caution!)

```bash
# First, test with dry-run
python -m cloud_finops.optimizer --provider aws --analyze --optimize --dry-run

# Then, if satisfied, apply for real
python -m cloud_finops.optimizer --provider aws --optimize
```

## Python API Usage

### Basic Analysis

```python
from cloud_finops.optimizer import CloudFinOpsOptimizer
from cloud_finops.utils.config import Config

config = Config()
optimizer = CloudFinOpsOptimizer(config=config)

# Analyze AWS
result = optimizer.analyze_provider('aws', days=30)

if result['success']:
    print(f"Total Cost: ${result['cost_analysis'].total_cost:,.2f}")
    print(f"Recommendations: {len(result['recommendations'])}")
```

### Custom Analysis

```python
from cloud_finops.providers.aws_provider import AWSProvider
from cloud_finops.analyzers.cost_analyzer import CostAnalyzer
from cloud_finops.analyzers.resource_analyzer import ResourceAnalyzer
from cloud_finops.analyzers.optimizer import Optimizer
from datetime import datetime, timedelta

# Initialize provider
aws = AWSProvider(region='us-east-1')

# Get cost data
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=30)
cost_data = aws.get_cost_data(start_date, end_date)

# Analyze
cost_analyzer = CostAnalyzer()
cost_analysis = cost_analyzer.analyze(cost_data)

resource_analyzer = ResourceAnalyzer()
resource_analysis = resource_analyzer.analyze(cost_data.resources)

# Get recommendations
optimizer = Optimizer()
recommendations = optimizer.get_recommendations(
    cost_analysis, resource_analysis, cost_data.resources
)

# Print recommendations
for rec in recommendations:
    print(f"{rec.title}: ${rec.estimated_savings:,.2f}/month")
```

## Examples

See the `examples/` directory for more detailed examples:
- `basic_analysis.py` - Basic cost analysis
- `automated_optimization.py` - Automated optimization workflow
- `custom_report.py` - Custom report generation

## Security Best Practices

1. **Use IAM Roles**: Prefer IAM roles over access keys when possible
2. **Read-Only Access**: For analysis, use read-only permissions
3. **Separate Credentials**: Use different credentials for optimization actions
4. **Dry-Run First**: Always test with `--dry-run` before applying changes
5. **Resource Tagging**: Tag resources properly for safe filtering

## Troubleshooting

### AWS Credentials Not Found
- Ensure AWS credentials are configured via environment variables, `.env` file, or AWS credentials file
- Check that `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set

### Azure Authentication Failed
- Verify subscription ID, client ID, client secret, and tenant ID
- Ensure the service principal has necessary permissions

### GCP Authentication Failed
- Verify the service account JSON file path
- Ensure the service account has necessary permissions

### No Recommendations Found
- Check that resources are properly tagged
- Verify that utilization data is available
- Adjust `SAVINGS_THRESHOLD` if recommendations are too small

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out the [examples/](examples/) directory for more use cases
- Customize the configuration for your specific needs

