"""Deployment API endpoints."""
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models import DeploymentRequest, DeploymentResponse, ErrorResponse
from cli.config import load_config
from cli.commands.deploy import (
    _build_and_validate_resources,
    _calculate_hpa_defaults,
    _get_cpu_target_default,
)
from lib.k8s_client import K8sClient

router = APIRouter(prefix="/api/deployments", tags=["deployments"])


@router.post(
    "/",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def create_deployment(request: DeploymentRequest):
    """
    Deploy an application to Kubernetes.

    Supports service, job, and worker deployment types with full configuration
    including autoscaling, metrics, logging, secrets, and GitOps.
    """
    try:
        # Validate request
        if request.type == "service" and not request.port:
            raise HTTPException(
                status_code=400,
                detail="Port is required for service deployments",
            )

        # Load configuration
        config = load_config()

        # Convert env vars and secrets to tuple format expected by CLI
        env_tuple = tuple(
            f"{env.name}={env.value}" if env.value else f"{env.name}"
            for env in request.env
        )
        secret_tuple = tuple(
            f"{secret.secret}:{secret.key}" for secret in request.secrets
        )

        # Calculate HPA defaults if autoscaling is enabled
        if request.autoscaling and request.type != "job":
            calculated_min, calculated_max = _calculate_hpa_defaults(
                type=request.type,
                replicas=request.replicas,
                min_replicas=request.min_replicas,
                max_replicas=request.max_replicas,
            )
            final_min_replicas = (
                request.min_replicas if request.min_replicas is not None else calculated_min
            )
            final_max_replicas = (
                request.max_replicas if request.max_replicas is not None else calculated_max
            )
            final_cpu_target = (
                request.cpu_target
                if request.cpu_target is not None
                else _get_cpu_target_default(request.type)
            )
        else:
            final_min_replicas = request.min_replicas if request.min_replicas is not None else 1
            final_max_replicas = request.max_replicas if request.max_replicas is not None else 10
            final_cpu_target = request.cpu_target if request.cpu_target is not None else 70

        # Auto-determine metrics port
        final_metrics_port = request.metrics_port if request.metrics_port else "http"

        # Build resources
        resources = _build_and_validate_resources(
            config=config,
            type=request.type,
            name=request.name,
            image=request.image,
            namespace=request.namespace,
            port=request.port,
            replicas=request.replicas,
            template=request.template,
            env=env_tuple,
            secret=secret_tuple,
            autoscaling=request.autoscaling,
            min_replicas=final_min_replicas,
            max_replicas=final_max_replicas,
            cpu_target=final_cpu_target,
            memory_target=request.memory_target,
            metrics=request.metrics,
            metrics_path=request.metrics_path,
            metrics_port=final_metrics_port,
            metrics_interval=request.metrics_interval,
            logging=request.logging,
            logging_environment=request.logging_environment,
            external_secret=tuple(request.external_secrets),
            secret_store=request.secret_store,
            secret_refresh_interval=request.secret_refresh_interval,
        )

        # If dry run, return resources without applying
        if request.dry_run:
            return DeploymentResponse(
                success=True,
                message="Dry run completed successfully",
                resources=resources,
                deployment_name=request.name,
                namespace=request.namespace,
            )

        # Apply resources to cluster
        try:
            client = K8sClient()
            from cli.commands.deploy import _apply_resources

            _apply_resources(client, resources, request.name, request.namespace, None)

            # Handle GitOps if requested
            if request.gitops:
                if not request.git_repo:
                    raise HTTPException(
                        status_code=400,
                        detail="git_repo is required for GitOps deployment",
                    )

                from cli.commands.deploy import _deploy_gitops

                _deploy_gitops(
                    name=request.name,
                    namespace=request.namespace,
                    git_repo=request.git_repo,
                    git_path=request.git_path,
                    git_branch=request.git_branch,
                    argocd_project=request.argocd_project,
                    argocd_namespace=request.argocd_namespace,
                    auto_sync=request.auto_sync,
                    prune=request.prune,
                    self_heal=request.self_heal,
                    config=config,
                    client=client,
                    click_obj=None,  # Not needed for API
                )

            return DeploymentResponse(
                success=True,
                message=f"Successfully deployed {request.type} '{request.name}' to namespace '{request.namespace}'",
                resources=resources,
                deployment_name=request.name,
                namespace=request.namespace,
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error deploying to cluster: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/", response_model=List[dict], tags=["deployments"])
async def list_deployments(namespace: Optional[str] = None):
    """
    List all deployments.

    Returns deployments from the specified namespace or all namespaces.
    """
    try:
        client = K8sClient()
        apps_v1 = client.apps_v1

        if namespace:
            deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
        else:
            deployments = apps_v1.list_deployment_for_all_namespaces()

        result = []
        for deployment in deployments.items:
            result.append(
                {
                    "name": deployment.metadata.name,
                    "namespace": deployment.metadata.namespace,
                    "replicas": deployment.spec.replicas,
                    "image": deployment.spec.template.spec.containers[0].image
                    if deployment.spec.template.spec.containers
                    else None,
                    "ready_replicas": deployment.status.ready_replicas or 0,
                    "available_replicas": deployment.status.available_replicas or 0,
                }
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing deployments: {str(e)}",
        )


@router.get("/{name}", response_model=dict, tags=["deployments"])
async def get_deployment(name: str, namespace: str = "default"):
    """
    Get deployment details.

    Returns detailed information about a specific deployment.
    """
    try:
        client = K8sClient()
        deployment = client.apps_v1.read_namespaced_deployment(
            name=name, namespace=namespace
        )

        return {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas,
            "image": deployment.spec.template.spec.containers[0].image
            if deployment.spec.template.spec.containers
            else None,
            "ready_replicas": deployment.status.ready_replicas or 0,
            "available_replicas": deployment.status.available_replicas or 0,
            "labels": deployment.metadata.labels or {},
            "annotations": deployment.metadata.annotations or {},
        }

    except Exception as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 500,
            detail=f"Error getting deployment: {str(e)}",
        )


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT, tags=["deployments"])
async def delete_deployment(name: str, namespace: str = "default"):
    """
    Delete a deployment.

    Removes the deployment and associated resources from the cluster.
    """
    try:
        client = K8sClient()
        client.delete_deployment(name=name, namespace=namespace)
        return None

    except Exception as e:
        raise HTTPException(
            status_code=404 if "not found" in str(e).lower() else 500,
            detail=f"Error deleting deployment: {str(e)}",
        )

