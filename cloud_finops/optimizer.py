"""Main Cloud FinOps optimizer CLI."""

import click
from datetime import datetime, timedelta
from typing import Optional, List
from cloud_finops.utils.config import Config
from cloud_finops.utils.logger import setup_logger
from cloud_finops.providers.aws_provider import AWSProvider
from cloud_finops.providers.azure_provider import AzureProvider
from cloud_finops.providers.gcp_provider import GCPProvider
from cloud_finops.analyzers.cost_analyzer import CostAnalyzer
from cloud_finops.analyzers.resource_analyzer import ResourceAnalyzer
from cloud_finops.analyzers.optimizer import Optimizer
from cloud_finops.actions.downscaler import Downscaler
from cloud_finops.reporting.reporter import Reporter
from cloud_finops.reporting.visualizer import Visualizer

logger = setup_logger(__name__)


class CloudFinOpsOptimizer:
    """Main Cloud FinOps optimizer class."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize Cloud FinOps optimizer.

        Args:
            config: Configuration object (optional)
        """
        self.config = config or Config()
        self.providers = {}

    def get_provider(self, provider_name: str):
        """Get or create a cloud provider instance."""
        if provider_name in self.providers:
            return self.providers[provider_name]

        if provider_name.lower() == 'aws':
            provider = AWSProvider(
                region=self.config.aws_region,
                access_key_id=self.config.aws_access_key_id,
                secret_access_key=self.config.aws_secret_access_key
            )
        elif provider_name.lower() == 'azure':
            if not self.config.azure_subscription_id:
                raise ValueError("Azure subscription ID not configured")
            provider = AzureProvider(
                subscription_id=self.config.azure_subscription_id,
                client_id=self.config.azure_client_id,
                client_secret=self.config.azure_client_secret,
                tenant_id=self.config.azure_tenant_id
            )
        elif provider_name.lower() == 'gcp':
            if not self.config.gcp_project_id:
                raise ValueError("GCP project ID not configured")
            provider = GCPProvider(
                project_id=self.config.gcp_project_id,
                credentials_path=self.config.gcp_credentials_path
            )
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

        self.providers[provider_name] = provider
        return provider

    def analyze_provider(self, provider_name: str, days: int = 30) -> dict:
        """
        Analyze a single cloud provider.

        Args:
            provider_name: Provider name ('aws', 'azure', 'gcp')
            days: Number of days to analyze

        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing {provider_name.upper()}...")

        try:
            provider = self.get_provider(provider_name)
        except Exception as e:
            logger.error(f"Error initializing {provider_name} provider: {e}")
            return {
                'provider': provider_name,
                'error': str(e),
                'success': False
            }

        # Get cost data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        try:
            cost_data = provider.get_cost_data(start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching cost data: {e}")
            return {
                'provider': provider_name,
                'error': f"Error fetching cost data: {e}",
                'success': False
            }

        # Analyze costs
        cost_analyzer = CostAnalyzer()
        cost_analysis = cost_analyzer.analyze(cost_data)

        # Analyze resources
        resource_analyzer = ResourceAnalyzer()
        resource_analysis = resource_analyzer.analyze(cost_data.resources)

        # Get optimization recommendations
        optimizer = Optimizer(savings_threshold=self.config.savings_threshold)
        recommendations = optimizer.get_recommendations(
            cost_analysis,
            resource_analysis,
            cost_data.resources
        )

        return {
            'provider': provider_name,
            'success': True,
            'cost_analysis': cost_analysis,
            'resource_analysis': resource_analysis,
            'recommendations': recommendations,
            'cost_data': cost_data
        }

    def analyze_all_providers(self, days: int = 30) -> dict:
        """
        Analyze all configured cloud providers.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with results from all providers
        """
        results = {
            'providers': {},
            'total_cost': 0.0,
            'total_potential_savings': 0.0
        }

        # Try each provider
        for provider_name in ['aws', 'azure', 'gcp']:
            try:
                # Check if provider is configured
                if provider_name == 'aws' and not self.config.aws_access_key_id:
                    continue
                elif provider_name == 'azure' and not self.config.azure_subscription_id:
                    continue
                elif provider_name == 'gcp' and not self.config.gcp_project_id:
                    continue

                result = self.analyze_provider(provider_name, days)
                results['providers'][provider_name] = result

                if result.get('success'):
                    results['total_cost'] += result['cost_analysis'].total_cost
                    results['total_potential_savings'] += sum(
                        rec.estimated_savings for rec in result['recommendations']
                    )
            except Exception as e:
                logger.warning(f"Could not analyze {provider_name}: {e}")

        return results

    def apply_optimizations(self, provider_name: str, recommendations: List, dry_run: bool = True) -> dict:
        """
        Apply optimization recommendations.

        Args:
            provider_name: Provider name
            recommendations: List of recommendations to apply
            dry_run: If True, only simulate actions

        Returns:
            Dictionary with results
        """
        logger.info(f"Applying optimizations for {provider_name} (dry_run={dry_run})...")

        provider = self.get_provider(provider_name)
        downscaler = Downscaler(provider, dry_run=dry_run)

        results = {
            'provider': provider_name,
            'dry_run': dry_run,
            'recommendations_applied': 0,
            'recommendations_succeeded': 0,
            'recommendations_failed': 0,
            'results': []
        }

        for recommendation in recommendations:
            try:
                result = downscaler.apply_recommendation(recommendation)
                results['results'].append(result)
                results['recommendations_applied'] += 1

                if result.get('resources_succeeded', 0) > 0:
                    results['recommendations_succeeded'] += 1
                else:
                    results['recommendations_failed'] += 1
            except Exception as e:
                logger.error(f"Error applying recommendation: {e}")
                results['recommendations_failed'] += 1

        return results


@click.command()
@click.option('--provider', '-p', type=click.Choice(['aws', 'azure', 'gcp', 'all']), 
              default='aws', help='Cloud provider to analyze')
@click.option('--analyze', '-a', is_flag=True, help='Run cost and resource analysis')
@click.option('--optimize', '-o', is_flag=True, help='Apply optimization recommendations')
@click.option('--days', '-d', type=int, default=30, help='Number of days to analyze')
@click.option('--dry-run', is_flag=True, default=True, help='Dry run mode (no actual changes)')
@click.option('--report', '-r', type=str, help='Generate report and save to file')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'html', 'csv']), 
              default='text', help='Report format')
@click.option('--config', '-c', type=str, help='Path to configuration file')
def main(provider, analyze, optimize, days, dry_run, report, format, config):
    """Cloud FinOps Optimizer - Intelligent cloud cost and performance optimization."""
    
    # Load configuration
    cfg = Config(config_file=config) if config else Config()

    # Override dry_run from config if not specified
    if not dry_run and not cfg.dry_run:
        dry_run = False

    optimizer = CloudFinOpsOptimizer(config=cfg)

    if analyze:
        # Run analysis
        if provider == 'all':
            results = optimizer.analyze_all_providers(days=days)
        else:
            result = optimizer.analyze_provider(provider, days=days)
            results = {
                'providers': {provider: result},
                'total_cost': result.get('cost_analysis', {}).total_cost if result.get('success') else 0.0,
                'total_potential_savings': sum(
                    rec.estimated_savings for rec in result.get('recommendations', [])
                ) if result.get('success') else 0.0
            }

        # Generate and display report
        reporter = Reporter()
        visualizer = Visualizer()

        for prov_name, result in results['providers'].items():
            if not result.get('success'):
                logger.warning(f"Skipping {prov_name} due to errors")
                continue

            cost_analysis = result['cost_analysis']
            resource_analysis = result['resource_analysis']
            recommendations = result['recommendations']

            # Print text report to console
            text_report = reporter.generate_text_report(
                cost_analysis, resource_analysis, recommendations, prov_name.upper()
            )
            click.echo(text_report)

            # Save report if requested
            if report:
                if format == 'html':
                    html = visualizer.generate_html_report(
                        cost_analysis, resource_analysis, recommendations, prov_name.upper()
                    )
                    output_path = report if provider != 'all' else f"{report}_{prov_name}.html"
                    visualizer.save_html_report(html, output_path)
                elif format == 'json':
                    json_data = reporter.generate_json_report(
                        cost_analysis, resource_analysis, recommendations, prov_name.upper()
                    )
                    output_path = report if provider != 'all' else f"{report}_{prov_name}.json"
                    reporter.save_report(json_data, output_path, format='json')
                elif format == 'csv':
                    json_data = reporter.generate_json_report(
                        cost_analysis, resource_analysis, recommendations, prov_name.upper()
                    )
                    output_path = report if provider != 'all' else f"{report}_{prov_name}.csv"
                    reporter.save_report(json_data, output_path, format='csv')
                else:
                    output_path = report if provider != 'all' else f"{report}_{prov_name}.txt"
                    reporter.save_report(text_report, output_path, format='text')

        # Summary
        if provider == 'all':
            click.echo("\n" + "=" * 60)
            click.echo("SUMMARY ACROSS ALL PROVIDERS")
            click.echo("=" * 60)
            click.echo(f"Total Cost: ${results['total_cost']:,.2f}")
            click.echo(f"Total Potential Savings: ${results['total_potential_savings']:,.2f}/month")

    if optimize:
        # Apply optimizations
        if provider == 'all':
            click.echo("Optimization for 'all' providers not yet supported. Please specify a provider.")
            return

        result = optimizer.analyze_provider(provider, days=days)
        if not result.get('success'):
            click.echo(f"Error analyzing {provider}: {result.get('error', 'Unknown error')}")
            return

        recommendations = result['recommendations']
        
        if not recommendations:
            click.echo("No optimization recommendations found.")
            return

        click.echo(f"\nFound {len(recommendations)} optimization recommendations.")
        
        if dry_run:
            click.echo("DRY RUN MODE - No actual changes will be made.\n")
        else:
            if not click.confirm(f"Apply {len(recommendations)} recommendations? This will make actual changes to your cloud resources."):
                click.echo("Cancelled.")
                return

        optimize_results = optimizer.apply_optimizations(provider, recommendations, dry_run=dry_run)
        
        click.echo("\n" + "=" * 60)
        click.echo("OPTIMIZATION RESULTS")
        click.echo("=" * 60)
        click.echo(f"Recommendations Applied: {optimize_results['recommendations_applied']}")
        click.echo(f"Succeeded: {optimize_results['recommendations_succeeded']}")
        click.echo(f"Failed: {optimize_results['recommendations_failed']}")

        for res in optimize_results['results']:
            click.echo(f"\n{res['recommendation']}:")
            click.echo(f"  Resources Processed: {res['resources_processed']}")
            click.echo(f"  Succeeded: {res['resources_succeeded']}")
            click.echo(f"  Failed: {res['resources_failed']}")
            if res.get('errors'):
                for error in res['errors']:
                    click.echo(f"  Error: {error}")

    if not analyze and not optimize:
        click.echo("Please specify --analyze or --optimize (or both)")
        click.echo("Use --help for more information")


if __name__ == '__main__':
    main()

