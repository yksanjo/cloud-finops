"""Custom report generation example."""

from datetime import datetime, timedelta
from cloud_finops.optimizer import CloudFinOpsOptimizer
from cloud_finops.utils.config import Config
from cloud_finops.reporting.reporter import Reporter
from cloud_finops.reporting.visualizer import Visualizer

# Initialize
config = Config()
optimizer = CloudFinOpsOptimizer(config=config)

# Analyze all providers
print("Analyzing all cloud providers...")
results = optimizer.analyze_all_providers(days=30)

print(f"\nTotal Cost Across All Providers: ${results['total_cost']:,.2f}")
print(f"Total Potential Savings: ${results['total_potential_savings']:,.2f}/month\n")

# Generate reports for each provider
reporter = Reporter()
visualizer = Visualizer()

for provider_name, result in results['providers'].items():
    if not result.get('success'):
        continue

    cost_analysis = result['cost_analysis']
    resource_analysis = result['resource_analysis']
    recommendations = result['recommendations']

    # Generate HTML report
    html = visualizer.generate_html_report(
        cost_analysis,
        resource_analysis,
        recommendations,
        provider_name.upper()
    )
    
    output_path = f"output/report_{provider_name}.html"
    visualizer.save_html_report(html, output_path)
    print(f"HTML report saved: {output_path}")

    # Generate JSON report
    json_data = reporter.generate_json_report(
        cost_analysis,
        resource_analysis,
        recommendations,
        provider_name.upper()
    )
    
    json_path = f"output/report_{provider_name}.json"
    reporter.save_report(json_data, json_path, format='json')
    print(f"JSON report saved: {json_path}")

print("\nAll reports generated successfully!")

