"""Status command for Mini-IDP CLI."""
import sys
import time
from pathlib import Path
from typing import Optional

import click
from kubernetes.client.rest import ApiException

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.k8s_client import K8sClient


def _get_deployment_status(client: K8sClient, name: str, namespace: str) -> Optional[dict]:
    """Get deployment status."""
    try:
        deployment = client.apps_v1.read_namespaced_deployment(
            name=name, namespace=namespace
        )
        service = None
        try:
            service = client.core_v1.read_namespaced_service(
                name=name, namespace=namespace
            )
        except ApiException:
            pass

        # Get pods
        pods = client.core_v1.list_namespaced_pod(
            namespace=namespace, label_selector=f"app={name}"
        )

        # Get HPA if exists
        hpa = None
        try:
            from kubernetes.client import AutoscalingV2Api

            autoscaling_api = AutoscalingV2Api()
            hpa = autoscaling_api.read_namespaced_horizontal_pod_autoscaler(
                name=name, namespace=namespace
            )
        except ApiException:
            pass

        return {
            "type": "deployment",
            "deployment": deployment,
            "service": service,
            "pods": pods.items,
            "hpa": hpa,
        }
    except ApiException as e:
        if e.status == 404:
            return None
        raise


def _get_job_status(client: K8sClient, name: str, namespace: str) -> Optional[dict]:
    """Get job status."""
    try:
        job = client.batch_v1.read_namespaced_job(name=name, namespace=namespace)

        # Get pods
        pods = client.core_v1.list_namespaced_pod(
            namespace=namespace, label_selector=f"job-name={name}"
        )

        return {
            "type": "job",
            "job": job,
            "pods": pods.items,
        }
    except ApiException as e:
        if e.status == 404:
            return None
        raise


def _display_status(status: dict, name: str, namespace: str) -> None:
    """Display application status."""
    click.echo(f"\n📊 Status of '{name}' in namespace '{namespace}':\n")

    if status["type"] == "deployment":
        deployment = status["deployment"]
        pods = status["pods"]
        service = status.get("service")
        hpa = status.get("hpa")

        # Deployment info
        click.echo("📦 Deployment:")
        ready = deployment.status.ready_replicas or 0
        desired = deployment.spec.replicas or 0
        available = deployment.status.available_replicas or 0
        click.echo(f"  Replicas: {ready}/{desired} ready, {available} available")
        click.echo(f"  Image: {deployment.spec.template.spec.containers[0].image}")

        # Pod status
        click.echo(f"\n🔄 Pods ({len(pods)}):")
        for pod in pods:
            phase = pod.status.phase
            ready_containers = sum(
                1
                for container_status in pod.status.container_statuses or []
                if container_status.ready
            )
            total_containers = len(pod.spec.containers)
            status_icon = "✓" if phase == "Running" and ready_containers == total_containers else "⚠"
            click.echo(
                f"  {status_icon} {pod.metadata.name}: {phase} "
                f"({ready_containers}/{total_containers} containers ready)"
            )

        # Service info
        if service:
            click.echo(f"\n🌐 Service:")
            click.echo(f"  Type: {service.spec.type}")
            if service.spec.type == "LoadBalancer" and service.status.load_balancer.ingress:
                click.echo(f"  External IP: {service.status.load_balancer.ingress[0].hostname or service.status.load_balancer.ingress[0].ip}")
            ports = ", ".join(
                f"{port.port}:{port.target_port}" for port in service.spec.ports
            )
            click.echo(f"  Ports: {ports}")

        # HPA info
        if hpa:
            click.echo(f"\n📈 Autoscaling (HPA):")
            click.echo(
                f"  Replicas: {hpa.status.current_replicas or 0}/"
                f"{hpa.spec.min_replicas}-{hpa.spec.max_replicas}"
            )
            if hpa.status.conditions:
                for condition in hpa.status.conditions:
                    click.echo(f"  {condition.type}: {condition.status}")

    elif status["type"] == "job":
        job = status["job"]
        pods = status["pods"]

        # Job info
        click.echo("📋 Job:")
        if job.status.succeeded:
            click.echo(f"  Status: ✓ Succeeded ({job.status.succeeded} completed)")
        elif job.status.failed:
            click.echo(f"  Status: ✗ Failed ({job.status.failed} failed)")
        elif job.status.active:
            click.echo(f"  Status: ⏳ Running ({job.status.active} active)")
        else:
            click.echo("  Status: ⏸ Pending")

        # Pod status
        click.echo(f"\n🔄 Pods ({len(pods)}):")
        for pod in pods:
            phase = pod.status.phase
            status_icon = "✓" if phase == "Succeeded" else "⚠" if phase == "Failed" else "⏳"
            click.echo(f"  {status_icon} {pod.metadata.name}: {phase}")


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
    kubeconfig = ctx.obj.get("kubeconfig")

    if not namespace:
        namespace = config.get("default_namespace", "default")

    try:
        client = K8sClient(kubeconfig=kubeconfig)

        if watch:
            click.echo(f"Watching status of '{name}' in namespace '{namespace}'...")
            click.echo("Press Ctrl+C to stop\n")

            try:
                while True:
                    # Clear screen (works on most terminals)
                    click.clear()

                    # Try deployment first
                    status_info = _get_deployment_status(client, name, namespace)
                    if not status_info:
                        # Try job
                        status_info = _get_job_status(client, name, namespace)

                    if status_info:
                        _display_status(status_info, name, namespace)
                    else:
                        click.echo(f"⚠ Application '{name}' not found in namespace '{namespace}'")

                    time.sleep(2)  # Update every 2 seconds

            except KeyboardInterrupt:
                click.echo("\n\nStopped watching.")
        else:
            # Try deployment first
            status_info = _get_deployment_status(client, name, namespace)
            if not status_info:
                # Try job
                status_info = _get_job_status(client, name, namespace)

            if status_info:
                _display_status(status_info, name, namespace)
            else:
                click.echo(
                    f"Error: Application '{name}' not found in namespace '{namespace}'", err=True
                )
                sys.exit(1)

    except ApiException as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
