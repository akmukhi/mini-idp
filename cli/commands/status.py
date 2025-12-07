"""
Status command for Mini-IDP CLI.
"""

import click


@click.command("status")
@click.argument("name")
@click.option(
    "--namespace",
    "-n",
    help="Kubernetes namespace (default: from config)",
)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Watch status changes",
)
@click.pass_context
def status(ctx, name, namespace, watch):
    """
    Show status of a deployed application.

    \b
    Examples:
      # Show application status
      mini-idp status my-api

      # Watch status changes
      mini-idp status my-api --watch

      # Check status in specific namespace
      mini-idp status my-api --namespace production
    """
    config = ctx.obj["config"]

    if not namespace:
        namespace = config.get("default_namespace", "default")

    click.echo(f"Status of application '{name}' in namespace '{namespace}':")

    if watch:
        click.echo("Watching for changes... (Press Ctrl+C to stop)")
        # TODO: Implement watch logic
        click.echo("Watch functionality will be implemented in next steps.")
    else:
        # TODO: Implement status retrieval logic
        click.echo("\nStatus information:")
        click.echo("  - Deployment status: Will be retrieved from Kubernetes")
        click.echo("  - Pod status: Will show running/failed pods")
        click.echo("  - Service status: Will show service endpoints")
        click.echo("  - Autoscaling: Will show HPA status")
        click.echo("  - Metrics: Will show metrics availability")
