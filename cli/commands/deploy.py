"""
Deploy command for Mini-IDP CLI.
"""

import sys
from typing import List, Optional

import click
import yaml

from lib.k8s_client import K8sClient
from lib.template_builder import TemplateBuilder


def _calculate_hpa_defaults(
    type: str, replicas: int, min_replicas: Optional[int], max_replicas: Optional[int]
) -> tuple[int, int]:
    """
    Calculate sensible HPA defaults based on deployment type and replicas.

    Args:
        type: Deployment type (service, worker)
        replicas: Initial number of replicas
        min_replicas: User-specified min replicas (None if not specified)
        max_replicas: User-specified max replicas (None if not specified)

    Returns:
        Tuple of (min_replicas, max_replicas)
    """
    # Calculate min_replicas
    if min_replicas is not None:
        calculated_min = min_replicas
    else:
        # For production workloads, min should allow for rolling updates
        if replicas > 1:
            # Min should be at least 50% of replicas, but at least 1
            calculated_min = max(1, replicas // 2)
        else:
            calculated_min = 1

    # Calculate max_replicas
    if max_replicas is not None:
        calculated_max = max_replicas
    else:
        # Max should be at least 2x replicas for burst capacity
        # For services, use 3x; for workers, use 2x
        multiplier = 3 if type == "service" else 2
        calculated_max = max(10, replicas * multiplier)

    # Ensure min <= max
    if calculated_min > calculated_max:
        calculated_max = calculated_min * 2

    return calculated_min, calculated_max


def _get_cpu_target_default(type: str) -> int:
    """
    Get default CPU target based on deployment type.

    Args:
        type: Deployment type (service, worker)

    Returns:
        Default CPU target percentage
    """
    # Services: 70% (balanced)
    # Workers: 60% (more aggressive scaling for queue processing)
    return 60 if type == "worker" else 70


def _build_resources(
    template_builder: TemplateBuilder,
    type: str,
    name: str,
    image: str,
    namespace: str,
    port: Optional[int],
    replicas: int,
    template: Optional[str],
    env: tuple,
    secret: tuple,
    autoscaling: bool,
    min_replicas: Optional[int],
    max_replicas: Optional[int],
    cpu_target: Optional[int],
    memory_target: Optional[int],
    metrics: bool,
) -> List[dict]:
    """
    Build Kubernetes resources from template.

    Args:
        template_builder: Template builder instance
        type: Resource type (service, job, worker)
        name: Application name
        image: Container image
        namespace: Kubernetes namespace
        port: Container port
        replicas: Number of replicas
        template: Custom template name (optional)
        env: Environment variables tuple
        secret: Secret references tuple
        autoscaling: Enable autoscaling
        min_replicas: Minimum replicas
        max_replicas: Maximum replicas
        cpu_target: CPU target percentage
        memory_target: Memory target percentage
        metrics: Enable metrics

    Returns:
        List of Kubernetes resource dictionaries
    """
    # Build based on type
    if type == "service":
        resources = template_builder.build_service(
            name=name,
            image=image,
            namespace=namespace,
            port=port,
            replicas=replicas,
            env=list(env) if env else [],
            secret=list(secret) if secret else [],
            autoscaling=autoscaling,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            cpu_target=cpu_target,
            memory_target=memory_target,
            metrics=metrics,
            logging_enabled=logging,
            logging_environment=logging_environment,
        )
    elif type == "job":
        resources = template_builder.build_job(
            name=name,
            image=image,
            namespace=namespace,
            env=list(env) if env else [],
            secret=list(secret) if secret else [],
            logging_enabled=logging,
            logging_environment=logging_environment,
        )
    elif type == "worker":
        resources = template_builder.build_worker(
            name=name,
            image=image,
            namespace=namespace,
            replicas=replicas,
            env=list(env) if env else [],
            secret=list(secret) if secret else [],
            autoscaling=autoscaling,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            cpu_target=cpu_target,
            memory_target=memory_target,
            metrics=metrics,
            logging_enabled=logging,
            logging_environment=logging_environment,
        )
    else:
        raise ValueError(f"Unknown type: {type}")

    return resources


def _apply_resources(
    client: K8sClient,
    resources: List[dict],
    name: str,
    namespace: str,
    click_obj,
) -> None:
    """
    Apply Kubernetes resources to cluster.

    Args:
        client: Kubernetes client
        resources: List of resource dictionaries
        name: Application name (for logging)
        namespace: Kubernetes namespace
        click_obj: Click context for output
    """
    for resource in resources:
        kind = resource.get("kind", "Unknown")
        resource_name = resource.get("metadata", {}).get("name", "unknown")

        try:
            _apply_single_resource(client, resource, kind, resource_name, click_obj)
        except Exception as e:
            click_obj.echo(
                f"  ✗ Failed to apply {kind} {resource_name}: {e}",
                err=True,
            )
            raise


def _apply_single_resource(client, resource, kind, resource_name, click_obj):
    """Apply a single Kubernetes resource."""
    handlers = {
        "Deployment": _apply_deployment_resource,
        "Service": _apply_service_resource,
        "Job": _apply_job_resource,
        "CronJob": _apply_cronjob_resource,
        "HorizontalPodAutoscaler": _apply_hpa_resource,
        "ServiceMonitor": _apply_servicemonitor_resource,
    }

    handler = handlers.get(kind)
    if handler:
        handler(client, resource, resource_name, click_obj)
    else:
        click_obj.echo(f"  ⚠ Skipping unsupported resource: {kind}")


def _apply_deployment_resource(client, resource, resource_name, click_obj):
    """Apply a Deployment resource."""
    from io import StringIO

    from kubernetes.client import V1Deployment
    from kubernetes.utils import create_from_yaml

    yaml_str = yaml.dump(resource, default_flow_style=False)
    yaml_file = StringIO(yaml_str)
    objs = create_from_yaml(client.api_client, yaml_file)
    deployment = objs[0] if objs else None
    if deployment and isinstance(deployment, V1Deployment):
        result = client.apply_deployment(deployment)
        click_obj.echo(f"  ✓ {result['action']} Deployment: {resource_name}")


def _apply_service_resource(client, resource, resource_name, click_obj):
    """Apply a Service resource."""
    from io import StringIO

    from kubernetes.client import V1Service
    from kubernetes.utils import create_from_yaml

    yaml_str = yaml.dump(resource, default_flow_style=False)
    yaml_file = StringIO(yaml_str)
    objs = create_from_yaml(client.api_client, yaml_file)
    service = objs[0] if objs else None
    if service and isinstance(service, V1Service):
        result = client.apply_service(service)
        click_obj.echo(f"  ✓ {result['action']} Service: {resource_name}")


def _apply_job_resource(client, resource, resource_name, click_obj):
    """Apply a Job resource."""
    from io import StringIO

    from kubernetes.client import V1Job
    from kubernetes.utils import create_from_yaml

    yaml_str = yaml.dump(resource, default_flow_style=False)
    yaml_file = StringIO(yaml_str)
    objs = create_from_yaml(client.api_client, yaml_file)
    job = objs[0] if objs else None
    if job and isinstance(job, V1Job):
        result = client.apply_job(job)
        click_obj.echo(f"  ✓ {result['action']} Job: {resource_name}")


def _apply_cronjob_resource(client, resource, resource_name, click_obj):
    """Apply a CronJob resource."""
    from io import StringIO

    from kubernetes.client import V1CronJob
    from kubernetes.utils import create_from_yaml

    yaml_str = yaml.dump(resource, default_flow_style=False)
    yaml_file = StringIO(yaml_str)
    objs = create_from_yaml(client.api_client, yaml_file)
    cronjob = objs[0] if objs else None
    if cronjob and isinstance(cronjob, V1CronJob):
        result = client.apply_cron_job(cronjob)
        click_obj.echo(f"  ✓ {result['action']} CronJob: {resource_name}")


def _apply_hpa_resource(client, resource, resource_name, click_obj):
    """Apply a HorizontalPodAutoscaler resource."""
    from io import StringIO

    from kubernetes.utils import create_from_yaml

    yaml_str = yaml.dump(resource, default_flow_style=False)
    yaml_file = StringIO(yaml_str)
    objs = create_from_yaml(client.api_client, yaml_file)
    hpa = objs[0] if objs else None
    if hpa:
        result = client.apply_hpa(hpa)
        click_obj.echo(
            f"  ✓ {result['action']} HorizontalPodAutoscaler: {resource_name}"
        )


def _apply_servicemonitor_resource(client, resource, resource_name, click_obj):
    """Apply a ServiceMonitor resource."""
    result = client.apply_service_monitor(resource)
    click_obj.echo(f"  ✓ {result['action']} ServiceMonitor: {resource_name}")


def _deploy_gitops(
    name: str,
    namespace: str,
    git_repo: Optional[str],
    git_path: Optional[str],
    config: dict,
    client: K8sClient,
    click_obj,
) -> None:
    """
    Deploy via ArgoCD GitOps.

    Args:
        name: Application name
        namespace: Kubernetes namespace
        git_repo: Git repository URL
        git_path: Path in repository
        config: CLI configuration
        client: Kubernetes client
        click_obj: Click context for output
    """
    from lib.argocd import build_argocd_application

    if not git_repo:
        raise ValueError("--git-repo is required for GitOps deployment")

    if not git_path:
        git_path = "manifests"

    argocd_namespace = config.get("argocd_namespace", "argocd")

    application = build_argocd_application(
        name=name,
        namespace=argocd_namespace,
        repo_url=git_repo,
        path=git_path,
        target_revision="HEAD",
    )

    # Convert to dict for custom resource API
    from kubernetes.client import ApiClient

    api_client = ApiClient()
    app_dict = api_client.sanitize_for_serialization(application)

    result = client.apply_argocd_application(app_dict)
    click_obj.echo(f"  ✓ {result['action']} ArgoCD Application: {name}")


@click.command("deploy")
@click.argument("type", type=click.Choice(["service", "job", "worker"]))
@click.argument("name")
@click.option(
    "--image",
    required=True,
    help="Container image to deploy (e.g., gcr.io/project/image:tag)",
)
@click.option(
    "--port",
    type=int,
    help="Container port (required for services)",
)
@click.option(
    "--namespace",
    "-n",
    help="Kubernetes namespace (default: from config)",
)
@click.option(
    "--replicas",
    "-r",
    type=int,
    default=1,
    help="Number of replicas (default: 1)",
)
@click.option(
    "--template",
    "-t",
    help="Template to use (optional, uses default for type)",
)
@click.option(
    "--env",
    "-e",
    multiple=True,
    help="Environment variables (format: KEY=VALUE)",
)
@click.option(
    "--secret",
    "-s",
    multiple=True,
    help="Secret references (format: SECRET_NAME:KEY)",
)
@click.option(
    "--autoscaling/--no-autoscaling",
    default=True,
    help="Enable autoscaling (default: enabled)",
)
@click.option(
    "--min-replicas",
    type=int,
    default=None,
    help="Minimum replicas for autoscaling (auto-calculated if not specified)",
)
@click.option(
    "--max-replicas",
    type=int,
    default=None,
    help="Maximum replicas for autoscaling (auto-calculated if not specified)",
)
@click.option(
    "--cpu-target",
    type=int,
    default=None,
    help="CPU target percentage for autoscaling (70% for services, 60% for workers)",
)
@click.option(
    "--memory-target",
    type=int,
    default=80,
    help="Memory target percentage for autoscaling (default: 80)",
)
@click.option(
    "--metrics/--no-metrics",
    default=True,
    help="Enable Prometheus metrics collection (default: enabled)",
)
@click.option(
    "--logging/--no-logging",
    default=True,
    help="Enable Fluent Bit log collection (default: enabled)",
)
@click.option(
    "--logging-environment",
    help="Environment label for logs (e.g., production, staging)",
)
@click.option(
    "--gitops/--no-gitops",
    default=False,
    help="Deploy via ArgoCD GitOps (default: disabled)",
)
@click.option(
    "--git-repo",
    help="Git repository URL for GitOps deployment",
)
@click.option(
    "--git-path",
    help="Path in Git repository for GitOps deployment",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deployed without actually deploying",
)
@click.pass_context
def deploy(
    ctx,
    type,
    name,
    image,
    port,
    namespace,
    replicas,
    template,
    env,
    secret,
    autoscaling,
    min_replicas,
    max_replicas,
    cpu_target,
    memory_target,
    metrics,
    logging,
    logging_environment,
    gitops,
    git_repo,
    git_path,
    dry_run,
):
    """
    Deploy an application to Kubernetes.

    \b
    Types:
      service  - Deploy a stateless service (web app, API)
      job      - Deploy a one-time or scheduled job
      worker   - Deploy a long-running worker process

    \b
    Examples:
      # Deploy a service
      mini-idp deploy service my-api --image gcr.io/project/api:v1.0 \\
        --port 8080

      # Deploy a job with environment variables
      mini-idp deploy job data-processor \\
        --image gcr.io/project/processor:latest \\
        --env DATABASE_URL=postgres://... --env API_KEY=secret

      # Deploy a worker with autoscaling
      mini-idp deploy worker queue-worker \\
        --image gcr.io/project/worker:latest \\
        --replicas 3 --min-replicas 2 --max-replicas 10

      # Deploy with custom template
      mini-idp deploy service my-api --image gcr.io/project/api:v1.0 \\
        --port 8080 --template custom-service

      # Deploy with GitOps
      mini-idp deploy service my-api --image gcr.io/project/api:v1.0 \\
        --port 8080 --gitops --git-repo https://github.com/org/repo \\
        --git-path k8s/manifests
    """
    config = ctx.obj["config"]

    # Validate and setup
    _validate_deploy_options(type, port)
    namespace = namespace or config.get("default_namespace", "default")
    kubeconfig = ctx.obj.get("kubeconfig") or config.get("kubeconfig")

    # Calculate automatic HPA defaults if autoscaling is enabled
    if autoscaling and type != "job":
        calculated_min, calculated_max = _calculate_hpa_defaults(
            type=type,
            replicas=replicas,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
        )
        # Use calculated values if user didn't specify custom ones
        final_min_replicas = min_replicas if min_replicas is not None else calculated_min
        final_max_replicas = max_replicas if max_replicas is not None else calculated_max
        # Use type-specific CPU target if not explicitly set
        final_cpu_target = (
            cpu_target if cpu_target is not None else _get_cpu_target_default(type)
        )
    else:
        # Use defaults if not specified
        final_min_replicas = min_replicas if min_replicas is not None else 1
        final_max_replicas = max_replicas if max_replicas is not None else 10
        final_cpu_target = cpu_target if cpu_target is not None else 70

    # Build resources
    resources = _build_and_validate_resources(
        config=config,
        type=type,
        name=name,
        image=image,
        namespace=namespace,
        port=port,
        replicas=replicas,
        template=template,
        env=env,
        secret=secret,
        autoscaling=autoscaling,
        min_replicas=final_min_replicas,
        max_replicas=final_max_replicas,
        cpu_target=final_cpu_target,
        memory_target=memory_target,
        metrics=metrics,
        logging=logging,
        logging_environment=logging_environment,
    )

    # Display info (show calculated HPA values if autoscaling is enabled)
    _display_deployment_info(
        type, name, namespace, image, port, replicas, resources
    )
    if autoscaling and type != "job":
        click.echo(f"  Autoscaling: min={final_min_replicas}, max={final_max_replicas}, cpu={final_cpu_target}%")

    # Handle dry-run
    if dry_run:
        _display_dry_run(resources)
        return

    # Deploy to cluster
    _deploy_to_cluster(
        kubeconfig=kubeconfig,
        resources=resources,
        name=name,
        namespace=namespace,
        gitops=gitops,
        git_repo=git_repo,
        git_path=git_path,
        config=config,
    )

    click.echo(f"\n✓ Successfully deployed {type} '{name}' to namespace '{namespace}'")


def _validate_deploy_options(type: str, port: Optional[int]) -> None:
    """Validate deployment options."""
    if type == "service" and not port:
        raise click.UsageError("--port is required for service deployments")


def _build_and_validate_resources(
    config: dict,
    type: str,
    name: str,
    image: str,
    namespace: str,
    port: Optional[int],
    replicas: int,
    template: Optional[str],
    env: tuple,
    secret: tuple,
    autoscaling: bool,
    min_replicas: int,
    max_replicas: int,
    cpu_target: int,
    memory_target: Optional[int],
    metrics: bool,
    logging: bool = True,
    logging_environment: Optional[str] = None,
) -> List[dict]:
    """Build and validate resources from template."""
    templates_dir = config.get("templates_dir")
    template_builder = TemplateBuilder(template_dir=templates_dir)

    try:
        return _build_resources(
            template_builder=template_builder,
            type=type,
            name=name,
            image=image,
            namespace=namespace,
            port=port,
            replicas=replicas,
            template=template,
            env=env,
            secret=secret,
            autoscaling=autoscaling,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            cpu_target=cpu_target,
            memory_target=memory_target,
            metrics=metrics,
            logging=logging,
            logging_environment=logging_environment,
        )
    except Exception as e:
        click.echo(f"Error building resources: {e}", err=True)
        sys.exit(1)


def _display_deployment_info(
    type: str,
    name: str,
    namespace: str,
    image: str,
    port: Optional[int],
    replicas: int,
    resources: List[dict],
) -> None:
    """Display deployment information."""
    click.echo(f"Deploying {type} '{name}' to namespace '{namespace}'...")
    click.echo(f"  Image: {image}")
    if port:
        click.echo(f"  Port: {port}")
    if type != "job":
        click.echo(f"  Replicas: {replicas}")
    click.echo(f"  Resources: {len(resources)}")


def _display_dry_run(resources: List[dict]) -> None:
    """Display dry-run information."""
    click.echo("\n[DRY RUN] Would deploy the following resources:")
    for resource in resources:
        kind = resource.get("kind", "Unknown")
        resource_name = resource.get("metadata", {}).get("name", "unknown")
        click.echo(f"  - {kind}: {resource_name}")

    click.echo("\n--- Resource YAML ---")
    for resource in resources:
        click.echo("---")
        click.echo(yaml.dump(resource, default_flow_style=False))
    click.echo("\nUse --no-dry-run to actually deploy.")


def _deploy_to_cluster(
    kubeconfig: Optional[str],
    resources: List[dict],
    name: str,
    namespace: str,
    gitops: bool,
    git_repo: Optional[str],
    git_path: Optional[str],
    config: dict,
) -> None:
    """Deploy resources to cluster."""
    try:
        client = K8sClient(kubeconfig=kubeconfig)
        _apply_resources(client, resources, name, namespace, click)
    except Exception as e:
        click.echo(f"Error deploying resources: {e}", err=True)
        sys.exit(1)

    # Handle GitOps if requested
    if gitops:
        try:
            _deploy_gitops(
                name=name,
                namespace=namespace,
                git_repo=git_repo,
                git_path=git_path,
                config=config,
                client=client,
                click_obj=click,
            )
        except Exception as e:
            click.echo(f"Warning: GitOps deployment failed: {e}", err=True)
            click.echo("Resources were deployed directly to cluster.")
