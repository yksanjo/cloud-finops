"""Basic cost analysis example."""

from datetime import datetime, timedelta
from cloud_finops.optimizer import CloudFinOpsOptimizer
from cloud_finops.utils.config import Config
from cloud_finops.reporting.reporter import Reporter

# Initialize configuration
config = Config()

# Create optimizer
optimizer = CloudFinOpsOptimizer(config=config)

# Analyze AWS (last 30 days)
print("Analyzing AWS costs...")
result = optimizer.analyze_provider('aws', days=30)

if result['success']:
    cost_analysis = result['cost_analysis']
    resource_analysis = result['resource_analysis']
    recommendations = result['recommendations']

    # Generate text report
    reporter = Reporter()
    report = reporter.generate_text_report(
        cost_analysis,
        resource_analysis,
        recommendations,
        'AWS'
    )

    print(report)

    # Save JSON report
    json_report = reporter.generate_json_report(
        cost_analysis,
        resource_analysis,
        recommendations,
        'AWS'
    )
    reporter.save_report(json_report, 'output/aws_analysis.json', format='json')
    print("\nReport saved to output/aws_analysis.json")
else:
    print(f"Error: {result.get('error', 'Unknown error')}")

