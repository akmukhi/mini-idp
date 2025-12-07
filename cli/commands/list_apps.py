"""
List applications command for Mini-IDP CLI.
"""

import click


@click.command("list")
@click.option(
    "--namespace",
    "-n",
    help="Kubernetes namespace (default: all namespaces)",
)
@click.option(
    "--type",
    "-t",
    type=click.Choice(["service", "job", "worker", "all"]),
    default="all",
    help="Filter by application type (default: all)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
@click.pass_context
def list_apps(ctx, namespace, type, output):
    """
    List deployed applications.

    \b
    Examples:
      # List all applications
      mini-idp list

      # List services in a specific namespace
      mini-idp list --namespace production --type service

      # Output as JSON
      mini-idp list --output json
    """
    config = ctx.obj["config"]

    if not namespace:
        namespace = config.get("default_namespace")

    click.echo(f"Listing applications in namespace '{namespace or 'all'}':")
    click.echo(f"  Type filter: {type}")
    click.echo(f"  Output format: {output}")

    # TODO: Implement actual listing logic
    click.echo("\nListing logic will be implemented in next steps.")
    click.echo("This will query Kubernetes for deployed applications.")
