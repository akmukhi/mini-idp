"""
Delete command for Mini-IDP CLI.
"""

import click


@click.command("delete")
@click.argument("name")
@click.option(
    "--namespace",
    "-n",
    help="Kubernetes namespace (default: from config)",
)
@click.option(
    "--type",
    "-t",
    type=click.Choice(["service", "job", "worker", "auto"]),
    default="auto",
    help="Application type (default: auto-detect)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force deletion without confirmation",
)
@click.pass_context
def delete(ctx, name, namespace, type, force):
    """
    Delete a deployed application.

    \b
    Examples:
      # Delete an application (with confirmation)
      mini-idp delete my-api

      # Force delete without confirmation
      mini-idp delete my-api --force

      # Delete from specific namespace
      mini-idp delete my-api --namespace production
    """
    config = ctx.obj["config"]

    if not namespace:
        namespace = config.get("default_namespace", "default")

    if not force:
        if not click.confirm(
            f"Are you sure you want to delete '{name}' from namespace '{namespace}'?"
        ):
            click.echo("Deletion cancelled.")
            return

    click.echo(f"Deleting application '{name}' from namespace '{namespace}'...")
    click.echo(f"  Type: {type}")

    # TODO: Implement actual deletion logic
    click.echo("Deletion logic will be implemented in next steps.")
    click.echo("This will delete the Kubernetes resources for the application.")
