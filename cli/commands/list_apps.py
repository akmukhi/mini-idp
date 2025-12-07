"""List applications command for Mini-IDP CLI."""
import json
import sys
from pathlib import Path
from typing import List, Optional

import click
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.k8s_client import K8sClient


def _format_table(apps: List[dict]) -> None:
    """Format applications as a table."""
    if not apps:
        click.echo("No applications found.")
        return

    # Calculate column widths
    name_width = max(len(app["name"]) for app in apps) + 2
    namespace_width = max(len(app["namespace"]) for app in apps) + 2
    type_width = max(len(app["type"]) for app in apps) + 2
    status_width = 12

    # Header
    click.echo(
        f"{'NAME':<{name_width}} {'NAMESPACE':<{namespace_width}} "
        f"{'TYPE':<{type_width}} {'STATUS':<{status_width}} {'REPLICAS':<10} {'IMAGE'}"
    )
    click.echo("-" * (name_width + namespace_width + type_width + status_width + 10 + 50))

    # Rows
    for app in apps:
        status = app.get("status", "Unknown")
        replicas = app.get("replicas", "N/A")
        if isinstance(replicas, dict):
            replicas_str = f"{replicas.get('ready', 0)}/{replicas.get('desired', 0)}"
        else:
            replicas_str = str(replicas)
        image = app.get("image", "N/A")
        if len(image) > 45:
            image = image[:42] + "..."

        click.echo(
            f"{app['name']:<{name_width}} {app['namespace']:<{namespace_width}} "
            f"{app['type']:<{type_width}} {status:<{status_width}} {replicas_str:<10} {image}"
        )


def _get_deployments(client: K8sClient, namespace: Optional[str] = None) -> List[dict]:
    """Get deployments from Kubernetes."""
    apps = []
    try:
        if namespace:
            deployments = client.apps_v1.list_namespaced_deployment(namespace=namespace)
        else:
            deployments = client.apps_v1.list_deployment_for_all_namespaces()

        for deployment in deployments.items:
            # Determine type from labels
            labels = deployment.metadata.labels or {}
            app_type = labels.get("type", "service")
            if app_type not in ["service", "worker"]:
                app_type = "service"

            # Get status
            ready = deployment.status.ready_replicas or 0
            desired = deployment.spec.replicas or 0
            if ready == desired and desired > 0:
                status = "Ready"
            elif ready > 0:
                status = "Partial"
            else:
                status = "Not Ready"

            image = (
                deployment.spec.template.spec.containers[0].image
                if deployment.spec.template.spec.containers
                else "N/A"
            )

            apps.append(
                {
                    "name": deployment.metadata.name,
                    "namespace": deployment.metadata.namespace,
                    "type": app_type,
                    "status": status,
                    "replicas": {"ready": ready, "desired": desired},
                    "image": image,
                }
            )
    except Exception as e:
        click.echo(f"Error listing deployments: {e}", err=True)

    return apps


def _get_jobs(client: K8sClient, namespace: Optional[str] = None) -> List[dict]:
    """Get jobs from Kubernetes."""
    apps = []
    try:
        if namespace:
            jobs = client.batch_v1.list_namespaced_job(namespace=namespace)
        else:
            jobs = client.batch_v1.list_job_for_all_namespaces()

        for job in jobs.items:
            # Get status
            if job.status.succeeded:
                status = "Succeeded"
            elif job.status.failed:
                status = "Failed"
            elif job.status.active:
                status = "Running"
            else:
                status = "Pending"

            image = (
                job.spec.template.spec.containers[0].image
                if job.spec.template.spec.containers
                else "N/A"
            )

            apps.append(
                {
                    "name": job.metadata.name,
                    "namespace": job.metadata.namespace,
                    "type": "job",
                    "status": status,
                    "replicas": {
                        "succeeded": job.status.succeeded or 0,
                        "failed": job.status.failed or 0,
                        "active": job.status.active or 0,
                    },
                    "image": image,
                }
            )
    except Exception as e:
        click.echo(f"Error listing jobs: {e}", err=True)

    return apps


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
    kubeconfig = ctx.obj.get("kubeconfig")

    if not namespace:
        namespace = config.get("default_namespace")

    try:
        client = K8sClient(kubeconfig=kubeconfig)

        # Collect applications
        all_apps = []

        if type in ["all", "service", "worker"]:
            deployments = _get_deployments(client, namespace)
            if type == "all":
                all_apps.extend(deployments)
            else:
                all_apps.extend([app for app in deployments if app["type"] == type])

        if type in ["all", "job"]:
            jobs = _get_jobs(client, namespace)
            all_apps.extend(jobs)

        # Sort by namespace, then name
        all_apps.sort(key=lambda x: (x["namespace"], x["name"]))

        # Output
        if output == "json":
            click.echo(json.dumps(all_apps, indent=2))
        elif output == "yaml":
            click.echo(yaml.dump(all_apps, default_flow_style=False))
        else:
            if namespace:
                click.echo(f"\nApplications in namespace '{namespace}':")
            else:
                click.echo("\nAll applications:")
            _format_table(all_apps)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
