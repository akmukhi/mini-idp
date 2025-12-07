"""Delete command for Mini-IDP CLI."""
import sys
from pathlib import Path
from typing import Optional

import click
from kubernetes.client.rest import ApiException

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.k8s_client import K8sClient


def _detect_type(client: K8sClient, name: str, namespace: str) -> Optional[str]:
    """Auto-detect application type."""
    try:
        # Check for deployment
        try:
            deployment = client.apps_v1.read_namespaced_deployment(
                name=name, namespace=namespace
            )
            labels = deployment.metadata.labels or {}
            return labels.get("type", "service")
        except ApiException:
            pass

        # Check for job
        try:
            client.batch_v1.read_namespaced_job(name=name, namespace=namespace)
            return "job"
        except ApiException:
            pass

        return None
    except Exception:
        return None


def _delete_resources(client: K8sClient, name: str, namespace: str, app_type: str) -> None:
    """Delete all resources for an application."""
    deleted = []

    # Delete deployment
    if app_type in ["service", "worker"]:
        try:
            client.delete_deployment(name=name, namespace=namespace)
            deleted.append("Deployment")
        except ApiException as e:
            if e.status != 404:
                raise

    # Delete job
    if app_type == "job":
        try:
            client.batch_v1.delete_namespaced_job(
                name=name, namespace=namespace, propagation_policy="Foreground"
            )
            deleted.append("Job")
        except ApiException as e:
            if e.status != 404:
                raise

    # Delete service
    try:
        client.delete_service(name=name, namespace=namespace)
        deleted.append("Service")
    except ApiException as e:
        if e.status != 404:
            raise

    # Delete HPA
    try:
        client.delete_hpa(name=name, namespace=namespace)
        deleted.append("HPA")
    except ApiException as e:
        if e.status != 404:
            raise

    # Delete ServiceMonitor
    try:
        client.custom_objects.delete_namespaced_custom_object(
            group="monitoring.coreos.com",
            version="v1",
            namespace=namespace,
            plural="servicemonitors",
            name=name,
        )
        deleted.append("ServiceMonitor")
    except ApiException as e:
        if e.status != 404:
            raise

    # Delete ExternalSecret
    try:
        client.custom_objects.delete_namespaced_custom_object(
            group="external-secrets.io",
            version="v1beta1",
            namespace=namespace,
            plural="externalsecrets",
            name=name,
        )
        deleted.append("ExternalSecret")
    except ApiException as e:
        if e.status != 404:
            pass  # ExternalSecret might not exist

    return deleted


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
    kubeconfig = ctx.obj.get("kubeconfig")

    if not namespace:
        namespace = config.get("default_namespace", "default")

    try:
        client = K8sClient(kubeconfig=kubeconfig)

        # Auto-detect type if needed
        if type == "auto":
            detected_type = _detect_type(client, name, namespace)
            if detected_type:
                type = detected_type
                click.echo(f"Detected application type: {type}")
            else:
                click.echo(
                    f"Warning: Could not detect application type. "
                    f"Attempting to delete all resources for '{name}'.",
                    err=True,
                )
                type = "service"  # Default to service

        if not force:
            if not click.confirm(
                f"Are you sure you want to delete '{name}' ({type}) "
                f"from namespace '{namespace}'?"
            ):
                click.echo("Deletion cancelled.")
                return

        click.echo(f"Deleting application '{name}' from namespace '{namespace}'...")

        # Delete resources
        deleted = _delete_resources(client, name, namespace, type)

        if deleted:
            click.echo(f"✓ Successfully deleted: {', '.join(deleted)}")
        else:
            click.echo(f"⚠ No resources found for '{name}' in namespace '{namespace}'")

    except ApiException as e:
        if e.status == 404:
            click.echo(f"Error: Application '{name}' not found in namespace '{namespace}'", err=True)
        else:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
