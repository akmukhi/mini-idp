"""
Main CLI entry point for Mini-IDP.
"""

import sys
from pathlib import Path

import click

from cli.commands import deploy, list_apps, delete, status
from cli.config import get_config, init_config


@click.group()
@click.version_option(version="0.1.0", prog_name="mini-idp")
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--kubeconfig",
    type=click.Path(exists=True, path_type=Path),
    help="Path to kubeconfig file",
)
@click.pass_context
def cli(ctx, config, kubeconfig):
    """
    Mini-IDP: Deploy applications to Kubernetes with no YAML required.

    Deploy services, jobs, and workers using simple templates with built-in
    best practices for autoscaling, logging, metrics, secrets, and GitOps.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Load configuration
    cfg = get_config(config_path=config)
    ctx.obj["config"] = cfg

    # Set kubeconfig if provided
    if kubeconfig:
        ctx.obj["kubeconfig"] = str(kubeconfig)
    else:
        ctx.obj["kubeconfig"] = cfg.get("kubeconfig")

    # Initialize configuration if needed
    if not cfg.get("initialized"):
        click.echo("Initializing Mini-IDP configuration...")
        init_config()
        click.echo("Configuration initialized successfully!")


# Register command groups
cli.add_command(deploy.deploy)
cli.add_command(list_apps.list_apps)
cli.add_command(delete.delete)
cli.add_command(status.status)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
