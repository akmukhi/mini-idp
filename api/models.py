"""Pydantic models for API requests and responses."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EnvVar(BaseModel):
    """Environment variable model."""

    name: str
    value: Optional[str] = None
    secret: Optional[str] = None
    key: Optional[str] = None


class SecretRef(BaseModel):
    """Secret reference model."""

    secret: str
    key: str


class DeploymentRequest(BaseModel):
    """Deployment request model."""

    type: str = Field(..., description="Deployment type: service, job, or worker")
    name: str = Field(..., description="Application name")
    image: str = Field(..., description="Container image")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    port: Optional[int] = Field(None, description="Container port (required for service)")
    replicas: int = Field(default=1, description="Number of replicas")
    template: Optional[str] = Field(None, description="Custom template name")
    env: List[EnvVar] = Field(default_factory=list, description="Environment variables")
    secrets: List[SecretRef] = Field(default_factory=list, description="Secret references")
    external_secrets: List[str] = Field(
        default_factory=list, description="External secrets from GCP Secret Manager"
    )
    secret_store: str = Field(default="gcp-secret-store", description="SecretStore name")
    secret_refresh_interval: str = Field(default="1h", description="Secret refresh interval")
    autoscaling: bool = Field(default=True, description="Enable autoscaling")
    min_replicas: Optional[int] = Field(None, description="Minimum replicas")
    max_replicas: Optional[int] = Field(None, description="Maximum replicas")
    cpu_target: Optional[int] = Field(None, description="CPU target percentage")
    memory_target: Optional[int] = Field(None, description="Memory target percentage")
    metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    metrics_port: Optional[str] = Field(None, description="Metrics port name")
    metrics_interval: str = Field(default="30s", description="Prometheus scrape interval")
    logging: bool = Field(default=True, description="Enable Fluent Bit logging")
    logging_environment: Optional[str] = Field(None, description="Logging environment tag")
    gitops: bool = Field(default=False, description="Deploy via ArgoCD GitOps")
    git_repo: Optional[str] = Field(None, description="Git repository URL")
    git_path: Optional[str] = Field(None, description="Path in Git repository")
    git_branch: str = Field(default="main", description="Git branch/tag/commit")
    argocd_project: str = Field(default="default", description="ArgoCD project name")
    argocd_namespace: str = Field(default="argocd", description="ArgoCD namespace")
    auto_sync: bool = Field(default=True, description="Enable automated sync")
    prune: bool = Field(default=True, description="Enable automatic pruning")
    self_heal: bool = Field(default=True, description="Enable self-healing")
    dry_run: bool = Field(default=False, description="Dry run mode")


class DeploymentResponse(BaseModel):
    """Deployment response model."""

    success: bool
    message: str
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    deployment_name: str
    namespace: str


class TemplateInfo(BaseModel):
    """Template information model."""

    name: str
    path: str
    exists: bool


class TemplateContent(BaseModel):
    """Template content model."""

    name: str
    content: str
    path: str


class TemplateCreate(BaseModel):
    """Template creation model."""

    name: str
    content: str


class TemplateUpdate(BaseModel):
    """Template update model."""

    content: str


class DeploymentListResponse(BaseModel):
    """Deployment list response model."""

    deployments: List[Dict[str, Any]]
    total: int


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: Optional[str] = None

