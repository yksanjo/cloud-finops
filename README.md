# Cloud FinOps Optimizer

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/yksanjo/cloud-finops)

A comprehensive Python tool for intelligent cloud cost and performance optimization across AWS, Azure, and GCP. This script actively monitors cloud usage, identifies unused resources, suggests optimizations, and can automatically execute cost-saving actions.

## 🎯 Key Features

### 1. Multi-Cloud Support
- **AWS**: Full integration with Boto3 for EC2, RDS, S3, Lambda, and more
- **Azure**: Azure SDK integration for VMs, Storage, App Services, and more
- **GCP**: Google Cloud SDK for Compute Engine, Cloud SQL, Storage, and more

### 2. Intelligent Resource Analysis
- **Unused Resource Detection**: Identifies idle instances, empty databases, unused storage
- **Cost Anomaly Detection**: Flags unusual spending patterns
- **Performance Analysis**: Correlates cost with resource utilization
- **Right-Sizing Recommendations**: Suggests optimal instance types based on usage

### 3. Automated Optimization
- **Automatic Downscaling**: Reduces non-critical environments during off-hours
- **Resource Scheduling**: Start/stop resources based on schedules
- **Reserved Instance Recommendations**: Identifies opportunities for savings plans
- **Storage Lifecycle Management**: Moves old data to cheaper storage tiers

### 4. Comprehensive Reporting
- **Cost Breakdown**: Detailed spending by service, region, and tag
- **Savings Projections**: Estimates potential cost reductions
- **Trend Analysis**: Historical cost patterns and forecasting
- **Export Formats**: JSON, CSV, HTML reports

## 🚀 Quick Start

### Installation

```bash
cd cloud-finops
pip install -r requirements.txt
```

### Configuration

Create a `.env` file or set environment variables:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Azure Configuration (optional)
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id

# GCP Configuration (optional)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your_project_id

# Optimization Settings
AUTO_DOWNSCALE_ENABLED=false  # Set to true to enable automatic actions
NON_CRITICAL_ENV_TAG=environment:dev  # Tag for non-critical environments
```

### Basic Usage

```bash
# Analyze costs and get recommendations (dry-run)
python -m cloud_finops.optimizer --provider aws --analyze

# Analyze all providers
python -m cloud_finops.optimizer --provider all --analyze

# Generate detailed report
python -m cloud_finops.optimizer --provider aws --analyze --report output/report.html

# Apply optimizations (requires AUTO_DOWNSCALE_ENABLED=true)
python -m cloud_finops.optimizer --provider aws --optimize --dry-run

# Apply optimizations for real
python -m cloud_finops.optimizer --provider aws --optimize
```

## 📊 Example Output

```
Cloud FinOps Analysis Report
============================

Provider: AWS
Analysis Period: 2024-01-01 to 2024-01-31

Total Monthly Cost: $12,450.00
Potential Savings: $3,240.00 (26%)

Top Cost Drivers:
  - EC2 Instances: $8,200.00 (66%)
  - RDS Databases: $2,100.00 (17%)
  - S3 Storage: $1,500.00 (12%)
  - Lambda Functions: $650.00 (5%)

Optimization Opportunities:
  1. Unused EC2 Instances (8 instances)
     - Estimated Savings: $1,800/month
     - Action: Terminate or stop instances
     - Resources: i-1234567890abcdef0, i-0987654321fedcba0, ...

  2. Over-provisioned RDS Instances (3 instances)
     - Estimated Savings: $900/month
     - Action: Downsize to smaller instance types
     - Resources: db-prod-1 (db.r5.2xlarge → db.r5.xlarge)

  3. Idle Development Environments (5 instances)
     - Estimated Savings: $540/month
     - Action: Schedule stop during weekends/off-hours
     - Resources: dev-env-1, dev-env-2, ...

  4. Unused S3 Storage (2.5 TB)
     - Estimated Savings: $50/month
     - Action: Move to Glacier or delete
     - Buckets: old-backups, archived-logs
```

## 🏗️ Architecture

```
cloud-finops/
├── cloud_finops/
│   ├── __init__.py
│   ├── optimizer.py          # Main CLI entry point
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── aws_provider.py   # AWS cost analysis
│   │   ├── azure_provider.py # Azure cost analysis
│   │   └── gcp_provider.py   # GCP cost analysis
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── cost_analyzer.py  # Cost analysis engine
│   │   ├── resource_analyzer.py  # Resource utilization analysis
│   │   └── optimizer.py      # Optimization recommendations
│   ├── actions/
│   │   ├── __init__.py
│   │   ├── downscaler.py     # Automatic downscaling
│   │   ├── scheduler.py      # Resource scheduling
│   │   └── lifecycle.py      # Storage lifecycle management
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── reporter.py       # Report generation
│   │   └── visualizer.py     # HTML/Chart generation
│   └── utils/
│       ├── __init__.py
│       ├── config.py         # Configuration management
│       └── logger.py         # Logging utilities
├── examples/
│   ├── basic_analysis.py
│   ├── automated_optimization.py
│   └── custom_report.py
├── tests/
│   ├── test_aws_provider.py
│   ├── test_cost_analyzer.py
│   └── test_optimizer.py
├── requirements.txt
├── setup.py
└── README.md
```

## 🔧 Advanced Usage

### Custom Analysis

```python
from cloud_finops.providers.aws_provider import AWSProvider
from cloud_finops.analyzers.cost_analyzer import CostAnalyzer
from cloud_finops.analyzers.optimizer import Optimizer

# Initialize provider
aws = AWSProvider(region='us-east-1')

# Get cost data
costs = aws.get_cost_data(start_date='2024-01-01', end_date='2024-01-31')

# Analyze costs
analyzer = CostAnalyzer()
analysis = analyzer.analyze(costs)

# Get optimization recommendations
optimizer = Optimizer()
recommendations = optimizer.get_recommendations(analysis)

# Print recommendations
for rec in recommendations:
    print(f"{rec.title}: {rec.estimated_savings}/month")
    print(f"  Action: {rec.action}")
    print(f"  Resources: {', '.join(rec.resources)}")
```

### Automated Scheduling

```python
from cloud_finops.actions.scheduler import ResourceScheduler

scheduler = ResourceScheduler(provider='aws')

# Schedule dev environments to stop on weekends
scheduler.schedule_stop(
    tag_filter={'environment': 'dev'},
    schedule='weekends',  # or cron: '0 18 * * 5' (Fridays at 6 PM)
    timezone='America/New_York'
)

# Schedule production backup instances to start only during backup windows
scheduler.schedule_start(
    tag_filter={'role': 'backup', 'environment': 'prod'},
    schedule='0 2 * * *',  # Daily at 2 AM
    timezone='UTC'
)
```

## 📈 Monitoring & Alerts

The tool can be integrated into monitoring systems:

```python
from cloud_finops.optimizer import CloudFinOpsOptimizer

optimizer = CloudFinOpsOptimizer()

# Run daily analysis
results = optimizer.analyze_all_providers()

# Send alerts if savings opportunities exceed threshold
if results.total_potential_savings > 1000:
    send_alert(f"High savings opportunity: ${results.total_potential_savings}/month")
```

## 🔒 Security Best Practices

1. **IAM Roles**: Use IAM roles with least-privilege access
2. **Read-Only Access**: For analysis, use read-only permissions
3. **Separate Credentials**: Use different credentials for optimization actions
4. **Dry-Run Mode**: Always test with `--dry-run` before applying changes
5. **Resource Tagging**: Tag resources properly for safe filtering

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## 🆘 Support

For issues, questions, or feature requests, please open an issue on [GitHub](https://github.com/yksanjo/cloud-finops/issues).

## 🔗 Repository

**GitHub**: [https://github.com/yksanjo/cloud-finops](https://github.com/yksanjo/cloud-finops)

